// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.navbar')) {
                navLinks.classList.remove('active');
            }
        });
    }
});

// Flash Message Close
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    
    flashMessages.forEach(function(flash) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            flash.style.animation = 'slideOut 0.3s ease';
            setTimeout(function() {
                flash.remove();
            }, 300);
        }, 5000);

        // Manual close button
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                flash.style.animation = 'slideOut 0.3s ease';
                setTimeout(function() {
                    flash.remove();
                }, 300);
            });
        }
    });
});

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// API Request Helper
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Show Flash Message
function showFlash(message, type = 'success') {
    const flashContainer = document.querySelector('.flash-messages') || createFlashContainer();
    
    const flash = document.createElement('div');
    flash.className = `flash flash-${type}`;
    flash.innerHTML = `
        <span>${message}</span>
        <button class="flash-close">&times;</button>
    `;
    
    flashContainer.appendChild(flash);
    
    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        flash.style.animation = 'slideOut 0.3s ease';
        setTimeout(function() {
            flash.remove();
        }, 300);
    }, 5000);
    
    // Close button
    flash.querySelector('.flash-close').addEventListener('click', function() {
        flash.style.animation = 'slideOut 0.3s ease';
        setTimeout(function() {
            flash.remove();
        }, 300);
    });
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-messages';
    document.body.appendChild(container);
    return container;
}

// Form Validation Helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    return password.length >= 8 && 
           /[A-Z]/.test(password) && 
           /[a-z]/.test(password) && 
           /[0-9]/.test(password);
}

function showFieldError(input, message) {
    const formGroup = input.closest('.form-group');
    let errorDiv = formGroup.querySelector('.field-error');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.style.color = '#dc3545';
        errorDiv.style.fontSize = '13px';
        errorDiv.style.marginTop = '4px';
        formGroup.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
    input.style.borderColor = '#dc3545';
}

function clearFieldError(input) {
    const formGroup = input.closest('.form-group');
    const errorDiv = formGroup.querySelector('.field-error');
    
    if (errorDiv) {
        errorDiv.remove();
    }
    
    input.style.borderColor = '';
}

// Date Formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
}

function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

function formatDateTime(dateString, timeString) {
    return `${formatDate(dateString)} at ${formatTime(timeString)}`;
}

// Loading Indicator
function showLoading(element, text = 'Loading...') {
    element.innerHTML = `
        <div class="loading">
            <p>${text}</p>
        </div>
    `;
}

function showError(element, message) {
    element.innerHTML = `
        <div class="error">
            <p>${message}</p>
        </div>
    `;
}

// Debounce Function for Search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for use in other scripts
window.MuleSpace = {
    apiRequest,
    showFlash,
    validateEmail,
    validatePassword,
    showFieldError,
    clearFieldError,
    formatDate,
    formatTime,
    formatDateTime,
    showLoading,
    showError,
    debounce
};
