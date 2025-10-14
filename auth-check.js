/**
 * Authentication Check Middleware for Frontend Pages
 * Checks if user is authenticated and redirects to login if not
 */

const API_BASE_URL = window.location.origin;

// Check authentication and redirect if not logged in
async function requireAuth() {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        // No token, redirect to login
        window.location.href = '/auth.html';
        return null;
    }
    
    try {
        // Verify token with backend
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.success && data.user) {
            // Token is valid, return user data
            return data.user;
        } else {
            // Token invalid, clear and redirect
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            window.location.href = '/auth.html';
            return null;
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        // On error, redirect to login
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/auth.html';
        return null;
    }
}

// Get current user from localStorage (without API call)
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (userStr) {
        try {
            return JSON.parse(userStr);
        } catch (e) {
            return null;
        }
    }
    return null;
}

// Logout function
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    window.location.href = '/index.html';
}

// Make authenticated API request
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        throw new Error('Not authenticated');
    }
    
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    
    const response = await fetch(url, {
        ...options,
        headers
    });
    
    // If unauthorized, redirect to login
    if (response.status === 401) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/auth.html';
        throw new Error('Unauthorized');
    }
    
    return response;
}

// Update navigation to show user info and logout button
function updateNavigation() {
    const user = getCurrentUser();
    
    if (!user) {
        return;
    }
    
    // Find navigation elements
    const navRight = document.querySelector('.navbar-nav.ms-auto');
    
    if (navRight) {
        // Add user info and logout button
        const userNav = document.createElement('li');
        userNav.className = 'nav-item dropdown';
        userNav.innerHTML = `
            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="fas fa-user-circle me-1"></i> ${user.phone_number}
            </a>
            <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="userDropdown">
                <li><a class="dropdown-item" href="/profile.html"><i class="fas fa-user me-2"></i>Profile</a></li>
                <li><a class="dropdown-item" href="/saved-trades.html"><i class="fas fa-bookmark me-2"></i>Saved Trades</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="#" onclick="logout(); return false;"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
            </ul>
        `;
        
        // Remove existing login link if present
        const loginLink = navRight.querySelector('a[href*="auth.html"]');
        if (loginLink && loginLink.parentElement) {
            loginLink.parentElement.remove();
        }
        
        navRight.appendChild(userNav);
    }
}

// Initialize authentication on page load
window.addEventListener('DOMContentLoaded', async () => {
    // Check if this page requires authentication
    const requiresAuth = document.body.dataset.requireAuth === 'true';
    
    if (requiresAuth) {
        const user = await requireAuth();
        if (user) {
            updateNavigation();
        }
    } else {
        // Optional auth - just update nav if logged in
        const token = localStorage.getItem('authToken');
        if (token) {
            updateNavigation();
        }
    }
});

