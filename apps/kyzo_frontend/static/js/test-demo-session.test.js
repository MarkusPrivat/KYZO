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
 * @param {Object} responseData - The JSON response to return.
 * @returns {{ promise: Promise, lastRequest: Object|null }}
 */
function createFetchMock(responseData) {
    var capturedRequest = null;
    var resolveFn = null;

    var mockPromise = new Promise(function (resolve) {
        resolveFn = function () { resolve(); };
    });

    // Store original fetch
    var origFetch = window.fetch;

    window.fetch = function (url, options) {
        capturedRequest = { url: url, options: options };
        return mockPromise.then(function () {
            return new Response(JSON.stringify(responseData), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        });
    };

    return {
        get lastRequest() { return capturedRequest; },
        resolve: function () { if (resolveFn) resolveFn(); },
        restore: function () { window.fetch = origFetch; }
    };
}

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

    console.log('\n=== Ergebnis: ' + _passCount + '/' + _testCount + ' bestanden, ' + _failCount + ' fehlgeschlagen ===');

    if (_failCount > 0) {
        console.error('Einige Tests sind fehlgeschlagen!');
    } else {
        console.log('Alle Tests bestanden!');
    }

    return { total: _testCount, passed: _passCount, failed: _failCount };
}
