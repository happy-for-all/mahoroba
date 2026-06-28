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
