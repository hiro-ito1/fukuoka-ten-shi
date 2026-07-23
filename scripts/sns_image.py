# -*- coding: utf-8 -*-
"""
sns_image.py - 投稿用のカード画像をプログラムで生成する（著作権フリー）。

1080x1080 のJPEGカード。内容（掲載件数・新着件数・日付）は毎回変わり、
さらに「モチーフ（テニスボール/ラケット/トロフィー/表彰状/紙吹雪/太陽/月）」と
配色を日替わりで切り替えて見た目に変化を出す。

デザイン方針:
  ・背景は縦グラデーション＋カードにソフトシャドウで奥行きを出す
  ・「現在の掲載」は淡いアクセント地のスタッツパネルにまとめ、数字だけ大きくアクセント色
  ・「新着◯件」（前回投稿からの差分）はピル型バッジで小さめ（0件でもカッコ悪く見えないように）
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
]

SIZE = 1080
CARD = (255, 255, 255)
INK = (33, 37, 41)
SUB = (130, 133, 138)
MARGIN = 56
RADIUS = 52


# ── フォント ─────────────────────────────────────────────
def _find_font_path():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    raise RuntimeError("日本語フォントが見つかりません。ubuntuなら fonts-noto-cjk を導入。")


def _font(path, size):
    return ImageFont.truetype(path, size, index=0)


# ── 色ユーティリティ ─────────────────────────────────────
def _mix(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _lighten(c, f):
    return tuple(int(x + (255 - x) * f) for x in c)


def _darken(c, f):
    return tuple(int(x * (1 - f)) for x in c)


# ── テキスト配置 ─────────────────────────────────────────
def _center(draw, cx, y, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (bbox[2] - bbox[0]) / 2, y), text, font=font, fill=fill)


def _center_segments(draw, cx, baseline_y, segments):
    """複数フォント・色のテキストを1行に並べ、中央寄せ＋下端（ベースライン）揃えで描画。
    segments: [(text, font, fill), ...]"""
    measured = []
    total_w = 0
    for text, font, fill in segments:
        b = draw.textbbox((0, 0), text, font=font)
        measured.append((text, font, fill, b, b[2] - b[0]))
        total_w += b[2] - b[0]
    x = cx - total_w / 2
    for text, font, fill, b, w in measured:
        draw.text((x - b[0], baseline_y - b[3]), text, font=font, fill=fill)
        x += w


def _vertical_gradient(w, h, c_top, c_bot):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=_mix(c_top, c_bot, t))
    return img


# ── モチーフ描画 ─────────────────────────────────────────
def m_tennis(d, cx, cy, r, accent, seed, card_bg):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(208, 227, 51))
    inset = int(r * 0.7)
    w = max(4, r // 12)
    d.arc([cx - r - inset, cy - r, cx - r + inset, cy + r], 300, 60, fill=CARD, width=w)
    d.arc([cx + r - inset, cy - r, cx + r + inset, cy + r], 120, 240, fill=CARD, width=w)


def m_racket(d, cx, cy, r, accent, seed, card_bg):
    hw, hh = int(r * 0.8), int(r * 1.0)
    top = cy - r
    head = [cx - hw, top, cx + hw, top + 2 * hh]
    d.ellipse(head, outline=accent, width=max(7, r // 8))
    for i in range(1, 5):
        x = cx - hw + 2 * hw * i / 5
        d.line([x, top + 12, x, top + 2 * hh - 12], fill=(205, 205, 205), width=2)
        y = top + 12 + (2 * hh - 24) * i / 5
        d.line([cx - hw + 12, y, cx + hw - 12, y], fill=(205, 205, 205), width=2)
    d.line([cx, top + 2 * hh - 6, cx, cy + r], fill=accent, width=max(9, r // 6))


def m_trophy(d, cx, cy, r, accent, seed, card_bg):
    g = accent
    d.rectangle([cx - r * 0.8, cy - r * 0.9, cx + r * 0.8, cy - r * 0.7], fill=g)  # rim
    d.rectangle([cx - r * 0.7, cy - r * 0.7, cx + r * 0.7, cy], fill=g)            # cup body
    d.pieslice([cx - r * 0.7, cy - r * 0.3, cx + r * 0.7, cy + r * 0.5], 0, 180, fill=g)
    d.arc([cx - r * 1.15, cy - r * 0.85, cx - r * 0.45, cy - r * 0.15], 90, 270, fill=g, width=max(7, r // 10))
    d.arc([cx + r * 0.45, cy - r * 0.85, cx + r * 1.15, cy - r * 0.15], 270, 90, fill=g, width=max(7, r // 10))
    d.rectangle([cx - r * 0.12, cy + r * 0.35, cx + r * 0.12, cy + r * 0.65], fill=g)  # stem
    d.rectangle([cx - r * 0.5, cy + r * 0.65, cx + r * 0.5, cy + r * 0.85], fill=g)    # base


def m_certificate(d, cx, cy, r, accent, seed, card_bg):
    w, h = int(r * 1.15), int(r * 1.35)
    d.rounded_rectangle([cx - w, cy - h, cx + w, cy + h], radius=10,
                        fill=(255, 252, 240), outline=accent, width=5)
    for i in range(4):
        yy = cy - h + 34 + i * 26
        d.line([cx - w + 24, yy, cx + w - 24, yy], fill=(190, 190, 190), width=5)
    sx, sy = cx + w - 22, cy + h - 22
    d.polygon([(sx - 10, sy), (sx - 22, sy + 40), (sx + 2, sy + 28)], fill=accent)
    d.polygon([(sx + 10, sy), (sx + 22, sy + 40), (sx - 2, sy + 28)], fill=accent)
    d.ellipse([sx - 24, sy - 24, sx + 24, sy + 24], fill=accent)


def m_confetti(d, cx, cy, r, accent, seed, card_bg):
    rnd = random.Random(seed)
    cols = [(229, 57, 53), (255, 193, 7), (30, 136, 229),
            (67, 160, 71), (142, 36, 170), (255, 112, 67)]
    for _ in range(46):
        px = cx + rnd.randint(-r, r)
        py = cy + rnd.randint(-r, r)
        if (px - cx) ** 2 + (py - cy) ** 2 > (r * 1.15) ** 2:
            continue
        c = rnd.choice(cols)
        if rnd.random() < 0.5:
            d.rectangle([px, py, px + 12, py + 18], fill=c)
        else:
            d.ellipse([px, py, px + 13, py + 13], fill=c)


def m_sun(d, cx, cy, r, accent, seed, card_bg):
    for i in range(12):
        a = math.radians(i * 30)
        d.line([cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78,
                cx + math.cos(a) * r * 1.18, cy + math.sin(a) * r * 1.18],
               fill=accent, width=max(6, r // 12))
    d.ellipse([cx - r * 0.6, cy - r * 0.6, cx + r * 0.6, cy + r * 0.6], fill=accent)


def m_moon(d, cx, cy, r, accent, seed, card_bg):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent)
    off = int(r * 0.55)
    d.ellipse([cx - r + off, cy - r * 1.05, cx + r + off, cy + r * 0.95], fill=card_bg)
    for (sx, sy, sr) in [(cx + r * 0.9, cy - r * 0.7, 5), (cx + r * 1.1, cy + r * 0.2, 4),
                         (cx + r * 0.6, cy + r * 0.9, 4)]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=accent)


# テーマ = (外枠背景色, アクセント色, モチーフ)
THEMES = [
    ((27, 94, 32),   (46, 125, 50),  m_tennis),      # 緑・テニスボール
    ((21, 60, 110),  (30, 100, 190), m_racket),      # 紺・ラケット
    ((124, 92, 12),  (200, 150, 20), m_trophy),      # 金茶・トロフィー
    ((15, 100, 100), (20, 150, 150), m_certificate), # 青緑・表彰状
    ((90, 30, 120),  (142, 60, 175), m_confetti),    # 紫・紙吹雪
    ((200, 110, 20), (240, 150, 30), m_sun),         # 橙・太陽
    ((40, 45, 95),   (95, 105, 190), m_moon),        # 藍・月
]


def _pill(d, cx, cy, text, font, fill_rgb, text_rgb, pad_x=40, pad_y=18):
    """中央 (cx, cy) を中心にピル型（角丸フル）バッジを描く。"""
    b = d.textbbox((0, 0), text, font=font)
    tw, th = b[2] - b[0], b[3] - b[1]
    w, h = tw + pad_x * 2, th + pad_y * 2
    x0, y0 = cx - w / 2, cy - h / 2
    d.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=h / 2, fill=fill_rgb)
    d.text((cx - tw / 2 - b[0], cy - th / 2 - b[1]), text, font=font, fill=text_rgb)


def generate(out_path, new_count, general_count, junior_count, date_str, day_index=0):
    font_path = _find_font_path()
    bg, accent, motif = THEMES[day_index % len(THEMES)]

    # 背景（縦グラデーション）＋カードのソフトシャドウ
    base = _vertical_gradient(SIZE, SIZE, _lighten(bg, 0.16), _darken(bg, 0.30)).convert("RGBA")
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [MARGIN, MARGIN + 18, SIZE - MARGIN, SIZE - MARGIN + 18], radius=RADIUS, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(shadow)

    img = base
    d = ImageDraw.Draw(img)

    # 白カード
    d.rounded_rectangle([MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN], radius=RADIUS, fill=CARD)

    cx = SIZE // 2

    f_title = _font(font_path, 60)
    f_label = _font(font_path, 38)
    f_row = _font(font_path, 54)
    f_num = _font(font_path, 88)
    f_unit = _font(font_path, 40)
    f_badge = _font(font_path, 40)
    f_date = _font(font_path, 36)

    # モチーフ（日替わり）
    motif(d, cx, 208, 74, accent, day_index, CARD)

    # タイトル
    _center(d, cx, 300, "福岡テニス大会情報", f_title, accent)

    # タイトル下のアクセント区切り線
    d.rounded_rectangle([cx - 78, 392, cx + 78, 400], radius=4, fill=accent)

    # 現在の掲載（淡いアクセント地のスタッツパネル・数字だけ大きくアクセント色）
    tint = _mix(CARD, accent, 0.10)
    d.rounded_rectangle([146, 436, SIZE - 146, 732], radius=34, fill=tint)
    _center(d, cx, 456, "現在の掲載", f_label, SUB)
    _center_segments(d, cx, 596, [
        ("一般大会  ", f_row, INK), (f"{general_count}", f_num, accent), (" 件", f_unit, INK),
    ])
    _center_segments(d, cx, 700, [
        ("ジュニア大会  ", f_row, INK), (f"{junior_count}", f_num, accent), (" 件", f_unit, INK),
    ])

    # 新着（前回投稿からの差分）＝ピル型バッジ
    _pill(d, cx, 800, f"新着 {new_count}件", f_badge, accent, CARD)

    # 日付
    _center(d, cx, 862, date_str, f_date, SUB)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, "JPEG", quality=92)
    return out_path
