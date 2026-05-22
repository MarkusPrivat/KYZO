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

/**
 * Load subjects from API and populate the table
 */
async function loadSubjects() {
    try {
        const response = await fetch('/api/v1/knowledge/subjects/list-all');
        
        if (response.ok) {
            const data = await response.json();
            currentSubjects = data.subjects || [];
            renderSubjectsTable();
        } else {
            showToast('Error loading subjects. Please try again.', true);
            console.error('Error loading subjects:', response.status);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
        console.error('Network error:', error);
    }
}

/**
 * Render subjects table with data
 */
function renderSubjectsTable() {
    const tableBody = document.getElementById('subjects-table-body');
    
    if (!tableBody) return;
    
    // Clear loading row
    tableBody.innerHTML = '';
    
    if (currentSubjects.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px;">
                    No subjects found. Click "Create Subject" to add your first subject.
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort subjects by ID
    currentSubjects.sort((a, b) => a.id - b.id);
    
    // Render each subject
    currentSubjects.forEach(subject => {
        const row = document.createElement('tr');
        row.dataset.subjectId = subject.id;
        
        row.innerHTML = `
            <td>${subject.id}</td>
            <td>${subject.name}</td>
            <td>
                <span class="status-badge status-badge--${subject.is_active ? 'active' : 'inactive'}">
                    ${subject.is_active ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${formatDate(subject.created_at)}</td>
            <td class="actions-cell">
                <button class="action-btn action-btn-edit" data-subject-id="${subject.id}">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="action-btn action-btn-toggle" data-subject-id="${subject.id}">
                    <i class="fas fa-toggle-${subject.is_active ? 'on' : 'off'}"></i> 
                    ${subject.is_active ? 'Deactivate' : 'Activate'}
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
    
    // Toast notification
    document.getElementById('toast-close')?.addEventListener('click', hideToast);
    
    // Form validation
    document.getElementById('create-subject-name')?.addEventListener('input', validateSubjectName);
    document.getElementById('edit-subject-name')?.addEventListener('input', validateSubjectName);
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
        const response = await fetch('/api/v1/knowledge/subjects/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name
            })
        });
        
        if (response.ok) {
            const newSubject = await response.json();
            currentSubjects.push(newSubject);
            renderSubjectsTable();
            hideCreateSubjectModal();
            showToast('Subject created successfully!');
        } else if (response.status === 409) {
            showToast('Subject with this name already exists.', true);
        } else {
            const errorData = await response.json();
            showToast(`Error creating subject: ${errorData.message || 'Unknown error'}`, true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
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
        const response = await fetch(`/api/v1/knowledge/subjects/${subjectId}/edit`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
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
                renderSubjectsTable();
            }
            hideEditSubjectModal();
            showToast('Subject updated successfully!');
        } else if (response.status === 409) {
            showToast('Subject with this name already exists.', true);
        } else {
            const errorData = await response.json();
            showToast(`Error updating subject: ${errorData.message || 'Unknown error'}`, true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
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
        document.getElementById('detail-subject-status').textContent = subject.is_active ? 'Active' : 'Inactive';
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
            ? 'Are you sure you want to deactivate this subject?'
            : 'Are you sure you want to activate this subject?';
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
        const response = await fetch(`/api/v1/knowledge/subjects/${subjectId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
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
                renderSubjectsTable();
                showToast(`Subject ${newStatus ? 'activated' : 'deactivated'} successfully!`);
            }
        } else {
            const errorData = await response.json();
            showToast(`Error toggling status: ${errorData.message || 'Unknown error'}`, true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
        console.error('Network error:', error);
    }
}

/**
 * Validate subject name
 * @returns {boolean} - True if valid, false otherwise
 */
function validateSubjectName() {
    const input = event.target;
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

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {boolean} isError - Whether this is an error message
 */
function showToast(message, isError = false) {
    const toast = document.getElementById('toast-notification');
    const toastMessage = document.getElementById('toast-message');
    
    if (toast && toastMessage) {
        toastMessage.textContent = message;
        
        if (isError) {
            toast.classList.add('toast-error');
            toast.classList.remove('toast-success');
        } else {
            toast.classList.add('toast-success');
            toast.classList.remove('toast-error');
        }
        
        toast.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(hideToast, 5000);
    }
}

/**
 * Hide toast notification
 */
function hideToast() {
    const toast = document.getElementById('toast-notification');
    if (toast) {
        toast.style.display = 'none';
    }
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