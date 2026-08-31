# chinese-copywriting skill

> 語言：**繁體中文** ｜ [English](SKILL-README.en.md) ｜ [简体中文](SKILL-README.zh-Hans.md)

把《中文文案排版指北》做成 AI 編碼代理可直接使用的 skill，附一支零依賴的檢查腳本。

支援 Claude Code、Codex CLI、Copilot CLI、OpenCode、Cursor 等讀取 `skills/` 目錄的工具。

## 這個 skill 做什麼

只管**排版層**：空格、全形半形、標點形制、名詞寫法。

| 做 | 不做 |
| --- | --- |
| 中英文、中文與數字、數字與單位之間的空格 | 錯別字校訂 |
| 全形與半形標點的形制 | 文句潤飾、改寫 |
| 重複標點 | 去除 AI 痕跡 |
| 專有名詞大小寫、不道地的縮寫 | 翻譯 |

不動字句與內容。遇到職責以外的需求，skill 會說明並交給對應的工具。

## 安裝

### 方法一：ai-global（推薦）

[ai-global](https://github.com/lazyjerry/ai-global) 會把 skill 裝進中央目錄，再一次投影給所有 AI 工具，不必每個工具各複製一份。

```bash
ai-global add-skill lazyjerry/chinese-copywriting-guidelines
ai-global relink
```

`add-skill` 會自動掃出 repo 裡含 `SKILL.md` 的目錄，實體放進 `~/.ai-global/v-skills/lazyjerry/chinese-copywriting-guidelines/chinese-copywriting/`，各工具讀的是投影出去的 symlink。

只裝在單一專案就加 `-p`：

```bash
ai-global -p add-skill lazyjerry/chinese-copywriting-guidelines
```

常用的後續操作：

| 指令 | 用途 |
| --- | --- |
| `ai-global list-skills` | 列出已安裝的 skill 分類樹 |
| `ai-global update-skills` | 依安裝紀錄重新拉取更新 |
| `ai-global disable chinese-copywriting` | 暫時停用，實體與紀錄都保留 |
| `ai-global enable chinese-copywriting` | 解除停用 |
| `ai-global remove-skill lazyjerry/chinese-copywriting-guidelines` | 移除並清除安裝紀錄 |

**要修改 skill 內容請改 `v-skills` 底下那份**，`~/.ai-global/skills/` 只是扁平的 symlink 投影層。

### 方法二：手動安裝

各家工具的 skills 目錄都只認第一層，把整個 `chinese-copywriting` 目錄放進去即可：

| 工具 | 全域 | 專案 |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Codex CLI | `~/.agents/skills/` | `.agents/skills/` |
| Copilot CLI | `~/.copilot/skills/` | `.github/skills/` |
| OpenCode | `~/.config/opencode/skills/` | `.claude/skills/` |
| Cursor | `~/.cursor/skills/` | `.cursor/skills/` |

以 Claude Code 全域安裝為例：

```bash
git clone https://github.com/lazyjerry/chinese-copywriting-guidelines.git
cp -r chinese-copywriting-guidelines/skills/chinese-copywriting ~/.claude/skills/
```

改建 symlink 的話，之後 `git pull` 就能同步更新：

```bash
cd chinese-copywriting-guidelines
ln -s "$(pwd)/skills/chinese-copywriting" ~/.claude/skills/chinese-copywriting
```

### 確認裝好了

在代理裡輸入「幫我校對這份文案的排版」，看它有沒有進入校對流程。或直接跑腳本：

```bash
python3 ~/.claude/skills/chinese-copywriting/scripts/check_copywriting.py --help
```

## 使用

### 校對模式

跟代理說「校對」「排版檢查」「檢查中英文空格」，或指名某份中文文件要求檢查格式。

流程刻意把確認點放在最前面，**開跑之前一次問完兩件事**：

1. **校對哪個檔** — 預設是編輯器當前開啟的檔案，會標示「（當前開啟）」放在第一個選項。訊息裡已指定路徑就直接用。
2. **查完要怎麼處理** — 自動修正可安全處理的項目、全部修正、只出報告不改檔，或先看清單再決定。

**絕不自動改檔，也絕不未經確認就開跑。** 未取得同意之前不會執行帶 `--fix` 的指令。

報告的每一條違規都會附引用參考，指回唯一事實根據：

```text
{規則名稱} L{起始行}-L{結束行}
```

例如 `數字與單位之間需要增加空格 L52-L74`。行號查的是上游 README，不是自行推算。

校對排版規則文件時（例如本專案的 `README*.md`），`錯誤：` 底下的示範句是刻意寫錯的教材，skill 不會修正它們，並會與真違規分開列。

### 撰寫模式

請代理產出中文文案時，排版規則直接套用，不出報告、不詢問、不附引用參考。

### 只用檢查腳本

腳本零依賴，不需要 AI 代理也能單獨使用：

```bash
# 只報告，有違規時 exit code 為 1
python3 skills/chinese-copywriting/scripts/check_copywriting.py <檔案>

# 就地修正
python3 skills/chinese-copywriting/scripts/check_copywriting.py --fix <檔案>

# 機器可讀輸出
python3 skills/chinese-copywriting/scripts/check_copywriting.py --json <檔案>

# 一併檢查〈爭議〉一節的兩條規則
python3 skills/chinese-copywriting/scripts/check_copywriting.py --dispute <檔案>
```

`--fix` 只處理可安全機械判定的規則：中英文與數字之間的空格、數字與單位之間的空格、全形標點旁多餘的空白、重複的標點、全形數字。大小寫、不道地的縮寫等需要語意判斷的項目一律只報告。

腳本會自動跳過程式碼區塊、行內程式碼的內容、URL、Markdown 連結目標與表格分隔線、HTML 標籤屬性，以及 YAML frontmatter。

**腳本本身不做互動確認**，這樣才進得了 CI；「問使用者要不要修」是 skill 流程的責任。

## 規則與引用來源

12 條規則的完整正誤範例、行號索引與例外索引都在
[skills/chinese-copywriting/references/rules.md](skills/chinese-copywriting/references/rules.md)。

行號的唯一事實根據是上游 README：

<https://github.com/sparanoid/chinese-copywriting-guidelines/blob/master/README.md>

本專案 `README.md` 第 1 至 266 行與上游逐字相同，所以同一組行號兩邊都適用。核對基準記在 `references/rules.md` 開頭，上游改版後要重新核對。

## 開發

### 目錄

```
skills/chinese-copywriting/
├─ SKILL.md                    流程、引用規範、報告樣板
├─ references/rules.md         唯一事實根據、規則索引、例外索引、12 條細則
└─ scripts/check_copywriting.py

skill-tests/                   三層測試，見下
```

### 改東西要動哪幾份

| 想改的東西 | 要動的檔 | 收尾 |
| --- | --- | --- |
| 校對流程、報告格式 | `SKILL.md` | 跑排版自檢 |
| 規則細則、行號索引 | `references/rules.md` | 跑 `test_citations.py` |
| 偵測或修正邏輯 | `scripts/check_copywriting.py` | 跑全部測試 |
| 測試樣本 | `skill-tests/script/cases/` | 跑 `regenerate_cases.py` |
| 已知缺陷清單 | `skill-tests/script/gaps.py` | 跑 `regenerate_cases.py` 與 `regenerate_known_gaps.py` |

三支產生器維護三份生成檔，不要手改生成檔：

```bash
python3 skill-tests/script/regenerate_cases.py       # cases.json
python3 skill-tests/script/regenerate_known_gaps.py  # KNOWN-GAPS.md
python3 skill-tests/script/regenerate_citations.py   # citations-baseline.json
```

`regenerate_citations.py` 是唯一需要停下來想一下的：雜湊對不上代表上游 README 改了，要先確認 `references/rules.md` 的行號與細則要不要跟著改，**不要直接覆蓋基準了事**。

### 文件本身也要合規

改完說明文件，拿自己的腳本掃一遍：

```bash
python3 skills/chinese-copywriting/scripts/check_copywriting.py \
  SKILL-README.md skills/chinese-copywriting/SKILL.md
```

`skill-tests/script/cases/` 與 `skill-tests/evals/fixtures/` 底下的檔案**故意違反排版規則**，是測試資料不是文件，已由 `.remarkignore` 排除，不要「順手修好」。

## 測試

```bash
bash skill-tests/run-script-tests.sh               # 綠燈 + 紅燈，秒回、無網路
bash skill-tests/run-script-tests.sh --green-only  # 只跑綠燈，開發時用
bash skill-tests/evals/run-evals.sh                # 模型行為，慢、有 API 成本
bash skill-tests/check-upstream-drift.sh           # 選用，需網路
```

三層各自解決不同問題：

| 層 | 測什麼 |
| --- | --- |
| 綠燈 | 鎖住檢查腳本現行**正確**的行為，含刻意不做的事 |
| 紅燈 | 標出腳本**還做不到**的事 |
| eval | 模型有沒有照 `SKILL.md` 的約定做事 |

### 紅燈現在是紅的

這是刻意的。紅燈沒有用 `expectedFailure` 蓋掉——把紅燈藏成綠色等於沒測。腳本目前有一批已知缺陷，逐條列在
[skill-tests/KNOWN-GAPS.md](skill-tests/KNOWN-GAPS.md)，修好一條對應的紅燈就會自己轉綠。

修好之後的完整循環：

1. 改 `scripts/check_copywriting.py`
2. 把修好的那筆從 `skill-tests/script/gaps.py` 刪掉
3. 跑 `regenerate_cases.py` 與 `regenerate_known_gaps.py`
4. 重跑測試，綠燈應全過、紅燈少一條

**修好腳本之後綠燈會先變紅**，因為快照還停在舊行為。失敗訊息會告訴你重跑產生器，這不是缺陷。

### 加一個測試案例

寫一份 `skill-tests/script/cases/case-*.md`，在 `regenerate_cases.py` 的 `TITLES` 補一行，然後跑產生器。測試邏輯讀資料，不必動 Python。

細節見 [skill-tests/README.md](skill-tests/README.md) 與 [skill-tests/evals/README.md](skill-tests/evals/README.md)。

## 授權

與本專案相同，見 [LICENSE](LICENSE)。
