# -*- coding: utf-8 -*-
"""
sns_image.py - 投稿用のカード画像をプログラムで生成する（著作権フリー）。

緑背景にテニスボールの絵と、タイトル・新着件数・掲載件数・日付を描画した
1080x1080 のJPEG画像を作る。毎回内容（件数・日付）が変わる。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# GitHub Actions (ubuntu) で fonts-noto-cjk を入れると置かれる候補パス
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    # Windows（ローカル動作確認用）
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
]

SIZE = 1080
BG = (27, 94, 32)        # 深い緑
CARD = (255, 255, 255)
ACCENT = (46, 125, 50)   # 緑
BALL = (208, 227, 51)    # テニスボールの黄緑
INK = (33, 33, 33)
SUB = (100, 100, 100)


def _find_font_path():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError(
        "日本語フォントが見つかりません。ubuntuなら `fonts-noto-cjk` を入れてください。"
    )


def _font(path, size):
    # .ttc はコレクションなので index=0 を指定
    return ImageFont.truetype(path, size, index=0)


def _center_text(draw, cx, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def _draw_tennis_ball(draw, cx, cy, r):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BALL)
    # ボールの白いカーブ線（左右に2本）を弧で表現
    inset = int(r * 0.7)
    draw.arc([cx - r - inset, cy - r, cx - r + inset, cy + r],
             start=300, end=60, fill=CARD, width=max(4, r // 12))
    draw.arc([cx + r - inset, cy - r, cx + r + inset, cy + r],
             start=120, end=240, fill=CARD, width=max(4, r // 12))


def generate(out_path, new_count, listed_count, date_str):
    font_path = _find_font_path()
    img = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(img)

    # 内側の白カード（角丸）
    margin = 60
    d.rounded_rectangle([margin, margin, SIZE - margin, SIZE - margin],
                        radius=48, fill=CARD)

    cx = SIZE // 2

    # テニスボール
    _draw_tennis_ball(d, cx, 260, 90)

    f_title = _font(font_path, 64)
    f_big = _font(font_path, 150)
    f_mid = _font(font_path, 56)
    f_label = _font(font_path, 44)
    f_date = _font(font_path, 40)

    _center_text(d, cx, 390, "福岡テニス大会情報", f_title, ACCENT)

    # 新着件数（大きく）
    _center_text(d, cx, 500, "新着", f_label, SUB)
    _center_text(d, cx, 540, f"{new_count}件", f_big, INK)

    # 掲載件数
    _center_text(d, cx, 740, f"現在の掲載 {listed_count}件", f_mid, ACCENT)

    # 日付
    _center_text(d, cx, 850, date_str, f_date, SUB)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=90)
    return out_path
