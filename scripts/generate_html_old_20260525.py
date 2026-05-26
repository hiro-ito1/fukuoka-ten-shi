"""
福岡テニス大会情報 - WEB公開用HTML生成スクリプト
v1.1: 本番データ直接読み込み版

入力: DATA/events_approved.json (Single Source of Truth)
出力: docs/index.html (GitHub Pages用)

機能:
- 確定済みデータを読み込み
- 月別・主催者別にグループ化
- カレンダー形式でHTML生成
- レスポンシブデザイン（スマホ対応）

修正内容:
- data_file のパスを修正（本番データを直接読み込む）
- Single Source of Truth の原則に準拠
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from collections import defaultdict


class HTMLGenerator:
    """HTML生成クラス"""
    
    def __init__(self, data_file: str, output_dir: str):
        self.data_file = Path(data_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def load_data(self) -> List[Dict]:
        """events_approved.json を読み込み"""
        if not self.data_file.exists():
            print(f"⚠️  データファイルが見つかりません: {self.data_file}")
            return []
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 募集中のみを抽出（結果は除外）
        events = [e for e in data if e.get('event_status') == '募集中']
        
        # 開催日でソート
        events.sort(key=lambda x: x.get('event_date', ''))
        
        print(f"📊 読み込み完了: {len(events)}件（募集中のみ）")
        
        return events
    
    def group_by_month(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """月別にグループ化"""
        grouped = defaultdict(list)
        
        for event in events:
            date_str = event.get('event_date', '')
            if not date_str:
                continue
            
            # YYYY/MM/DD(曜) から YYYY年MM月 を抽出
            try:
                year_month = date_str[:7]  # "2026/06"
                year, month = year_month.split('/')
                key = f"{year}年{int(month):02d}月"
                grouped[key].append(event)
            except:
                continue
        
        return dict(grouped)
    
    def generate_html(self):
        """HTMLを生成"""
        events = self.load_data()
        
        if not events:
            print("📋 公開可能なデータがありません")
            return
        
        grouped = self.group_by_month(events)
        
        # HTML生成
        html = self._generate_html_content(events, grouped)
        
        # 出力
        output_file = self.output_dir / "index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ HTML生成完了: {output_file}")
        print(f"📊 公開件数: {len(events)}件")
        print(f"📅 対象月: {len(grouped)}ヶ月")
        
        # 月別の内訳を表示
        for month, month_events in sorted(grouped.items()):
            print(f"   - {month}: {len(month_events)}件")
    
    def _generate_html_content(self, events: List[Dict], grouped: Dict[str, List[Dict]]) -> str:
        """HTML本体を生成"""
        
        # 統計情報
        total = len(events)
        general = len([e for e in events if e.get('category') == '一般'])
        junior = len([e for e in events if e.get('category') == 'ジュニア'])
        
        # 更新日時
        now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        
        # HTMLテンプレート
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="福岡エリアのテニス大会情報を掲載しています。筑紫野・糸島・福岡市内のテニストーナメント情報をチェック！">
    <title>福岡＋αテニス試合情報 | Fukuoka Tennis Tournaments</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- ヘッダー -->
    <header class="header">
        <div class="container">
            <h1 class="site-title">🎾 福岡＋αテニス試合情報</h1>
            <p class="site-subtitle">Fukuoka Tennis Tournaments</p>
        </div>
    </header>

    <!-- メインコンテンツ -->
    <main class="main">
        <div class="container">
            
            <!-- 統計情報 -->
            <section class="stats">
                <div class="stat-card">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">募集中の大会</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{general}</div>
                    <div class="stat-label">一般大会</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{junior}</div>
                    <div class="stat-label">ジュニア大会</div>
                </div>
            </section>

            <!-- フィルター -->
            <section class="filter">
                <button class="filter-btn active" data-filter="all">すべて</button>
                <button class="filter-btn" data-filter="一般">一般</button>
                <button class="filter-btn" data-filter="ジュニア">ジュニア</button>
            </section>

            <!-- 大会リスト -->
            <section class="events">
"""
        
        # 月別に大会カードを生成
        for month, month_events in sorted(grouped.items()):
            html += f"""
                <div class="month-section">
                    <h2 class="month-title">📅 {month}</h2>
                    <div class="event-grid">
"""
            
            for event in month_events:
                card = self._generate_event_card(event)
                html += card
            
            html += """
                    </div>
                </div>
"""
        
        # フッター
        html += f"""
            </section>
        </div>
    </main>

    <!-- フッター -->
    <footer class="footer">
        <div class="container">
            <p class="update-time">最終更新: {now}</p>
            <p class="copyright">&copy; 2026 福岡＋αテニス試合情報</p>
            <p class="note">※ 大会情報は各主催団体の公式サイトをご確認ください</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>
"""
        
        return html
    
    def _generate_event_card(self, event: Dict) -> str:
        """イベントカードを生成"""
        
        title = event.get('title', '大会名未定')
        date = event.get('event_date', '')
        category = event.get('category', '一般')
        organizer = event.get('organizer', '')
        event_type = event.get('event_type', '-')
        gender = event.get('gender', '-')
        level = event.get('level', '-')
        detail_url = event.get('detail_url', '') or event.get('source_url', '')
        
        # カテゴリバッジの色
        category_class = 'general' if category == '一般' else 'junior'
        
        card = f"""
                        <div class="event-card" data-category="{category}">
                            <div class="card-header">
                                <span class="category-badge {category_class}">{category}</span>
                                <span class="event-date">{date}</span>
                            </div>
                            <h3 class="event-title">{title}</h3>
                            <div class="event-details">
                                <p><strong>主催:</strong> {organizer}</p>
                                <p><strong>種目:</strong> {event_type} | <strong>性別:</strong> {gender}</p>
                                <p><strong>レベル:</strong> {level}</p>
                            </div>
"""
        
        if detail_url:
            card += f"""
                            <a href="{detail_url}" class="detail-link" target="_blank" rel="noopener">
                                詳細を見る →
                            </a>
"""
        
        card += """
                        </div>
"""
        
        return card


def main():
    """メイン処理"""
    
    import os
    from pathlib import Path
    
    # スクリプトの場所を基準にルートディレクトリを特定
    script_dir = Path(__file__).parent
    
    # 修正: 本番データの場所（Single Source of Truth）
    # fukuoka-ten-shi/scripts/generate_html.py から見て
    # ten-shi/DATA/events_approved.json へのパス
    
    project_root = script_dir.parent  # fukuoka-ten-shi
    ten_shi_root = project_root.parent  # ten-shi
    
    data_file = ten_shi_root / "DATA" / "events_approved.json"
    output_dir = project_root / "docs"
    
    print("=" * 60)
    print("🎾 福岡＋αテニス試合情報 - HTML生成")
    print("=" * 60)
    print(f"📂 データソース: {data_file}")
    print(f"📂 出力先: {output_dir}")
    print("-" * 60)
    
    # データファイルの存在確認
    if not data_file.exists():
        print(f"❌ エラー: データファイルが見つかりません")
        print(f"   期待されるパス: {data_file}")
        print(f"   現在の作業ディレクトリ: {Path.cwd()}")
        return
    
    # HTML生成
    generator = HTMLGenerator(str(data_file), str(output_dir))
    generator.generate_html()
    
    print("=" * 60)
    print("✅ 処理完了")
    print("=" * 60)


if __name__ == "__main__":
    main()