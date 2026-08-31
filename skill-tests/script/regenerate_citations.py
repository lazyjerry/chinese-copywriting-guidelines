#!/usr/bin/env python3
"""重新產生 citations-baseline.json。

**不要在測試變紅時直接跑這支把基準蓋掉。** 雜湊對不上代表 README 改了，
要先確認 references/rules.md 的行號與細則要不要跟著改，改完才更新基準。

    python3 skill-tests/script/regenerate_citations.py
"""

import json
from pathlib import Path

import citations

HERE = Path(__file__).resolve().parent
PREFIX_LINES = 266  # 本地 README.md 與上游逐字相同的範圍


def main():
    rules, groups = citations.readme_structure()
    lines = citations.readme_lines()
    baseline = {
        "note": "由 regenerate_citations.py 產生。雜湊對不上時先看 README 改了什麼，不要直接覆蓋。",
        "upstream": "https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.md",
        "upstream_commit": "bd7873c",
        "prefix_lines": PREFIX_LINES,
        "prefix_sha": citations.sha("\n".join(lines[:PREFIX_LINES])),
        "rules": {name: meta["sha"] for name, meta in rules.items()},
        "groups": {name: list(span) for name, span in groups.items()},
        "exception_lines": sorted(citations.readme_exceptions()),
    }
    (HERE / "citations-baseline.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"寫入 citations-baseline.json：{len(baseline['rules'])} 條規則、"
        f"{len(baseline['groups'])} 個章節、{len(baseline['exception_lines'])} 條例外"
    )


if __name__ == "__main__":
    main()
