#!/usr/bin/env bash
# 產生校對報告的落地路徑。
#
#   new_report.sh <原檔路徑>
#
# 建好 <專案根>/docs/chinese-copywriting/，第一次建立時補上 .gitignore
# 讓報告只留在本機，最後把報告檔的完整路徑印到 stdout 供寫入。
#
# 檔名格式：{年月日}-{時分秒}-{原檔案名稱}.{副檔名}
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "用法：new_report.sh <原檔路徑>" >&2
  exit 1
fi

src="$1"
if [ ! -e "$src" ]; then
  echo "找不到檔案：$src" >&2
  exit 1
fi

# 專案根：git 根目錄優先，否則往上找專案標記檔
resolve_root() {
  local dir root
  dir="$(cd "$(dirname "$1")" && pwd)"
  if root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)"; then
    printf '%s\n' "$root"
    return
  fi
  while [ "$dir" != "/" ]; do
    for marker in CLAUDE.md AGENTS.md package.json; do
      if [ -e "$dir/$marker" ]; then
        printf '%s\n' "$dir"
        return
      fi
    done
    dir="$(dirname "$dir")"
  done
  # 都找不到就落在原檔旁邊，總比寫進使用者家目錄好
  printf '%s\n' "$(cd "$(dirname "$1")" && pwd)"
}

outdir="$(resolve_root "$src")/docs/chinese-copywriting"
mkdir -p "$outdir"

# 報告是本機產出，不該推上遠端。skill 被複製到別的專案時那裡不一定有對應的忽略規則，
# 所以在目錄自己這層擋掉。
if [ ! -e "$outdir/.gitignore" ]; then
  cat > "$outdir/.gitignore" <<'IGNORE'
# 校對報告只留在本機，不進版控
*
!.gitignore
IGNORE
fi

printf '%s/%s-%s\n' "$outdir" "$(date '+%Y%m%d-%H%M%S')" "$(basename "$src")"
