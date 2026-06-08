// Shared navigation — included by every page
// Detects current page and highlights active link
(function() {
  const path = window.location.pathname;
  const pages = [
    { href: '/',             label: 'Matthew.' },
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
    <style>
      .nav-logo-name {
        position: relative;
        display: inline-block;
      }
      .nav-logo-name .primary {
        display: inline;
        transition: opacity 0.3s ease;
      }
      .nav-logo-name .personal {
        position: absolute;
        left: 0; top: 0;
        opacity: 0;
        white-space: nowrap;
        transition: opacity 0.35s ease, transform 0.35s ease;
        transform: translateY(3px);
      }
      .nav-logo:hover .nav-logo-name .primary { opacity: 0; }
      .nav-logo:hover .nav-logo-name .personal {
        opacity: 1;
        transform: translateY(0);
      }
    </style>
    <div class="nav-inner">
      <a href="/" class="nav-logo" title="Also known as Matteo">
        <span class="nav-logo-name">
          <span class="primary">Matthew<span>.</span></span>
          <span class="personal">Matteo<span>.</span></span>
        </span>
      </a>
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
