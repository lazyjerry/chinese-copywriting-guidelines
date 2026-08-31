"""--units：擴充規則 3 的單位表。

內建的 UNITS 是篩過的，帶進來的沒有。單位縮寫跟產品代號在正則眼裡一模一樣
（`5G` 對 `3bar`），所以自訂單位一律標 low、不自動修，留給裁決步驟判。
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import checker

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
SCRIPT = str(checker.SCRIPT_PATH)
CLEAN = str(HERE / "cases" / "case-01-clean.md")


def run(*args):
    return subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True
    )


class TestParseUnits(unittest.TestCase):
    def test_splits_and_trims(self):
        self.assertEqual(["kHz", "ms"], checker.parse_units(" kHz , ms "))

    def test_empty_input(self):
        self.assertEqual([], checker.parse_units(""))
        self.assertEqual([], checker.parse_units(None))
        self.assertEqual([], checker.parse_units(",,"))


class TestCustomUnitDetection(unittest.TestCase):
    TEXT = "取樣率 44.1kHz，延遲 100ms。\n"

    def test_not_detected_without_flag(self):
        self.assertEqual([], checker.check_text(self.TEXT))

    def test_detected_with_flag(self):
        issues = checker.check_text(self.TEXT, extra_units=["kHz", "ms"])
        self.assertEqual(
            [("R3", "kHz"), ("R3", "ms")],
            sorted((i.rule, i.message.split("「")[1].split("」")[0]) for i in issues),
        )

    def test_custom_units_are_low_and_unfixable(self):
        for issue in checker.check_text(self.TEXT, extra_units=["kHz", "ms"]):
            self.assertEqual("low", issue.confidence)
            self.assertFalse(issue.fixable, "自訂單位可能是產品代號，不得自動修")

    def test_builtin_units_stay_high(self):
        issues = checker.check_text("硬碟 20TB。\n", extra_units=["kHz"])
        self.assertEqual(["high"], [i.confidence for i in issues])
        self.assertTrue(all(i.fixable for i in issues))

    def test_fix_leaves_custom_units_alone(self):
        got, changed = checker.fix_text(self.TEXT, extra_units=["kHz", "ms"])
        self.assertEqual(self.TEXT, got)
        self.assertEqual(0, changed)

    def test_no_state_leaks_between_runs(self):
        """自訂單位是模組級狀態，下一次不帶旗標時必須回到內建表。"""
        checker.check_text(self.TEXT, extra_units=["kHz", "ms"])
        self.assertEqual([], checker.check_text(self.TEXT))


class TestOverlapWithProductNames(unittest.TestCase):
    """預期會出錯的例子：帶了 --units 之後 `5G` 一定會被報成違規，那就是誤報。

    語料與各筆的裁決結論在 `gaps.py` 的 ADJUDICATION，樣本檔是
    `cases/case-11-unit-overlap.md`，兩者都會出現在 KNOWN-GAPS.md 的〈需裁決〉。

    這一組盯的不是「誤報有沒有消失」——`5G` 與 `3bar` 在 UNIT_RE 眼裡形狀相同，
    那是資訊上的限制不是實作缺陷，修不好。這裡盯的是**誤報不會造成傷害**。
    模型有沒有真的 drop 掉，只有 evals/cases/custom-unit-overlap 測得到。
    """

    CASE = "cases/case-11-unit-overlap.md"

    def setUp(self):
        self.case = next(c for c in DATA["cases"] if c["file"] == self.CASE)
        self.rows = self.case["adjudication"]
        self.units = self.case["adjudication_units"]
        self.path = str(HERE / self.CASE)

    def _hits(self, extra_units):
        return checker.check_file(self.path, extra_units=extra_units)

    def test_corpus_covers_both_verdicts(self):
        verdicts = {r["verdict"] for r in self.rows}
        self.assertEqual(
            {"code", "measure"}, verdicts,
            "語料要同時有代號與量測值，否則測不出「腳本不分辨」這件事",
        )

    def test_nothing_reported_without_flag(self):
        """誤報只在使用者主動擴充單位表時才存在，預設一筆都沒有。"""
        reported = {
            (i.line, i.snippet) for i in self._hits(())
        }
        for row in self.rows:
            with self.subTest(hit=row["contains"]):
                self.assertFalse(
                    any(row["contains"] in snip for _, snip in reported
                        if _ == row["line"]),
                    f"不帶 --units 時「{row['contains']}」不該被報出來",
                )

    def test_every_row_is_reported_with_flag(self):
        hits = self._hits(self.units)
        for row in self.rows:
            with self.subTest(hit=row["contains"], verdict=row["verdict"]):
                matched = [
                    i for i in hits
                    if i.line == row["line"] and row["contains"] in i.snippet
                ]
                self.assertTrue(
                    matched,
                    f"「{row['contains']}」（{row['why']}）應該被報出來，"
                    f"由裁決步驟決定去留",
                )

    def test_measurements_are_low_too(self):
        """量測值也標 low，腳本不得自作聰明分辨。

        有人日後想在腳本裡加啟發式（看前後文有沒有「輸出」「壓力」）就會撞到這裡。
        那是裁決步驟的職責，塞進正則只會換一種誤判。
        """
        rows_by_line = {}
        for row in self.rows:
            rows_by_line.setdefault(row["line"], []).append(row)
        for issue in self._hits(self.units):
            if issue.confidence == "high":
                continue  # 內建單位的命中，不歸這組管
            with self.subTest(line=issue.line, snippet=issue.snippet[:20]):
                self.assertEqual("low", issue.confidence)
                self.assertFalse(issue.fixable)

    def test_fix_never_touches_them(self):
        """最關鍵的一條：報錯無傷，改錯有傷。

        `5G` 被改成 `5 G` 是把對的文章改壞，比漏報嚴重得多。
        內建單位（`400Mbps`）照常修，這裡只驗自訂單位那幾筆原封不動。
        """
        original = Path(self.path).read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "case.md"
            copy.write_text(original, encoding="utf-8")
            checker.fix_file(str(copy), extra_units=self.units)
            fixed = copy.read_text(encoding="utf-8")
        for row in self.rows:
            with self.subTest(hit=row["contains"]):
                self.assertIn(
                    row["contains"], fixed,
                    f"「{row['contains']}」（{row['why']}）不得被 --fix 動到",
                )


class TestCli(unittest.TestCase):
    def test_flag_end_to_end(self):
        case = str(HERE / "cases" / "case-03-units.md")
        before = json.loads(run("--json", case).stdout)
        after = json.loads(run("--json", "--units", "kHz,ms,mAh,nm,GiB,dB", case).stdout)
        self.assertGreater(len(after), len(before), "帶旗標要抓到更多")
        added = [i for i in after if i["confidence"] == "low"]
        self.assertTrue(added)
        self.assertEqual([], [i for i in added if i["fixable"]])

    def test_clean_file_unaffected(self):
        r = run("--units", "kHz,ms", CLEAN)
        self.assertEqual(0, r.returncode)


if __name__ == "__main__":
    unittest.main()
