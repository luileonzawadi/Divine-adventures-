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
  const closeBtn  = document.getElementById('mobile-close');
  if (!hamburger || !mobileMenu) return;

  function openMenu() {
    hamburger.classList.add('active');
    hamburger.setAttribute('aria-expanded', 'true');
    mobileMenu.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    hamburger.classList.remove('active');
    hamburger.setAttribute('aria-expanded', 'false');
    mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
  }

  hamburger.addEventListener('click', () => {
    mobileMenu.classList.contains('open') ? closeMenu() : openMenu();
  });

  if (closeBtn) closeBtn.addEventListener('click', closeMenu);

  // Close when clicking the backdrop (outside the drawer)
  mobileMenu.addEventListener('click', (e) => {
    if (e.target === mobileMenu) closeMenu();
  });

  // Close on link click
  mobileMenu.querySelectorAll('.navbar__mobile-link').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && mobileMenu.classList.contains('open')) closeMenu();
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
