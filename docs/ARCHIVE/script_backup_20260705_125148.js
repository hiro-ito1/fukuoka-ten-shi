/*
福岡テニス大会情報 - JavaScript（公開版）
v3: P24改修版（私好み=利用者カスタム保存・主催自動対応）

機能:
- 絞り込みフィルター（大人Jr × 曜日 × 主催 の掛け合わせ AND）
  - 大人Jr / 曜日: 単一選択（全て/個別）
  - 主催: 複数選択（選択した主催の OR）
- お気に入り（♥）: localStorage 保存・カード右上ハート
- 私好み（利用者カスタムプリセット）:
  - 「今の設定を保存」→ 名前を入力 → ボタンとして登録（最大5件）
  - ボタンを押すとその設定（大人Jr/曜日/主催）を復元
  - ×ボタンで削除
  - すべて localStorage 保存（再訪問でも残る）
- フィルタ結果0件の日付ヘッダー/月見出しを自動で非表示（日付のみ行バグ修正）
- アコーディオン開閉
- 状態保存（localStorage）:
    大人Jr / 曜日 / 主催 / アコーディオン開閉 / お気に入り / 私好みプリセット

データ属性（generate_html.py が各カードに付与）:
  data-category = "一般" | "ジュニア"
  data-daytype  = "holiday"(土日祝) | "weekday"(平日) | "unknown"
  data-org      = 主催キー（固定 or auto1.. or other）
  data-favid    = お気に入り識別子
*/

(function () {
    'use strict';

    const MAX_PRESETS = 5;

    // ===== localStorage キー =====
    const LS = {
        cat: 'tenshi_filter_cat',
        day: 'tenshi_filter_day',
        orgs: 'tenshi_filter_orgs',
        accordion: 'tenshi_accordion',
        favs: 'tenshi_favorites',
        presets: 'tenshi_my_presets'   // 利用者カスタムプリセット（配列）
    };

    // ===== 状態 =====
    let state = { cat: 'all', day: 'all', orgs: [] };

    // ===== 安全な localStorage =====
    function lsGet(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
    function lsSet(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }
    function lsJSON(key, fallback) {
        const raw = lsGet(key);
        if (!raw) return fallback;
        try { return JSON.parse(raw); } catch (e) { return fallback; }
    }

    // ===== 現在フィルタ状態の保存/読込 =====
    function saveState() {
        lsSet(LS.cat, state.cat);
        lsSet(LS.day, state.day);
        lsSet(LS.orgs, JSON.stringify(state.orgs));
    }
    function loadState() {
        const cat = lsGet(LS.cat);
        const day = lsGet(LS.day);
        if (cat) state.cat = cat;
        if (day) state.day = day;
        state.orgs = lsJSON(LS.orgs, []) || [];
    }

    // ===== UIへ反映 =====
    function syncUI() {
        document.querySelectorAll('.fb.cat').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-cat') === state.cat);
        });
        document.querySelectorAll('.fb.day').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('data-day') === state.day);
        });
        document.querySelectorAll('.ob').forEach(btn => {
            const key = btn.getAttribute('data-org');
            const on = state.orgs.indexOf(key) !== -1;
            btn.classList.toggle('active', on);
            const chk = btn.querySelector('.chk');
            if (chk) chk.textContent = on ? '☑' : '☐';
        });
        highlightMatchingPreset();
    }

    // ===== フィルタ適用 =====
    function applyFilters() {
        const cards = document.querySelectorAll('.event-card');
        cards.forEach(card => {
            const cat = card.getAttribute('data-category');
            const day = card.getAttribute('data-daytype');
            const org = card.getAttribute('data-org');
            let show = true;
            if (state.cat !== 'all' && cat !== state.cat) show = false;
            if (show && state.day !== 'all' && day !== state.day) show = false;
            if (show && state.orgs.length > 0 && state.orgs.indexOf(org) === -1) show = false;
            card.style.display = show ? '' : 'none';
        });

        // 日付セクション: 表示カード0なら見出しごと非表示（バグ修正①⑨）
        document.querySelectorAll('.date-section').forEach(sec => {
            const visible = sec.querySelectorAll('.event-card:not([style*="display: none"])').length;
            sec.style.display = visible === 0 ? 'none' : '';
        });
        // 月別セクション: 空ならグリッドを隠す
        document.querySelectorAll('.month-section').forEach(sec => {
            const visible = sec.querySelectorAll('.event-card:not([style*="display: none"])').length;
            const grid = sec.querySelector('.event-grid');
            if (grid) grid.style.display = visible === 0 ? 'none' : '';
        });
    }
    window.applyFilters = applyFilters;

    // ===== 私好み（利用者カスタムプリセット） =====
    function getPresets() { return lsJSON(LS.presets, []) || []; }
    function setPresets(arr) { lsSet(LS.presets, JSON.stringify(arr)); }

    function renderPresets() {
        const list = document.getElementById('myfav-list');
        if (!list) return;
        const presets = getPresets();
        list.innerHTML = '';
        if (presets.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'myfav-empty';
            empty.textContent = 'まだありません。下のボタンで今の絞り込みに名前をつけて保存できます。';
            list.appendChild(empty);
            return;
        }
        presets.forEach((pre, i) => {
            const btn = document.createElement('button');
            btn.className = 'fb preset';
            btn.setAttribute('data-preset-idx', i);
            btn.textContent = pre.name;
            btn.addEventListener('click', (ev) => {
                if (ev.target.classList.contains('preset-del')) return;
                applyPreset(i);
            });
            const del = document.createElement('button');
            del.className = 'preset-del';
            del.textContent = '×';
            del.setAttribute('aria-label', '削除');
            del.addEventListener('click', (ev) => {
                ev.stopPropagation();
                deletePreset(i);
            });
            btn.appendChild(del);
            list.appendChild(btn);
        });
        updateSaveBtnState();
        highlightMatchingPreset();
    }

    function updateSaveBtnState() {
        const btn = document.getElementById('save-preset-btn');
        if (!btn) return;
        const presets = getPresets();
        if (presets.length >= MAX_PRESETS) {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            btn.style.cursor = 'not-allowed';
            btn.textContent = '💾 保存は最大' + MAX_PRESETS + '件まで';
        } else {
            btn.disabled = false;
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
            btn.textContent = '💾 今の設定を保存';
        }
    }

    window.saveCurrentPreset = function () {
        const presets = getPresets();
        if (presets.length >= MAX_PRESETS) {
            alert('保存は最大' + MAX_PRESETS + '件までです。不要なものを削除してください。');
            return;
        }
        const name = prompt('この絞り込みに名前をつけて保存します（例: 準居の文山）');
        if (name === null) return;          // キャンセル
        const trimmed = name.trim();
        if (!trimmed) { alert('名前を入力してください。'); return; }
        presets.push({
            name: trimmed.length > 16 ? trimmed.slice(0, 16) : trimmed,
            cat: state.cat,
            day: state.day,
            orgs: state.orgs.slice()
        });
        setPresets(presets);
        renderPresets();
    };

    function applyPreset(idx) {
        const presets = getPresets();
        const pre = presets[idx];
        if (!pre) return;
        state.cat = pre.cat || 'all';
        state.day = pre.day || 'all';
        state.orgs = (pre.orgs || []).slice();
        syncUI();
        applyFilters();
        saveState();
    }

    function deletePreset(idx) {
        const presets = getPresets();
        if (idx < 0 || idx >= presets.length) return;
        if (!confirm('「' + presets[idx].name + '」を削除しますか？')) return;
        presets.splice(idx, 1);
        setPresets(presets);
        renderPresets();
    }

    // 現在のフィルタ状態と一致するプリセットをハイライト
    function highlightMatchingPreset() {
        const presets = getPresets();
        const sameOrgs = (a, b) => {
            if (a.length !== b.length) return false;
            const sa = a.slice().sort(), sb = b.slice().sort();
            return sa.every((v, i) => v === sb[i]);
        };
        document.querySelectorAll('#myfav-list .fb.preset').forEach(btn => {
            const i = parseInt(btn.getAttribute('data-preset-idx'), 10);
            const pre = presets[i];
            const match = pre && pre.cat === state.cat && pre.day === state.day && sameOrgs(pre.orgs || [], state.orgs);
            btn.classList.toggle('active', !!match);
        });
    }

    // ===== お気に入り =====
    function getFavs() { return lsJSON(LS.favs, []) || []; }
    function setFavs(arr) { lsSet(LS.favs, JSON.stringify(arr)); }
    function initFavs() {
        const favs = getFavs();
        document.querySelectorAll('.fav-btn').forEach(btn => {
            const id = btn.getAttribute('data-favid');
            const on = favs.indexOf(id) !== -1;
            btn.classList.toggle('active', on);
            btn.textContent = on ? '♥' : '♡';
        });
    }
    window.toggleFav = function (btn) {
        const id = btn.getAttribute('data-favid');
        let favs = getFavs();
        const idx = favs.indexOf(id);
        if (idx === -1) { favs.push(id); btn.classList.add('active'); btn.textContent = '♥'; }
        else { favs.splice(idx, 1); btn.classList.remove('active'); btn.textContent = '♡'; }
        setFavs(favs);
    };

    // ===== アコーディオン =====
    window.toggleAccordion = function () {
        const body = document.getElementById('acc-body');
        const arrow = document.getElementById('acc-arrow');
        if (!body) return;
        const closed = body.classList.toggle('closed');
        if (arrow) arrow.textContent = closed ? '▼' : '▲';
        lsSet(LS.accordion, closed ? 'closed' : 'open');
    };
    function initAccordion() {
        const body = document.getElementById('acc-body');
        const arrow = document.getElementById('acc-arrow');
        if (!body) return;
        const saved = lsGet(LS.accordion);
        if (saved === 'closed') { body.classList.add('closed'); if (arrow) arrow.textContent = '▼'; }
        else { body.classList.remove('closed'); if (arrow) arrow.textContent = '▲'; }
    };

    // ===== イベント登録 =====
    function bindEvents() {
        document.querySelectorAll('.fb.cat').forEach(btn => {
            btn.addEventListener('click', () => {
                state.cat = btn.getAttribute('data-cat');
                syncUI(); applyFilters(); saveState();
            });
        });
        document.querySelectorAll('.fb.day').forEach(btn => {
            btn.addEventListener('click', () => {
                state.day = btn.getAttribute('data-day');
                syncUI(); applyFilters(); saveState();
            });
        });
        document.querySelectorAll('.ob').forEach(btn => {
            btn.addEventListener('click', () => {
                const key = btn.getAttribute('data-org');
                const idx = state.orgs.indexOf(key);
                if (idx === -1) state.orgs.push(key); else state.orgs.splice(idx, 1);
                syncUI(); applyFilters(); saveState();
            });
        });
    }

    // ===== スクロールトップ =====
    function initScrollTop() {
        const btn = document.createElement('button');
        btn.innerHTML = '↑';
        btn.className = 'scroll-top-btn';
        btn.style.cssText = 'position:fixed;bottom:30px;right:30px;width:50px;height:50px;border-radius:50%;background:#2E7D32;color:white;border:none;font-size:1.5rem;cursor:pointer;display:none;box-shadow:0 4px 8px rgba(0,0,0,0.2);z-index:1000;';
        document.body.appendChild(btn);
        window.addEventListener('scroll', () => {
            btn.style.display = window.pageYOffset > 300 ? 'block' : 'none';
        });
        btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
    }

    // ===== 起動 =====
    document.addEventListener('DOMContentLoaded', () => {
        loadState();
        initAccordion();
        bindEvents();
        renderPresets();
        syncUI();
        initFavs();
        applyFilters();
        initScrollTop();
        console.log('✅ 福岡テニス大会情報 - フィルター起動完了 (v3)');
    });
})();