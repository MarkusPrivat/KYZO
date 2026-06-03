/**
 * Unit tests for draft-review-polling.js
 *
 * Load this file in a browser AFTER draft-review-polling.js to run tests.
 * Results are logged to the console. Open DevTools to see output.
 *
 * Usage:
 *   1. Open the draft-review page in a browser
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

/* ── Test helpers ────────────────────────────────────────────────────────── */

/**
 * Spies on a global function by replacing it with a spy that tracks calls.
 * @param {string} funcName
 * @returns {{ spy: Function, calls: Array, restore: Function }}
 */
function createSpy(funcName) {
    var original = window[funcName];
    var calls = [];
    var spy = function () {
        calls.push(Array.prototype.slice.call(arguments));
        if (original) return original.apply(this, arguments);
    };
    spy.calls = calls;
    spy.restore = function () {
        window[funcName] = original;
    };
    window[funcName] = spy;
    return { spy: spy, calls: calls, restore: spy.restore };
}

/**
 * Wait for a given number of milliseconds, returning a Promise.
 * @param {number} ms
 * @returns {Promise<void>}
 */
function wait(ms) {
    return new Promise(function (resolve) {
        setTimeout(resolve, ms);
    });
}

/**
 * Mock fetch globally for a test.
 * @param {Function} mockFn - function(url, options) => { response: { ok: boolean, json: function() => Promise<object> } }
 */
function mockFetch(mockFn) {
    window.originalFetch = window.fetch;
    window.fetch = function (url, options) {
        return Promise.resolve(mockFn(url, options));
    };
}

function restoreFetch() {
    if (window.originalFetch) {
        window.fetch = window.originalFetch;
        delete window.originalFetch;
    }
}

/* ── Test suites ─────────────────────────────────────────────────────────── */

function runStartPollingExistsTests() {
    console.log('\n── startPolling exists ──');

    assert(typeof startPolling === 'function', 'startPolling is a function');
    assert(typeof stopPolling === 'function', 'stopPolling is a function');
}

function runStartPollingReturnsIntervalIdTests() {
    console.log('\n── startPolling returns interval ID ──');

    var onReady = function () { };
    var onInterval = function () { };
    var intervalId = startPolling(1, onReady, onInterval);
    assertNotNull(intervalId, 'startPolling returns a non-null value');
    assert(typeof intervalId === 'number', 'startPolling returns a number');
}

function runPollingMakesFetchCallTests() {
    console.log('\n── startPolling triggers fetch call ──');

    var fetchCalled = false;
    var fetchUrl = '';

    mockFetch(function (url) {
        fetchCalled = true;
        fetchUrl = url;
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: true });
            }
        };
    });

    var onReady = function () { };
    var onInterval = function () { };
    startPolling(42, onReady, onInterval);

    assert(fetchCalled, 'fetch is called on startPolling');
    assert(fetchUrl.indexOf('42') !== -1, 'fetch URL contains the question input ID');

    stopPolling();
    restoreFetch();
}

function runPollingStopsWhenProcessedTests() {
    console.log('\n── Polling stops when is_processed is true ──');

    var fetchCallCount = 0;

    mockFetch(function () {
        fetchCallCount++;
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: true });
            }
        };
    });

    var onReadyCalled = false;
    var onReady = function () { onReadyCalled = true; };
    var onInterval = function () { };

    startPolling(1, onReady, onInterval);

    // Wait for at least one poll cycle
    wait(3000).then(function () {
        assert(onReadyCalled, 'onReady callback is called when is_processed becomes true');
        stopPolling();
        restoreFetch();
    });
}

function runOnIntervalCalledEachCycleTests() {
    console.log('\n── onInterval called on each poll cycle ──');

    var fetchCallCount = 0;

    mockFetch(function () {
        fetchCallCount++;
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: false });
            }
        };
    });

    var intervalCallCount = 0;
    var onInterval = function () { intervalCallCount++; };
    var onReady = function () { };

    startPolling(1, onReady, onInterval);

    // Wait for multiple poll cycles
    wait(6000).then(function () {
        assert(intervalCallCount >= 2, 'onInterval called at least twice (called ' + intervalCallCount + ' times)');
        stopPolling();
        restoreFetch();
    });
}

function runStopPollingClearsIntervalTests() {
    console.log('\n── stopPolling clears interval ──');

    var fetchCallCount = 0;

    mockFetch(function () {
        fetchCallCount++;
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: false });
            }
        };
    });

    var onReady = function () { };
    var onInterval = function () { };
    var intervalId = startPolling(1, onReady, onInterval);

    // Let one poll happen
    wait(1500).then(function () {
        var countBeforeStop = fetchCallCount;

        stopPolling();

        // Wait a bit more - fetch should not be called after stop
        wait(3000).then(function () {
            assert(fetchCallCount === countBeforeStop, 'no more fetch calls after stopPolling (before: ' + countBeforeStop + ', after: ' + fetchCallCount + ')');
            restoreFetch();
        });
    });
}

function runErrorHandlingTests() {
    console.log('\n── Error handling for network errors ──');

    mockFetch(function () {
        return Promise.reject(new Error('Network error'));
    });

    var onErrorCalled = false;
    var onError = function (error) { onErrorCalled = true; };
    var onReady = function () { };
    var onInterval = function () { };

    startPolling(1, onReady, onInterval, onError);

    wait(3000).then(function () {
        assert(onErrorCalled, 'onError callback is called on network error');
        stopPolling();
        restoreFetch();
    });
}

function runErrorHandlingApiErrorTests() {
    console.log('\n── Error handling for API errors (non-2xx) ──');

    mockFetch(function () {
        return {
            ok: false,
            status: 500,
            json: function () {
                return Promise.resolve({ detail: 'Internal server error' });
            }
        };
    });

    var onErrorCalled = false;
    var onError = function (error) { onErrorCalled = true; };
    var onReady = function () { };
    var onInterval = function () { };

    startPolling(1, onReady, onInterval, onError);

    wait(3000).then(function () {
        assert(onErrorCalled, 'onError callback is called on API error');
        stopPolling();
        restoreFetch();
    });
}

function runNoGlobalStateTests() {
    console.log('\n── No global state pollution ──');

    var beforeKeys = [];
    for (var key in window) {
        if (window.hasOwnProperty(key)) {
            beforeKeys.push(key);
        }
    }

    var onReady = function () { };
    var onInterval = function () { };
    startPolling(1, onReady, onInterval);
    stopPolling();

    var afterKeys = [];
    for (var key in window) {
        if (window.hasOwnProperty(key)) {
            afterKeys.push(key);
        }
    }

    var newKeys = [];
    for (var i = 0; i < afterKeys.length; i++) {
        var found = false;
        for (var j = 0; j < beforeKeys.length; j++) {
            if (beforeKeys[j] === afterKeys[i]) {
                found = true;
                break;
            }
        }
        if (!found) {
            newKeys.push(afterKeys[i]);
        }
    }

    assert(newKeys.length === 0, 'no new global properties added by startPolling/stopPolling');
}

function runLoadingIndicatorTests() {
    console.log('\n── Loading indicator displayed during polling ──');

    mockFetch(function () {
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: false });
            }
        };
    });

    var onReady = function () { };
    var onInterval = function () { };

    startPolling(1, onReady, onInterval);

    // Wait for at least one poll cycle
    wait(3000).then(function () {
        var loadingEl = document.getElementById('draft-review-loading-indicator');
        assert(loadingEl !== null, 'loading indicator element exists');
        assert(loadingEl.style.display !== 'none', 'loading indicator is visible');
        assert(loadingEl.textContent.indexOf('Wird generiert') !== -1, 'loading indicator shows "Wird generiert..."');
        stopPolling();
        restoreFetch();
    });
}

function runLoadingIndicatorHiddenOnReadyTests() {
    console.log('\n── Loading indicator hidden when ready ──');

    mockFetch(function () {
        return {
            ok: true,
            json: function () {
                return Promise.resolve({ id: 1, is_processed: true });
            }
        };
    });

    var onReadyCalled = false;
    var onReady = function () { onReadyCalled = true; };
    var onInterval = function () { };

    startPolling(1, onReady, onInterval);

    wait(3000).then(function () {
        if (onReadyCalled) {
            var loadingEl = document.getElementById('draft-review-loading-indicator');
            if (loadingEl) {
                assert(loadingEl.style.display === 'none' || loadingEl.style.display === '',
                    'loading indicator is hidden when ready');
            }
        }
        stopPolling();
        restoreFetch();
    });
}

/* ── Entry point ─────────────────────────────────────────────────────────── */

function loadAndRunTests() {
    console.log('=== Draft Review Polling Unit Tests ===\n');

    runStartPollingExistsTests();
    runStartPollingReturnsIntervalIdTests();
    runPollingMakesFetchCallTests();
    runPollingStopsWhenProcessedTests();
    runOnIntervalCalledEachCycleTests();
    runStopPollingClearsIntervalTests();
    runErrorHandlingTests();
    runErrorHandlingApiErrorTests();
    runNoGlobalStateTests();
    runLoadingIndicatorTests();
    runLoadingIndicatorHiddenOnReadyTests();

    console.log('\n=== Ergebnis: ' + _passCount + '/' + _testCount + ' bestanden, ' + _failCount + ' fehlgeschlagen ===');

    if (_failCount > 0) {
        console.error('Einige Tests sind fehlgeschlagen!');
    } else {
        console.log('Alle Tests bestanden!');
    }

    return { total: _testCount, passed: _passCount, failed: _failCount };
}
