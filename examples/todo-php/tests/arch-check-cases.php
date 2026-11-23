<?php
/** Runs arch-check.php on a throwaway tree: a custom exception may extend
 *  one built-in exception; any other `extends` and any trait fail the check;
 *  a closure's `use` is not a trait; past 200 code lines warns, past
 *  300 fails, and comments do not count.
 *  php tests/arch-check-cases.php */

$tree = sys_get_temp_dir() . '/fides-arch-' . bin2hex(random_bytes(4));
mkdir($tree . '/Entities/Thing', 0777, true);
$bodies = [
    'ThingMissing' => "class ThingMissing extends \\RuntimeException\n{\n}",
    'ThingGone' => "final class ThingGone extends ThingMissing\n{\n}",
    'Thing' => "final class Thing extends Model\n{\n}",
    'ThingCounter' => "final class ThingCounter\n{\n    use Counts;\n\n"
        . "    public function adder(int \$step): \\Closure\n    {\n"
        . "        return static fn(int \$n): int => \$n + \$step;\n    }\n\n"
        . "    public function adderToo(int \$step): \\Closure\n    {\n"
        . "        return static function (int \$n) use (\$step): int {\n"
        . "            return \$n + \$step;\n        };\n    }\n}",
];
$constants = static fn(int $count): string => "final class %s\n{\n"
    . implode('', array_map(static fn(int $i): string => "    public const C$i = $i;\n", range(1, $count)))
    . '}';
$bodies['ThingLong'] = sprintf($constants(250), 'ThingLong');
$bodies['ThingTooLong'] = sprintf($constants(310), 'ThingTooLong');
$bodies['ThingExplained'] = sprintf($constants(150), 'ThingExplained')
    . str_repeat("\n// why\n", 200);
foreach ($bodies as $name => $body) {
    file_put_contents(
        "$tree/Entities/Thing/$name.php",
        "<?php\n\nnamespace App\\Entities\\Thing;\n\n$body\n"
    );
}

$command = 'php ' . escapeshellarg(dirname(__DIR__) . '/arch-check.php');
exec($command . ' ' . escapeshellarg($tree), $output, $exit);
$report = implode("\n", $output);

array_map('unlink', glob("$tree/Entities/Thing/*.php") ?: []);
rmdir("$tree/Entities/Thing");
rmdir("$tree/Entities");
rmdir($tree);

$cases = [
    'a built-in parent passes' => !str_contains($report, 'ThingMissing.php: extends'),
    'a custom exception parent fails' => str_contains($report, 'ThingGone.php: extends'),
    'any other parent fails' => str_contains($report, 'Thing.php: extends Model'),
    'a trait fails' => str_contains($report, 'ThingCounter.php: uses trait Counts'),
    'a closure use is not a trait' => substr_count($report, 'uses trait') === 1,
    'past 200 code lines warns' => str_contains($report, 'ThingLong.php: 254 code lines (aim for 200)'),
    'past 300 code lines fails' => str_contains($report, 'ThingTooLong.php: 314 code lines (max 300)'),
    'comments do not count' => !str_contains($report, 'ThingExplained'),
    'the check exits 1' => $exit === 1,
];
$failed = array_keys(array_filter($cases, static fn(bool $ok): bool => !$ok));
foreach ($failed as $name) {
    echo "FAIL: arch-check case: $name\n";
}
if ($failed !== []) {
    echo $report, "\n";
}
exit($failed === [] ? 0 : 1);
