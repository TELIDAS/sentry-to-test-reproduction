# Language and test framework detection

Use this after checking the applicable agent instructions, testing docs, and nearby tests. Pick by repository signals; if several match, prefer the runner used by the module containing the failing frame.

| Signal in repo | Language | Framework | Typical command |
|---|---|---|---|
| `pyproject.toml` with pytest config/dependency, `pytest.ini`, `setup.cfg`, `tox.ini`, or `conftest.py` | Python | pytest | `pytest path/to/test.py -x -q` |
| Existing `unittest.TestCase` tests and no pytest configuration | Python | unittest | `python -m unittest path.to.test_module` |
| `manage.py` + `tests.py` without pytest | Python | Django test runner | `python manage.py test app.tests.TestCase` |
| `package.json` with `jest` | JS/TS | Jest | `npx jest path/to/file.test.ts` |
| `package.json` with `vitest` | JS/TS | Vitest | `npx vitest run path/to/file.test.ts` |
| `go.mod` | Go | `go test` | `go test ./pkg/... -run TestIssue123` |
| `pom.xml` / `build.gradle` | Java/Kotlin | JUnit | `mvn -Dtest=ClassName test` / `gradle test --tests ClassName` |
| `Cargo.toml` | Rust | `cargo test` | `cargo test issue_123` |
| `Gemfile` with `rspec` | Ruby | RSpec | `bundle exec rspec spec/path_spec.rb` |
| `composer.json` with `phpunit` | PHP | PHPUnit | `vendor/bin/phpunit --filter Issue123` |
| `*.csproj` | C# | xUnit/NUnit | `dotnet test --filter Issue123` |

If no signal matches, identify the language from the failing source and inspect its manifests, scripts, dependencies, and neighboring tests. Use pytest as the final fallback only for a Python project. For a non-Python project or unresolved ambiguity, ask the user which runner to use rather than creating a test in an arbitrary framework.
