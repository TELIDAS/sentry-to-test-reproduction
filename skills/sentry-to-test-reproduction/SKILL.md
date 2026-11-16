---
name: sentry-to-test-reproduction
description: Turn a Sentry issue into a failing reproduction test. Use whenever the user shares a Sentry issue URL or ID, pastes a Sentry event or stack trace, or asks to reproduce, write a test for, or add a regression test for a production error, even if they don't say "Sentry" explicitly. Pulls the stack trace, breadcrumbs, request data and tags via the Sentry MCP, detects the project's language and test framework from CLAUDE.md and the repo (defaulting to pytest), and writes a test that fails with the same error using real, sanitized event data. Does not fix the bug until the failure is reproduced.
---

# Sentry to Test Reproduction

Goal: a **failing test that reproduces the Sentry error with real event data**. Fixing comes after, never before.

## Requirements

- Sentry MCP connected (`claude mcp add --transport http sentry https://mcp.sentry.dev/mcp`). If unavailable, ask the user to paste the event JSON and continue from step 2.
- Access to the repository where the error occurs.

## Workflow

### 1. Fetch the event
Use the Sentry MCP to get the issue and its latest event (or a specific event if the user gave one). Collect:
- exception type and message
- full stack trace, with in-app frames marked
- request data (URL, method, headers, body, query)
- breadcrumbs, tags, release, environment, user-agent/runtime info

### 2. Sanitize
Event data contains PII. Save the raw event to a temp file and run:

```bash
python scripts/event_to_fixture.py event.json > tests/fixtures/sentry_<issue-id>.json
```

The script masks emails, IPs, auth headers, cookies, tokens, passwords and secrets, and keeps only what a test needs. Never commit raw events. Never put tokens in the repo.

### 3. Detect language and test framework
Check in this order, stop at the first clear answer:
1. `CLAUDE.md` (and any nested CLAUDE.md near the failing file): test command, framework, directory, naming rules.
2. Repo signals: see `references/frameworks.md`.
3. Nothing found: **default to Python + pytest**, tests in `tests/`.

Follow the project's existing test style (naming, fixtures, assertions, imports). Read one or two existing tests first.

### 4. Understand the failing path
Read every in-app frame of the stack trace. Trace what data reaches the failing function upstream. Do not guess a cause yet; the aim is a faithful reproduction.

### 5. Write the failing test
- Use the exact inputs from the event (sanitized), not simplified ones.
- Name it after the issue: `test_issue_<id>_<short_description>`, with a comment linking the Sentry issue.
- Assert the **expected correct behavior**, so the test fails today with the same exception type and message as in Sentry.
- If the error needs external services, mock only the boundary, not the failing logic.

### 6. Verify the reproduction
Run the test with the project's command. It must fail with the **same error** as the event. If it fails differently or passes:
- compare against the event again (types, missing keys, ordering, env/runtime version);
- adjust the test, not the story. Do not weaken assertions to force a failure.
If it truly cannot be reproduced, say so and list what was tried and which conditions seem missing (data volume, concurrency, environment, version).

### 7. Report
Give the user: test file path, the command to run it, the observed failure vs the Sentry error, and any assumptions. Stop here unless asked to fix. When asked to fix, make the minimal fix so this test passes and keep the test as a regression test.

## Rules
- A reproduction test that passes before the fix is not a reproduction.
- Keep all variants that were useful (failing and passing neighbors); they document the boundary.
- Never leave raw PII, tokens or full request bodies in committed files.
