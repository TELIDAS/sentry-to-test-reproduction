---
name: sentry-repro
description: Turn a Sentry issue into a failing reproduction test. Use when the user shares a Sentry issue URL or ID, an event or stack trace, or asks to reproduce a production error. Get event data through the official Sentry MCP, detect the project's language and test framework, sanitize event data, and write a test that reproduces the reported error. Do not fix the bug until the reproduction is verified.
---

# Sentry Repro

Create a test that reproduces the Sentry failure using the event's real inputs, with personally identifying information and secrets removed. The goal is a faithful failing test; a fix comes afterward.

## Workflow

1. **Get the event.** Use the connected official Sentry MCP to look up the issue from its URL or ID and fetch the relevant event. Gather the exception type and message, full stack trace, breadcrumbs, request method/URL/query/headers/body, tags, release, environment, and runtime details that are available. If Sentry MCP is unavailable, ask the user to provide the event JSON or stack trace and continue with that.
2. **Sanitize event data.** Never write the raw event into the repository. Prefer piping it to the script on standard input. If a temporary file is required, create it outside the repository with owner-only permissions, remove it immediately after sanitizing, and do not put event contents in shell history or logs:

   ```bash
   umask 077
   python /path/to/sentry-repro/scripts/event_to_fixture.py - < /private/temp/sentry-event.json > tests/fixtures/sentry_<issue-id>.json
   rm -f /private/temp/sentry-event.json
   ```

   Review the fixture before committing it. The script masks common PII and secrets, but cannot guarantee that every private value is detected. Remove fields that are unnecessary for reproducing the failure.
3. **Choose the language and test framework.** Follow applicable agent instructions first: `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex or other agents, including nested files near the affected code. Then check testing docs such as `TESTING.md`, `CONTRIBUTING.md`, and `README.md`; then project test/build configuration and package scripts; then nearby existing tests. Use `references/frameworks.md` to interpret repository signals. Prefer the runner used by the code around the failing frame. Resolve conflicting instructions by scope and proximity; if they remain ambiguous, report the conflict instead of guessing. If no Markdown instructions exist, infer from config files, dependencies, scripts, source language, and existing tests. Use pytest only when the project is Python and no test framework can be identified. If the language or runner remains unclear, ask before creating a test.
4. **Trace the failing path.** Read the in-app stack frames and follow the event inputs into the affected code. Do not assume the cause; reproduce the observed behavior first.
5. **Write the test.** Follow the repository's existing test style. Use the sanitized event inputs, name the test `test_issue_<id>_<short_description>`, and include the Sentry issue link when available. Assert the intended correct behavior so the test fails on the current bug. Mock external boundaries only when needed; keep the failing application logic real.
6. **Verify the reproduction.** Run the narrowest project-appropriate test command. Confirm that it fails with the same exception type and message reported by Sentry. If the result differs or passes, compare input types, missing fields, ordering, runtime and release details; adjust the reproduction only when supported by the event. Do not weaken assertions just to make a test fail. If it cannot be reproduced, report what was tried and what information or conditions appear to be missing.
7. **Report and stop.** Give the test path, command, observed failure, comparison with the Sentry error, and any assumptions. Do not fix the bug unless the user asks. If asked to fix it, make the smallest suitable change and keep the reproduction as a regression test; hand off to `fix-sentry-issues` when that skill is available.

## Safety and quality

- A test that passes before the fix is not a reproduction.
- Do not commit raw Sentry events, credentials, or unreviewed request bodies.
- Preserve useful neighboring cases when they clarify the boundary of the bug.
- If the available event omits data required for a faithful test, state that instead of inventing it.
