# sentry-repro

An agent skill that turns a Sentry issue into a failing reproduction test using the project's own language and test framework.

The official Sentry MCP provides issue and event data. This skill explains how to inspect that data, identify the failing code path, sanitize a fixture, and write a test that reproduces the reported error. The bundled Python script handles deterministic fixture extraction and common PII masking; a separate MCP server is not needed.

## Repository layout

```text
sentry-repro/
├── SKILL.md
├── scripts/
│   └── event_to_fixture.py
├── references/
│   └── frameworks.md
├── README.md
└── examples/
```

## Requirements

- An agent environment that can use the official [Sentry MCP](https://github.com/getsentry/sentry-mcp). Without it, provide the event JSON or stack trace directly.
- Python 3 to run the sanitizer (standard library only).

## Install

Install from the existing GitHub repository:

```bash
npx skills add https://github.com/TELIDAS/sentry-to-test-reproduction --skill sentry-repro
```

Or copy `SKILL.md`, `scripts/`, and `references/` into your agent's skill directory.

## Usage

Ask your coding agent:

```text
Reproduce https://your-org.sentry.io/issues/4242/
```

Or provide the event directly:

```text
Write a failing reproduction test for this Sentry event, then stop: <event JSON>
```

The workflow follows the active agent's instructions (`CLAUDE.md`, `AGENTS.md`, or equivalent), then testing documentation, project configuration, and nearby tests. If no Markdown guidance exists, it infers the runner from manifests, scripts, dependencies, and source files. Python + pytest is the fallback only for an otherwise unidentified Python project; if language or runner is still unclear, it asks before writing a test. It stops after the failing reproduction unless you ask for a fix.

## Sanitize an event manually

The script accepts a Sentry event JSON file or standard input and prints a compact fixture:

```bash
python scripts/event_to_fixture.py /tmp/sentry-event.json > tests/fixtures/sentry_4242.json
cat /tmp/sentry-event.json | python scripts/event_to_fixture.py - > tests/fixtures/sentry_4242.json
```

Review generated fixtures before committing. The script masks common identity and credential fields, emails, IP addresses, authorization values, cookies, sensitive URL parameters, tokens, passwords, and secret-like strings, but automated masking can miss sensitive data. Never commit real raw events or credentials. The event under `examples/` is synthetic demonstration data.

## Privacy and security

- The sanitizer uses only Python's standard library, makes no network requests, and writes output to stdout. Data is persisted only where the caller redirects it.
- The skill sends event data through the configured Sentry MCP and coding-agent environment. This repository does not control their processing, retention, or training policies. Use production data only if your organization's policies approve those services.
- Grant the Sentry connection read-only access for reproduction work, and limit it to the needed organization/project where possible. The official Sentry MCP documents `org:read`, `project:read`, `team:read`, and `event:read` as minimum read-only scopes in its [server documentation](https://github.com/getsentry/sentry-mcp).
- Treat generated fixtures as sensitive until reviewed. Keep only fields needed by the test, verify `git diff` before committing, and do not assume `.gitignore` removes data already tracked or from Git history.
- For incidents involving regulated or highly sensitive data, use synthetic inputs or a locally approved workflow instead of sending event contents to an unapproved coding agent.

## Example

[`examples/python-keyerror`](examples/python-keyerror) contains a sample event, sanitized fixture, small application, and reproduction test. Run it from the example directory with:

```bash
pytest -q
```

The sample test fails with `KeyError: 'discount'`, matching the error in the sample event.

## License

MIT
