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
  if (!hamburger || !miniPopup) return;

  let isOpen = false;

  function openPopup() {
    isOpen = true;
    miniPopup.style.cssText = [
      'display: flex',
      'flex-direction: column',
      'position: absolute',
      'top: calc(100% + 8px)',
      'right: 0',
      'width: 260px',
      'max-width: calc(100vw - 1rem)',
      'background: #ffffff',
      'border-radius: 12px',
      'box-shadow: 0 8px 40px rgba(0,0,0,0.22)',
      'padding: 12px',
      'z-index: 99999',
      'gap: 4px',
      'opacity: 1',
      'pointer-events: all',
      'transform: none',
    ].join(';');
    hamburger.classList.add('active');
    hamburger.setAttribute('aria-expanded', 'true');
  }

  function closePopup() {
    isOpen = false;
    miniPopup.style.display = 'none';
    hamburger.classList.remove('active');
    hamburger.setAttribute('aria-expanded', 'false');
  }

  // Start hidden
  miniPopup.style.display = 'none';

  hamburger.addEventListener('click', (e) => {
    e.stopPropagation();
    isOpen ? closePopup() : openPopup();
  });

  // Close when clicking outside
  document.addEventListener('click', (e) => {
    if (isOpen && !hamburger.closest('.navbar__hamburger-wrap').contains(e.target)) {
      closePopup();
    }
  });

  // Close on link click
  miniPopup.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => closePopup());
  });

  // Side drawer close button
  if (closeBtn && mobileMenu) {
    closeBtn.addEventListener('click', () => {
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  }

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closePopup();
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
