"""綠燈：鎖住腳本現行正確的行為。

資料在 cases.json，由 regenerate_cases.py 產生。這裡只有邏輯，沒有資料——
要加一個案例，寫一份 cases/case-*.md 再重跑產生器就好，不必動這個檔。
"""

import json
import unittest
from pathlib import Path

import checker
import gaps

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
REPO_ROOT = checker.REPO_ROOT


def _effective(rel, issues):
    """扣掉已知誤報。誤報修好之後這些項目會自然消失，綠燈不受影響。"""
    return [i for i in issues if not gaps.is_known_false_positive(rel, i)]


class TestCases(unittest.TestCase):
    def test_expect_matches_exactly(self):
        for case in DATA["cases"]:
            rel = case["file"]
            with self.subTest(case=rel, title=case["title"]):
                actual = _effective(rel, checker.check_file(str(HERE / rel)))
                got = [(i.line, i.col, i.rule, i.snippet) for i in actual]
                want = [(e["line"], e["col"], e["rule"], e["snippet"]) for e in case["expect"]]
                self.assertEqual(
                    want, got,
                    f"\n{rel}（{case['title']}）的違規清單與快照不符。"
                    f"\n若這是刻意的改動，重跑 regenerate_cases.py 更新快照；"
                    f"\n若不是，腳本的行為被改壞了。",
                )

    def test_expect_total(self):
        for case in DATA["cases"]:
            rel = case["file"]
            with self.subTest(case=rel):
                actual = _effective(rel, checker.check_file(str(HERE / rel)))
                self.assertEqual(case["expect_total"], len(actual))

    def test_dispute_total(self):
        for case in DATA["cases"]:
            rel = case["file"]
            with self.subTest(case=rel):
                actual = _effective(rel, checker.check_file(str(HERE / rel), dispute=True))
                self.assertEqual(case["dispute_total"], len(actual))

    def test_dispute_rules_off_by_default(self):
        for case in DATA["cases"]:
            rel = case["file"]
            with self.subTest(case=rel):
                rules = {i.rule for i in checker.check_file(str(HERE / rel))}
                self.assertFalse(
                    rules & {"R11", "R12"},
                    "爭議規則必須要加 --dispute 才檢查，預設不得出現",
                )


class TestDeliberateBehaviour(unittest.TestCase):
    """乙類：刻意不做的事。有人日後想「順手補上」就會撞到這裡。"""

    def assert_clean(self, text, why):
        issues = checker.check_text(text)
        self.assertEqual([], [(i.line, i.rule, i.snippet) for i in issues], why)

    def test_dash_and_tilde_keep_surrounding_space(self):
        self.assert_clean(
            "拍照表現—— 尤其是夜景—— 進步得相當明顯。\n\n價格帶落在三萬 ～ 四萬之間。\n",
            "破折號與波浪號兩側留白是刻意保留的排版風格，指北沒有對應範例，不得報違規",
        )

    def test_single_letter_units_not_collected(self):
        self.assert_clean(
            "他是在 the 90s 長大的，身高 3m 的雕像立在門口，額定 5A 的保險絲燒了。\n",
            "單字母單位會把英文大量誤判，刻意不收進 UNITS",
        )

    def test_english_word_lookalike_units_not_collected(self):
        self.assert_clean(
            "資料寫在 4in 的欄位，農地面積 3ha，時間標記 2at 都不該被當成單位。\n",
            "與英文單字撞名的組合刻意不收",
        )

    def test_markdown_table_separator_not_flagged(self):
        self.assert_clean(
            "| 型號 | 螢幕（吋） | 售價（元） |\n| --- | --- | --- |\n| 進階版（含配件） | 6.7 | 36900 |\n",
            "表格分隔線的空白是 Markdown 語法，不是文案裡的空格；"
            "這是施工筆記記載過的舊 bug，改動 R4 的字元集合時最容易復發",
        )

    def test_r9_r10_left_to_the_model(self):
        issues = checker.check_text(
            "我們的客戶有 Github、FourSquare、MicroSoft Corporation。\n\n"
            "需要一位熟悉 Ts、h5 的 FED。\n"
        )
        self.assertEqual(
            [], issues,
            "專有名詞大小寫與不道地縮寫刻意交給模型判斷，腳本不得擅自開始偵測",
        )

    def test_rule_titles_has_no_r9_r10(self):
        self.assertNotIn("R9", checker.RULE_TITLES)
        self.assertNotIn("R10", checker.RULE_TITLES)


class TestRuleBookInvariants(unittest.TestCase):
    """真實規則書的不變量。巢狀括號 bug 當初就是漏在這裡。"""

    READMES = ["README.md", "README.en.md", "README.zh-Hans.md"]

    # 三份 README 的示範標記各自不同，繁中／簡中／英文都要認得
    BAD_MARKERS = ("錯誤：", "错误：", "Bad:")
    RESET_MARKERS = ("正確：", "正确：", "Good:", "例外", "例外：", "注意：", "Exception")

    @classmethod
    def _demo_lines(cls, path):
        """標出「錯誤：」底下的引用區塊——那些是刻意寫錯的教材。"""
        bad, mode = set(), None
        for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if line.startswith("#"):
                mode = None
            elif line.startswith(cls.BAD_MARKERS):
                mode = "bad"
            elif line.startswith(cls.RESET_MARKERS):
                mode = None
            elif line.startswith(">"):
                if mode == "bad":
                    bad.add(n)
            elif line.strip():
                mode = None
        return bad

    def test_prose_is_clean(self):
        for name in self.READMES:
            path = REPO_ROOT / name
            with self.subTest(readme=name):
                demo = self._demo_lines(path)
                stray = [
                    f"L{i.line} [{i.rule}] {i.snippet}"
                    for i in checker.check_file(str(path))
                    if i.line not in demo
                ]
                self.assertEqual(
                    [], stray,
                    f"{name} 的正文與「正確：」示範不得有違規。"
                    f"\n落在示範區之外的違規幾乎都是誤報。",
                )


if __name__ == "__main__":
    unittest.main()
