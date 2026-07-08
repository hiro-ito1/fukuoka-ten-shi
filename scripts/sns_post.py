# -*- coding: utf-8 -*-
"""
sns_post.py - GitHub Actionsから毎日20:30(JST)に呼び出され、Threadsへ自動投稿する。

公開済みの docs/index.html を解析して、新着大会（前回実行時からの data-favid 差分）と
現在の掲載件数を投稿文に含める。events_approved.json 等の非公開データは一切参照しない
（サイトに既に公開されている情報のみを使うため、GitHubへ同期する必要がない）。

新着0件でも必ず投稿する。

認証: 環境変数 THREADS_ACCESS_TOKEN（GitHub Secretsから注入）
状態: data/sns_snapshot.json（本リポジトリにコミットして次回実行に引き継ぐ）
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
INDEX_HTML = REPO_ROOT / "docs" / "index.html"
SNAPSHOT_FILE = REPO_ROOT / "data" / "sns_snapshot.json"

GRAPH_BASE = "https://graph.threads.net/v1.0"

GUIDANCE = (
    "・民間テニスクラブ・協会は無料掲載中！\n"
    "・ピックルボールは大会情報掲載を募集中（無料）\n"
    "詳細は別途確認\n\n"
    "#福岡テニス #ピックルボール"
)

CARD_RE = re.compile(
    r'<div class="event-card"[^>]*data-favid="([^"]+)"[^>]*>.*?'
    r'<h3 class="event-title">([^<]*)</h3>',
    re.DOTALL,
)


def _parse_events():
    """docs/index.html は主催アコーディオン表示のため同じ大会が複数回出現するので、
    data-favid で重複除去する（初出のタイトルを採用）。"""
    html = INDEX_HTML.read_text(encoding="utf-8")
    deduped = {}
    for favid, title in CARD_RE.findall(html):
        deduped.setdefault(favid, title.strip())
    return list(deduped.items())


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


def _truncate(title, limit=40):
    return title if len(title) <= limit else title[:limit] + "…"


def build_post_text(new_events, listed_count):
    new_count = len(new_events)
    lines = [
        f"【福岡テニス大会情報】新着{new_count}件追加しました！",
        f"現在の掲載件数: {listed_count}件",
    ]
    if new_events:
        lines.append("")
        for _favid, title in new_events[:10]:
            lines.append(f"・{_truncate(title)}")
        if new_count > 10:
            lines.append(f"他{new_count - 10}件")
    lines.append("")
    lines.append(GUIDANCE)
    return "\n".join(lines)


def _get_threads_user_id(access_token):
    resp = requests.get(
        f"{GRAPH_BASE}/me",
        params={"fields": "id,username", "access_token": access_token},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def post_to_threads(access_token, user_id, text):
    create_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/threads",
        data={"media_type": "TEXT", "text": text, "access_token": access_token},
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]

    time.sleep(5)

    publish_resp = requests.post(
        f"{GRAPH_BASE}/{user_id}/threads_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    return publish_resp.json()["id"]


def main():
    if not INDEX_HTML.exists():
        print(f"[ERROR] {INDEX_HTML} が見つかりません")
        sys.exit(1)

    events = _parse_events()
    listed_count = len(events)
    current_ids = {favid for favid, _title in events}
    prev_ids = _load_prev_ids()

    if prev_ids is None:
        print("初回実行のため差分なし。スナップショットのみ保存し、投稿は行いません。")
        _save_snapshot(current_ids)
        return

    new_events = [(favid, title) for favid, title in events if favid not in prev_ids]
    text = build_post_text(new_events, listed_count)

    print(f"新着{len(new_events)}件・掲載{listed_count}件を検出。Threadsへ投稿します。")
    print("-" * 40)
    print(text)
    print("-" * 40)

    access_token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not access_token:
        print("[ERROR] 環境変数 THREADS_ACCESS_TOKEN が設定されていません")
        sys.exit(1)

    user_id = _get_threads_user_id(access_token)
    thread_id = post_to_threads(access_token, user_id, text)
    print(f"投稿成功: thread_id={thread_id}")

    _save_snapshot(current_ids)  # 成功時のみスナップショットを進める


if __name__ == "__main__":
    main()
