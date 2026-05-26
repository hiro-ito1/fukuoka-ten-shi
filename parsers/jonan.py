"""
城南テニスクラブ専用パーサー v2.5 FIXED
完全修正版

修正内容:
1. タイトル抽出: 「BCシリーズ（ベテラン）」を正しく取得
2. レベル抽出: テーブルの「レベル」列から取得
3. 補足（年齢制限）: ※年齢制限 を抽出
"""
import re
import logging
from datetime import datetime
from playwright.sync_api import Page
from parsers.base_parser import BaseParser
from schema import TournamentEvent


class JonanParser(BaseParser):
    """城南テニスクラブ専用パーサー v2.5"""
    
    def __init__(self):
        super().__init__(
            organizer_name="城南テニスクラブ",
            source_url="https://jonantennis.net/convention/"
        )
    
    def parse(self, page: Page) -> list[TournamentEvent]:
        """
        城南TC TABLE形式のスクレイピング
        
        テーブル列構造（スクリーンショットより）:
        1列目: 日付（06/14(日)）
        2列目: 時間（10:30）
        3列目: タイトル（BCシリーズ（ベテラン）【最低4試合保証】）
        4列目: 種目（女子シングルス）
        5列目: レベル（BC）
        6列目: 参加費（3,500）
        7列目: 状態（募集中）
        8列目: 定員（8名）
        
        補足情報:
        ※切日 6/12 (金) 15:00 定員=8名 ※年齢制限 35歳以上 1991/12/31以前生まれ
        """
        events = []
        
        try:
            # HTML全体を取得
            html_content = page.content()
            
            # <tr>タグで行を分割
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.DOTALL)
            
            self.logger.info(f"城南TC {len(rows)}行を検出 (HTML)")
            
            for row_idx, row in enumerate(rows, 1):  # 全行をスキャン
                # <td>タグで列を抽出
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cols) < 5:
                    continue
                
                # 🔍 DEBUG: cols[0] と cols[2] の中身を確認（最初の9行）
                if row_idx <= 9:
                    col0_clean = re.sub(r'<[^>]+>', '', cols[0]).strip()
                    col2_clean = re.sub(r'<[^>]+>', '', cols[2]).strip()
                    self.logger.info(f"[DEBUG] Row {row_idx}: cols[0] = '{col0_clean[:40]}' | cols[2] = '{col2_clean[:40]}'")
                
                # 日付抽出（cols[0]）
                date_text = re.sub(r'<[^>]+>', '', cols[0]).strip()
                # HTMLエンティティを除去（&nbsp; → スペース）
                date_text = date_text.replace('&nbsp;', ' ')
                date_text = date_text.replace('&ensp;', ' ')
                date_text = date_text.replace('&emsp;', ' ')
                
                date_match = re.search(r'(\d{1,2}/\d{1,2})\s*\(([月火水木金土日])\)', date_text)
                
                if not date_match:
                    # 日付が見つからない場合はスキップ
                    if row_idx <= 9:
                        self.logger.info(f"[DEBUG] Row {row_idx}: 日付なし（'{date_text}'）→ スキップ")
                    continue
                
                month_day = date_match.group(1)
                weekday = date_match.group(2)
                event_date = self._normalize_date(f"{month_day}({weekday})")
                
                if not event_date:
                    continue
                
                # 🎯 タイトル抽出（cols[2]）
                # 修正: 「【最低4試合保証】」の前の部分を取得
                title_full = re.sub(r'<[^>]+>', '', cols[2]).strip()
                
                # パターン: "BCシリーズ（ベテラン）【最低4試合保証】https://..."
                title_match = re.search(r'^(.+?)【最低[４4]試合保証】', title_full)
                
                if title_match:
                    title_raw = title_match.group(1).strip()
                else:
                    # 【】がない場合はそのまま使用
                    title_raw = title_full.split('http')[0].strip()
                
                # 種目抽出（cols[3]）
                event_type_text = re.sub(r'<[^>]+>', '', cols[3]).strip()
                event_type = self._determine_event_type(event_type_text)
                
                # 性別抽出
                gender = self._determine_gender(event_type_text)
                
                # 🎯 レベル抽出（cols[4]）
                level_text = re.sub(r'<[^>]+>', '', cols[4]).strip()
                
                # 🎯 補足抽出（年齢制限）
                # cols[2] の中に「※年齢制限 35歳以上」が含まれている
                notes = ""
                age_match = re.search(r'※年齢制限\s*(\d+歳以上)', title_full)
                if age_match:
                    notes = age_match.group(1)
                
                # DEBUG出力（最初の4件のみ）
                if len(events) < 4:
                    self.logger.info(f"[DEBUG {len(events)+1}] title_raw = '{title_raw}'")
                    self.logger.info(f"[DEBUG {len(events)+1}] level = '{level_text}'")
                    self.logger.info(f"[DEBUG {len(events)+1}] notes = '{notes}'")
                
                # TournamentEvent生成
                event = self.process_event_data(
                    title=title_raw,
                    date_str=event_date,
                    location="城南テニスクラブ",
                    event_type=event_type,
                    level=level_text,
                    category="一般",
                    index=len(events)
                )
                
                if event:
                    # 性別・補足を追加
                    event.gender = gender
                    event.notes = notes
                    
                    events.append(event)
                    
                    self.logger.info(
                        f"✅ {title_raw} (種目={event_type}, 性別={gender}, レベル={level_text}, 補足={notes})"
                    )
        
        except Exception as e:
            self.logger.error(f"パースエラー: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        self.logger.info(f"城南TC 最終的に {len(events)}件のイベントを抽出")
        return events
    
    def _determine_event_type(self, text: str) -> str:
        """種目判定"""
        if 'シングルス' in text:
            return 'シングルス'
        elif 'ダブルス' in text:
            return 'ダブルス'
        return ''
    
    def _determine_gender(self, text: str) -> str:
        """性別判定"""
        if '男子' in text and '女子' in text:
            return '混合'
        elif '男女' in text:
            return '男女'
        elif '女子' in text:
            return '女子'
        elif '男子' in text:
            return '男子'
        return ''