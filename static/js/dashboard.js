/**
 * NepseSewa Dashboard Specific Logic
 * Handles dynamic rendering of Rank, Profit, Activity, Performance, and Watchlist
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initialized - loading dynamic components...');

    // Initial Load
    refreshDashboardData();

    // Setup 30s Auto Refresh
    setInterval(refreshDashboardData, 30000);
});

/**
 * Main orchestrator for dashboard updates
 */
async function refreshDashboardData() {
    initTicker(); // Keep the ticker updated (from core script.js or shared)

    // Core dynamic components
    loadDashboardSummary();
    loadPortfolioAnalytics();
    loadDashboardPerformance('1D'); // Default 1D
    loadDashboardActivity();
    loadDashboardWatchlist();
}

/**
 * 1. Dashboard Summary: Rank and Total Wealth
 */
async function loadDashboardSummary() {
    try {
        const res = await fetch('/api/dashboard/summary/');
        const json = await res.json();

        if (json.success) {
            const d = json.data;

            // Value
            const valEl = document.getElementById('dashboardPortfolioValue');
            if (valEl) valEl.textContent = `Rs ${fmtNumber(d.total_wealth, 2)}`;

            // Rank
            const rankEl = document.getElementById('dashboardRank');
            const totalEl = document.getElementById('dashboardRankTotal');
            if (rankEl) rankEl.textContent = `#${d.rank}`;
            if (totalEl) totalEl.textContent = `of ${d.total_users} users`;
        }
    } catch (err) {
        console.error("Dashboard Summary error:", err);
    }
}

/**
 * 2. Portfolio Analytics: Today's Profit
 */
async function loadPortfolioAnalytics() {
    try {
        const res = await fetch('/api/portfolio/analytics/');
        const json = await res.json();

        if (json.success) {
            const d = json.data;
            const profitEl = document.getElementById('dashboardTodayProfit');
            const profitPctEl = document.getElementById('dashboardTodayProfitPct');

            if (profitEl) {
                const sign = d.today_pl >= 0 ? '+' : '-';
                const cls = d.today_pl >= 0 ? 'text-success' : 'text-danger';
                profitEl.textContent = `Rs ${fmtNumber(Math.abs(d.today_pl), 2)}`;
                profitEl.className = `stat-value ${cls}`;

                if (profitPctEl) {
                    profitPctEl.textContent = `${sign}${fmtNumber(d.today_pl_pct, 2)}%`;
                    profitPctEl.className = `fw-bold ${cls}`;
                }
            }
        }
    } catch (err) {
        console.error("Portfolio Analytics error:", err);
    }
}

/**
 * 3. Bespoke Pro Choice Chart (Premium NEPSE Index Chart)
 */
let dashboardChart = null;
async function loadDashboardPerformance(range = '1D') {
    const canvas = document.getElementById('portfolioChart');
    if (!canvas) return;

    // Update buttons
    document.querySelectorAll('.btn-group-sm .btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('onclick').includes(`'${range}'`));
    });

    try {
        const res = await fetch(`/api/nepse-index/performance/?range=${range}`);
        const json = await res.json();

        if (json.success) {
            const d = json.data;

            updatePerfLabel('dashboardPerf1d', d.performance['1d']);
            updatePerfLabel('dashboardPerf1w', d.performance['1w']);
            updatePerfLabel('dashboardPerf1m', d.performance['1m']);

            const ctx = canvas.getContext('2d');
            if (dashboardChart) dashboardChart.destroy();

            // Create Premium Gradient (Blue for NEPSE)
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)'); // Pro Blue
            gradient.addColorStop(0.5, 'rgba(59, 130, 246, 0.05)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

            dashboardChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: d.labels.map(l => {
                        try {
                            const date = new Date(l);
                            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
                        } catch { return ''; }
                    }),
                    datasets: [{
                        label: 'NEPSE Index',
                        data: d.values,
                        borderColor: '#3b82f6',
                        borderWidth: 3,
                        backgroundColor: gradient,
                        fill: true,
                        tension: 0.4, // Smooth Spline
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointHoverBackgroundColor: '#3b82f6',
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
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
                                label: (ctx) => `NEPSE Index: ${fmtNumber(ctx.raw, 2)}`,
                                title: (items) => new Date(d.labels[items[0].dataIndex]).toLocaleString()
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
                            border: { display: false },
                            grid: { color: 'rgba(226, 232, 240, 0.5)', drawTicks: false },
                            ticks: {
                                font: { size: 10, weight: '600' },
                                color: '#94a3b8',
                                padding: 10,
                                callback: (v) => fmtNumber(v, 0)
                            }
                        }
                    }
                }
            });
        }
    } catch (err) {
        console.error("NEPSE Chart error:", err);
    }
}

function updatePerfLabel(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    const cls = val >= 0 ? 'text-success' : 'text-danger';
    const sign = val >= 0 ? '+' : '';
    el.textContent = `${sign}${fmtNumber(val, 2)}%`;
    el.className = `fw-bold ${cls}`;
}

/**
 * 4. Recent Activity (Professional View)
 */
async function loadDashboardActivity() {
    const container = document.getElementById('dashboardRecentActivity');
    if (!container) return;

    try {
        const res = await fetch('/api/portfolio/activity/?page=1');
        const json = await res.json();

        if (json.success) {
            const list = json.data;
            if (list.length === 0) {
                container.innerHTML = '<div class="text-muted p-2">No recent activity yet.</div>';
                return;
            }

            let html = '<div class="activity-feed">';
            list.slice(0, 3).forEach(act => { // Top 3 explicitly
                const isBuy = act.side === 'BUY';
                const cls = isBuy ? 'success' : 'danger';
                const sign = isBuy ? '+' : '-';

                html += `
                <div class="d-flex align-items-center mb-3">
                    <div class="rounded-circle bg-${cls}-subtle p-2 me-3" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                        <i class="fas ${isBuy ? 'fa-cart-plus' : 'fa-hand-holding-dollar'} text-${cls}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="fw-bold" style="font-size: .9rem;">${isBuy ? 'Bought' : 'Sold'} ${act.symbol}</div>
                        <div class="text-muted small">${act.quantity} shares @ Rs ${fmtNumber(act.price)}</div>
                    </div>
                    <div class="text-end">
                        <div class="text-muted" style="font-size: .75rem; font-weight: 700;">${act.formatted_date}</div>
                        <div class="text-muted small" style="font-size: .65rem;">${act.formatted_time}</div>
                    </div>
                </div>
                `;
            });
            html += '</div>';

            // Add a link to the full activity
            html += '<div class="mt-2 pt-2 border-top text-center"><a href="/portfolio/" class="text-primary small fw-bold text-decoration-none">View All Activity <i class="fas fa-arrow-right ms-1"></i></a></div>';

            container.innerHTML = html;
        }
    } catch (err) {
        console.error("Activity error:", err);
    }
}

/**
 * 5. Watchlist
 */
async function loadDashboardWatchlist() {
    const tbody = document.getElementById('dashboardWatchlistTbody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/watchlist/');
        const json = await res.json();

        if (json.success) {
            const list = json.data;
            if (!list || list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center p-4 text-muted">Your watchlist is empty.</td></tr>';
                return;
            }

            let html = '';
            list.forEach(item => {
                const cls = item.change >= 0 ? 'text-success' : 'text-danger';
                const sign = item.change >= 0 ? '+' : '';

                html += `
                <tr>
                    <td class="ps-3 fw-bold">${item.symbol}</td>
                    <td class="text-muted">${item.name}</td>
                    <td class="fw-bold">${fmtNumber(item.price)}</td>
                    <td class="${cls} fw-bold">${sign}${fmtNumber(item.change)}%</td>
                    <td class="text-end pe-3">
                        <a href="/trade/?symbol=${item.symbol}" class="btn btn-sm btn-outline-success">Trade</a>
                    </td>
                </tr>
                `;
            });

            tbody.innerHTML = html;
        }
    } catch (err) {
        console.error("Watchlist load error:", err);
    }
}

/**
 * Shared Ticker Logic (if required to be in dashboard.js)
 */
async function initTicker() {
    const tickerContent = document.getElementById('tickerContent');
    const tickerAsOf = document.getElementById('tickerAsOf');
    const activeStocksEl = document.getElementById('activeStocks');

    if (!tickerContent) return;

    try {
        const res = await fetch('/api/latest/');
        const json = await res.json();

        if (json.success && json.data) {
            const ts = new Date(json.timestamp);
            if (tickerAsOf) tickerAsOf.innerText = "As of " + ts.toLocaleTimeString();

            let html = '';
            json.data.forEach(item => {
                const color = item.change_pct >= 0 ? '#10b981' : '#ef4444';
                const icon = item.change_pct >= 0 ? 'fa-caret-up' : 'fa-caret-down';
                html += `
                <div class="ticker-item">
                    <span style="color:#111827;">${item.symbol}</span>
                    <span style="color:${color};">${fmtNumber(item.ltp)}</span>
                    <i class="fas ${icon}" style="color:${color};"></i>
                    <span style="color:${color};">${item.change_pct.toFixed(2)}%</span>
                </div>
                `;
            });
            tickerContent.innerHTML = html + html;
            if (activeStocksEl) activeStocksEl.innerText = json.data.length;
        }
    } catch (err) { }
}

/**
 * Global Init
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial Data Load
    loadDashboardSummary();
    loadDashboardPerformance('1D');
    loadDashboardActivity();
    loadDashboardWatchlist();
    initTicker();

    // 2. Refresh Loop (Every 60s for live feel)
    setInterval(() => {
        loadDashboardSummary();
        initTicker();
    }, 60000);
});
