"""報告落地：new_report.sh 產生的路徑與 .gitignore。

報告檔名帶時間戳、目錄要自己擋掉版控，這兩件事是固定流程，
交給腳本才不會每次拼得不一樣。
"""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import checker

SCRIPT = str(checker.SKILL_DIR / "scripts" / "new_report.sh")


def run(src):
    return subprocess.run(
        ["bash", SCRIPT, str(src)], capture_output=True, text=True
    )


class TestReportPath(unittest.TestCase):
    def _fake_project(self, tmp, name="README.md"):
        """建一個不在 git repo 裡的假專案，讓腳本走標記檔那條路徑。"""
        root = Path(tmp)
        (root / "package.json").write_text("{}", encoding="utf-8")
        src = root / name
        src.write_text("# 測試\n", encoding="utf-8")
        return root, src

    def test_path_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = self._fake_project(tmp)
            out = Path(run(src).stdout.strip())
            self.assertEqual(
                root / "docs" / "chinese-copywriting", out.parent,
                "報告要落在專案根的 docs/chinese-copywriting/ 底下",
            )
            self.assertRegex(
                out.name, r"^\d{8}-\d{6}-README\.md$",
                "檔名格式是 {年月日}-{時分秒}-{原檔案名稱}.{副檔名}",
            )

    def test_extension_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, src = self._fake_project(tmp, "規格.txt")
            out = Path(run(src).stdout.strip())
            self.assertRegex(out.name, r"^\d{8}-\d{6}-規格\.txt$")

    def test_gitignore_created_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = self._fake_project(tmp)
            run(src)
            ignore = root / "docs" / "chinese-copywriting" / ".gitignore"
            self.assertTrue(ignore.exists(), "第一次建立目錄要補上 .gitignore")
            body = ignore.read_text(encoding="utf-8")
            self.assertIn("*", body)
            self.assertEqual(
                [], [ln for ln in body.splitlines() if ln.startswith("!")],
                "這個目錄整個不進版控，沒有例外——報告、裁決、.gitignore 自己都算",
            )

            ignore.write_text("# 使用者改過的\n*\n", encoding="utf-8")
            run(src)
            self.assertEqual(
                "# 使用者改過的\n*\n", ignore.read_text(encoding="utf-8"),
                "已存在的 .gitignore 不得被覆寫",
            )

    def test_does_not_write_the_report_itself(self):
        """腳本只給路徑，內容由模型寫。先建檔會蓋掉還沒寫的報告。"""
        with tempfile.TemporaryDirectory() as tmp:
            _, src = self._fake_project(tmp)
            out = Path(run(src).stdout.strip())
            self.assertFalse(out.exists())

    def test_missing_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(Path(tmp) / "不存在.md")
            self.assertNotEqual(0, r.returncode, "找不到原檔要回非零")


if __name__ == "__main__":
    unittest.main()
