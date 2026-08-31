# chinese-copywriting skill 測試

三層測試，各自解決不同的問題。

| 層 | 測什麼 | 怎麼跑 | 成本 |
| --- | --- | --- | --- |
| 綠燈 | 鎖住 `check_copywriting.py` 現行正確的行為 | `bash skill-tests/run-script-tests.sh` | 秒回、無網路 |
| 紅燈 | 標出腳本還做不到的事 | 同上 | 秒回、無網路 |
| eval | 模型有沒有照 SKILL.md 的約定做事 | `bash skill-tests/evals/run-evals.sh` | 慢、有 API 成本 |

不接 CI，改完自己跑。

## 現在應該是紅的

紅燈是真的失敗，沒有用 `expectedFailure` 蓋掉——把紅燈藏成綠色等於沒測。
失敗數不等於缺陷數：28 條缺陷展開成 30 個失敗的 subtest，因為修正缺陷同時
違反「修完要乾淨」與「再跑不動」兩條不變量。

逐條說明見 [KNOWN-GAPS.md](KNOWN-GAPS.md)。修好一條，對應的紅燈會自己轉綠。

開發別的東西時只想確認沒改壞：

```bash
bash skill-tests/run-script-tests.sh --green-only
```

## 目錄

```
skill-tests/
├─ run-script-tests.sh        綠燈 + 紅燈
├─ check-upstream-drift.sh    選用，需網路：比對本地 README 與上游是否仍一致
├─ KNOWN-GAPS.md              缺陷清單，由 gaps.py 生成
├─ script/
│  ├─ cases/                  10 份約 500 字的樣本文本
│  ├─ cases.json              違規快照，由 regenerate_cases.py 生成
│  ├─ gaps.py                 缺陷清單的唯一來源
│  ├─ citations-baseline.json 引用索引的基準，由 regenerate_citations.py 生成
│  ├─ checker.py              載入待測腳本，並提供 check_text／fix_text
│  ├─ citations.py            解析 README 結構與 rules.md 的索引表
│  ├─ test_cases.py           綠燈：逐案快照、刻意行為、規則書不變量
│  ├─ test_gaps.py            紅燈
│  ├─ test_fix.py             --fix 逐條規則與邊界
│  ├─ test_cli.py             exit code、JSON、旗標
│  └─ test_citations.py       行號正確性、來源漂移、文件自我一致
└─ evals/                     模型行為，見 evals/README.md
```

## 資料與邏輯分離

要加一個腳本測試案例，寫一份 `script/cases/case-*.md`、在
`regenerate_cases.py` 的 `TITLES` 補一行，然後：

```bash
python3 skill-tests/script/regenerate_cases.py
```

測試邏輯不必動。三支 `regenerate_*.py` 各自負責一份生成檔：

| 腳本 | 產出 | 什麼時候跑 |
| --- | --- | --- |
| `regenerate_cases.py` | `cases.json` | 改了樣本或 `gaps.py` |
| `regenerate_known_gaps.py` | `KNOWN-GAPS.md` | 改了 `gaps.py` |
| `regenerate_citations.py` | `citations-baseline.json` | **確認過** README 的改動之後 |

`regenerate_citations.py` 是唯一需要停下來想一下的：雜湊對不上代表 README 改了，
要先確認 `references/rules.md` 的行號與細則要不要跟著改，不要直接覆蓋基準了事。

## 樣本刻意寫錯

`script/cases/` 與 `evals/fixtures/` 底下的檔案**故意違反排版規則**，
是測試資料不是文件。不要拿排版檢查腳本去掃它們，也不要「順手修好」。

說明文件本身則要合規：

```bash
python3 skills/chinese-copywriting/scripts/check_copywriting.py \
  skill-tests/README.md skill-tests/KNOWN-GAPS.md skill-tests/evals/README.md
```
