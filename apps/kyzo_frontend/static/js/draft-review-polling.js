/**
 * draft-review-polling.js — Polling module for draft review.
 *
 * Polls the is_processed status of a QuestionInput via the API endpoint
 * and displays a loading indicator while waiting.
 *
 * Public API:
 *   startPolling(questionInputId, onReady, onInterval, onError?)
 *   stopPolling()
 *
 * Usage:
 *   var intervalId = startPolling(42, function() { console.log('Ready!'); }, function() { console.log('Polling...'); });
 *   stopPolling();
 */

/* ── Internal state (closure — no global pollution) ─────────────────────── */

var _intervalId = null;
var _isPolling = false;

/* ── Loading indicator ──────────────────────────────────────────────────── */

/**
 * Create or show the loading indicator element.
 */
function _showLoadingIndicator() {
    var el = document.getElementById('draft-review-loading-indicator');
    if (!el) {
        el = document.createElement('div');
        el.id = 'draft-review-loading-indicator';
        el.className = 'loading-state';
        el.innerHTML = '<div class="spinner"></div> Wird generiert...';
        el.style.display = 'flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        el.style.gap = '10px';
        el.style.padding = '40px';
        el.style.color = '#6c757d';

        var container = document.getElementById('draft-questions-list');
        if (container) {
            container.appendChild(el);
        }
    } else {
        el.style.display = 'flex';
    }
}

/**
 * Hide the loading indicator element.
 */
function _hideLoadingIndicator() {
    var el = document.getElementById('draft-review-loading-indicator');
    if (el) {
        el.style.display = 'none';
    }
}

/**
 * Show an error message in the loading indicator.
 * @param {string} message
 */
function _showErrorMessage(message) {
    var el = document.getElementById('draft-review-loading-indicator');
    if (el) {
        el.style.display = 'block';
        el.style.color = '#dc3545';
        el.innerHTML = '<span>' + message + '</span>';
    }
}

/* ── Polling logic ──────────────────────────────────────────────────────── */

/**
 * Perform a single poll cycle.
 * @param {number} questionInputId
 * @param {Function} onReady
 * @param {Function} onInterval
 * @param {Function} onError
 */
function _pollOnce(questionInputId, onReady, onInterval, onError) {
    var apiUrl = typeof API_URL !== 'undefined' ? API_URL : '/api/v1';
    var url = apiUrl + '/questions/inputs/' + questionInputId;

    fetch(url, {
        method: 'GET',
        headers: { 'Authorization': 'Bearer ' + (typeof getCookie === 'function' ? getCookie('jwt_token') : '') }
    })
        .then(function (response) {
            if (!response.ok) {
                return response.json().then(function (data) {
                    throw new Error('API error: ' + (data.detail || response.status));
                });
            }
            return response.json();
        })
        .then(function (data) {
            onInterval();
            if (data.is_processed) {
                _hideLoadingIndicator();
                onReady();
                stopPolling();
            }
        })
        .catch(function (error) {
            if (_isPolling) {
                _showErrorMessage('Fehler beim Laden: ' + error.message);
                if (onError) onError(error);
                stopPolling();
            }
        });
}

/* ── Public API ─────────────────────────────────────────────────────────── */

/**
 * Start polling the is_processed status of a QuestionInput.
 * @param {number} questionInputId - The QuestionInput ID to poll
 * @param {Function} onReady - Callback when is_processed becomes true
 * @param {Function} onInterval - Callback on each poll cycle
 * @param {Function} [onError] - Optional callback on error
 * @returns {number} - The interval ID (for cleanup)
 */
function startPolling(questionInputId, onReady, onInterval, onError) {
    _isPolling = true;
    _showLoadingIndicator();

    // Poll immediately on start
    _pollOnce(questionInputId, onReady, onInterval, onError);

    _intervalId = setInterval(function () {
        if (_isPolling) {
            _pollOnce(questionInputId, onReady, onInterval, onError);
        }
    }, 2000);

    return _intervalId;
}

/**
 * Stop polling and clean up the loading indicator.
 */
function stopPolling() {
    _isPolling = false;
    if (_intervalId !== null) {
        clearInterval(_intervalId);
        _intervalId = null;
    }
    _hideLoadingIndicator();
}
