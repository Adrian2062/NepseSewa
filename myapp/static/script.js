/* ============================================
   NEPSESEWA - COMBINED JAVASCRIPT
   ============================================ */

// ============================================
// PAGE DETECTION & INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Detect which page we're on and initialize accordingly
    if (document.querySelector('.hero-section')) {
        // Landing Page
        initializeLandingPage();
    } else if (document.querySelector('.auth-form')) {
        // Login/Register Page
        initializeAuthPage();
    } else if (document.querySelector('.main-content')) {
        // Home/Dashboard Page
        initializeHomePage();
    }
});

// ============================================
// LANDING PAGE FUNCTIONS
// ============================================

function initializeLandingPage() {
    console.log('Landing page initialized');
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
            }
        }
    });

    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Animate elements on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card, .market-overview-card');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };

    // Set initial state for animated elements
    document.querySelectorAll('.feature-card, .market-overview-card').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });

    // Run animation on scroll
    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll();

    // Start market simulation
    startLandingMarketSimulation();
}

function startLandingMarketSimulation() {
    const marketElements = {
        nepseIndex: document.querySelector('.market-stat-large .stat-value.text-success'),
        turnover: document.querySelectorAll('.market-stat-large .stat-value')[1],
        tradedShares: document.querySelectorAll('.market-stat-large .stat-value')[2],
        indexChange: document.querySelector('.market-stat-large .stat-change.text-success'),
        turnoverChange: document.querySelectorAll('.market-stat-large .stat-change')[1],
        sharesChange: document.querySelectorAll('.market-stat-large .stat-change')[2]
    };

    setInterval(() => {
        updateLandingMarketData(marketElements);
    }, 8000);
}

function updateLandingMarketData(elements) {
    const indexChange = (Math.random() - 0.5) * 0.4;
    const currentIndex = 2191.42 + (indexChange * 10);
    const percentChange = (indexChange / 2191.42) * 100;
    
    const formattedIndex = currentIndex.toFixed(2);
    const formattedPercent = percentChange > 0 ? `+${percentChange.toFixed(2)}%` : `${percentChange.toFixed(2)}%`;
    const formattedTurnover = `Rs ${(3.5 + Math.random() * 0.3).toFixed(1)}B`;
    const formattedShares = `${(4.2 + Math.random() * 0.5).toFixed(1)}M`;
    
    if (elements.nepseIndex) {
        elements.nepseIndex.textContent = formattedIndex;
        elements.indexChange.textContent = formattedPercent;
        elements.indexChange.className = `stat-change ${percentChange >= 0 ? 'text-success' : 'text-danger'}`;
        elements.indexChange.innerHTML = `${formattedPercent} <i class="fas fa-arrow-${percentChange >= 0 ? 'up' : 'down'} ms-1"></i>`;
    }
    
    if (elements.turnover) {
        elements.turnover.textContent = formattedTurnover;
    }
    
    if (elements.tradedShares) {
        elements.tradedShares.textContent = formattedShares;
    }
    
    if (elements.turnoverChange) {
        const turnoverChangeVal = (Math.random() * 5 + 8).toFixed(1);
        elements.turnoverChange.className = 'stat-change text-success';
        elements.turnoverChange.innerHTML = `+${turnoverChangeVal}% <i class="fas fa-arrow-up ms-1"></i>`;
    }
    
    if (elements.sharesChange) {
        const sharesChangeVal = (Math.random() * 4 + 6).toFixed(1);
        elements.sharesChange.className = 'stat-change text-success';
        elements.sharesChange.innerHTML = `+${sharesChangeVal}% <i class="fas fa-arrow-up ms-1"></i>`;
    }
    
    updateLandingStockTicker();
}

function updateLandingStockTicker() {
    const tickerItems = document.querySelectorAll('.ticker-item');
    
    tickerItems.forEach((item, index) => {
        const changeElement = item.querySelector('.stock-price');
        if (changeElement) {
            let change;
            if (index < 3) {
                change = (Math.random() * 3 + 0.5).toFixed(1);
                changeElement.textContent = `+${change}%`;
                changeElement.className = 'stock-price text-success';
            } else {
                change = (Math.random() * 2 + 0.5).toFixed(1);
                changeElement.textContent = `-${change}%`;
                changeElement.className = 'stock-price text-danger';
            }
        }
    });
}

// ============================================
// LOGIN/REGISTER PAGE FUNCTIONS
// ============================================

function initializeAuthPage() {
    console.log('Auth page initialized');
    
    // Show login form by default
    showLoginForm();
    startAuthMarketSimulation();
    
    // Make form toggle functions global for onclick handlers
    window.showLoginForm = showLoginForm;
    window.showRegisterForm = showRegisterForm;
    window.showForgotPassword = showForgotPassword;
}

function showLoginForm() {
    hideAllForms();
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.classList.add('active');
    }
    updateAuthMarketData();
}

function showRegisterForm() {
    hideAllForms();
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.classList.add('active');
    }
}

function showForgotPassword() {
    hideAllForms();
    const forgotForm = document.getElementById('forgot-password-form');
    if (forgotForm) {
        forgotForm.classList.add('active');
    }
}

function hideAllForms() {
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => form.classList.remove('active'));
}

function startAuthMarketSimulation() {
    setInterval(updateAuthMarketData, 5000);
    
    const newsItems = document.querySelectorAll('.news-item');
    let currentNewsIndex = 0;
    
    if (newsItems.length > 0) {
        setInterval(() => {
            newsItems.forEach(item => item.style.display = 'none');
            newsItems[currentNewsIndex].style.display = 'flex';
            currentNewsIndex = (currentNewsIndex + 1) % newsItems.length;
        }, 4000);
    }
}

function updateAuthMarketData() {
    const change = (Math.random() - 0.5) * 0.8;
    const currentPoints = 2191.42 + (change * 10);
    const percentChange = (change / 2191.42) * 100;
    
    const formattedPoints = currentPoints.toFixed(2);
    const formattedPercent = percentChange > 0 ? `+${percentChange.toFixed(2)}%` : `${percentChange.toFixed(2)}%`;
    const formattedTurnover = `Rs ${(3.5 + Math.random() * 0.5).toFixed(1)}B`;
    
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length >= 3) {
        statValues[0].textContent = formattedPercent;
        statValues[0].className = `stat-value ${percentChange >= 0 ? 'text-success' : 'text-danger'}`;
        
        statValues[1].textContent = formattedPoints;
        statValues[1].className = 'stat-value text-white';
        
        statValues[2].textContent = formattedTurnover;
        statValues[2].className = 'stat-value text-success';
    }
    
    updateAuthStockMovers();
}

function updateAuthStockMovers() {
    const gainers = document.querySelectorAll('.gainers .stock-change');
    const losers = document.querySelectorAll('.losers .stock-change');
    
    gainers.forEach((change, index) => {
        let value;
        if (index === 0) value = (Math.random() * 2 + 3.2).toFixed(1);
        else if (index === 1) value = (Math.random() * 1 + 1.0).toFixed(1);
        else value = (Math.random() * 0.5 + 0.5).toFixed(1);
        change.textContent = `+${value}%`;
    });
    
    losers.forEach((change, index) => {
        let value;
        if (index === 0) value = (Math.random() * 1 + 2.3).toFixed(1);
        else if (index === 1) value = (Math.random() * 0.5 + 1.4).toFixed(1);
        else value = (Math.random() * 0.3 + 0.9).toFixed(1);
        change.textContent = `-${value}%`;
    });
}

// ============================================
// HOME/DASHBOARD PAGE FUNCTIONS
// ============================================

function initializeHomePage() {
    console.log('Home page initialized');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    startHomeMarketSimulation();
    simulatePortfolioChart();
    updateWatchlist();
    updateRecentActivity();
    initializeQuickTradeForm();
}

function startHomeMarketSimulation() {
    const marketElements = {
        nepseIndex: document.querySelector('.market-stat h3.text-success'),
        turnover: document.querySelectorAll('.market-stat h3')[1],
        tradedShares: document.querySelectorAll('.market-stat h3')[2],
        indexChange: document.querySelectorAll('.market-stat p span')[0],
        turnoverChange: document.querySelectorAll('.market-stat p span')[1],
        sharesChange: document.querySelectorAll('.market-stat p span')[2]
    };

    setInterval(() => {
        updateHomeMarketData(marketElements);
        updateGainersLosers();
    }, 10000);
}

function updateHomeMarketData(elements) {
    const indexChange = (Math.random() - 0.5) * 0.4;
    const currentIndex = 2191.42 + (indexChange * 10);
    const percentChange = (indexChange / 2191.42) * 100;
    
    const formattedIndex = currentIndex.toFixed(2);
    const formattedPercent = percentChange > 0 ? `+${percentChange.toFixed(2)}%` : `${percentChange.toFixed(2)}%`;
    const formattedTurnover = `Rs ${(3.5 + Math.random() * 0.3).toFixed(1)}B`;
    const formattedShares = `${(4.2 + Math.random() * 0.5).toFixed(1)}M`;
    
    if (elements.nepseIndex) {
        elements.nepseIndex.textContent = formattedIndex;
        if (elements.indexChange) {
            elements.indexChange.textContent = formattedPercent;
            elements.indexChange.className = percentChange >= 0 ? 'text-success' : 'text-danger';
        }
    }
    
    if (elements.turnover) {
        elements.turnover.textContent = formattedTurnover;
    }
    
    if (elements.tradedShares) {
        elements.tradedShares.textContent = formattedShares;
    }
    
    if (elements.turnoverChange) {
        const turnoverChangeVal = (Math.random() * 5 + 8).toFixed(1);
        elements.turnoverChange.textContent = `+${turnoverChangeVal}%`;
        elements.turnoverChange.className = 'text-success';
    }
    
    if (elements.sharesChange) {
        const sharesChangeVal = (Math.random() * 4 + 6).toFixed(1);
        elements.sharesChange.textContent = `+${sharesChangeVal}%`;
        elements.sharesChange.className = 'text-success';
    }
}

function updateGainersLosers() {
    const gainers = document.querySelectorAll('.list-group-item .text-success.fw-bold');
    const losers = document.querySelectorAll('.list-group-item .text-danger.fw-bold');
    
    gainers.forEach((change, index) => {
        if (change.parentElement.classList.contains('list-group-item')) {
            let value;
            if (index === 0) value = (Math.random() * 2 + 3.2).toFixed(1);
            else if (index === 1) value = (Math.random() * 1 + 1.0).toFixed(1);
            else value = (Math.random() * 0.5 + 0.5).toFixed(1);
            change.textContent = `+${value}%`;
        }
    });
    
    losers.forEach((change, index) => {
        if (change.parentElement.classList.contains('list-group-item')) {
            let value;
            if (index === 0) value = (Math.random() * 1 + 2.3).toFixed(1);
            else if (index === 1) value = (Math.random() * 0.5 + 1.4).toFixed(1);
            else value = (Math.random() * 0.3 + 0.9).toFixed(1);
            change.textContent = `-${value}%`;
        }
    });
}

function simulatePortfolioChart() {
    const timeButtons = document.querySelectorAll('.btn-group .btn-outline-success');
    
    timeButtons.forEach(button => {
        button.addEventListener('click', function() {
            timeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            const placeholder = document.querySelector('.chart-placeholder');
            if (placeholder) {
                placeholder.innerHTML = `
                    <div class="spinner-border text-success mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="text-muted">Loading chart data...</p>
                `;
                
                setTimeout(() => {
                    placeholder.innerHTML = `
                        <i class="fas fa-chart-area fa-3x text-muted mb-3"></i>
                        <p class="text-muted">Portfolio performance chart for ${this.textContent} period</p>
                        <div class="performance-stats">
                            <div class="row text-center">
                                <div class="col-4">
                                    <h5 class="text-success">+${(Math.random() * 5 + 1).toFixed(1)}%</h5>
                                    <small>Return</small>
                                </div>
                                <div class="col-4">
                                    <h5>Rs ${(Math.random() * 50000 + 10000).toFixed(0)}</h5>
                                    <small>Profit/Loss</small>
                                </div>
                                <div class="col-4">
                                    <h5 class="text-success">+${(Math.random() * 10 + 5).toFixed(1)}%</h5>
                                    <small>Vs. Market</small>
                                </div>
                            </div>
                        </div>
                    `;
                }, 1000);
            }
        });
    });
}

function updateWatchlist() {
    setInterval(() => {
        const watchlistItems = document.querySelectorAll('.card-body .list-group-item');
        
        watchlistItems.forEach(item => {
            const priceElement = item.querySelector('.text-muted');
            const changeElement = item.querySelector('.fw-bold');
            
            if (priceElement && changeElement && priceElement.textContent.includes('Rs')) {
                const currentPrice = parseFloat(priceElement.textContent.replace('Rs ', ''));
                const changePercent = (Math.random() - 0.5) * 6;
                const newPrice = currentPrice * (1 + changePercent / 100);
                const isPositive = changePercent >= 0;
                
                priceElement.textContent = `Rs ${newPrice.toFixed(2)}`;
                changeElement.textContent = `${isPositive ? '+' : ''}${changePercent.toFixed(1)}%`;
                changeElement.className = `fw-bold ${isPositive ? 'text-success' : 'text-danger'}`;
            }
        });
    }, 15000);
}

function updateRecentActivity() {
    const activities = [
        { action: 'Bought', symbol: 'NBL', shares: 50, price: 240.00 },
        { action: 'Sold', symbol: 'SCB', shares: 30, price: 680.50 },
        { action: 'Bought', symbol: 'NTC', shares: 20, price: 875.00 },
        { action: 'Bought', symbol: 'NICA', shares: 40, price: 420.75 },
        { action: 'Sold', symbol: 'SHL', shares: 25, price: 315.25 }
    ];
    
    setInterval(() => {
        const activityList = document.querySelector('.card:has(h5:contains("Recent Activity")) .list-group');
        if (!activityList) return;
        
        if (activityList.children.length >= 5) {
            activityList.removeChild(activityList.lastElementChild);
        }
        
        const randomActivity = activities[Math.floor(Math.random() * activities.length)];
        const timeAgo = ['2 minutes ago', '5 minutes ago', '10 minutes ago', '15 minutes ago'][Math.floor(Math.random() * 4)];
        
        const newActivity = document.createElement('div');
        newActivity.className = 'list-group-item';
        newActivity.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${randomActivity.action} ${randomActivity.symbol}</h6>
                <small class="${randomActivity.action === 'Bought' ? 'text-success' : 'text-danger'}">
                    ${randomActivity.action === 'Bought' ? '+' : '-'}${randomActivity.shares} shares
                </small>
            </div>
            <p class="mb-1">${randomActivity.shares} shares @ Rs ${randomActivity.price.toFixed(2)}</p>
            <small class="text-muted">${timeAgo}</small>
        `;
        
        activityList.insertBefore(newActivity, activityList.firstChild);
    }, 30000);
}

function initializeQuickTradeForm() {
    const tradeForm = document.querySelector('form');
    if (tradeForm && tradeForm.querySelector('select')) {
        tradeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const symbol = this.querySelector('select').value;
            const tradeType = this.querySelector('input[name="tradeType"]:checked');
            const quantity = this.querySelector('input[type="number"]').value;
            const priceInputs = this.querySelectorAll('input[type="number"]');
            const price = priceInputs.length > 1 ? priceInputs[1].value : '';
            
            if (!symbol || symbol === 'Select Stock' || !quantity || !price) {
                showAlert('Please fill in all fields', 'danger');
                return;
            }
            
            const tradeTypeText = tradeType ? tradeType.nextElementSibling.textContent : 'Buy';
            showAlert(`Trade executed: ${tradeTypeText} ${quantity} shares of ${symbol} @ Rs ${price}`, 'success');
            
            this.reset();
            const buyRadio = this.querySelector('#buy');
            if (buyRadio) buyRadio.checked = true;
        });
    }
}

// ============================================
// UTILITY FUNCTIONS (SHARED)
// ============================================

function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert.position-fixed');
    existingAlerts.forEach(alert => alert.remove());
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = `
        top: 80px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    `;
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Add loading animation
window.addEventListener('load', function() {
    document.body.classList.add('loaded');
});