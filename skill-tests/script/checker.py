"""載入待測的 check_copywriting 模組。

腳本放在 skills/ 底下、檔名帶底線，直接 import 不會找到，
所以集中在這裡處理路徑，其他測試檔一律 `import checker`。
"""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / "skills" / "chinese-copywriting"
SCRIPT_PATH = SKILL_DIR / "scripts" / "check_copywriting.py"

_spec = importlib.util.spec_from_file_location("check_copywriting", SCRIPT_PATH)
_module = importlib.util.module_from_spec(_spec)
sys.modules["check_copywriting"] = _module
_spec.loader.exec_module(_module)

check_file = _module.check_file
fix_file = _module.fix_file
FIXABLE = _module.FIXABLE
RULE_TITLES = _module.RULE_TITLES
UNITS = _module.UNITS


def check_text(text, dispute=False):
    """把一段文字寫進暫存檔再檢查，回傳 Issue 清單。"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        return check_file(path, dispute=dispute)
    finally:
        Path(path).unlink(missing_ok=True)


def fix_text(text):
    """把一段文字寫進暫存檔跑 --fix，回傳 (修正後內容, 改動行數)。"""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        changed = fix_file(path)
        return Path(path).read_text(encoding="utf-8"), changed
    finally:
        Path(path).unlink(missing_ok=True)
