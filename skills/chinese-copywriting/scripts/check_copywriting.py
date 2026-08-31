#!/usr/bin/env python3
"""依《中文文案排版指北》檢查中文文案排版，可選擇就地修正。

用法：
    check_copywriting.py [--fix] [--json] [--dispute] [--units U1,U2] <file>...

不帶 --fix 時只報告；有違規時 exit code 為 1。
"""

import argparse
import json
import re
import sys

CJK = r"一-鿿㐀-䶿぀-ヿ가-힯"

# 官方定義即為無空格寫法的產品名詞，整體豁免規則 1、2
EXCEPTION_TERMS = [
    "豆瓣FM",
]

# 規則 3 的單位。只收大小寫敏感、不易與一般英文單字混淆的常見單位。
# 這份表刻意窄——單位縮寫與英文單字、產品代號大量重疊（`bar`、`in`、`5G` 的 G），
# 收得寬就會誤報。要擴充走 --units，那些單位一律標 low 交模型裁決。
UNITS = [
    "Gbps", "Mbps", "Kbps", "bps",
    "TB", "GB", "MB", "KB", "PB",
    "GHz", "MHz", "KHz", "Hz",
    "km", "cm", "mm", "kg", "mg", "ml",
    "px", "pt", "dpi", "fps",
]

# 破折號與間隔號刻意不列入：兩側留白是常見的排版風格，指北也沒有給對應範例，
# 自動修正它們風險大於效益。
FULLWIDTH_PUNCT = "，。！？；：、（）「」『』【】《》〈〉…"
# 只有右側標點允許前面沒有內容（行首續行），左括號類另外處理
FW_CLOSING = "，。！？；：、）」』】》〉…"
FW_OPENING = "（「『【《〈"

RULE_TITLES = {
    "R1": "中英文之間需要增加空格",
    "R2": "中文與數字之間需要增加空格",
    "R3": "數字與單位之間需要增加空格",
    "R4": "全形標點與其他字符之間不加空格",
    "R5": "不重複使用標點符號",
    "R6": "使用全形中文標點",
    "R7": "數字使用半形字符",
    "R8": "英文整句、特殊名詞內使用半形標點",
    "R11": "超連結之間增加空格",
    "R12": "簡體中文使用直角引號",
}

# --fix 能安全處理的規則；其餘只報告
FIXABLE = {"R1", "R2", "R3", "R4", "R5", "R7"}

# 規則命中但需要上下文才能定奪的項目標成 low，一律不自動修，交給模型逐筆裁決。
# 純字元層、無歧義的標 high。
HIGH = "high"
LOW = "low"


class Issue:
    def __init__(self, path, line, col, rule, message, snippet,
                 confidence=HIGH, in_example=False):
        self.path = path
        self.line = line
        self.col = col
        self.rule = rule
        self.message = message
        self.snippet = snippet
        self.confidence = confidence
        self.in_example = in_example

    @property
    def fixable(self):
        return (
            self.rule in FIXABLE
            and self.confidence == HIGH
            and not self.in_example
        )

    def as_dict(self):
        return {
            "path": self.path,
            "line": self.line,
            "column": self.col,
            "rule": self.rule,
            "title": RULE_TITLES[self.rule],
            "message": self.message,
            "snippet": self.snippet,
            "confidence": self.confidence,
            "in_example": self.in_example,
            "fixable": self.fixable,
        }


# ---------------------------------------------------------------------------
# 遮罩：把不該碰的區段換成等長的 \x00，位置與長度都保持不變，
# 讓後續正則能沿用同一組偏移量回寫原文。
# ---------------------------------------------------------------------------

MASK = "\x00"

INLINE_CODE_RE = re.compile(r"(`+)(?:.*?)\1")
# 連結目標允許一層成對括號，例如 MSDN 的 …/ms531164(v=vs.85).aspx
LINK_DEST = r"(?:[^()]|\([^()]*\))*"
LINK_TARGET_RE = re.compile(rf"\]\({LINK_DEST}\)")
AUTOLINK_RE = re.compile(r"<[^>\s]+>")
BARE_URL_RE = re.compile(r"(?:https?://|ftp://|www\.)[^\s，。！？「」（）]+")
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]")


def mask_spans(text, pattern):
    def repl(m):
        return MASK * (m.end() - m.start())

    return pattern.sub(repl, text)


def mask_line(line):
    """把 inline code、連結目標、URL、HTML 標籤遮成 \\x00。"""
    masked = line
    for pattern in (
        INLINE_CODE_RE,
        LINK_TARGET_RE,
        AUTOLINK_RE,
        BARE_URL_RE,
        HTML_TAG_RE,
    ):
        masked = mask_spans(masked, pattern)
    for term in EXCEPTION_TERMS:
        masked = masked.replace(term, MASK * len(term))
    return masked


# 規則書的反例：一行以冒號收尾且點明是錯誤示範，其後連續的 blockquote 就是
# 刻意寫錯的教材。這些行照常偵測、照常回報，只是標記起來不自動修。
EXAMPLE_LEAD_RE = re.compile(r"[:：]\s*$")


def _is_counterexample_lead(stripped):
    if not EXAMPLE_LEAD_RE.search(stripped):
        return False
    return "錯" in stripped or "對比用法" in stripped


def scannable_lines(lines):
    """產生 (index, masked_line, in_example)，跳過 fenced code block 與 YAML frontmatter。"""
    in_fence = False
    fence_marker = ""
    in_frontmatter = False
    in_counterexample = False

    for i, raw in enumerate(lines):
        stripped = raw.strip()

        if i == 0 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped in ("---", "..."):
                in_frontmatter = False
            continue

        fence = re.match(r"^\s*(`{3,}|~{3,})", raw)
        if fence:
            marker = fence.group(1)[0] * 3
            if not in_fence:
                in_fence = True
                fence_marker = marker
                continue
            if marker == fence_marker:
                in_fence = False
            continue
        if in_fence:
            continue

        # 縮排四格以上的程式碼區塊
        if re.match(r"^(\t| {4,})\S", raw) and raw.strip():
            continue

        is_quote = stripped.startswith(">")
        if _is_counterexample_lead(stripped):
            in_counterexample = True
        elif stripped and not is_quote:
            in_counterexample = False

        yield i, mask_line(raw), in_counterexample and is_quote


# ---------------------------------------------------------------------------
# 各規則：偵測回傳 (col, rule, message, snippet, confidence)；修正回傳新字串。
# 修正一律作用在原始行上，但比對位置取自遮罩行，因此遮罩區段不會被改到。
# ---------------------------------------------------------------------------


def snippet_of(line, start, end, pad=12):
    left = max(0, start - pad)
    right = min(len(line), end + pad)
    prefix = "…" if left > 0 else ""
    suffix = "…" if right < len(line) else ""
    return prefix + line[left:right].strip() + suffix


def find_missing_space(masked, line):
    """規則 1、2：CJK 與半形英數字之間缺空格（雙向）。"""
    issues = []
    patterns = [
        re.compile(rf"([{CJK}])([A-Za-z0-9])"),
        re.compile(rf"([A-Za-z0-9])([{CJK}])"),
    ]
    for pattern in patterns:
        for m in pattern.finditer(masked):
            if MASK in m.group(0):
                continue
            rule = "R2" if m.group(0).strip()[-1].isdigit() or m.group(0)[0].isdigit() else "R1"
            issues.append(
                (
                    m.start() + 1,
                    rule,
                    f"「{m.group(0)}」之間需要增加空格",
                    snippet_of(line, m.start(), m.end()),
                    HIGH,
                )
            )
    return issues


def fix_missing_space(masked, line):
    out = []
    for i, ch in enumerate(line):
        if i > 0 and MASK not in (masked[i - 1], masked[i]):
            prev = line[i - 1]
            if _is_cjk(prev) and _is_latin(ch):
                out.append(" ")
            elif _is_latin(prev) and _is_cjk(ch):
                out.append(" ")
        out.append(ch)
    return "".join(out)


def _is_cjk(ch):
    return re.match(rf"[{CJK}]", ch) is not None


def _is_latin(ch):
    return re.match(r"[A-Za-z0-9]", ch) is not None


def _code_span_boundaries(line):
    """回傳行內程式碼兩側緊貼中文字的位置。

    inline code 的內容在遮罩行已被抹掉，邊界要在原始行上找。
    """
    positions = []
    for m in INLINE_CODE_RE.finditer(line):
        if m.start() > 0 and _is_cjk(line[m.start() - 1]):
            positions.append(m.start())
        if m.end() < len(line) and _is_cjk(line[m.end()]):
            positions.append(m.end())
    return positions


def find_code_span_space(masked, line):
    return [
        (
            pos + 1,
            "R1",
            "行內程式碼與中文之間需要增加空格",
            snippet_of(line, max(0, pos - 1), min(len(line), pos + 1)),
            HIGH,
        )
        for pos in _code_span_boundaries(line)
    ]


def fix_code_span_space(masked, line):
    result = line
    for pos in sorted(_code_span_boundaries(line), reverse=True):
        result = result[:pos] + " " + result[pos:]
    return result


def build_unit_re(extra=()):
    """把內建與自訂單位組成一條正則。長的排前面，避免短的先匹配掉。"""
    units = list(UNITS) + [u for u in extra if u not in UNITS]
    alternation = "|".join(re.escape(u) for u in sorted(units, key=len, reverse=True))
    return re.compile(rf"(?<![A-Za-z])(\d)({alternation})(?![A-Za-z])")


UNIT_RE = build_unit_re()

# 使用者帶進來的單位。內建表是篩過的，自訂的沒有，所以命中一律標 low：
# `5G`、`3in1`、`4K` 這種數字加英文的寫法跟單位長得一模一樣，只有上下文分得出來。
CUSTOM_UNITS = set()


def configure_units(extra=()):
    """設定自訂單位。每次檢查都會呼叫，不帶參數就是重置回內建表。"""
    global UNIT_RE, CUSTOM_UNITS
    CUSTOM_UNITS = {u.strip() for u in extra if u and u.strip()} - set(UNITS)
    UNIT_RE = build_unit_re(CUSTOM_UNITS)


def parse_units(raw):
    """把 --units 的逗號字串拆成單位清單。"""
    if not raw:
        return []
    return [u.strip() for u in raw.split(",") if u.strip()]
# 度數與百分比反過來：數字與 ° %  之間不該有空格。
# 溫標 °C／°F／°K 例外——依國際單位制，數字與溫標之間要留白，`25 °C` 是正確寫法。
DEGREE_SPACE_RE = re.compile(r"(\d)\s+(°(?![CFK])|%)")


def find_unit_space(masked, line):
    issues = []
    for m in UNIT_RE.finditer(masked):
        if MASK in m.group(0):
            continue
        issues.append(
            (
                m.start() + 1,
                "R3",
                f"數字與單位「{m.group(2)}」之間需要增加空格",
                snippet_of(line, m.start(), m.end()),
                LOW if m.group(2) in CUSTOM_UNITS else HIGH,
            )
        )
    for m in DEGREE_SPACE_RE.finditer(masked):
        if MASK in m.group(0):
            continue
        issues.append(
            (
                m.start() + 1,
                "R3",
                f"數字與「{m.group(2)}」之間不需要增加空格",
                snippet_of(line, m.start(), m.end()),
                HIGH,
            )
        )
    return issues


def fix_unit_space(masked, line):
    result = line
    for m in reversed(list(UNIT_RE.finditer(masked))):
        if MASK in m.group(0) or m.group(2) in CUSTOM_UNITS:
            continue
        pos = m.start() + 1
        result = result[:pos] + " " + result[pos:]
    masked2 = mask_line(result)
    for m in reversed(list(DEGREE_SPACE_RE.finditer(masked2))):
        if MASK in m.group(0):
            continue
        result = result[: m.start() + 1] + m.group(2) + result[m.end():]
    return result


# `|` 兩側的空白是 Markdown 表格的語法，不是文案裡的空格，必須排除，
# 否則 --fix 會把表格重排。
FW_SPACE_AFTER_RE = re.compile(rf"([{FULLWIDTH_PUNCT}])[ \t]+(?=[^|\s])")
FW_SPACE_BEFORE_RE = re.compile(rf"(?<=[^|\s])[ \t]+(?=[{FW_CLOSING}])")
FW_SPACE_AFTER_OPENING_RE = re.compile(rf"(?<=[{FW_OPENING}])[ \t]+(?=[^|\s])")


def find_fullwidth_space(masked, line):
    issues = []
    for pattern, msg in (
        (FW_SPACE_BEFORE_RE, "全形標點前不應有空格"),
        (FW_SPACE_AFTER_RE, "全形標點後不應有空格"),
    ):
        for m in pattern.finditer(masked):
            if MASK in m.group(0):
                continue
            issues.append(
                (m.start() + 1, "R4", msg, snippet_of(line, m.start(), m.end()), HIGH)
            )
    return issues


def fix_fullwidth_space(masked, line):
    result = FW_SPACE_BEFORE_RE.sub("", line)
    result = FW_SPACE_AFTER_RE.sub(r"\1", result)
    result = FW_SPACE_AFTER_OPENING_RE.sub("", result)
    return result


# 允許單一「？！」；其餘連續的驚嘆號、問號都算重複
DUP_PUNCT_RE = re.compile(r"[！？]{2,}")


def find_duplicate_punct(masked, line):
    issues = []
    for m in DUP_PUNCT_RE.finditer(masked):
        if MASK in m.group(0) or m.group(0) == "？！":
            continue
        issues.append(
            (
                m.start() + 1,
                "R5",
                f"重複使用標點符號「{m.group(0)}」",
                snippet_of(line, m.start(), m.end()),
                HIGH,
            )
        )
    return issues


def _collapse(run):
    """！！！→！；？？！！／？！？！→？！；？？？→？"""
    if "？" in run and "！" in run:
        return "？！"
    return run[0]


def fix_duplicate_punct(masked, line):
    result = line
    for m in reversed(list(DUP_PUNCT_RE.finditer(masked))):
        if MASK in m.group(0) or m.group(0) == "？！":
            continue
        result = result[: m.start()] + _collapse(m.group(0)) + result[m.end():]
    return result


HALFWIDTH_PUNCT_RE = re.compile(rf"(?:[{CJK}][,!?;:]|[,!?;:][{CJK}])")
CJK_QUOTE_RE = re.compile(rf'(?:[{CJK}]\s*"|"\s*[{CJK}])')
CJK_PAREN_RE = re.compile(rf"(?:[{CJK}]\s*\(|\)\s*[{CJK}])")


def find_halfwidth_punct(masked, line):
    """半形逗號、驚嘆號這類無歧義；引號與括號要看上下文才知道是不是誤用。

    `呼叫 setState() 之後` 的括號屬於程式碼寫法而非中文標點，正則分不出來，
    所以這兩條標 low 交給模型裁決。
    """
    issues = []
    for pattern, confidence in (
        (HALFWIDTH_PUNCT_RE, HIGH),
        (CJK_QUOTE_RE, LOW),
        (CJK_PAREN_RE, LOW),
    ):
        for m in pattern.finditer(masked):
            if MASK in m.group(0):
                continue
            issues.append(
                (
                    m.start() + 1,
                    "R6",
                    "中文語境內應使用全形標點",
                    snippet_of(line, m.start(), m.end()),
                    confidence,
                )
            )
    return issues


FULLWIDTH_DIGIT_RE = re.compile(r"[０-９]")


def find_fullwidth_digit(masked, line):
    issues = []
    for m in FULLWIDTH_DIGIT_RE.finditer(masked):
        if MASK in m.group(0):
            continue
        issues.append(
            (
                m.start() + 1,
                "R7",
                f"數字應使用半形「{m.group(0)}」",
                snippet_of(line, m.start(), m.end()),
                HIGH,
            )
        )
    return issues


def fix_fullwidth_digit(masked, line):
    result = line
    for m in reversed(list(FULLWIDTH_DIGIT_RE.finditer(masked))):
        if MASK in m.group(0):
            continue
        half = chr(ord(m.group(0)) - 0xFEE0)
        result = result[: m.start()] + half + result[m.end():]
    return result


# 只看引號／書名號包起來的整段。整段沒有中文字才算「完整的英文整句」，
# 否則 `Gbps，SSD` 這種中文句子裡的斷句會被誤判。
QUOTED_SPAN_RE = re.compile(r"「[^「」]*」|『[^『』]*』|《[^《》]*》|\"[^\"]*\"")
CJK_RE = re.compile(rf"[{CJK}]")
FULLWIDTH_IN_EN_RE = re.compile(r"[，。；：、＆／]")


def find_en_fullwidth_punct(masked, line):
    issues = []
    for span in QUOTED_SPAN_RE.finditer(masked):
        text = span.group(0)
        if MASK in text or CJK_RE.search(text):
            continue
        if not re.search(r"[A-Za-z]", text):
            continue
        if text[0] == "《":
            issues.append(
                (
                    span.start() + 1,
                    "R8",
                    "英文書籍名、報刊名應以英文斜體表示，不借用中文書名號",
                    snippet_of(line, span.start(), span.end()),
                    LOW,
                )
            )
            continue
        for m in FULLWIDTH_IN_EN_RE.finditer(text):
            pos = span.start() + m.start()
            issues.append(
                (
                    pos + 1,
                    "R8",
                    f"英文整句內應使用半形標點，不用「{m.group(0)}」",
                    snippet_of(line, pos, pos + 1),
                    LOW,
                )
            )
    return issues


# 只認 Markdown 連結本身，別把一般的半形括號也算進去。
# 連結目標在遮罩行已被抹掉，因此這條規則直接掃原始行。
LINK_NO_SPACE_RE = re.compile(
    rf"[{CJK}]\[[^\]]+\]\(|\]\({LINK_DEST}\)[{CJK}]"
)
CURLY_QUOTE_RE = re.compile(r"[“”‘’]")


def find_link_space(masked, line):
    issues = []
    for m in LINK_NO_SPACE_RE.finditer(line):
        issues.append(
            (
                m.start() + 1,
                "R11",
                "超連結與中文之間可增加空格（爭議規則）",
                snippet_of(line, m.start(), m.end()),
                HIGH,
            )
        )
    return issues


def find_curly_quote(masked, line):
    issues = []
    for m in CURLY_QUOTE_RE.finditer(masked):
        if MASK in m.group(0):
            continue
        issues.append(
            (
                m.start() + 1,
                "R12",
                "建議改用直角引號「」『』（爭議規則）",
                snippet_of(line, m.start(), m.end()),
                HIGH,
            )
        )
    return issues


DETECTORS = [
    find_missing_space,
    find_code_span_space,
    find_unit_space,
    find_fullwidth_space,
    find_duplicate_punct,
    find_halfwidth_punct,
    find_fullwidth_digit,
    find_en_fullwidth_punct,
]

DISPUTE_DETECTORS = [find_link_space, find_curly_quote]

# 修正順序有意義：先補空格再收全形標點旁的空白，避免補完又留下多餘空格
FIXERS = [
    fix_missing_space,
    fix_code_span_space,
    fix_unit_space,
    fix_duplicate_punct,
    fix_fullwidth_digit,
    fix_fullwidth_space,
]


def check_file(path, dispute=False, extra_units=()):
    configure_units(extra_units)
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    detectors = DETECTORS + (DISPUTE_DETECTORS if dispute else [])
    issues = []
    for i, masked, in_example in scannable_lines(lines):
        for detector in detectors:
            for col, rule, message, snippet, confidence in detector(masked, lines[i]):
                issues.append(
                    Issue(path, i + 1, col, rule, message, snippet,
                          confidence, in_example)
                )
    issues.sort(key=lambda x: (x.line, x.col, x.rule))
    return issues


def fix_file(path, extra_units=()):
    configure_units(extra_units)
    with open(path, encoding="utf-8") as f:
        original = f.read()
    lines = original.splitlines()
    newline = "\r\n" if "\r\n" in original else "\n"

    changed = 0
    for i, _, in_example in scannable_lines(lines):
        if in_example:
            continue
        line = lines[i]
        for fixer in FIXERS:
            line = fixer(mask_line(line), line)
        if line != lines[i]:
            lines[i] = line
            changed += 1

    if changed:
        trailing = newline if original.endswith(("\n", "\r\n")) else ""
        with open(path, "w", encoding="utf-8") as f:
            f.write(newline.join(lines) + trailing)
    return changed


def main():
    parser = argparse.ArgumentParser(
        description="依《中文文案排版指北》檢查中文文案排版"
    )
    parser.add_argument("files", nargs="+", metavar="file")
    parser.add_argument("--fix", action="store_true", help="就地修正可安全處理的項目")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    parser.add_argument(
        "--dispute", action="store_true", help="一併檢查爭議規則（R11、R12）"
    )
    parser.add_argument(
        "--units",
        metavar="UNIT[,UNIT...]",
        help="擴充規則 3 的單位表，逗號分隔。這些單位命中一律標 low、不自動修",
    )
    args = parser.parse_args()
    extra_units = parse_units(args.units)

    if args.fix:
        total = 0
        for path in args.files:
            changed = fix_file(path, extra_units=extra_units)
            total += changed
            if not args.json:
                print(f"{path}: 修正 {changed} 行")
        if args.json:
            print(json.dumps({"fixed_lines": total}, ensure_ascii=False))
        return 0

    all_issues = []
    for path in args.files:
        all_issues.extend(
            check_file(path, dispute=args.dispute, extra_units=extra_units)
        )

    if args.json:
        print(
            json.dumps(
                [issue.as_dict() for issue in all_issues], ensure_ascii=False, indent=2
            )
        )
    else:
        for issue in all_issues:
            mark = "" if issue.fixable else "（需人工判斷）"
            print(
                f"{issue.path}:{issue.line}:{issue.col}: "
                f"[{issue.rule}] {issue.message}{mark}"
            )
            print(f"    {issue.snippet}")
        print(f"\n共 {len(all_issues)} 項" if all_issues else "通過，無排版違規")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
