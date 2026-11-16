#!/usr/bin/env python3
"""Convert a raw Sentry event (JSON) into a small, sanitized fixture for tests.

Usage:
    python event_to_fixture.py event.json > tests/fixtures/sentry_<id>.json
    cat event.json | python event_to_fixture.py - > fixture.json

Handles both the Sentry API shape (``entries`` list) and the SDK/envelope shape
(top-level ``exception`` / ``request`` / ``breadcrumbs``).

PII handling: masks values of sensitive keys, emails, IPv4 addresses, bearer
tokens and long hex/base64-like secrets. Review the output before committing.
"""
import json
import re
import sys

SENSITIVE_KEYS = re.compile(
    r"(pass(word)?|secret|token|api[_-]?key|authorization|cookie|session|"
    r"csrf|ssn|card|cvv|email|phone|ip_address|auth)",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
BEARER_RE = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]+")
SECRET_RE = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")

MASK = "[REDACTED]"
MAX_BREADCRUMBS = 30
MAX_STR = 2000


def scrub_str(value: str) -> str:
    value = EMAIL_RE.sub("user@example.com", value)
    value = IPV4_RE.sub("0.0.0.0", value)
    value = BEARER_RE.sub(lambda m: f"{m.group(1)} {MASK}", value)
    value = SECRET_RE.sub(MASK, value)
    if len(value) > MAX_STR:
        value = value[:MAX_STR] + "...[truncated]"
    return value


def scrub(obj, key=None):
    if key is not None and SENSITIVE_KEYS.search(str(key)):
        return MASK
    if isinstance(obj, dict):
        return {k: scrub(v, k) for k, v in obj.items()}
    if isinstance(obj, list):
        # header-style pairs: ["Cookie", "..."]
        if len(obj) == 2 and isinstance(obj[0], str) and SENSITIVE_KEYS.search(obj[0]):
            return [obj[0], MASK]
        return [scrub(v) for v in obj]
    if isinstance(obj, str):
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
    raw = sys.stdin.read() if argv[1] == "-" else open(argv[1], encoding="utf-8").read()
    event = json.loads(raw)
    json.dump(build_fixture(event), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
