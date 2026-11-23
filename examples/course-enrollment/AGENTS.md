# AGENTS.md: rules for AI coding agents (and humans) working here

This app follows FIDES. The full spec is in the repository root under `docs/`.
This page is the part you need while changing code. `python3 run_tests.py`
checks most of it and fails the build when a rule is broken. Install mypy
(`pip install mypy`) so it type-checks `src/` too.

## Where code goes

| You are adding... | Put it in |
|---|---|
| A rule that is always true for a concept | that concept's folder in `src/entities/` |
| Something a user or system does | a new folder in `src/features/` |
| A new way the outside world reaches the app | `src/delivery/` |
| A new web page | `src/delivery/web/<page>/`: `<page>.py`, `<page>.html`, and any page-specific `.css` or `.js` |
| A new way the app reaches the outside world | `src/integrations/`, behind a contract |
| A contract no single entity owns | `src/shared/` |
| A read across two entities or more | a read model: `src/shared/<read_model>/` holds only the query contract and its rows; an integration answers it with one query |
| A setting | declared with its default in the owner's settings class |
| An override for a setting | `config/<Owner>.toml` (never inside `src/`) |

If a change needs more than a feature folder, the entities it names and one
integration, stop and ask whether a concept is being spread too far.

## Rules

1. **One owner.** Only the unit that owns data changes it. Others call its actions.
   Reading through properties is fine.
2. **Entities stand alone.** An entity imports only its own folder. Refer to
   another entity by id, never by object. Cross-entity rules live in features.
   Cross-entity reads go through a read model (`shared/class_roster/`).
3. **One use case per feature folder,** readable top to bottom, with its view
   and CSS beside it. Features never import other features. They react to
   messages instead.
4. **The core is pure.** Entities, features and shared never touch the database,
   files, network, environment or clock. Features get time from the `Clock`
   contract and pass it into entities.
5. **Dependencies point inward.** Features import entities and shared.
   Integrations import entities and shared. Delivery imports features and
   shared. Only `delivery/wiring.py` imports integrations.
6. **No inheritance.** Compose small objects. The only base classes allowed are
   `Protocol`, for contracts, and one built-in exception, for a custom error
   (`class CourseFull(ValueError)`). Integrations fulfill contracts without
   inheriting. This app needs no custom errors: a built-in one with a clear
   message is usually enough.
7. **Messages are recorded, saved, then dispatched.** Entities record them,
   stores save them in the same write, the worker dispatches them after
   commit. Never send email or call out from inside a change. Handlers must be
   safe to run twice.
8. **One write by default.** A store's `save()` is the transaction. Ask for
   `UnitOfWork` only when a feature changes two entities, so it is visible in
   the constructor.
9. **Settings are declared in code, overridden in `config/`, then by the
   environment,** merged once at startup. Unknown keys and invalid values stop
   startup. Secrets come from the environment only. The database holds
   transactional data, never configuration.
10. **Views only display.** Templates have no logic. Values are escaped unless
    they are `Markup`. A feature shapes plain values for its own views.
11. **Pages compose features.** A page is a folder in `src/delivery/web/`:
    `<page>.py` reads the request and calls features, `<page>.html` places
    their views, and any page-specific `.css` and `.js` sit beside them. A form
    belongs to the feature that handles it. CSS and JS are global in layout,
    feature-specific in `src/features/<feature>/`, and page-specific in the
    page folder; feature assets load when a feature view renders, so never list
    them by hand.
12. **Keep it close and small.** At most `zone/owner/file` deep (pages:
    `delivery/web/<page>/file`), lines up to 100 characters. Aim for files
    under 200 code lines (the check warns past 200 and fails past 300;
    comments and blank lines do not count). Split by concept, never by kind
    of code. If a file you touched warns: split out any concept you can name.
    Keep it whole only if one name covers all of it and a split would leave
    `part1`, `helpers` or files that import each other, and say why in your
    summary. 200 to 300 is room for one concept, not space to fill.
13. **Explanations sit with what they explain.** Every file opens with a
    docstring: what it does, then why. Comments say what is true now; what
    changed goes in the commit message. A decision no unit owns is a file in
    `docs/decisions/`, named in code as `Decision: <name>`. A TODO names its
    issue: `TODO(#123)`.

## Before you finish

```bash
python3 run_tests.py      # architecture check, type check (with mypy), all tests
```

Coming back after months away? Read this page, then `config/`, then
`src/features/transfer/transfer.py` (the one feature that shows every rule),
then `src/delivery/wiring.py` to see how it all connects.
