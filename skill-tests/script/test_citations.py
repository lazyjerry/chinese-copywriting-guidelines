"""引用來源：行號對不對、來源改了有沒有跟上、文件內部一不一致。

references/rules.md 的行號一旦漂掉，就從「事實根據」變成看起來很精確的假話。
這組測試同時擋兩件事：引用本身寫錯，以及來源變了而引用沒跟上。
"""

import json
import re
import unittest
from pathlib import Path

import checker
import citations

HERE = Path(__file__).resolve().parent
BASE = json.loads((HERE / "citations-baseline.json").read_text(encoding="utf-8"))

REFRESH = (
    "\n若這是刻意的改動：先確認 references/rules.md 的行號與細則要不要跟著改，"
    "\n改完再跑 regenerate_citations.py 更新基準。不要直接覆蓋基準了事。"
)


class TestLineNumbers(unittest.TestCase):
    """甲、行號本身正不正確。"""

    def setUp(self):
        self.rules, self.groups = citations.readme_structure()
        self.index = citations.parse_index()

    def test_citation_points_at_the_real_heading(self):
        for row in self.index:
            with self.subTest(rule=row["no"], name=row["name"]):
                self.assertIn(row["name"], self.rules, "索引裡的規則名稱在 README 找不到對應標題")
                parsed = citations.split_citation(f"{row['name']} {row['span']}")
                self.assertIsNotNone(parsed, "引用格式必須是「規則名稱 L起-L迄」")
                _, start, end = parsed
                meta = self.rules[row["name"]]
                self.assertEqual(meta["start"], start, "起始行必須是該 H3 標題所在的行")
                self.assertEqual(meta["end"], end, "結束行必須是下一個同級或更高級標題前的最後一個非空行")

    def test_group_citation_matches(self):
        for row in self.index:
            with self.subTest(rule=row["no"]):
                parsed = citations.split_citation(row["group_citation"])
                self.assertIsNotNone(parsed)
                name, start, end = parsed
                self.assertIn(name, self.groups)
                self.assertEqual(list(self.groups[name]), [start, end])
                self.assertEqual(
                    self.rules[row["name"]]["group"], name,
                    "規則登記的所屬章節與 README 的實際歸屬不符",
                )

    def test_rule_spans_do_not_overlap(self):
        spans = []
        for row in self.index:
            _, start, end = citations.split_citation(f"{row['name']} {row['span']}")
            spans.append((start, end, row["name"]))
        spans.sort()
        for (s1, e1, n1), (s2, _, n2) in zip(spans, spans[1:]):
            self.assertLess(e1, s2, f"「{n1}」與「{n2}」的行號區間重疊")

    def test_rule_spans_sit_inside_their_group(self):
        for row in self.index:
            _, start, end = citations.split_citation(f"{row['name']} {row['span']}")
            _, gs, ge = citations.split_citation(row["group_citation"])
            with self.subTest(rule=row["no"]):
                self.assertGreaterEqual(start, gs)
                self.assertLessEqual(end, ge)

    def test_exception_citations_point_at_exception_lines(self):
        exceptions = citations.readme_exceptions()
        for row in citations.parse_exception_index():
            with self.subTest(desc=row["desc"][:12]):
                parsed = citations.split_citation(row["citation"])
                self.assertIsNotNone(parsed)
                _, start, end = parsed
                hit = [n for n in exceptions if start <= n <= end]
                self.assertTrue(
                    hit,
                    f"引用 {row['citation']} 指到的範圍內沒有任何「例外：」或「注意：」開頭的行",
                )


class TestSourceDrift(unittest.TestCase):
    """乙、來源改了而引用沒跟上。"""

    def setUp(self):
        self.rules, _ = citations.readme_structure()
        self.index = citations.parse_index()

    def test_every_readme_rule_is_indexed(self):
        indexed = {row["name"] for row in self.index}
        missing = sorted(set(self.rules) - indexed)
        self.assertEqual(
            [], missing,
            f"README 有規則沒被收進 references/rules.md 的規則索引：{missing}"
            "\n來源新增了規則，引用索引沒跟上。",
        )

    def test_index_has_no_orphans(self):
        indexed = {row["name"] for row in self.index}
        orphans = sorted(indexed - set(self.rules))
        self.assertEqual(
            [], orphans,
            f"索引裡有 README 找不到的規則：{orphans}"
            "\n來源刪掉或改名了規則，索引留下孤兒條目。",
        )

    def test_rule_bodies_unchanged(self):
        for name, meta in self.rules.items():
            with self.subTest(rule=name):
                self.assertIn(name, BASE["rules"], "這條規則不在基準裡，來源新增了東西" + REFRESH)
                self.assertEqual(
                    BASE["rules"][name], meta["sha"],
                    f"README 的〈{name}〉內文改了，但引用索引與細則不一定跟上。" + REFRESH,
                )

    def test_group_spans_unchanged(self):
        _, groups = citations.readme_structure()
        self.assertEqual(
            {k: list(v) for k, v in groups.items()}, BASE["groups"],
            "README 的章節範圍變了，索引的「所屬章節」欄要重新核對。" + REFRESH,
        )

    def test_every_exception_is_indexed(self):
        cited = []
        for row in citations.parse_exception_index():
            _, start, end = citations.split_citation(row["citation"])
            cited.append((start, end))
        for line in citations.readme_exceptions():
            with self.subTest(line=line):
                self.assertTrue(
                    any(s <= line <= e for s, e in cited),
                    f"README L{line} 的例外沒有出現在例外索引裡。"
                    "\n來源新增了例外，索引沒跟上。",
                )

    def test_exception_line_set_unchanged(self):
        self.assertEqual(
            BASE["exception_lines"], sorted(citations.readme_exceptions()),
            "README 的例外行有增減。" + REFRESH,
        )


class TestSelfConsistency(unittest.TestCase):
    """丙、references/rules.md 內部自我一致。"""

    def setUp(self):
        self.index = citations.parse_index()
        self.inline = citations.parse_inline_citations()

    def test_inline_citation_matches_index(self):
        for row in self.index:
            with self.subTest(rule=row["no"]):
                self.assertIn(row["no"], self.inline, "這條規則的內文缺少「引用參考」那一行")
                self.assertEqual(
                    f"{row['name']} {row['span']}", self.inline[row["no"]],
                    "內文的引用參考與索引表不一致，同一份檔裡兩處對不上",
                )

    def test_every_rule_has_a_detail_section(self):
        self.assertEqual(
            {row["no"] for row in self.index}, set(self.inline),
            "索引表與內文章節的規則編號對不上",
        )

    def test_script_rules_are_all_cited(self):
        names = {row["name"] for row in self.index}
        rules_md = citations.RULES_MD.read_text(encoding="utf-8")
        for rule_id in checker.RULE_TITLES:
            with self.subTest(rule=rule_id):
                no = int(rule_id[1:])
                match = [row for row in self.index if row["no"] == no]
                self.assertTrue(match, f"腳本會輸出 {rule_id}，索引表卻沒有第 {no} 條")
                self.assertIn(match[0]["name"], names)
                self.assertIn(match[0]["name"], rules_md)

    def test_citation_format(self):
        pattern = re.compile(r"^[^ ]+(?: [^ ]+)*? L\d+(?:-L\d+)?$")
        for row in self.index:
            for text in (f"{row['name']} {row['span']}", row["group_citation"]):
                with self.subTest(text=text):
                    self.assertRegex(text, pattern, "引用格式必須是「規則名稱 L起-L迄」，單一半形空格分隔")
                    self.assertNotIn("：", text, "分隔符不得用全形冒號")
                    self.assertNotIn(":", text, "分隔符不得用半形冒號")
                    self.assertNotIn("  ", text, "不得出現連續空格")


class TestSourceIdentity(unittest.TestCase):
    """丁、本地 README 與上游的對應關係還成不成立。"""

    def test_prefix_matches_upstream_snapshot(self):
        lines = citations.readme_lines()
        actual = citations.sha("\n".join(lines[: BASE["prefix_lines"]]))
        self.assertEqual(
            BASE["prefix_sha"], actual,
            f"README.md 前 {BASE['prefix_lines']} 行變了。"
            f"\n這段本來與上游 commit {BASE['upstream_commit']} 逐字相同，"
            f"行號才能兩邊通用；變動之後這個前提不再成立，索引要整份重新核對。" + REFRESH,
        )

    def test_baseline_commit_matches_rules_md(self):
        text = citations.RULES_MD.read_text(encoding="utf-8")
        self.assertIn(
            BASE["upstream_commit"], text,
            "基準記的上游 commit 與 references/rules.md 寫的不一致",
        )
        self.assertIn(BASE["upstream"], text, "基準記的上游網址與 references/rules.md 寫的不一致")


if __name__ == "__main__":
    unittest.main()
