"""
筑紫野ローンテニスクラブ専用パーサー v11.0
URL: https://chikushinotennis.web.fc2.com/

【v10.3 → v11.0 の変更点】
- _extract_event_details() 関数を追加
- タイトルから種目・性別・年齢を抽出
- notes フィールドに補足情報を格納

【v10.3の戦略】
1. 募集中を最優先（古い結果を除外）
2. タイトルの意味付け（大会名をセット）
3. タイムアウト対策（短縮 + エラー処理強化）
4. 重複排除（日付+タイトルでユニーク化）
"""
import re
from datetime import datetime
from typing import List, Set, Tuple
from urllib.parse import urljoin
from playwright.sync_api import Page
from parsers.base_parser import BaseParser
from schema import TournamentEvent


class ChikushinoParser(BaseParser):
    """筑紫野ローンTC v11.0: 種目・性別分離版"""
    
    def __init__(self):
        super().__init__(
            organizer_name="筑紫野ローンTC",
            source_url="https://chikushinotennis.web.fc2.com/"
        )
        
        # 重要子ページリスト
        self.dive_targets = [
            "jr_shiai.html",    # ジュニア
            "ebisucup.html",    # 一般
            "inter.html"        # ステップアップ
        ]
        
        # 除外キーワード（拡張版）
        self.exclude_keywords = [
            'コーチ', 'スクール', '案内', '活躍', '紹介', 
            'レッスン', 'お休み', 'アクセス', 'リンク'
        ]
        
        # 結果キーワード（これらを含むものは古いデータとして除外）
        self.result_keywords = [
            '結果', '入賞', '優勝', '準優勝', 'リザルト'
        ]
    
    def _extract_event_details(self, title: str) -> Tuple[str, str, str, str]:
        """
        タイトルから種目・性別・レベル・補足を抽出
        
        Examples:
            "ゑびすカップ 女子ダブルス" → ("ダブルス", "女子", "", "")
            "ジュニアシングルス 小学生" → ("シングルス", "", "", "小学生, ジュニア")
            "ステップアップトーナメント" → ("シングルス", "", "", "")
        
        Returns:
            (event_type, gender, level, notes)
        """
        event_type = ""
        gender = ""
        level = ""
        notes_list = []
        
        # 性別判定
        if "女子" in title:
            gender = "女子"
        elif "男子" in title:
            gender = "男子"
        elif "混合" in title or "ミックス" in title:
            gender = "混合"
        
        # 種目判定
        if "ダブルス" in title:
            event_type = "ダブルス"
        elif "シングルス" in title:
            event_type = "シングルス"
        elif "団体" in title:
            event_type = "団体"
        else:
            # デフォルトはシングルス
            event_type = "シングルス"
        
        # レベル判定
        if "オープン" in title or "OP" in title:
            level = "OP"
        elif "初級" in title:
            level = "初級"
        elif "中級" in title:
            level = "中級"
        elif "上級" in title:
            level = "上級"
        
        # 補足情報
        if "ジュニア" in title:
            notes_list.append("ジュニア")
        if "小学生" in title:
            notes_list.append("小学生")
        if "中学生" in title:
            notes_list.append("中学生")
        if "高校生" in title:
            notes_list.append("高校生")
        if "ステップアップ" in title:
            notes_list.append("ステップアップ")
        
        # 年齢制限
        age_match = re.search(r'(\d+)歳', title)
        if age_match:
            notes_list.append(f"{age_match.group(1)}歳")
        
        notes = ", ".join(notes_list) if notes_list else ""
        
        return (event_type, gender, level, notes)
    
    def parse(self, page: Page) -> List[TournamentEvent]:
        """
        v11.0: 種目・性別分離 + 精密フィルタリング
        """
        all_events = []
        now = datetime.now()
        
        self.logger.info(f"[{self.organizer_name}] v11.0 種目・性別分離モード起動")
        
        # 各子ページを巡回
        for target in self.dive_targets:
            target_url = urljoin(self.source_url, target)
            
            try:
                self.logger.info(f"  → 攻略中: {target}")
                
                # ページ遷移（タイムアウト: 20秒、失敗時は次へ）
                page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)  # 短縮
                
                # 子ページから抽出
                events = self._extract_from_page(page, target, now)
                all_events.extend(events)
                
                self.logger.info(f"    → 取得: {len(events)}件")
            
            except Exception as e:
                self.logger.warning(f"    ! {target} スキップ: {str(e)}")
                continue
        
        # 重複除去（日付+タイトルでユニーク化）
        unique_events = self._remove_duplicates_by_date_title(all_events)
        
        self.logger.info(f"[{self.organizer_name}] 最終結果: {len(unique_events)}件")
        
        return unique_events
    
    def _extract_from_page(self, page: Page, filename: str, now: datetime) -> List[TournamentEvent]:
        """
        ページからイベント抽出（種目・性別分離版）
        """
        extracted = []
        
        try:
            # カテゴリ判定
            category = "ジュニア" if "jr" in filename.lower() else "一般"
            
            # body要素を取得（None チェック）
            body = page.query_selector("body")
            if not body:
                self.logger.warning(f"      ! body要素が見つかりません")
                return []
            
            content = body.inner_text()
            if not content or not content.strip():
                self.logger.warning(f"      ! コンテンツが空です")
                return []
            
            lines = content.split('\n')
            
            # 現在の大会タイトル（階層構造を保持）
            current_main_title = "大会情報"
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # 空行 or 除外キーワード
                if not line or self._should_exclude(line):
                    continue
                
                # 日付（M/D）がある行を特定
                date_match = re.search(r'(\d{1,2})/(\d{1,2})', line)
                
                if date_match:
                    m, d = map(int, date_match.groups())
                    
                    # 過去データ除外（2ヶ月以上前は除外）
                    if self._is_old_date(m, d, now):
                        self.logger.debug(f"      古いデータ除外: {m}/{d}")
                        continue
                    
                    # タイトル決定（大会名 + 行内容）
                    title = self._build_title(current_main_title, line)
                    
                    # 結果キーワードチェック
                    if any(kw in title for kw in self.result_keywords):
                        self.logger.debug(f"      結果データ除外: {title}")
                        continue
                    
                    # ==========================================
                    # 【v11.0 修正】種目・性別・補足を抽出
                    # ==========================================
                    event_type, gender, level, notes = self._extract_event_details(title)
                    
                    # イベント生成
                    event = self.process_event_data(
                        title=title,
                        date_str=f"{m}/{d}",  # 年は base_parser が自動判定
                        category=category,
                        event_type=event_type,
                        level=level,
                        index=len(extracted),
                        detail_url=page.url
                    )
                    
                    if event:
                        event.gender = gender
                        event.notes = notes
                        extracted.append(event)
                        self.logger.debug(f"      抽出: {title} (種目={event_type}, 性別={gender}) - {m}/{d}")
                
                else:
                    # 日付がない行で、大会名っぽいものを保存
                    if self._is_main_title(line):
                        current_main_title = line
                        self.logger.debug(f"      大会名認識: {line}")
        
        except Exception as e:
            self.logger.error(f"ページ抽出エラー: {str(e)}")
        
        return extracted
    
    def _should_exclude(self, text: str) -> bool:
        """除外フィルター"""
        if not text:
            return True
        
        for keyword in self.exclude_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _is_old_date(self, month: int, day: int, now: datetime) -> bool:
        """
        過去データ判定
        
        現在月より2ヶ月以上前のものは除外
        例: 現在が5月 → 3月以前は除外
        """
        current_month = now.month
        
        # 2ヶ月以上前かチェック
        if month < current_month - 1:
            return True
        
        return False
    
    def _is_main_title(self, line: str) -> bool:
        """
        大会名っぽい行かどうか判定
        
        条件:
        - 長さが5〜30文字
        - 「大会」「カップ」「トーナメント」を含む
        """
        if not line or len(line) < 5 or len(line) > 30:
            return False
        
        title_keywords = ['大会', 'カップ', 'トーナメント', '選手権', 'テニス']
        
        return any(kw in line for kw in title_keywords)
    
    def _build_title(self, main_title: str, line: str) -> str:
        """
        タイトルを構築
        
        フォーマット: [大会名] + [行内容から日付を除外したもの]
        """
        # 行から日付を除去
        cleaned = re.sub(r'\d{1,2}/\d{1,2}', '', line)
        cleaned = re.sub(r'\([月火水木金土日祝]+\)', '', cleaned)
        cleaned = self.clean_text(cleaned)
        
        # 空になったら大会名のみ
        if not cleaned or len(cleaned) < 3:
            return main_title
        
        # 大会名 + 詳細
        return f"{main_title} {cleaned}"[:60]  # 60文字に制限
    
    def _remove_duplicates_by_date_title(self, events: List[TournamentEvent]) -> List[TournamentEvent]:
        """
        重複除去（日付+タイトルでユニーク化）
        """
        unique_events = []
        seen: Set[str] = set()
        
        for event in events:
            # 日付とタイトルで一意キーを作成
            key = f"{event.event_date}|{event.title}"
            
            if key not in seen:
                unique_events.append(event)
                seen.add(key)
        
        if len(events) > len(unique_events):
            self.logger.info(f"重複除去: {len(events)}件 → {len(unique_events)}件")
        
        return unique_events