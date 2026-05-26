"""
BaseParser - 全パーサーの共通基底クラス
v12.2: 1日猶予の法則実装版

【必須実装機能】
1. 日付抽出9パターン完全対応（和暦含む）
2. 日付形式: YYYY/MM/DD(曜) への正規化
3. ステータス判定（event_status: 募集中/結果）+ 1日猶予
4. カテゴリ判別（category: ジュニア/一般）
5. ID生成（auto_{主催者}_{YYYYMMDD}_{連番}）
6. 締切日抽出器（_extract_deadline）
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Optional
from abc import ABC, abstractmethod
from playwright.sync_api import Page

from schema import TournamentEvent


class BaseParser(ABC):
    """パーサーの基底クラス（v12.1: 定義書完全準拠）"""
    
    def __init__(self, organizer_name: str, source_url: str):
        self.organizer_name = organizer_name
        self.source_url = source_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def parse(self, page: Page) -> list[TournamentEvent]:
        """
        サブクラスで実装必須
        
        重要: page.goto() 等の通信処理は禁止
        渡された page オブジェクトからテキスト抽出のみ
        """
        pass
    
    def clean_text(self, text: str) -> str:
        """テキストのクリーニング"""
        if not text:
            return ""
        return ' '.join(text.split())
    
    def process_event_data(
        self,
        title: str,
        date_str: str,
        location: str = "",
        event_type: str = "",
        level: str = "",
        category: str = "",
        index: int = 0,
        detail_url: str = ""
    ) -> Optional[TournamentEvent]:
        """
        イベントデータを処理してTournamentEventを生成
        
        v12.1: 推測・補完の完全禁止
        日付が取れない場合は None を返す（強行突破禁止）
        """
        try:
            # 日付正規化（9パターン対応）
            normalized_date = self._normalize_date(date_str)
            
            # 日付が取れなければ None を返す（定義書準拠）
            if not normalized_date:
                self.logger.warning(f"日付抽出失敗: {date_str} → スキップ")
                return None
            
            # カテゴリが指定されていなければ判別
            if not category:
                category = self._determine_category(title)
            
            # ステータス判定（event_status: 募集中/結果）
            event_status = self._determine_event_status(title, normalized_date)
            
            # 結果の場合はタイトルに【結果報告】を付与
            if event_status == "結果" and not title.startswith("【結果報告】"):
                title = f"【結果報告】{title}"
            
            # ID生成
            date_for_id = normalized_date.replace('/', '').replace('(', '').replace(')', '')[:8]
            unique_id = self._generate_unique_id(date_for_id, index)
            
            # TournamentEvent生成
            event = TournamentEvent(
                unique_id=unique_id,
                title=self.clean_text(title),
                event_date=normalized_date,
                category=category,
                event_status=event_status,
                review_status="pending",  # 常にpending（人間が後で承認）
                organizer=self.organizer_name,
                location=location or "",
                event_type=event_type or "",
                level=level or "",
                source_url=self.source_url,
                detail_url=detail_url or "",
                entry_deadline="",
            )
            
            return event
        
        except Exception as e:
            self.logger.error(f"イベントデータ処理エラー: {str(e)}")
            # v12.1: エラー時は None を返す（ダミーデータ禁止）
            return None
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        日付を YYYY/MM/DD(曜) 形式に正規化
        
        【9パターン完全対応】
        1. 2026/5/13
        2. 2026-5-13
        3. 5/13
        4. 5月13日
        5. R8 5/13（和暦）
        6. 令和8年5月13日（和暦）
        7. 2026年5月13日
        8. 5/13(火)
        9. 2026/05/13(火)
        
        【年の自動判定】
        - 年表記なし → 月が現在月より前なら翌年、以降なら今年
        - 和暦 → 西暦2026年に変換（令和8年 = R8 = 2026年）
        """
        if not date_str:
            return None
        
        try:
            year = None
            month = None
            day = None
            
            # パターン1-2: 2026/5/13 または 2026-5-13
            match = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', date_str)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
            
            # パターン3: 5/13
            if not match:
                match = re.search(r'(\d{1,2})/(\d{1,2})', date_str)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
            
            # パターン4: 5月13日
            if not match:
                match = re.search(r'(\d{1,2})月(\d{1,2})日', date_str)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
            
            # パターン5: R8 5/13（和暦）
            if not match:
                match = re.search(r'R(\d{1,2})\s*(\d{1,2})[/\-](\d{1,2})', date_str)
                if match:
                    reiwa_year = int(match.group(1))
                    year = 2018 + reiwa_year  # 令和元年 = 2019年
                    month = int(match.group(2))
                    day = int(match.group(3))
            
            # パターン6: 令和8年5月13日
            if not match:
                match = re.search(r'令和(\d{1,2})年(\d{1,2})月(\d{1,2})日', date_str)
                if match:
                    reiwa_year = int(match.group(1))
                    year = 2018 + reiwa_year
                    month = int(match.group(2))
                    day = int(match.group(3))
            
            # パターン7: 2026年5月13日
            if not match:
                match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
            
            # パターン8: 5/13(火)
            if not match:
                match = re.search(r'(\d{1,2})/(\d{1,2})\([月火水木金土日]\)', date_str)
                if match:
                    month = int(match.group(1))
                    day = int(match.group(2))
            
            # パターン9: 2026/05/13(火)
            if not match:
                match = re.search(r'(\d{4})/(\d{2})/(\d{2})\([月火水木金土日]\)', date_str)
                if match:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
            
            # 月日が取得できなければ失敗
            if not month or not day:
                return None
            
            # 年の自動判定（年表記がない場合）
            if not year:
                now = datetime.now()
                current_year = now.year
                current_month = now.month
                
                # 過去の月 → 翌年
                if month < current_month:
                    year = current_year + 1
                else:
                    year = current_year
            
            # 曜日を計算
            try:
                date_obj = datetime(year, month, day)
                weekday = ['月', '火', '水', '木', '金', '土', '日'][date_obj.weekday()]
                return f"{year:04d}/{month:02d}/{day:02d}({weekday})"
            except ValueError:
                # 不正な日付（例: 2月30日）
                return None
        
        except Exception as e:
            self.logger.debug(f"日付正規化失敗: {date_str} - {str(e)}")
            return None
    
    def _determine_event_status(self, title: str, event_date: str) -> str:
        """
        イベントステータス判定（1日猶予の法則）
        
        判定ロジック:
        - タイトルに「結果」「入賞者」「リザルト」「優勝」を含む → "結果"
        - event_date が （今日 - 1日）より前 → "結果"
        - それ以外 → "募集中"
        
        【1日猶予の法則】
        今日が5/21の場合:
        - 5/20以降 → 募集中として取得
        - 5/19以前 → 結果として除外
        """
        # タイトルキーワードチェック
        result_keywords = ['結果', '入賞', '優勝', '準優勝', 'リザルト']
        if any(kw in title for kw in result_keywords):
            return "結果"
        
        # 日付が過去かチェック（1日猶予）
        try:
            date_part = event_date.split('(')[0]
            event_dt = datetime.strptime(date_part, "%Y/%m/%d")
            now = datetime.now()
            
            # 1日猶予: 今日 - 1日 より前なら「結果」
            grace_date = now.date() - timedelta(days=1)
            
            if event_dt.date() < grace_date:
                self.logger.info(f"【1日猶予の法則】過去イベントを自動除外: {title} ({event_date})")
                return "結果"
        except:
            pass
        
        return "募集中"
    
    def _determine_category(self, title: str) -> str:
        """
        カテゴリ判別
        
        タイトルに「ジュニア」「小学」「中学」「高校」を含む → "ジュニア"
        それ以外 → "一般"
        """
        junior_keywords = ['ジュニア', '小学', '中学', '高校']
        
        if any(kw in title for kw in junior_keywords):
            return "ジュニア"
        
        return "一般"
    
    def _generate_unique_id(self, date_part: str, index: int) -> str:
        """
        ID生成（定義書準拠）
        
        形式: auto_{主催者名}_{YYYYMMDD}_{連番}
        例: auto_筑紫野ロー_20260513_001
        
        主催者名は先頭5文字に丸める
        """
        org_short = self.organizer_name[:5]
        seq = f"{index + 1:03d}"
        return f"auto_{org_short}_{date_part}_{seq}"
    
    def _extract_deadline(self, text: str) -> Optional[str]:
        """
        締切日抽出器（器のみ提供）
        
        「締切」「申込」の近くにある日付を抽出
        個別パーサーから呼び出される想定
        
        戻り値: YYYY/MM/DD(曜) 形式 または None
        """
        if not text:
            return None
        
        # 「締切」「申込」が含まれる行のみ対象
        deadline_keywords = ['締切', '申込', 'エントリー', '受付']
        if not any(kw in text for kw in deadline_keywords):
            return None
        
        # その行から日付を抽出
        normalized = self._normalize_date(text)
        return normalized