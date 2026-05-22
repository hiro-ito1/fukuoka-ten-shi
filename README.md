# 🎾 fukuoka-ten-shi

**福岡テニス試合情報 × 福岡天使**

福岡エリアのテニス大会情報を収集・公開するプロジェクト

---

## 🌐 公開サイト

**GitHub Pages**: https://hiro-ito1.github.io/fukuoka-ten-shi/

---

## 📋 プロジェクト概要

福岡市・筑紫野市・糸島市エリアのテニス大会情報を自動収集し、  
見やすいカレンダー形式で公開するシステムです。

### 主な機能
- 📅 月別カレンダー表示
- 🏷️ カテゴリフィルター（一般/ジュニア）
- 📱 レスポンシブデザイン（スマホ対応）
- 🔄 データ自動更新

---

## 📂 ディレクトリ構造

```
fukuoka-ten-shi/
├── docs/                       # GitHub Pages公開フォルダ
│   ├── index.html              # メインページ（自動生成）
│   ├── style.css               # スタイルシート
│   └── script.js               # フィルター機能
│
├── data/
│   └── events_approved.json    # 大会データ（承認済み）
│
├── scripts/
│   └── generate_html.py        # HTML生成スクリプト
│
└── README.md
```

---

## 🚀 使い方

### ローカルでHTMLを生成

```bash
# プロジェクトルートで実行
python scripts/generate_html.py
```

生成された `docs/index.html` をブラウザで開いて確認できます。

### データの更新

`data/events_approved.json` を編集後、HTML生成スクリプトを実行：

```bash
python scripts/generate_html.py
```

---

## 📊 データ形式

```json
[
  {
    "unique_id": "auto_筑紫野ロー_20260615_001",
    "title": "ゑびすカップ要項 次々回開催",
    "event_date": "2026/06/15(月)",
    "category": "一般",
    "event_status": "募集中",
    "organizer": "筑紫野ローンテニスクラブ",
    "event_type": "ダブルス",
    "gender": "男女混合",
    "level": "中級",
    "source_url": "https://chikushinotennis.web.fc2.com/",
    "detail_url": "https://chikushinotennis.web.fc2.com/ebisucup.html"
  }
]
```

---

## 🎨 デザイン

- **カラースキーム**: テニスコートの緑 × テニスボールの黄色
- **レスポンシブ**: スマホ・タブレット・PC対応
- **フィルター**: 一般/ジュニア切り替え

---

## 📝 ライセンス

MIT License

---

## 👤 作成者

hiro-ito1

---

**最終更新**: 2026年5月21日
