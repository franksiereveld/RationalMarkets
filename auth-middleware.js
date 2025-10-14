/**
 * Authentication Middleware for RationalMarkets
 * Protects pages and handles authenticated API requests
 */

// API base URL
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000'
    : 'https://your-backend-url.railway.app';  // Update with your Railway URL

/**
 * Check if user is authenticated
 * Redirects to login page if not authenticated
 */
function requireAuth() {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        // Save current page to return after login
        const returnUrl = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `auth.html?return=${returnUrl}`;
        return false;
    }
    
    return true;
}

/**
 * Get current user info from localStorage
 */
function getCurrentUser() {
    const userJson = localStorage.getItem('user');
    if (userJson) {
        try {
            return JSON.parse(userJson);
        } catch (e) {
            return null;
        }
    }
    return null;
}

/**
 * Get phone number of current user
 */
function getCurrentPhoneNumber() {
    return localStorage.getItem('phoneNumber');
}

/**
 * Check if user is logged in (without redirecting)
 */
function isAuthenticated() {
    return !!localStorage.getItem('authToken');
}

/**
 * Logout user
 */
async function logout() {
    const token = localStorage.getItem('authToken');
    
    if (token) {
        try {
            await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (e) {
            console.error('Logout error:', e);
        }
    }
    
    // Clear local storage
    localStorage.removeItem('authToken');
    localStorage.removeItem('phoneNumber');
    localStorage.removeItem('user');
    
    // Redirect to home
    window.location.href = 'index.html';
}

/**
 * Make authenticated API request
 */
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        window.location.href = 'auth.html';
        throw new Error('Not authenticated');
    }
    
    // Add auth header
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
    
    const response = await fetch(url, options);
    
    // Handle 401 Unauthorized
    if (response.status === 401) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('phoneNumber');
        localStorage.removeItem('user');
        window.location.href = 'auth.html';
        throw new Error('Session expired');
    }
    
    return response;
}

/**
 * Save trade to database
 */
async function saveTrade(tradeData) {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/trades/`, {
            method: 'POST',
            body: JSON.stringify(tradeData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save trade');
        }
        
        const data = await response.json();
        return data.trade;
    } catch (error) {
        console.error('Error saving trade:', error);
        throw error;
    }
}

/**
 * Get all trades for current user
 */
async function getTrades(limit = 50, offset = 0) {
    try {
        const response = await authenticatedFetch(
            `${API_BASE_URL}/api/trades/?limit=${limit}&offset=${offset}`
        );
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch trades');
        }
        
        const data = await response.json();
        return data.trades;
    } catch (error) {
        console.error('Error fetching trades:', error);
        throw error;
    }
}

/**
 * Get a specific trade
 */
async function getTrade(tradeId) {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/trades/${tradeId}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch trade');
        }
        
        const data = await response.json();
        return data.trade;
    } catch (error) {
        console.error('Error fetching trade:', error);
        throw error;
    }
}

/**
 * Delete a trade
 */
async function deleteTrade(tradeId) {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/trades/${tradeId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete trade');
        }
        
        return true;
    } catch (error) {
        console.error('Error deleting trade:', error);
        throw error;
    }
}

/**
 * Get trade statistics
 */
async function getTradeStats() {
    try {
        const response = await authenticatedFetch(`${API_BASE_URL}/api/trades/stats`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to fetch stats');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error fetching stats:', error);
        throw error;
    }
}

/**
 * Update user display on page
 */
function updateUserDisplay() {
    const user = getCurrentUser();
    const phoneNumber = getCurrentPhoneNumber();
    
    // Update any user info displays
    const userDisplays = document.querySelectorAll('.user-phone');
    userDisplays.forEach(el => {
        el.textContent = phoneNumber || 'Not logged in';
    });
    
    // Show/hide auth buttons
    const loginButtons = document.querySelectorAll('.login-btn');
    const logoutButtons = document.querySelectorAll('.logout-btn');
    
    if (isAuthenticated()) {
        loginButtons.forEach(btn => btn.style.display = 'none');
        logoutButtons.forEach(btn => btn.style.display = 'inline-block');
    } else {
        loginButtons.forEach(btn => btn.style.display = 'inline-block');
        logoutButtons.forEach(btn => btn.style.display = 'none');
    }
}

// Auto-update user display on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateUserDisplay);
} else {
    updateUserDisplay();
}

