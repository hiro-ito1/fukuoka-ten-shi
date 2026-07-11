# -*- coding: utf-8 -*-
"""
sns_post.py - GitHub Actionsから毎日19:23(JST)目安に呼び出され、Threads と Instagram へ自動投稿する。

公開済みの docs/index.html を解析して、新着大会（前回実行時からの data-favid 差分）と
現在の掲載件数（一般/ジュニア別）を投稿文に含める。events_approved.json 等の非公開データは
一切参照しない（サイトに既に公開されている情報のみを使うため、GitHubへ同期する必要がない）。

新着0件でも必ず投稿する。ThreadsとInstagramは独立して投稿し、片方が失敗しても他方は投稿する。

認証（GitHub Secretsから環境変数で注入）:
  - THREADS_ACCESS_TOKEN   … Threads用（無ければThreadsをスキップ）
  - INSTAGRAM_ACCESS_TOKEN … Instagram用（無ければInstagramをスキップ）
状態: data/sns_snapshot.json（本リポジトリにコミットして次回実行に引き継ぐ）
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

import sns_image

REPO_ROOT = Path(__file__).parent.parent
INDEX_HTML = REPO_ROOT / "docs" / "index.html"
SNAPSHOT_FILE = REPO_ROOT / "data" / "sns_snapshot.json"
IMAGE_FILE = REPO_ROOT / "docs" / "sns" / "post_image.jpg"

GRAPH_BASE = "https://graph.threads.net/v1.0"

# Instagram（Instagramログインのビジネスアカウント。graph.instagram.com を使用）
IG_GRAPH_BASE = "https://graph.instagram.com/v21.0"
IG_USER_ID = "17841434842142642"  # 秘密情報ではないので直接埋め込み（fukuokatenshi）

JST = timezone(timedelta(hours=9))

SITE_URL = "https://hiro-ito1.github.io/fukuoka-ten-shi/"

GUIDANCE_BODY = (
    "・民間テニスクラブ・協会は無料掲載中！\n"
    "・ピックルボールは大会情報掲載を募集中（無料）\n"
    "詳細は別途確認ください"
)
# Threadsは先頭の半角#をトピック化して本文から消すため全角＃で表示を残す。
TAGS_THREADS = "＃福岡テニス　＃ピックルボール"
# Instagramは半角#が機能ハッシュタグ（発見されやすい）なので半角で付ける。
TAGS_INSTAGRAM = "#福岡テニス #ピックルボール #テニス #福岡 #大会情報"

CARD_RE = re.compile(r'<div class="event-card"([^>]*)>')
FAVID_RE = re.compile(r'data-favid="([^"]+)"')
CAT_RE = re.compile(r'data-category="([^"]+)"')


def _parse_events():
    """docs/index.html は主催アコーディオン表示のため同じ大会が複数回出現するので、
    data-favid で重複除去する。favid -> category("一般"/"ジュニア") の辞書を返す。"""
    html = INDEX_HTML.read_text(encoding="utf-8")
    deduped = {}
    for attrs in CARD_RE.findall(html):
        fm = FAVID_RE.search(attrs)
        if not fm:
            continue
        favid = fm.group(1)
        cm = CAT_RE.search(attrs)
        deduped.setdefault(favid, cm.group(1) if cm else "一般")
    return deduped


def _load_prev_ids():
    if not SNAPSHOT_FILE.exists():
        return None
    with open(SNAPSHOT_FILE, encoding="utf-8") as f:
        return set(json.load(f).get("favids", []))


def _save_snapshot(ids):
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_FILE.write_text(
        json.dumps({"favids": sorted(ids)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_post_text(new_count, general_count, junior_count, tags):
    lines = [
        "【福岡テニス大会情報】",
        "現在の掲載",
        f"　一般大会 {general_count}件",
        f"　ジュニア大会 {junior_count}件",
        f"（本日の新着 {new_count}件）",
        "",
        f"▼大会情報はこちら\n{SITE_URL}",
        "",
        GUIDANCE_BODY,
        "",
        tags,
    ]
    return "\n".join(lines)


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=str(REPO_ROOT),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def commit_and_push_image(image_path):
    """生成した画像をコミット＆pushし、その commit SHA を返す。
    Threadsは公開URLの画像しか受け付けないため、SHA固定の raw URL を使う
    （SHA固定なのでCDNキャッシュで古い画像が返る事故がない）。"""
    rel = str(image_path.relative_to(REPO_ROOT)).replace("\\", "/")
    _git("add", rel)
    staged = _git("diff", "--cached", "--quiet")
    if staged.returncode != 0:  # 差分あり
        _git("commit", "-m", "chore: sns post image [skip ci]")
        push = _git("push")
        if push.returncode != 0:
            raise RuntimeError(f"画像のpushに失敗: {push.stdout}{push.stderr}")
    sha = _git("rev-parse", "HEAD").stdout.strip()
    return sha, rel


def commit_and_push_snapshot():
    """更新したスナップショットをコミット＆push（投稿成功後に次回の基準を進める）。"""
    rel = str(SNAPSHOT_FILE.relative_to(REPO_ROOT)).replace("\\", "/")
    _git("add", rel)
    if _git("diff", "--cached", "--quiet").returncode != 0:
        _git("commit", "-m", "chore: update sns snapshot [skip ci]")
        push = _git("push")
        if push.returncode != 0:
            print(f"[WARN] スナップショットのpushに失敗: {push.stdout}{push.stderr}")


def _image_url(sha, rel):
    repo = os.environ.get("GITHUB_REPOSITORY", "hiro-ito1/fukuoka-ten-shi")
    return f"https://raw.githubusercontent.com/{repo}/{sha}/{rel}"


def _get_threads_user_id(access_token):
    resp = requests.get(
        f"{GRAPH_BASE}/me",
        params={"fields": "id,username", "access_token": access_token},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _check(resp, label):
    if resp.status_code >= 400:
        print(f"[ERROR] {label} failed: HTTP {resp.status_code}")
        print(f"  response: {resp.text}")
        resp.raise_for_status()
    return resp


def post_to_threads(access_token, user_id, text, image_url=None):
    if image_url:
        data = {
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": access_token,
        }
    else:
        data = {"media_type": "TEXT", "text": text, "access_token": access_token}

    create_resp = _check(requests.post(
        f"{GRAPH_BASE}/{user_id}/threads", data=data, timeout=30,
    ), "container create")
    creation_id = create_resp.json()["id"]

    time.sleep(5)

    publish_resp = _check(requests.post(
        f"{GRAPH_BASE}/{user_id}/threads_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    ), "publish")
    return publish_resp.json()["id"]


def post_to_instagram(access_token, ig_user_id, image_url, caption):
    """Instagramは画像必須（テキストのみ投稿不可）。2段階publish。"""
    create_resp = _check(requests.post(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
        timeout=60,
    ), "IG container create")
    creation_id = create_resp.json()["id"]

    time.sleep(6)  # コンテナ生成の処理待ち

    publish_resp = _check(requests.post(
        f"{IG_GRAPH_BASE}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=60,
    ), "IG publish")
    return publish_resp.json()["id"]


def main():
    if not INDEX_HTML.exists():
        print(f"[ERROR] {INDEX_HTML} が見つかりません")
        sys.exit(1)

    events = _parse_events()  # favid -> category
    listed_count = len(events)
    general_count = sum(1 for c in events.values() if c == "一般")
    junior_count = sum(1 for c in events.values() if c == "ジュニア")
    current_ids = set(events.keys())
    prev_ids = _load_prev_ids()

    if prev_ids is None:
        print("初回実行のため差分なし。スナップショットのみ保存し、投稿は行いません。")
        _save_snapshot(current_ids)
        return

    new_count = len(current_ids - prev_ids)
    print(f"新着{new_count}件・掲載{listed_count}件（一般{general_count}/ジュニア{junior_count}）を検出。")

    threads_token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    ig_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not threads_token and not ig_token:
        print("[ERROR] Threads/Instagram どちらのトークンも設定されていません")
        sys.exit(1)

    # カード画像を生成 → コミット/push → SHA固定の公開URLを取得
    now = datetime.now(JST)
    date_str = now.strftime("%Y.%-m.%-d") if os.name != "nt" else now.strftime("%Y.%#m.%#d")
    day_index = now.timetuple().tm_yday  # 年間通算日→モチーフ/配色を日替わりに
    image_url = None
    try:
        sns_image.generate(IMAGE_FILE, new_count, general_count, junior_count,
                           date_str, day_index)
        sha, rel = commit_and_push_image(IMAGE_FILE)
        image_url = _image_url(sha, rel)
        print(f"画像URL: {image_url}")
    except Exception as e:
        print(f"[WARN] 画像生成/公開に失敗。Threadsはテキストのみ、Instagramはスキップします: {e}")

    results = {}  # platform -> bool

    # ── Threads（画像なしでもテキスト投稿可）──
    if threads_token:
        try:
            text = build_post_text(new_count, general_count, junior_count, TAGS_THREADS)
            user_id = _get_threads_user_id(threads_token)
            tid = post_to_threads(threads_token, user_id, text, image_url)
            print(f"[Threads] 投稿成功: thread_id={tid}")
            results["Threads"] = True
        except Exception as e:
            print(f"[Threads][ERROR] 投稿失敗: {e}")
            results["Threads"] = False

    # ── Instagram（画像必須）──
    if ig_token:
        if not image_url:
            print("[Instagram][ERROR] 画像URLが無いため投稿できません（Instagramは画像必須）")
            results["Instagram"] = False
        else:
            try:
                caption = build_post_text(new_count, general_count, junior_count, TAGS_INSTAGRAM)
                mid = post_to_instagram(ig_token, IG_USER_ID, image_url, caption)
                print(f"[Instagram] 投稿成功: media_id={mid}")
                results["Instagram"] = True
            except Exception as e:
                print(f"[Instagram][ERROR] 投稿失敗: {e}")
                results["Instagram"] = False

    # どこかに1つでも投稿できたらスナップショットを進める（同じ新着の二重通知を防ぐ）
    if any(results.values()):
        _save_snapshot(current_ids)
        commit_and_push_snapshot()

    print(f"結果: {results}")
    if not results or not all(results.values()):
        sys.exit(1)  # 1つでも失敗したらActionsを赤くして気づけるように


if __name__ == "__main__":
    main()
