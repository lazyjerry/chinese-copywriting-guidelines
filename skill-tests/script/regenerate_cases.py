#!/usr/bin/env python3
"""重新產生 cases.json。

新增或修改 cases/ 底下的樣本、或改動 gaps.py 之後跑這支，
把腳本的現行行為重新快照下來。

    python3 skill-tests/script/regenerate_cases.py

產出的 expect 是「實際輸出扣掉已知誤報」，所以綠燈測試不會被誤報污染；
missed 類的缺陷本來就不在輸出裡，自然也不在 expect。

--fix 的行為刻意不快照。修正後不該殘留可修正違規、跑第二次不該再改動，
這兩條是不變量而不是現況，寫成斷言放在 test_fix.py。
"""

import json
from pathlib import Path

import checker
import gaps

HERE = Path(__file__).resolve().parent

TITLES = {
    "case-01-clean.md": "全部寫對的基準文本",
    "case-02-latin-space.md": "中英文與數字之間的空格",
    "case-03-units.md": "數字與單位之間的空格",
    "case-04-punct-space.md": "全形標點兩側的空白",
    "case-05-duplicate.md": "重複使用標點符號",
    "case-06-halfwidth.md": "全形與半形標點",
    "case-07-english.md": "英文整句與書名內的標點",
    "case-08-masking.md": "遮罩區段一律不檢查",
    "case-09-code-span.md": "行內程式碼兩側的空格",
    "case-10-dispute.md": "爭議規則預設關閉",
}


def snapshot(path):
    rel = f"cases/{path.name}"
    issues = checker.check_file(str(path))
    effective = [i for i in issues if not gaps.is_known_false_positive(rel, i)]

    return {
        "file": rel,
        "title": TITLES[path.name],
        "expect_total": len(effective),
        "expect": [
            {"line": i.line, "col": i.col, "rule": i.rule, "snippet": i.snippet}
            for i in effective
        ],
        "dispute_total": len(
            [i for i in checker.check_file(str(path), dispute=True)
             if not gaps.is_known_false_positive(rel, i)]
        ),
        "gaps": gaps.gaps_for(rel),
        "fix_gaps": gaps.fix_gaps_for(rel),
    }


def main():
    cases = [snapshot(p) for p in sorted((HERE / "cases").glob("case-*.md"))]
    out = {
        "note": "由 regenerate_cases.py 產生，不要手改。改樣本或 gaps.py 之後重跑。",
        "cases": cases,
    }
    (HERE / "cases.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total_expect = sum(c["expect_total"] for c in cases)
    total_gaps = sum(len(c["gaps"]) + len(c["fix_gaps"]) for c in cases)
    print(f"寫入 cases.json：{len(cases)} 個 case、綠燈 {total_expect} 項、紅燈 {total_gaps} 項")


if __name__ == "__main__":
    main()
