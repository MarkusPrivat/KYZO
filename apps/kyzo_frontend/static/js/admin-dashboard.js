/**
 * Admin Dashboard JavaScript
 * Fetches statistics from API and updates the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the admin dashboard page
    if (document.querySelector('.admin-dashboard')) {
        loadDashboardStatistics();
        setupQuickLinks();
    }
});

/**
 * Load dashboard statistics from API
 */
async function loadDashboardStatistics() {
    try {
        // Fetch total users
        const usersResponse = await fetch('/api/v1/users/list-all');
        if (usersResponse.ok) {
            const usersData = await usersResponse.json();
            const totalUsers = usersData.users ? usersData.users.length : 0;
            updateStatCard('total-users', totalUsers);
        }
        
        // Fetch total subjects
        const subjectsResponse = await fetch('/api/v1/knowledge/subjects/list-all');
        if (subjectsResponse.ok) {
            const subjectsData = await subjectsResponse.json();
            const totalSubjects = subjectsData.subjects ? subjectsData.subjects.length : 0;
            updateStatCard('total-subjects', totalSubjects);
            
            // Calculate total topics from subjects data
            let totalTopics = 0;
            if (subjectsData.subjects) {
                subjectsData.subjects.forEach(subject => {
                    if (subject.topics && subject.topics.length) {
                        totalTopics += subject.topics.length;
                    }
                });
            }
            updateStatCard('total-topics', totalTopics);
        }
        
        // Fetch active users (filtered count)
        // For now, we'll use the same users count as active users
        // In a real implementation, this would be a separate API endpoint
        const activeUsers = totalUsers || 0;
        updateStatCard('active-users', activeUsers);
        
    } catch (error) {
        console.error('Error loading dashboard statistics:', error);
        // Show error state in UI
        const statCards = document.querySelectorAll('.admin-stat__value');
        statCards.forEach(card => {
            if (card.textContent === '0') {
                card.textContent = 'N/A';
                card.style.color = '#dc3545';
            }
        });
    }
}

/**
 * Update a statistic card with new value
 * @param {string} cardId - The ID of the card to update
 * @param {number} value - The value to display
 */
function updateStatCard(cardId, value) {
    const card = document.getElementById(cardId);
    if (card) {
        card.textContent = value.toString();
    }
}

/**
 * Set up quick link navigation
 */
function setupQuickLinks() {
    // Knowledge management quick link
    const knowledgeLink = document.getElementById('quick-link-knowledge');
    if (knowledgeLink) {
        knowledgeLink.addEventListener('click', function(e) {
            e.preventDefault();
            // Navigate to knowledge management section
            // This would typically change the sidebar tab and load the appropriate content
            console.log('Navigate to Knowledge Management');
            // In a real implementation, this would trigger a route change or load content dynamically
        });
    }
    
    // Users management quick link
    const usersLink = document.getElementById('quick-link-users');
    if (usersLink) {
        usersLink.addEventListener('click', function(e) {
            e.preventDefault();
            // Navigate to users management section
            console.log('Navigate to Users Management');
            // In a real implementation, this would trigger a route change or load content dynamically
        });
    }
}