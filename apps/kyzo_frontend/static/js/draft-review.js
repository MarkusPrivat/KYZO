/**
 * draft-review.js — Draft Review Page controller.
 *
 * Integrates DraftReviewCardRenderer, DraftReviewPolling, and toast
 * into the draft_review.html template.
 *
 * Public API:
 *   window.renderDraftReview(questionInputId)
 *
 * Usage:
 *   Loaded automatically by draft_review.html template.
 */

(function () {
    'use strict';

    var _questionInputId = null;
    var _isProcessed = false;

    /* ── Helpers ─────────────────────────────────────────────────────────── */

    /**
     * Escape HTML special characters to prevent XSS.
     * @param {string} text
     * @returns {string}
     */
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text || ''));
        return div.innerHTML;
    }

    /**
     * Get auth header value from cookie.
     * @returns {string}
     */
    function getAuthHeader() {
        var token = getCookie('jwt_token');
        return token ? 'Bearer ' + token : '';
    }

    /**
     * Get cookie by name.
     * @param {string} name
     * @returns {string}
     */
    function getCookie(name) {
        var match = document.cookie.match(
            new RegExp('(?:^|;\\s*)' + name + '=([^;]*)')
        );
        return match ? match[1] : '';
    }

    /* ── Metadata rendering ──────────────────────────────────────────────── */

    /**
     * Render metadata section from QuestionInput data.
     * @param {Object} data
     */
    function renderMetadata(data) {
        var subjectEl = document.getElementById('metadata-subject');
        var topicEl = document.getElementById('metadata-topic');
        var gradeEl = document.getElementById('metadata-grade');
        var inputTypeEl = document.getElementById('metadata-input-type');
        var numQuestionsEl = document.getElementById('metadata-num-questions');

        if (subjectEl) subjectEl.textContent = data.subject || '—';
        if (topicEl) topicEl.textContent = data.topic || '—';
        if (gradeEl) gradeEl.textContent = data.grade != null ? String(data.grade) : '—';
        if (inputTypeEl) inputTypeEl.textContent = data.input_type || '—';
        if (numQuestionsEl) {
            numQuestionsEl.textContent =
                data.extracted_questions && data.extracted_questions.length > 0
                    ? String(data.extracted_questions.length)
                    : '0';
        }
    }

    /* ── RAWInput Accordion ──────────────────────────────────────────────── */

    /**
     * Render the RAWInput accordion content.
     * @param {Object} rawInput - raw_input object from API
     */
    function renderRawInputAccordion(rawInput) {
        if (!rawInput) return;

        var placeholder = document.getElementById('rawinput-placeholder');
        if (!placeholder) return;

        // Show file info for uploads
        if (rawInput.source_ref) {
            var fileInfo = document.createElement('div');
            fileInfo.className = 'rawinput-file-info';
            fileInfo.style.marginBottom = '8px';
            fileInfo.style.fontSize = '0.85rem';
            fileInfo.style.color = '#6c757d';

            var fileName = document.createElement('strong');
            fileName.textContent = rawInput.source_ref;
            fileInfo.appendChild(fileName);

            if (rawInput.file_size) {
                var sizeSpan = document.createElement('span');
                sizeSpan.textContent = ' (' + rawInput.file_size + ')';
                fileInfo.appendChild(sizeSpan);
            }

            if (rawInput.file_type) {
                var typeSpan = document.createElement('span');
                typeSpan.textContent = ' — Typ: ' + rawInput.file_type;
                fileInfo.appendChild(typeSpan);
            }

            placeholder.innerHTML = '';
            placeholder.appendChild(fileInfo);
        }

        // Show content
        if (rawInput.content) {
            var contentEl = document.createElement('div');
            contentEl.style.whiteSpace = 'pre-wrap';
            contentEl.style.wordBreak = 'break-word';
            contentEl.style.fontFamily = "'Courier New', monospace";
            contentEl.style.fontSize = '0.9rem';
            contentEl.style.color = '#495057';
            contentEl.style.maxHeight = '300px';
            contentEl.style.overflowY = 'auto';
            contentEl.style.resize = 'vertical';
            contentEl.textContent = rawInput.content;
            placeholder.appendChild(contentEl);
        }
    }

    /* ── RAWInput accordion toggle ───────────────────────────────────────── */

    /**
     * Initialize the RAWInput accordion toggle button.
     */
    function initRawInputAccordion() {
        var toggle = document.querySelector('.card-header__toggle');
        var content = document.getElementById('rawinput-content');
        if (!toggle || !content) return;

        toggle.addEventListener('click', function () {
            var expanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!expanded));
            content.style.display = expanded ? 'none' : 'block';
        });
    }

    /* ── Draft-Fragen-Karten ─────────────────────────────────────────────── */

    /**
     * Render all draft question cards.
     * @param {Array} questions - Array of QuestionInputExtractedQuestions
     */
    function renderDraftCards(questions) {
        var container = document.getElementById('draft-questions-list');
        if (!container) return;

        // Clear loading state
        container.innerHTML = '';

        if (!questions || questions.length === 0) {
            var emptyEl = document.createElement('div');
            emptyEl.className = 'loading-state';
            emptyEl.textContent = 'Keine Draft-Fragen gefunden.';
            container.appendChild(emptyEl);
            return;
        }

        // Max 25 questions, no pagination
        var limited = questions.slice(0, 25);
        for (var i = 0; i < limited.length; i++) {
            var card = renderCard(limited[i]);
            container.appendChild(card);
        }
    }

    /* ── Finalize-Button ─────────────────────────────────────────────────── */

    /**
     * Setup the finalize button behavior.
     * @param {number} questionInputId
     * @param {boolean} isProcessed
     */
    function setupFinalizeButton(questionInputId, isProcessed) {
        var btn = document.getElementById('finalize-btn');
        if (!btn) return;

        if (isProcessed) {
            btn.disabled = true;
            btn.textContent = 'Bereits verarbeitet';
            var notice = document.createElement('p');
            notice.style.marginTop = '8px';
            notice.style.fontSize = '0.85rem';
            notice.style.color = '#6c757d';
            notice.textContent = 'Dieser Input wurde bereits verarbeitet.';
            var actions = document.getElementById('finalize-actions');
            if (actions) actions.appendChild(notice);
            return;
        }

        btn.addEventListener('click', function () {
            finalizeQuestionInput(questionInputId);
        });
    }

    /**
     * Finalize the QuestionInput via POST.
     * @param {number} questionInputId
     */
    function finalizeQuestionInput(questionInputId) {
        var btn = document.getElementById('finalize-btn');
        if (!btn) return;

        btn.disabled = true;
        btn.textContent = 'Wird übernommen...';

        var apiUrl = typeof API_URL !== 'undefined' ? API_URL : '/api/v1';
        var url = apiUrl + '/questions/inputs/' + questionInputId + '/finalize';

        fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': getAuthHeader(),
                'Content-Type': 'application/json'
            }
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (response.ok) {
                        var count = data.questions_added || 0;
                        var msg = count + ' Fragen wurden in den Katalog übernommen.';
                        showToast(msg, 'success');
                        // Reload page to reflect is_processed state
                        setTimeout(function () {
                            location.reload();
                        }, 2000);
                    } else {
                        var errorMsg = 'Fehler beim Finalize: ' + (data.detail || 'Unbekannter Fehler');
                        showToast(errorMsg, 'error');
                        // Re-enable button on error
                        btn.disabled = false;
                        btn.textContent = 'Fragen übernehmen';
                    }
                });
            })
            .catch(function (err) {
                showToast('Fehler beim Finalize: ' + err.message, 'error');
                btn.disabled = false;
                btn.textContent = 'Fragen übernehmen';
            });
    }

    /* ── Page initialization ─────────────────────────────────────────────── */

    /**
     * Initialize the draft review page.
     * @param {number} questionInputId
     */
    function renderDraftReview(questionInputId) {
        _questionInputId = questionInputId;

        // Start polling
        DraftReviewPolling.startPolling(
            questionInputId,
            function onReady(data) {
                // Render everything when polling completes
                renderMetadata(data);
                renderRawInputAccordion(data.raw_input);
                renderDraftCards(data.extracted_questions);
                setupFinalizeButton(questionInputId, data.is_processed);
                initRawInputAccordion();
            },
            function onInterval() {
                // Update loading indicator (handled by polling module)
            }
        );
    }

    /* ── Public API ──────────────────────────────────────────────────────── */

    window.renderDraftReview = renderDraftReview;

    /* ── Auto-init on DOMContentLoaded ───────────────────────────────────── */

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            var container = document.querySelector('.admin-draft-review');
            if (!container) return;
            var id = parseInt(container.dataset.questionInputId, 10);
            if (id) {
                renderDraftReview(id);
            }
        });
    } else {
        var container = document.querySelector('.admin-draft-review');
        if (container) {
            var id = parseInt(container.dataset.questionInputId, 10);
            if (id) {
                renderDraftReview(id);
            }
        }
    }
})();
