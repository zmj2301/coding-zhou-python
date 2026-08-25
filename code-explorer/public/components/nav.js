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

    // Normalize: strip trailing slash for matching
    var normalizedPath = path.replace(/\/$/, '') || '/';

    // Find matching nav item
    var activeIndex = -1;
    var bestMatchLen = 0;

    Object.keys(NAV_MAP).forEach(function(key) {
      if (key === '/') {
        // Home matches exactly '/' or empty
        if (normalizedPath === '/' || normalizedPath === '') {
          activeIndex = NAV_MAP[key];
          bestMatchLen = key.length;
        }
      } else if (normalizedPath === key || normalizedPath.startsWith(key + '/')) {
        // Longer matches take priority
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

  function initThemeToggle() {
    // Support both ce- prefixed and legacy theme toggle buttons
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
      btn.classList.remove('hidden');
      btn.style.display = 'flex';
      var nameEl = document.getElementById('ceUserName') || document.getElementById('userMenuName');
      if (nameEl) nameEl.textContent = userName;
    } else {
      // 无本地用户信息时也显示按钮，允许点击展开常用菜单项
      btn.classList.remove('hidden');
      btn.style.display = 'flex';
    }

    var dropdown = document.getElementById('userDropdown');
    // 绑定用户按钮的下拉展开
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      if (dropdown) dropdown.classList.toggle('show');
    });
    // 点击页面其它区域关闭下拉
    document.addEventListener('click', function() {
      if (dropdown) dropdown.classList.remove('show');
    });
    if (dropdown) {
      dropdown.addEventListener('click', function(e) {
        e.stopPropagation();
      });
    }

    // 绑定五个菜单项
    var profileBtn = document.getElementById('profileFromMenu');
    if (profileBtn) {
      profileBtn.addEventListener('click', function() {
        window.location.href = '/profile';
      });
    }
    var feedbackBtn = document.getElementById('openFeedbackMenu');
    if (feedbackBtn) {
      feedbackBtn.addEventListener('click', function() {
        window.location.href = '/feedback';
      });
    }
    var adminBtn = document.getElementById('openAdminFromMenu');
    if (adminBtn) {
      adminBtn.addEventListener('click', function() {
        if (typeof showAdminDashboard === 'function') {
          showAdminDashboard();
        } else {
          window.location.href = '/console#admin';
        }
      });
    }
    var inboxBtn = document.getElementById('openInboxMenu');
    if (inboxBtn) {
      inboxBtn.addEventListener('click', function() {
        window.location.href = '/feedback?view=inbox';
      });
    }
    var logoutBtn = document.getElementById('logoutFromMenu');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function() {
        if (typeof doLogout === 'function') {
          doLogout();
        } else {
          try {
            localStorage.removeItem('code_explorer_user');
            document.cookie = 'wg_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax';
            fetch('/api/logout', { method: 'POST', credentials: 'include' }).catch(function() {});
          } catch (_) {}
          window.location.href = '/';
        }
      });
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

  // Auto-insert nav if component exists
  function autoInsertNav() {
    // Check if nav already exists on page (supports both ce- prefixed and legacy top-nav)
    var existingNav = document.querySelector('.ce-top-nav') || document.querySelector('.top-nav');
    if (existingNav) {
      initNav();
      // Dispatch nav:ready event after nav is initialized
      document.dispatchEvent(new CustomEvent('nav:ready'));
      return;
    }

    // Try to fetch nav.html and insert it
    fetch('/components/nav.html')
      .then(function(r) { return r.ok ? r.text() : Promise.reject('Nav not found'); })
      .then(function(html) {
        var div = document.createElement('div');
        div.innerHTML = html.trim();
        if (div.firstChild) {
          // Insert after <body> opening tag
          var body = document.body;
          if (body.firstChild) {
            body.insertBefore(div.firstChild, body.firstChild);
          } else {
            body.appendChild(div.firstChild);
          }
          document.body.classList.add('ce-has-nav');
          initNav();
          // Dispatch nav:ready event after nav is fully initialized
          document.dispatchEvent(new CustomEvent('nav:ready'));
        }
      })
      .catch(function() {
        // If fetch fails (e.g. file:// protocol), try inline approach
        console.warn('[CE Nav] Could not load nav.html via fetch. Skipping auto-insert.');
        // Still dispatch nav:ready to allow fallback initialization
        document.dispatchEvent(new CustomEvent('nav:ready'));
      });
  }

  // Expose init function
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

  // Auto-initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInsertNav);
  } else {
    autoInsertNav();
  }
})();