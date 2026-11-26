# Structure

## The zones

Every file in `src/` belongs to exactly one zone. The zone decides what the
file may hold and what it may import.

### Entities

The rules that are true everywhere, grouped by the concept that owns them.
One folder per entity holds:

- the **entity** itself: identity plus actions that enforce its rules
- its **values**: small immutable things that check themselves (`Email`, `Seats`)
- its **messages**: records of what happened (`StudentEnrolled`)
- its **settings**: every tunable value, with its default and its rules
- its **store contract**: what the app needs in order to find and save it
- its **read rows**, if a store returns some: small typed, read-only records
  for lists and screens that do not need the whole entity. Never a raw array
  or dictionary from the database driver, so the type checker sees every
  field a feature reads.

An entity imports only its own folder. It refers to other entities by
identity (an id or key), never by holding them.

### Features

One use case per folder, named as an action: `enroll`, `transfer`,
`list_courses`. The folder holds the use case, plus its views and any
feature-specific CSS and JS if it shows anything. The use case reads top to
bottom. A feature with a view also shapes the plain values that view prints.

Features import entities and shared. They never import another feature,
an integration or delivery. Rules that involve two entities ("an inactive
student cannot enroll") live here, because neither entity owns them.

Some features react to messages instead of to people
(`send_enrollment_confirmation` reacts to `StudentEnrolled`).

#### Feature groups

A flat list of action folders is easy to scan at ten features and hard at
forty. A project may then group its features by area, one level deeper:

```
features/
  alerts/                 # a group: the area people look for
    save_alert_rule/      # the owner: one use case, as before
    deliver_alert/
  billing/
    send_invoice/
```

- **Name the group for the area people look for,** usually the screen or menu
  entry the features are reached from, so a person or an AI agent can go
  straight from what they see in the app to the code.
- **A group is only a folder.** It holds no files of its own, nothing shared
  between its features, and no rules. Code two features need belongs in an
  entity or in shared, exactly as without groups.
- **The use case stays the owner.** Features in one group still never import
  each other, and the checker treats `features/<group>/<use_case>/` as the
  owner.
- **All or nothing.** Groups are optional, but once a project uses them, every
  feature sits in one, so a reader never has to guess which shape a folder
  has. Start with one group per area, and split a group only when another
  area starts using some of its features.
- **Entities, shared and integrations do not group.** They stay at
  `zone/owner/file`; an entity is already one concept.

### Shared

Contracts that no single entity owns: `UnitOfWork`, `Clock`, `Mailer`,
`MessageBus`, plus ownerless settings (`AppSettings`) and read models.
Contracts and small values only, never logic, or it turns into a junk drawer.
Shared imports nothing else from the app.

#### Read models

Some screens need several entities at once: a roster of students per course,
an invoice with its client, time entries and payments. No entity owns that
view, and entities never hold each other, so the read gets a contract of its
own, a **read model**, in a folder of its own in shared:

```
shared/class_roster/
  class_roster        # the query contract and its typed, read-only rows
integrations/database/
  class_roster        # fulfills it with one query: a join or a database view
features/list_roster/
  list_roster         # asks the read model and shapes the rows for its view
```

- **Two entities or more.** A read model joins or aggregates across at least
  two entities. A list of one entity is not a read model: that entity's store
  returns read rows (see Entities).
- **It only reads.** Every change still goes through the owning entity and its
  store, so the rules stay in one place.
- **Pure data.** The folder holds the query contract and its immutable rows,
  nothing else: no sorting or filtering helpers, no formatting. Rows hold
  plain values (text, numbers, dates, ids), never entities, so shared still
  imports nothing else from the app.
- **One query behind it.** The integration answers with a join or a database
  view, never a loop that loads entities one by one.
- **Features use it, delivery does not.** A feature asks the read model and
  shapes the rows for its view, like any use case. Two features may use the
  same read model: that is sharing a contract, not features calling each
  other.

This is the read side of CQRS without separate databases or events: writes go
through entities, reads that span entities go through read models, and both
use the same database.

### Integrations

How the app reaches the world. Each integration fulfills a contract that an
entity or shared declares: a database store, a mailer, a clock, the config
loader. Integrations import entities and shared, never features or delivery.

Each integration talks to its system one way. If the database stores use a
small set of query helpers, every store uses them and none reaches past them
to the driver. Two styles side by side double what a reader has to know.

### Delivery

How the world reaches the app: web routes, API endpoints, CLI commands, the
worker that dispatches messages. Delivery translates input into feature calls
and feature results into output. It holds no business rules.

One file in delivery, **wiring**, builds the whole object graph at startup.
It is the only file that knows integrations exist. In a framework with a
dependency-injection container, the container builds the objects and the
wiring file binds every contract to its integration
([frameworks.md](frameworks.md#containers-what-stays-explicit)).

#### Pages

Each page in web delivery gets its own folder in `delivery/web/<page>/`. The
page is the unit of web delivery, the way a use case is the unit of features.

```
delivery/web/
  layout              # the outer frame every page sits in
  layout.css          # global styles for the frame
  layout.js           # global scripts for the frame
  renderer            # escapes by default, loads layout, feature and page assets
  routes              # paths to pages
  board/
    board             # page code: reads the request, calls features, responds
    board_view        # page template: lays out the page, places feature views
    board.css         # page-specific styles for markup the page template prints
    board.js          # page-specific scripts for this page and its layout
features/
  show_board/
    show_board        # the use case, and the plain values its views print
    board_view        # a feature view
    show_board.css    # feature-specific styles; loads when a view here renders
    show_board.js     # feature-specific scripts; loads when a view here renders
  manage_board_items/
    manage_board_items
    add_card_form     # the form belongs to the feature that handles it
```

How a page is put together:

- **The page template places feature views.** It prints a heading and some
  structure, then hands each area to the feature that owns it. Read it to
  know what is on the page.
- **A feature view displays one feature's values.** It never renders another
  feature's view or a page template. Once a template language can run code,
  this needs a check in the build.
- **A form belongs to the feature that handles its submission.** Its fields,
  labels and choices live in that feature's view, so the code that reads the
  form and the markup that sends it sit in one folder.
- **Slots.** When one feature's area holds another feature's form (an edit
  form inside a board card), the page renders that form and hands it to the
  first view as ready-made, already escaped HTML. The view prints the slot
  where it belongs and knows nothing about what is inside.
- **One-button actions can sit in any view.** A button that posts nothing but
  an id (mark done, delete) has no fields for a feature to own. A slot per
  button would cost more than it saves.
- **Three levels of CSS and JS: global in layout, feature-specific in
  features, page-specific in page folders.**
  - **Layout (`delivery/web/layout.css`, `layout.js`)** holds global styles
    and scripts for the outer frame (navigation, flash messages, shared page
    shell) that every page uses.
  - **Features (`features/<feature>/<feature>.css`, `<feature>.js`)** hold
    feature-specific styles and scripts for the markup and interactions that
    feature's views own. They travel with the feature wherever its view is
    placed.
  - **Page folders (`delivery/web/<page>/<page>.css`, `<page>.js`)** hold
    page-specific styles and scripts: CSS for markup the page template prints
    itself, and JS that belongs to that page alone or coordinates between the
    features placed on it. If a style rule or script targets one feature's own
    markup or behavior, it belongs in that feature's folder so any page that
    places the feature gets it too.
- **Assets load with their views, in render order.** A feature's CSS and JS
  load automatically when one of its views renders on the page: the layout's
  global assets first, then each feature's in the order the features first
  rendered, then the page folder's own assets last. Delivery never keeps a
  hand-written list of which page needs which feature stylesheet or script, so
  a feature cannot appear without its styling or behavior, and page-specific
  assets always load after the features they arrange.

Keep CSS and JS in their colocated `.css` and `.js` files rather than inline
`<style>` blocks, `style=""` attributes or inline `<script>` tags, and serve
layout, feature and page assets from their folders (through the app, or copied
by a build step). Separate files make asset ownership checkable in the build
and keep a strict Content-Security-Policy possible. Give every file in a
folder the same casing — either `snake_case` (`show_board/show_board.css`,
`board/board.js`, `layout.css`) or `PascalCase` (`ShowBoard/ShowBoard.css`,
`Board/Board.js`, `Layout.css`) — so the renderer can find a feature's or
page's assets directly from its folder name.

The cost is honest: a screen is now two places, its page folder and the
features it shows. In exchange, each part of the screen is found by asking
who handles it, and nothing on the page is owned twice.

##### Optional: group the frame in `_layout/`

The tree above keeps the layout, its global CSS and JS, and the renderer
loose at the root of `delivery/web/`. That is the default, not a rule. When
those files start to crowd the page folders, or the frame picks up helpers
that several pages use, you can move them into one folder that stands apart
from the pages:

```
delivery/web/
  routes              # stays at the root: paths to pages
  _layout/
    layout            # the outer frame every page sits in
    layout.css        # global styles for the frame
    layout.js         # global scripts for the frame
    renderer          # escapes by default, loads layout, feature and page assets
    flash             # the flash message the frame prints on every page
  board/
    ...
```

The underscore marks the folder as not a page and, in most editors, sorts it
above the page folders. Use the project's casing (`_layout/` or `_Layout/`).
The folder keeps the layout's job and nothing more:

- **Presentation only.** Delivery holds no business rules, and neither does
  `_layout/`.
- **More than one page uses it.** A helper or style for one page stays in
  that page's folder, and a rule for one feature's markup stays in that
  feature.
- **Tell the checker.** A checker that treats every folder in
  `delivery/web/` as a page must skip `_layout/`, and the renderer must load
  the frame from its new path.

### Outside `src/`

| Path | Holds |
|---|---|
| `config/` | Setting overrides, one file per owner, owned by whoever runs the app (a folder of their own where the framework already uses `config/`: see [frameworks.md](frameworks.md#the-config-folder)) |
| `tests/` | Entity tests (no fakes), feature tests (with fakes), integration tests |
| `AGENTS.md` | The rules on one page, for AI agents and people |
| `docs/decisions/` | Decisions no unit in `src/` owns, one short file each ([comments.md](comments.md#decisions-no-unit-owns)) |
| the checker | A script that fails the build when a rule is broken |
| `var/` | Runtime files (local database, logs), never committed |

## Import direction

| Zone | May import |
|---|---|
| shared | nothing else from the app |
| entities/X | only entities/X |
| features/X | entities, shared, and features/X itself |
| integrations/X | entities, shared, and integrations/X itself |
| delivery | features, shared, delivery |
| delivery/wiring | anything |

**Never:** a feature importing another feature, a feature importing an
integration, an entity importing another entity, or anything importing
delivery (except delivery itself).

The core (entities, features, shared) also never imports I/O modules
(database drivers, HTTP, file system, environment) and never reads the clock.

### Enforce it

Write the import rule into the build so it cannot erode. Existing tools:

| Language | Tools |
|---|---|
| PHP | Deptrac, or a short script over `use` statements |
| Python | import-linter, or a short `ast` script (see the example's `arch_check.py`) |
| JavaScript / TypeScript | dependency-cruiser, eslint-plugin-boundaries |
| Java / Kotlin | ArchUnit, Konsist, or one Gradle module per zone |
| C# | NetArchTest, ArchUnitNET, or one project per zone |
| Go | `internal/` packages, go-arch-lint |
| Rust | one crate per zone in a workspace; Cargo enforces the direction |

Where the build system can make each zone its own module (Gradle modules,
.NET projects, Rust crates), the compiler enforces the direction for free.

Run the language's type checker or static analyser in the same build, at a
strict setting. It catches what the import check cannot: a field that does
not exist, a variable used before it is set, a branch that can never run.
Typed read rows and feature-shaped view values matter here, because a checker
only sees as far as the types reach.

## Spread: count the folders

The question FIDES asks of any structure is: **how many folders do you open
to understand or change one thing?**

A layered app commonly splits "enroll a student" across something like:

```
controller/   dto/   mapper/   validator/   service/   service/impl/
repository/   repository/impl/   entity/   event/   listener/
config/   templates/   static/css/
```

That is fourteen places for one concept, and every new developer and every
AI agent has to rediscover the route between them.

In FIDES the same work lives in:

```
features/enroll/          # the use case, its view, its CSS and JS
entities/course/          # the rules, values, messages, settings, contract
integrations/database/    # one store file
delivery/wiring           # one line that connects them
```

Four places, and most days you only open the first two.

FIDES keeps exactly one split that layered apps also have: a contract lives
with its entity and its implementation lives in integrations. That split is
what lets the core be tested without a database and swapped to a new one
without touching a rule.

**The spread test:** a change should touch its feature folder, the entities
that feature names, at most one integration, and wiring. If it needs more, a
concept is spread too far.

### Depth, size and naming

Spread has a vertical side too:

- **Shallow.** Never deeper than `zone/owner/file`. The two exceptions are a
  page in delivery (`delivery/web/<page>/file`) and a feature in a group
  (`features/<group>/<use_case>/file`, see [feature groups](#feature-groups)).
- **Small files.** Aim for under 200 code lines (blank lines and comments do
  not count). Past 200 the check warns and you decide; past 300 it fails.
  - **Split** when you can name a second concept in the file, when a part
    could be read and tested on its own, or when parts change for different
    reasons. Give the new concept its own unit, named for it.
  - **Keep together** when one name honestly covers the whole file, its parts
    change together, and a split would only give you `part1`, `helpers`, or
    two files that import each other.
  - 200 to 300 is room for a file that is truly one concept, not space to
    fill. A file kept past 200 gets its reason in the change description. A data file (a lookup table,
  generated code) may be listed in the checker as an exemption, with its
  reason, never logic and never with a comment in the file itself.
- **Short lines.** About 100 characters, one statement per line, so code
  reads down the page instead of across it.
- **Split by concept, never by kind of code.** A folder of "helpers" or
  "utils" is a sign a concept has no owner yet.
- **Consistent casing: `snake_case` or `PascalCase`.** Folder and file names
  stay flexible to match the language, but pick one of the two standard styles
  and use it everywhere in `src/` and `config/` — across zone folders,
  entities, features, pages, view templates, `.css` and `.js`. Bias toward
  `snake_case` in module-based languages (Python, Rust, Go, and the diagrams
  in these docs: `entities/course/course_store`, `features/enroll/enroll.css`)
  and toward `PascalCase` where namespaces and classes map 1:1 to folders and
  files on disk (PHP PSR-4, C#: `Entities/Technician/TechnicianStore.php`,
  `Features/Enroll/Enroll.css`). Never mix casings inside a project, and check
  the choice in the build.

## Glossary

| Term | Meaning |
|---|---|
| Unit | The smallest thing that owns data: a class, a package or a module, depending on the language |
| Entity | A unit with identity and rules that are true everywhere |
| Value | A unit with no identity that checks itself and never changes |
| Contract | A promise one side needs and the other side keeps: an interface, protocol or trait |
| Store | The contract for finding and saving an entity, fulfilled by an integration |
| Message | A record of something that happened, saved with the change that caused it |
| Feature | One use case, in one folder |
| Feature group | An optional folder over features, named for an area of the app; it holds no code, and each use case in it stays its own owner |
| Feature view | A template in a feature's folder that displays that feature's values |
| Page | One screen of a web delivery, in its own folder in delivery: page code, a page template, and any page-specific CSS and JS |
| Page template | The template that lays out a page and places feature views on it |
| Slot | Ready-made HTML a page hands into a feature view, such as another feature's form |
| Read row | A small typed, read-only record a store returns for lists and screens |
| Read model | A read-only query contract in shared for data that spans two entities or more, with its typed rows, fulfilled by an integration |
| Settings | An owner's tunable values, declared in code with defaults and rules |
| Wiring | The one file that builds the app from its parts; with a dependency-injection container, the one file that binds every contract to its integration |
