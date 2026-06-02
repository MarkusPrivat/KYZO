/**
 * Question Input JavaScript
 * Handles subject/topic loading, mode toggle, file upload, and question generation.
 *
 * Public API:
 *   window.submitQuestionInput() — validates all fields and sends the API request.
 *
 * Validation functions (also available for testing):
 *   validateSubject(subjectId)
 *   validateTopic(topicId)
 *   validateGrade(grade)
 *   validateInputType(mode)
 *   validateNumOfQuestions(num)
 *   validateFiles(files)
 *   validateTextInput(text)
 *   validateAll()
 */

/* ── Validation functions (pure, testable) ───────────────────────────────── */

/**
 * Validate subject selection.
 * @param {string|number|null} subjectId
 * @returns {{ valid: boolean, error: string }}
 */
function validateSubject(subjectId) {
    var id = subjectId !== null && subjectId !== undefined ? parseInt(subjectId, 10) : NaN;
    if (isNaN(id) || id <= 0) {
        return { valid: false, error: 'Bitte wählen Sie ein Fach aus.' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate topic selection.
 * @param {string|number|null} topicId
 * @returns {{ valid: boolean, error: string }}
 */
function validateTopic(topicId) {
    var id = topicId !== null && topicId !== undefined ? parseInt(topicId, 10) : NaN;
    if (isNaN(id) || id <= 0) {
        return { valid: false, error: 'Bitte wählen Sie ein Thema aus.' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate grade selection.
 * @param {string|number|null} grade
 * @returns {{ valid: boolean, error: string }}
 */
function validateGrade(grade) {
    var g = grade !== null && grade !== undefined ? parseInt(grade, 10) : NaN;
    if (isNaN(g) || g < 1 || g > 13) {
        return { valid: false, error: 'Bitte wählen Sie eine Klasse aus (1–13).' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate input type (mode).
 * @param {string} mode
 * @returns {{ valid: boolean, error: string }}
 */
function validateInputType(mode) {
    if (mode !== 'scan' && mode !== 'manual') {
        return { valid: false, error: 'Bitte wählen Sie einen Eingabetyp.' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate question count (5–25 in steps of 5).
 * @param {string|number|null} num
 * @returns {{ valid: boolean, error: string }}
 */
function validateNumOfQuestions(num) {
    var n = num !== null && num !== undefined ? parseInt(num, 10) : NaN;
    if (isNaN(n) || n < 5 || n > 25 || n % 5 !== 0) {
        return { valid: false, error: 'Anzahl muss 5–25 in 5er-Schritten sein.' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate file uploads.
 * @param {FileList|File[]|null} files
 * @returns {{ valid: boolean, error: string }}
 */
function validateFiles(files) {
    if (!files || files.length === 0) {
        return { valid: false, error: 'Bitte laden Sie mindestens eine Datei hoch.' };
    }
    if (files.length > 10) {
        return { valid: false, error: 'Maximal 10 Dateien erlaubt.' };
    }
    var allowedMimes = [
        'image/jpeg',
        'image/png',
        'image/webp',
        'application/pdf'
    ];
    var maxSize = 25 * 1024 * 1024; // 25 MB
    for (var i = 0; i < files.length; i++) {
        if (!allowedMimes.includes(files[i].type)) {
            return { valid: false, error: 'Datei "' + files[i].name + '" hat einen unsupported Typ.' };
        }
        if (files[i].size > maxSize) {
            return { valid: false, error: 'Datei "' + files[i].name + '" überschreitet 25 MB Limit.' };
        }
    }
    return { valid: true, error: '' };
}

/**
 * Validate text input.
 * @param {string|null} text
 * @returns {{ valid: boolean, error: string }}
 */
function validateTextInput(text) {
    if (!text || !text.trim()) {
        return { valid: false, error: 'Bitte geben Sie einen Text ein.' };
    }
    return { valid: true, error: '' };
}

/**
 * Validate all fields. Returns an array of { field, error } for failures.
 * @returns {{ field: string, error: string }[]}
 */
function validateAll() {
    var errors = [];

    var subjectResult = validateSubject(document.getElementById('subject-dropdown').value);
    if (!subjectResult.valid) {
        errors.push({ field: 'subject', error: subjectResult.error });
    }

    var topicResult = validateTopic(document.getElementById('topic-dropdown').value);
    if (!topicResult.valid) {
        errors.push({ field: 'topic', error: topicResult.error });
    }

    var gradeResult = validateGrade(document.getElementById('grade-dropdown').value);
    if (!gradeResult.valid) {
        errors.push({ field: 'grade', error: gradeResult.error });
    }

    var modeResult = validateInputType(document.getElementById('input-type-dropdown').value);
    if (!modeResult.valid) {
        errors.push({ field: 'inputType', error: modeResult.error });
    }

    var numResult = validateNumOfQuestions(document.getElementById('num-of-questions-dropdown').value);
    if (!numResult.valid) {
        errors.push({ field: 'numOfQuestions', error: numResult.error });
    }

    var mode = document.getElementById('input-type-dropdown').value;
    if (mode === 'scan') {
        var fileResult = validateFiles(selectedFiles);
        if (!fileResult.valid) {
            errors.push({ field: 'files', error: fileResult.error });
        }
    } else {
        var textInput = document.getElementById('text-input');
        var textResult = validateTextInput(textInput ? textInput.value : null);
        if (!textResult.valid) {
            errors.push({ field: 'textInput', error: textResult.error });
        }
    }

    return errors;
}

/* ── Visual error marker helpers ─────────────────────────────────────────── */

var errorFieldMap = {
    subject: 'subject-dropdown',
    topic: 'topic-dropdown',
    grade: 'grade-dropdown',
    inputType: 'input-type-dropdown',
    numOfQuestions: 'num-of-questions-dropdown',
    files: 'upload-zone',
    textInput: 'text-input'
};

/**
 * Clear all visual error markers.
 */
function clearErrorMarkers() {
    var fields = ['subject-dropdown', 'topic-dropdown', 'grade-dropdown',
                  'input-type-dropdown', 'num-of-questions-dropdown', 'text-input'];
    for (var i = 0; i < fields.length; i++) {
        var el = document.getElementById(fields[i]);
        if (el) {
            el.classList.remove('is-invalid');
            var existing = el.parentElement.querySelector('.invalid-feedback');
            if (existing) existing.remove();
        }
    }
    var uploadZone = document.getElementById('upload-zone');
    if (uploadZone) uploadZone.classList.remove('is-invalid');
}

/**
 * Show visual error markers for a specific field.
 * @param {string} field - The field name (subject, topic, grade, etc.)
 * @param {string} message - The error message to display.
 */
function showFieldError(field, message) {
    var elId = errorFieldMap[field];
    if (!elId) return;

    var el = document.getElementById(elId);
    if (el) {
        el.classList.add('is-invalid');
        var feedback = el.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.setAttribute('role', 'alert');
            el.parentElement.appendChild(feedback);
        }
        feedback.textContent = message;
    }
}

/* ── JWT helper ──────────────────────────────────────────────────────────── */

/**
 * Extract user_id from the JWT token stored in localStorage.
 * @returns {number|null}
 */
function getUserIdFromToken() {
    var token = typeof getAuthHeader === 'function' ? (getAuthHeader()['Authorization'] || '').replace('Bearer ', '') : '';
    if (!token) return null;
    try {
        var parts = token.split('.');
        if (parts.length < 2) return null;
        var payload = JSON.parse(atob(parts[1]));
        return payload.sub ? parseInt(payload.sub, 10) : null;
    } catch (e) {
        return null;
    }
}

/* ── Module state ────────────────────────────────────────────────────────── */

var selectedSubjectId = null;
var selectedFiles = [];

/* ── Public API ──────────────────────────────────────────────────────────── */

/**
 * Submit question input via API.
 * Validates all fields, shows visual error markers on failure,
 * and sends a multipart/form-data POST to the backend.
 * @returns {boolean} True if submission was attempted, false if validation failed.
 */
window.submitQuestionInput = function () {
    clearErrorMarkers();

    var errors = validateAll();
    if (errors.length > 0) {
        for (var i = 0; i < errors.length; i++) {
            showFieldError(errors[i].field, errors[i].error);
        }
        return false;
    }

    var mode = document.getElementById('input-type-dropdown').value;
    var userId = getUserIdFromToken();
    if (!userId) {
        showToast('Authentifizierung fehlgeschlagen. Bitte erneut anmelden.', 'error');
        return false;
    }

    var input_data = {
        user_id: userId,
        subject_id: parseInt(document.getElementById('subject-dropdown').value, 10),
        topic_id: parseInt(document.getElementById('topic-dropdown').value, 10),
        grade: parseInt(document.getElementById('grade-dropdown').value, 10),
        input_type: mode,
        raw_input: {
            content: '',
            source_ref: ''
        }
    };

    if (mode === 'manual') {
        input_data.raw_input.content = document.getElementById('text-input').value.trim();
    }

    var url = API_URL + '/questions/input/add';
    var headers = getAuthHeader();
    var formData = new FormData();
    formData.append('input_data_json', JSON.stringify(input_data));
    formData.append('num_of_questions', parseInt(document.getElementById('num-of-questions-dropdown').value, 10));

    if (mode === 'scan' && selectedFiles.length > 0) {
        for (var i = 0; i < selectedFiles.length; i++) {
            formData.append('files', selectedFiles[i]);
        }
    }

    var submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Wird generiert...';

    fetch(url, {
        method: 'POST',
        headers: headers,
        body: formData
    })
        .then(function (response) {
            if (response.status === 201) {
                showToast('Fragen erfolgreich generiert!', 'success');
            } else {
                return response.json().catch(function () { return null; });
            }
        })
        .then(function (errData) {
            if (errData) {
                var detail = errData.detail;
                if (Array.isArray(detail)) {
                    detail = detail.map(function (e) { return e.msg || e.message; }).join('; ');
                }
                showToast(detail || 'Fehler beim Generieren', 'error');
            }
        })
        .catch(function (err) {
            showToast('Netzwerkfehler: ' + err.message, 'error');
        })
        .finally(function () {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Fragen generieren';
        });

    return true;
};

/* ── DOM initialization ──────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
    var subjectDropdown = document.getElementById('subject-dropdown');
    var topicDropdown = document.getElementById('topic-dropdown');
    var gradeDropdown = document.getElementById('grade-dropdown');
    var inputTypeDropdown = document.getElementById('input-type-dropdown');
    var fileUploadInput = document.getElementById('file-upload');
    var uploadZone = document.getElementById('upload-zone');
    var fileList = document.getElementById('file-list');

    if (!subjectDropdown || !topicDropdown) return;

    // ── Load subjects on page load ──────────────────────────────────────

    loadSubjects();

    // ── Subject change: load topics ─────────────────────────────────────

    subjectDropdown.addEventListener('change', function () {
        var value = this.value;
        selectedSubjectId = value ? parseInt(value, 10) : null;

        if (selectedSubjectId) {
            topicDropdown.disabled = false;
            loadTopics(selectedSubjectId);
        } else {
            topicDropdown.disabled = true;
            topicDropdown.innerHTML = '<option value="">-- Thema auswählen --</option>';
        }
    });

    // ── Mode toggle: show/hide panels ───────────────────────────────────

    inputTypeDropdown.addEventListener('change', function () {
        var mode = this.value;
        if (mode === 'scan') {
            fileUploadPanel.style.display = 'block';
            textInputPanel.style.display = 'none';
        } else {
            fileUploadPanel.style.display = 'none';
            textInputPanel.style.display = 'block';
        }
    });

    // ── File upload handling ────────────────────────────────────────────

    var fileUploadPanel = document.getElementById('file-upload-panel');
    var textInputPanel = document.getElementById('text-input-panel');

    if (uploadZone && fileUploadInput) {
        uploadZone.addEventListener('click', function () {
            fileUploadInput.click();
        });

        uploadZone.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileUploadInput.click();
            }
        });

        fileUploadInput.addEventListener('change', function () {
            handleFiles(this.files);
        });

        uploadZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#E4572E';
            uploadZone.style.backgroundColor = 'rgba(228, 87, 46, 0.05)';
        });

        uploadZone.addEventListener('dragleave', function () {
            uploadZone.style.borderColor = '#E8E2DC';
            uploadZone.style.backgroundColor = '';
        });

        uploadZone.addEventListener('drop', function (e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#E8E2DC';
            uploadZone.style.backgroundColor = '';
            handleFiles(e.dataTransfer.files);
        });
    }

    function handleFiles(files) {
        var remaining = 10 - selectedFiles.length;
        if (remaining <= 0) {
            showToast('Maximal 10 Dateien erlaubt.', 'error');
            return;
        }

        var filesToAdd = Array.from(files).slice(0, remaining);
        for (var i = 0; i < filesToAdd.length; i++) {
            var file = filesToAdd[i];
            if (file.size > 25 * 1024 * 1024) {
                showToast('Datei "' + file.name + '" überschreitet 25 MB Limit.', 'error');
                continue;
            }
            selectedFiles.push(file);
        }
        renderFileList();
    }

    function renderFileList() {
        if (!fileList) return;
        fileList.innerHTML = '';
        for (var i = 0; i < selectedFiles.length; i++) {
            var item = document.createElement('div');
            item.className = 'file-list__item';
            item.innerHTML =
                '<span>' + escapeHtml(selectedFiles[i].name) + ' (' + formatFileSize(selectedFiles[i].size) + ')</span>' +
                '<button type="button" class="file-list__remove" data-index="' + i + '" aria-label="' + escapeHtml(selectedFiles[i].name) + ' entfernen">&times;</button>';
            fileList.appendChild(item);
        }

        var removeButtons = fileList.querySelectorAll('.file-list__remove');
        for (var j = 0; j < removeButtons.length; j++) {
            removeButtons[j].addEventListener('click', (function (idx) {
                return function () {
                    selectedFiles.splice(idx, 1);
                    renderFileList();
                };
            })(j));
        }
    }

    // ── Helper functions ────────────────────────────────────────────────

    async function loadSubjects() {
        try {
            var response = await fetch(API_URL + '/knowledge/subjects/list-all', {
                headers: getAuthHeader()
            });
            if (!response.ok) return;
            var data = await response.json();
            var subjects = Array.isArray(data) ? data : [];
            for (var i = 0; i < subjects.length; i++) {
                var opt = document.createElement('option');
                opt.value = subjects[i].id;
                opt.textContent = subjects[i].name;
                subjectDropdown.appendChild(opt);
            }
        } catch (err) {
            console.error('Failed to load subjects:', err);
        }
    }

    async function loadTopics(subjectId) {
        topicDropdown.innerHTML = '<option value="">-- Thema auswählen --</option>';
        try {
            var response = await fetch(API_URL + '/knowledge/subjects/' + subjectId + '/topics/list-all', {
                headers: getAuthHeader()
            });
            if (!response.ok) return;
            var data = await response.json();
            var topics = Array.isArray(data) ? data : [];
            for (var i = 0; i < topics.length; i++) {
                var opt = document.createElement('option');
                opt.value = topics[i].id;
                opt.textContent = topics[i].name;
                topicDropdown.appendChild(opt);
            }
        } catch (err) {
            console.error('Failed to load topics:', err);
        }
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
});
