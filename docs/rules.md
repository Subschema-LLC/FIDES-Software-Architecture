# The rules

These are all of FIDES's rules. Each comes with the reason for it. Rules
marked **(checkable)** have a part that a script in the build can check. The
example's `arch_check.py` checks each of them, or says why its template
language already makes breaking the rule impossible.

**The test behind every rule:** a new developer or an AI agent understands any
feature in five minutes, and you can come back after six months and find your
way.

## Ownership

**1. One owner.** Only the unit that owns data changes it. Everything else asks
through the owner's actions (`course.enroll(...)`), never by setting its
fields. Reading through read-only accessors is fine.
*Why: when data is wrong, there is one place to look.*

**2. Ownership follows consistency.** An entity owns everything it must keep
consistent and saves it in one write. A Course owns its enrollments because
the seats taken must always match them.
*Why: a rule can never be half-applied.*

**3. Entities stand alone.** An entity imports only its own folder. It refers
to other entities by identity (an id or a key), never by holding them. A
screen that needs several entities at once reads them through a read model, a
read-only query contract in shared ([structure.md](structure.md#read-models)),
never by one entity holding another. **(checkable)**
*Why: any entity can be read, tested and changed without opening another.*

## Features

**4. One use case per feature folder,** named as an action and readable top to
bottom. Its views and feature-specific CSS and JS sit beside it, including any
form whose submission it handles. Rules that involve two entities live here,
because neither entity owns them.
*Why: one concept, one place.*

**5. Features never call each other.** When one thing should follow another,
the first records a message and a second feature reacts to it. **(checkable)**
*Why: each feature can be understood and removed on its own.*

## Boundaries

**6. The core is pure.** Entities, features and shared never touch the
database, files, network, environment variables or the clock directly. They
state what they need as contracts. Features get the time from a `Clock`
contract and pass it into entities. **(checkable)**
*Why: the core can be tested in milliseconds with no setup, and the outside
world can change without touching a rule.*

**7. Dependencies point inward.** Delivery uses features, features use
entities and shared, integrations fulfill contracts from entities and shared.
Only wiring knows integrations exist. See the table in
[structure.md](structure.md#import-direction). **(checkable)**
*Why: the parts that change most often (the edges) depend on the parts that
change least (the rules), never the reverse.*

**8. No inheritance.** Compose small units. Contracts are interfaces,
protocols or traits, and implementations fulfill them without extending
anything. If a framework forces you to subclass one of its types, keep that
class at the edge (delivery or integrations), thin and with no rules in it.
Code mixed into a class counts as inheritance too (PHP traits, Python mixin
classes, TypeScript class-factory mixins, Ruby modules): it puts a unit's
behavior in another file. None in the core; one a framework requires stays at
the edge, like a required base class. A Rust trait is a contract, not a
mixin. One allowance holds in every zone: where an error has to extend the
language's built-in exception type to be thrown, or to carry a stack trace
(PHP, Python, Java, C#, JavaScript), a custom error may extend one built-in
exception type, never another custom error. Often no custom error is needed:
a built-in exception with a clear message is enough. **(checkable)**
*Why: what a unit does is in the unit, not spread up a chain of parents. A
custom error that extends a built-in one adds a name to catch, not a chain to
climb.*

## Change

**9. One write by default.** A store's save writes the entity, its children and
its messages in one transaction. A feature that changes two entities asks for
a `UnitOfWork` in its constructor, so the exception is visible to every
reader. Saves check a version so two simultaneous changes cannot both win.
*Why: changes are all or nothing, and the rare multi-entity change is obvious.*

**10. Messages are recorded, saved, then dispatched.** Entities record what
happened. Stores save messages in the same write as the change. A worker
dispatches them after commit. Nothing is ever sent from inside a change, and
every handler is safe to run twice.
*Why: a failed email cannot undo an enrollment, and a rolled-back enrollment
never sends one.*

Details: [changes.md](changes.md).

## Configuration

**11. Settings are declared by their owner and overridden from outside.** The
owner declares every setting in code with its default and its rules. Overrides
live in `config/`, outside the source tree, one file per owner. Environment
variables win over the file. Everything is merged once per startup and stays
frozen until the next: once per process for a long-running server, once per
request where the runtime builds the app for each request, as PHP usually
does. Unknown keys and invalid values stop startup. Secrets come from the
environment only.
*Why: code updates never overwrite an operator's settings, typos fail loudly,
and there is one answer to "where did this value come from?"*

**12. The database holds transactional and reporting data, never
configuration.**
*Why: configuration that hides in a table cannot be reviewed, versioned or
reproduced.*

Details: [configuration.md](configuration.md).

## Presentation

**13. Views only display.** A view gets plain values shaped by its feature,
never fetches data and holds no business rules. The shaping happens in the
feature's code, where tests and the type checker can see it, and a template
never names an entity. Output is escaped by default, and unescaped output is
explicit and rare. Prefer a logic-less template language (Mustache-style) so
the template cannot break this rule. If your templates can run code, check
the rule in the build. **(checkable)**
*Why: a view that can only display cannot hide a rule or a security hole, and
a mistake in shaping is caught where it is made, not on a page nobody opened.*

**14. Pages compose features.** A page lives in delivery, one folder per page
(`delivery/web/<page>/`): the code that reads the request and calls features,
a page template that lays out the page and places feature views, and any
page-specific CSS and JS. A feature's view never renders another feature's
view or a page template. A form belongs to the feature that handles its
submission. When one feature's area holds another feature's form, the page
renders that form and hands it in, ready-made, for the view to print in place.
CSS and JS follow the same three owners: global frame assets sit with the
layout, feature-specific assets sit in the feature folder, and page-specific
assets sit in the page folder, loaded in that order (layout, then rendered
features, then page) from `.css` and `.js` files rather than inline.
**(checkable)**
*Why: every part of a screen has one owner, and the page template reads as a
list of what is on the page.*

Details: [structure.md](structure.md#pages).

## Size and spread

**15. One concept, one place.** A change touches its feature folder, the
entities that feature names, at most one integration, and wiring. If it needs
more, a concept is spread too far.
*Why: the cost of a change is mostly the cost of finding everything it
touches.*

**16. Small and shallow.** Never deeper than `zone/owner/file`. Two places get
one extra level: a page in delivery (`delivery/web/<page>/file`) and a feature
in a group (`features/<group>/<use_case>/file`). A group is named for the area
people look for, usually a screen or a menu entry. It is only a folder: it
holds no code, the use case stays the owner, and features in one group still
never call each other. Groups are optional; once a project uses them, every
feature sits in one ([structure.md](structure.md#feature-groups)). Aim for
files under 200 code lines; past 200 the check warns, and past 300 it fails.
Code lines leave out blank lines and comments, so nobody deletes an
explanation to pass. Past 200, split out any concept you can name; keep the
file whole only when it is one concept, and say why in the change
([structure.md](structure.md#depth-size-and-naming)). Lines stay under about 100 characters. Split by concept,
never by kind of code, and name the concept: files called `part1` and `part2`
hide it.
A file that is data, not logic (a lookup table, generated code), may skip the
size limits when the checker lists it with its reason, in one place where
review sees it. Logic never does. **(checkable)**
*Why: a small file holds one concept you can understand whole, and a person or
an AI agent finds a feature by the area it belongs to. The 200 is a habit, not
a measured optimum: studies of file size and defects disagree on any one
number, so the hard limit sits higher and the warning starts the
conversation.*

## Practice

**17. Rules are required, tools are examples.** FIDES names what must be true,
never which framework, database or template engine to use. Inside a
framework, keep its conventions and map the zones onto them
([frameworks.md](frameworks.md)); each rule's *why* says what must survive
the mapping. Follow your
language's own conventions for naming and syntax — typically `snake_case` in
module-based languages or `PascalCase` where namespaces and classes map 1:1 to
folders and files — and keep that single casing consistent across folders,
code, views, `.css`, `.js` and `config/` files. **(checkable)**
*Why: the rules outlive the tools, and consistent naming within a project lets
people, renderers and AI agents predict every file path.*

**18. Enforce mechanically.** The rules marked checkable run as a check in the
build, and so does the language's type checker or static analyser, at a
strict setting. An `AGENTS.md` states the rules on one page.
*Why: a written rule is a request. A failing build is the part nobody, human
or AI, can quietly skip. A rule the build does not check drifts: in a
production app moved onto FIDES, the size limits were written down but not
checked, and they were not kept.*

**19. Explanations sit with what they explain.** Every code file opens with a
header: what the unit does, then the reasons the code cannot show. Comments
say why, and what is true now; history goes in the commit message. A decision
no unit owns gets a short record in `docs/decisions/`, and code names it as
`Decision: <name>`, never by number. A TODO names the issue that owns it.
**(checkable)**
*Why: whoever opens one file gets the reasons with the code, and a reference
the build checks cannot point at something that is gone.*

Details: [comments.md](comments.md).
