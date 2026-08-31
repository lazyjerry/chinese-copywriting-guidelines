#!/usr/bin/env bash
# 選用，需要網路，不在預設測試裡。
#
# 比對本地 README.md 前 266 行與上游是否仍然逐字相同。
# 行號引用的前提就是這段相同；一旦漂了，references/rules.md 要整份重新核對。
set -euo pipefail

RAW="https://raw.githubusercontent.com/sparanoid/chinese-copywriting-guidelines/master/README.md"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo "抓取上游 README.md …"
curl -sS -f -o "$TMP" "$RAW"

PREFIX=$(python3 -c "
import json, pathlib
p = pathlib.Path('$HERE/script/citations-baseline.json')
print(json.loads(p.read_text(encoding='utf-8'))['prefix_lines'])
")

if diff -q <(head -n "$PREFIX" "$ROOT/README.md") <(head -n "$PREFIX" "$TMP") >/dev/null; then
  echo "前 ${PREFIX} 行與上游一致，行號引用的前提仍然成立。"
  exit 0
fi

echo "前 ${PREFIX} 行與上游已經不同："
diff <(head -n "$PREFIX" "$ROOT/README.md") <(head -n "$PREFIX" "$TMP") | head -n 40
echo
echo "請重新核對 skills/chinese-copywriting/references/rules.md 的行號與細則，"
echo "確認之後再跑 skill-tests/script/regenerate_citations.py 更新基準。"
exit 1
