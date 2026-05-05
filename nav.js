// Shared navigation — included by every page
// Detects current page and highlights active link
(function() {
  const path = window.location.pathname;
  const pages = [
    { href: '/',             label: 'Matteo.' },
    { href: '/professional', label: 'Professional' },
    { href: '/training',     label: 'Training' },
    { href: '/genealogy',    label: 'Genealogy' },
    { href: '/italian',      label: 'Italian' },
    { href: '/wine',         label: 'Wine' },
    { href: '/news',         label: 'News' },
  ];

  function isActive(href) {
    if (href === '/') return path === '/' || path === '/index.html';
    return path.startsWith(href);
  }

  const nav = document.createElement('nav');
  nav.id = 'site-nav';
  nav.innerHTML = `
    <div class="nav-inner">
      <a href="/" class="nav-logo">Matteo<span>.</span></a>
      <div class="nav-links">
        ${pages.slice(1).map(p => `
          <a href="${p.href}" class="nav-link${isActive(p.href) ? ' active' : ''}">${p.label}</a>
        `).join('')}
      </div>
      <button class="nav-mobile-toggle" onclick="document.getElementById('site-nav').classList.toggle('open')" aria-label="Menu">
        <span></span><span></span><span></span>
      </button>
    </div>
    <div class="nav-mobile-menu">
      ${pages.slice(1).map(p => `
        <a href="${p.href}" class="nav-mobile-link${isActive(p.href) ? ' active' : ''}">${p.label}</a>
      `).join('')}
    </div>
  `;

  // Insert as first child of body
  document.body.insertBefore(nav, document.body.firstChild);
})();
