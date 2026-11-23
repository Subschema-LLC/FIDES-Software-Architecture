# Changelog

## Unreleased

### Rules

- **Rule 16, small and shallow,** allows feature groups:
  `features/<group>/<use_case>/file`. A group is named for the area people
  look for (usually a screen or menu entry), holds no code, and leaves the use
  case as the owner, so features in one group still never call each other.
  Groups are optional; once a project uses them, every feature sits in one.
  Found while porting the alerts area of a Symfony app, where nine features
  under one flat folder were hard to browse.
- **Rule 19, explanations sit with what they explain** (new). Every code file
  opens with a header saying what it does and why. Comments say why, and what
  is true now. A decision no unit owns gets a short record in
  `docs/decisions/`, named in code as `Decision: <name>`, never by number.
  A TODO names its issue. The one-page rules had "comments say what is true
  now" as rule 13 with no counterpart in `rules.md`; this is that rule, grown.
- **Rule 16, small and shallow,** makes the file size limit two-tier: aim for
  200 code lines, the check warns past 200 and fails past 300. It counts code
  lines only, leaving out blank lines, comments and docstrings. The rule said
  "about 200" while both checkers failed at exactly 200 and counted every line,
  which pushed people and agents to cut comments to pass. Research on file size
  and defects does not support one exact number, so the hard limit has room
  and the warning starts the conversation. `structure.md` gives the test for
  a file past 200: split out any concept you can name; keep it whole only when
  one name covers it and a split would leave `part1`, `helpers` or files that
  import each other, and say why in the change. The `AGENTS.md` template and
  both examples tell agents the same, and the warning text repeats it.

### Docs

- `structure.md`: a section on feature groups, the depth exception, and a
  glossary entry. `ai.md`: the one-page rules mention groups.
- The example checkers still require `features/<use_case>/file`. The examples
  are small and use no groups, and a stricter checker is still a correct one.
- `comments.md` (new): where each explanation goes, the file header, comments
  in code, decision records that keep only what is true now, and why this
  suits agents. `README.md`, `structure.md` and `ai.md` point to it, and the
  `AGENTS.md` template's rule 13 says the same in brief.

### Examples

- The Python example's checker requires a docstring in every file, checks
  that every `Decision: <name>` and every `docs/` path a comment names exists,
  and requires an issue on every TODO. It has one decision record,
  `standard_library_only.md`.
- Its zone files pointed at `docs/02-zones.md`, which does not exist. The new
  check caught all five; they now say what their zone may import.
- The PHP examples do not check comments yet.
- Both example checkers warn past 200 code lines and fail past 300, with
  tests for each tier. The PHP example's `AGENTS.md` now states the size rule.

## 0.3 (2026-11-17)

Findings from mapping a Symfony 7.4 app (about 450 PHP files, a DI container,
YAML settings edited from an admin screen) onto FIDES, and from an outside
review of draft 0.2. FIDES is an approach, not a framework, and this release
says how it fits inside one.

### Rules

- **Rule 3, entities stand alone,** points reads that span entities to a
  read model: a read-only query contract in `shared/<read_model>/`, fulfilled
  by an integration with one query.
- **Rule 8, no inheritance,** allows one more `extends`, in every zone: a
  custom error extending one built-in exception type, where an error has to
  extend it to be thrown or to carry a stack trace (PHP, Python, Java, C#,
  JavaScript). Never one custom error extending another. Code mixed into a
  class (PHP traits, mixins) counts as inheritance: none in the core, and a
  framework-required one stays at the edge.
- **Rule 11, settings,** defines "once at startup": once per process for a
  long-running server, once per request where the runtime builds the app for
  each request, as PHP usually does. Settings stay frozen for each unit of
  work.
- **Rule 16, small and shallow,** says a split names its concept, and lets a
  data file (a lookup table, generated code) skip the size limits when the
  checker lists it with its reason. Logic never does.
- **Rule 17, rules are required, tools are examples,** says to keep a
  framework's conventions and map the zones onto them.

### Docs

- `frameworks.md` (new): where a framework's pieces go, what stays explicit
  with a dependency-injection container, the clash over `config/`, settings a
  framework compiles into a cache, ORMs without associations between entities
  (foreign keys stay in the schema), template inheritance kept inside
  delivery, base classes and traits, and moving in a piece at a time.
- `structure.md`: read models (two entities or more, read-only, pure data,
  one query, used by features), size exemptions, new glossary term.
- `configuration.md`: what startup means for each runtime, and settings
  edited through the app.
- `languages.md`: custom errors in every language, traits and mixins, and
  what startup means in PHP.
- `why.md`, `ai.md`, `README.md`: wiring with a container, the `config/`
  pointer, the exception allowance, read models as a cost and in the AGENTS.md
  template, frameworks as a good fit.

### Examples

- The Python example has a read model, `shared/class_roster/`, answered by
  one SQLite join and read by a new `list_roster` feature (`python3 app.py
  roster`).
- Both architecture checks allow a custom error extending one built-in
  exception and still fail on any other parent. The PHP check moved its
  inheritance part to `arch-check-inheritance.php`, which reads PHP tokens and
  also fails on traits. `arch-check.php` takes a folder to check, so a new
  test runs it on a throwaway tree of rule breaks.
- `arch_check.py` has a `SIZE_EXEMPT` list, empty in this app, with a test.
- **New example, `todo-symfony`:** the PHP to-do app inside Symfony 7.4 with
  Doctrine ORM and Twig. Its entities, feature use cases and `Clock` are the
  PHP example's byte for byte, and its tests check that. It shows wiring in
  one container file (checked: every contract bound), Doctrine mapping on a
  record class in integrations, Twig feature views as fragments under an
  `@Features` namespace, plain controllers, invokable commands, the kernel
  as the one listed edge exception, `overrides/` beside Symfony's `config/`,
  and settings built per request. 19 tests plus the architecture check.
- Three comments in the PHP example's core no longer name `.php` view files
  or `config/`, so the same core reads true inside Symfony.
- Test counts: 38 in the Python example (from 34), 23 plus the architecture
  check in the PHP example (its README said 21).

### What the app taught

- **PHP cannot follow "no inheritance" to the letter.** A class can only be
  thrown if it extends a built-in exception. The Python example never defined
  a custom error, so the rule never met the case.
- **"Startup" means different things.** Under PHP-FPM the app starts on every
  request, which is what lets an admin screen's edit apply without a cache
  clear.
- **A container is the wiring, but not a readable one.** Autowiring hides
  which integration fulfills a contract, so the bindings need one file.
- **`config/` already has an owner.** Symfony, Laravel and Rails put code-owned
  configuration there. The rule is about ownership, not the folder name.
- **Reads were the gap.** An analytics app is mostly reads across entities.
  Read rows covered one entity's lists, and nothing had a place for a join.

## 0.2 (2026-11-13)

Findings from moving a production PHP app onto FIDES: about 30 features,
16 web pages and 46 form actions, with plain PHP templates and MariaDB. Every
page, form action, layout and script was compared against the running
version before and after each step.

### Rules

- **Rule 13, views only display,** now says where shaping happens (in the
  feature's code, where tests and the type checker see it) and that a
  template never names an entity. It is checkable when templates can run
  code.
- **New rule 14, pages compose features.** One folder per page in delivery. A
  page template places feature views. A feature's view never renders another
  feature's view. A form belongs to the feature that handles it, and the page
  hands one feature's form into another feature's area as a slot. CSS and JS
  follow three owners: global frame assets with the layout, feature-specific
  assets in the feature folder, and page-specific assets in the page folder,
  loaded in that order when views render.
- Rules 14 to 17 are now 15 to 18.
- **Rule 16, small and shallow,** allows one extra level for pages:
  `delivery/web/<page>/file`.
- **Rule 17, rules are required, tools are examples,** recommends picking
  either `snake_case` (module-based languages) or `PascalCase` (where
  namespaces and classes map 1:1 to folders and files) and keeping that single
  casing consistent across folders, code, views, `.css`, `.js` and `config/`.
- **Rule 18, enforce mechanically,** now includes the language's type checker.

### Docs

- `structure.md`: a Pages section (folders, slots, one-button actions, three
  levels of CSS and JS across layout, features and page folders, and render
  order), `snake_case` vs. `PascalCase` consistency across folders and
  colocated files, typed read rows beside the store contract, one way to talk
  to each system per integration, new glossary terms.
- `migrating.md` (new): moving an existing app and proving nothing changed.
- `ai.md`: page rules and "comments say what is true now" in the AGENTS.md
  template; add the checks on day one; prompting tips.
- `languages.md`: `snake_case` and `PascalCase` naming guidance (including
  PSR-4 `PascalCase` in PHP), what plain PHP templates need, and a type
  checker for PHP, Python and TypeScript.
- `why.md`: the cost that a screen is now two places.

### Example

- The home page is now a page folder, `delivery/web/courses/`, with its own
  code and template.
- A `Renderer` loads each feature's CSS when its view renders, replacing the
  hand-written stylesheet list.
- `arch_check.py` checks page folders and the delivery depth exception.
- `run_tests.py` runs mypy in strict mode over `src/` when it is installed.
  Two type errors it found are fixed.
- Three web tests and three new checker cases (34 tests, from 31).

### What the app taught

- **Unchecked rules drift.** The size limits were written down and never
  checked. About 2,000 lines of PHP ran past 100 characters, and nine files
  ran past 200 lines, the largest a 1,217-line global stylesheet.
- **A type checker earns its place on the first run.** It found a flash
  message printing an undefined variable and a redirect that could never run.
- **Templates that can run code need checks, not trust.** The one rendering
  regression was a template reading a field that no longer existed. Shaping
  values in typed feature code, and an integration test for that state,
  closed it.
- **Page-sized templates hide owners.** The first template pass gave each page
  one big template. Splitting it into feature views put each form's markup
  beside the code that handles it, and left the page template a short list of
  what is on the page.
- **Comments drift toward history.** Notes about the move ("replaces the old
  function", "phase 2") had to be removed once it was done.

## 0.1

First draft: five zones, seventeen rules, a Python example.
