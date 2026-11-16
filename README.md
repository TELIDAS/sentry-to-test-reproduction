# sentry-to-test-reproduction

Claude Code skill that turns a Sentry error into a **failing reproduction test**, using real (sanitized) event data and the project's own test framework: `CLAUDE.md` first, repo signals second, **pytest by default**.

The skill does not fix the bug until the failure is reproduced. When you ask for a fix, the test becomes the regression test.

## How it works

1. Fetches the issue and latest event through the [Sentry MCP](https://github.com/getsentry/sentry-mcp): stack trace, breadcrumbs, request data, tags, release.
2. Sanitizes the event with `scripts/event_to_fixture.py` (emails, IPs, auth headers, cookies, tokens, passwords are masked).
3. Detects language and test framework: `CLAUDE.md` -> repo signals -> Python + pytest.
4. Writes `test_issue_<id>_<description>` with the exact inputs from the event and checks that it fails with the **same error** as in Sentry.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Sentry MCP connected:
  ```bash
  claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
  ```
  Without it, paste the event JSON into the chat and the skill continues from the sanitize step.
- Python 3 (for the sanitizer script, standard library only)

## Install

```bash
npx skills add https://github.com/<your-username>/sentry-to-test-reproduction --skill sentry-to-test-reproduction
```

Or manually:

```bash
git clone https://github.com/<your-username>/sentry-to-test-reproduction
cp -r sentry-to-test-reproduction/skills/sentry-to-test-reproduction ~/.claude/skills/
```

## Usage

```
Reproduce https://your-org.sentry.io/issues/4242/
```

```
Write a failing test for this Sentry error, then stop: <pasted stack trace>
```

To pin the framework, add a line to your project's `CLAUDE.md`:

```
Tests: pytest, files in tests/, run with `pytest -x -q`.
```

## Example

[`examples/python-keyerror`](examples/python-keyerror): a raw event, its sanitized fixture, a tiny app and the generated failing test.

```bash
python skills/sentry-to-test-reproduction/scripts/event_to_fixture.py examples/python-keyerror/event.json
cd examples/python-keyerror && pytest -q   # fails with KeyError: 'discount', as in Sentry
```

## Privacy

Sentry events contain user data. The sanitizer masks common PII and secrets, but **review fixtures before committing** and never commit raw events or tokens.

## License

MIT
