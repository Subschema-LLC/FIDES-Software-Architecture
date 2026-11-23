#!/usr/bin/env python3
"""Checks the FIDES rules that a machine can check. Exit code 1 on any violation.

Run it in the build so a person or an AI agent cannot quietly break a rule.

  Imports      shared        -> shared
               entities/X    -> entities/X only (entities never import each other)
               features/X    -> entities, shared, features/X
               integrations/X-> entities, shared, integrations/X
               delivery      -> features, shared, delivery (wiring.py may import anything)
  Core is pure entities, features and shared never import I/O modules or read the clock
  No inheritance  classes may only subclass Protocol (a contract), or one built-in
               exception (a custom error), never another class of the app
  Spread       at most zone/owner/file deep (delivery: delivery/door/page/file),
               100-character lines; a warning past 200 code lines and a failure
               past 300 (blank lines, comments and docstrings do not count; data
               files listed in SIZE_EXEMPT, each with its reason, skip the size
               limits; logic never does)
  Pages        each folder in delivery/web/ is one page: <page>.py, plus files named
               <page>.html, <page>.css, <page>.js or <page>_<part>.<ext>
  Comments     every .py file opens with a docstring, every "Decision: <name>" has a
               docs/decisions/<name>.md, every docs/....md a comment names exists,
               and every TODO names its issue: TODO(#123)

Two presentation rules need no check here because string.Template cannot break
them: a template cannot name an entity, and a feature's view cannot render
another feature's view or a page template. Check them if your templates can
run code.
"""

import ast
import builtins
import io
import re
import sys
import tokenize
from pathlib import Path

ZONES = ("shared", "entities", "features", "integrations", "delivery")
CORE = ("shared", "entities", "features")
IO_MODULES = {"os", "sys", "io", "pathlib", "shutil", "subprocess", "socket", "sqlite3",
              "http", "urllib", "smtplib", "tomllib", "wsgiref", "requests"}
CLOCK_CALLS = ("datetime.now", "datetime.utcnow", "datetime.today", "date.today",
               "time.time", "time.time_ns", "time.monotonic")
MAX_LINE, MAX_DEPTH = 100, 3
# A file past TARGET_LINES code lines gets a warning: look for a concept hiding in it.
# Past MAX_LINES it fails. Counting only code keeps comments from being cut to pass.
TARGET_LINES, MAX_LINES = 200, 300
# Files that are data, not logic (a lookup table, generated code), and why each may
# pass the size limits. This app needs none.
SIZE_EXEMPT: dict[str, str] = {}
BUILTIN_EXCEPTIONS = {name for name, value in vars(builtins).items()
                      if isinstance(value, type) and issubclass(value, BaseException)}
DECISION = re.compile(r"Decision: (\w+)")
DOC_PATH = re.compile(r"\bdocs/[\w./-]+\.md\b")
TODO_WITHOUT_ISSUE = re.compile(r"\bTODO\b(?!\([^)\s]+\))")
BLOCK_COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->", re.DOTALL)
NOT_CODE = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT,
            tokenize.DEDENT, tokenize.ENDMARKER}


def source_files(src: Path) -> list[Path]:
    return [path for path in sorted(src.rglob("*"))
            if path.is_file() and path.suffix in (".py", ".html", ".css", ".js")]


def check(src: Path, decisions: Path | None = None) -> list[str]:
    decisions = decisions or src.parent / "docs" / "decisions"
    problems = []
    for path in source_files(src):
        problems += check_spread(src, path) + check_comments(src, path, decisions)
        if path.suffix == ".py":
            problems += check_python(src, path)
    return problems + check_pages(src / "delivery" / "web")


def warnings(src: Path) -> list[str]:
    """Files past the size target but under the limit. These never fail the build."""
    found = []
    for path in source_files(src):
        rel = path.relative_to(src).as_posix()
        count = code_lines(path)
        if rel not in SIZE_EXEMPT and TARGET_LINES < count <= MAX_LINES:
            found.append(f"{rel}: {count} code lines (aim for {TARGET_LINES}); "
                         "is a concept hiding in it?")
    return found


def code_lines(path: Path) -> int:
    """Lines holding code: not blank, not only a comment, not part of a docstring."""
    text = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        text = BLOCK_COMMENT.sub(lambda m: "\n" * m.group().count("\n"), text)
        return sum(1 for line in text.splitlines()
                   if line.strip() and not line.strip().startswith("//"))
    lines: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type not in NOT_CODE:
            lines.update(range(token.start[0], token.end[0] + 1))
    for node in ast.walk(ast.parse(text)):
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str) and node.end_lineno):
            lines -= set(range(node.lineno, node.end_lineno + 1))
    return len(lines)


def check_comments(src: Path, path: Path, decisions: Path) -> list[str]:
    rel = path.relative_to(src)
    problems = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for name in DECISION.findall(line):
            if not (decisions / f"{name}.md").is_file():
                problems.append(f"{rel}:{number}: names decision {name}, "
                                f"but docs/decisions/{name}.md does not exist")
        for doc in DOC_PATH.findall(line):
            if not (src.parent / doc).is_file():
                problems.append(f"{rel}:{number}: names {doc}, which does not exist")
        if TODO_WITHOUT_ISSUE.search(line):
            problems.append(f"{rel}:{number}: a TODO names its issue: TODO(#123)")
    return problems


def check_spread(src: Path, path: Path) -> list[str]:
    rel = path.relative_to(src)
    problems = []
    depth = MAX_DEPTH + 1 if rel.parts[0] == "delivery" else MAX_DEPTH
    if len(rel.parts) > depth:
        shape = "delivery/door/page/file" if rel.parts[0] == "delivery" else "zone/owner/file"
        problems.append(f"{rel}: deeper than {shape}")
    if rel.as_posix() in SIZE_EXEMPT:
        return problems
    count = code_lines(path)
    if count > MAX_LINES:
        problems.append(f"{rel}: {count} code lines (max {MAX_LINES}); "
                        "a concept is hiding in it")
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        if len(line) > MAX_LINE:
            problems.append(f"{rel}:{number}: {len(line)} characters (max {MAX_LINE})")
    return problems


def check_pages(web: Path) -> list[str]:
    if not web.is_dir():
        return []
    problems = []
    for folder in sorted(p for p in web.iterdir() if p.is_dir() and p.name != "__pycache__"):
        page = folder.name
        files = [p.name for p in folder.iterdir() if p.is_file()]
        if f"{page}.py" not in files:
            problems.append(f"delivery/web/{page}: a page folder needs {page}.py")
        for name in sorted(files):
            if name.split(".")[0] != page and not name.startswith(f"{page}_"):
                problems.append(f"delivery/web/{page}/{name}: page files are named for the page")
    return problems


def check_python(src: Path, path: Path) -> list[str]:
    rel = path.relative_to(src)
    zone = rel.parts[0]
    owner = rel.parts[1] if len(rel.parts) > 2 else ""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(rel))
    problems = []
    if not ast.get_docstring(tree):
        problems.append(f"{rel}: no header; open with a docstring that says what it does")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            problems.append(f"{rel}:{node.lineno}: relative import; use the full path")
        for module in imported_modules(node):
            reason = import_problem(zone, owner, rel, module)
            if reason:
                line = getattr(node, "lineno", 0)
                problems.append(f"{rel}:{line}: imports {module}, but {reason}")
        if isinstance(node, ast.ClassDef) and not allowed_bases(node.bases):
            problems.append(f"{rel}:{node.lineno}: {node.name} inherits; compose instead")
        if zone in CORE and isinstance(node, ast.Call) and reads_clock(node):
            problems.append(f"{rel}:{node.lineno}: reads the clock; pass the time in")
    return problems


def imported_modules(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module]
    return []


def import_problem(zone: str, owner: str, rel: Path, module: str) -> str:
    parts = module.split(".")
    target, target_owner = parts[0], (parts[1] if len(parts) > 1 else "")
    if target not in ZONES:
        if zone in CORE and target in IO_MODULES:
            return f"{zone} must not touch the outside world"
        return ""
    own_folder = target == zone and target_owner == owner
    if zone == "shared":
        allowed = target == "shared"
    elif zone == "entities":
        allowed = own_folder
    elif zone in ("features", "integrations"):
        allowed = target in ("entities", "shared") or own_folder
    else:  # delivery
        is_wiring = rel.as_posix() == "delivery/wiring.py"
        allowed = is_wiring or target in ("features", "shared", "delivery")
    return "" if allowed else f"{zone}/{owner or rel.name} may not import from {target}"


def allowed_bases(bases: list[ast.expr]) -> bool:
    """Contracts subclass Protocol. A custom error may subclass one built-in exception,
    because Python only raises exceptions."""
    base = bases[0] if len(bases) == 1 else None
    if isinstance(base, ast.Name) and base.id in BUILTIN_EXCEPTIONS:
        return True
    return all(is_protocol(b) for b in bases)


def is_protocol(base: ast.expr) -> bool:
    if isinstance(base, ast.Subscript):
        base = base.value
    return isinstance(base, ast.Name) and base.id == "Protocol"


def reads_clock(call: ast.Call) -> bool:
    return dotted_name(call.func).endswith(CLOCK_CALLS)


def dotted_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{dotted_name(node.value)}.{node.attr}"
    return ""


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    for warning in warnings(root / "src"):
        print(f"arch_check warning: {warning}", file=sys.stderr)
    found = check(root / "src")
    if found:
        print("arch_check FAILED:\n  " + "\n  ".join(found), file=sys.stderr)
        raise SystemExit(1)
    print("arch_check OK: imports, purity, no inheritance, spread, pages, comments")
