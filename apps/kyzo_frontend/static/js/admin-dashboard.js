/**
 * Admin Dashboard JavaScript
 * Fetches statistics from API and updates the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the admin dashboard page
    if (document.querySelector('.admin-dashboard')) {
        loadDashboardStatistics();
    }
});

/**
 * Load dashboard statistics from API
 */
async function loadDashboardStatistics() {
    try {
        // Fetch total users
        const usersResponse = await fetch('/api/v1/users/list-all', {
            headers: getAuthHeader()
        });
        let totalUsers = 0;
        let activeUsers = 0;
        if (usersResponse.ok) {
            const usersData = await usersResponse.json();
            totalUsers = Array.isArray(usersData) ? usersData.length : 0;
            updateStatCard('total-users', totalUsers);
            activeUsers = Array.isArray(usersData)
                ? usersData.filter(u => u.is_active === true).length
                : 0;
            updateStatCard('active-users', activeUsers);
        }

        // Fetch total subjects
        const subjectsResponse = await fetch('/api/v1/knowledge/subjects/list-all', {
            headers: getAuthHeader()
        });
        if (subjectsResponse.ok) {
            const subjectsData = await subjectsResponse.json();
            const totalSubjects = Array.isArray(subjectsData) ? subjectsData.length : 0;
            updateStatCard('total-subjects', totalSubjects);

            // Calculate total topics from subjects data
            let totalTopics = 0;
            if (Array.isArray(subjectsData)) {
                subjectsData.forEach(subject => {
                    if (subject.topics && subject.topics.length) {
                        totalTopics += subject.topics.length;
                    }
                });
            }
            updateStatCard('total-topics', totalTopics);
        }

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
