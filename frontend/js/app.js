/** app.js - Core Utilities */

// Check authentication
function checkAuth() {
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = 'index.html';
        return null;
    }
    return token;
}

// Custom Fetch Wrapper
async function apiCall(endpoint, options = {}) {
    const token = checkAuth();
    if (!token) return;

    const defaultHeaders = {
        'Authorization': `Bearer ${token}`
    };

    // Auto-set Content-Type for JSON unless it's FormData (which sets its own boundary)
    if (!(options.body instanceof FormData)) {
        defaultHeaders['Content-Type'] = 'application/json';
    }

    const mergedOptions = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, mergedOptions);

        // Handle 401 Unauthorized globally
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            window.location.href = 'index.html';
            throw new Error('Session expired. Please log in again.');
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.detail || `Error: ${response.status}`);
        }

        return data;

    } catch (error) {
        showToast(error.message, 'error');
        throw error;
    }
}

// Toast Notification System
let toastCounter = 0;
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toastId = `toast - ${++toastCounter}`;
    const toast = document.createElement('div');
    toast.className = `toast ${type} `;
    toast.id = toastId;

    // Icons
    const iconStr = type === 'success'
        ? `< svg xmlns = "http://www.w3.org/2000/svg" width = "24" height = "24" viewBox = "0 0 24 24" fill = "none" stroke = "currentColor" stroke - width="2" stroke - linecap="round" stroke - linejoin="round" class="lucide lucide-check-circle" ><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg > `
        : `< svg xmlns = "http://www.w3.org/2000/svg" width = "24" height = "24" viewBox = "0 0 24 24" fill = "none" stroke = "currentColor" stroke - width="2" stroke - linecap="round" stroke - linejoin="round" class="lucide lucide-alert-circle" ><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg > `;

    toast.innerHTML = `
        < div class="toast-content" >
            ${iconStr}
    <span>${message}</span>
        </div >
        <button class="toast-close" onclick="closeToast('${toastId}')">&times;</button>
    `;

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        closeToast(toastId);
    }, 4000);
}

function closeToast(id) {
    const toast = document.getElementById(id);
    if (toast) {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300); // Wait for animation
    }
}

// Setup common logout functionality
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('authToken');
            window.location.href = 'index.html';
        });
    }

    // Toggle dropdown menus
    document.addEventListener('click', (e) => {
        const isDropdownBtn = e.target.closest('#userMenuBtn');
        const userMenu = document.getElementById('userMenu');

        if (isDropdownBtn && userMenu) {
            userMenu.classList.toggle('show');
        } else if (userMenu) {
            userMenu.classList.remove('show');
        }
    });

    // Mobile and Desktop sidebar toggle
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            // Mobile toggle
            sidebar.classList.toggle('open');
            // Desktop toggle
            sidebar.classList.toggle('collapsed');
        });
    }
});
