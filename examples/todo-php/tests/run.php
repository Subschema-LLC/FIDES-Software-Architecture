<?php
/** The test run: the architecture check, then the rules, with a
 *  throwaway SQLite database. php tests/run.php */

$root = dirname(__DIR__);
require $root . '/autoload.php';
require $root . '/src/Delivery/Wiring.php';

$passes = 0;
$fails = 0;
function check(bool $ok, string $name): void
{
    global $passes, $fails;
    if ($ok) {
        $passes++;
    } else {
        $fails++;
        echo "FAIL: $name\n";
    }
}

// Architecture first: a broken shape fails the whole run.
passthru('php ' . escapeshellarg($root . '/arch-check.php'), $archExit);
check($archExit === 0, 'arch-check passes');
passthru('php ' . escapeshellarg(__DIR__ . '/arch-check-cases.php'), $casesExit);
check($casesExit === 0, 'arch-check catches inheritance and file size');

use App\Delivery\Web\WebApp;
use App\Entities\TodoItem\TodoItem;
use App\Entities\TodoItem\TodoItemSettings;
use App\Entities\TodoItem\TodoItemStore;
use App\Features\TodoManagement\AddTodo\AddTodo;
use App\Features\TodoManagement\CompleteTodo\CompleteTodo;
use App\Features\TodoManagement\DeleteTodo\DeleteTodo;
use App\Features\TodoManagement\ListTodos\ListTodos;
use App\Features\TodoManagement\ReopenTodo\ReopenTodo;
use App\Integrations\Clock\SystemClock;
use App\Integrations\Config\ConfigLoader;
use App\Integrations\Database\SqliteTodoItemStore;

final class FakeTodoItemStore implements TodoItemStore
{
    /** @var array<int, TodoItem> */
    private array $items = [];
    private int $nextId = 1;

    public function save(TodoItem $item): TodoItem
    {
        if ($item->id === null) {
            $item = $item->withId($this->nextId++);
        }
        $this->items[$item->id] = $item;
        return $item;
    }

    public function get(int $id): ?TodoItem
    {
        return $this->items[$id] ?? null;
    }

    public function all(int $limit): array
    {
        $all = array_values($this->items);
        usort($all, static fn(TodoItem $a, TodoItem $b): int => (int) $b->id <=> (int) $a->id);
        return array_slice($all, 0, $limit);
    }

    public function delete(int $id): void
    {
        unset($this->items[$id]);
    }
}

$now = new DateTimeImmutable('2026-11-13 12:00:00');

// Entity rules.
check(TodoItem::create('  Write the spec  ', $now)->title === 'Write the spec', 'titles are trimmed');
try {
    TodoItem::create('   ', $now);
    check(false, 'an empty title is refused');
} catch (InvalidArgumentException) {
    check(true, 'an empty title is refused');
}
try {
    TodoItem::create(str_repeat('a', 201), $now);
    check(false, 'a title over 200 characters is refused');
} catch (InvalidArgumentException) {
    check(true, 'a title over 200 characters is refused');
}
$item = TodoItem::create('Ship it', $now);
check($item->complete($now)->done && $item->complete($now)->completedAt == $now, 'complete marks done with the time passed in');
check($item->complete($now)->complete($now->modify('+1 day'))->completedAt == $now, 'completing a done item changes nothing');
check($item->complete($now)->reopen()->done === false && $item->reopen() === $item, 'reopen clears done; reopening an open item changes nothing');

// Settings: defaults, file override, env wins, undeclared key fails.
$loader = new ConfigLoader($root . '/config', []);
check($loader->todoItemSettings()->listLimit === 25, 'config/TodoItem.yaml overrides the default 50 with 25');
$loader = new ConfigLoader($root . '/config', ['TODOITEM_LIST_LIMIT' => '7']);
check($loader->todoItemSettings()->listLimit === 7, 'the environment wins over the file');
$badDir = sys_get_temp_dir() . '/fides-todo-badcfg';
@mkdir($badDir);
file_put_contents($badDir . '/TodoItem.yaml', "bogus_key: 1\n");
try {
    (new ConfigLoader($badDir, []))->todoItemSettings();
    check(false, 'an undeclared config key fails startup');
} catch (RuntimeException) {
    check(true, 'an undeclared config key fails startup');
}
try {
    new TodoItemSettings(0);
    check(false, 'an out-of-range list_limit is refused');
} catch (InvalidArgumentException) {
    check(true, 'an out-of-range list_limit is refused');
}

// Store round-trip and the feature flow.
$store = new FakeTodoItemStore();
$saved = $store->save(TodoItem::create('First', $now));
check($saved->id !== null && $store->get($saved->id)->title === 'First', 'the store saves and reads back');
$store->save(TodoItem::create('Second', $now));
check(count($store->all(50)) === 2 && count($store->all(1)) === 1, 'all() lists newest first within the limit');
$store->save($saved->complete($now));
check($store->get($saved->id)->done === true, 'an update through save() persists');
$store->delete($saved->id);
check($store->get($saved->id) === null && count($store->all(50)) === 1, 'delete removes the item');

if (in_array('sqlite', PDO::getAvailableDrivers(), true)) {
    $tmp = tempnam(sys_get_temp_dir(), 'fides-todo-') . '.sqlite';
    $pdo = new PDO('sqlite:' . $tmp);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $sqliteStore = new SqliteTodoItemStore($pdo);
    $sqliteSaved = $sqliteStore->save(TodoItem::create('SQLite item', $now));
    check($sqliteSaved->id !== null && $sqliteStore->get($sqliteSaved->id)?->title === 'SQLite item', 'SqliteTodoItemStore round-trip');
    unlink($tmp);
}

// Web delivery: dashboard page, todo page, asset loading order, and POST actions.
$clock = new SystemClock();
$settings = new TodoItemSettings(25);
$web = new WebApp([
    'list' => new ListTodos($store, $settings),
    'add' => new AddTodo($store, $clock),
    'complete' => new CompleteTodo($store, $clock),
    'reopen' => new ReopenTodo($store),
    'delete' => new DeleteTodo($store),
]);
$_SESSION = ['csrf' => 'test-csrf-token'];

$dashboardHtml = $web->handle('GET', [], '/');
check(
    str_contains($dashboardHtml, '<h1>Dashboard</h1>')
    && str_contains($dashboardHtml, 'Second')
    && str_contains($dashboardHtml, 'href="/todo"'),
    'GET / renders the dashboard page with summary and ListTodos view'
);
$layoutCssPos = strpos($dashboardHtml, '/assets/Layout.css');
$listCssPos = strpos($dashboardHtml, '/assets/Features/TodoManagement/ListTodos/ListTodos.css');
$dashCssPos = strpos($dashboardHtml, '/assets/Pages/Dashboard/Dashboard.css');
check(
    $layoutCssPos !== false && $listCssPos !== false && $dashCssPos !== false
    && $layoutCssPos < $listCssPos && $listCssPos < $dashCssPos,
    'dashboard CSS loads in FIDES order: layout, then ListTodos, then dashboard'
);

$todoHtml = $web->handle('GET', [], '/todo');
check(
    str_contains($todoHtml, '<h1>To-dos</h1>')
    && str_contains($todoHtml, 'class="add-todo-form"')
    && str_contains($todoHtml, 'Second'),
    'GET /todo renders the todo page composing AddTodo and ListTodos views'
);
$todoLayoutCss = strpos($todoHtml, '/assets/Layout.css');
$addTodoCss = strpos($todoHtml, '/assets/Features/TodoManagement/AddTodo/AddTodo.css');
$todoListCss = strpos($todoHtml, '/assets/Features/TodoManagement/ListTodos/ListTodos.css');
$todoPageCss = strpos($todoHtml, '/assets/Pages/Todo/Todo.css');
check(
    $todoLayoutCss !== false && $addTodoCss !== false && $todoListCss !== false && $todoPageCss !== false
    && $todoLayoutCss < $addTodoCss && $addTodoCss < $todoListCss && $todoListCss < $todoPageCss,
    'todo page CSS loads in FIDES order: layout, AddTodo, ListTodos, then todo page'
);

$web->handle('POST', ['_csrf' => 'test-csrf-token', 'action' => 'add', 'title' => 'Third item', 'return_to' => '/todo'], '/todo');
check(($_SESSION['flash'] ?? '') === 'Added: Third item', 'POST /todo adds a to-do and sets flash message');

$cssAsset = $web->handle('GET', [], '/assets/Features/TodoManagement/ListTodos/ListTodos.css');
$jsAsset = $web->handle('GET', [], '/assets/Features/TodoManagement/ListTodos/ListTodos.js');
check(
    str_contains($cssAsset, '.todos') && str_contains($jsAsset, 'data-todo-list'),
    'GET /assets/... serves colocated PascalCase CSS and JS assets'
);

$apiJson = json_decode($web->handle('GET', [], '/api/todos'), true);
check(
    is_array($apiJson)
    && ($apiJson['summary']['total'] ?? 0) === 2
    && ($apiJson['items'][0]['title'] ?? '') === 'Third item',
    'GET /api/todos returns JSON summary and items via ReadTodos'
);

echo "\n$passes passed, $fails failed\n";
exit($fails === 0 ? 0 : 1);
