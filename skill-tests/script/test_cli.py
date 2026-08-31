"""命令列介面：exit code、輸出格式、旗標。

這一組走 subprocess，因為要驗的正是 main() 的行為，不是 check_file()。
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import checker

HERE = Path(__file__).resolve().parent
SCRIPT = str(checker.SCRIPT_PATH)
CLEAN = str(HERE / "cases" / "case-01-clean.md")
DIRTY = str(HERE / "cases" / "case-02-latin-space.md")


def run(*args):
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )


class TestExitCode(unittest.TestCase):
    def test_clean_file_exits_zero(self):
        r = run(CLEAN)
        self.assertEqual(0, r.returncode)
        self.assertIn("通過，無排版違規", r.stdout)

    def test_dirty_file_exits_one(self):
        r = run(DIRTY)
        self.assertEqual(1, r.returncode, "有違規時要回非零，CI 才擋得住")
        self.assertIn("共 25 項", r.stdout)

    def test_fix_always_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "x.md"
            shutil.copy(DIRTY, copy)
            r = run("--fix", str(copy))
            self.assertEqual(0, r.returncode, "--fix 是修正不是檢查，不該用 exit code 表示違規")
            self.assertIn("修正", r.stdout)


class TestJsonOutput(unittest.TestCase):
    FIELDS = {"path", "line", "column", "rule", "title", "message", "snippet", "fixable"}

    def test_shape(self):
        data = json.loads(run("--json", DIRTY).stdout)
        self.assertTrue(data)
        for item in data:
            self.assertEqual(self.FIELDS, set(item), "JSON 欄位不得增減，下游靠它解析")
            self.assertEqual(item["title"], checker.RULE_TITLES[item["rule"]])
            self.assertIs(item["fixable"], item["rule"] in checker.FIXABLE)

    def test_clean_file_is_empty_array(self):
        self.assertEqual([], json.loads(run("--json", CLEAN).stdout))

    def test_fix_json_reports_line_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "x.md"
            shutil.copy(DIRTY, copy)
            out = json.loads(run("--fix", "--json", str(copy)).stdout)
            self.assertEqual({"fixed_lines"}, set(out))
            self.assertGreater(out["fixed_lines"], 0)


class TestFlags(unittest.TestCase):
    DISPUTE = str(HERE / "cases" / "case-10-dispute.md")

    def test_dispute_off_by_default(self):
        r = run(self.DISPUTE)
        self.assertEqual(0, r.returncode)

    def test_dispute_on_with_flag(self):
        data = json.loads(run("--dispute", "--json", self.DISPUTE).stdout)
        self.assertEqual({"R11", "R12"}, {i["rule"] for i in data})


class TestMultipleFiles(unittest.TestCase):
    def test_results_carry_path_and_stay_sorted(self):
        data = json.loads(run("--json", DIRTY, CLEAN).stdout)
        self.assertEqual({DIRTY}, {i["path"] for i in data}, "乾淨的檔不該產生任何項目")
        keys = [(i["line"], i["column"], i["rule"]) for i in data]
        self.assertEqual(sorted(keys), keys, "同一檔的違規要依行、欄、規則排序")


if __name__ == "__main__":
    unittest.main()
