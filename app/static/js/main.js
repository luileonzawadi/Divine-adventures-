/**
 * Devine Adventures — Main JavaScript
 * Handles navbar scroll behavior, mobile menu, and flash messages.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initMobileMenu();
  initFlashMessages();
  initSmoothScroll();
});

/* ============================================
   NAVBAR — Transparent to Solid on Scroll
   ============================================ */
function initNavbar() {
  const navbar = document.getElementById('main-nav');
  if (!navbar) return;

  const SCROLL_THRESHOLD = 50;
  let ticking = false;

  function updateNavbar() {
    if (window.scrollY > SCROLL_THRESHOLD) {
      navbar.classList.add('navbar--solid');
    } else {
      navbar.classList.remove('navbar--solid');
    }
    ticking = false;
  }

  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(updateNavbar);
      ticking = true;
    }
  }, { passive: true });

  // Initial check in case page is already scrolled
  updateNavbar();
}

/* ============================================
   MOBILE MENU
   ============================================ */
function initMobileMenu() {
  const hamburger = document.getElementById('navbar-hamburger');
  const miniPopup  = document.getElementById('navbar-mini-popup');
  const mobileMenu = document.getElementById('mobile-menu');
  const closeBtn   = document.getElementById('mobile-close');
  if (!hamburger) return;

  // Toggle mini popup on hamburger click
  hamburger.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = miniPopup.classList.toggle('open');
    hamburger.classList.toggle('active', isOpen);
    hamburger.setAttribute('aria-expanded', String(isOpen));

    if (isOpen) {
      // Position popup below the hamburger button
      const rect = hamburger.getBoundingClientRect();
      miniPopup.style.top = (rect.bottom + 10) + 'px';
      miniPopup.style.right = (window.innerWidth - rect.right) + 'px';
    }
  });

  // Close mini popup when clicking outside
  document.addEventListener('click', (e) => {
    if (!hamburger.closest('.navbar__hamburger-wrap').contains(e.target)) {
      miniPopup.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });

  // Close mini popup on link click
  if (miniPopup) {
    miniPopup.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        miniPopup.classList.remove('open');
        hamburger.classList.remove('active');
      });
    });
  }

  // Side drawer close button (keep for fallback)
  if (closeBtn && mobileMenu) {
    closeBtn.addEventListener('click', () => {
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  }

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      miniPopup && miniPopup.classList.remove('open');
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });
}

/* ============================================
   FLASH MESSAGES — Auto-dismiss
   ============================================ */
function initFlashMessages() {
  const flashMessages = document.querySelectorAll('.flash-message');

  flashMessages.forEach(msg => {
    // Auto-dismiss after 5 seconds
    const timer = setTimeout(() => {
      dismissFlash(msg);
    }, 5000);

    // Close button
    const closeBtn = msg.querySelector('.flash-message__close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        clearTimeout(timer);
        dismissFlash(msg);
      });
    }
  });
}

function dismissFlash(element) {
  element.style.animation = 'fadeOut 0.3s ease-out forwards';
  setTimeout(() => {
    element.remove();
  }, 300);
}

/* ============================================
   SMOOTH SCROLL
   ============================================ */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href');
      if (targetId === '#') return;

      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        const navbarHeight = document.getElementById('main-nav')?.offsetHeight || 80;
        const targetPosition = target.getBoundingClientRect().top + window.scrollY - navbarHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}
