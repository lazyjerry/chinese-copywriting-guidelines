"""解析引用來源與 references/rules.md 的索引表。

行號的唯一事實根據是上游 README.md：
https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.md
本地 README.md 前 266 行與上游逐字相同，所以離線就能核對。
"""

import hashlib
import re
from pathlib import Path

import checker

REPO_ROOT = checker.REPO_ROOT
README = REPO_ROOT / "README.md"
RULES_MD = checker.SKILL_DIR / "references" / "rules.md"

# 收規則的五個章節，其餘 H2（工具、誰在這樣做？…）不列入
RULE_GROUPS = ("空格", "標點符號", "全形和半形", "名詞", "爭議")

CITATION_RE = re.compile(r"^(?P<name>.+?) (?P<span>L\d+(?:-L\d+)?)$")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def readme_lines():
    return README.read_text(encoding="utf-8").split("\n")


def _headings(lines):
    out = []
    for n, line in enumerate(lines, 1):
        m = re.match(r"^(#{2,3}) (.+)$", line)
        if m:
            out.append((n, len(m.group(1)), m.group(2)))
    return out


def _span(lines, heads, idx):
    start, level, _ = heads[idx]
    end = len(lines)
    for n2, lv2, _ in heads[idx + 1:]:
        if lv2 <= level:
            end = n2 - 1
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return start, end


def readme_structure():
    """回傳 (規則, 章節)。規則的判準是章節內出現範例標記——
    正式規則用「正確：」，爭議規則用「用法：」，
    這樣才分得開真正的規則與 `text-spacing` 那種補充說明。"""
    lines = readme_lines()
    heads = _headings(lines)
    rules, groups, current_group = {}, {}, None

    for i, (n, level, title) in enumerate(heads):
        start, end = _span(lines, heads, i)
        if level == 2:
            current_group = title if title in RULE_GROUPS else None
            if current_group:
                groups[title] = (start, end)
        elif level == 3 and current_group:
            body = lines[start:end]
            if any(l.startswith(("正確：", "用法：")) for l in body):
                rules[title] = {
                    "start": start,
                    "end": end,
                    "group": current_group,
                    "sha": sha("\n".join(body)),
                }
    return rules, groups


def readme_exceptions():
    """README 裡每一行「例外：」與「注意：」的行號。"""
    return {
        n: line
        for n, line in enumerate(readme_lines(), 1)
        if line.startswith(("例外：", "注意："))
    }


def _tables(text):
    """把 markdown 表格切成 (標題, [列]) 的清單。"""
    out, heading, rows = [], None, []
    for line in text.split("\n"):
        m = re.match(r"^#{2,3} (.+)$", line)
        if m:
            if heading and rows:
                out.append((heading, rows))
            heading, rows = m.group(1), []
        elif line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("#", "例外"):
                rows.append(cells)
    if heading and rows:
        out.append((heading, rows))
    return dict(out)


def parse_index():
    """規則索引：[{no, name, span, group_citation}]"""
    tables = _tables(RULES_MD.read_text(encoding="utf-8"))
    return [
        {"no": int(r[0]), "name": r[1], "span": r[2], "group_citation": r[3]}
        for r in tables["規則索引"]
        if r[0].isdigit()
    ]


def parse_exception_index():
    """例外索引：[{desc, rule_no, citation}]"""
    tables = _tables(RULES_MD.read_text(encoding="utf-8"))
    return [
        {"desc": r[0], "rule_no": int(r[1]), "citation": r[2]}
        for r in tables["例外索引"]
        if len(r) == 3 and r[1].isdigit()
    ]


def parse_inline_citations():
    """rules.md 每個 `## N.` 章節底下那行「引用參考 …」。"""
    out, current = {}, None
    for line in RULES_MD.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^#{2,3} (\d+)\. (.+)$", line)
        if m:
            current = int(m.group(1))
        elif current and line.startswith("引用參考 "):
            out[current] = line[len("引用參考 "):].strip()
            current = None
    return out


def split_citation(text):
    """把「規則名稱 L22-L38」拆成 (名稱, 起, 迄)。格式不合回傳 None。"""
    m = CITATION_RE.match(text)
    if not m:
        return None
    span = m.group("span")
    parts = span.split("-")
    start = int(parts[0][1:])
    end = int(parts[1][1:]) if len(parts) > 1 else start
    return m.group("name"), start, end
