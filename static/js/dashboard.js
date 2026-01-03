// Dashboard Specific Logic

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    initTicker();
    setInterval(initTicker, 30000); // Update ticker & stats every 30s
});


// 1. Chart.js
function initChart() {
    const ctx = document.getElementById('portfolioChart');
    if (!ctx) return;

    // Gradient fill
    let gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], // Dummy week
            datasets: [{
                label: 'Portfolio Value',
                data: [100000, 102500, 101200, 104800, 103900, 106000, 106000], // Dummy data
                borderColor: '#10b981', // var(--primary)
                backgroundColor: gradient,
                borderWidth: 2,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#10b981',
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#6b7280' }
                },
                y: {
                    border: { display: false },
                    grid: { color: '#e5e7eb', borderDash: [5, 5] },
                    ticks: { color: '#6b7280' }
                }
            }
        }
    });
}


// 2. Ticker & Dashboard Stats (Active Stocks, etc)
async function initTicker() {
    const tickerContent = document.getElementById('tickerContent');
    const tickerAsOf = document.getElementById('tickerAsOf');
    const tickerLabel = document.getElementById('tickerLabel');
    const activeStocksEl = document.getElementById('activeStocks');

    if (!tickerContent) return;

    try {
        const res = await fetch('/api/latest/');
        const json = await res.json();

        if (json.data && json.data.length > 0) {
            // Update Timestamp
            const ts = new Date(json.timestamp);
            if (tickerAsOf) tickerAsOf.innerText = "As of " + ts.toLocaleTimeString();

            // Build ticker HTML
            let html = '';
            json.data.forEach(item => {
                // Ensure proper number formatting
                const ltp = Number(item.ltp);
                const chg = Number(item.change_pct);
                const color = chg >= 0 ? '#10b981' : '#ef4444';
                const icon = chg >= 0 ? 'fa-caret-up' : 'fa-caret-down';
                const sign = chg >= 0 ? '+' : '';

                html += `
                <div class="ticker-item">
                    <span style="color:#111827;">${item.symbol}</span>
                    <span style="color:${color};">${fmtNumber(ltp, 2)}</span>
                    <i class="fas ${icon}" style="color:${color};font-size:0.75rem;"></i>
                    <span style="color:${color};font-size:0.8rem;">${sign}${fmtNumber(chg, 2)}%</span>
                </div>
                `;
            });

            // Duplicate for smooth loop if short, or just set it
            tickerContent.innerHTML = html + html;

            // Active stocks count
            if (activeStocksEl) activeStocksEl.innerText = json.count || json.data.length;

            // Simple status check strictly for the ticker badge
            const now = new Date();
            const diffMins = (now - ts) / 1000 / 60;
            if (diffMins < 15 && tickerLabel) {
                tickerLabel.classList.add('bg-danger'); // Blink/Red for Live
                tickerLabel.innerHTML = '<i class="fas fa-circle"></i>Live';
            } else if (tickerLabel) {
                tickerLabel.classList.remove('bg-danger');
                tickerLabel.style.backgroundColor = '#6b7280';
                tickerLabel.innerHTML = '<i class="fas fa-circle"></i>Ended';
            }
        }
    } catch (err) {
        console.error("Dashboard Ticker error:", err);
    }
}
