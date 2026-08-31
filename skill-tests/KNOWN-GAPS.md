# 已知缺陷

`skills/chinese-copywriting/scripts/check_copywriting.py` 目前做不到的事。
每一條都對應 `script/test_gaps.py` 的一個失敗測試——**這些測試現在應該是紅的**。

修好一條之後：把該筆從 `script/gaps.py` 刪掉，重跑 `regenerate_cases.py`
與 `regenerate_known_gaps.py`，對應的紅燈就會轉綠、這份文件也會跟著更新。

分類：

- **誤報**：不該報卻報了。比漏報嚴重，會讓使用者把對的文章改壞，優先處理
- **漏報**：該報而沒報
- **修正缺陷**：`--fix` 自己製造出新的違規，或動到不該動的東西


## 偵測缺陷

| # | 樣本 | 行 | 規則 | 片段 | 種類 | 成因 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `case-02-latin-space.md` | 25 | R1 | `𠮟responsible` | **漏報** | CJK 字元類只涵蓋四段 BMP 範圍，擴充 B 以上（U+20000+）的漢字貼著英文抓不到 |
| 2 | `case-03-units.md` | 21 | R3 | `44.1kHz` | **漏報** | UNITS 收了 KHz 卻沒收正確 SI 寫法的 kHz |
| 3 | `case-03-units.md` | 21 | R3 | `120dB` | **漏報** | UNITS 缺聲壓單位 dB |
| 4 | `case-03-units.md` | 23 | R3 | `5000mAh` | **漏報** | UNITS 缺電池容量單位 mAh |
| 5 | `case-03-units.md` | 23 | R3 | `65W` | **漏報** | UNITS 缺功率單位 W 系列 |
| 6 | `case-03-units.md` | 25 | R3 | `7nm` | **漏報** | UNITS 缺長度單位 nm |
| 7 | `case-03-units.md` | 25 | R3 | `16GiB` | **漏報** | UNITS 缺二進位詞頭 GiB／MiB／TiB |
| 8 | `case-03-units.md` | 31 | R3 | `100ms` | **漏報** | UNITS 缺時間單位 ms |
| 9 | `case-03-units.md` | 31 | R3 | `180ms` | **漏報** | UNITS 缺時間單位 ms |
| 10 | `case-04-punct-space.md` | 30 | R4 | `〔` | **漏報** | FULLWIDTH_PUNCT 手寫清單沒收全形方括號，Unicode 標為 Ps／Pe |
| 11 | `case-04-punct-space.md` | 30 | R4 | `｝` | **漏報** | FULLWIDTH_PUNCT 手寫清單沒收全形大括號 |
| 12 | `case-04-punct-space.md` | 32 | R4 | `＂` | **漏報** | FULLWIDTH_PUNCT 手寫清單沒收全形雙引號 |
| 13 | `case-04-punct-space.md` | 32 | R4 | `％` | **漏報** | FULLWIDTH_PUNCT 手寫清單沒收全形百分號 |
| 14 | `case-04-punct-space.md` | 34 | R4 | `／` | **漏報** | FULLWIDTH_PUNCT 手寫清單沒收全形斜線 |
| 15 | `case-05-duplicate.md` | 23 | R5 | `。。。` | **漏報** | DUP_PUNCT_RE 只認 `[！？]{2,}`，重複句號抓不到 |
| 16 | `case-05-duplicate.md` | 25 | R5 | `，，` | **漏報** | DUP_PUNCT_RE 只認 `[！？]{2,}`，重複逗號抓不到 |
| 17 | `case-05-duplicate.md` | 27 | R5 | `！ ！` | **漏報** | 重複標點中間夾空白時 DUP_PUNCT_RE 不連續，只被 R4 抓到空格 |
| 18 | `case-06-halfwidth.md` | 21 | R6 | `收好.這個` | **漏報** | HALFWIDTH_PUNCT_RE 的集合只有 `,!?;:`，缺半形句號 |
| 19 | `case-06-halfwidth.md` | 23 | R6 | `'標準流程'` | **漏報** | CJK_QUOTE_RE 只認半形雙引號，缺單引號 |
| 20 | `case-06-halfwidth.md` | 25 | R6 | `[影像]` | **漏報** | 半形方括號不在任何半形標點集合裡 |
| 21 | `case-06-halfwidth.md` | 27 | R6 | `{進階}` | **漏報** | 半形大括號不在任何半形標點集合裡 |
| 22 | `case-07-english.md` | 23 | R8 | `He said，it works` | **漏報** | QUOTED_SPAN_RE 只掃引號與書名號包起來的整段，沒有引號的英文整句不檢查 |
| 23 | `case-07-english.md` | 25 | R8 | `Stay hungry！` | **漏報** | FULLWIDTH_IN_EN_RE 缺全形驚嘆號 |
| 24 | `case-07-english.md` | 27 | R8 | `Are you serious？` | **漏報** | FULLWIDTH_IN_EN_RE 缺全形問號 |

## 修正缺陷

| # | 樣本 | 行 | 規則 | 成因 |
| --- | --- | --- | --- | --- |
| 25 | `case-04-punct-space.md` | 32 | R2 | fix_fullwidth_digit 把 `１５` 轉成 `15` 之後製造出中文與數字之間缺空格，但 fix_missing_space 在 FIXERS 裡排在它前面，同一次 pass 收不到 |
| 26 | `case-05-duplicate.md` | 27 | R5 | fix_fullwidth_space 拿掉 `！ ！` 中間的空白之後製造出重複標點，但 fix_duplicate_punct 在 FIXERS 裡排在它前面，同一次 pass 收不到 |
| 27 | 不綁樣本 | — | — | fix_file 讀檔沒有關掉萬用換行，CRLF 檔案被靜靜改成 LF。fix_file 裡那行 newline 判斷看得出本意是保留 CRLF，但 `open()` 預設的萬用換行已經先把 CRLF 轉成 LF，條件永遠成立不了。修法是 `open(path, encoding="utf-8", newline="")` |

合計 **27** 條。

## 需裁決：規則層分不出來的

**這些是預期會出錯的例子。** 帶了 `--units` 之後腳本一定會把 `5G` 報成違規，那就是誤報。

它不列進上面的誤報，因為那一類的定義是「不該報卻報了，修好就會轉綠」，而這條**修不好**——
`5G` 與 `3bar` 在 `UNIT_RE` 眼裡形狀相同（數字緊接英文、兩側不接字母），
那個形狀本身不帶區分資訊。誤報要在裁決步驟消除，不是在腳本層。

腳本層能保證的只有**誤報不會造成傷害**：一律標 `low`、一律不可修、`--fix` 之後逐字不變。
這三條是綠燈，鎖在 `script/test_units.py`。模型有沒有真的 drop 掉，
只有 `evals/cases/custom-unit-overlap` 測得到。

不帶 `--units` 時這些一筆都不會報——誤報只在使用者主動擴充單位表時才存在。

| 樣本 | 行 | 片段 | 帶入的單位 | 裁決 | 實際是什麼 |
| --- | --- | --- | --- | --- | --- |
| `case-11-unit-overlap.md` | 5 | `5G` | `G` | **drop** | 行動網路制式，不是 5 高斯 |
| `case-11-unit-overlap.md` | 5 | `4G` | `G` | **drop** | 行動網路制式，不是 4 高斯 |
| `case-11-unit-overlap.md` | 7 | `4K` | `K` | **drop** | 螢幕解析度，不是 4 克耳文 |
| `case-11-unit-overlap.md` | 7 | `8K` | `K` | **drop** | 螢幕解析度，不是 8 克耳文 |
| `case-11-unit-overlap.md` | 11 | `65W` | `W` | **keep 並補空格** | 功率 65 瓦，要補成 `65 W` |
| `case-11-unit-overlap.md` | 11 | `24h` | `h` | **keep 並補空格** | 24 小時，要補成 `24 h` |
| `case-11-unit-overlap.md` | 13 | `3bar` | `bar` | **keep 並補空格** | 壓力 3 巴，要補成 `3 bar` |
| `case-11-unit-overlap.md` | 17 | `2T` | `T` | **drop** | 口語的 `2TB`，不是 2 特斯拉 |
| `case-11-unit-overlap.md` | 19 | `3in1` | `in` | **drop** | 三合一配方，不是 3 英吋 |

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

