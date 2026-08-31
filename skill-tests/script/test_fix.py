"""--fix 的正確性。

逐條規則的修正結果用短輸入直接寫在這裡，不需要 500 字的樣本；
樣本檔那一層只驗「修完要乾淨、再跑不動」這兩條不變量。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import checker

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))


class TestFixPerRule(unittest.TestCase):
    def assert_fix(self, before, after, why):
        got, _ = checker.fix_text(before)
        self.assertEqual(after, got, why)

    def test_r1_latin_space(self):
        self.assert_fix(
            "在LeanCloud上，資料儲存是圍繞`AVObject`進行的。\n",
            "在 LeanCloud 上，資料儲存是圍繞 `AVObject` 進行的。\n",
            "規則 1：中英文之間與行內程式碼兩側都要補空格",
        )

    def test_r2_digit_space(self):
        self.assert_fix(
            "今天出去買菜花了5000元。\n",
            "今天出去買菜花了 5000 元。\n",
            "規則 2：中文與數字之間要補空格",
        )

    def test_r3_unit_space(self):
        self.assert_fix(
            "我家的光纖入屋寬頻有 10Gbps，SSD 一共有 20TB。\n",
            "我家的光纖入屋寬頻有 10 Gbps，SSD 一共有 20 TB。\n",
            "規則 3：數字與單位之間要補空格",
        )

    def test_r3_degree_and_percent(self):
        self.assert_fix(
            "角度為 90 ° 的角。新 MacBook Pro 有 15 % 的效能提升。\n",
            "角度為 90° 的角。新 MacBook Pro 有 15% 的效能提升。\n",
            "規則 3 例外：度數與百分比要把多餘空格收掉",
        )

    def test_r4_fullwidth_space(self):
        self.assert_fix(
            "剛剛買了一部 iPhone ，好開心！\n剛剛買了一部 iPhone， 好開心！\n",
            "剛剛買了一部 iPhone，好開心！\n剛剛買了一部 iPhone，好開心！\n",
            "規則 4：全形標點前後的空白要收掉",
        )

    def test_r5_duplicate_punct(self):
        self.assert_fix(
            "德國隊竟然戰勝了巴西隊！！\n她竟然對你說「喵」？？！！\n她竟然對你說「喵」？！\n",
            "德國隊竟然戰勝了巴西隊！\n她竟然對你說「喵」？！\n她竟然對你說「喵」？！\n",
            "規則 5：重複標點收成一組；單一組「？！」保持不變",
        )

    def test_r7_fullwidth_digit(self):
        self.assert_fix(
            "這件蛋糕只賣 １０００ 元。\n",
            "這件蛋糕只賣 1000 元。\n",
            "規則 7：全形數字轉半形",
        )


class TestFixBoundaries(unittest.TestCase):
    def test_non_fixable_rules_untouched(self):
        text = "嗨!你知道嘛?今天前台的小妹跟我說\"喵\"了哎!\n賈伯斯說：「Stay hungry，stay foolish。」\n"
        got, changed = checker.fix_text(text)
        self.assertEqual(text, got, "規則 6、8 需要語意判斷，--fix 一律不得動")
        self.assertEqual(0, changed)

    def test_masked_regions_untouched(self):
        text = (
            "```js\nconst 設定 = {名稱:\"值10筆\"};\n```\n\n"
            "行內程式碼 `一共有20TB` 的內容不動。\n\n"
            "連結 [pangu.js](https://github.com/vinta/pangu.js) 與網址 https://example.com/中文path 不動。\n\n"
            "豆瓣FM 是官方寫法。\n"
        )
        got, changed = checker.fix_text(text)
        self.assertEqual(text, got, "遮罩區段與豁免名詞在 --fix 之後必須逐字不變")
        self.assertEqual(0, changed)

    def test_table_separator_untouched(self):
        text = "| 型號 | 螢幕（吋） |\n| --- | --- |\n| 進階版（含配件） | 6.7 |\n"
        got, _ = checker.fix_text(text)
        self.assertEqual(text, got, "表格語法不得被 --fix 重排")

    def test_missing_trailing_newline_preserved(self):
        got, _ = checker.fix_text("在LeanCloud上開發。")
        self.assertEqual("在 LeanCloud 上開發。", got, "檔尾沒有換行就不要補上")


class TestFixOnSamples(unittest.TestCase):
    """樣本層的不變量。有登記 fix 缺陷的案例歸 test_gaps.py 管，這裡只跑其餘的。"""

    def _fix_twice(self, rel):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / Path(rel).name
            shutil.copy(HERE / rel, copy)
            checker.fix_file(str(copy))
            left = [i for i in checker.check_file(str(copy)) if i.rule in checker.FIXABLE]
            again = checker.fix_file(str(copy))
        return left, again

    def test_clean_and_idempotent(self):
        for case in DATA["cases"]:
            if case["fix_gaps"]:
                continue
            rel = case["file"]
            with self.subTest(case=rel):
                left, again = self._fix_twice(rel)
                self.assertEqual(
                    [], [f"L{i.line} [{i.rule}]" for i in left],
                    "--fix 跑完不得殘留可修正的違規",
                )
                self.assertEqual(0, again, "--fix 必須是不動點，第二次不該再改動")


if __name__ == "__main__":
    unittest.main()
