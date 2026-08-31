"""紅燈：腳本現在做不到的事。這些測試**應該是紅的**。

刻意不掛 unittest.expectedFailure——把紅燈藏成綠色等於沒測。
每一則失敗都對應 KNOWN-GAPS.md 的一個段落，修好 check_copywriting.py
之後對應測試會自己轉綠，接著把該筆從 gaps.py 刪掉、重跑 regenerate_cases.py。

三種缺陷：
    missed             該報而沒報
    false_positive     不該報卻報了
    fix 不動點          --fix 自己製造出新的違規，一次 pass 收不乾淨
    行為缺陷            --fix 動到不該動的東西，例如換行風格
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import checker
import gaps

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


def _hits(rel, gap):
    """找出對應這筆缺陷的違規。同一行同規則有多筆時，靠 col 分辨。"""
    col = gap.get("col")
    return [
        i for i in checker.check_file(str(HERE / rel), dispute=True)
        if i.line == gap["line"]
        and i.rule == gap["rule"]
        and gap["contains"] in i.snippet
        and (col is None or i.col == col)
    ]


class TestDetectionGaps(unittest.TestCase):
    def test_missed(self):
        for case in DATA["cases"]:
            for g in case["gaps"]:
                if g["kind"] != "missed":
                    continue
                with self.subTest(case=case["file"], line=g["line"], rule=g["rule"]):
                    self.assertTrue(
                        _hits(case["file"], g),
                        f"\n漏報：{case['file']} L{g['line']} 的「{g['contains']}」"
                        f"應該報 {g['rule']} 卻沒有。"
                        f"\n成因：{g['why']}"
                        f"\n見 KNOWN-GAPS.md",
                    )

    def test_false_positive(self):
        for case in DATA["cases"]:
            for g in case["gaps"]:
                if g["kind"] != "false_positive":
                    continue
                with self.subTest(case=case["file"], line=g["line"], rule=g["rule"]):
                    self.assertEqual(
                        [], [i.snippet for i in _hits(case["file"], g)],
                        f"\n誤報：{case['file']} L{g['line']} 的「{g['contains']}」"
                        f"寫法正確，不該報 {g['rule']}。"
                        f"\n成因：{g['why']}"
                        f"\n誤報比漏報嚴重，會讓使用者把對的文章改壞。"
                        f"\n見 KNOWN-GAPS.md",
                    )


class TestFixGaps(unittest.TestCase):
    """--fix 應該是不動點：跑完就乾淨，再跑一次不動任何一行。"""

    def _fix_twice(self, rel):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / Path(rel).name
            shutil.copy(HERE / rel, copy)
            checker.fix_file(str(copy))
            left = [i for i in checker.check_file(str(copy)) if i.rule in checker.FIXABLE]
            again = checker.fix_file(str(copy))
        return left, again

    def test_fix_leaves_nothing_fixable(self):
        for case in DATA["cases"]:
            if not case["fix_gaps"]:
                continue
            rel = case["file"]
            with self.subTest(case=rel):
                left, _ = self._fix_twice(rel)
                why = "；".join(g["why"] for g in case["fix_gaps"])
                self.assertEqual(
                    [], [f"L{i.line} [{i.rule}] {i.snippet}" for i in left],
                    f"\n--fix 跑完之後還留著可修正的違規。"
                    f"\n成因：{why}"
                    f"\n見 KNOWN-GAPS.md",
                )

    def test_fix_is_idempotent(self):
        for case in DATA["cases"]:
            if not case["fix_gaps"]:
                continue
            rel = case["file"]
            with self.subTest(case=rel):
                _, again = self._fix_twice(rel)
                self.assertEqual(
                    0, again,
                    f"\n--fix 不是不動點：第二次還改了 {again} 行。"
                    f"\n修正過程自己製造出新的違規，而製造出來的那條規則"
                    f"在 FIXERS 裡排得比較前面，同一次 pass 收不到。"
                    f"\n修法是把 FIXERS 迭代到不動點（設迭代上限），不是重排順序。",
                )


class TestBehaviourGaps(unittest.TestCase):
    """不綁樣本檔的行為缺陷。"""

    def test_crlf_is_preserved(self):
        got, _ = checker.fix_text("在LeanCloud上開發。\r\n第二行。\r\n")
        self.assertEqual(
            "在 LeanCloud 上開發。\r\n第二行。\r\n", got,
            "\n--fix 把 CRLF 檔案靜靜改成 LF。"
            "\nfix_file 裡那行 newline = \"\\r\\n\" if ... 看得出本意是保留，"
            "\n但 open() 預設的萬用換行已經先把 \\r\\n 轉成 \\n，條件永遠不成立。"
            "\n修法：open(path, encoding=\"utf-8\", newline=\"\")"
            "\n見 KNOWN-GAPS.md",
        )


if __name__ == "__main__":
    unittest.main()
