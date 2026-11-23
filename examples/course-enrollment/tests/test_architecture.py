"""The checker passes on this app and catches each kind of violation."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import arch_check  # noqa: E402
from arch_check import check  # noqa: E402

BAD_FILES = {
    "entities/course/course.py": "from entities.student.student import Student\n",
    "features/enroll/enroll.py": "from integrations.database.course_store import SqlCourseStore\n",
    "entities/student/student.py": "class Student(Person):\n    pass\n",
    "features/drop/drop.py": "from datetime import datetime\nNOW = datetime.now()\n",
    "shared/clock.py": "import sqlite3\n",
    "delivery/web/app.py": "from integrations.email.file_mailer import FileMailer\n",
    "integrations/email/mailer.py": "x = '" + "a" * 120 + "'\n",
    "delivery/web/roster/roster.py": "",
    "delivery/web/roster/helpers.py": "",
    "delivery/web/grades/grades.html": "",
    "delivery/web/roster/parts/table.html": "",
}


class ArchitectureTest(unittest.TestCase):
    def test_this_app_follows_the_rules(self) -> None:
        self.assertEqual(check(ROOT / "src"), [])

    def test_catches_each_kind_of_violation(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)
            for rel, text in BAD_FILES.items():
                (src / rel).parent.mkdir(parents=True, exist_ok=True)
                (src / rel).write_text(text, encoding="utf-8")
            problems = "\n".join(check(src))
        for expected in ("entities/course may not import from entities",
                         "features/enroll may not import from integrations",
                         "Student inherits", "reads the clock",
                         "shared must not touch the outside world",
                         "delivery/web may not import from integrations",
                         "characters (max 100)",
                         "roster/helpers.py: page files are named for the page",
                         "delivery/web/grades: a page folder needs grades.py",
                         "deeper than delivery/door/page/file"):
            self.assertIn(expected, problems)

    def test_a_custom_error_may_extend_one_builtin_exception(self) -> None:
        errors = ("class CourseFull(ValueError):\n    pass\n\n\n"
                  "class WaitlistFull(CourseFull):\n    pass\n")
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)
            (src / "entities/course").mkdir(parents=True)
            (src / "entities/course/course_full.py").write_text(errors, encoding="utf-8")
            problems = "\n".join(check(src))
        self.assertNotIn("CourseFull inherits", problems)
        self.assertIn("WaitlistFull inherits", problems)


    def test_a_listed_data_file_may_pass_the_size_limits(self) -> None:
        table = '"""Bot names."""\nPATTERNS = [\n' + "    'bot',\n" * 320 + "]\n"
        exempt = {"integrations/bots/patterns.py": "a lookup table, not logic"}
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)
            (src / "integrations/bots").mkdir(parents=True)
            (src / "integrations/bots/patterns.py").write_text(table, encoding="utf-8")
            (src / "integrations/bots/rules.py").write_text(table, encoding="utf-8")
            with mock.patch.dict(arch_check.SIZE_EXEMPT, exempt):
                problems = "\n".join(check(src))
        self.assertNotIn("patterns.py", problems)
        self.assertIn("rules.py: 322 code lines (max 300)", problems)

    def test_size_counts_code_warns_past_200_and_fails_past_300(self) -> None:
        def module(code: int, comments: int = 0) -> str:
            header = '"""A header.\n\nThat runs\nover lines.\n"""\n'
            return header + "# why\n\n" * comments + "x = 1\n" * code

        files = {"long": module(250), "too_long": module(310),
                 "explained": module(150, comments=200)}
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder)
            (src / "shared").mkdir()
            for name, text in files.items():
                (src / f"shared/{name}.py").write_text(text, encoding="utf-8")
            problems = "\n".join(check(src))
            warned = "\n".join(arch_check.warnings(src))
        self.assertIn("too_long.py: 310 code lines (max 300)", problems)
        self.assertNotIn("shared/long.py", problems)
        self.assertIn("shared/long.py: 250 code lines (aim for 200)", warned)
        self.assertNotIn("too_long", warned)
        self.assertNotIn("explained", problems + warned)

    def test_headers_decisions_and_todos(self) -> None:
        files = {
            "src/features/drop/drop.py": "x = 1\n",
            "src/features/enroll/enroll.py": '"""Enroll."""\n# TODO: a waitlist\n',
            "src/features/transfer/transfer.py": '"""Move."""\n# TODO(#142): a waitlist\n',
            "src/integrations/database/store.py": '"""S."""\n# Gone (Decision: no_soft_deletes)\n',
            "src/integrations/database/seeder.py": '"""Seed."""\n# Demo (Decision: demo_data)\n',
            "src/shared/__init__.py": '"""Zone: shared. See docs/02-zones.md."""\n',
            "docs/decisions/demo_data.md": "# Demo data\n",
        }
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for rel, text in files.items():
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(text, encoding="utf-8")
            problems = "\n".join(check(root / "src"))
        self.assertIn("features/drop/drop.py: no header", problems)
        self.assertIn("enroll.py:2: a TODO names its issue", problems)
        self.assertNotIn("transfer.py", problems)
        self.assertIn("names decision no_soft_deletes, but docs/decisions/", problems)
        self.assertNotIn("demo_data", problems)
        self.assertIn("shared/__init__.py:1: names docs/02-zones.md, which does not", problems)


if __name__ == "__main__":
    unittest.main()
