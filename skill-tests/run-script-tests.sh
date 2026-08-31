#!/usr/bin/env bash
# 跑第一層（綠燈）與第二層（紅燈）的腳本測試。
#
#   bash skill-tests/run-script-tests.sh                # 全部
#   bash skill-tests/run-script-tests.sh --green-only   # 只跑綠燈，開發時用
#
# 紅燈代表 check_copywriting.py 還有缺陷沒修，見 KNOWN-GAPS.md。
# 修好之前這支指令的 exit code 就是非零，這是刻意的。
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE/script"

GREEN=(test_cases test_fix test_cli test_citations test_report test_units)
RED=(test_gaps)

green_only=0
[[ "${1:-}" == "--green-only" ]] && green_only=1

echo "── 綠燈：鎖住現行正確行為 ──"
python3 -m unittest "${GREEN[@]}" 2>&1 | tail -n 4
green_rc=${PIPESTATUS[0]}

if (( green_only )); then
  exit "$green_rc"
fi

echo
echo "── 紅燈：已知缺陷，修好前應該是紅的 ──"
python3 -m unittest "${RED[@]}" 2>&1 | tail -n 4
red_rc=${PIPESTATUS[0]}

echo
gaps=$(python3 -c 'import gaps; print(gaps.gap_count())')
if (( green_rc != 0 )); then
  echo "綠燈有失敗——腳本的現行行為被改壞了，先看上面那段。"
elif (( red_rc != 0 )); then
  echo "綠燈全過。紅燈仍有 ${gaps} 條缺陷待修，逐條說明見 skill-tests/KNOWN-GAPS.md。"
else
  echo "綠燈與紅燈都過了。若 KNOWN-GAPS.md 還列著缺陷，代表已經修好但沒清掉，"
  echo "請把修好的條目從 script/gaps.py 刪掉，重跑 regenerate_cases.py 與 KNOWN-GAPS.md。"
fi

(( green_rc == 0 && red_rc == 0 )) && exit 0 || exit 1
