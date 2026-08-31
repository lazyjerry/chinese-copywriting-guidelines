#!/usr/bin/env bash
# 第三層：模型行為 eval。慢、有成本，刻意不接在 run-script-tests.sh 裡。
#
#   bash skill-tests/evals/run-evals.sh                 # 跑全部，只產 transcript
#   bash skill-tests/evals/run-evals.sh citation-required   # 只跑一個 case
#   bash skill-tests/evals/run-evals.sh --judge         # 額外用第二次呼叫依 expect.md 評分
#
# 每個 case 在一份乾淨的暫存 repo 副本裡跑，skill 裝在該副本的 .claude/skills/ 底下，
# 避免讀到本機既有的設定。輸出寫進 results/<case>/。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
RESULTS="$HERE/results"

command -v claude >/dev/null || { echo "找不到 claude CLI，先安裝再跑。"; exit 2; }

judge=0
cases=()
for arg in "$@"; do
  case "$arg" in
    --judge) judge=1 ;;
    *) cases+=("$arg") ;;
  esac
done
(( ${#cases[@]} )) || cases=($(ls "$HERE/cases"))

mkdir -p "$RESULTS"
pass=0; fail=0; done_n=0

for name in "${cases[@]}"; do
  dir="$HERE/cases/$name"
  [[ -d "$dir" ]] || { echo "沒有這個 case：$name"; exit 2; }

  work="$(mktemp -d)"
  mkdir -p "$work/.claude/skills"
  cp -R "$ROOT/skills/chinese-copywriting" "$work/.claude/skills/"
  cp "$ROOT/README.md" "$work/"
  mkdir -p "$work/skill-tests/evals/fixtures"
  cp "$HERE"/fixtures/* "$work/skill-tests/evals/fixtures/"

  out="$RESULTS/$name"
  mkdir -p "$out"
  echo "── $name ──"
  ( cd "$work" && claude -p "$(cat "$dir/prompt.txt")" --output-format json ) \
    > "$out/output.json" 2> "$out/stderr.txt"
  python3 - "$out/output.json" "$out/transcript.md" <<'PY'
import json, sys, pathlib
raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
try:
    data = json.loads(raw)
    text = data.get("result") or json.dumps(data, ensure_ascii=False, indent=2)
except json.JSONDecodeError:
    text = raw
pathlib.Path(sys.argv[2]).write_text(text, encoding="utf-8")
PY
  cp "$dir/expect.md" "$out/expect.md"
  rm -rf "$work"
  done_n=$((done_n + 1))

  if (( judge )); then
    verdict=$(claude -p "你是 eval 評分員。依〈通過條件〉判斷〈實際輸出〉是否通過。
第一行只輸出 PASS 或 FAIL，第二行起寫一句理由。

# 通過條件
$(cat "$dir/expect.md")

# 實際輸出
$(cat "$out/transcript.md")")
    printf '%s\n' "$verdict" > "$out/verdict.txt"
    if [[ "$verdict" == PASS* ]]; then
      pass=$((pass + 1)); echo "  PASS"
    else
      fail=$((fail + 1)); echo "  FAIL — $(sed -n 2p <<<"$verdict")"
    fi
  else
    echo "  transcript → skill-tests/evals/results/$name/transcript.md"
  fi
done

echo
if (( judge )); then
  echo "評分結果：$pass 通過 / $fail 失敗，共 $done_n 個 case。"
  (( fail == 0 )) || exit 1
else
  echo "$done_n 個 case 的 transcript 已產出，對照各自的 expect.md 判讀。"
  echo "要自動評分請加 --judge。"
fi
