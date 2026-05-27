r"""
generate_html_auto.py
fukuoka-ten-shi / local / 専用版

配置場所: C:\Users\tenni\ten-shi\fukuoka-ten-shi\local\generate_html_auto.py
入力: C:\Users\tenni\ten-shi\DATA\events_approved.json
出力:
  1. C:\Users\tenni\ten-shi\fukuoka-ten-shi\docs\ (世界配布用)
  2. GitHub に自動プッシュ（deploy.py 経由）

理想のフロー:
  管理画面で承認
    (自動)
  WEB生成
    (自動)
  fukuoka-ten-shi/docs/ に反映
    (自動)
  GitHub に自動プッシュ
    (自動)
  世界公開完了
"""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


# ============================================
# パス設定
# ============================================

# このファイルの場所: fukuoka-ten-shi/local/
LOCAL_DIR = Path(__file__).parent          # local/
FUKUOKA_DIR = LOCAL_DIR.parent             # fukuoka-ten-shi/
TEN_SHI_DIR = FUKUOKA_DIR.parent          # ten-shi/

# 入力: DATA/events_approved.json
DATA_FILE = TEN_SHI_DIR / "DATA" / "events_approved.json"

# 出力1: fukuoka-ten-shi/docs/（世界配布用）
DOCS_DIR = FUKUOKA_DIR / "docs"

# デプロイスクリプト
DEPLOY_SCRIPT = FUKUOKA_DIR / "deploy.py"


# ============================================
# HTML生成クラス（generate_html.py v6 から移植）
# ============================================

class HTMLGenerator:
    """HTML生成クラス（世界配布用）"""

    def __init__(self, data_file: str, output_dir: str):
        self.data_file = Path(data_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def load_data(self) -> List[Dict]:
        if not self.data_file.exists():
            print(f"ERROR: data file not found: {self.data_file}")
            return []
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        events = [e for e in data if e.get('event_status') == '募集中']
        events.sort(key=lambda x: x.get('event_date', ''))
        print(f"Loaded: {len(events)} events")
        return events

    def group_by_month(self, events: List[Dict]) -> Dict:
        groups = defaultdict(list)
        for event in events:
            date_str = event.get('event_date', '')
            try:
                month_key = date_str[:7]  # YYYY/MM
                groups[month_key].append(event)
            except Exception:
                continue
        return dict(sorted(groups.items()))

    def group_by_date(self, events: List[Dict]) -> Dict:
        groups = defaultdict(list)
        for event in events:
            date_str = event.get('event_date', '')
            groups[date_str].append(event)
        return dict(sorted(groups.items()))

    def generate_html(self):
        """HTML生成（ACTIVE_CODE の generate_html.py と同じロジック）"""

        # ACTIVE_CODE の generate_html.py を直接呼び出す（DRY原則）
        active_generate = TEN_SHI_DIR / "ACTIVE_CODE" / "generate_html.py"

        if active_generate.exists():
            print("Using ACTIVE_CODE/generate_html.py...")
            import importlib.util
            spec = importlib.util.spec_from_file_location("generate_html", active_generate)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            # ACTIVE_CODE のジェネレーターを実行
            gen = mod.HTMLGenerator(str(DATA_FILE), str(DOCS_DIR))
            gen.generate_html()
        else:
            print(f"ERROR: {active_generate} not found")
            raise FileNotFoundError(f"{active_generate} not found")


# ============================================
# 自動デプロイ
# ============================================

def auto_deploy():
    """GitHub に自動プッシュ"""
    print()
    print("=" * 60)
    print("Auto deploy to GitHub...")
    print("=" * 60)

    if not DEPLOY_SCRIPT.exists():
        print(f"ERROR: deploy.py not found: {DEPLOY_SCRIPT}")
        return False

    result = subprocess.run(
        ["python", str(DEPLOY_SCRIPT)],
        cwd=str(FUKUOKA_DIR),
        capture_output=False  # リアルタイム出力
    )

    if result.returncode == 0:
        print("Deploy SUCCESS!")
        return True
    else:
        print("Deploy FAILED!")
        return False


# ============================================
# メイン処理
# ============================================

def main():
    print("=" * 60)
    print("fukuoka-ten-shi WEB Generator + Auto Deploy")
    print("=" * 60)
    print(f"Data   : {DATA_FILE}")
    print(f"Output : {DOCS_DIR}")
    print(f"Deploy : {DEPLOY_SCRIPT}")
    print("-" * 60)

    # Step 1: データ確認
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found")
        return

    # Step 2: HTML生成
    print()
    print("Step 1/2: Generate HTML...")
    generator = HTMLGenerator(str(DATA_FILE), str(DOCS_DIR))
    generator.generate_html()
    print("HTML generation DONE!")

    # Step 3: 自動デプロイ
    print()
    print("Step 2/2: Auto deploy...")
    success = auto_deploy()

    print()
    print("=" * 60)
    if success:
        print("ALL DONE!")
        print()
        print("Check: https://hiro-ito1.github.io/fukuoka-ten-shi/")
    else:
        print("HTML generated, but deploy failed.")
        print("Run manually: python deploy.py")
    print("=" * 60)


if __name__ == "__main__":
    main()