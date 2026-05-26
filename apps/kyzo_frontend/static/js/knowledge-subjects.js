/**
 * Knowledge Subjects Management JavaScript
 * Handles CRUD operations for knowledge subjects
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the knowledge subjects page
    if (document.querySelector('.admin-knowledge-subjects')) {
        loadSubjects();
        setupEventListeners();
    }
});

// Global variables
let currentSubjects = [];
let currentAction = null;
let currentSubjectId = null;
let currentSearchTerm = '';
let currentFilter = 'all';
let searchTimeout = null;

/**
 * Load subjects from API and populate the table
 */
async function loadSubjects() {
    try {
        const response = await fetch(API_URL + '/knowledge/subjects/list-all', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const data = await response.json();
            currentSubjects = Array.isArray(data) ? data : [];
            renderFilteredSubjectsTable();
        } else {
            showToast('Fehler beim Laden der Fächer. Bitte versuche es erneut.', 'error');
            console.error('Error loading subjects:', response.status);
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Render subjects table with search and filter applied
 */
function renderFilteredSubjectsTable() {
    const tableBody = document.getElementById('subjects-table-body');
    
    if (!tableBody) return;
    
    // Clear loading row
    tableBody.innerHTML = '';
    
    // Apply search and filter
    let filtered = currentSubjects.filter(subject => {
        // Apply search filter
        const matchesSearch = currentSearchTerm === '' ||
            subject.name.toLowerCase().includes(currentSearchTerm.toLowerCase());
        
        // Apply status filter
        let matchesFilter = true;
        if (currentFilter === 'active') {
            matchesFilter = subject.is_active === true;
        } else if (currentFilter === 'inactive') {
            matchesFilter = subject.is_active === false;
        }
        
        return matchesSearch && matchesFilter;
    });
    
    if (filtered.length === 0) {
        const emptyMessage = currentSearchTerm || currentFilter !== 'all'
            ? 'Keine Ergebnisse'
            : 'Keine Fächer gefunden. Klicke "Fach erstellen" um dein erstes Fach hinzuzufügen.';
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px;">
                    ${emptyMessage}
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort filtered subjects by ID
    filtered.sort((a, b) => a.id - b.id);
    
    // Render each subject
    filtered.forEach(subject => {
        const row = document.createElement('tr');
        row.dataset.subjectId = subject.id;
        
        row.innerHTML = `
            <td>${subject.id}</td>
            <td>${subject.name}</td>
            <td>
                <span class="status-badge status-badge--${subject.is_active ? 'active' : 'inactive'}">
                    ${subject.is_active ? 'Aktiv' : 'Inaktiv'}
                </span>
            </td>
            <td>${formatDate(subject.created_at)}</td>
            <td class="actions-cell">
                <button class="action-btn action-btn-edit" data-subject-id="${subject.id}">
                    <i class="fas fa-pen"></i>
                </button>
                <button class="action-btn action-btn-toggle ${subject.is_active ? 'action-btn-toggle--active' : 'action-btn-toggle--inactive'}" data-subject-id="${subject.id}">
                    <i class="fas fa-toggle-${subject.is_active ? 'on' : 'off'}"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to rows for detail view
    document.querySelectorAll('.subjects-table tbody tr').forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.action-btn')) return;
            
            const subjectId = parseInt(row.dataset.subjectId);
            window.location.href = "/admin/knowledge/subjects/" + subjectId + "/topics";
        });
    });
}

/**
 * Format date string for display
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    try {
        const date = new Date(dateString);
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
    // Create subject button
    document.getElementById('create-subject-btn')?.addEventListener('click', showCreateSubjectModal);
    
    // Create subject modal
    document.getElementById('create-subject-close')?.addEventListener('click', hideCreateSubjectModal);
    document.getElementById('create-subject-cancel')?.addEventListener('click', hideCreateSubjectModal);
    document.getElementById('create-subject-submit')?.addEventListener('click', createSubject);
    
    // Edit subject modal
    document.getElementById('edit-subject-close')?.addEventListener('click', hideEditSubjectModal);
    document.getElementById('edit-subject-cancel')?.addEventListener('click', hideEditSubjectModal);
    document.getElementById('edit-subject-submit')?.addEventListener('click', saveEditedSubject);
    
    // Detail subject modal
    document.getElementById('detail-subject-close')?.addEventListener('click', hideDetailSubjectModal);
    document.getElementById('detail-subject-close-btn')?.addEventListener('click', hideDetailSubjectModal);
    
    // Confirmation dialog
    document.getElementById('confirmation-close')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-cancel')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-confirm')?.addEventListener('click', handleConfirmation);
    
    
    // Form validation
    document.getElementById('create-subject-name')?.addEventListener('input', validateSubjectName);
    document.getElementById('edit-subject-name')?.addEventListener('input', validateSubjectName);
    
    // Search input (debounced)
    document.getElementById('subjects-search')?.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearchTerm = e.target.value;
            renderFilteredSubjectsTable();
        }, 300);
    });
    
    // Filter dropdown
    document.getElementById('subjects-filter')?.addEventListener('change', function(e) {
        currentFilter = e.target.value;
        renderFilteredSubjectsTable();
    });
}

/**
 * Show create subject modal
 */
function showCreateSubjectModal() {
    const modal = document.getElementById('create-subject-modal');
    if (modal) {
        modal.style.display = 'block';
        document.getElementById('create-subject-name').value = '';
        document.getElementById('create-subject-name').focus();
    }
}

/**
 * Hide create subject modal
 */
function hideCreateSubjectModal() {
    document.getElementById('create-subject-modal').style.display = 'none';
}

/**
 * Create new subject
 */
async function createSubject() {
    const nameInput = document.getElementById('create-subject-name');
    const name = nameInput.value.trim();
    
    if (!validateSubjectName()) {
        return;
    }
    
    try {
        const response = await fetch(API_URL + '/knowledge/subjects/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                name: name
            })
        });
        
        if (response.ok) {
            const newSubject = await response.json();
            currentSubjects.push(newSubject);
            renderFilteredSubjectsTable();
            hideCreateSubjectModal();
            showToast('Fach erfolgreich erstellt.');
        } else if (response.status === 409) {
            showToast('Ein Fach mit diesem Namen existiert bereits.', 'error');
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Erstellen des Fachs: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show edit subject modal
 * @param {number} subjectId - ID of subject to edit
 */
function showEditSubjectModal(subjectId) {
    const subject = currentSubjects.find(s => s.id === subjectId);
    if (!subject) return;
    
    const modal = document.getElementById('edit-subject-modal');
    if (modal) {
        document.getElementById('edit-subject-id').value = subject.id;
        document.getElementById('edit-subject-name').value = subject.name;
        modal.style.display = 'block';
        document.getElementById('edit-subject-name').focus();
    }
}

/**
 * Hide edit subject modal
 */
function hideEditSubjectModal() {
    document.getElementById('edit-subject-modal').style.display = 'none';
}

/**
 * Save edited subject
 */
async function saveEditedSubject() {
    const subjectId = parseInt(document.getElementById('edit-subject-id').value);
    const nameInput = document.getElementById('edit-subject-name');
    const name = nameInput.value.trim();
    
    if (!validateSubjectName()) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/knowledge/subjects/${subjectId}/edit`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                name: name
            })
        });
        
        if (response.ok) {
            const updatedSubject = await response.json();
            const index = currentSubjects.findIndex(s => s.id === subjectId);
            if (index !== -1) {
                currentSubjects[index] = updatedSubject;
                renderFilteredSubjectsTable();
            }
            hideEditSubjectModal();
            showToast('Fach erfolgreich aktualisiert.');
        } else if (response.status === 409) {
            showToast('Ein Fach mit diesem Namen existiert bereits.', 'error');
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Aktualisieren des Fachs: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show subject detail modal
 * @param {number} subjectId - ID of subject to show details for
 */
function showSubjectDetail(subjectId) {
    const subject = currentSubjects.find(s => s.id === subjectId);
    if (!subject) return;
    
    const modal = document.getElementById('detail-subject-modal');
    if (modal) {
        document.getElementById('detail-subject-id').textContent = subject.id;
        document.getElementById('detail-subject-name').textContent = subject.name;
        document.getElementById('detail-subject-status').textContent = subject.is_active ? 'Aktiv' : 'Inaktiv';
        document.getElementById('detail-subject-created').textContent = formatDate(subject.created_at);
        modal.style.display = 'block';
    }
}

/**
 * Hide detail subject modal
 */
function hideDetailSubjectModal() {
    document.getElementById('detail-subject-modal').style.display = 'none';
}

/**
 * Show confirmation dialog for status toggle
 * @param {number} subjectId - ID of subject to toggle
 * @param {boolean} currentStatus - Current status of subject
 */
function showToggleConfirmation(subjectId, currentStatus) {
    currentAction = 'toggleStatus';
    currentSubjectId = subjectId;
    
    const dialog = document.getElementById('confirmation-dialog');
    const message = document.getElementById('confirmation-message');
    
    if (dialog && message) {
        message.textContent = currentStatus 
            ? 'Bist du sicher, dass du dieses Fach deaktivieren möchtest?'
            : 'Bist du sicher, dass du dieses Fach aktivieren möchtest?';
        dialog.style.display = 'block';
    }
}

/**
 * Hide confirmation dialog
 */
function hideConfirmationDialog() {
    document.getElementById('confirmation-dialog').style.display = 'none';
    currentAction = null;
    currentSubjectId = null;
}

/**
 * Handle confirmation action
 */
async function handleConfirmation() {
    if (!currentAction || currentSubjectId === null) {
        hideConfirmationDialog();
        return;
    }
    
    if (currentAction === 'toggleStatus') {
        await toggleSubjectStatus(currentSubjectId);
    }
    
    hideConfirmationDialog();
}

/**
 * Toggle subject status
 * @param {number} subjectId - ID of subject to toggle
 */
async function toggleSubjectStatus(subjectId) {
    const subject = currentSubjects.find(s => s.id === subjectId);
    if (!subject) return;
    
    const newStatus = !subject.is_active;
    
    try {
        const response = await fetch(`${API_URL}/knowledge/subjects/${subjectId}/status`, {
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
            const updatedSubject = await response.json();
            const index = currentSubjects.findIndex(s => s.id === subjectId);
            if (index !== -1) {
                currentSubjects[index] = updatedSubject;
                renderFilteredSubjectsTable();
                showToast(`Fach ${newStatus ? 'aktiviert' : 'deaktiviert'}.`);
            }
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Umschalten des Status: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Validate subject name
 * Works when called from event listeners or programmatic callers (createSubject, saveEditedSubject)
 * @returns {boolean} - True if valid, false otherwise
 */
function validateSubjectName() {
    const input = document.getElementById('create-subject-name') || document.getElementById('edit-subject-name');
    if (!input) return true;
    const name = input.value.trim();
    const feedback = input.nextElementSibling;
    
    const isValid = name.length >= 3 && name.length <= 100;
    
    if (feedback) {
        if (name.length === 0) {
            feedback.style.display = 'none';
        } else if (!isValid) {
            feedback.style.display = 'block';
        } else {
            feedback.style.display = 'none';
        }
    }
    
    return isValid;
}

// Event delegation for action buttons (since they're dynamically created)
document.addEventListener('click', function(e) {
    // Edit button click
    if (e.target.closest('.action-btn-edit')) {
        const subjectId = parseInt(e.target.closest('.action-btn-edit').dataset.subjectId);
        showEditSubjectModal(subjectId);
    }
    
    // Toggle button click
    if (e.target.closest('.action-btn-toggle')) {
        const subjectId = parseInt(e.target.closest('.action-btn-toggle').dataset.subjectId);
        const subject = currentSubjects.find(s => s.id === subjectId);
        if (subject) {
            showToggleConfirmation(subjectId, subject.is_active);
        }
    }
});