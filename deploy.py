"""
deploy.py - GitHub auto push

Place: C:\\Users\\tenni\\ten-shi\\fukuoka-ten-shi\\deploy.py
Run  : python deploy.py
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_git(cmd, cwd):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.returncode == 0, result.stdout + result.stderr


def main():
    repo_path = Path(__file__).parent

    print("=" * 70)
    print("deploy.py: GitHub auto push")
    print("=" * 70)
    print(f"repo: {repo_path}")

    if not repo_path.exists():
        print(f"[ERROR] repo not found: {repo_path}")
        sys.exit(1)

    # check status
    ok, out = run_git("git status --short", repo_path)
    if not ok:
        print(f"[ERROR] git status failed: {out}")
        sys.exit(1)

    if not out.strip():
        print("[INFO] nothing to commit (already up to date)")
        return

    print("\nChanges:")
    print(out)

    commit_msg = f"update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    print(f"commit: {commit_msg}")

    # git add
    ok, out = run_git("git add .", repo_path)
    if not ok:
        print(f"[ERROR] git add failed: {out}")
        sys.exit(1)
    print("[OK] git add")

    # git commit
    ok, out = run_git(f'git commit -m "{commit_msg}"', repo_path)
    if not ok:
        print(f"[ERROR] git commit failed: {out}")
        sys.exit(1)
    print("[OK] git commit")

    # git pull --rebase: SNS自動投稿(GitHub Actions)が push した
    # スナップショット/画像コミットを先に取り込む（枝分かれで push が弾かれるのを防ぐ）
    ok, out = run_git("git pull --rebase origin main", repo_path)
    if not ok:
        print(f"[WARN] git pull --rebase で問題: {out}")
        run_git("git rebase --abort", repo_path)  # 念のため中断して素のpushを試みる

    # git push（弾かれたら pull --rebase してもう一度）
    ok, out = run_git("git push origin main", repo_path)
    if not ok:
        print("[INFO] push 失敗。pull --rebase して再試行します。")
        run_git("git pull --rebase origin main", repo_path)
        ok, out = run_git("git push origin main", repo_path)
    if not ok:
        print(f"[ERROR] git push failed: {out}")
        sys.exit(1)
    print("[OK] git push")

    print("=" * 70)
    print("Done! Published in 2-3 min:")
    print("  https://hiro-ito1.github.io/fukuoka-ten-shi/")
    print("=" * 70)


if __name__ == "__main__":
    main()