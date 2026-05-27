/**
 * Users Management JavaScript
 * Handles CRUD operations for users
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the users management page
    if (document.querySelector('.admin-users')) {
        loadUsers();
        setupEventListeners();
    }
});

// Global variables
let currentUsers = [];

// SVG icon helper (replaces Font Awesome)
function svgIcon(name) {
    return '<img src="/static/svg/' + name + '.svg" alt="" width="16" height="16" class="icon icon--' + name + '">';
}
let currentAction = null;
let currentUserId = null;
let currentSearchTerm = '';
let currentFilter = 'all';
let searchTimeout = null;

/**
 * Load all users from API and populate the table
 */
async function loadUsers() {
    try {
        const response = await fetch(API_URL + '/users/list-all', {
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUsers = Array.isArray(data) ? data : [];
            renderFilteredUsersTable();
        } else {
            showToast('Fehler beim Laden der Benutzer. Bitte versuche es erneut.', 'error');
            console.error('Error loading users:', response.status);
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Render users table with search and filter applied
 */
function renderFilteredUsersTable() {
    const tableBody = document.getElementById('users-table-body');
    
    if (!tableBody) return;
    
    // Clear loading row
    tableBody.innerHTML = '';
    
    // Apply search and filter
    let filtered = currentUsers.filter(user => {
        // Apply search filter (name AND email)
        const matchesSearch = currentSearchTerm === '' ||
            (user.name && user.name.toLowerCase().includes(currentSearchTerm.toLowerCase())) ||
            (user.email && user.email.toLowerCase().includes(currentSearchTerm.toLowerCase()));
        
        // Apply status filter
        let matchesFilter = true;
        if (currentFilter === 'active') {
            matchesFilter = user.is_active !== false;
        } else if (currentFilter === 'inactive') {
            matchesFilter = user.is_active === false;
        }
        
        return matchesSearch && matchesFilter;
    });
    
    if (filtered.length === 0) {
        const emptyMessage = currentSearchTerm || currentFilter !== 'all'
            ? 'Keine Ergebnisse'
            : 'Keine Benutzer gefunden. Klicke \'Benutzer erstellen\' um deinen ersten Benutzer hinzuzufügen.';
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px;">
                    ${emptyMessage}
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort filtered users by ID
    filtered.sort((a, b) => a.id - b.id);
    
    // Render each user
    filtered.forEach(user => {
        const row = document.createElement('tr');
        row.dataset.userId = user.id;
        
        const roleClass = `role-badge--${user.role || 'student'}`;
        const roleLabels = { student: 'Schüler', teacher: 'Lehrer', admin: 'Administrator' };
        const statusClass = user.is_active !== false ? 'status-badge--active' : 'status-badge--inactive';
        const statusText = user.is_active !== false ? 'Aktiv' : 'Inaktiv';
        const grade = user.grade || 'N/A';
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${escapeHtml(user.name || '')}</td>
            <td>${escapeHtml(user.email || '')}</td>
            <td><span class="role-badge ${roleClass}">${escapeHtml(roleLabels[user.role] || user.role)}</span></td>
            <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            <td>${escapeHtml(String(grade))}</td>
            <td class="actions-cell">
                <button class="action-btn action-btn-edit" data-user-id="${user.id}">
                    ${svgIcon('pencil-solid-full')}
                </button>
                <button class="action-btn action-btn-toggle ${user.is_active !== false ? 'action-btn-toggle--active' : 'action-btn-toggle--inactive'}" data-user-id="${user.id}">
                    ${svgIcon('toggle-' + (user.is_active !== false ? 'on' : 'off') + '-solid-full')}
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to rows for detail view
    document.querySelectorAll('.users-table tbody tr').forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.action-btn')) return;
            
            const userId = parseInt(row.dataset.userId);
            showUserDetail(userId);
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
    const div = document.createElement('div');
    div.textContent = text;
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
    // Create user button
    document.getElementById('create-user-btn')?.addEventListener('click', showCreateUserModal);
    
    // Create user modal
    document.getElementById('create-user-close')?.addEventListener('click', hideCreateUserModal);
    document.getElementById('create-user-cancel')?.addEventListener('click', hideCreateUserModal);
    document.getElementById('create-user-submit')?.addEventListener('click', createUser);
    
    // Edit user modal
    document.getElementById('edit-user-close')?.addEventListener('click', hideEditUserModal);
    document.getElementById('edit-user-cancel')?.addEventListener('click', hideEditUserModal);
    document.getElementById('edit-user-submit')?.addEventListener('click', saveEditedUser);
    
    // Detail user modal
    document.getElementById('detail-user-close')?.addEventListener('click', hideDetailUserModal);
    document.getElementById('detail-user-close-btn')?.addEventListener('click', hideDetailUserModal);
    
    // Confirmation dialog
    document.getElementById('confirmation-close')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-cancel')?.addEventListener('click', hideConfirmationDialog);
    document.getElementById('confirmation-confirm')?.addEventListener('click', handleConfirmation);
    
    
    // Search input (debounced)
    document.getElementById('users-search')?.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentSearchTerm = e.target.value;
            renderFilteredUsersTable();
        }, 300);
    });
    
    // Filter dropdown
    document.getElementById('users-filter')?.addEventListener('change', function(e) {
        currentFilter = e.target.value;
        renderFilteredUsersTable();
    });
}

/**
 * Show create user modal
 */
function showCreateUserModal() {
    const modal = document.getElementById('create-user-modal');
    if (modal) {
        // Clear form
        document.getElementById('create-user-name').value = '';
        document.getElementById('create-user-email').value = '';
        document.getElementById('create-user-password').value = '';
        document.getElementById('create-user-grade').value = '';
        document.getElementById('create-user-role').value = '';
        
        // Clear errors
        document.querySelectorAll('#create-user-form .form-error').forEach(el => el.textContent = '');
        document.querySelectorAll('#create-user-form .form-control').forEach(el => el.removeAttribute('aria-invalid'));
        
        modal.style.display = 'block';
        document.getElementById('create-user-name').focus();
    }
}

/**
 * Hide create user modal
 */
function hideCreateUserModal() {
    document.getElementById('create-user-modal').style.display = 'none';
}

/**
 * Create new user
 */
async function createUser() {
    const nameInput = document.getElementById('create-user-name');
    const emailInput = document.getElementById('create-user-email');
    const passwordInput = document.getElementById('create-user-password');
    const gradeInput = document.getElementById('create-user-grade');
    const roleInput = document.getElementById('create-user-role');
    
    // Clear previous errors
    document.querySelectorAll('#create-user-form .form-error').forEach(el => el.textContent = '');
    document.querySelectorAll('#create-user-form .form-control').forEach(el => el.removeAttribute('aria-invalid'));
    
    let isValid = true;
    
    // Validate name
    const name = nameInput.value.trim();
    if (name.length < 3 || name.length > 100) {
        document.getElementById('create-user-name-error').textContent = 'Name muss zwischen 3 und 100 Zeichen lang sein.';
        nameInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate email
    const email = emailInput.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        document.getElementById('create-user-email-error').textContent = 'Bitte geben Sie eine gültige E-Mail-Adresse ein.';
        emailInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate password
    const password = passwordInput.value;
    if (password.length < 8) {
        document.getElementById('create-user-password-error').textContent = 'Passwort muss mindestens 8 Zeichen lang sein.';
        passwordInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate grade
    const grade = gradeInput.value;
    if (!grade) {
        document.getElementById('create-user-grade-error').textContent = 'Bitte wählen Sie eine Klasse aus.';
        gradeInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate role
    const role = roleInput.value;
    if (!role) {
        document.getElementById('create-user-role-error').textContent = 'Bitte wählen Sie eine Rolle aus.';
        roleInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    if (!isValid) return;
    
    try {
        const response = await fetch(API_URL + '/users/register-staff', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify({
                name: name,
                email: email,
                password: password,
                grade: parseInt(grade),
                role: role
            })
        });
        
        if (response.ok) {
            const newUser = await response.json();
            currentUsers.push(newUser);
            renderFilteredUsersTable();
            hideCreateUserModal();
            showToast('Benutzer erfolgreich erstellt.');
        } else if (response.status === 409) {
            showToast('Ein Benutzer mit dieser E-Mail existiert bereits.', 'error');
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Erstellen des Benutzers: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show edit user modal
 * @param {number} userId - ID of user to edit
 */
function showEditUserModal(userId) {
    const user = currentUsers.find(u => u.id === userId);
    if (!user) return;
    
    const modal = document.getElementById('edit-user-modal');
    if (modal) {
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-user-name').value = user.name || '';
        document.getElementById('edit-user-email').value = user.email || '';
        document.getElementById('edit-user-grade').value = user.grade || '';
        document.getElementById('edit-user-role').value = user.role || 'student';
        
        // Clear errors
        document.querySelectorAll('#edit-user-form .form-error').forEach(el => el.textContent = '');
        document.querySelectorAll('#edit-user-form .form-control').forEach(el => el.removeAttribute('aria-invalid'));
        
        modal.style.display = 'block';
    }
}

/**
 * Hide edit user modal
 */
function hideEditUserModal() {
    document.getElementById('edit-user-modal').style.display = 'none';
}

/**
 * Save edited user
 */
async function saveEditedUser() {
    const userId = parseInt(document.getElementById('edit-user-id').value);
    const nameInput = document.getElementById('edit-user-name');
    const emailInput = document.getElementById('edit-user-email');
    const gradeInput = document.getElementById('edit-user-grade');
    const roleInput = document.getElementById('edit-user-role');
    
    // Clear previous errors
    document.querySelectorAll('#edit-user-form .form-error').forEach(el => el.textContent = '');
    document.querySelectorAll('#edit-user-form .form-control').forEach(el => el.removeAttribute('aria-invalid'));
    
    let isValid = true;
    
    // Validate name
    const name = nameInput.value.trim();
    if (name.length < 3 || name.length > 100) {
        document.getElementById('edit-user-name-error').textContent = 'Name muss zwischen 3 und 100 Zeichen lang sein.';
        nameInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate email
    const email = emailInput.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        document.getElementById('edit-user-email-error').textContent = 'Bitte geben Sie eine gültige E-Mail-Adresse ein.';
        emailInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate grade
    const grade = gradeInput.value;
    if (!grade) {
        document.getElementById('edit-user-grade-error').textContent = 'Bitte wählen Sie eine Klasse aus.';
        gradeInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    // Validate role
    const role = roleInput.value;
    if (!role) {
        document.getElementById('edit-user-role-error').textContent = 'Bitte wählen Sie eine Rolle aus.';
        roleInput.setAttribute('aria-invalid', 'true');
        isValid = false;
    }
    
    if (!isValid) return;
    
    // Build payload with only changed fields
    const payload = {};
    if (name !== (currentUsers.find(u => u.id === userId)?.name || '')) {
        payload.name = name;
    }
    if (email !== (currentUsers.find(u => u.id === userId)?.email || '')) {
        payload.email = email;
    }
    if (grade !== String(currentUsers.find(u => u.id === userId)?.grade || '')) {
        payload.grade = parseInt(grade);
    }
    if (role !== (currentUsers.find(u => u.id === userId)?.role || '')) {
        payload.role = role;
    }
    
    if (Object.keys(payload).length === 0) {
        hideEditUserModal();
        showToast('Keine Änderungen zum Speichern.');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/users/${userId}/edit`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const updatedUser = await response.json();
            const index = currentUsers.findIndex(u => u.id === userId);
            if (index !== -1) {
                currentUsers[index] = updatedUser;
                renderFilteredUsersTable();
            }
            hideEditUserModal();
            showToast('Benutzer erfolgreich aktualisiert.');
        } else if (response.status === 409) {
            showToast('Ein Benutzer mit dieser E-Mail existiert bereits.', 'error');
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Aktualisieren des Benutzers: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

/**
 * Show user detail modal
 * @param {number} userId - ID of user to show details for
 */
function showUserDetail(userId) {
    const user = currentUsers.find(u => u.id === userId);
    if (!user) return;
    
    const modal = document.getElementById('detail-user-modal');
    if (modal) {
        document.getElementById('detail-user-id').textContent = user.id;
        document.getElementById('detail-user-name').textContent = user.name || 'N/A';
        document.getElementById('detail-user-email').textContent = user.email || 'N/A';
        const roleLabels = { student: 'Schüler', teacher: 'Lehrer', admin: 'Administrator' };
        document.getElementById('detail-user-role').textContent = roleLabels[user.role] || (user.role || 'student').charAt(0).toUpperCase() + (user.role || 'student').slice(1);
        document.getElementById('detail-user-status').textContent = user.is_active !== false ? 'Aktiv' : 'Inaktiv';
        document.getElementById('detail-user-grade').textContent = user.grade || 'N/A';
        document.getElementById('detail-user-created').textContent = formatDate(user.created_at);
        modal.style.display = 'block';
    }
}

/**
 * Hide detail user modal
 */
function hideDetailUserModal() {
    document.getElementById('detail-user-modal').style.display = 'none';
}

/**
 * Show confirmation dialog for status toggle
 * @param {number} userId - ID of user to toggle
 * @param {boolean} currentStatus - Current status of user
 */
function showToggleConfirmation(userId, currentStatus) {
    currentAction = 'toggleStatus';
    currentUserId = userId;
    
    const dialog = document.getElementById('confirmation-dialog');
    const message = document.getElementById('confirmation-message');
    
    if (dialog && message) {
        message.textContent = currentStatus 
            ? 'Sind Sie sicher, dass Sie diesen Benutzer deaktivieren möchten?'
            : 'Sind Sie sicher, dass Sie diesen Benutzer aktivieren möchten?';
        dialog.style.display = 'block';
    }
}

/**
 * Hide confirmation dialog
 */
function hideConfirmationDialog() {
    document.getElementById('confirmation-dialog').style.display = 'none';
    currentAction = null;
    currentUserId = null;
}

/**
 * Handle confirmation action
 */
async function handleConfirmation() {
    if (!currentAction || currentUserId === null) {
        hideConfirmationDialog();
        return;
    }
    
    if (currentAction === 'toggleStatus') {
        await toggleUserStatus(currentUserId);
    }
    
    hideConfirmationDialog();
}

/**
 * Toggle user status
 * @param {number} userId - ID of user to toggle
 */
async function toggleUserStatus(userId) {
    const user = currentUsers.find(u => u.id === userId);
    if (!user) return;
    
    const newStatus = !user.is_active;
    
    try {
        const response = await fetch(`${API_URL}/users/${userId}/status?active=${newStatus}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader(),
            }
        });
        
        if (response.ok) {
            const updatedUser = await response.json();
            const index = currentUsers.findIndex(u => u.id === userId);
            if (index !== -1) {
                currentUsers[index] = updatedUser;
                renderFilteredUsersTable();
            }
            showToast(`Benutzer ${newStatus ? 'aktiviert' : 'deaktiviert'}.`);
        } else {
            const errorData = await response.json();
            showToast(`Fehler beim Umschalten des Status: ${errorData.message || 'Unbekannter Fehler'}`, 'error');
        }
    } catch (error) {
        showToast('Netzwerkfehler. Bitte überprüfe deine Verbindung.', 'error');
        console.error('Network error:', error);
    }
}

// Event delegation for action buttons (since they're dynamically created)
document.addEventListener('click', function(e) {
    // Edit button click
    if (e.target.closest('.action-btn-edit')) {
        const userId = parseInt(e.target.closest('.action-btn-edit').dataset.userId);
        showEditUserModal(userId);
    }
    
    // Toggle button click
    if (e.target.closest('.action-btn-toggle')) {
        const userId = parseInt(e.target.closest('.action-btn-toggle').dataset.userId);
        const user = currentUsers.find(u => u.id === userId);
        if (user) {
            showToggleConfirmation(userId, user.is_active !== false);
        }
    }
});
