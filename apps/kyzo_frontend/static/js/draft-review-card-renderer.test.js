/**
 * Unit tests for draft-review-card-renderer.js
 *
 * Load this file in a browser AFTER draft-review-card-renderer.js to run tests.
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

/* ── Test data ───────────────────────────────────────────────────────────── */

var sampleQuestion = {
    question_text: 'What is the capital of France?',
    options: [
        { answer: 'Paris', is_correct: true },
        { answer: 'London', is_correct: false },
        { answer: 'Berlin', is_correct: false }
    ],
    answer: 0,
    explanations: [
        { explanation: 'Paris has been the capital since 987 AD.' }
    ],
    difficulty: 5,
    grade: 10
};

var sampleQuestionNoExplanation = {
    question_text: 'What is 2 + 2?',
    options: [
        { answer: '3', is_correct: false },
        { answer: '4', is_correct: true },
        { answer: '5', is_correct: false }
    ],
    answer: 1,
    explanations: [],
    difficulty: 3,
    grade: 5
};

var sampleQuestionSingleOption = {
    question_text: 'True or False: The sky is blue.',
    options: [
        { answer: 'True', is_correct: true }
    ],
    answer: 0,
    explanations: [
        { explanation: 'Rayleigh scattering.' }
    ],
    difficulty: 1,
    grade: 3
};

var sampleQuestionNoBadges = {
    question_text: 'Test question',
    options: [
        { answer: 'A', is_correct: false },
        { answer: 'B', is_correct: true }
    ],
    answer: 1,
    explanations: [],
    difficulty: null,
    grade: null
};

/* ── Test suites ─────────────────────────────────────────────────────────── */

function runRenderCardExistsTests() {
    console.log('\n── renderCard exists ──');

    assert(typeof renderCard === 'function', 'renderCard is a function');
}

function runRenderCardReturnsElementTests() {
    console.log('\n── renderCard returns HTMLElement ──');

    var card = renderCard(sampleQuestion);
    assertNotNull(card, 'renderCard returns non-null value');
    assert(card instanceof HTMLElement, 'renderCard returns an HTMLElement');
}

function runQuestionTextTests() {
    console.log('\n── Question text displayed ──');

    var card = renderCard(sampleQuestion);
    var questionTextEl = card.querySelector('.draft-card__question-text');
    assertNotNull(questionTextEl, 'question text element exists');
    assert(questionTextEl.textContent.trim() === sampleQuestion.question_text,
        'question text matches input');
}

function runOptionsListTests() {
    console.log('\n── Options list ──');

    var card = renderCard(sampleQuestion);
    var optionsList = card.querySelector('.draft-card__options');
    assertNotNull(optionsList, 'options list element exists');

    var optionItems = optionsList.querySelectorAll('.draft-card__option');
    assertEqual(optionItems.length, sampleQuestion.options.length,
        'correct number of option items');

    for (var i = 0; i < optionItems.length; i++) {
        var optionText = optionItems[i].querySelector('.draft-card__option-text');
        assertNotNull(optionText, 'option text element exists for option ' + i);
        assertEqual(optionText.textContent.trim(), sampleQuestion.options[i].answer,
            'option ' + i + ' text matches');
    }
}

function runCorrectAnswerMarkerTests() {
    console.log('\n── Correct answer marker ──');

    var card = renderCard(sampleQuestion);
    var optionItems = card.querySelectorAll('.draft-card__option');

    // First option is correct
    assert(optionItems[0].classList.contains('draft-card__option--correct'),
        'correct option has --correct class');
    assert(!optionItems[1].classList.contains('draft-card__option--correct'),
        'incorrect option does not have --correct class');
    assert(!optionItems[2].classList.contains('draft-card__option--correct'),
        'incorrect option does not have --correct class');
}

function runExplanationTests() {
    console.log('\n── Explanation displayed after correct answer ──');

    var card = renderCard(sampleQuestion);
    var explanationEl = card.querySelector('.draft-card__explanation');
    assertNotNull(explanationEl, 'explanation element exists');
    assert(explanationEl.textContent.trim() === sampleQuestion.explanations[0].explanation,
        'explanation text matches input');
}

function runExplanationMissingTests() {
    console.log('\n── Explanation missing when no explanations ──');

    var card = renderCard(sampleQuestionNoExplanation);
    var explanationEl = card.querySelector('.draft-card__explanation');
    assert(explanationEl === null || explanationEl.textContent.trim() === '',
        'no explanation element or empty when no explanations provided');
}

function runDifficultyBadgeTests() {
    console.log('\n── Difficulty badge ──');

    var card = renderCard(sampleQuestion);
    var badgeEl = card.querySelector('.draft-card__badge--difficulty');
    assertNotNull(badgeEl, 'difficulty badge element exists');
    assert(badgeEl.textContent.trim() === 'Difficulty: 5',
        'difficulty badge text is correct');
}

function runGradeBadgeTests() {
    console.log('\n── Grade badge ──');

    var card = renderCard(sampleQuestion);
    var badgeEl = card.querySelector('.draft-card__badge--grade');
    assertNotNull(badgeEl, 'grade badge element exists');
    assert(badgeEl.textContent.trim() === 'Grade: 10',
        'grade badge text is correct');
}

function runBadgesMissingTests() {
    console.log('\n── Badges missing when null ──');

    var card = renderCard(sampleQuestionNoBadges);
    var difficultyBadge = card.querySelector('.draft-card__badge--difficulty');
    var gradeBadge = card.querySelector('.draft-card__badge--grade');
    assert(difficultyBadge === null, 'no difficulty badge when difficulty is null');
    assert(gradeBadge === null, 'no grade badge when grade is null');
}

function runSingleOptionTests() {
    console.log('\n── Single option rendering ──');

    var card = renderCard(sampleQuestionSingleOption);
    var optionItems = card.querySelectorAll('.draft-card__option');
    assertEqual(optionItems.length, 1, 'single option rendered');
    assert(optionItems[0].classList.contains('draft-card__option--correct'),
        'single correct option has --correct class');
}

function runNoGlobalStateTests() {
    console.log('\n── No global state pollution ──');

    var beforeKeys = [];
    for (var key in window) {
        if (window.hasOwnProperty(key)) {
            beforeKeys.push(key);
        }
    }

    renderCard(sampleQuestion);

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

    assert(newKeys.length === 0, 'no new global properties added by renderCard');
}

function runCardStructureTests() {
    console.log('\n── Card DOM structure ──');

    var card = renderCard(sampleQuestion);
    assert(card.classList.contains('draft-card'), 'card has draft-card class');

    var body = card.querySelector('.draft-card__body');
    assertNotNull(body, 'card has body element');

    var footer = card.querySelector('.draft-card__footer');
    assertNotNull(footer, 'card has footer element for badges');
}

function runMultipleCallsIsolationTests() {
    console.log('\n── Multiple calls produce independent cards ──');

    var card1 = renderCard(sampleQuestion);
    var card2 = renderCard(sampleQuestion);

    assert(card1 !== card2, 'each call returns a new element');
    assert(card1 !== card2, 'cards are not the same reference');

    var text1 = card1.querySelector('.draft-card__question-text').textContent;
    var text2 = card2.querySelector('.draft-card__question-text').textContent;
    assertEqual(text1, text2, 'both cards have same question text');
}

/* ── Entry point ─────────────────────────────────────────────────────────── */

function loadAndRunTests() {
    console.log('=== Draft Review Card Renderer Unit Tests ===\n');

    runRenderCardExistsTests();
    runRenderCardReturnsElementTests();
    runQuestionTextTests();
    runOptionsListTests();
    runCorrectAnswerMarkerTests();
    runExplanationTests();
    runExplanationMissingTests();
    runDifficultyBadgeTests();
    runGradeBadgeTests();
    runBadgesMissingTests();
    runSingleOptionTests();
    runNoGlobalStateTests();
    runCardStructureTests();
    runMultipleCallsIsolationTests();

    console.log('\n=== Ergebnis: ' + _passCount + '/' + _testCount + ' bestanden, ' + _failCount + ' fehlgeschlagen ===');

    if (_failCount > 0) {
        console.error('Einige Tests sind fehlgeschlagen!');
    } else {
        console.log('Alle Tests bestanden!');
    }

    return { total: _testCount, passed: _passCount, failed: _failCount };
}
