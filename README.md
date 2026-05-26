# 🎾 福岡テニス試合情報 × 福岡大使

**福岡エリアのテニス大会情報を収集・公開するプロジェクト**

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://hiro-ito1.github.io/fukuoka-ten-shi/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌐 公開サイト

**👉 https://hiro-ito1.github.io/fukuoka-ten-shi/**

福岡エリアのテニス大会情報を一覧で確認できます。

---

## 📋 収集対象サイト

現在、以下の4つの団体から大会情報を自動収集しています：

1. **筑紫野ローンテニスクラブ**
2. **糸島市テニス協会**
3. **城南テニスクラブ**
4. **ITSテニスクラブ**

---

## 🎯 プロジェクトの目的

福岡エリアのテニス愛好家のために、
各団体の大会情報を一箇所に集約し、
わかりやすく表示することを目指しています。

---

## 🚀 機能

- ✅ 複数サイトからの自動収集
- ✅ 日付順・月別表示
- ✅ カテゴリフィルター（一般/ジュニア）
- ✅ レスポンシブデザイン（PC・スマホ対応）
- ✅ GitHub Pages で公開

---

## 🛠️ 技術スタック

### バックエンド（データ収集）
- Python 3.8+
- Playwright（ブラウザ自動化）
- Pydantic（データバリデーション）

### フロントエンド（WEB表示）
- HTML5 / CSS3 / JavaScript
- GitHub Pages

---

## 📂 プロジェクト構造

```
fukuoka-ten-shi/
├── docs/               # WEB公開（GitHub Pages）
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── scripts/            # 生成スクリプト
│   └── generate_html.py
│
├── parsers/            # パーサー（参考用）
│   ├── base_parser.py
│   ├── chikushino.py
│   ├── itoshima.py
│   └── jonan.py
│
├── data/               # サンプルデータ
│   └── targets.json
│
├── .gitignore
├── README.md
├── requirements.txt
└── deploy.py           # 自動デプロイ
```

---

## 💻 ローカル環境でのセットアップ

### 1. リポジトリをクローン

```bash
git clone https://github.com/hiro-ito1/fukuoka-ten-shi.git
cd fukuoka-ten-shi
```

### 2. 仮想環境の作成（推奨）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. Playwright のセットアップ

```bash
playwright install chromium
```

---

## 🔄 データ更新フロー

```
1. ローカルで管理画面を操作（app.py）
   ↓
2. 大会情報を収集・承認
   ↓
3. generate_html.py で HTML 生成
   ↓
4. deploy.py で GitHub にプッシュ
   ↓
5. GitHub Pages が自動更新
```

---

## 📜 ライセンス

MIT License

---

## 👤 作成者

**hiro-ito1**

- GitHub: [@hiro-ito1](https://github.com/hiro-ito1)
- プロジェクト: [fukuoka-ten-shi](https://github.com/hiro-ito1/fukuoka-ten-shi)

---

## 🙏 謝辞

福岡エリアのテニス大会情報を公開していただいている
各団体様に感謝いたします。

---

## 📝 更新履歴

- **2026-05-25**: Phase 16 完成・GitHub統合
- **2026-05-21**: Phase 15 完成・WEB公開システム完成
- **2026-05-17**: Phase 1 開始・プロジェクト始動

---

**福岡エリアのテニス愛好家の皆様へ** 🎾

このプロジェクトが、
皆様のテニスライフに少しでも役立てば幸いです。

**一緒にテニスを楽しみましょう！** 🌟
