# sentry-repro

An agent skill that turns a Sentry issue into a failing reproduction test using the project's own language and test framework.

The official Sentry MCP provides issue and event data. The skill writes the reproduction in the language and test stack used by the affected project, including frontend and native mobile projects. The bundled Python script is only an optional language-independent event-fixture sanitizer; it is not the test framework default, and no extra MCP server is needed for sanitization.

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

- Python 3 to run the sanitizer (standard library only).
- The official [Sentry MCP](https://github.com/getsentry/sentry-mcp) connected in your coding-agent environment. The skill uses that existing connection; installing the skill does not configure MCP. If MCP is unavailable, it tells you instead of claiming it fetched an issue.

## Install

Install into any supported coding agent with the `skills` CLI. It detects installed agents and lets you choose where to install. Node.js 22.20 or later is required by the current CLI.

```bash
npx skills add https://github.com/TELIDAS/sentry-to-test-reproduction --skill sentry-repro
```

To install into Claude Code and Codex project directories directly:

```bash
npx skills add https://github.com/TELIDAS/sentry-to-test-reproduction --skill sentry-repro -a claude-code -a codex
```

The same `SKILL.md` works across supported agents, including Claude Code, Codex, Cursor, and others. You can also use `-g` for user-wide installation. See the [`skills` CLI supported agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) for current agents and install paths. Configure the Sentry MCP separately in each agent where you want the skill to fetch issues; installing a skill does not create an MCP connection.

## Usage

Ask your coding agent:

```text
Reproduce https://your-org.sentry.io/issues/4242/
```

Or provide an already sanitized event, if your data policy permits:

```text
Write a failing reproduction test for this sanitized Sentry event, then stop: <sanitized event>
```

The skill fetches event data through the existing Sentry MCP connection, follows the project's test conventions, and stops after verifying the failing reproduction unless you ask for a fix.

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
