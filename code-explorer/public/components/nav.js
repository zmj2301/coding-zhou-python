/* Code Explorer Shared Navigation Bar JavaScript */
(function() {
  'use strict';

  // Path to active nav mapping
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
    // Support both ce- prefixed and legacy top-nav link classes
    var links = document.querySelectorAll('.ce-top-nav-link');
    if (!links.length) {
      links = document.querySelectorAll('.top-nav-link');
    }

    if (!links.length) return;

    // Normalize: strip trailing slash for matching
    var normalizedPath = path.replace(/\/$/, '') || '/';

    // Find matching nav item
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

    // Apply active state
    links.forEach(function(link, i) {
      if (i === activeIndex) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    // Also apply to body for backward compatibility
    document.body.classList.remove('theme-dark', 'theme-light');
    document.body.classList.add('theme-' + theme);
  }

  function initThemeToggle() {
    // Support both ce- prefixed and legacy theme toggle buttons
    var btn = document.getElementById('ceThemeToggleBtn') || document.getElementById('themeToggleBtn');
    
    // Always sync theme from storage on load
    var savedTheme = localStorage.getItem('code_explorer_theme') || 'dark';
    applyTheme(savedTheme);
    
    if (!btn) return;

    btn.addEventListener('click', function() {
      var current = document.documentElement.getAttribute('data-theme') || 'dark';
      var next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('code_explorer_theme', next);
      
      // Dispatch event for other components to react
      document.dispatchEvent(new CustomEvent('themechange', { detail: { theme: next } }));
    });
  }

  function initUserMenu() {
    var btn = document.getElementById('ceUserMenuBtn') || document.getElementById('userMenuBtn');
    if (!btn) return;

    var userName = localStorage.getItem('code_explorer_user') || '';
    if (userName) {
      btn.style.display = 'flex';
      var nameEl = document.getElementById('ceUserName') || document.getElementById('userMenuName');
      if (nameEl) nameEl.textContent = userName;
    }
  }

  function initNav() {
    // Apply theme FIRST to avoid FOUC
    var savedTheme = localStorage.getItem('code_explorer_theme') || 'dark';
    applyTheme(savedTheme);
    
    setActiveNav();
    initThemeToggle();
    initUserMenu();
  }

  // Auto-insert nav if component exists
  function autoInsertNav() {
    // Check if nav already exists on page
    var existingNav = document.querySelector('.ce-top-nav') || document.querySelector('.top-nav');
    if (existingNav) {
      initNav();
      return;
    }

    // Try to fetch nav.html and insert it
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
        }
      })
      .catch(function() {
        console.warn('[CE Nav] Could not load nav.html via fetch.');
        // Still init theme even if nav can't be loaded
        var savedTheme = localStorage.getItem('code_explorer_theme') || 'dark';
        applyTheme(savedTheme);
      });
  }

  // Expose init function
  window.CENav = {
    init: initNav,
    setActive: setActiveNav,
    setTheme: function(theme) {
      applyTheme(theme);
      localStorage.setItem('code_explorer_theme', theme);
    },
    getTheme: function() {
      return document.documentElement.getAttribute('data-theme') || 'dark';
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

  // Initialize as early as possible
  function bootstrap() {
    // Apply theme immediately (before DOM ready)
    var savedTheme = localStorage.getItem('code_explorer_theme') || 'dark';
    applyTheme(savedTheme);
    
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoInsertNav);
    } else {
      autoInsertNav();
    }
  }

  // Run bootstrap
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
  
  // Also apply theme ASAP even before DOMContentLoaded
  var earlyTheme = localStorage.getItem('code_explorer_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', earlyTheme);
})();
