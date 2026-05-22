/**
 * Knowledge Topics Management JavaScript
 * Handles CRUD operations for topics within a subject
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the knowledge topics page
    var container = document.querySelector('.admin-knowledge-topics');
    if (container) {
        var subjectId = parseInt(container.dataset.subjectId);
        if (subjectId) {
            loadSubjectName(subjectId);
            loadTopics(subjectId);
            setupEventListeners(subjectId);
        }
    }
});

// Global variables
var currentTopics = [];
var currentSubjectId = null;
var currentSubjectName = '';
var currentAction = null;
var currentTopicId = null;

/**
 * Load subject name from API and update page
 * @param {number} subjectId - ID of the subject
 */
async function loadSubjectName(subjectId) {
    try {
        var response = await fetch('/api/v1/knowledge/subjects/list-all');
        
        if (response.ok) {
            var data = await response.json();
            var subjects = data.subjects || [];
            var subject = subjects.find(function(s) { return s.id === subjectId; });
            
            if (subject) {
                currentSubjectName = subject.name;
                currentSubjectId = subjectId;
                
                // Update page title
                var pageTitle = document.getElementById('topics-page-title');
                if (pageTitle) {
                    pageTitle.textContent = 'Topics for ' + subject.name;
                }
                
                // Update breadcrumb
                var breadcrumbName = document.getElementById('breadcrumb-subject-name');
                if (breadcrumbName) {
                    breadcrumbName.textContent = subject.name;
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
                currentSubjectName = 'Subject #' + subjectId;
                var pageTitle = document.getElementById('topics-page-title');
                if (pageTitle) pageTitle.textContent = 'Topics for Subject #' + subjectId;
                var breadcrumbName = document.getElementById('breadcrumb-subject-name');
                if (breadcrumbName) breadcrumbName.textContent = 'Subject #' + subjectId;
            }
        } else {
            showToast('Error loading subject details. Please try again.', true);
        }
    } catch (error) {
        currentSubjectName = 'Subject #' + subjectId;
        var pageTitle = document.getElementById('topics-page-title');
        if (pageTitle) pageTitle.textContent = 'Topics for Subject #' + subjectId;
        var breadcrumbName = document.getElementById('breadcrumb-subject-name');
        if (breadcrumbName) breadcrumbName.textContent = 'Subject #' + subjectId;
        console.error('Error loading subject name:', error);
    }
}

/**
 * Load topics from API and populate the table
 * @param {number} subjectId - ID of the subject
 */
async function loadTopics(subjectId) {
    try {
        var response = await fetch('/api/v1/knowledge/subjects/' + subjectId + '/topics/list-all');
        
        if (response.ok) {
            var data = await response.json();
            currentTopics = data.topics || [];
            renderTopicsTable();
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else {
            showToast('Error loading topics. Please try again.', true);
            console.error('Error loading topics:', response.status);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
        console.error('Network error:', error);
    }
}

/**
 * Render topics table with data
 */
function renderTopicsTable() {
    var tableBody = document.getElementById('topics-table-body');
    
    if (!tableBody) return;
    
    // Clear loading row
    tableBody.innerHTML = '';
    
    if (currentTopics.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No topics found. Click "Create Topic" to add your first topic.</td></tr>';
        return;
    }
    
    // Sort topics by ID
    currentTopics.sort(function(a, b) { return a.id - b.id; });
    
    // Render each topic
    currentTopics.forEach(function(topic) {
        var row = document.createElement('tr');
        row.dataset.topicId = topic.id;
        
        row.innerHTML = '<td>' + topic.id + '</td>' +
            '<td>' + escapeHtml(topic.name) + '</td>' +
            '<td>' + (topic.expected_grade || 'N/A') + '</td>' +
            '<td><span class="status-badge status-badge--' + (topic.is_active ? 'active' : 'inactive') + '">' + (topic.is_active ? 'Active' : 'Inactive') + '</span></td>' +
            '<td>' + formatDate(topic.created_at) + '</td>' +
            '<td class="actions-cell">' +
                '<button class="action-btn action-btn-edit" data-topic-id="' + topic.id + '"><i class="fas fa-edit"></i> Edit</button>' +
                '<button class="action-btn action-btn-toggle" data-topic-id="' + topic.id + '"><i class="fas fa-toggle-' + (topic.is_active ? 'on' : 'off') + '"></i> ' + (topic.is_active ? 'Deactivate' : 'Activate') + '</button>' +
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
 * @param {number} subjectId - ID of the subject
 */
function setupEventListeners(subjectId) {
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
    
    // Toast notification
    document.getElementById('toast-close')?.addEventListener('click', hideToast);
}

/**
 * Show create topic modal
 */
function showCreateTopicModal() {
    var modal = document.getElementById('create-topic-modal');
    if (modal) {
        document.getElementById('create-topic-name').value = '';
        document.getElementById('create-topic-grade').value = '';
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
        showToast('Please select a valid expected grade (1-13).', true);
        return;
    }
    
    try {
        var response = await fetch('/api/v1/knowledge/subjects/' + currentSubjectId + '/topics/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                expected_grade: parseInt(grade)
            })
        });
        
        if (response.ok) {
            var newTopic = await response.json();
            currentTopics.push(newTopic);
            renderTopicsTable();
            hideCreateTopicModal();
            showToast('Topic created successfully!');
        } else if (response.status === 409) {
            showToast('Topic with this name already exists.', true);
        } else {
            var errorData = await response.json();
            showToast('Error creating topic: ' + (errorData.message || 'Unknown error'), true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
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
        showToast('Please select a valid expected grade (1-13).', true);
        return;
    }
    
    try {
        var response = await fetch('/api/v1/knowledge/subjects/' + currentSubjectId + '/topics/' + topicId + '/edit', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                expected_grade: parseInt(grade)
            })
        });
        
        if (response.ok) {
            var updatedTopic = await response.json();
            var index = currentTopics.findIndex(function(t) { return t.id === topicId; });
            if (index !== -1) {
                currentTopics[index] = updatedTopic;
                renderTopicsTable();
            }
            hideEditTopicModal();
            showToast('Topic updated successfully!');
        } else if (response.status === 409) {
            showToast('Topic with this name already exists.', true);
        } else {
            var errorData = await response.json();
            showToast('Error updating topic: ' + (errorData.message || 'Unknown error'), true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
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
        document.getElementById('detail-topic-status').textContent = topic.is_active ? 'Active' : 'Inactive';
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
            ? 'Are you sure you want to deactivate this topic?'
            : 'Are you sure you want to activate this topic?';
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
        var response = await fetch('/api/v1/knowledge/subjects/' + currentSubjectId + '/topics/' + topicId, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
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
                renderTopicsTable();
                showToast('Topic ' + (newStatus ? 'activated' : 'deactivated') + ' successfully!');
            }
        } else if (response.status === 401) {
            window.location.href = '/login';
        } else {
            var errorData = await response.json();
            showToast('Error toggling status: ' + (errorData.message || 'Unknown error'), true);
        }
    } catch (error) {
        showToast('Network error. Please check your connection.', true);
        console.error('Network error:', error);
    }
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {boolean} isError - Whether this is an error message
 */
function showToast(message, isError) {
    if (isError === undefined) isError = false;
    
    var toast = document.getElementById('toast-notification');
    var toastMessage = document.getElementById('toast-message');
    
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
    var toast = document.getElementById('toast-notification');
    if (toast) {
        toast.style.display = 'none';
    }
}

// Event delegation for action buttons (since they're dynamically created)
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