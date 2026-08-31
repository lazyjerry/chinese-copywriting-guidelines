#!/usr/bin/env python3
"""從 gaps.py 產生 KNOWN-GAPS.md。

缺陷清單只有一份來源（gaps.py），文件由它生成，才不會清單改了文件沒改。

    python3 skill-tests/script/regenerate_known_gaps.py
"""

from pathlib import Path

import gaps

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "KNOWN-GAPS.md"

HEAD = """# 已知缺陷

`skills/chinese-copywriting/scripts/check_copywriting.py` 目前做不到的事。
每一條都對應 `script/test_gaps.py` 的一個失敗測試——**這些測試現在應該是紅的**。

修好一條之後：把該筆從 `script/gaps.py` 刪掉，重跑 `regenerate_cases.py`
與 `regenerate_known_gaps.py`，對應的紅燈就會轉綠、這份文件也會跟著更新。

分類：

- **誤報**：不該報卻報了。比漏報嚴重，會讓使用者把對的文章改壞，優先處理
- **漏報**：該報而沒報
- **修正缺陷**：`--fix` 自己製造出新的違規，或動到不該動的東西
"""

ADJUDICATION_HEAD = """
## 需裁決：規則層分不出來的

**這些是預期會出錯的例子。** 帶了 `--units` 之後腳本一定會把 `5G` 報成違規，那就是誤報。

它不列進上面的誤報，因為那一類的定義是「不該報卻報了，修好就會轉綠」，而這條**修不好**——
`5G` 與 `3bar` 在 `UNIT_RE` 眼裡形狀相同（數字緊接英文、兩側不接字母），
那個形狀本身不帶區分資訊。誤報要在裁決步驟消除，不是在腳本層。

腳本層能保證的只有**誤報不會造成傷害**：一律標 `low`、一律不可修、`--fix` 之後逐字不變。
這三條是綠燈，鎖在 `script/test_units.py`。模型有沒有真的 drop 掉，
只有 `evals/cases/custom-unit-overlap` 測得到。

不帶 `--units` 時這些一筆都不會報——誤報只在使用者主動擴充單位表時才存在。
"""

ROOT_CAUSE = """
## 根因：手寫常數的覆蓋率

多數漏報都指向同一個地方——腳本開頭那幾個手打的字串。漏掉什麼全看當初想到什麼。

```python
CJK = r"一-鿿㐀-䶿぀-ヿ가-힯"
UNITS = ["Gbps", "Mbps", ..., "dpi", "fps"]           # 23 個
FULLWIDTH_PUNCT = "，。！？；：、（）「」『』【】《》〈〉…"
FW_CLOSING = "，。！？；：、）」』】》〉…"
FW_OPENING = "（「『【《〈"
```

### 標點與漢字：改用 Unicode 屬性推導

已實測，這三類都不必手打：

| 現行常數 | 可改成 | 效果 |
| --- | --- | --- |
| `FULLWIDTH_PUNCT` | `category` 開頭是 `P` 且 `east_asian_width` 屬於 `F`、`W`、`A` | 現行 20 個全數涵蓋，另外補上 `〔〕｛｝＂＇％＃＠＆／＼` |
| `FW_OPENING`、`FW_CLOSING` | 直接用 `Ps`（開）與 `Pe`（閉） | Unicode 本來就標好了，手寫清單漏掉 `〔｛〕｝` |
| `HALFWIDTH_PUNCT_RE` 的 `,!?;:` | `category` 開頭是 `P` 且 `east_asian_width` 屬於 `Na`、`H` | 一次補齊 `.`、`'`、`[`、`]`、`{`、`}` |
| `CJK` 字元範圍 | `category` 等於 `Lo` 且 `east_asian_width` 屬於 `W`、`F` | 涵蓋擴充 A、**擴充 B 以上**、相容表意、假名、諺文 |

刻意排除的項目改成一份**小的例外集合**：破折號 `—` 與 `～` 照舊不列入規則 4。
維護負擔從「想得到才收得到」翻轉成「明講不要什麼」。

效能不是問題：模組載入時掃一遍碼點、組成正則字元類快取起來即可，之後與現在一樣快。

**改動時務必同時跑綠燈**。`test_cases.py` 的 `TestDeliberateBehaviour` 鎖住了
破折號、波浪號、表格分隔線這些刻意不報的情況，放寬字元集合最容易把它們一起掃進來。

### 單位：沒有等價屬性，但可以生成

單位無法從 Unicode 推導，只能靠清單，但可以由 SI 詞頭與單位表交叉生成：
詞頭 `n μ m c d k M G T P` 與二進位詞頭 `Ki Mi Gi Ti`，乘上
`m g s A K Hz N Pa J W V F Ω L t B bit bps Wh Ah`，再加 IT 常用的
`px pt dpi ppi fps rpm dB`。

兩條護欄，兩條都已經寫成綠燈測試鎖住：

- **不收單字母單位**，會把 `the 90s`、`3m` 這類英文大量誤判
- **排除與英文單字撞名的組合**，例如 `in`、`at`、`as`、`ha`

`pint` 這類函式庫有完整的單位登錄表，但引入依賴違反這支腳本零依賴的前提。
參考它的單位表，不要引入它。

`--units` **不是這些漏報的修法**，是給使用者的臨時出口。帶進來的單位沒有經過上面兩條
護欄篩選，所以一律標 `low`、不自動修——`5G`、`4K`、`3in1`、`2T` 跟 `3bar`、`65W`、`24h`
在正則眼裡形狀相同，只有上下文分得出來，那是裁決步驟的事。底下這些漏報要真的轉綠，
還是得把單位收進 `UNITS` 並確認它們過得了兩條護欄。

### `--fix` 的共同修法

兩條修正缺陷的成因相同：`FIXERS` 是單向一次 pass，後面的修正會製造出前面才處理的違規。
修法是**把 `FIXERS` 迭代到不動點**（設迭代上限防呆），而不是重排順序——重排只會換一個方向漏。
"""

KIND_LABEL = {"missed": "漏報", "false_positive": "誤報"}


def main():
    lines = [HEAD, "\n## 偵測缺陷\n"]
    lines.append("| # | 樣本 | 行 | 規則 | 片段 | 種類 | 成因 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    n = 0
    ordered = sorted(
        ((path, e) for path, entries in gaps.GAPS.items() for e in entries),
        key=lambda x: (x[1][3] != "false_positive", x[0], x[1][0]),
    )
    for path, entry in ordered:
        ln, rule, frag, kind, why = entry[:5]
        n += 1
        sample = path.split("/")[-1]
        lines.append(
            f"| {n} | `{sample}` | {ln} | {rule} | `{frag}` | "
            f"**{KIND_LABEL[kind]}** | {why} |"
        )

    lines.append("\n## 修正缺陷\n")
    lines.append("| # | 樣本 | 行 | 規則 | 成因 |")
    lines.append("| --- | --- | --- | --- | --- |")
    for path, ln, rule, _frag, why in gaps.FIX_GAPS:
        n += 1
        lines.append(f"| {n} | `{path.split('/')[-1]}` | {ln} | {rule} | {why} |")
    for title, why in gaps.BEHAVIOUR_GAPS:
        n += 1
        lines.append(f"| {n} | 不綁樣本 | — | — | {title}。{why} |")

    lines.append(f"\n合計 **{n}** 條。")

    lines.append(ADJUDICATION_HEAD)
    lines.append("| 樣本 | 行 | 片段 | 帶入的單位 | 裁決 | 實際是什麼 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for path, entries in gaps.ADJUDICATION.items():
        sample = path.split("/")[-1]
        for ln, rule, frag, unit, verdict, why in entries:
            label = "drop" if verdict == "code" else "keep 並補空格"
            lines.append(
                f"| `{sample}` | {ln} | `{frag}` | `{unit}` | **{label}** | {why} |"
            )

    lines.append(ROOT_CAUSE)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"寫入 KNOWN-GAPS.md：{n} 條缺陷")


if __name__ == "__main__":
    main()
