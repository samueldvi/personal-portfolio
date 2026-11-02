/* Small enhancements only: static content and links remain usable without JS. */
(function () {
  const root = document.documentElement;
  const read = (key) => { try { return localStorage.getItem(key); } catch (_) { return null; } };
  const write = (key, value) => { try { localStorage.setItem(key, value); } catch (_) { /* Private browsing can block storage. */ } };

  const themeSelect = document.getElementById('themeSelect');
  const savedTheme = read('portfolio-theme');
  const theme = savedTheme === 'light' || savedTheme === 'dark' ? savedTheme : 'auto';
  if (themeSelect) {
    themeSelect.value = theme;
    themeSelect.addEventListener('change', () => {
      const selected = themeSelect.value;
      if (selected === 'light' || selected === 'dark') {
        root.dataset.theme = selected;
        write('portfolio-theme', selected);
      } else {
        root.removeAttribute('data-theme');
        write('portfolio-theme', 'auto');
      }
    });
  }
  // With Auto selected, the CSS media query follows system changes immediately.

  document.querySelectorAll('[data-language]').forEach((link) => {
    link.addEventListener('click', () => write('portfolio-language', link.dataset.language));
  });
  if (document.body.dataset.page === 'gateway') {
    const supported = new Set([...document.querySelectorAll('.language-card[data-language]')].map((link) => link.dataset.language));
    const browserPrimary = (navigator.languages?.[0] || navigator.language || '').split('-')[0].toLowerCase();
    const manual = read('portfolio-language');
    const preferred = supported.has(manual) ? manual : supported.has(browserPrimary) ? browserPrimary : 'en';
    const suggested = document.querySelector(`[data-language="${preferred}"]`);
    if (suggested) suggested.classList.add('is-recommended');
    const hint = document.getElementById('languageHint');
    const legacySection = { '#hero':'', '#home':'', '#about':'about/', '#projects':'projects/', '#skills':'about/', '#experience':'experience/', '#education':'experience/', '#contact':'contact/' }[window.location.hash];
    if (legacySection !== undefined) {
      document.querySelectorAll('.language-card[data-language]').forEach((link) => {
        link.href = `${link.dataset.language}/${legacySection}`;
      });
      if (hint) hint.textContent = hint.dataset.legacyHint;
    } else if (hint) {
      const name = suggested?.querySelector('strong')?.textContent || preferred.toUpperCase();
      hint.textContent = hint.dataset.suggestedTemplate.replace('{language}', name);
    }
  }

  const menuToggle = document.getElementById('menuToggle');
  const nav = document.getElementById('navMenu');
  function setMenu(open) {
    if (!menuToggle || !nav) return;
    menuToggle.setAttribute('aria-expanded', String(open));
    menuToggle.setAttribute('aria-label', open ? menuToggle.dataset.closeLabel : menuToggle.dataset.openLabel);
    nav.classList.toggle('nav--open', open);
  }
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => setMenu(menuToggle.getAttribute('aria-expanded') !== 'true'));
    nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
        setMenu(false);
        menuToggle.focus();
      }
    });
    document.addEventListener('click', (event) => {
      if (!nav.contains(event.target) && !menuToggle.contains(event.target)) setMenu(false);
    });
    window.matchMedia('(min-width: 1060px)').addEventListener?.('change', () => setMenu(false));
  }

  document.querySelectorAll('[data-embed-url]').forEach((button) => {
    button.addEventListener('click', () => {
      const frame = document.createElement('iframe');
      frame.src = button.dataset.embedUrl;
      frame.title = button.dataset.embedTitle;
      frame.loading = 'lazy';
      frame.referrerPolicy = 'strict-origin-when-cross-origin';
      frame.allowFullscreen = true;
      frame.setAttribute('allow', 'encrypted-media; picture-in-picture; fullscreen');
      button.closest('.embed-shell').replaceChildren(frame);
    });
  });

  const momentDialog = document.getElementById('momentLightbox');
  const momentImage = document.getElementById('momentLightboxImage');
  const momentTitle = document.getElementById('momentLightboxTitle');
  const momentCaption = document.getElementById('momentLightboxCaption');
  const momentClose = document.getElementById('momentLightboxClose');
  if (momentDialog?.showModal && momentImage && momentTitle && momentCaption && momentClose) {
    let returnFocus = null;
    document.querySelectorAll('[data-moment-open]').forEach((link) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        returnFocus = link;
        momentImage.src = link.href;
        momentImage.alt = link.dataset.alt;
        momentTitle.textContent = link.dataset.title;
        momentCaption.textContent = link.dataset.caption;
        momentDialog.showModal();
        momentClose.focus();
      });
    });
    momentClose.addEventListener('click', () => momentDialog.close());
    momentDialog.addEventListener('click', (event) => {
      if (event.target === momentDialog) momentDialog.close();
    });
    momentDialog.addEventListener('close', () => {
      momentImage.removeAttribute('src');
      returnFocus?.focus();
    });
  }

  const filterButtons = [...document.querySelectorAll('[data-filter]')];
  const cards = [...document.querySelectorAll('.project-card[data-category]')];
  const counter = document.getElementById('filterCount');
  if (filterButtons.length && cards.length) {
    filterButtons.forEach((button) => button.addEventListener('click', () => {
      const active = button.dataset.filter;
      filterButtons.forEach((item) => item.setAttribute('aria-pressed', String(item === button)));
      let visible = 0;
      cards.forEach((card) => {
        const show = active === 'all' || card.dataset.category === active;
        card.hidden = !show;
        if (show) visible += 1;
      });
      if (counter) counter.textContent = `${visible} ${visible === 1 ? counter.dataset.one : counter.dataset.many}`;
    }));
  }
}());
