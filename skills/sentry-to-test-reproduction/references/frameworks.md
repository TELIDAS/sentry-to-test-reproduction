# Language and test framework detection

Read this when CLAUDE.md does not say which framework to use. Pick by repo signals; if several match, prefer the one used by the module that contains the failing frame.

| Signal in repo | Language | Framework | Typical command |
|---|---|---|---|
| `pyproject.toml` / `pytest.ini` / `conftest.py` | Python | pytest | `pytest path/to/test.py -x -q` |
| `manage.py` + `tests.py` without pytest | Python | Django test runner | `python manage.py test app.tests.TestCase` |
| `package.json` with `jest` | JS/TS | Jest | `npx jest path/to/file.test.ts` |
| `package.json` with `vitest` | JS/TS | Vitest | `npx vitest run path/to/file.test.ts` |
| `go.mod` | Go | `go test` | `go test ./pkg/... -run TestIssue123` |
| `pom.xml` / `build.gradle` | Java/Kotlin | JUnit | `mvn -Dtest=ClassName test` / `gradle test --tests ClassName` |
| `Cargo.toml` | Rust | `cargo test` | `cargo test issue_123` |
| `Gemfile` with `rspec` | Ruby | RSpec | `bundle exec rspec spec/path_spec.rb` |
| `composer.json` with `phpunit` | PHP | PHPUnit | `vendor/bin/phpunit --filter Issue123` |
| `*.csproj` | C# | xUnit/NUnit | `dotnet test --filter Issue123` |

Default when nothing matches: Python + pytest, file `tests/test_issue_<id>_<short_description>.py`.
