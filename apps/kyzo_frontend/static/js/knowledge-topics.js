/**
 * Knowledge Topics Management JavaScript
 * Handles CRUD operations for topics within a subject
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the knowledge topics page
    var container = document.querySelector('.admin-knowledge-topics');
    if (container) {
        var subjectId = parseInt(container.dataset.subjectId);
        if (subjectId && subjectId > 0) {
            // A subject was passed from the server (navigated from subjects page)
            loadSubjectName(subjectId);
            loadTopics(subjectId);
            populateSubjectSelector(subjectId);
        } else {
            // No subject selected - show empty state
            populateSubjectSelector(null);
            renderEmptyState();
        }
        setupEventListeners();
    }
});

// Global variables
var currentTopics = [];
var currentSubjectId = null;
var currentSubjectName = '';
var currentAction = null;
var currentTopicId = null;
var currentSearchTerm = '';
var currentFilter = 'all';
var searchTimeout = null;
var allSubjects = [];

/**
 * Load subject name from API and update page
 * @param {number} subjectId - ID of the subject
 */
async function loadSubjectName(subjectId) {
    try {
        var response = await fetch(API_URL + '/knowledge/subjects/list-all', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            var data = await response.json();
            var subjects = Array.isArray(data) ? data : [];
            var subject = subjects.find(function(s) { return s.id === subjectId; });
            
            if (subject) {
                currentSubjectName = subject.name;
                currentSubjectId = subjectId;
                
                // Update page title
                var pageTitle = document.getElementById('topics-page-title');
                if (pageTitle) {
                    pageTitle.textContent = 'Themen für ' + subject.name;
                }
                
                // Update parent subject fields in modals
                var createParent = document.getElementById('create-topic-parent');
                if (createParent) createParent.value = subject.name;
                
                var editParent = document.getElementById('edit-topic-parent');
                if (editParent) editParent.value = subject.name;
                
                // Update edit form hidden field
                var editSubjectId = document.getElementById('edit-topic-subject-id');
                if (editSubjectId) editSubjectId.value = subjectId;
            } else {
                currentSubjectName = 'Fach #' + subjectId;
                var pageTitle = document.getElementById('topics-page-title');
                if (pageTitle) pageTitle.textContent = 'Themen für Fach #' + subjectId;
            }
        } else {
            showToast('Fehler beim Laden der Fachdetails. Bitte versuche es erneut.', 'error');
        }
    } catch (error) {
        currentSubjectName = 'Fach #' + subjectId;
        var pageTitle = document.getElementById('topics-page-title');
        if (pageTitle) pageTitle.textContent = 'Themen für Fach #' + subjectId;
        console.error('Error loading subject name:', error);
    }
}

/**
 * Load topics from API and populate the table
 * @param {number} subjectId - ID of the subject
 */
async function loadTopics(subjectId) {
    if (!subjectId) return;
    
    try {
        var response = await fetch(API_URL + '/knowledge/subjects/' + subjectId + '/topics/list-all', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            var data = await response.json();
            currentTopics = Array.isArray(data) ? data : [];
            renderFilteredTopicsTable();
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else {
            showToast('Fehler beim Laden der Themen. Bitte versuche es erneut.', 'error');
            console.error('Error loading topics:', response.status);
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Populate the subject selector dropdown
 * @param {number|null} selectedSubjectId - ID of the currently selected subject
 */
async function populateSubjectSelector(selectedSubjectId) {
    var dropdown = document.getElementById('subject-dropdown');
    if (!dropdown) return;
    
    try {
        var response = await fetch(API_URL + '/knowledge/subjects/list-all', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            var data = await response.json();
            allSubjects = Array.isArray(data) ? data : [];
            
            // Clear existing options except the first
            dropdown.innerHTML = '<option value="">-- Fach auswählen --</option>';
            
            allSubjects.forEach(function(subject) {
                var option = document.createElement('option');
                option.value = subject.id;
                option.textContent = subject.name + (subject.is_active ? '' : ' (Inaktiv)');
                option.dataset.isActive = subject.is_active;
                if (selectedSubjectId && subject.id === selectedSubjectId) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });
            
            // If a subject was selected, show header
            if (selectedSubjectId) {
                var subject = allSubjects.find(function(s) { return s.id === selectedSubjectId; });
                if (subject) {
                    currentSubjectName = subject.name;
                    currentSubjectId = selectedSubjectId;
                    document.getElementById('topics-page-title').textContent = 'Themen für ' + subject.name;
                }
            }
        }
    } catch (error) {
        console.error('Error populating subject selector:', error);
    }
}

/**
 * Populate the create topic modal subject selector dropdown
 */
async function populateCreateSubjectSelector() {
    var dropdown = document.getElementById('create-topic-subject');
    if (!dropdown) return;

    try {
        var response = await fetch(API_URL + '/knowledge/subjects/list-all', {
            headers: getAuthHeader()
        });

        if (response.ok) {
            var data = await response.json();
            var subjects = Array.isArray(data) ? data : [];

            // Clear existing options except the first
            dropdown.innerHTML = '<option value="">-- Fach auswählen --</option>';

            subjects.forEach(function(subject) {
                var option = document.createElement('option');
                option.value = subject.id;
                option.textContent = subject.name + (subject.is_active ? '' : ' (Inaktiv)');
                if (currentSubjectId && subject.id === currentSubjectId) {
                    option.selected = true;
                }
                dropdown.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error populating create topic subject selector:', error);
    }
}

/**
 * Render empty state when no subject is selected
 */
function renderEmptyState() {
    var tableBody = document.getElementById('topics-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">Keine Ergebnisse</td></tr>';
}

/**
 * Render topics table with search and filter applied
 */
function renderFilteredTopicsTable() {
    var tableBody = document.getElementById('topics-table-body');
    
    if (!tableBody) return;
    
    // Clear loading row
    tableBody.innerHTML = '';
    
    // Apply search and filter
    var filtered = currentTopics.filter(function(topic) {
        // Apply search filter
        var matchesSearch = currentSearchTerm === '' ||
            topic.name.toLowerCase().includes(currentSearchTerm.toLowerCase());
        
        // Apply status filter
        var matchesFilter = true;
        if (currentFilter === 'active') {
            matchesFilter = topic.is_active === true;
        } else if (currentFilter === 'inactive') {
            matchesFilter = topic.is_active === false;
        }
        
        return matchesSearch && matchesFilter;
    });
    
    if (filtered.length === 0) {
        var emptyMessage = currentSearchTerm || currentFilter !== 'all'
            ? 'Keine Ergebnisse'
            : 'Keine Themen gefunden. Klicke "Thema erstellen" um dein erstes Thema hinzuzufügen.';
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">' + emptyMessage + '</td></tr>';
        return;
    }
    
    // Sort filtered topics by ID
    filtered.sort(function(a, b) { return a.id - b.id; });
    
    // Render each topic
    filtered.forEach(function(topic) {
        var row = document.createElement('tr');
        row.dataset.topicId = topic.id;
        
        row.innerHTML = '<td>' + topic.id + '</td>' +
            '<td>' + escapeHtml(topic.name) + '</td>' +
            '<td>' + (topic.expected_grade || 'N/A') + '</td>' +
            '<td><span class="status-badge status-badge--' + (topic.is_active ? 'active' : 'inactive') + '">' + (topic.is_active ? 'Aktiv' : 'Inaktiv') + '</span></td>' +
            '<td>' + formatDate(topic.created_at) + '</td>' +
            '<td class="actions-cell">' +
                '<button class="action-btn action-btn-edit" data-topic-id="' + topic.id + '"><i class="fas fa-edit"></i> Bearbeiten</button>' +
                '<button class="action-btn action-btn-toggle" data-topic-id="' + topic.id + '"><i class="fas fa-toggle-' + (topic.is_active ? 'on' : 'off') + '"></i> ' + (topic.is_active ? 'Deaktivieren' : 'Aktivieren') + '</button>' +
            '</td>';
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to rows for detail view
    document.querySelectorAll('.topics-table tbody tr').forEach(function(row) {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.action-btn')) return;
            
            var topicId = parseInt(row.dataset.topicId);
            showTopicDetail(topicId);
        });
    });
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

/**
 * Format date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        var date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return dateString;
    }
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Create topic button
    document.getElementById('create-topic-btn')?.addEventListener('click', showCreateTopicModal);
    
    // Create topic modal
    document.getElementById('create-topic-close')?.addEventListener('click', hideCreateTopicModal);
    document.getElementById('create-topic-cancel')?.addEventListener('click', hideCreateTopicModal);
    document.getElementById('create-topic-submit')?.addEventListener('click', createTopic);
    
    // Edit topic modal
    document.getElementById('edit-topic-close')?.addEventListener('click', hideEditTopicModal);
    document.getElementById('edit-topic-cancel')?.addEventListener('click', hideEditTopicModal);
    document.getElementById('edit-topic-submit')?.addEventListener('click', saveEditedTopic);
    
    // Detail topic modal
    document.getElementById('detail-topic-close')?.addEventListener('click', hideDetailTopicModal);
    document.getElementById('detail-topic-close-btn')?.addEventListener('click', hideDetailTopicModal);
    
    // Confirmation dialog
    document.getElementById('confirmation-close')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-cancel')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-confirm')?.addEventListener('click', handleConfirmation);
    
    // Subject selector "Laden" button
    document.getElementById('load-topics-btn')?.addEventListener('click', function() {
        var dropdown = document.getElementById('subject-dropdown');
        var selectedSubjectId = parseInt(dropdown.value);
        if (selectedSubjectId) {
            currentSubjectId = selectedSubjectId;
            var selectedOption = dropdown.options[dropdown.selectedIndex];
            currentSubjectName = selectedOption.text.replace(' (Inaktiv)', '');
            document.getElementById('topics-page-title').textContent = 'Themen für ' + currentSubjectName;
            loadTopics(selectedSubjectId);
        }
    });
    
    // Search input (debounced)
    document.getElementById('topics-search')?.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(function() {
            currentSearchTerm = e.target.value;
            renderFilteredTopicsTable();
        }, 300);
    });
    
    // Filter dropdown
    document.getElementById('topics-filter')?.addEventListener('change', function(e) {
        currentFilter = e.target.value;
        renderFilteredTopicsTable();
    });
}

/**
 * Show create topic modal
 */
function showCreateTopicModal() {
    var modal = document.getElementById('create-topic-modal');
    if (modal) {
        document.getElementById('create-topic-name').value = '';
        document.getElementById('create-topic-grade').value = '';

        // Conditional parent subject field
        var createParent = document.getElementById('create-topic-parent');
        var createSubjectGroup = document.getElementById('create-topic-subject-group');

        if (currentSubjectId && currentSubjectId > 0) {
            // Navigated from a subject detail page: show readonly parent field
            if (createParent) createParent.style.display = 'block';
            if (createSubjectGroup) createSubjectGroup.style.display = 'none';
        } else {
            // Topics overview page: show subject dropdown
            if (createParent) createParent.style.display = 'none';
            if (createSubjectGroup) createSubjectGroup.style.display = 'block';
            // Populate the dropdown if empty
            var dropdown = document.getElementById('create-topic-subject');
            if (dropdown && dropdown.options.length <= 1) {
                populateCreateSubjectSelector();
            }
        }

        modal.style.display = 'block';
        document.getElementById('create-topic-name').focus();
    }
}

/**
 * Hide create topic modal
 */
function hideCreateTopicModal() {
    document.getElementById('create-topic-modal').style.display = 'none';
}

/**
 * Create new topic
 */
async function createTopic() {
    var nameInput = document.getElementById('create-topic-name');
    var gradeInput = document.getElementById('create-topic-grade');
    var name = nameInput.value.trim();
    var grade = gradeInput.value;
    
    // Validate name
    if (name.length < 2 || name.length > 150) {
        var feedback = nameInput.nextElementSibling;
        if (feedback) feedback.style.display = 'block';
        return;
    }
    
    // Validate grade
    if (!grade || grade < 1 || grade > 13) {
        showToast('Bitte wählen Sie eine gültige erwartete Klasse (1-13).', 'error');
        return;
    }
    
    // Determine subject_id from context
    var topicSubjectId = currentSubjectId;
    if (!topicSubjectId || topicSubjectId <= 0) {
        // On overview page: read from dropdown
        var subjectDropdown = document.getElementById('create-topic-subject');
        if (subjectDropdown) {
            topicSubjectId = parseInt(subjectDropdown.value);
        }
    }
    if (!topicSubjectId || topicSubjectId <= 0) {
        showToast('Bitte wählen Sie ein Fach aus.', 'error');
        return;
    }

    try {
        var response = await fetch(API_URL + '/knowledge/subjects/' + topicSubjectId + '/topics/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                name: name,
                expected_grade: parseInt(grade),
                subject_id: topicSubjectId
            })
        });
        
        if (response.ok) {
            var newTopic = await response.json();
            currentTopics.push(newTopic);
            renderFilteredTopicsTable();
            hideCreateTopicModal();
            showToast('Thema erfolgreich erstellt.');
        } else if (response.status === 409) {
            showToast('Ein Thema mit diesem Namen existiert bereits.', 'error');
        } else {
            var errorData = await response.json();
            showToast('Fehler beim Erstellen des Themas: ' + (errorData.message || 'Unbekannter Fehler'), 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show edit topic modal
 * @param {number} topicId - ID of topic to edit
 */
function showEditTopicModal(topicId) {
    var topic = currentTopics.find(function(t) { return t.id === topicId; });
    if (!topic) return;
    
    var modal = document.getElementById('edit-topic-modal');
    if (modal) {
        document.getElementById('edit-topic-id').value = topic.id;
        document.getElementById('edit-topic-name').value = topic.name;
        document.getElementById('edit-topic-grade').value = topic.expected_grade || '';
        modal.style.display = 'block';
        document.getElementById('edit-topic-name').focus();
    }
}

/**
 * Hide edit topic modal
 */
function hideEditTopicModal() {
    document.getElementById('edit-topic-modal').style.display = 'none';
}

/**
 * Save edited topic
 */
async function saveEditedTopic() {
    var topicId = parseInt(document.getElementById('edit-topic-id').value);
    var nameInput = document.getElementById('edit-topic-name');
    var gradeInput = document.getElementById('edit-topic-grade');
    var name = nameInput.value.trim();
    var grade = gradeInput.value;
    
    // Validate name
    if (name.length < 2 || name.length > 150) {
        var feedback = nameInput.nextElementSibling;
        if (feedback) feedback.style.display = 'block';
        return;
    }
    
    // Validate grade
    if (!grade || grade < 1 || grade > 13) {
        showToast('Bitte wählen Sie eine gültige erwartete Klasse (1-13).', 'error');
        return;
    }
    
    // Read subject_id from hidden field
    var editSubjectIdField = document.getElementById('edit-topic-subject-id');
    var editSubjectId = editSubjectIdField ? parseInt(editSubjectIdField.value) : null;
    if (!editSubjectId || editSubjectId <= 0) {
        showToast('Fehler: Fach-ID nicht gefunden.', 'error');
        return;
    }

    try {
        var response = await fetch(API_URL + '/knowledge/subjects/' + editSubjectId + '/topics/' + topicId + '/edit', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                name: name,
                expected_grade: parseInt(grade),
                subject_id: editSubjectId
            })
        });
        
        if (response.ok) {
            var updatedTopic = await response.json();
            var index = currentTopics.findIndex(function(t) { return t.id === topicId; });
            if (index !== -1) {
                currentTopics[index] = updatedTopic;
                renderFilteredTopicsTable();
            }
            hideEditTopicModal();
            showToast('Thema erfolgreich aktualisiert.');
        } else if (response.status === 409) {
            showToast('Ein Thema mit diesem Namen existiert bereits.', 'error');
        } else {
            var errorData = await response.json();
            showToast('Fehler beim Aktualisieren des Themas: ' + (errorData.message || 'Unbekannter Fehler'), 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show topic detail modal
 * @param {number} topicId - ID of topic to show details for
 */
function showTopicDetail(topicId) {
    var topic = currentTopics.find(function(t) { return t.id === topicId; });
    if (!topic) return;
    
    var modal = document.getElementById('detail-topic-modal');
    if (modal) {
        document.getElementById('detail-topic-id').textContent = topic.id;
        document.getElementById('detail-topic-name').textContent = topic.name;
        document.getElementById('detail-topic-grade').textContent = topic.expected_grade || 'N/A';
        document.getElementById('detail-topic-status').textContent = topic.is_active ? 'Aktiv' : 'Inaktiv';
        document.getElementById('detail-topic-created').textContent = formatDate(topic.created_at);
        document.getElementById('detail-topic-parent').textContent = currentSubjectName;
        modal.style.display = 'block';
    }
}

/**
 * Hide detail topic modal
 */
function hideDetailTopicModal() {
    document.getElementById('detail-topic-modal').style.display = 'none';
}

/**
 * Show confirmation dialog for status toggle
 * @param {number} topicId - ID of topic to toggle
 * @param {boolean} currentStatus - Current status of topic
 */
function showToggleConfirmation(topicId, currentStatus) {
    currentAction = 'toggleStatus';
    currentTopicId = topicId;
    
    var dialog = document.getElementById('confirmation-dialog');
    var message = document.getElementById('confirmation-message');
    
    if (dialog && message) {
        message.textContent = currentStatus 
            ? 'Sind Sie sicher, dass Sie dieses Thema deaktivieren möchten?'
            : 'Sind Sie sicher, dass Sie dieses Thema aktivieren möchten?';
        dialog.style.display = 'block';
    }
}

/**
 * Hide confirmation dialog
 */
function hideConfirmationDialog() {
    document.getElementById('confirmation-dialog').style.display = 'none';
    currentAction = null;
    currentTopicId = null;
}

/**
 * Handle confirmation action
 */
async function handleConfirmation() {
    if (!currentAction || currentTopicId === null) {
        hideConfirmationDialog();
        return;
    }
    
    if (currentAction === 'toggleStatus') {
        await toggleTopicStatus(currentTopicId);
    }
    
    hideConfirmationDialog();
}

/**
 * Toggle topic status
 * @param {number} topicId - ID of topic to toggle
 */
async function toggleTopicStatus(topicId) {
    var topic = currentTopics.find(function(t) { return t.id === topicId; });
    if (!topic) return;
    
    var newStatus = !topic.is_active;
    
    try {
        var response = await fetch(API_URL + '/knowledge/subjects/' + currentSubjectId + '/topics/' + topicId, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                is_active: newStatus
            })
        });
        
        if (response.ok) {
            var updatedTopic = await response.json();
            var index = currentTopics.findIndex(function(t) { return t.id === topicId; });
            if (index !== -1) {
                currentTopics[index] = updatedTopic;
                renderFilteredTopicsTable();
                showToast('Thema ' + (newStatus ? 'aktiviert' : 'deaktiviert') + '.');
            }
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else {
            var errorData = await response.json();
            showToast('Fehler beim Umschalten des Status: ' + (errorData.message || 'Unbekannter Fehler'), 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}
document.addEventListener('click', function(e) {
    // Edit button click
    var editBtn = e.target.closest('.action-btn-edit');
    if (editBtn) {
        var topicId = parseInt(editBtn.dataset.topicId);
        showEditTopicModal(topicId);
    }
    
    // Toggle button click
    var toggleBtn = e.target.closest('.action-btn-toggle');
    if (toggleBtn) {
        var topicId = parseInt(toggleBtn.dataset.topicId);
        var topic = currentTopics.find(function(t) { return t.id === topicId; });
        if (topic) {
            showToggleConfirmation(topicId, topic.is_active);
        }
    }
});