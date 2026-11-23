# AGENTS.md — rules for AI agents and people working in this app

This app follows FIDES. Run `php arch-check.php` and
`php tests/run.php` before you finish.

## Where code goes

- A rule always true for a concept → its folder in `src/Entities/`
- Something a user or system does → a new folder in `src/Features/TodoManagement/` (or `src/Features/<Group>/`)
- A new way the world reaches the app → `src/Delivery/`
- A new web page → `src/Delivery/Web/<Page>/`
- A new way the app reaches the world → `src/Integrations/`, behind a contract
- A contract no single entity owns → `src/Shared/`
- Setting overrides → `config/`, one YAML file per entity

## Naming convention

- **All directories and files in `src/` and `config/`:** `PascalCase` across zone folders, feature groups, page folders, PHP classes, interfaces, view templates (`*View.php`, `Layout.php`), stylesheets (`*.css`), scripts (`*.js`), and wiring (`Wiring.php`), matching PSR-4 namespaces 1:1 on disk — e.g. `Entities/TodoItem/TodoItem.php`, `Features/TodoManagement/ListTodos/ListTodos.php`, `ListTodosView.php`, `ListTodos.css`, `ListTodos.js`, `Features/TodoManagement/AddTodo/AddTodoView.php`, `AddTodo.css`, `Delivery/Web/Dashboard/Dashboard.php`, `DashboardView.php`, `Dashboard.css`, `Dashboard.js`, `Delivery/Web/Todo/Todo.php`, `TodoView.php`, `Todo.css`, `Todo.js`, `Layout.php`, `Layout.css`, `Layout.js`.

## The rules

1. **No inheritance.** Never use `extends` in `src/`. Compose small
   objects instead. Classes are `final`; contracts are interfaces.
   The one exception: PHP only throws `Throwable`s, so a custom
   exception may extend one built-in exception
   (`final class TodoMissing extends \RuntimeException`), never
   another custom exception. A built-in exception with a clear
   message is usually enough, as everywhere in this app today.
   No traits either: they put a class's behavior in another file.
2. **Entities hold rules that are true everywhere.** An entity
   imports only its own folder. It owns what it must keep
   consistent and saves in a single store write. (TodoItem owns its
   title rule and its done/open state.)
3. **Features hold one use case per folder**, readable top to
   bottom, with views and assets colocated (`TodoManagement/ListTodos/ListTodosView.php`,
   `TodoManagement/ListTodos/ListTodos.css`, `TodoManagement/ListTodos/ListTodos.js`,
   `TodoManagement/AddTodo/AddTodoView.php`, `TodoManagement/AddTodo/AddTodo.css`).
   Features import entities, `src/Shared/` contracts, and their own
   feature folder only: never integrations, never delivery, never another feature.
4. **Views only display.** Features shape plain values (`TodoRow`,
   `TodoSummary`) before rendering; templates never reference entities.
5. **Pages compose features.** Each web page lives in
   `src/Delivery/Web/<Page>/` (`<Page>.php`, `<Page>View.php`,
   `<Page>.css`, `<Page>.js`). `Renderer` loads CSS and JS in FIDES
   order: layout first, then each rendered feature in first-render
   order, then the page's own.
6. **Integrations fulfill contracts** (the SQLite store, the
   system clock, the config loader). They import entities and
   shared contracts only, never each other.
7. **Delivery reaches features only.** `src/Delivery/Wiring.php`
   is the only file allowed to import integrations; it builds the
   object graph and hands finished features to the doors.
8. **Time is passed in.** Features get the time from the shared
   Clock contract and pass it into entities. Entities never read
   a clock.
9. **Configuration is declared, then overridden.** Each entity
   declares its settings, defaults and validation in a Settings
   class in its own folder (`TodoItemSettings`). `config/` holds
   overrides only. The merger runs default, then config file,
   then environment variable; an undeclared override key fails
   startup. The database holds transactional data only, never
   configuration. Secrets, if this app ever has any, come from
   the environment only.
10. Escape every value you print. Every POST form carries the CSRF
    token and its handler checks it.
11. **Keep files small.** Aim for under 200 code lines. The check
    warns past 200 and fails past 300; comments and blank lines do
    not count. Split by concept, never by kind of code. If a file you
    touched warns: split out any concept you can name. Keep it whole
    only if one name covers all of it and a split would leave `Part1`,
    `Helpers` or classes that call each other back and forth, and say
    why in your summary. 200 to 300 is room for one concept, not space
    to fill.
