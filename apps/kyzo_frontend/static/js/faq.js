/**
 * Kyzo Frontend — FAQ Accordion
 * Vanilla JS accordion with ARIA attributes and keyboard support.
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var faqButtons = document.querySelectorAll('.faq-item__question');

    if (!faqButtons.length) {
      return;
    }

    /**
     * Toggle a single FAQ item open/closed
     * @param {HTMLElement} button - The button element
     */
    function toggleItem(button) {
      var answerId = button.getAttribute('aria-controls');
      var answer = document.getElementById(answerId);

      if (!answer) return;

      var isExpanded = button.getAttribute('aria-expanded') === 'true';

      if (isExpanded) {
        // Close
        button.setAttribute('aria-expanded', 'false');
        answer.setAttribute('hidden', '');
        answer.classList.remove('is-open');
      } else {
        // Open
        button.setAttribute('aria-expanded', 'true');
        answer.removeAttribute('hidden');
        answer.classList.add('is-open');
      }
    }

    /**
     * Close all FAQ items
     */
    function closeAll() {
      for (var i = 0; i < faqButtons.length; i++) {
        var btn = faqButtons[i];
        var answerId = btn.getAttribute('aria-controls');
        var answer = document.getElementById(answerId);
        if (answer) {
          btn.setAttribute('aria-expanded', 'false');
          answer.setAttribute('hidden', '');
          answer.classList.remove('is-open');
        }
      }
    }

    for (var i = 0; i < faqButtons.length; i++) {
      var btn = faqButtons[i];

      // Click handler
      btn.addEventListener('click', function () {
        toggleItem(this);
      });

      // Keyboard support
      btn.addEventListener('keydown', function (e) {
        var index = Array.prototype.indexOf.call(faqButtons, this);

        switch (e.key) {
          case 'Enter':
          case ' ':
            e.preventDefault();
            toggleItem(this);
            break;

          case 'Escape':
            if (this.getAttribute('aria-expanded') === 'true') {
              e.preventDefault();
              closeAll();
              this.focus();
            }
            break;

          case 'ArrowDown':
            e.preventDefault();
            var next = (index + 1) % faqButtons.length;
            faqButtons[next].focus();
            break;

          case 'ArrowUp':
            e.preventDefault();
            var prev = (index - 1 + faqButtons.length) % faqButtons.length;
            faqButtons[prev].focus();
            break;

          case 'Home':
            e.preventDefault();
            faqButtons[0].focus();
            break;

          case 'End':
            e.preventDefault();
            faqButtons[faqButtons.length - 1].focus();
            break;
        }
      });
    }
  });
})();
