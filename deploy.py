"""
fukuoka-ten-shi 自動デプロイスクリプト
v1.0: GitHub自動プッシュ

使い方:
    python deploy.py

機能:
    1. docs/ を GitHub にプッシュ
    2. コミットメッセージ自動生成
    3. エラーハンドリング
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: str, cwd: Path = None) -> tuple[bool, str]:
    """
    コマンドを実行
    
    Returns:
        (成功したか, 出力メッセージ)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    
    except Exception as e:
        return False, str(e)


def check_git_status(repo_path: Path) -> bool:
    """Git リポジトリの状態を確認"""
    success, output = run_command("git status", cwd=repo_path)
    
    if not success:
        print("❌ Gitリポジトリではありません")
        return False
    
    if "nothing to commit" in output:
        print("ℹ️  変更がありません（すでに最新）")
        return False
    
    return True


def deploy_to_github(repo_path: Path, commit_message: str = None):
    """
    GitHub に自動プッシュ
    
    Args:
        repo_path: リポジトリのパス
        commit_message: コミットメッセージ（省略時は自動生成）
    """
    print("=" * 70)
    print("🚀 fukuoka-ten-shi 自動デプロイ開始")
    print("=" * 70)
    print()
    
    # リポジトリパスの確認
    if not repo_path.exists():
        print(f"❌ リポジトリが見つかりません: {repo_path}")
        return False
    
    print(f"📂 リポジトリ: {repo_path}")
    print()
    
    # Git状態確認
    if not check_git_status(repo_path):
        return False
    
    print()
    print("📝 変更内容:")
    success, output = run_command("git status --short", cwd=repo_path)
    if success:
        print(output)
    print()
    
    # コミットメッセージ生成
    if not commit_message:
        now = datetime.now()
        commit_message = f"データ更新: {now.strftime('%Y-%m-%d %H:%M')}"
    
    print(f"💬 コミットメッセージ: {commit_message}")
    print()
    
    # ステップ1: git add
    print("ステップ 1/3: git add ...")
    success, output = run_command("git add .", cwd=repo_path)
    
    if not success:
        print(f"❌ git add 失敗: {output}")
        return False
    
    print("✅ git add 完了")
    print()
    
    # ステップ2: git commit
    print("ステップ 2/3: git commit ...")
    
    # コミットメッセージをエスケープ
    escaped_message = commit_message.replace('"', '\\"')
    
    success, output = run_command(
        f'git commit -m "{escaped_message}"',
        cwd=repo_path
    )
    
    if not success:
        print(f"❌ git commit 失敗: {output}")
        return False
    
    print("✅ git commit 完了")
    print()
    
    # ステップ3: git push
    print("ステップ 3/3: git push ...")
    success, output = run_command("git push origin main", cwd=repo_path)
    
    if not success:
        # main ブランチが存在しない場合は master を試す
        print("ℹ️  main ブランチが見つかりません。master ブランチを試します...")
        success, output = run_command("git push origin master", cwd=repo_path)
    
    if not success:
        print(f"❌ git push 失敗: {output}")
        print()
        print("トラブルシューティング:")
        print("1. GitHub への認証設定を確認してください")
        print("2. リモートリポジトリが正しく設定されているか確認してください")
        print("   git remote -v")
        return False
    
    print("✅ git push 完了")
    print()
    
    print("=" * 70)
    print("🎉 デプロイ成功！")
    print("=" * 70)
    print()
    print("🌐 GitHub Pages:")
    print("   https://hiro-ito1.github.io/fukuoka-ten-shi/")
    print()
    print("⏰ 反映まで数分かかる場合があります")
    print()
    
    return True


def main():
    """メイン処理"""
    # fukuoka-ten-shi のパス
    # ※注: 実行時のカレントディレクトリに合わせて調整してください
    repo_path = Path(__file__).parent
    
    # デプロイ実行
    success = deploy_to_github(repo_path)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
