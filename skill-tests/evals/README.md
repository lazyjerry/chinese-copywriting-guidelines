# 模型行為 eval

腳本測得到「檢查器有沒有抓對」，測不到「模型有沒有照約定做事」。
開跑前是否先問、預設檔案挑得對不對、報告有沒有附引用參考——這些只能實際跑一次模型。

## 跑法

```bash
bash skill-tests/evals/run-evals.sh                    # 全部，只產 transcript
bash skill-tests/evals/run-evals.sh citation-required  # 只跑一個
bash skill-tests/evals/run-evals.sh --judge            # 額外自動評分
```

每個 case 在一份乾淨的暫存目錄裡跑，skill 裝在該目錄的 `.claude/skills/` 底下，
不會讀到本機既有的設定。輸出寫進 `results/<case>/`，該目錄不進版控。

預設只產 transcript 交人判讀。加 `--judge` 會再呼叫一次模型，依 `expect.md` 給出
PASS 或 FAIL——方便，但評分本身也是模型判斷，結論有雜訊，有疑問就自己讀 transcript。

## 十個 case

| case | 驗的是 |
| --- | --- |
| `trigger-proofread` | 說「校對排版」時會觸發 |
| `no-trigger-polish` | 說「潤飾通順」時**不**觸發，屬於別的工具 |
| `no-trigger-translate` | 翻譯請求**不**觸發 |
| `ask-before-run` | 動手前先問處置方式，未同意不得帶 `--fix` |
| `default-open-file` | 沒指定路徑時，預設選項是編輯器當前開啟的檔案 |
| `citation-required` | 每條違規都附 `{規則名稱} L{起}-L{迄}`，行號與索引一致 |
| `rulebook-counterexample` | 校對規則書時不修正刻意寫錯的示範句 |
| `custom-unit-overlap` | `--units` 帶進來的命中，代號 drop、量測值 keep |
| `artifact-target` | 目標檔是產物時，改來源不改產物 |
| `write-mode` | 撰寫模式直接套用規則，不出報告、不附引用 |

前三個是觸發邊界，中間三個是流程約定，後四個是內容判斷。

`artifact-target` 的素材是一份帶「不要手動編輯」註記的產物，配一支生成它的腳本。
只改產物下次重跑建置就還原，而腳本層看不出目標檔是不是產物。

`custom-unit-overlap` 是裁決層唯一測得到的地方。腳本對 `5G` 與 `3bar` 一視同仁全報 `low`
（`script/test_units.py` 鎖住這條界線），要分辨它們只能靠模型讀上下文——腳本測不到那件事。

## 加一個 case

建一個 `cases/<名稱>/` 目錄，放兩個檔：

- `prompt.txt`：給模型的輸入，一句話就好
- `expect.md`：通過條件與失敗訊號，寫成人和模型都讀得懂的條列

需要待校對的素材就加進 `fixtures/`。那裡的檔案**故意違反排版規則**，不要修好它們。
