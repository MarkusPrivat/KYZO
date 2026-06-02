/**
 * Question Input JavaScript
 * Handles subject/topic loading, mode toggle, file upload, and question generation.
 */

document.addEventListener('DOMContentLoaded', function () {
    var subjectDropdown = document.getElementById('subject-dropdown');
    var topicDropdown = document.getElementById('topic-dropdown');
    var gradeDropdown = document.getElementById('grade-dropdown');
    var inputTypeDropdown = document.getElementById('input-type-dropdown');
    var numOfQuestionsDropdown = document.getElementById('num-of-questions-dropdown');
    var fileUploadPanel = document.getElementById('file-upload-panel');
    var textInputPanel = document.getElementById('text-input-panel');
    var fileUploadInput = document.getElementById('file-upload');
    var uploadZone = document.getElementById('upload-zone');
    var fileList = document.getElementById('file-list');
    var submitBtn = document.getElementById('submit-btn');

    if (!subjectDropdown || !topicDropdown) return;

    var selectedSubjectId = null;
    var selectedFiles = [];

    // ── Load subjects on page load ──────────────────────────────────────────

    loadSubjects();

    // ── Subject change: load topics ─────────────────────────────────────────

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

    // ── Mode toggle: show/hide panels ───────────────────────────────────────

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

    // ── File upload handling ────────────────────────────────────────────────

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

    // ── Submit: send question generation request ────────────────────────────

    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            if (!selectedSubjectId) {
                showToast('Bitte wählen Sie ein Fach aus.', 'error');
                return;
            }

            var mode = inputTypeDropdown.value;
            var payload = {
                subject_id: selectedSubjectId,
                topic_id: topicDropdown.value ? parseInt(topicDropdown.value, 10) : null,
                grade: gradeDropdown.value ? parseInt(gradeDropdown.value, 10) : null,
                input_type: mode,
                num_questions: parseInt(numOfQuestionsDropdown.value, 10)
            };

            if (mode === 'scan') {
                if (selectedFiles.length === 0) {
                    showToast('Bitte laden Sie mindestens eine Datei hoch.', 'error');
                    return;
                }
                payload.files = selectedFiles;
            } else {
                var textInput = document.getElementById('text-input');
                if (!textInput || !textInput.value.trim()) {
                    showToast('Bitte geben Sie einen Text ein.', 'error');
                    return;
                }
                payload.text = textInput.value.trim();
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Wird generiert...';
            generateQuestions(payload);
        });
    }

    // ── Helper functions ────────────────────────────────────────────────────

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

    async function generateQuestions(payload) {
        var url = API_URL + '/knowledge/questions/generate';
        var headers = getAuthHeader();

        if (payload.files) {
            var formData = new FormData();
            formData.append('subject_id', payload.subject_id);
            if (payload.topic_id) formData.append('topic_id', payload.topic_id);
            if (payload.grade) formData.append('grade', payload.grade);
            formData.append('input_type', payload.input_type);
            formData.append('num_questions', payload.num_questions);
            if (payload.text) formData.append('text', payload.text);
            for (var i = 0; i < payload.files.length; i++) {
                formData.append('files', payload.files[i]);
            }
            try {
                var response = await fetch(url, {
                    method: 'POST',
                    headers: headers,
                    body: formData
                });
                if (!response.ok) {
                    var errData = await response.json().catch(function () { return { detail: 'Fehler beim Generieren' }; });
                    showToast(errData.detail || 'Fehler beim Generieren', 'error');
                } else {
                    showToast('Fragen erfolgreich generiert!', 'success');
                }
            } catch (err) {
                showToast('Netzwerkfehler: ' + err.message, 'error');
            }
        } else {
            try {
                var response = await fetch(url, {
                    method: 'POST',
                    headers: Object.assign({ 'Content-Type': 'application/json' }, headers),
                    body: JSON.stringify(payload)
                });
                if (!response.ok) {
                    var errData = await response.json().catch(function () { return { detail: 'Fehler beim Generieren' }; });
                    showToast(errData.detail || 'Fehler beim Generieren', 'error');
                } else {
                    showToast('Fragen erfolgreich generiert!', 'success');
                }
            } catch (err) {
                showToast('Netzwerkfehler: ' + err.message, 'error');
            }
        }

        submitBtn.disabled = false;
        submitBtn.textContent = 'Fragen generieren';
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
