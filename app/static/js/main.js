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
  const mobileMenu = document.getElementById('mobile-menu');
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    mobileMenu.classList.toggle('open');
    document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
  });

  // Close mobile menu when clicking a link
  const mobileLinks = mobileMenu.querySelectorAll('.navbar__link');
  mobileLinks.forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('active');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // Close on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
      hamburger.classList.remove('active');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
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
