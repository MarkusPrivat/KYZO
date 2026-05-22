/**
 * Toast Notification System
 * Reusable toast notifications for the admin panel.
 * Displays success (green) and error (red/orange) toasts
 * stacked at the top-right of the viewport.
 */

(function () {
    'use strict';

    const TOAST_DURATION = 3000;
    const MAX_VISIBLE = 3;
    const FADE_IN = 200;
    const FADE_OUT = 300;

    let toastQueue = [];
    let activeToasts = [];

    /**
     * Show a toast notification.
     * @param {string} message - The message to display.
     * @param {string} [type='success'] - 'success' or 'error'.
     */
    window.showToast = function (message, type) {
        if (typeof type !== 'string') type = 'success';

        const toast = createToastElement(message, type);
        activeToasts.push(toast);
        repositionToasts();

        // Fade in
        requestAnimationFrame(function () {
            toast.style.opacity = '1';
        });

        // Click to dismiss
        toast.addEventListener('click', function () {
            dismissToast(toast);
        });

        // Auto-dismiss
        toast._timer = setTimeout(function () {
            dismissToast(toast);
        }, TOAST_DURATION);
    };

    /**
     * Create a toast DOM element.
     */
    function createToastElement(message, type) {
        const container = getOrCreateContainer();

        const toast = document.createElement('div');
        toast.className = 'toast toast--' + type;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');
        toast.textContent = message;
        toast.style.opacity = '0';

        container.appendChild(toast);
        return toast;
    }

    /**
     * Get or create the toast container.
     */
    function getOrCreateContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Dismiss a single toast.
     */
    function dismissToast(toast) {
        if (toast._dismissed) return;
        toast._dismissed = true;

        clearTimeout(toast._timer);
        toast.style.opacity = '0';

        setTimeout(function () {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            var idx = activeToasts.indexOf(toast);
            if (idx !== -1) activeToasts.splice(idx, 1);
            repositionToasts();
        }, FADE_OUT);
    }

    /**
     * Reposition all active toasts so they stack vertically.
     */
    function repositionToasts() {
        var visible = activeToasts.filter(function (t) { return !t._dismissed; });
        // Keep only the top MAX_VISIBLE
        if (visible.length > MAX_VISIBLE) {
            visible.slice(0, visible.length - MAX_VISIBLE).forEach(function (t) {
                dismissToast(t);
            });
            visible = activeToasts.filter(function (t) { return !t._dismissed; });
        }
        visible.forEach(function (toast, i) {
            toast.style.top = (16 + i * 64) + 'px';
        });
    }
})();
