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

Install from the GitHub repository after its name is set to `sentry-repro`:

```bash
npx skills add https://github.com/TELIDAS/sentry-repro --skill sentry-repro
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

The workflow uses `CLAUDE.md` first, repository signals second, and Python + pytest if no framework can be identified. It stops after the failing reproduction unless you ask for a fix.

## Sanitize an event manually

The script accepts a Sentry event JSON file or standard input and prints a compact fixture:

```bash
python scripts/event_to_fixture.py /tmp/sentry-event.json > tests/fixtures/sentry_4242.json
cat /tmp/sentry-event.json | python scripts/event_to_fixture.py - > tests/fixtures/sentry_4242.json
```

Review generated fixtures before committing. The script masks common emails, IP addresses, authorization values, cookies, tokens, passwords, and secret-like strings, but automated masking can miss sensitive data. Never commit raw events or credentials.

## Example

[`examples/python-keyerror`](examples/python-keyerror) contains a sample event, sanitized fixture, small application, and reproduction test. Run it from the example directory with:

```bash
pytest -q
```

The sample test fails with `KeyError: 'discount'`, matching the error in the sample event.

## License

MIT
