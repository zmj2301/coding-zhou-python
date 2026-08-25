/* Code Explorer Shared Navigation Bar JavaScript */
(function() {
  'use strict';

  var NAV_MAP = {
    '/': 0,
    '/console': 1,
    '/resources': 2,
    '/web-games': 3,
    '/scratch': 4,
    '/python': 5,
    '/run/local': 6
  };

  function getCurrentPath() {
    return window.location.pathname;
  }

  function setActiveNav() {
    var path = getCurrentPath();
    var links = document.querySelectorAll('.ce-top-nav-link');
    if (!links.length) {
      links = document.querySelectorAll('.top-nav-link');
    }
    var normalizedPath = path.replace(/\/$/, '') || '/';
    var activeIndex = -1;
    var bestMatchLen = 0;
    Object.keys(NAV_MAP).forEach(function(key) {
      if (key === '/') {
        if (normalizedPath === '/' || normalizedPath === '') {
          activeIndex = NAV_MAP[key];
          bestMatchLen = key.length;
        }
      } else if (normalizedPath === key || normalizedPath.startsWith(key + '/')) {
        if (key.length > bestMatchLen) {
          activeIndex = NAV_MAP[key];
          bestMatchLen = key.length;
        }
      }
    });
    links.forEach(function(link, i) {
      if (i === activeIndex) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  function initThemeToggle() {
    var btn = document.getElementById('ceThemeToggleBtn') || document.getElementById('themeToggleBtn');
    if (!btn) return;
    var savedTheme = localStorage.getItem('code_explorer_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    btn.addEventListener('click', function() {
      var current = document.documentElement.getAttribute('data-theme') || 'dark';
      var next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('code_explorer_theme', next);
    });
  }

  function initUserMenu() {
    var btn = document.getElementById('ceUserMenuBtn') || document.getElementById('userMenuBtn');
    if (!btn) return;
    var userName = localStorage.getItem('code_explorer_user') || '';
    if (userName) {
      btn.style.display = 'flex';
      var nameEl = document.getElementById('ceUserName');
      if (nameEl) nameEl.textContent = userName;
    }
  }

  function initChangelogBtn() {
    var btn = document.getElementById('ceChangelogBtn');
    if (!btn) return;
    btn.addEventListener('click', function() {
      if (window.location.pathname === '/') {
        if (typeof openChangelogModal === 'function') {
          openChangelogModal();
        }
      } else {
        window.location.href = '/';
      }
    });
  }

  function initNav() {
    setActiveNav();
    initThemeToggle();
    initUserMenu();
    initChangelogBtn();
  }

  function autoInsertNav() {
    var existingNav = document.querySelector('.ce-top-nav') || document.querySelector('.top-nav');
    if (existingNav) {
      initNav();
      document.dispatchEvent(new CustomEvent('nav:ready'));
      return;
    }
    fetch('/components/nav.html')
      .then(function(r) { return r.ok ? r.text() : Promise.reject('Nav not found'); })
      .then(function(html) {
        var div = document.createElement('div');
        div.innerHTML = html.trim();
        if (div.firstChild) {
          var body = document.body;
          if (body.firstChild) {
            body.insertBefore(div.firstChild, body.firstChild);
          } else {
            body.appendChild(div.firstChild);
          }
          document.body.classList.add('ce-has-nav');
          initNav();
          document.dispatchEvent(new CustomEvent('nav:ready'));
        }
      })
      .catch(function() {
        console.warn('[CE Nav] Could not load nav.html via fetch. Skipping auto-insert.');
        document.dispatchEvent(new CustomEvent('nav:ready'));
      });
  }

  window.CENav = {
    init: initNav,
    setActive: setActiveNav,
    setTheme: function(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('code_explorer_theme', theme);
    },
    setUser: function(name) {
      localStorage.setItem('code_explorer_user', name);
      var btn = document.getElementById('ceUserMenuBtn') || document.getElementById('userMenuBtn');
      if (btn) {
        btn.style.display = name ? 'flex' : 'none';
        var nameEl = document.getElementById('ceUserName') || document.getElementById('userMenuName');
        if (nameEl) nameEl.textContent = name || '用户';
      }
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInsertNav);
  } else {
    autoInsertNav();
  }
})();