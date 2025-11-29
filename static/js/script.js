// ============================================
// NEPSESEWA - ALL JAVASCRIPT
// ============================================

// Common Utility Functions
class NepseSewaUtils {
    // Show message function
    static showMessage(message, type, containerId = 'message-container') {
        const messageContainer = document.getElementById(containerId);
        if (!messageContainer) return;

        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        messageContainer.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Set button loading state
    static setButtonLoading(button, isLoading) {
        if (isLoading) {
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            button.classList.add('loading');
            button.disabled = true;
        } else {
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
            }
            button.classList.remove('loading');
            button.disabled = false;
        }
    }

    // Format currency
    static formatCurrency(amount) {
        return new Intl.NumberFormat('en-NP', {
            style: 'currency',
            currency: 'NPR'
        }).format(amount);
    }

    // Format percentage
    static formatPercentage(value) {
        return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    }

    // Validate email
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    // Check password strength
    static checkPasswordStrength(password) {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        
        return {
            strength: strength,
            level: strength <= 1 ? 'weak' : 
                   strength === 2 ? 'fair' : 
                   strength === 3 ? 'good' : 'strong'
        };
    }
}

// Landing Page Functionality
class LandingPage {
    static init() {
        this.initNavbarScroll();
        this.initAnimations();
        this.initMarketDataUpdates();
    }

    static initNavbarScroll() {
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (!navbar) return;

            if (window.scrollY > 50) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
            }
        });
    }

    static initAnimations() {
        // Initialize animation states
        document.querySelectorAll('.animate-fade-in').forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        });

        // Animate on scroll
        this.animateOnScroll();
        window.addEventListener('scroll', () => this.animateOnScroll());
    }

    static animateOnScroll() {
        const elements = document.querySelectorAll('.animate-fade-in');
        
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    }

    static initMarketDataUpdates() {
        // Update market data every 15 seconds
        setInterval(() => {
            this.updateMarketData();
        }, 15000);
    }

    static updateMarketData() {
        const statValues = document.querySelectorAll('.market-stat .value');
        if (statValues.length > 0) {
            // Randomly update the first stat (NEPSE Index)
            const currentText = statValues[0].textContent;
            const currentMatch = currentText.match(/(\d+\.\d+)/);
            if (currentMatch) {
                const currentValue = parseFloat(currentMatch[1]);
                const change = (Math.random() - 0.5) * 0.1;
                const newValue = Math.max(0, currentValue + change);
                statValues[0].innerHTML = `${newValue.toFixed(2)} <small>(${NepseSewaUtils.formatPercentage(change)})</small>`;
                statValues[0].className = `value ${change >= 0 ? 'text-success' : 'text-danger'}`;
            }
        }
    }
}

// Login Page Functionality
class LoginPage {
    static init() {
        this.initFormSwitching();
        this.initPasswordStrength();
        this.initFormSubmissions();
        this.initMarketDataUpdates();
    }

    static initFormSwitching() {
        // Form switching functionality
        window.showLoginForm = function() {
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.remove('active');
            });
            document.getElementById('login-form').classList.add('active');
        }

        window.showRegisterForm = function() {
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.remove('active');
            });
            document.getElementById('register-form').classList.add('active');
        }

        window.showForgotPassword = function() {
            document.querySelectorAll('.auth-form').forEach(form => {
                form.classList.remove('active');
            });
            document.getElementById('forgot-password-form').classList.add('active');
        }
    }

    static initPasswordStrength() {
        const passwordInput = document.getElementById('register-password');
        const confirmInput = document.getElementById('register-confirm-password');
        
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                const password = this.value;
                const strengthBar = document.querySelector('.password-strength');
                
                if (!strengthBar) return;
                
                // Reset classes
                strengthBar.className = 'password-strength';
                
                if (password.length === 0) {
                    return;
                }
                
                const strength = NepseSewaUtils.checkPasswordStrength(password);
                strengthBar.classList.add(strength.level);
            });
        }

        if (confirmInput) {
            confirmInput.addEventListener('input', function() {
                const password = document.getElementById('register-password').value;
                const confirmPassword = this.value;
                const matchText = document.getElementById('password-match');
                
                if (!matchText) return;
                
                if (confirmPassword.length === 0) {
                    matchText.textContent = '';
                    return;
                }
                
                if (password === confirmPassword) {
                    matchText.textContent = 'Passwords match!';
                    matchText.className = 'form-text text-success';
                } else {
                    matchText.textContent = 'Passwords do not match';
                    matchText.className = 'form-text text-danger';
                }
            });
        }
    }

    static initFormSubmissions() {
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        const forgotForm = document.getElementById('forgot-password-form');

        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLoginSubmit);
        }

        if (registerForm) {
            registerForm.addEventListener('submit', this.handleRegisterSubmit);
        }

        if (forgotForm) {
            forgotForm.addEventListener('submit', this.handleForgotPasswordSubmit);
        }
    }

    static handleLoginSubmit(e) {
        e.preventDefault();
        const button = e.target.querySelector('button[type="submit"]');
        
        NepseSewaUtils.setButtonLoading(button, true);
        
        // Simulate API call
        setTimeout(() => {
            NepseSewaUtils.setButtonLoading(button, false);
            NepseSewaUtils.showMessage('Login successful! Redirecting...', 'success');
            
            // Redirect after delay
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        }, 2000);
    }

    static handleRegisterSubmit(e) {
        e.preventDefault();
        const button = e.target.querySelector('button[type="submit"]');
        
        NepseSewaUtils.setButtonLoading(button, true);
        
        // Simulate API call
        setTimeout(() => {
            NepseSewaUtils.setButtonLoading(button, false);
            NepseSewaUtils.showMessage('Account created successfully! Please check your email for verification.', 'success');
            
            // Switch to login form after delay
            setTimeout(() => {
                if (window.showLoginForm) {
                    window.showLoginForm();
                }
            }, 3000);
        }, 2000);
    }

    static handleForgotPasswordSubmit(e) {
        e.preventDefault();
        const button = e.target.querySelector('button[type="submit"]');
        
        NepseSewaUtils.setButtonLoading(button, true);
        
        // Simulate API call
        setTimeout(() => {
            NepseSewaUtils.setButtonLoading(button, false);
            NepseSewaUtils.showMessage('Password reset link sent to your email!', 'success');
            
            // Switch to login form after delay
            setTimeout(() => {
                if (window.showLoginForm) {
                    window.showLoginForm();
                }
            }, 3000);
        }, 2000);
    }

    static initMarketDataUpdates() {
        // Update market data every 10 seconds
        setInterval(() => {
            this.updateMarketData();
        }, 10000);
    }

    static updateMarketData() {
        const statValues = document.querySelectorAll('.stat-value');
        if (statValues.length > 0) {
            // Randomly update the first stat (NEPSE Index)
            const currentText = statValues[0].textContent;
            const currentMatch = currentText.match(/[+-]?(\d+\.\d+)%/);
            if (currentMatch) {
                const currentValue = parseFloat(currentMatch[1]);
                const change = (Math.random() - 0.5) * 0.1;
                const newValue = Math.max(0, currentValue + change);
                statValues[0].textContent = NepseSewaUtils.formatPercentage(newValue);
                statValues[0].className = `stat-value ${newValue >= 0 ? 'text-success' : 'text-danger'}`;
            }
        }
    }
}

// Dashboard Page Functionality
class DashboardPage {
    static init() {
        this.initSidebarToggle();
        this.initChartData();
        this.initPortfolioUpdates();
    }

    static initSidebarToggle() {
        const sidebarToggle = document.querySelector('[data-bs-toggle="sidebar"]');
        const sidebar = document.querySelector('.sidebar');
        
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 768 && sidebar && sidebar.classList.contains('show')) {
                if (!sidebar.contains(e.target) && !e.target.closest('[data-bs-toggle="sidebar"]')) {
                    sidebar.classList.remove('show');
                }
            }
        });
    }

    static initChartData() {
        // Simulate chart data loading
        const chartPlaceholders = document.querySelectorAll('.chart-placeholder');
        
        chartPlaceholders.forEach(chart => {
            setTimeout(() => {
                chart.innerHTML = `
                    <div class="text-center">
                        <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                        <h5 class="text-muted">Live Chart Data</h5>
                        <p class="text-muted">Interactive charts would be displayed here</p>
                    </div>
                `;
            }, 1000);
        });
    }

    static initPortfolioUpdates() {
        // Simulate live portfolio updates
        setInterval(() => {
            this.updatePortfolioValues();
        }, 5000);
    }

    static updatePortfolioValues() {
        const portfolioValues = document.querySelectorAll('.portfolio-value');
        const changeElements = document.querySelectorAll('.portfolio-change');
        
        portfolioValues.forEach((element, index) => {
            const currentValue = parseFloat(element.textContent.replace(/[^0-9.]/g, ''));
            const change = (Math.random() - 0.5) * 100;
            const newValue = Math.max(0, currentValue + change);
            
            element.textContent = NepseSewaUtils.formatCurrency(newValue);
            
            if (changeElements[index]) {
                changeElements[index].textContent = NepseSewaUtils.formatPercentage(change / currentValue * 100);
                changeElements[index].className = `portfolio-change ${change >= 0 ? 'text-success' : 'text-danger'}`;
            }
        });
    }
}

// Main Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Determine which page we're on and initialize accordingly
    const body = document.body;
    
    if (body.classList.contains('landing-page')) {
        LandingPage.init();
    } else if (body.classList.contains('login-page')) {
        LoginPage.init();
    } else if (body.classList.contains('dashboard-page')) {
        DashboardPage.init();
    }
    
    // Initialize tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });


});