# Language and test framework detection

Use this after checking the applicable agent instructions, testing docs, and nearby tests. Pick by repository signals; if several match, prefer the runner used by the module containing the failing frame.

| Signal near the failing code | Project type | Likely test stack |
|---|---|---|
| `package.json` scripts/dependencies and nearby tests | Web frontend (React, Vue, Angular, Svelte, etc.) | Use the configured Jest, Vitest, Testing Library, Playwright, Cypress, or project runner; follow package scripts |
| `package.json` with React Native | React Native mobile | Use the existing Jest/component setup; use Detox or another configured device runner only when the bug requires it |
| `Package.swift`, `.xcodeproj`, or `.xcworkspace` | Swift / native iOS | XCTest; derive scheme and destination from project/CI configuration |
| `.xcodeproj` or `.xcworkspace` with Objective-C sources | Objective-C / native iOS | XCTest; follow existing target and scheme |
| `build.gradle` / `build.gradle.kts` with Android sources | Kotlin or Java / native Android | Existing JUnit, Robolectric, or instrumentation setup; use the matching Gradle task |
| `pubspec.yaml` | Dart / Flutter | `flutter test` and existing widget/unit conventions |
| `pyproject.toml` with pytest config/dependency, `pytest.ini`, `setup.cfg`, `tox.ini`, or `conftest.py` | Python | pytest |
| Existing `unittest.TestCase` tests and no pytest configuration | Python | unittest |
| `manage.py` + Django tests without pytest | Python / Django | Django test runner |
| `go.mod` | Go | `go test` |
| `pom.xml` / `build.gradle` with JVM tests | Java / Kotlin | Existing JUnit or project-configured runner |
| `Cargo.toml` | Rust | `cargo test` |
| `Gemfile` with RSpec | Ruby | RSpec |
| `composer.json` with PHPUnit | PHP | PHPUnit |
| `*.csproj` | C# | Existing xUnit/NUnit/MSTest setup via `dotnet test` |
| `CMakeLists.txt` / `CTestTestfile.cmake` | C / C++ | Existing GoogleTest, Catch2, or CTest setup |

Read commands from repository scripts and CI when possible; do not assume a global CLI or run a root-level command in a monorepo when the affected package has its own runner. A Sentry platform label is a clue, not proof: confirm the language from the stack frame and source. If no test runner is configured, follow the ecosystem's existing conventions; if none are recognizable, ask rather than defaulting to Python. Native mobile tests may require a simulator, emulator, or device; report that constraint if unavailable.

The Python sanitizer is a language-independent helper for Sentry JSON. It does not determine the language or framework used for the reproduction test.
