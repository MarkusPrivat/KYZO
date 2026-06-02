/**
 * Unit tests for question-input.js validation functions.
 *
 * Load this file in a browser AFTER question-input.js to run tests.
 * Results are logged to the console. Open DevTools to see output.
 *
 * Usage:
 *   1. Open the question-input page in a browser
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

/* ── Test suites ─────────────────────────────────────────────────────────── */

function runValidateSubjectTests() {
    console.log('\n── validateSubject ──');

    assert(validateSubject(1).valid === true, 'valid subject ID returns valid');
    assert(validateSubject(42).valid === true, 'large valid subject ID returns valid');
    assert(validateSubject(0).valid === false, 'subject ID 0 returns invalid');
    assert(validateSubject(-1).valid === false, 'negative subject ID returns invalid');
    assert(validateSubject('').valid === false, 'empty string returns invalid');
    assert(validateSubject(null).valid === false, 'null returns invalid');
    assert(validateSubject(undefined).valid === false, 'undefined returns invalid');
    assert(validateSubject('abc').valid === false, 'non-numeric string returns invalid');

    var emptyResult = validateSubject('');
    assertEqual(emptyResult.error, 'Bitte wählen Sie ein Fach aus.', 'empty string error message');

    var nullResult = validateSubject(null);
    assertEqual(nullResult.error, 'Bitte wählen Sie ein Fach aus.', 'null error message');
}

function runValidateTopicTests() {
    console.log('\n── validateTopic ──');

    assert(validateTopic(1).valid === true, 'valid topic ID returns valid');
    assert(validateTopic(0).valid === false, 'topic ID 0 returns invalid');
    assert(validateTopic('').valid === false, 'empty string returns invalid');
    assert(validateTopic(null).valid === false, 'null returns invalid');
    assert(validateTopic(undefined).valid === false, 'undefined returns invalid');

    var emptyResult = validateTopic('');
    assertEqual(emptyResult.error, 'Bitte wählen Sie ein Thema aus.', 'empty string error message');
}

function runValidateGradeTests() {
    console.log('\n── validateGrade ──');

    assert(validateGrade(1).valid === true, 'grade 1 is valid');
    assert(validateGrade(7).valid === true, 'grade 7 is valid');
    assert(validateGrade(13).valid === true, 'grade 13 is valid');
    assert(validateGrade(0).valid === false, 'grade 0 is invalid');
    assert(validateGrade(14).valid === false, 'grade 14 is invalid');
    assert(validateGrade(-1).valid === false, 'negative grade is invalid');
    assert(validateGrade('').valid === false, 'empty string is invalid');
    assert(validateGrade(null).valid === false, 'null is invalid');
    assert(validateGrade(undefined).valid === false, 'undefined is invalid');

    var outOfRangeResult = validateGrade(14);
    assertEqual(outOfRangeResult.error, 'Bitte wählen Sie eine Klasse aus (1–13).', 'out of range error message');
}

function runValidateInputTypeTests() {
    console.log('\n── validateInputType ──');

    assert(validateInputType('scan').valid === true, 'scan mode is valid');
    assert(validateInputType('manual').valid === true, 'manual mode is valid');
    assert(validateInputType('').valid === false, 'empty string is invalid');
    assert(validateInputType(null).valid === false, 'null is invalid');
    assert(validateInputType('invalid').valid === false, 'invalid mode is invalid');
    assert(validateInputType(undefined).valid === false, 'undefined is invalid');

    var invalidResult = validateInputType('invalid');
    assertEqual(invalidResult.error, 'Bitte wählen Sie einen Eingabetyp.', 'invalid mode error message');
}

function runValidateNumOfQuestionsTests() {
    console.log('\n── validateNumOfQuestions ──');

    assert(validateNumOfQuestions(5).valid === true, '5 is valid');
    assert(validateNumOfQuestions(10).valid === true, '10 is valid');
    assert(validateNumOfQuestions(15).valid === true, '15 is valid');
    assert(validateNumOfQuestions(20).valid === true, '20 is valid');
    assert(validateNumOfQuestions(25).valid === true, '25 is valid');
    assert(validateNumOfQuestions('5').valid === true, 'string "5" is valid');
    assert(validateNumOfQuestions('10').valid === true, 'string "10" is valid');
    assert(validateNumOfQuestions(4).valid === false, '4 is invalid (below range)');
    assert(validateNumOfQuestions(6).valid === false, '6 is invalid (not step of 5)');
    assert(validateNumOfQuestions(26).valid === false, '26 is invalid (above range)');
    assert(validateNumOfQuestions(12).valid === false, '12 is invalid (not step of 5)');
    assert(validateNumOfQuestions(0).valid === false, '0 is invalid');
    assert(validateNumOfQuestions(-5).valid === false, 'negative is invalid');
    assert(validateNumOfQuestions('').valid === false, 'empty string is invalid');
    assert(validateNumOfQuestions(null).valid === false, 'null is invalid');
    assert(validateNumOfQuestions(undefined).valid === false, 'undefined is invalid');

    var belowRangeResult = validateNumOfQuestions(4);
    assertEqual(belowRangeResult.error, 'Anzahl muss 5–25 in 5er-Schritten sein.', 'below range error message');

    var wrongStepResult = validateNumOfQuestions(12);
    assertEqual(wrongStepResult.error, 'Anzahl muss 5–25 in 5er-Schritten sein.', 'wrong step error message');
}

function runValidateFilesTests() {
    console.log('\n── validateFiles ──');

    // Empty/null cases
    assert(validateFiles(null).valid === false, 'null files returns invalid');
    assert(validateFiles(undefined).valid === false, 'undefined files returns invalid');
    assert(validateFiles([]).valid === false, 'empty array returns invalid');

    // Simulated file objects for testing
    function makeFile(name, mime, size) {
        return { name: name, type: mime, size: size };
    }

    var validFiles = [makeFile('test.jpg', 'image/jpeg', 1024)];
    assert(validateFiles(validFiles).valid === true, 'single valid file returns valid');

    var multiFiles = [
        makeFile('a.jpg', 'image/jpeg', 1024),
        makeFile('b.png', 'image/png', 2048),
        makeFile('c.pdf', 'application/pdf', 4096)
    ];
    assert(validateFiles(multiFiles).valid === true, 'multiple valid files returns valid');

    // Too many files
    var tooMany = [];
    for (var i = 0; i < 11; i++) {
        tooMany.push(makeFile('file' + i + '.jpg', 'image/jpeg', 1024));
    }
    assert(validateFiles(tooMany).valid === false, '11 files returns invalid (max 10)');

    // Wrong MIME type
    var wrongMime = [makeFile('file.exe', 'application/x-executable', 1024)];
    assert(validateFiles(wrongMime).valid === false, 'wrong MIME type returns invalid');

    // File too large
    var tooLarge = [makeFile('big.pdf', 'application/pdf', 26 * 1024 * 1024)];
    assert(validateFiles(tooLarge).valid === false, 'file > 25MB returns invalid');

    var tooManyResult = validateFiles(tooMany);
    assertEqual(tooManyResult.error, 'Maximal 10 Dateien erlaubt.', 'too many files error message');

    var tooLargeResult = validateFiles(tooLarge);
    assert(tooLargeResult.error.indexOf('25 MB') >= 0, 'too large file error message contains size');
}

function runValidateTextInputTests() {
    console.log('\n── validateTextInput ──');

    assert(validateTextInput('Hello world').valid === true, 'non-empty text is valid');
    assert(validateTextInput('  ').valid === false, 'whitespace-only text is invalid');
    assert(validateTextInput('').valid === false, 'empty string is invalid');
    assert(validateTextInput(null).valid === false, 'null is invalid');
    assert(validateTextInput(undefined).valid === false, 'undefined is invalid');

    var emptyResult = validateTextInput('');
    assertEqual(emptyResult.error, 'Bitte geben Sie einen Text ein.', 'empty text error message');
}

function runValidateAllTests() {
    console.log('\n── validateAll (integration) ──');

    // validateAll depends on DOM elements, so we test it only if the DOM is present
    var subjectEl = document.getElementById('subject-dropdown');
    if (!subjectEl) {
        console.log('  ⊘ Skipped validateAll tests (DOM not available)');
        return;
    }

    // Test with all fields empty
    var errors = validateAll();
    assert(errors.length > 0, 'validateAll returns errors when fields are empty');

    // Test with valid subject but empty topic
    subjectEl.value = '1';
    errors = validateAll();
    assert(errors.length > 0, 'validateAll returns errors when topic is empty');
}

function runPublicApiTests() {
    console.log('\n── Public API ──');

    assert(typeof window.submitQuestionInput === 'function', 'window.submitQuestionInput is a function');
    assert(typeof validateSubject === 'function', 'validateSubject is exposed globally');
    assert(typeof validateTopic === 'function', 'validateTopic is exposed globally');
    assert(typeof validateGrade === 'function', 'validateGrade is exposed globally');
    assert(typeof validateInputType === 'function', 'validateInputType is exposed globally');
    assert(typeof validateNumOfQuestions === 'function', 'validateNumOfQuestions is exposed globally');
    assert(typeof validateFiles === 'function', 'validateFiles is exposed globally');
    assert(typeof validateTextInput === 'function', 'validateTextInput is exposed globally');
    assert(typeof validateAll === 'function', 'validateAll is exposed globally');
}

/* ── Entry point ─────────────────────────────────────────────────────────── */

function loadAndRunTests() {
    console.log('=== Question Input JS Unit Tests ===\n');

    runPublicApiTests();
    runValidateSubjectTests();
    runValidateTopicTests();
    runValidateGradeTests();
    runValidateInputTypeTests();
    runValidateNumOfQuestionsTests();
    runValidateFilesTests();
    runValidateTextInputTests();
    runValidateAllTests();

    console.log('\n=== Ergebnis: ' + _passCount + '/' + _testCount + ' bestanden, ' + _failCount + ' fehlgeschlagen ===');

    if (_failCount > 0) {
        console.error('Einige Tests sind fehlgeschlagen!');
    } else {
        console.log('Alle Tests bestanden!');
    }

    return { total: _testCount, passed: _passCount, failed: _failCount };
}
