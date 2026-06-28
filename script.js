    // ① ナビ：スクロール時にクラス付与（シュリンク・影の付与）
    const nav = document.getElementById('global-nav');
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 40);
    }, { passive: true });

    // ① ハンバーガーメニューの開閉
    const hamburger = document.getElementById('hamburger');
    const drawer    = document.getElementById('nav-drawer');
    hamburger.addEventListener('click', () => {
      const isOpen = hamburger.classList.toggle('open');
      drawer.classList.toggle('open', isOpen);
      hamburger.setAttribute('aria-expanded', isOpen);
    });
    function closeDrawer() {
      hamburger.classList.remove('open');
      drawer.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
    }

    // ② スクロールフェードイン（Intersection Observer）
    const fadeEls = document.querySelectorAll('.fade-in-up');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target); // 一度表示したら監視を解除して負荷を軽減
        }
      });
    }, {
      threshold: 0.12 // 要素が12%画面に入ったら発火
    });
    fadeEls.forEach(el => observer.observe(el));

// ============================================================
// 世界の攻略情報：articles.json を読み込んで表示
// ============================================================
fetch('./articles.json')
  .then(r => r.json())
  .then(data => {
    // 更新日時をタグに表示
    const dateEl = document.getElementById('world-info-date');
    if (dateEl) dateEl.textContent = data.generated_at + ' 更新';

    const body = document.getElementById('world-info-body');
    if (!body) return;

    if (!data.articles || data.articles.length === 0) {
      body.innerHTML = '<p>現在、記事を取得中です。しばらくお待ちください。</p>';
      return;
    }

    // 上位10件を表示
    const html = data.articles.slice(0, 10).map(a => `
      <p style="margin-bottom: 12px; padding-bottom: 12px;
                border-bottom: 1px solid var(--color-glass-border);">
        <span style="font-size:10px; background:rgba(199,139,68,0.12);
                     color:var(--color-accent); padding:2px 6px;
                     border-radius:10px; margin-right:6px;">${a.source}</span>
        <a href="${a.url}" target="_blank" rel="noopener noreferrer">
          ${a.title}
        </a>
        <span style="display:block; font-size:11px;
                     color:var(--color-accent); margin-top:4px;">
          ${a.date}
        </span>
      </p>
    `).join('');

    body.innerHTML = html;
  })
  .catch(() => {
    const body = document.getElementById('world-info-body');
    if (body) body.innerHTML =
      '<p>情報の読み込みに失敗しました。しばらくお待ちください。</p>';
  });
