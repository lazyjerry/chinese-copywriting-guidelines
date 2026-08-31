"""已知缺陷清單：腳本現在做不到、下一輪要修的事。

每筆對應 KNOWN-GAPS.md 的一個段落，也對應 test_gaps.py 的一個紅燈測試。
GAPS 是偵測面的缺陷，kind：
    missed          該報而沒報
    false_positive  不該報卻報了（比漏報嚴重，會讓使用者改壞好文章）

FIX_GAPS 是 --fix 面的缺陷：修正過程自己製造出新的違規，一次 pass 收不乾淨。
修好一條之後，把該筆從這裡刪掉並重跑 regenerate_cases.py。
"""

GAPS = {
    "cases/case-02-latin-space.md": [
        # 同一行另有一筆已被偵測的 R1（「e地」），所以必須指定欄位才分得開
        (25, "R1", "𠮟responsible", "missed",
         "CJK 字元類只涵蓋四段 BMP 範圍，擴充 B 以上（U+20000+）的漢字貼著英文抓不到",
         9),
    ],
    "cases/case-03-units.md": [
        (29, "R3", "25 °", "false_positive",
         "攝氏度依國際單位制應保留空格，DEGREE_SPACE_RE 沒分辨角度與溫度，把正確寫法判成違規"),
        (21, "R3", "44.1kHz", "missed", "UNITS 收了 KHz 卻沒收正確 SI 寫法的 kHz"),
        (21, "R3", "120dB", "missed", "UNITS 缺聲壓單位 dB"),
        (23, "R3", "5000mAh", "missed", "UNITS 缺電池容量單位 mAh"),
        (23, "R3", "65W", "missed", "UNITS 缺功率單位 W 系列"),
        (25, "R3", "7nm", "missed", "UNITS 缺長度單位 nm"),
        (25, "R3", "16GiB", "missed", "UNITS 缺二進位詞頭 GiB／MiB／TiB"),
        (31, "R3", "100ms", "missed", "UNITS 缺時間單位 ms"),
        (31, "R3", "180ms", "missed", "UNITS 缺時間單位 ms"),
    ],
    "cases/case-04-punct-space.md": [
        (30, "R4", "〔", "missed", "FULLWIDTH_PUNCT 手寫清單沒收全形方括號，Unicode 標為 Ps／Pe"),
        (30, "R4", "｝", "missed", "FULLWIDTH_PUNCT 手寫清單沒收全形大括號"),
        (32, "R4", "＂", "missed", "FULLWIDTH_PUNCT 手寫清單沒收全形雙引號"),
        (32, "R4", "％", "missed", "FULLWIDTH_PUNCT 手寫清單沒收全形百分號"),
        (34, "R4", "／", "missed", "FULLWIDTH_PUNCT 手寫清單沒收全形斜線"),
    ],
    "cases/case-05-duplicate.md": [
        (23, "R5", "。。。", "missed", "DUP_PUNCT_RE 只認 `[！？]{2,}`，重複句號抓不到"),
        (25, "R5", "，，", "missed", "DUP_PUNCT_RE 只認 `[！？]{2,}`，重複逗號抓不到"),
        (27, "R5", "！ ！", "missed", "重複標點中間夾空白時 DUP_PUNCT_RE 不連續，只被 R4 抓到空格"),
    ],
    "cases/case-06-halfwidth.md": [
        (21, "R6", "收好.這個", "missed", "HALFWIDTH_PUNCT_RE 的集合只有 `,!?;:`，缺半形句號"),
        (23, "R6", "'標準流程'", "missed", "CJK_QUOTE_RE 只認半形雙引號，缺單引號"),
        (25, "R6", "[影像]", "missed", "半形方括號不在任何半形標點集合裡"),
        (27, "R6", "{進階}", "missed", "半形大括號不在任何半形標點集合裡"),
    ],
    "cases/case-07-english.md": [
        (23, "R8", "He said，it works", "missed",
         "QUOTED_SPAN_RE 只掃引號與書名號包起來的整段，沒有引號的英文整句不檢查"),
        (25, "R8", "Stay hungry！", "missed", "FULLWIDTH_IN_EN_RE 缺全形驚嘆號"),
        (27, "R8", "Are you serious？", "missed", "FULLWIDTH_IN_EN_RE 缺全形問號"),
    ],
}


def gaps_for(rel_path):
    """第 6 個元素是可選的欄位號，用在同一行同一規則已有其他違規、光靠片段分不開時。"""
    out = []
    for entry in GAPS.get(rel_path, []):
        ln, rule, frag, kind, why = entry[:5]
        item = {"line": ln, "rule": rule, "contains": frag, "kind": kind, "why": why}
        if len(entry) > 5:
            item["col"] = entry[5]
        out.append(item)
    return out


def is_known_false_positive(rel_path, issue):
    for entry in GAPS.get(rel_path, []):
        ln, rule, frag, kind = entry[0], entry[1], entry[2], entry[3]
        col = entry[5] if len(entry) > 5 else None
        if kind != "false_positive":
            continue
        if issue.line == ln and issue.rule == rule and frag in issue.snippet:
            if col is None or issue.col == col:
                return True
    return False


# --fix 的缺陷：FIXERS 是單向一次 pass，後面的修正會製造出前面才處理的違規。
# 共同的修法是把 FIXERS 迭代到不動點（設迭代上限），而不是排序。
FIX_GAPS = [
    ("cases/case-04-punct-space.md", 32, "R2", "誤差大約15％",
     "fix_fullwidth_digit 把 `１５` 轉成 `15` 之後製造出中文與數字之間缺空格，"
     "但 fix_missing_space 在 FIXERS 裡排在它前面，同一次 pass 收不到"),
    ("cases/case-05-duplicate.md", 27, "R5", "謝謝你們！！",
     "fix_fullwidth_space 拿掉 `！ ！` 中間的空白之後製造出重複標點，"
     "但 fix_duplicate_punct 在 FIXERS 裡排在它前面，同一次 pass 收不到"),
]


def fix_gaps_for(rel_path):
    return [
        {"line": ln, "rule": rule, "contains": frag, "why": why}
        for path, ln, rule, frag, why in FIX_GAPS
        if path == rel_path
    ]


# 不綁在特定樣本上的行為型缺陷，各自對應 test_gaps.py 裡一個具名測試。
BEHAVIOUR_GAPS = [
    ("fix_file 讀檔沒有關掉萬用換行，CRLF 檔案被靜靜改成 LF",
     "fix_file 裡那行 newline 判斷看得出本意是保留 CRLF，"
     "但 `open()` 預設的萬用換行已經先把 CRLF 轉成 LF，條件永遠成立不了。"
     "修法是 `open(path, encoding=\"utf-8\", newline=\"\")`"),
]


def gap_count():
    detection = sum(len(v) for v in GAPS.values())
    return detection + len(FIX_GAPS) + len(BEHAVIOUR_GAPS)
