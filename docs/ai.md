# Working with AI

FIDES was designed for teams where people and AI agents work in the same
codebase. The properties that help a new developer help an agent even more.

## Why the shape helps agents

- **Small, complete context.** A feature folder plus the entities it names is
  everything an agent needs to read. It does not have to search a dozen
  layers to find the pieces.
- **Contracts say what is possible.** An agent writing a feature sees exactly
  which stores and services it may use, by reading the constructor.
- **One obvious place for new code.** "Something a user does" is always a new
  feature folder. Agents stop inventing new layers.
- **Good code to imitate.** Agents copy the nearest example. When every
  feature has the same shape, the nearest example is a correct one.
- **Reasons travel with the code.** Every file opens with what it does and
  why, so an agent that opens one file has the reasons too, and does not
  "fix" a choice made on purpose ([comments.md](comments.md)).
- **Rules a machine can check.** An agent can run the check itself and fix
  what it broke before you ever see it.

## Two things every FIDES repo needs

**1. An `AGENTS.md` at the root.** The rules on one page, plus where new code
goes and what to run before finishing. Agents read it first; people coming
back after months away should too. Keep it short: if it does not fit on a
page, it will not be followed.

**2. A check in the build.** The import rules, purity, no inheritance, the
size limits and the page rules, enforced by a script or tool that fails the
build, plus the language's type checker at a strict setting. A written rule
is a request. A failing build is the part nobody can quietly skip. Six months
from now, an agent will "helpfully" import a database class into a feature to
save a step. The check is what stops it.

Add both on day one. In a production app moved onto FIDES, the first run of
a static analyser found a flash message printing an undefined variable and a
redirect that could never run. The size limits there were written down but
never checked, and by the time anyone measured, about 2,000 lines ran past
100 characters.

## AGENTS.md template

Adapt the names to your language and app. The example app's
[AGENTS.md](../examples/course-enrollment/AGENTS.md) is a filled-in version.

```markdown
# AGENTS.md

This app follows FIDES. Run `<check command>` before you finish.

## Where code goes
- A rule always true for a concept      -> its folder in src/entities/
- Something a user or system does       -> a new folder in src/features/
- A new way the world reaches the app   -> src/delivery/
- A new web page                        -> src/delivery/web/<page>/
- CSS or JS for a feature, page, frame  -> the feature folder, page folder, or layout
- A new way the app reaches the world   -> src/integrations/, behind a contract
- A contract no single entity owns      -> src/shared/
- A read across two entities or more    -> a read model in src/shared/<name>/
- A setting                             -> declared in the owner's settings
- An override for a setting             -> config/<Owner> (never in src/)

## Rules
1. Only the owner changes its data. Others call its actions.
2. Entities import only their own folder. Refer to other entities by id.
3. One use case per feature folder. Features never import each other.
4. The core never touches the database, files, network, environment or clock.
5. Dependencies point inward. Only wiring imports integrations.
6. No inheritance. Compose. Contracts are interfaces. A custom error may
   extend one built-in exception, nothing else.
7. Messages: entities record, stores save with the change, a worker dispatches.
8. One write by default. UnitOfWork only when two entities change.
9. Settings: declared in code, overridden in config/, then env. Secrets: env only.
10. Views only display. Escaped by default. Features shape their values.
11. Pages compose features: a folder per page in delivery/web/<page>/. A form
    belongs to the feature that handles it. A feature view never renders
    another's. CSS and JS are feature-specific in features/, global in layout,
    and page-specific in the page folder (never inline).
12. At most zone/owner/file deep (pages: delivery/web/<page>/file; grouped
    features: features/<group>/<use_case>/file, all or none, no code in a group).
    Files: aim for 200 code lines, never past 300. Past 200, split out any
    concept you can name; keep it whole only if it is one concept, and say
    why in your summary. Lines up to 100 characters. Keep one casing (snake_case or PascalCase)
    consistent across folders, code, views, .css, .js and config/.
13. Every file opens with what it does and why. Comments say why, and what
    is true now; history goes in the commit message. A decision no unit owns
    goes in docs/decisions/<name>.md and is named in code as
    `Decision: <name>`. A TODO names its issue: TODO(#123).

## Naming
A name is a promise. If the code drifts from the name, that is a defect.
- Guess before you look: a reader who knows the domain should be able to
  guess a feature's path, and a file's contents from its name alone. If
  they cannot, rename it.
- Say it out loud: full words, no abbreviations, nothing clever. A name
  should survive being spoken in a sentence. Length is fine; ambiguity
  is not.
- One word per concept: the domain's nouns and verbs, spelled the same in
  folders, classes, files, methods, routes and tests. If the business
  says "cancel", the code never also says "void" or "revoke" for the
  same act.
- Grammar carries meaning: features and use cases are verb phrases
  (IssueInvoice). Entities are plain nouns (Invoice). Methods read as
  sentences at the call site ($invoice->markPaid()). A method that
  answers yes or no is a question (hasBalanceDue(), isOverdue()).
- Empty words are banned: Manager, Helper, Utils, Handler, Processor,
  Data, Info, Misc. They say nothing; banning them puts the meaning in
  the name. A check can flag these.
- "And" means two jobs: split the unit. If a name needs a comment to say
  what the thing is, the name failed; fix the name, not the comment.
- Tests are named as the rule they check (invoice_total_includes_tax,
  subscription_cannot_cancel_twice). The suite reads as the spec.
- When a convention from the wider ecosystem fights readability,
  readability wins.

If a change touches more than its feature folder, the entities it names,
one integration and wiring, stop and ask whether something is spread too far.
```

## Reading order for a returning human or a new agent

1. `AGENTS.md`: the rules, in one page.
2. `config/`: what this installation is set up to do.
3. One feature folder that changes two entities: it shows every rule at once.
4. `delivery/wiring`: the one place that shows how everything connects.
5. The feature folder for whatever you need to change.

## Prompting tips

- Name the feature folder: "Add a waitlist to `features/enroll`" gives the
  agent its whole context in one phrase.
- Ask for the check: "Run the architecture check and the tests before you
  finish."
- When an agent wants to add a new zone, layer or "helpers" folder, treat it
  as a design question, not a code change.
- Ask for comments that say what is true now. Agents tend to leave notes about
  what they changed ("now uses X instead of Y", "moved from the old routes
  file"). That is history. It belongs in the commit message, and in the code
  it goes stale the day it is written.
- When an agent restructures working code, ask it to prove nothing changed,
  not to say so. [migrating.md](migrating.md) describes checks that do.
