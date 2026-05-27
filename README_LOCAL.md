# 📋 fukuoka-ten-shi/local/ フォルダ

**作成日:** 2026-05-27  
**目的:** 理想のフロー実装（完全自動化）

---

## 🎯 **このフォルダの役割**

```
local/ = ローカル専用フォルダ

特徴:
✅ 主君のPCにのみ存在
✅ GitHub にアップロードされない（.gitignore で除外）
✅ 管理画面 + 自動デプロイスクリプトを格納
```

---

## 📂 **フォルダ構造**

```
local/
├── app.py                      # 管理画面（Streamlit）
├── generate_html_auto.py       # 自動デプロイ版 WEB生成
├── scraping_engine.py          # 収集エンジン
├── schema.py                   # データモデル
├── parsers/                    # パーサー群
│   ├── base_parser.py
│   ├── chikushino.py
│   ├── itoshima.py
│   └── jonan.py
└── data/                       # データストア
    ├── events_approved.json    # 承認済みデータ
    ├── events_pending.json     # 未承認データ
    └── targets.json            # 収集対象サイト
```

---

## 🚀 **使い方**

### 1. セットアップ（初回のみ）

```cmd
cd C:\Users\tenni\ten-shi\fukuoka-ten-shi
setup_local.bat
```

### 2. 管理画面の起動

```cmd
cd C:\Users\tenni\ten-shi\fukuoka-ten-shi\local
python -m streamlit run app.py
```

### 3. WEB生成 & 自動デプロイ

```cmd
cd C:\Users\tenni\ten-shi\fukuoka-ten-shi\local
python generate_html_auto.py
```

---

## 🎯 **理想のフロー**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【完全自動化】

① 管理画面で承認
   cd local
   python -m streamlit run app.py
   → 収集実行
   → 仕分け作業
   → 承認

② WEB生成 & 自動デプロイ
   python generate_html_auto.py
   ↓（自動）
   fukuoka-ten-shi/docs/ にコピー
   ↓（自動）
   GitHub に自動プッシュ
   ↓（自動）
   世界公開完了！

所要時間: 約3分
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ⚠️ **注意事項**

### GitHub にアップロードされないもの

```
local/ フォルダ全体
  ↓
.gitignore で除外済み
  ↓
主君のPCにのみ存在
  ↓
世界中の人は見られない（安全）
```

### データの同期

```
ACTIVE_CODE/DATA/ と local/data/ は別物

更新方法:
setup_local.bat を再実行
→ 最新データがコピーされる
```

---

## 🔧 **トラブルシューティング**

### Q: 管理画面が起動しない

```
A: Streamlit がインストールされているか確認

pip install streamlit
```

### Q: generate_html_auto.py でエラー

```
A: data/events_approved.json があるか確認

dir local\data
```

### Q: GitHub デプロイに失敗

```
A: deploy.py が正しく動作するか確認

cd C:\Users\tenni\ten-shi\fukuoka-ten-shi
python deploy.py
```

---

## 📚 **関連ドキュメント**

- **README.md** - プロジェクト全体の説明
- **PROJECT_OS.md** - システム定義書
- **KNOWLEDGE_BASE/** - 成功・失敗パターン

---

**主君専用の完全本番環境** 🎾
