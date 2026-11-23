**FIDES rules.** These are the rules every FIDES repository shares. This
repository's own guide, outside this block, adapts them to its language and
framework and names its check command. Where the two differ, follow this
repository's guide: its checker enforces it.

**Rules**

1. Only the owner changes its data. Others call its actions.
2. Entities import only their own folder. Refer to other entities by id.
3. One use case per feature folder. Features never import each other.
4. The core (entities, features, shared) never touches the database, files,
   network, environment or clock.
5. Dependencies point inward. Only wiring imports integrations.
6. No inheritance. Compose. Contracts are interfaces. A custom error may
   extend one built-in exception, nothing else. No traits or mixins in the core.
7. Messages: entities record, stores save with the change, a worker
   dispatches after commit. Every handler is safe to run twice.
8. One write by default. A UnitOfWork only when two entities change.
9. Settings: declared in code by their owner, overridden in config/, then by
   the environment. Secrets come from the environment only. The database
   never holds configuration.
10. Views only display values their feature shaped. Escaped by default.
11. Pages compose features: a folder per page in delivery. A form belongs to
    the feature that handles it. A feature view never renders another's. CSS
    and JS sit with the layout, feature or page, never inline.
12. At most `zone/owner/file` deep (pages: `delivery/<door>/<page>/file`;
    grouped features: `features/<group>/<use_case>/file`, all or none, no code
    in a group). Lines up to 100 characters. One casing (snake_case or
    PascalCase) everywhere.
13. Files: aim for 200 code lines, never past 300 (blank lines and comments
    do not count). Past 200, split out any concept you can name. Keep a file
    whole only if one name covers all of it and a split would leave `part1`,
    `helpers` or files that import each other, and say why in your summary.
    200 to 300 is room for one concept, not space to fill.
14. Every file opens with what it does and why. Comments say why, and what is
    true now; history goes in the commit message. A decision no unit owns
    goes in `docs/decisions/<name>.md`, named in code as `Decision: <name>`.
    A TODO names its issue: TODO(#123).

**Naming.** A name is a promise; if the code drifts from it, that is a defect.

- A reader who knows the domain can guess a feature's path, and a file's
  contents from its name. If they cannot, rename it.
- Full words, no abbreviations, nothing clever. Length is fine; ambiguity
  is not.
- One word per concept, spelled the same in folders, classes, methods,
  routes and tests.
- Features are verb phrases (IssueInvoice), entities plain nouns (Invoice),
  and a method that answers yes or no is a question (isOverdue).
- No empty words: Manager, Helper, Utils, Handler, Processor, Data, Info,
  Misc. "And" in a name means two jobs: split the unit.
- Tests are named as the rule they check (invoice_total_includes_tax).

**Spread.** If a change touches more than its feature folder, the entities it
names, one integration and wiring, stop and ask whether a concept is spread
too far.
