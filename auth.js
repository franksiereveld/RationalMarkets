/**
 * Authentication JavaScript for RationalMarkets
 * Handles phone verification and JWT token management
 */

// API base URL - change for production
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000'
    : 'https://your-backend-url.railway.app';  // Update with your Railway URL

let currentPhoneNumber = '';

/**
 * Send verification code to phone number
 */
async function sendVerificationCode() {
    const phoneNumber = document.getElementById('phoneNumber').value.trim();
    const sendBtn = document.getElementById('sendCodeBtn');
    
    if (!phoneNumber) {
        showMessage('Please enter a phone number', 'error');
        return;
    }
    
    // Validate E.164 format
    if (!phoneNumber.startsWith('+')) {
        showMessage('Phone number must start with + and country code (e.g., +1 for US)', 'error');
        return;
    }
    
    // Disable button and show loading
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading"></span>Sending...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/send-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phoneNumber })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentPhoneNumber = phoneNumber;
            document.getElementById('phoneDisplay').textContent = phoneNumber;
            document.getElementById('phoneStep').style.display = 'none';
            document.getElementById('codeStep').style.display = 'block';
            
            // Show dev mode message if applicable
            if (data.dev_mode) {
                showMessage(data.message, 'info');
            } else {
                showMessage('Verification code sent successfully!', 'success');
            }
            
            // Focus on code input
            setTimeout(() => {
                document.getElementById('verificationCode').focus();
            }, 100);
        } else {
            showMessage(data.error || data.message || 'Failed to send verification code', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Network error. Please check your connection and try again.', 'error');
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = 'Send Code';
    }
}

/**
 * Verify the OTP code
 */
async function verifyCode() {
    const code = document.getElementById('verificationCode').value.trim();
    const verifyBtn = document.getElementById('verifyBtn');
    
    if (!code || code.length !== 6) {
        showMessage('Please enter a 6-digit code', 'error');
        return;
    }
    
    // Disable button and show loading
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<span class="loading"></span>Verifying...';
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/verify-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                phoneNumber: currentPhoneNumber,
                code 
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.verified) {
            // Store JWT token and user info
            localStorage.setItem('authToken', data.access_token);
            localStorage.setItem('phoneNumber', data.phone_number);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            showMessage('Login successful! Redirecting...', 'success');
            
            // Redirect to main app after short delay
            setTimeout(() => {
                const returnUrl = new URLSearchParams(window.location.search).get('return') || 'index.html';
                window.location.href = returnUrl;
            }, 1000);
        } else {
            showMessage(data.message || 'Invalid verification code', 'error');
            document.getElementById('verificationCode').value = '';
            document.getElementById('verificationCode').focus();
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage('Network error. Please try again.', 'error');
    } finally {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = 'Verify Code';
    }
}

/**
 * Resend verification code
 */
function resendCode() {
    document.getElementById('phoneNumber').value = currentPhoneNumber;
    sendVerificationCode();
}

/**
 * Change phone number
 */
function changeNumber() {
    document.getElementById('phoneStep').style.display = 'block';
    document.getElementById('codeStep').style.display = 'none';
    document.getElementById('verificationCode').value = '';
    hideMessage();
}

/**
 * Show message to user
 */
function showMessage(message, type = 'info') {
    const messageBox = document.getElementById('messageBox');
    messageBox.className = type;
    messageBox.textContent = message;
    messageBox.style.display = 'block';
}

/**
 * Hide message
 */
function hideMessage() {
    const messageBox = document.getElementById('messageBox');
    messageBox.style.display = 'none';
}

/**
 * Handle Enter key press
 */
document.addEventListener('DOMContentLoaded', () => {
    // Phone number input
    document.getElementById('phoneNumber').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendVerificationCode();
        }
    });
    
    // Verification code input
    document.getElementById('verificationCode').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            verifyCode();
        }
    });
    
    // Auto-submit when 6 digits entered
    document.getElementById('verificationCode').addEventListener('input', (e) => {
        const code = e.target.value;
        if (code.length === 6 && /^\d{6}$/.test(code)) {
            verifyCode();
        }
    });
    
    // Check if already logged in
    const token = localStorage.getItem('authToken');
    if (token) {
        // Verify token is still valid
        fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                // Already logged in, redirect
                const returnUrl = new URLSearchParams(window.location.search).get('return') || 'index.html';
                window.location.href = returnUrl;
            }
        })
        .catch(() => {
            // Token invalid, clear it
            localStorage.removeItem('authToken');
            localStorage.removeItem('phoneNumber');
            localStorage.removeItem('user');
        });
    }
});

