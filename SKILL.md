---
name: sentry-repro
description: Reproduce a Sentry issue as a failing test. Use for Sentry issue links or IDs, event data, and requests to reproduce production errors or add regression tests.
---

# Sentry Repro

Turn a Sentry failure into a focused failing test in the affected project's language and test stack. Python is used only by the optional fixture-sanitizer script; it is never the default language for the reproduced test. Do not fix the bug unless the user asks.

1. **Use the connected Sentry MCP.** Look up the issue and relevant event; retrieve only details needed to understand the failure. If Sentry MCP is unavailable or access is denied, tell the user plainly and stop. Do not imply the issue was fetched. Do not ask for a raw production event by default.
2. **Choose the project's test conventions.** Use the language and module at the failing in-app frame. Follow the active agent's instructions (`CLAUDE.md`, `AGENTS.md`, or equivalent), then testing docs, project configuration, and nearby tests. In monorepos, use the nearest package/module configuration. With no Markdown guidance, infer from manifests, scripts, dependencies, source language, and existing tests; see `references/frameworks.md`. Use pytest only as a last fallback when the affected project code is Python. If the language or runner is still unclear, ask before writing a test.
3. **Create the reproduction.** Trace the in-app frames, use the event's relevant inputs, and follow the existing test style. Keep the failing application logic real; mock only external boundaries. Sanitize values before persisting them. Never put a raw event in the repository. Use `scripts/event_to_fixture.py` when a fixture is needed, and review it before saving.
4. **Verify and report.** Run the narrowest relevant test. Confirm it fails with the same exception type and message as Sentry. If it does not, report the mismatch and assumptions; do not force a failure. Report the test path and command, then stop. If the user asks for a fix, keep the reproduction as a regression test.

## Privacy boundary

The sanitizer masks common PII and secrets but cannot guarantee complete redaction. The connected Sentry MCP and coding agent also process event data; this skill cannot control their retention or data policies. Never promise 100% security. If the user's policy does not approve those services for production event data, do not retrieve or process that data.
