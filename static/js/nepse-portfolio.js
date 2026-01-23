/**
 * NepseSewa Portfolio Analytics Dashboard
 * Handles dynamic portfolio data, charts, and real-time updates
 */

// Global variables
let portfolioValueChart = null;
let allocationChart = null;
let currentRange = '1D';

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
        loadRecentActivity();
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
 * Load recent activity feed
 */
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/portfolio/activity/');
        const result = await response.json();

        if (result.success) {
            const activities = result.data;
            const container = document.getElementById('recentActivity');

            if (activities.length === 0) {
                container.innerHTML = `
                    <div class="text-muted" style="font-weight:700;">
                        No recent activity. <a href="/trade/" class="text-primary">Place your first trade</a>.
                    </div>
                `;
                return;
            }

            // Build activity list
            let html = '<div class="list-group list-group-flush">';
            activities.forEach(activity => {
                const sideClass = activity.side === 'BUY' ? 'text-success' : 'text-danger';
                const sideIcon = activity.side === 'BUY' ? 'fa-arrow-up' : 'fa-arrow-down';

                html += `
                    <div class="list-group-item px-0 py-2 border-0">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <span class="${sideClass}" style="font-weight:900;">
                                    <i class="fas ${sideIcon} me-1"></i>${activity.side}
                                </span>
                                <strong>${activity.quantity}</strong> ${activity.symbol}
                                @ Rs ${formatNumber(activity.price)}
                            </div>
                            <small class="text-muted">${activity.time_ago}</small>
                        </div>
                    </div>
                `;
            });
            html += '</div>';

            container.innerHTML = html;
        } else {
            console.error('Failed to load activity:', result.error);
        }
    } catch (error) {
        console.error('Error loading activity:', error);
    }
}

/**
 * Update portfolio value chart
 */
function updatePortfolioValueChart(labels, values) {
    const ctx = document.getElementById('portfolioValueChart');

    if (!ctx) {
        console.error('Portfolio value chart canvas not found');
        return;
    }

    // Destroy existing chart if it exists
    if (portfolioValueChart) {
        portfolioValueChart.destroy();
    }

    // Create gradient
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');

    portfolioValueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value',
                data: values,
                borderColor: 'rgb(16, 185, 129)',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: 'rgb(16, 185, 129)',
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
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
                            return 'Rs ' + formatNumber(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxTicksLimit: 8,
                        font: {
                            size: 11
                        }
                    }
                },
                y: {
                    display: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function (value) {
                            return 'Rs ' + formatNumber(value, 0);
                        },
                        font: {
                            size: 11
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
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
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-success');
                });
                buttons[range].classList.remove('btn-outline-success');
                buttons[range].classList.add('btn-success');

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
