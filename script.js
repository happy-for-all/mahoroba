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
    // XSSエスケープ関数（innerHTML直接埋め込みを安全に）
    function escHtml(str) {
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    const html = data.articles.slice(0, 10).map(a => {
      const summary = a.summary
        ? `<span style="display:block; font-size:12px; color:var(--color-text);
                        margin-top:4px; opacity:0.75; line-height:1.6;">
             ${escHtml(a.summary.slice(0, 100))}${a.summary.length > 100 ? '…' : ''}
           </span>`
        : '';
      return `
        <p style="margin-bottom:14px; padding-bottom:14px;
                  border-bottom:1px solid var(--color-glass-border);">
          <span style="font-size:10px; background:rgba(199,139,68,0.12);
                       color:var(--color-accent); padding:2px 6px;
                       border-radius:10px; margin-right:6px;">
            ${escHtml(a.source)}
          </span>
          <span style="font-size:10px; background:rgba(100,160,100,0.12);
                       color:#5a8a5a; padding:2px 6px;
                       border-radius:10px; margin-right:6px;">
            ${a.lang === 'JP' ? '日本語' : 'English'}
          </span>
          <a href="${escHtml(a.url)}" target="_blank" rel="noopener noreferrer"
             style="font-weight:500;">
            ${escHtml(a.title)}
          </a>
          ${summary}
          <span style="display:block; font-size:11px;
                       color:var(--color-accent); margin-top:4px;">
            📅 ${escHtml(a.date)}
          </span>
        </p>`;
    }).join('');

    body.innerHTML = html || '<p>現在、記事を取得中です。しばらくお待ちください。</p>';
  })
  .catch(() => {
    const body = document.getElementById('world-info-body');
    if (body) body.innerHTML =
      '<p>情報の読み込みに失敗しました。しばらくお待ちください。</p>';
  });


// ============================================================
// ③ トップに戻るボタンの制御
// ============================================================
const pageTopBtn = document.getElementById('page-top');

// スクロール量が300pxを超えたらボタンを表示
window.addEventListener('scroll', () => {
  if (window.scrollY > 300) {
    pageTopBtn.classList.add('show');
  } else {
    pageTopBtn.classList.remove('show');
  }
}, { passive: true });

// クリックされたら一番上へスムーズにスクロール
pageTopBtn.addEventListener('click', () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
});


// ============================================================
// ④ ギャラリー画像の拡大表示（ライトボックス）
// ============================================================
const modal = document.getElementById('image-modal');
const modalImg = document.getElementById('modal-img');
const modalBg = document.querySelector('.modal-bg');
const modalClose = document.getElementById('modal-close');
const galleryImgs = document.querySelectorAll('.gold-frame img');

// 画像がクリックされたら、その画像をモーダルに渡して表示
galleryImgs.forEach(img => {
  img.addEventListener('click', () => {
    modalImg.src = img.src; 
    modal.classList.add('show');
  });
});

// 背景の黒い部分、または「×」ボタンを押したら閉じる
const closeModal = () => {
  modal.classList.remove('show');
};
modalBg.addEventListener('click', closeModal);
modalClose.addEventListener('click', closeModal);


// ============================================================
// 👑 新規追加：ピンクの肉球マーク（カーソル追従＆タップエフェクト）
// ============================================================
(function() {
  const PAW_COLOR = '#F596AA'; // サイトのアクセントピンクと統一
  let lastPawTime = 0;
  const PAW_INTERVAL = 120; // ms単位の間引き（連続しすぎないように）

  function createPaw(x, y) {
    const paw = document.createElement('div');
    paw.className = 'mahoroba-paw';
    paw.style.left = x + 'px';
    paw.style.top = y + 'px';
    paw.style.transform = `translate(-50%, -50%) rotate(${Math.random() * 40 - 20}deg)`;
    paw.innerHTML = `
      <svg width="22" height="22" viewBox="0 0 24 24" fill="${PAW_COLOR}">
        <ellipse cx="12" cy="16" rx="6" ry="5"/>
        <ellipse cx="5" cy="9" rx="2.3" ry="3"/>
        <ellipse cx="10" cy="5.5" rx="2.3" ry="3"/>
        <ellipse cx="15" cy="5.5" rx="2.3" ry="3"/>
        <ellipse cx="19.5" cy="9" rx="2.3" ry="3"/>
      </svg>`;
    document.body.appendChild(paw);

    // アニメーション終了後に要素を除去（メモリリーク防止）
    setTimeout(() => paw.remove(), 900);
  }

  // PC：マウス移動で肉球を間引きしながら表示
  window.addEventListener('mousemove', (e) => {
    const now = Date.now();
    if (now - lastPawTime > PAW_INTERVAL) {
      createPaw(e.clientX, e.clientY);
      lastPawTime = now;
    }
  });

  // スマホ：タップ時に表示
  window.addEventListener('touchstart', (e) => {
    if (e.touches && e.touches[0]) {
      createPaw(e.touches[0].clientX, e.touches[0].clientY);
    }
  }, { passive: true });

  // スマホ：スクロール中も控えめに表示（画面中央寄りランダム位置）
  let lastScrollPawTime = 0;
  window.addEventListener('scroll', () => {
    const now = Date.now();
    if (now - lastScrollPawTime > 400) {
      const x = window.innerWidth * (0.3 + Math.random() * 0.4);
      const y = window.innerHeight * (0.3 + Math.random() * 0.4);
      createPaw(x, y);
      lastScrollPawTime = now;
    }
  }, { passive: true });
})();
