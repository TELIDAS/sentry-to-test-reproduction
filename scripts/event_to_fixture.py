#!/usr/bin/env python3
"""Convert a raw Sentry event (JSON) into a small, sanitized fixture for tests.

Usage:
    python scripts/event_to_fixture.py event.json > tests/fixtures/sentry_<id>.json
    cat event.json | python scripts/event_to_fixture.py - > fixture.json

Handles both the Sentry API shape (``entries`` list) and the SDK/envelope shape
(top-level ``exception`` / ``request`` / ``breadcrumbs``).

PII handling: masks common identity/credential keys, emails, IPv4/IPv6 addresses,
URL credentials and sensitive query parameters, bearer tokens, and long
secret-like strings. Automated detection is incomplete; review output before use.
"""
import json
import ipaddress
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_CANDIDATE_RE = re.compile(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")
BEARER_RE = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+")
SECRET_RE = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
URL_USERINFO_RE = re.compile(r"(?i)(https?://)[^/@\s]+@")
SENSITIVE_KEY_PARTS = {
    "address", "api_key", "auth", "authorization", "birth_date", "card",
    "client_ip", "cookie", "csrf", "cvv", "date_of_birth", "dob", "email",
    "first_name", "full_name", "ip", "ip_address", "last_name", "mobile",
    "name", "password", "passwd", "phone", "postal_code", "pwd", "remote_addr",
    "secret", "session", "ssn", "street", "token", "user", "user_id",
    "username", "zip_code",
}

MASK = "[REDACTED]"
MAX_BREADCRUMBS = 30
MAX_STR = 2000


def normalize_key(key) -> str:
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(key))
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def is_sensitive_key(key) -> bool:
    parts = set(normalize_key(key).split("_"))
    normalized = normalize_key(key)
    return normalized in SENSITIVE_KEY_PARTS or bool(parts & SENSITIVE_KEY_PARTS)


def scrub_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        if not parts.scheme or not parts.netloc:
            return value
        host = parts.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        if parts.port:
            host = f"{host}:{parts.port}"
        if parts.username is not None or parts.password is not None:
            host = f"{MASK}@{host}"
        query = urlencode(
            [(key, MASK if is_sensitive_key(key) else val)
             for key, val in parse_qsl(parts.query, keep_blank_values=True)],
            doseq=True,
        )
        fragment = parts.fragment
        if "=" in fragment:
            fragment = urlencode(
                [(key, MASK if is_sensitive_key(key) else val)
                 for key, val in parse_qsl(fragment.lstrip("?"), keep_blank_values=True)],
                doseq=True,
            )
        return urlunsplit((parts.scheme, host, parts.path, query, fragment))
    except ValueError:
        # Do not leak URL userinfo even if parsing fails on a malformed port.
        return URL_USERINFO_RE.sub(rf"\1{MASK}@", value)


def scrub_text(value: str) -> str:
    value = EMAIL_RE.sub("user@example.com", value)
    value = IPV4_RE.sub("0.0.0.0", value)

    def mask_ipv6(match):
        candidate = match.group(0)
        try:
            ipaddress.IPv6Address(candidate)
            return "::"
        except ipaddress.AddressValueError:
            return candidate

    value = IPV6_CANDIDATE_RE.sub(mask_ipv6, value)
    value = BEARER_RE.sub(lambda m: f"{m.group(1)} {MASK}", value)
    value = SECRET_RE.sub(MASK, value)
    if len(value) > MAX_STR:
        value = value[:MAX_STR] + "...[truncated]"
    return value


def scrub_str(value: str) -> str:
    value = URL_RE.sub(lambda m: scrub_url(m.group(0)), value)
    return scrub_text(value)


def scrub(obj, key=None):
    if key is not None and is_sensitive_key(key):
        return MASK
    if isinstance(obj, dict):
        return {k: scrub(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        # header-style pairs: ["Cookie", "..."]
        if len(obj) == 2 and isinstance(obj[0], str) and is_sensitive_key(obj[0]):
            return [obj[0], MASK]
        return [scrub(v) for v in obj]
    if isinstance(obj, str):
        if normalize_key(key or "") in {"query", "query_string", "querystring"} and "=" in obj:
            return scrub_str(scrub_url(f"https://redaction.invalid/?{obj.lstrip('?')}").split("?", 1)[1])
        return scrub_str(obj)
    return obj


def find_entry(event: dict, entry_type: str):
    for entry in event.get("entries", []) or []:
        if entry.get("type") == entry_type:
            return entry.get("data")
    return event.get(entry_type)


def extract_exception(event: dict):
    data = find_entry(event, "exception")
    if not data:
        return []
    values = data.get("values", []) if isinstance(data, dict) else data
    out = []
    for exc in values or []:
        frames = (exc.get("stacktrace") or {}).get("frames", []) or []
        out.append(
            {
                "type": exc.get("type"),
                "value": exc.get("value"),
                "module": exc.get("module"),
                "mechanism": (exc.get("mechanism") or {}).get("type"),
                "frames": [
                    {
                        "filename": f.get("filename"),
                        "module": f.get("module"),
                        "function": f.get("function"),
                        "lineno": f.get("lineno"),
                        "in_app": f.get("in_app"),
                        "context_line": f.get("context_line") or f.get("context"),
                        "vars": f.get("vars"),
                    }
                    for f in frames
                ],
            }
        )
    return out


def extract_breadcrumbs(event: dict):
    data = find_entry(event, "breadcrumbs")
    if not data:
        return []
    values = data.get("values", []) if isinstance(data, dict) else data
    keep = ("timestamp", "category", "type", "level", "message", "data")
    return [{k: b.get(k) for k in keep if k in b} for b in (values or [])[-MAX_BREADCRUMBS:]]


def tags_to_dict(tags):
    if isinstance(tags, dict):
        return tags
    out = {}
    for t in tags or []:
        if isinstance(t, dict) and "key" in t:
            out[t["key"]] = t.get("value")
        elif isinstance(t, (list, tuple)) and len(t) == 2:
            out[t[0]] = t[1]
    return out


def build_fixture(event: dict) -> dict:
    request = find_entry(event, "request") or {}
    fixture = {
        "sentry": {
            "event_id": event.get("eventID") or event.get("event_id"),
            "issue_id": event.get("groupID") or event.get("issue_id"),
            "title": event.get("title"),
            "platform": event.get("platform"),
            "release": (event.get("release") or {}).get("version")
            if isinstance(event.get("release"), dict)
            else event.get("release"),
            "environment": tags_to_dict(event.get("tags")).get("environment")
            or event.get("environment"),
        },
        "exception": extract_exception(event),
        "request": {
            "method": request.get("method"),
            "url": request.get("url"),
            "query": request.get("query") or request.get("query_string"),
            "headers": request.get("headers"),
            "data": request.get("data"),
        }
        if request
        else None,
        "tags": tags_to_dict(event.get("tags")),
        "breadcrumbs": extract_breadcrumbs(event),
        "contexts": event.get("contexts"),
    }
    ids = {k: fixture["sentry"][k] for k in ("event_id", "issue_id")}
    fixture = scrub(fixture)
    fixture["sentry"].update(ids)  # ids are not secrets; keep them for traceability
    return fixture


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(__doc__)
        return 2
    if argv[1] == "-":
        raw = sys.stdin.read()
    else:
        with open(argv[1], encoding="utf-8") as source:
            raw = source.read()
    event = json.loads(raw)
    json.dump(build_fixture(event), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
