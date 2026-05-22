/*
福岡テニス大会情報 - JavaScriptフィルター
v1.0: GitHub Pages公開版
カテゴリフィルター機能
*/

document.addEventListener('DOMContentLoaded', () => {
    // フィルターボタンの取得
    const filterButtons = document.querySelectorAll('.filter-btn');
    const eventCards = document.querySelectorAll('.event-card');
    
    // フィルター処理
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filter = button.getAttribute('data-filter');
            
            // アクティブボタンの切り替え
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // カードの表示/非表示
            eventCards.forEach(card => {
                const category = card.getAttribute('data-category');
                
                if (filter === 'all') {
                    card.style.display = 'block';
                    card.style.animation = 'fadeIn 0.5s ease-out';
                } else if (category === filter) {
                    card.style.display = 'block';
                    card.style.animation = 'fadeIn 0.5s ease-out';
                } else {
                    card.style.display = 'none';
                }
            });
            
            // 月別セクションの表示/非表示
            updateMonthSections();
        });
    });
    
    // 月別セクションの表示制御
    function updateMonthSections() {
        const monthSections = document.querySelectorAll('.month-section');
        
        monthSections.forEach(section => {
            const visibleCards = section.querySelectorAll('.event-card[style*="display: block"], .event-card:not([style*="display: none"])');
            
            if (visibleCards.length === 0) {
                section.style.display = 'none';
            } else {
                section.style.display = 'block';
            }
        });
    }
    
    // スムーズスクロール
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 統計情報の更新（フィルター時）
    function updateStats(filter) {
        let visibleCards = [];
        
        if (filter === 'all') {
            visibleCards = Array.from(eventCards);
        } else {
            visibleCards = Array.from(eventCards).filter(
                card => card.getAttribute('data-category') === filter
            );
        }
        
        // 統計カウントの更新（オプション）
        const total = visibleCards.length;
        const general = visibleCards.filter(
            card => card.getAttribute('data-category') === '一般'
        ).length;
        const junior = visibleCards.filter(
            card => card.getAttribute('data-category') === 'ジュニア'
        ).length;
        
        console.log(`表示中: ${total}件 (一般: ${general}, ジュニア: ${junior})`);
    }
    
    // ページトップへ戻るボタン（オプション）
    const scrollTopBtn = document.createElement('button');
    scrollTopBtn.innerHTML = '↑';
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--primary);
        color: white;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        display: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        z-index: 1000;
    `;
    
    document.body.appendChild(scrollTopBtn);
    
    // スクロール時の表示/非表示
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollTopBtn.style.display = 'block';
        } else {
            scrollTopBtn.style.display = 'none';
        }
    });
    
    // クリックでトップへ
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // ホバーエフェクト
    scrollTopBtn.addEventListener('mouseenter', () => {
        scrollTopBtn.style.transform = 'scale(1.1)';
        scrollTopBtn.style.background = 'var(--primary-light)';
    });
    
    scrollTopBtn.addEventListener('mouseleave', () => {
        scrollTopBtn.style.transform = 'scale(1)';
        scrollTopBtn.style.background = 'var(--primary)';
    });
    
    console.log('✅ 福岡テニス大会情報 - システム起動完了');
});
