/**
 * Kyzo Frontend — Navigation Toggle (Hamburger Menu)
 * Mobile menu toggle with keyboard support and escape key handling.
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var hamburger = document.querySelector('.nav__hamburger');
    var mobileMenu = document.querySelector('.nav__mobile-menu');

    if (!hamburger || !mobileMenu) {
      return;
    }

    /**
     * Toggle the mobile menu open/closed state
     */
    function toggleMenu() {
      var isOpen = hamburger.getAttribute('aria-expanded') === 'true';
      hamburger.setAttribute('aria-expanded', String(!isOpen));
      hamburger.setAttribute(
        'aria-label',
        isOpen ? 'Menü öffnen' : 'Menü schließen'
      );
      mobileMenu.classList.toggle('is-open');
    }

    /**
     * Close the mobile menu
     */
    function closeMenu() {
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.setAttribute('aria-label', 'Menü öffnen');
      mobileMenu.classList.remove('is-open');
    }

    // Toggle on hamburger click
    hamburger.addEventListener('click', toggleMenu);

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileMenu.classList.contains('is-open')) {
        closeMenu();
        hamburger.focus();
      }
    });

    // Close when clicking outside
    document.addEventListener('click', function (e) {
      if (
        mobileMenu.classList.contains('is-open') &&
        !mobileMenu.contains(e.target) &&
        !hamburger.contains(e.target)
      ) {
        closeMenu();
      }
    });

    // Close mobile menu when resizing to desktop (>= 768px)
    var mediaQuery = window.matchMedia('(min-width: 768px)');
    mediaQuery.addEventListener('change', function (e) {
      if (e.matches) {
        closeMenu();
      }
    });

    // Check initial state
    if (mediaQuery.matches) {
      closeMenu();
    }
  });
})();
