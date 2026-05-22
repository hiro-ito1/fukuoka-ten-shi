# 🚀 fukuoka-ten-shi デプロイ手順

---

## 📋 前提条件

- GitHubアカウント
- Gitコマンドが使える環境
- ダウンロードした `fukuoka-ten-shi` フォルダ

---

## 🎯 手順

### **Step 1: GitHubで新規リポジトリ作成**

1. GitHubにログイン
2. 右上の `+` → `New repository`
3. **Repository name**: `fukuoka-ten-shi`
4. **Public** を選択
5. **Add a README file**: チェックしない（すでにある）
6. **Create repository** をクリック

---

### **Step 2: ローカルでGit初期化**

```bash
# fukuoka-ten-shi フォルダに移動
cd fukuoka-ten-shi

# Git初期化
git init

# ファイルをステージング
git add .

# 初回コミット
git commit -m "Initial commit: 福岡天使プロジェクト開始"

# ブランチ名を main に変更
git branch -M main

# リモートリポジトリを追加
git remote add origin https://github.com/hiro-ito1/fukuoka-ten-shi.git

# プッシュ
git push -u origin main
```

---

### **Step 3: GitHub Pages 設定**

1. GitHubのリポジトリページを開く
2. **Settings** タブをクリック
3. 左メニューから **Pages** を選択
4. **Source** セクションで以下を選択：
   - Branch: `main`
   - Folder: `/docs`
5. **Save** をクリック

数分待つと、公開URLが表示されます：
```
https://hiro-ito1.github.io/fukuoka-ten-shi/
```

---

### **Step 4: 公開確認**

上記URLにアクセスして、サイトが表示されることを確認。

---

## 🔄 データ更新手順

### **通常の更新**

```bash
# 1. data/events_approved.json を編集

# 2. HTML生成
python scripts/generate_html.py

# 3. 変更をコミット
git add .
git commit -m "Update: 大会情報更新"
git push
```

数分後にGitHub Pagesが自動更新されます。

---

## 🧪 ローカルテスト

プッシュ前に必ずローカルで確認：

```bash
# HTML生成
python scripts/generate_html.py

# ブラウザで開く
open docs/index.html

# または
cd docs
python -m http.server 8000
# http://localhost:8000 にアクセス
```

---

## ⚠️ トラブルシューティング

### ケース1: GitHub Pagesが404エラー

- Settings → Pages で設定を確認
- `/docs` フォルダが選択されているか確認
- 数分待ってから再度アクセス

### ケース2: HTMLが生成されない

```bash
# パスを確認
python scripts/generate_html.py

# エラーメッセージを確認
```

### ケース3: スタイルが反映されない

- `docs/style.css` が存在するか確認
- ブラウザのキャッシュをクリア（Ctrl+Shift+R）

---

## 📚 参考情報

- GitHub Pages公式ドキュメント: https://docs.github.com/ja/pages
- リポジトリURL: https://github.com/hiro-ito1/fukuoka-ten-shi
- 公開URL: https://hiro-ito1.github.io/fukuoka-ten-shi/

---

**作成日**: 2026年5月21日
