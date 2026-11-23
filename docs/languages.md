# Language notes

The rules are the same in every language. What changes is how each language
expresses a unit, a contract and a value, and how strongly it can enforce
them. Where a language cannot enforce a rule, write the rule down plainly and
rely on review and the build check.

| Concept | What it needs |
|---|---|
| Unit | Something that can hide its data and expose actions |
| Contract | Something that describes what a unit can do, without saying how |
| Value | Something that checks itself when created and never changes |
| No inheritance | A way to share behavior by composing, not extending |
| Custom error | The language's built-in exception type, extended once at most |

Folder and file casing follows the language, kept consistent across code,
views, `.css`, `.js` and `config/` files: bias toward `snake_case` in
module-based languages (Python, Rust, Go, and the language-neutral diagrams in
these docs) and toward `PascalCase` where namespaces and classes map 1:1 to
directories and files on disk (PHP with PSR-4, C#).

## PHP

- **Unit:** a `final class` with `private` properties.
- **Contract:** an `interface`. Implementations use `implements`, never `extends`.
- **Value:** a `final readonly class` that validates in its constructor.
- **Custom error:** PHP only throws `Throwable`s, and a class becomes one only
  by extending `\Exception` or `\Error` or one of their built-in children. A
  custom exception is a `final class` that extends one built-in exception
  (`\RuntimeException`, `\InvalidArgumentException`, `\DomainException`),
  never another custom exception. It is the one `extends` the check allows.
  Until a caller needs to catch a case on its own, throw a built-in exception
  with a clear message.
- **Traits:** they count as inheritance, so none in the core. A trait the
  framework requires (Symfony's `MicroKernelTrait` on the kernel) sits at the
  edge, listed in the check. Read tokens to find them: a `use` directly in a
  class body is a trait, while a closure's `use ($x)` sits deeper, inside a
  method.
- **Enforcement:** Deptrac, or a short script that reads `use` statements and
  PHP tokens and fails on any trait and any `extends` except a built-in
  exception parent (the example's `arch-check-inheritance.php`). Run PHPStan
  or Psalm in the same build, level 5 or higher.
- **Views:** Mustache is logic-less. Twig and Blade escape by default but
  allow logic, so keep it out by review. Plain PHP templates need no
  dependency and every PHP developer reads them, but they can run any code
  and every value must be escaped by hand, so one missed call is a security
  hole. If you choose them, keep them close to logic-less: a short escape
  helper on every value, loops and conditions only over values the feature
  already shaped, and a check in the build that fails when a template names an
  entity or renders another feature's view. Give each template's values a
  `@var` type so the static analyser reads them; an untyped value is a blind
  spot. A production app moved onto FIDES used plain PHP templates, and its
  one rendering regression was a template reading a field that no longer
  existed.
- **Config:** PHP has no built-in YAML parser. Use JSON, PHP arrays, or a
  small reader for the subset of YAML you allow.
- **Startup:** under PHP-FPM, PHP builds the app on every request, so "merged
  once at startup" means once per request. Merge settings when wiring runs and
  keep that one object for the rest of the request, as the example's
  `public/index.php` does. An edited override file then applies on the next
  request, with no cache to clear. A server that keeps the app in memory
  between requests (FrankenPHP worker mode, RoadRunner, Swoole) must rebuild
  or reset the settings object between requests, never during one. A
  framework that compiles configuration into a cache freezes it until the
  cache is cleared; see
  [frameworks.md](frameworks.md#settings-the-framework-compiles).
- **Naming:** PSR-4 maps namespaces and class names 1:1 to directories and
  files (`Entities/Technician/TechnicianStore.php`,
  `Features/ShowBoard/ShowBoard.php`). Keep `PascalCase` consistent across
  folders, classes, view templates, `.css`, `.js` and `config/` files
  (`ShowBoardView.php`, `ShowBoard.css`, `ShowBoard.js`, `Layout.css`,
  `Layout.js`) so the renderer and build check match every colocated file by
  folder name without mixing cases.

See [the PHP example app](../examples/todo-php), and the same app inside
Symfony with Doctrine and Twig ([todo-symfony](../examples/todo-symfony)).

## Python

- **Unit:** a class with underscore-prefixed attributes and read-only
  properties. Python cannot enforce privacy, so rule 1 relies on convention
  and review.
- **Contract:** `typing.Protocol`. Implementations match it by shape and do not
  inherit from it. A mixin is a base class, so the check refuses it like any
  other.
- **Value:** `@dataclass(frozen=True)` that checks itself in `__post_init__`.
- **Custom error:** Python only raises exceptions, so a custom error subclasses
  one built-in exception (`class CourseFull(ValueError)`), never another
  custom error. The example needs none: `ValueError` and `LookupError` with
  clear messages cover it.
- **Enforcement:** import-linter, or a short `ast` script (the example's
  `arch_check.py` is under 250 lines). Add mypy or pyright in strict mode.
- **Views:** `string.Template` is logic-less and in the standard library.
- **Web:** a plain WSGI function avoids subclassing a framework's handler.

See [the example app](../examples/course-enrollment).

## TypeScript and JavaScript (server side)

- **Unit:** a class with `#private` fields (truly private at runtime), or a
  module that exports only functions.
- **Contract:** an `interface`. TypeScript matches by shape, so implementations
  need no `extends` and no `implements`, though `implements` documents intent.
- **Value:** a class with `readonly` fields, frozen with `Object.freeze`.
- **Custom error:** JavaScript can throw any value, but only an `Error` carries
  a stack trace, so a custom error is `class CourseFull extends Error`, the one
  `extends` allowed. A class-factory mixin (`class Course extends
  Timestamped(Base)`) is an `extends` like any other, and is refused.
- **Enforcement:** dependency-cruiser or eslint-plugin-boundaries, plus
  `tsc --strict`.
- **Note:** FIDES fits the Node backend. For the browser app itself, see
  [why.md](why.md#where-it-fits).

## Java and Kotlin

- **Unit:** a `final` class (Kotlin classes are final by default) with
  `private` fields.
- **Contract:** an `interface`.
- **Value:** a `record` (Java) or `data class` (Kotlin) that checks itself in
  its constructor.
- **Custom error:** a `final` class that extends one built-in exception
  (`IllegalStateException`, `RuntimeException`), never another custom one.
- **Enforcement:** ArchUnit or Konsist. Stronger: one Gradle or Maven module
  per zone, so the compiler enforces the direction.
- **Frameworks:** organize packages by feature, not by layer. Keep framework
  annotations and base classes in delivery and integrations. A
  `TransactionTemplate` can fulfill the `UnitOfWork` contract.

## C\#

- **Unit:** a `sealed` class with `private` fields.
- **Contract:** an `interface`.
- **Value:** a `record` that validates in its constructor.
- **Custom error:** a `sealed` class that extends one built-in exception
  (`InvalidOperationException`), never another custom one.
- **Enforcement:** NetArchTest or ArchUnitNET, or one project per zone with
  project references pointing inward.

## Go

- **Unit:** a package. Unexported fields keep data private to the package.
- **Contract:** an `interface`. Go satisfies interfaces implicitly, which
  matches FIDES naturally.
- **Value:** a struct with unexported fields and a constructor function that
  validates.
- **No inheritance:** the language has none. Embedding is composition, but do
  not use it to imitate inheritance. Errors are values of any type with an
  `Error() string` method, so nothing is extended.
- **Enforcement:** `internal/` directories plus go-arch-lint.
- **Naming:** Go package names are short and lowercase (`course`, `enroll`).

## Rust

- **Unit:** a struct with private fields inside a module.
- **Contract:** a `trait`.
- **Value:** a struct with private fields and a constructor that returns a
  `Result`.
- **No inheritance:** the language has none. A custom error is a type that
  implements the `std::error::Error` trait, so nothing is extended.
- **Enforcement:** make each zone a crate in a workspace. Cargo will refuse a
  dependency that points the wrong way.
