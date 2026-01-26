/**
 * NepseSewa Portfolio Analytics Dashboard
 * Handles dynamic portfolio data, charts, and real-time updates
 */

// Global variables
let portfolioValueChart = null;
let allocationChart = null;
let currentRange = '1D';
let currentActivityPage = 1;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('Portfolio page loaded - initializing...');

    // Load all portfolio data
    loadPortfolioAnalytics();
    loadPortfolioHoldings();
    loadPortfolioPerformance('1D');
    loadRecentActivity();

    // Setup event listeners for time range buttons
    setupTimeRangeButtons();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadPortfolioAnalytics();
        loadPortfolioHoldings();
        loadPortfolioPerformance(currentRange);
        loadRecentActivity(currentActivityPage);
    }, 30000);
});

/**
 * Load portfolio analytics summary (cards at top)
 */
async function loadPortfolioAnalytics() {
    try {
        const response = await fetch('/api/portfolio/analytics/');
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // Update summary cards
            document.getElementById('sumTotalValue').textContent = `Rs ${formatNumber(data.total_value)}`;
            document.getElementById('sumHoldings').textContent = data.holdings_count;

            // Today's P/L
            const todayPL = data.today_pl;
            const todayPLPct = data.today_pl_pct;
            document.getElementById('sumTodayPL').textContent = formatPL(todayPL);
            document.getElementById('sumTodayPLPct').textContent = formatPLPercent(todayPLPct);
            document.getElementById('sumTodayPLPct').className = getPLClass(todayPL);

            // Overall P/L
            const overallPL = data.overall_pl;
            const overallPLPct = data.overall_pl_pct;
            document.getElementById('sumOverallPL').textContent = formatPL(overallPL);
            document.getElementById('sumOverallPLPct').textContent = formatPLPercent(overallPLPct);
            document.getElementById('sumOverallPLPct').className = getPLClass(overallPL);

            // Update timestamp
            const timestamp = new Date(data.timestamp);
            document.getElementById('portfolioAsOf').textContent = `As of ${formatTimestamp(timestamp)}`;
        } else {
            console.error('Failed to load portfolio analytics:', result.error);
        }
    } catch (error) {
        console.error('Error loading portfolio analytics:', error);
    }
}

/**
 * Load portfolio holdings table
 */
async function loadPortfolioHoldings() {
    try {
        const response = await fetch('/api/portfolio/holdings/');
        const result = await response.json();

        if (result.success) {
            const holdings = result.data;
            const tbody = document.getElementById('holdingsTbody');

            if (holdings.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted p-4">
                            No holdings yet. <a href="/trade/" class="text-primary">Start trading</a> to build your portfolio.
                        </td>
                    </tr>
                `;

                // Also update allocation chart for empty state
                updateAllocationChart([]);
                return;
            }

            // Build table rows
            let html = '';
            holdings.forEach(holding => {
                const plClass = holding.pl >= 0 ? 'text-success' : 'text-danger';
                const plSign = holding.pl >= 0 ? '+' : '';

                html += `
                    <tr>
                        <td class="ps-3">
                            <span class="symbol-pill badge bg-primary">${holding.symbol}</span>
                        </td>
                        <td>${formatNumber(holding.quantity, 0)}</td>
                        <td>Rs ${formatNumber(holding.avg_price)}</td>
                        <td>Rs ${formatNumber(holding.current_ltp)}</td>
                        <td>Rs ${formatNumber(holding.market_value)}</td>
                        <td class="text-end pe-3 ${plClass}" style="font-weight:900;">
                            ${plSign}Rs ${formatNumber(Math.abs(holding.pl))}
                            <br>
                            <small>(${plSign}${holding.pl_pct.toFixed(2)}%)</small>
                        </td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;

            // Update allocation chart
            updateAllocationChart(holdings);
        } else {
            console.error('Failed to load holdings:', result.error);
        }
    } catch (error) {
        console.error('Error loading holdings:', error);
    }
}

/**
 * Load portfolio performance chart
 */
async function loadPortfolioPerformance(range = '1D') {
    try {
        const response = await fetch(`/api/portfolio/performance/?range=${range}`);
        const result = await response.json();

        if (result.success) {
            const data = result.data;

            // Update performance metrics
            document.getElementById('perf1d').textContent = formatPLPercent(data.performance['1d']);
            document.getElementById('perf1d').className = `fw-bold ${getPLClass(data.performance['1d'])}`;

            document.getElementById('perf1w').textContent = formatPLPercent(data.performance['1w']);
            document.getElementById('perf1w').className = `fw-bold ${getPLClass(data.performance['1w'])}`;

            document.getElementById('perf1m').textContent = formatPLPercent(data.performance['1m']);
            document.getElementById('perf1m').className = `fw-bold ${getPLClass(data.performance['1m'])}`;

            // Update chart
            updatePortfolioValueChart(data.labels, data.values);
        } else {
            console.error('Failed to load performance:', result.error);
        }
    } catch (error) {
        console.error('Error loading performance:', error);
    }
}

/**
 * Load recent activity feed with pagination
 */
async function loadRecentActivity(page = 1) {
    try {
        console.log(`Loading activity page ${page}...`);
        currentActivityPage = page;
        const response = await fetch(`/api/portfolio/activity/?page=${page}`);
        const result = await response.json();

        if (result.success) {
            const activities = result.data;
            const pagination = result.pagination;
            const container = document.getElementById('recentActivity');

            if (!container) return;

            if (activities.length === 0 && page === 1) {
                container.innerHTML = `
                    <div class="text-muted" style="font-weight:700;">
                        No recent activity. <a href="/trade/" class="text-primary">Place your first trade</a>.
                    </div>
                `;
                return;
            }

            // Build activity list
            let html = '<div class="activity-list">';
            activities.forEach(activity => {
                const isBuy = activity.side === 'BUY';
                const iconClass = isBuy ? 'buy' : 'sell';
                const icon = isBuy ? 'fa-cart-shopping' : 'fa-hand-holding-dollar';
                const sideText = isBuy ? 'Bought' : 'Sold';

                html += `
                    <div class="activity-item">
                        <div class="activity-icon ${iconClass}">
                            <i class="fas ${icon}"></i>
                        </div>
                        <div class="activity-details">
                            <div class="activity-title">${sideText} ${activity.symbol}</div>
                            <div class="activity-meta">
                                <strong>${activity.quantity} shares</strong> @ Rs ${formatNumber(activity.price)}
                            </div>
                        </div>
                        <div class="activity-time">
                            <div style="color: #4a5568; font-weight: 800;">${activity.formatted_date}</div>
                            <div style="font-size: 0.7rem; color: #a0aec0;">${activity.formatted_time}</div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';

            // Add pagination controls
            if (pagination && pagination.total_items > 0) {
                html += `
                    <div class="d-flex justify-content-between align-items-center mt-4">
                        <button class="btn btn-pg shadow-sm ${!pagination.has_prev ? 'disabled' : ''}" 
                                onclick="window.loadRecentActivity(${page - 1})" ${!pagination.has_prev ? 'disabled' : ''}>
                            <i class="fas fa-arrow-left"></i>
                        </button>
                        
                        <div class="text-center">
                            <span class="pg-indicator">Page ${pagination.current_page} of ${pagination.total_pages}</span>
                            <div class="text-muted mt-2" style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
                                ${pagination.total_items} transactions
                            </div>
                        </div>
                        
                        <button class="btn btn-pg shadow-sm ${!pagination.has_next ? 'disabled' : ''}" 
                                onclick="window.loadRecentActivity(${page + 1})" ${!pagination.has_next ? 'disabled' : ''}>
                            <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>
                `;
            }

            container.innerHTML = html;
        } else {
            console.error('Failed to load activity:', result.error);
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

// Ensure globally accessible for inline onclick
window.loadRecentActivity = loadRecentActivity;

/**
 * Update portfolio value chart
 */
function updatePortfolioValueChart(labels, values) {
    const ctx = document.getElementById('portfolioValueChart');
    if (!ctx) return;

    if (portfolioValueChart) {
        portfolioValueChart.destroy();
    }

    // Create Premium Pro Gradient
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)'); // Blue
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

    portfolioValueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.map(l => {
                try {
                    const d = new Date(l);
                    // Format based on granularity
                    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                } catch { return ''; }
            }),
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: '#3b82f6',
                borderWidth: 3,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4, // Smooth splines
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#3b82f6',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    padding: 12,
                    titleFont: { size: 13, weight: 'bold' },
                    bodyFont: { size: 12 },
                    cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        label: (ctx) => `Value: Rs ${formatNumber(ctx.raw, 0)}`,
                        title: (items) => new Date(labels[items[0].dataIndex]).toLocaleString()
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: { display: false },
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 7,
                        font: { size: 10, weight: '600' },
                        color: '#94a3b8'
                    }
                },
                y: {
                    display: true,
                    grid: { color: 'rgba(0, 0, 0, 0.03)', drawTicks: false },
                    border: { display: false },
                    ticks: {
                        callback: (v) => 'Rs ' + formatNumber(v, 0),
                        font: { size: 10, weight: '600' },
                        color: '#94a3b8',
                        padding: 10
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

/**
 * Update allocation pie chart
 */
function updateAllocationChart(holdings) {
    const ctx = document.getElementById('allocationChart');

    if (!ctx) {
        console.error('Allocation chart canvas not found');
        return;
    }

    // Destroy existing chart if it exists
    if (allocationChart) {
        allocationChart.destroy();
    }

    if (holdings.length === 0) {
        // Show empty state
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    // Take top 8 holdings
    const top8 = holdings.slice(0, 8);
    const others = holdings.slice(8);

    // Calculate total value
    const totalValue = holdings.reduce((sum, h) => sum + h.market_value, 0);

    // Prepare data
    const labels = top8.map(h => h.symbol);
    const data = top8.map(h => (h.market_value / totalValue * 100).toFixed(2));

    // Add "Others" if there are more than 8 holdings
    if (others.length > 0) {
        const othersValue = others.reduce((sum, h) => sum + h.market_value, 0);
        labels.push('Others');
        data.push((othersValue / totalValue * 100).toFixed(2));
    }

    // Color palette
    const colors = [
        'rgb(16, 185, 129)',   // Primary green
        'rgb(59, 130, 246)',   // Blue
        'rgb(245, 158, 11)',   // Orange
        'rgb(239, 68, 68)',    // Red
        'rgb(168, 85, 247)',   // Purple
        'rgb(236, 72, 153)',   // Pink
        'rgb(14, 165, 233)',   // Sky
        'rgb(34, 197, 94)',    // Green
        'rgb(156, 163, 175)'   // Gray for Others
    ];

    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12,
                            weight: '700'
                        },
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 13
                    },
                    callbacks: {
                        label: function (context) {
                            return context.label + ': ' + context.parsed + '%';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Setup time range button event listeners
 */
function setupTimeRangeButtons() {
    const buttons = {
        '1D': document.getElementById('btnRange1D'),
        '1W': document.getElementById('btnRange1W'),
        '1M': document.getElementById('btnRange1M')
    };

    Object.keys(buttons).forEach(range => {
        if (buttons[range]) {
            buttons[range].addEventListener('click', () => {
                currentRange = range;

                // Update button states
                Object.values(buttons).forEach(btn => {
                    btn.classList.remove('btn-primary');
                    btn.classList.add('btn-outline-primary');
                });
                buttons[range].classList.remove('btn-outline-primary');
                buttons[range].classList.add('btn-primary');

                // Load new data
                loadPortfolioPerformance(range);
            });
        }
    });

    // Set initial active button
    if (buttons['1D']) {
        buttons['1D'].classList.remove('btn-outline-success');
        buttons['1D'].classList.add('btn-success');
    }
}

/**
 * Utility: Format number with commas
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined) return '0.00';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Utility: Format P/L value
 */
function formatPL(value) {
    if (value === null || value === undefined) return 'Rs 0.00';
    const sign = value >= 0 ? '+' : '';
    return `${sign}Rs ${formatNumber(Math.abs(value))}`;
}

/**
 * Utility: Format P/L percentage
 */
function formatPLPercent(value) {
    if (value === null || value === undefined) return '0.00%';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
}

/**
 * Utility: Get CSS class for P/L value
 */
function getPLClass(value) {
    if (value > 0) return 'text-success fw-bold';
    if (value < 0) return 'text-danger fw-bold';
    return 'text-muted fw-bold';
}

/**
 * Utility: Format timestamp
 */
function formatTimestamp(date) {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} min ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;

    // Format as date and time
    const options = {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return date.toLocaleDateString('en-US', options);
}

console.log('Portfolio analytics module loaded');
