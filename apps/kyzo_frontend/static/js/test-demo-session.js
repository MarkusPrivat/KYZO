/**
 * Test Demo Session Module
 * Fetches session data and renders questions for the demo test flow.
 *
 * Public API:
 *   window.initTestDemo(testId) — initializes the test demo, fetches session, renders UI.
 *
 * Usage:
 *   Called automatically from template when a valid test_id is provided.
 */

(function () {
    'use strict';

    /* ── JWT cookie extraction (private) ─────────────────────────────── */

    /**
     * Extract jwt_token from cookies and return Bearer header value.
     * @returns {string} Authorization header value or empty string if no token found.
     */
    function getAuthHeader() {
        var match = document.cookie.match(/(?:^|;\s*)jwt_token=([^;]*)/);
        return match ? 'Bearer ' + decodeURIComponent(match[1]) : '';
    }

    /* ── Session fetch (private) ─────────────────────────────────────── */

    /**
     * Fetch session data from the API.
     * @param {string} testId - The test session ID.
     * @returns {Promise<Object>} Parsed JSON response with test, next_question, all_done.
     */
    function fetchSessionData(testId) {
        var apiUrl = typeof API_URL !== 'undefined' ? API_URL : '/api/v1';
        return fetch(apiUrl + '/test/' + encodeURIComponent(testId) + '/session', {
            method: 'GET',
            headers: {
                'Authorization': getAuthHeader(),
                'Content-Type': 'application/json'
            }
        }).then(function (response) {
            if (!response.ok) {
                return response.json().catch(function () { return {}; });
            }
            return response.json();
        });
    }

    /* ── HTML escaping (private) ─────────────────────────────────────── */

    /**
     * Escape HTML special characters to prevent XSS.
     * @param {string} text
     * @returns {string}
     */
    function escapeHtml(text) {
        if (typeof text !== 'string') return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

    /* ── Module state (private) ─────────────────────────────────────── */

    var _currentTestId = null;
    var _currentQuestionId = null;
    var _questionStartTime = 0;

    /* ── Metadata rendering (private) ─────────────────────────────────── */

    /**
     * Render session metadata (subject, topic, grade).
     * @param {Object} testData - Test object from API response.
     */
    function renderMetadata(testData) {
        var container = document.getElementById('session-metadata');
        if (!container || !testData) return;

        // Fetch subject/topic names via separate lookups or use IDs as fallback
        var metadataParts = [];

        if (testData.subject_id != null) {
            metadataParts.push('<span class="demo-test__meta-item">Fach-ID: ' + escapeHtml(String(testData.subject_id)) + '</span>');
        }
        if (testData.topic_id != null) {
            metadataParts.push('<span class="demo-test__meta-item">Thema-ID: ' + escapeHtml(String(testData.topic_id)) + '</span>');
        }
        if (testData.grade != null) {
            metadataParts.push('<span class="demo-test__meta-item">Klasse: ' + escapeHtml(String(testData.grade)) + '</span>');
        }

        container.innerHTML = metadataParts.join('');
    }

    /* ── Question rendering (private) ─────────────────────────────────── */

    /**
     * Render a question with radio button options and a "Weiter" button.
     * @param {Object} question - next_question object from API response.
     */
    function renderQuestion(question) {
        var container = document.getElementById('question-container');
        if (!container || !question) return;

        // Clear previous content
        container.innerHTML = '';

        // Track current question state for finalize timing
        _currentQuestionId = question.id != null ? question.id : null;
        _questionStartTime = Date.now();

        // Question text
        var questionTextEl = document.createElement('div');
        questionTextEl.className = 'demo-test__question-text';
        questionTextEl.textContent = question.question_text || '';
        container.appendChild(questionTextEl);

        // Options list with radio buttons
        if (question.options && question.options.length > 0) {
            var optionsList = document.createElement('div');
            optionsList.className = 'demo-test__options';

            for (var i = 0; i < question.options.length; i++) {
                var option = question.options[i];
                var radioId = 'option-' + i;

                var labelEl = document.createElement('label');
                labelEl.className = 'demo-test__option-label';
                labelEl.setAttribute('for', radioId);

                var radioInput = document.createElement('input');
                radioInput.type = 'radio';
                radioInput.name = 'test-option';
                radioInput.id = radioId;
                radioInput.value = i;
                radioInput.className = 'demo-test__option-radio';

                labelEl.appendChild(radioInput);

                var optionTextSpan = document.createElement('span');
                optionTextSpan.className = 'demo-test__option-text';
                optionTextSpan.textContent = option.answer || '';
                labelEl.appendChild(optionTextSpan);

                optionsList.appendChild(labelEl);
            }

            container.appendChild(optionsList);
        }

        // Weiter button
        var weiterBtn = document.createElement('button');
        weiterBtn.type = 'button';
        weiterBtn.id = 'weiter-btn';
        weiterBtn.className = 'demo-test__weiter-btn btn-primary';
        weiterBtn.textContent = 'Weiter';
        container.appendChild(weiterBtn);

        // Weiter button — click handler sends the selected answer via POST /finalize
        (function () {
            weiterBtn.addEventListener('click', function () {
                var selectedRadio = document.querySelector('input[name="test-option"]:checked');
                if (!selectedRadio) return;

                var studentChoice = parseInt(selectedRadio.value, 10);
                var timeSpentMs = Date.now() - _questionStartTime;

                var apiUrl = typeof API_URL !== 'undefined' ? API_URL : '/api/v1';
                fetch(apiUrl + '/test/' + encodeURIComponent(_currentTestId || '') + '/question/' + encodeURIComponent(_currentQuestionId || '') + '/finalize', {
                    method: 'POST',
                    headers: {
                        'Authorization': getAuthHeader(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ student_choice: studentChoice, time_spent_milliseconds: timeSpentMs })
                }).then(function (response) {
                    if (!response.ok) throw new Error('Antwort konnte nicht gesendet werden.');
                    return response.json();
                }).then(function (data) {
                    // Re-render with next question or completion message
                    renderSessionData(data);
                }).catch(function () {
                    showToast('Fehler beim Senden der Antwort.', 'error');
                });
            });
        })();
    }

    /* ── Completion message (private) ─────────────────────────────────── */

    /**
     * Render completion message when all questions are done.
     * @param {Object} testData - Test object with score info.
     */
    function renderCompletion(testData) {
        var container = document.getElementById('completion-message');
        if (!container || !testData) return;

        var parts = [];
        parts.push('<p class="demo-test__score">Ergebnis: ' + escapeHtml(String(testData.score)) + ' / ' + escapeHtml(String(testData.max_score)) + '</p>');

        if (testData.ai_feedback_summary) {
            parts.push('<p class="demo-test__feedback">' + escapeHtml(testData.ai_feedback_summary) + '</p>');
        }

        container.innerHTML = parts.join('');
        container.style.display = 'block';
    }

    /* ── Session data rendering (private) ─────────────────────────────── */

    /**
     * Render session metadata and question from API response.
     * @param {Object} data - Full session response: { test, next_question, all_done }.
     */
    function renderSessionData(data) {
        if (!data || !data.test) return;

        // Clear previous state
        var questionContainer = document.getElementById('question-container');
        if (questionContainer) questionContainer.innerHTML = '';

        // Render metadata
        renderMetadata(data.test);

        // Check completion
        if (data.all_done === true || data.is_done === true) {
            renderCompletion(data.test);
            return;
        }

        // Render next question
        if (data.next_question) {
            renderQuestion(data.next_question);
        }
    }

    /* ── Public API ───────────────────────────────────────────────────── */

    /**
     * Initialize the test demo flow.
     * Fetches session data and renders metadata + first question automatically.
     * @param {number|string|null} testId - Test session ID from URL query parameter.
     */
    function init(testId) {
        if (!testId) return; // Guard: no test_id provided

        _currentTestId = testId;

        fetchSessionData(testId)
            .then(function (data) { renderSessionData(data); })
            .catch(function () {
                showToast('Fehler beim Laden der Session-Daten.', 'error');
            });
    }

    window.initTestDemo = init;
})();
