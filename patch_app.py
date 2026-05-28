# patch_app.py - local/app.py のDATA_DIRを修正
from pathlib import Path

target = Path(__file__).parent / "local" / "app.py"
content = target.read_text(encoding="utf-8")
content = content.replace(
    'DATA_DIR = SCRIPT_DIR.parent / "DATA"',
    'DATA_DIR = SCRIPT_DIR / "DATA"'
)
target.write_text(content, encoding="utf-8")
print("app.py patched OK")