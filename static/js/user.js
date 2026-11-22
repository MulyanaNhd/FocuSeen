// ========================================
// NOTIFICATION SYSTEM
// ========================================

let notificationInterval = null;

function toggleNotifications() {
    const dropdown = document.querySelector('.notification-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
        if (dropdown.classList.contains('show')) {
            loadNotifications();
        }
    }
}

async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        if (response.ok) {
            const data = await response.json();
            displayNotifications(data.notifications, data.unread_count);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function displayNotifications(notifications, unreadCount) {
    const container = document.querySelector('.notification-list');
    const badge = document.querySelector('.notification-badge');
    
    if (badge) {
        if (unreadCount > 0) {
            badge.textContent = unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
    
    if (container) {
        if (notifications.length === 0) {
            container.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>Tidak ada notifikasi</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        notifications.forEach(notif => {
            const date = new Date(notif.created_at);
            const timeAgo = getTimeAgo(date);
            
            html += `
                <div class="notification-item ${notif.is_read ? '' : 'unread'}" 
                     data-id="${notif.id}" onclick="markAsRead(${notif.id})">
                    <div class="notification-icon">
                        <i class="fas fa-${notif.type === 'deadline' ? 'clock' : notif.type === 'reminder' ? 'bell' : 'info-circle'}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-message">${notif.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                    ${notif.is_read ? '' : '<span class="notification-dot"></span>'}
                </div>
            `;
        });
        
        container.innerHTML = html;
    }
}

function getTimeAgo(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} hari yang lalu`;
    if (hours > 0) return `${hours} jam yang lalu`;
    if (minutes > 0) return `${minutes} menit yang lalu`;
    return 'Baru saja';
}

async function markAsRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        
        // Update UI
        const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
        if (item) {
            item.classList.remove('unread');
            item.querySelector('.notification-dot')?.remove();
        }
        
        // Reload notifications
        loadNotifications();
    } catch (error) {
        console.error('Error marking as read:', error);
    }
}

// Auto-refresh notifications every 30 seconds
function startNotificationRefresh() {
    notificationInterval = setInterval(loadNotifications, 30000);
}

function stopNotificationRefresh() {
    if (notificationInterval) {
        clearInterval(notificationInterval);
    }
}

// ========================================
// PROGRESS TRACKING
// ========================================

async function updateTaskProgress(tugasId, progress) {
    try {
        const response = await fetch(`/api/user-tugas/${tugasId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({progress: progress})
        });
        
        if (response.ok) {
            showSuccess('Progress berhasil diupdate!');
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error updating progress:', error);
        showError('Gagal update progress');
        return false;
    }
}

async function addTaskNote(tugasId, note) {
    try {
        const response = await fetch(`/api/user-tugas/${tugasId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({notes: note})
        });
        
        if (response.ok) {
            showSuccess('Catatan berhasil ditambahkan!');
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error adding note:', error);
        showError('Gagal menambahkan catatan');
        return false;
    }
}

// ========================================
// BOOKMARK SYSTEM
// ========================================

async function toggleTaskBookmark(tugasId, element) {
    try {
        const response = await fetch(`/api/bookmark/${tugasId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        if (response.ok) {
            const data = await response.json();
            updateBookmarkUI(element, data.bookmarked);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error toggling bookmark:', error);
        showError('Gagal update bookmark');
        return false;
    }
}

function updateBookmarkUI(element, isBookmarked) {
    const icon = element.querySelector('i');
    if (isBookmarked) {
        icon.className = 'fas fa-bookmark bookmarked';
        showSuccess('Tugas ditambahkan ke bookmark!');
    } else {
        icon.className = 'fas fa-bookmark';
        showSuccess('Tugas dihapus dari bookmark!');
    }
}

// ========================================
// UI HELPERS
// ========================================

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to body
    document.body.appendChild(toast);
    
    // Show
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    // Auto hide after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// ========================================
// PAGE LOAD
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Start notification refresh if user is logged in
    const isLoggedIn = document.body.dataset.loggedIn === 'true';
    if (isLoggedIn) {
        startNotificationRefresh();
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const notificationBell = document.querySelector('.notification-bell');
        const notificationDropdown = document.querySelector('.notification-dropdown');
        
        if (notificationDropdown && notificationDropdown.classList.contains('show')) {
            if (!notificationBell.contains(e.target) && !notificationDropdown.contains(e.target)) {
                notificationDropdown.classList.remove('show');
            }
        }
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopNotificationRefresh();
});