# FIDES Architecture

**Every unit keeps its word.**

FIDES is a way to structure software so it stays simple, readable and
encapsulated, for the people who write it and for the AI agents that help
them. It works in any programming language.

> **Status:** draft 0.3. The rules are being tested against real apps and
> will change. See [CHANGELOG.md](CHANGELOG.md) for what changed and why.

## The problem

Most codebases are organized by kind of code: controllers in one folder,
services in another, then repositories, implementations, DTOs, mappers,
events, listeners and templates. To understand one thing, like "enroll a
student", you open a dozen folders. Inheritance chains add more places to
look. Frameworks pull every project toward that scattered shape, and AI agents
copy whatever shape they find.

FIDES organizes code by what it does and who owns it, keeps each concept in
one place, and enforces a short list of rules with an automated check.

## The idea in one minute

- **One concept, one place.** A use case lives in one folder: its logic, its
  views, its CSS and JS. A page in delivery places those views; it does not
  own them.
- **One owner.** Every piece of data has exactly one owner, and only the owner
  changes it.
- **Dependencies point inward,** toward the rules that are true everywhere.
  The outside world stays at the edges.
- **No inheritance.** Small units are composed, never extended.
- **Rules are required, tools are examples.** FIDES says what must be true,
  not which library to use. It is an approach, not a framework: it fits
  inside the framework you already use.

**The test:** a new developer, or an AI agent, understands any feature in
five minutes, and you can come back after six months and find your way.

## The five zones

| Zone | Holds | Example |
|---|---|---|
| **F**eatures | one use case per folder, with its view and assets | `features/enroll/` |
| **I**ntegrations | how the app reaches the world: database, email, clock | `integrations/database/` |
| **D**elivery | how the world reaches the app: web, API, CLI, worker | `delivery/web/` |
| **E**ntities | the rules that are true everywhere | `entities/course/` |
| **S**hared | contracts that no single entity owns | `shared/unit_of_work` |

Outside `src/`, a `config/` folder holds the setting overrides that belong to
whoever runs the app. Where a framework already uses `config/` for its own
files, the overrides get a folder of their own
([docs/frameworks.md](docs/frameworks.md#the-config-folder)).

*Fides* is also Latin for good faith: keeping your word. Every unit promises
something through its contract and keeps that promise. The acronym is a memory
aid, not a constraint. If a zone is ever added or renamed, the name stays.
(FIDES is unrelated to Ethyca's Fides privacy platform.)

## The shape

```
AGENTS.md            # the rules on one page, for AI agents and people
config/              # overrides only, one file per owner
docs/decisions/      # decisions no unit in src/ owns, one short file each
src/
  shared/            # ownerless contracts: UnitOfWork, Clock, Mailer, MessageBus
    class_roster/    # a read model: a read-only query across entities
  entities/
    course/          # Course, its values, messages, settings, store contract
    student/
  features/
    enroll/          # the use case, its view, its feature-specific CSS and JS
    transfer/
  integrations/
    database/        # fulfills the store contracts
    email/
  delivery/
    web/             # layout (with global CSS and JS), routes, and one folder per page
      courses/       # page code, page template, and page-specific CSS and JS
    cli/  worker/
    wiring           # the only file that knows integrations exist
```

Dependencies point one way. Delivery uses features, features use entities,
integrations fulfill the contracts entities and shared declare, and only
wiring sees integrations. Folder and file names stay flexible to match your
language — bias toward `snake_case` in module-based languages (as shown above)
or `PascalCase` where namespaces and classes map 1:1 to folders and files (as
in PSR-4 PHP and C#) — and keep that choice consistent across folders, code,
views, `.css`, `.js` and `config/`.

## Where FIDES fits

**Good fit**
- Server-side web apps and APIs
- Monoliths and modular monoliths with a database
- The backend behind a single-page or mobile app
- CLIs and background workers that share rules with a web app
- One service inside a larger system
- Apps built on a framework (Symfony, Laravel, Rails, Django, Spring,
  ASP.NET Core): the zones map onto the framework instead of replacing it

**Poor fit**
- The single-page app itself (React, Vue, Svelte) and other rich clients
  such as mobile and desktop apps. Client code is mostly component state and
  rendering, its frameworks bring their own structure, and FIDES ideas like
  stores, transactions and an outbox have nothing to attach to. Feature
  folders and composition over inheritance still carry over.
- Libraries and SDKs, small scripts, data pipelines and game engines.

More in [docs/why.md](docs/why.md).

## Read more

1. [Why FIDES](docs/why.md): goals, fit, costs and prior art
2. [Structure](docs/structure.md): the zones, imports and spread
3. [Rules](docs/rules.md): every rule, with its reason
4. [Changes and messages](docs/changes.md): transactions, the outbox, concurrency
5. [Configuration](docs/configuration.md): defaults, overrides, environment
6. [Working with AI](docs/ai.md): AGENTS.md, the build check, reading order;
   [keeping AGENTS.md in sync](agents/README.md) across repositories
7. [Comments and decisions](docs/comments.md): the file header, what a comment
   says, and decision records
8. [Language notes](docs/languages.md): FIDES in PHP, Python, TypeScript, Java,
   C#, Go and Rust
9. [Moving an existing app](docs/migrating.md): change the structure and prove
   nothing else changed
10. [Inside a framework](docs/frameworks.md): containers, `config/`, compiled
    settings and base classes in Symfony, Laravel, Rails, Spring and others

## Examples

[examples/course-enrollment](examples/course-enrollment) is a small Python app
(standard library only) where students enroll in, drop and transfer between
courses. It shows every rule in working code, with 39 tests, an architecture
check, and a type check when mypy is installed.

```bash
cd examples/course-enrollment
python3 run_tests.py          # architecture check, type check, tests
python3 app.py serve          # http://127.0.0.1:8080
```

[examples/todo-php](examples/todo-php) is a very small to-do app in plain PHP
with no dependencies. [examples/todo-symfony](examples/todo-symfony) is the
same app inside Symfony 7.4 with Doctrine ORM and Twig: its entities and
features are the plain PHP example's, byte for byte, and only integrations,
delivery and templates change.

## Contributing

The most useful contribution is a real case where a rule got in the way. Open
an issue with the code, the rule and what you did instead.

---

AI transparency: Co-created by the author and AI.
