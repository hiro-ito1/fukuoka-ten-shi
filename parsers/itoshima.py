"""
ItoshimaParser - 糸島市テニス協会専用パーサー
v14.0: 種目・性別分離版（2026-05-23）

【v13.4 → v14.0 の変更点】
- _extract_event_details() 関数を追加
- タイトルから種目・性別・年齢を抽出
  例: "糸島レディーステニス大会" → event_type="ダブルス", gender="女子"
- notes フィールドに補足情報を格納

【完全版】大量スペース対応 + 日付行結合前処理 + 正規表現強靭化
"""
import re
from datetime import datetime
from playwright.sync_api import Page
from typing import List, Tuple, Optional

from parsers.base_parser import BaseParser
from schema import TournamentEvent


class ItoshimaParser(BaseParser):
    """糸島市テニス協会のウェブサイトを解析するパーサー v14.0"""

    def __init__(self):
        super().__init__(
            organizer_name="糸島市テニス協会",
            source_url="https://itosima-tennis.com/"
        )
    
    def _extract_event_details(self, title: str) -> Tuple[str, str, str, str]:
        """
        タイトルから種目・性別・レベル・補足を抽出
        
        Examples:
            "糸島レディーステニス大会" → ("ダブルス", "女子", "", "レディース")
            "糸島シニア選手権" → ("シングルス", "", "", "シニア")
            "糸島ジュニアオープン" → ("シングルス", "", "OP", "ジュニア")
        
        Returns:
            (event_type, gender, level, notes)
        """
        event_type = ""
        gender = ""
        level = ""
        notes_list = []
        
        # 性別判定
        if "レディース" in title or "レディス" in title or "女子" in title:
            gender = "女子"
            notes_list.append("レディース")
        elif "男子" in title:
            gender = "男子"
        elif "混合" in title or "ミックス" in title:
            gender = "混合"
        
        # 種目判定（デフォルトはシングルス）
        if "ダブルス" in title:
            event_type = "ダブルス"
        elif "団体" in title:
            event_type = "団体"
        else:
            # レディース大会は通常ダブルス
            if "レディース" in title or "レディス" in title:
                event_type = "ダブルス"
            else:
                event_type = "シングルス"
        
        # レベル判定
        if "オープン" in title or "OP" in title:
            level = "OP"
        
        # 補足情報
        if "シニア" in title:
            notes_list.append("シニア")
        if "ジュニア" in title:
            notes_list.append("ジュニア")
        if "小学生" in title:
            notes_list.append("小学生")
        if "中学生" in title:
            notes_list.append("中学生")
        
        # 年齢制限
        age_match = re.search(r'(\d+)歳', title)
        if age_match:
            notes_list.append(f"{age_match.group(1)}歳")
        
        notes = ", ".join(notes_list) if notes_list else ""
        
        return (event_type, gender, level, notes)

    def parse(self, page: Page) -> List[TournamentEvent]:
        """
        糸島市テニス協会のページを解析（トップページ & 年間情報ページ両対応）
        """
        self.logger.info("解析実行中...")
        events = []
        
        # 🔥 対策1: タイミングの罠 - Wix動的描画を最大8秒待つ
        self.logger.info("📊 動的コンテンツの描画完了を待機中（最大8秒）...")
        try:
            page.wait_for_selector("body", timeout=8000, state="visible")
            page.wait_for_timeout(3000)
            self.logger.info("✅ 描画完了を確認")
        except Exception as e:
            self.logger.warning(f"⚠️ 待機タイムアウト: {str(e)}")
        
        # 💡 ページテキスト取得
        page_text = page.locator("body").inner_text()
        lines = page_text.split("\n")
        
        # 🔍 デバッグ：最初の30行を出力
        self.logger.info("=" * 60)
        self.logger.info("📄 ページテキストの最初の30行:")
        for i, line in enumerate(lines[:30]):
            self.logger.info(f"  行{i:02d}: {line[:80]}")
        self.logger.info("=" * 60)

        # ==========================================
        # ページ自動判定
        # ==========================================
        is_calendar_page = any("年度" in line for line in lines[:15]) and any("実施大会" in line for line in lines[:15])

        if is_calendar_page:
            self.logger.info("【ページ判定】年間スケジュール（テーブル/テキスト）解析モードを発動")
            
            # --- 年度情報の検出 ---
            current_year = datetime.now().year
            fiscal_year = current_year
            for line in lines:
                fiscal_match = re.search(r'(令和\s*(\d+)|R\s*(\d+))\s*年度', line)
                if fiscal_match:
                    reiwa_val = fiscal_match.group(2) or fiscal_match.group(3)
                    fiscal_year = 2018 + int(reiwa_val)
                    self.logger.info(f"📅 年度情報検出: 令和{reiwa_val}年度 = {fiscal_year}年度")
                    break
            
            # ==========================================
            # 🔥 対策2: 改行による分断の解決
            # 日付だけの行を見つけて、次の有効テキスト行と結合
            # ==========================================
            merged_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 日付パターン（月と日と曜日）だけの行を検出
                # 例: "4    19(日)" や "6    21(日)"
                date_only_match = re.match(r'^(\d{1,2})\s+(\d{1,2})\s*[\(（]([月火水木金土日])[\)）]\s*$', line)
                
                if date_only_match:
                    # 日付だけの行を発見
                    month = date_only_match.group(1)
                    day = date_only_match.group(2)
                    weekday = date_only_match.group(3)
                    
                    # 次の有効なテキスト行（大会名など）を探す
                    j = i + 1
                    next_text = ""
                    while j < len(lines):
                        candidate = lines[j].strip()
                        # 空行や数字だけの行はスキップ
                        if candidate and not re.match(r'^\d+$', candidate):
                            next_text = candidate
                            break
                        j += 1
                    
                    # 日付と大会名を結合
                    if next_text:
                        merged = f"{month}{day}({weekday}) {next_text}"
                        merged_lines.append(merged)
                        self.logger.info(f"🔧 行結合: [{line}] + [{next_text}] → [{merged}]")
                        i = j + 1  # スキップした行を飛ばす
                        continue
                
                # 通常の行はそのまま追加
                merged_lines.append(line)
                i += 1
            
            self.logger.info(f"📊 行結合完了: {len(lines)}行 → {len(merged_lines)}行")
            
            # ==========================================
            # マッチング処理
            # ==========================================
            index = 0
            matched_count = 0
            
            for line_num, line in enumerate(merged_lines):
                line = self.clean_text(line)
                if not line:
                    continue
                
                # 🔍 デバッグ：日付パターンがある行を出力
                if re.search(r'\d+.*[\(（][月火水木金土日][\)）]', line):
                    self.logger.info(f"🔍 候補行{line_num}: {line[:100]}")
                
                # 🔥 対策1&3: 大量スペース対応 + 正規表現強靭化
                # 月と日の間に任意の数のスペース（\s+）を許容
                match = re.search(r'^(\d{1,2})\s*(\d{1,2})\s*[\(（]([月火水木金土日])[\)）]\s*(.*)', line)
                
                if match:
                    matched_count += 1
                    self.logger.info(f"✅ マッチ成功 {matched_count}件目: {line[:80]}")
                    
                    month = int(match.group(1))
                    day = int(match.group(2))
                    raw_title = match.group(4).strip()
                    
                    self.logger.info(f"  → 月={month}, 日={day}, タイトル={raw_title[:50]}")
                    
                    # 不要なノイズを排除
                    title_clean = re.sub(r'\d+名.*|\d+チーム.*|●.*|指定事業.*', '', raw_title).strip()
                    
                    # --------------------------------------------------
                    # 🔥 分裂魔法（同セル内マルチイベント）
                    # --------------------------------------------------
                    multi_match = re.search(r'^(\d{1,2})\s*[\(（]([月火水木金土日])[\)）]\s*(.*)', title_clean)
                    
                    if multi_match:
                        day2 = int(multi_match.group(1))
                        rest_text = multi_match.group(3).strip()
                        
                        self.logger.info(f"  🔥 分裂検知: 2つ目の日={day2}")
                        
                        parts = rest_text.split('大会')
                        if len(parts) >= 3:
                            title1 = parts[0] + '大会'
                            title2 = parts[1] + '大会'
                        elif len(parts) == 2 and parts[1].strip():
                            title1 = parts[0] + '大会'
                            title2 = parts[1].strip()
                        else:
                            mid = len(rest_text) // 2
                            title1 = rest_text[:mid].strip()
                            title2 = rest_text[mid:].strip()
                        
                        # ==========================================
                        # 【v14.0 修正】種目・性別・補足を抽出
                        # ==========================================
                        event_type1, gender1, level1, notes1 = self._extract_event_details(title1)
                        
                        # 1件目
                        event1 = self.process_event_data(
                            title=title1,
                            date_str=f"{month}月{day}日",
                            location="糸島市運動公園",
                            event_type=event_type1,
                            level=level1,
                            index=index
                        )
                        if event1:
                            event1.gender = gender1
                            event1.notes = notes1
                            self.logger.info(f"✨ [分裂成功①] {event1.event_date} -> {event1.title} (種目={event_type1}, 性別={gender1})")
                            events.append(event1)
                            index += 1
                        
                        # ==========================================
                        # 【v14.0 修正】種目・性別・補足を抽出
                        # ==========================================
                        event_type2, gender2, level2, notes2 = self._extract_event_details(title2)
                        
                        # 2件目
                        event2 = self.process_event_data(
                            title=title2,
                            date_str=f"{month}月{day2}日",
                            location="糸島市運動公園",
                            event_type=event_type2,
                            level=level2,
                            index=index
                        )
                        if event2:
                            event2.gender = gender2
                            event2.notes = notes2
                            self.logger.info(f"✨ [分裂成功②] {event2.event_date} -> {event2.title} (種目={event_type2}, 性別={gender2})")
                            events.append(event2)
                            index += 1
                            
                        continue
                    
                    # --------------------------------------------------
                    # 通常の1行1大会
                    # --------------------------------------------------
                    if not title_clean or len(title_clean) < 3:
                        self.logger.info(f"  ⏭️ スキップ: タイトルが短すぎる({len(title_clean)}文字)")
                        continue

                    # ==========================================
                    # 【v14.0 修正】種目・性別・補足を抽出
                    # ==========================================
                    event_type, gender, level, notes = self._extract_event_details(title_clean)
                    
                    event = self.process_event_data(
                        title=title_clean,
                        date_str=f"{month}月{day}日",
                        location="糸島市運動公園",
                        event_type=event_type,
                        level=level,
                        index=index
                    )
                    if event:
                        event.gender = gender
                        event.notes = notes
                        self.logger.info(f"✅ [通常取得] {event.event_date} -> {event.title} (種目={event_type}, 性別={gender})")
                        events.append(event)
                        index += 1
                    else:
                        self.logger.info(f"  ⏭️ スキップ: 過去のイベント")
            
            self.logger.info(f"=" * 60)
            self.logger.info(f"📊 最終結果: マッチ{matched_count}行 / 取得{len(events)}件")
            self.logger.info(f"=" * 60)
            
            return events

        # ==========================================
        # ルートB: 通常のトップページ（h3箇条書き）
        # ==========================================
        else:
            self.logger.info("【ページ判定】通常トップページ（h3）解析モードを発動")
            h3_elements = page.locator('h3').all()
            self.logger.info(f"h3要素数: {len(h3_elements)}件")

            for i, h3 in enumerate(h3_elements):
                title_text = h3.inner_text()
                if not title_text:
                    continue

                if "ご挨拶" in title_text:
                    continue

                date_match = re.search(
                    r'(令和\d+年\d+月\d+日|R\d+\s*\d+/\d+|\d{4}年\d+月\d+日|\d{4}/\d+/\d+|\d+/\d+)',
                    title_text
                )

                if date_match:
                    extracted_date = date_match.group(1)
                    
                    clean_title = title_text
                    for suffix in ["の参加者募集について", "の募集について", "参加者募集について"]:
                        clean_title = clean_title.replace(suffix, "")

                    # ==========================================
                    # 【v14.0 修正】種目・性別・補足を抽出
                    # ==========================================
                    event_type, gender, level, notes = self._extract_event_details(clean_title)
                    
                    event = self.process_event_data(
                        title=clean_title,
                        date_str=extracted_date,
                        event_type=event_type,
                        level=level,
                        index=i
                    )
                    
                    if event is None:
                        continue

                    event.gender = gender
                    event.notes = notes
                    events.append(event)

            return events