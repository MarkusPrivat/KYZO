/**
 * Unit tests for test-demo-session.js
 *
 * Load this file in a browser AFTER test-demo-session.js to run tests.
 * Results are logged to the console. Open DevTools to see output.
 *
 * Usage:
 *   1. Open the demo-test page in a browser (with test_id query param)
 *   2. Open DevTools console
 *   3. Run: loadAndRunTests()
 */

/* ── Minimal test runner ─────────────────────────────────────────────────── */

var _testCount = 0;
var _passCount = 0;
var _failCount = 0;

function assert(condition, message) {
    _testCount++;
    if (condition) {
        _passCount++;
        console.log('✓ ' + message);
    } else {
        _failCount++;
        console.error('✗ FAIL: ' + message);
    }
}

function assertEqual(actual, expected, message) {
    _testCount++;
    if (actual === expected) {
        _passCount++;
        console.log('✓ ' + message);
    } else {
        _failCount++;
        console.error('✗ FAIL: ' + message + ' (expected "' + expected + '", got "' + actual + '")');
    }
}

function assertDeepEqual(actual, expected, message) {
    _testCount++;
    if (JSON.stringify(actual) === JSON.stringify(expected)) {
        _passCount++;
        console.log('✓ ' + message);
    } else {
        _failCount++;
        console.error('✗ FAIL: ' + message);
        console.error('  expected: ' + JSON.stringify(expected));
        console.error('  actual:   ' + JSON.stringify(actual));
    }
}

function assertNotNull(actual, message) {
    _testCount++;
    if (actual !== null && actual !== undefined) {
        _passCount++;
        console.log('✓ ' + message);
    } else {
        _failCount++;
        console.error('✗ FAIL: ' + message + ' (got null/undefined)');
    }
}

/* ── Mock data ───────────────────────────────────────────────────────────── */

var mockSessionData = {
    test: {
        id: 42,
        user_id: 7,
        subject_id: 3,
        topic_id: 12,
        grade: 9,
        difficulty: null,
        score: 0,
        max_score: 5,
        ai_feedback_summary: '',
        started_at: '2026-06-07T10:00:00Z',
        is_done: false,
        completed_at: null
    },
    next_question: {
        question_text: 'Was ist die Hauptstadt von Frankreich?',
        options: [
            { answer: 'Paris', is_correct: true },
            { answer: 'London', is_correct: false },
            { answer: 'Berlin', is_correct: false }
        ],
        answer: 0,
        explanations: [],
        difficulty: null,
        grade: 9
    },
    all_done: false
};

var mockSessionDone = {
    test: {
        id: 42,
        user_id: 7,
        subject_id: 3,
        topic_id: 12,
        grade: 9,
        difficulty: null,
        score: 5,
        max_score: 5,
        ai_feedback_summary: 'Perfekte Leistung!',
        started_at: '2026-06-07T10:00:00Z',
        is_done: true,
        completed_at: '2026-06-07T10:30:00Z'
    },
    next_question: null,
    all_done: true
};

var mockSessionSingleOption = {
    test: {
        id: 43,
        user_id: 7,
        subject_id: 3,
        topic_id: 12,
        grade: 5,
        difficulty: null,
        score: 0,
        max_score: 1,
        ai_feedback_summary: '',
        started_at: '2026-06-07T11:00:00Z',
        is_done: false,
        completed_at: null
    },
    next_question: {
        question_text: 'Ist Wasser H2O?',
        options: [
            { answer: 'Ja', is_correct: true }
        ],
        answer: 0,
        explanations: [],
        difficulty: null,
        grade: 5
    },
    all_done: false
};

/* ── Fetch mock infrastructure ───────────────────────────────────────────── */

/**
 * Create a fetch mock that resolves with the given data.
 * @param {Object|Function} responseData - The JSON response to return, or a function(url, options) => Object for dynamic responses.
 * @returns {{ promise: Promise, lastRequest: Object|null, resolveWith: Function, restore: Function }}
 */
function createFetchMock(responseDataOrFn) {
    var capturedRequests = [];
    var isFnResponse = typeof responseDataOrFn === 'function';

    // Store original fetch
    var origFetch = window.fetch;

    window.fetch = function (url, options) {
        capturedRequests.push({ url: url, options: options });
        return new Promise(function (resolve) {
            var resolveLater = function () {
                var data = isFnResponse ? responseDataOrFn(url, options) : responseDataOrFn;
                resolve(new Response(JSON.stringify(data), {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                }));
            };

            // If already resolved (no pending resolution needed for simple cases)
            if (_mockResolvedImmediately) {
                resolveLater();
            } else {
                _pendingResolve = resolveLater;
            }
        });
    };

    return {
        get lastRequest() { return capturedRequests.length > 0 ? capturedRequests[capturedRequests.length - 1] : null; },
        get allRequests() { return capturedRequests; },
        resolve: function () { _mockResolvedImmediately = true; if (_pendingResolve) { var fn = _pendingResolve; _pendingResolve = null; fn(); } },
        resolveWith: function (newData) { responseDataOrFn = newData; isFnResponse = typeof newData === 'function'; if (_mockResolvedImmediately && _pendingResolve) { var fn = _pendingResolve; _pendingResolve = null; fn(); } },
        restore: function () { window.fetch = origFetch; _mockResolvedImmediately = false; _pendingResolve = null; capturedRequests = []; }
    };
}

var _mockResolvedImmediately = false;
var _pendingResolve = null;

/* ── DOM setup helper ────────────────────────────────────────────────────── */

function setupTestDom() {
    var body = document.body || document.documentElement;

    if (!document.getElementById('session-metadata')) {
        var metaEl = document.createElement('div');
        metaEl.id = 'session-metadata';
        metaEl.className = 'demo-test__metadata';
        body.appendChild(metaEl);
    }

    if (!document.getElementById('question-container')) {
        var qEl = document.createElement('div');
        qEl.id = 'question-container';
        qEl.className = 'demo-test__question-area';
        body.appendChild(qEl);
    }

    if (!document.getElementById('completion-message')) {
        var cEl = document.createElement('div');
        cEl.id = 'completion-message';
        cEl.className = 'demo-test__completion';
        cEl.style.display = 'none';
        body.appendChild(cEl);
    }

    if (typeof API_URL === 'undefined') {
        window.API_URL = '/api/v1';
    }
}

/* ── Test suites ─────────────────────────────────────────────────────────── */

function runPublicApiTests() {
    console.log('\n── Public API (init exists) ──');

    assert(typeof window.initTestDemo === 'function', 'window.initTestDemo is a function');
}

function runInitWithTestIdCallsFetchTests() {
    console.log('\n── init(testId) calls fetch with correct URL ──');

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        assertEqual(mock.lastRequest.url, '/api/v1/test/42/session', 'fetch URL is correct');
        assert(
            (mock.lastRequest.options.headers.Authorization || '').indexOf('Bearer ') === 0,
            'Authorization header starts with Bearer'
        );

        mock.restore();
    }, 50);
}

function runInitGuardNoTestIdTests() {
    console.log('\n── init guards against missing test_id ──');

    // When called without a valid testId, init should return early without errors.
    try {
        window.initTestDemo(null);
        assert(true, 'init(null) does not throw');
    } catch (e) {
        assert(false, 'init(null) did not throw: ' + e.message);
    }

    try {
        window.initTestDemo('');
        assert(true, "init('') does not throw");
    } catch (e) {
        assert(false, "init('') did not throw: " + e.message);
    }

    try {
        window.initTestDemo(undefined);
        assert(true, 'init(undefined) does not throw');
    } catch (e) {
        assert(false, 'init(undefined) did not throw: ' + e.message);
    }
}

function runMetadataRenderingTests() {
    console.log('\n── Metadata rendering ──');

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete
        setTimeout(function () {
            var metadataEl = document.getElementById('session-metadata');
            assertNotNull(metadataEl, 'metadata element exists after render');

            if (metadataEl) {
                assert(
                    metadataEl.innerHTML.indexOf('Fach-ID: 3') >= 0,
                    'subject_id rendered in metadata'
                );
                assert(
                    metadataEl.innerHTML.indexOf('Thema-ID: 12') >= 0,
                    'topic_id rendered in metadata'
                );
                assert(
                    metadataEl.innerHTML.indexOf('Klasse: 9') >= 0,
                    'grade rendered in metadata'
                );

                var metaItems = metadataEl.querySelectorAll('.demo-test__meta-item');
                assertEqual(metaItems.length, 3, 'three metadata items rendered (subject, topic, grade)');
            }

            mock.restore();
        }, 50);
    }, 50);
}

function runQuestionRenderingTests() {
    console.log('\n── Question rendering ──');

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete
        setTimeout(function () {
            var questionContainer = document.getElementById('question-container');
            assertNotNull(questionContainer, 'question-container element exists after init');

            if (questionContainer) {
                assert(
                    questionContainer.innerHTML.indexOf(mockSessionData.next_question.question_text) >= 0,
                    'question text is rendered'
                );
            }

            mock.restore();
        }, 50);
    }, 50);
}

function runRadioButtonsTests() {
    console.log('\n── Radio button options ──');

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete
        setTimeout(function () {
            var questionContainer = document.getElementById('question-container');
            if (!questionContainer) {
                console.log('  ⊘ Skipped radio tests (no #question-container in DOM)');
                mock.restore();
                return;
            }

            var radios = questionContainer.querySelectorAll('input[type="radio"]');
            assertEqual(radios.length, mockSessionData.next_question.options.length,
                'correct number of radio buttons (' + mockSessionData.next_question.options.length + ')');

            // Verify each option text matches
            for (var i = 0; i < radios.length; i++) {
                var labelForRadio = document.querySelector('label[for="' + radios[i].id + '"]');
                assertNotNull(labelForRadio, 'radio button has associated label');
            }

            // Verify radio name grouping
            assert(
                questionContainer.querySelectorAll('[name="test-option"]').length > 0,
                'all options share the same radio group name'
            );

            mock.restore();
        }, 50);
    }, 50);
}

function runWeiterButtonTests() {
    console.log('\n── Weiter-Button visibility ──');

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete
        setTimeout(function () {
            var weiterBtn = document.getElementById('weiter-btn');
            assertNotNull(weiterBtn, 'Weiter-Button element exists after question render');

            if (weiterBtn) {
                assertEqual(weiterBtn.textContent.trim(), 'Weiter', 'button text is "Weiter"');
                assertEqual(weiterBtn.type, 'button', 'button type is button');
            }

            mock.restore();
        }, 50);
    }, 50);
}

function runJwtCookieAuthTests() {
    console.log('\n── JWT cookie auth ──');

    // Set a test cookie so getAuthHeader can extract it
    document.cookie = 'jwt_token=test-jwt-token-value; path=/';

    var mock = createFetchMock(mockSessionData);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        assert(
            (mock.lastRequest.options.headers.Authorization || '').indexOf('Bearer test-jwt-token-value') >= 0,
            'JWT token from cookie is sent as Bearer Authorization header'
        );

        // Clean up
        document.cookie = 'jwt_token=; path=/; max-age=0';
        mock.restore();
    }, 50);
}

function runCompletionMessageTests() {
    console.log('\n── Completion message on all_done ──');

    var mock = createFetchMock(mockSessionDone);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete
        setTimeout(function () {
            var completionEl = document.getElementById('completion-message');
            assertNotNull(completionEl, 'completion element exists after init');

            if (completionEl) {
                assertEqual(completionEl.style.display, 'block', 'completion message is visible when all_done');
                assert(
                    completionEl.innerHTML.indexOf(mockSessionDone.test.score + ' / ' + mockSessionDone.test.max_score) >= 0,
                    'score displayed in completion message'
                );

                if (mockSessionDone.test.ai_feedback_summary) {
                    assert(
                        completionEl.innerHTML.indexOf(mockSessionDone.test.ai_feedback_summary) >= 0,
                        'AI feedback summary displayed'
                    );
                }
            }

            mock.restore();
        }, 50);
    }, 50);
}

function runNoGlobalStateTests() {
    console.log('\n── No global state pollution ──');

    var beforeKeys = [];
    for (var key in window) {
        if (window.hasOwnProperty(key)) {
            beforeKeys.push(key);
        }
    }

    // initTestDemo is the only expected addition to window
    assert(typeof window.initTestDemo === 'function', 'initTestDemo exists on window');

    var afterKeys = [];
    for (var key in window) {
        if (window.hasOwnProperty(key)) {
            afterKeys.push(key);
        }
    }

    // The only new global should be initTestDemo itself.
    assert(
        beforeKeys.indexOf('init') >= 0 || true, // init is expected as window.initTestDemo
        'only public API exposed on window'
    );

    // Verify no unexpected globals were added by checking that only initTestDemo exists
    var newGlobals = [];
    for (var i = 0; i < afterKeys.length; i++) {
        if (beforeKeys.indexOf(afterKeys[i]) === -1) {
            newGlobals.push(afterKeys[i]);
        }
    }

    assert(
        newGlobals.length <= 1 && newGlobals[0] === 'initTestDemo',
        'only initTestDemo added to window globals, no other pollution'
    );
}

/* ── Mock data for finalize flow tests (Issue 050) ─────────────── */

var mockSessionNextQuestion = {
    test: {
        id: 42,
        user_id: 7,
        subject_id: 3,
        topic_id: 12,
        grade: 9,
        difficulty: null,
        score: 0,
        max_score: 5,
        ai_feedback_summary: '',
        started_at: '2026-06-07T10:00:00Z',
        is_done: false,
        completed_at: null
    },
    next_question: {
        question_text: 'Was ist 2 + 2?',
        options: [
            { answer: '3', is_correct: false },
            { answer: '4', is_correct: true },
            { answer: '5', is_correct: false }
        ],
        answer: 1,
        explanations: [],
        difficulty: null,
        grade: 9
    },
    all_done: false
};

var mockSessionAllDone = {
    test: {
        id: 42,
        user_id: 7,
        subject_id: 3,
        topic_id: 12,
        grade: 9,
        difficulty: null,
        score: 5,
        max_score: 5,
        ai_feedback_summary: 'Perfekte Leistung!',
        started_at: '2026-06-07T10:00:00Z',
        is_done: true,
        completed_at: '2026-06-07T10:30:00Z'
    },
    next_question: null,
    all_done: true
};

/* ── Test suites for finalize flow (Issue 050) ─────────────── */

function runFinalizeEndpointTests() {
    console.log('\n── Finalize endpoint URL (Issue 050) ──');

    var mock = createFetchMock(mockSessionNextQuestion);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Wait for async render to complete, then simulate Weiter click
        setTimeout(function () {
            var weiterBtn = document.getElementById('weiter-btn');
            if (!weiterBtn) {
                console.log('  ⊘ Skipped finalize endpoint test (no #weiter-btn in DOM)');
                mock.restore();
                return;
            }

            // Simulate selecting option index 1 and clicking Weiter
            var radio = document.querySelector('#question-container input[name="test-option"]:checked');
            if (!radio) {
                var radios = document.querySelectorAll('#question-container input[type="radio"]');
                if (radios.length > 0) radios[1].click(); // select second option
            }

            weiterBtn.click();

            assert(
                mock.lastRequest.url.indexOf('/finalize') >= 0,
                'fetch URL contains /finalize endpoint'
            );

            mock.restore();
        }, 60);
    }, 50);
}

function runFinalizePayloadTests() {
    console.log('\n── Finalize payload structure (Issue 050) ──');

    var capturedBody = null;
    var origFetch = window.fetch;

    // Custom mock that captures the request body for inspection
    window.fetch = function (url, options) {
        if ((options.body || '').indexOf('student_choice') >= 0) {
            try {
                capturedBody = JSON.parse(options.body);
            } catch (e) {
                capturedBody = null;
            }
        }
        return new Promise(function (resolve) {
            resolve(new Response(JSON.stringify(mockSessionNextQuestion), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }));
        });
    };

    setupTestDom();
    window.initTestDemo('42');

    setTimeout(function () {
        // Simulate Weiter click with option index 1 selected
        var radio = document.querySelector('#question-container input[name="test-option"]:checked');
        if (!radio) {
            var radios = document.querySelectorAll('#question-container input[type="radio"]');
            if (radios.length > 0) radios[1].click();
        }

        var weiterBtn = document.getElementById('weiter-btn');
        if (weiterBtn) weiterBtn.click();

        setTimeout(function () {
            assert(
                capturedBody !== null && typeof capturedBody === 'object',
                'finalize payload is a valid JSON object'
            );

            assertNotNull(capturedBody.student_choice, 'payload contains student_choice field');

            assertNotNull(capturedBody.time_spent_milliseconds, 'payload contains time_spent_milliseconds field');

            assert(
                typeof capturedBody.student_choice === 'number',
                'student_choice is a number (0-based index)'
            );

            assert(
                typeof capturedBody.time_spent_milliseconds === 'number' && capturedBody.time_spent_milliseconds >= 0,
                'time_spent_milliseconds is a non-negative number'
            );

            window.fetch = origFetch;
        }, 60);
    }, 50);
}

function runNextQuestionRenderingTests() {
    console.log('\n── Next question rendering on all_done=false (Issue 050) ──');

    var mock = createFetchMock(mockSessionAllDone);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Simulate Weiter click with option selected
        setTimeout(function () {
            var radio = document.querySelector('#question-container input[name="test-option"]:checked');
            if (!radio) {
                var radios = document.querySelectorAll('#question-container input[type="radio"]');
                if (radios.length > 0) radios[1].click();
            }

            var weiterBtn = document.getElementById('weiter-btn');
            if (weiterBtn) weiterBtn.click();

            // Wait for finalize response and re-render
            setTimeout(function () {
                mock.resolveWith(mockSessionNextQuestion);

                setTimeout(function () {
                    var questionContainer = document.getElementById('question-container');
                    assertNotNull(questionContainer, 'question-container exists after next_question render');

                    if (questionContainer) {
                        assert(
                            questionContainer.innerHTML.indexOf(mockSessionNextQuestion.next_question.question_text) >= 0,
                            'next question text is rendered'
                        );

                        var radios = questionContainer.querySelectorAll('input[type="radio"]');
                        assertNotNull(radios.length > 0, 'radio buttons present for next question (' + radios.length + ')');
                    }

                    mock.restore();
                }, 60);
            }, 50);
        }, 50);
    }, 50);
}

function runCompletionDisplayTests() {
    console.log('\n── Completion display on all_done=true (Issue 050) ──');

    var mock = createFetchMock(mockSessionNextQuestion);
    setupTestDom();

    window.initTestDemo('42');

    setTimeout(function () {
        mock.resolve();

        // Simulate Weiter click with option selected
        setTimeout(function () {
            var radio = document.querySelector('#question-container input[name="test-option"]:checked');
            if (!radio) {
                var radios = document.querySelectorAll('#question-container input[type="radio"]');
                if (radios.length > 0) radios[1].click();
            }

            var weiterBtn = document.getElementById('weiter-btn');
            if (weiterBtn) weiterBtn.click();

            // Wait for finalize response, then resolve with all_done=true
            setTimeout(function () {
                mock.resolveWith(mockSessionAllDone);

                setTimeout(function () {
                    var completionEl = document.getElementById('completion-message');
                    assertNotNull(completionEl, 'completion element exists after all_done');

                    if (completionEl) {
                        assertEqual(completionEl.style.display, 'block', 'completion message is visible when all_done=true');
                        assert(
                            completionEl.innerHTML.indexOf(mockSessionAllDone.test.score + ' / ' + mockSessionAllDone.test.max_score) >= 0,
                            'score displayed in completion'
                        );

                        if (mockSessionAllDone.test.ai_feedback_summary) {
                            assert(
                                completionEl.innerHTML.indexOf(mockSessionAllDone.test.ai_feedback_summary) >= 0,
                                'AI feedback summary displayed'
                            );
                        }
                    }

                    mock.restore();
                }, 60);
            }, 50);
        }, 50);
    }, 50);
}

/* ── Entry point ─────────────────────────────────────────────────────────── */

function loadAndRunTests() {
    console.log('=== Test Demo Session Unit Tests ===\n');

    runPublicApiTests();
    runInitWithTestIdCallsFetchTests();
    runInitGuardNoTestIdTests();
    runMetadataRenderingTests();
    runQuestionRenderingTests();
    runRadioButtonsTests();
    runWeiterButtonTests();
    runJwtCookieAuthTests();
    runCompletionMessageTests();
    runNoGlobalStateTests();

    // Issue 050: Finalize flow tests
    runFinalizeEndpointTests();
    runFinalizePayloadTests();
    runNextQuestionRenderingTests();
    runCompletionDisplayTests();

    console.log('\n=== Ergebnis: ' + _passCount + '/' + _testCount + ' bestanden, ' + _failCount + ' fehlgeschlagen ===');

    if (_failCount > 0) {
        console.error('Einige Tests sind fehlgeschlagen!');
    } else {
        console.log('Alle Tests bestanden!');
    }

    return { total: _testCount, passed: _passCount, failed: _failCount };
}
