// File: static/js/nepse-dashboard.js

class NepseDashboard {
    constructor() {
        this.apiBase = '/api';
        this.updateInterval = 5000; // 5 seconds
        this.portfolioChart = null;
        this.init();
    }

    init() {
        // chart
        this.initPortfolioChart();

        // data
        this.loadMarketStats();
        this.loadTopGainers();
        this.loadTopLosers();
        this.loadMostActive();

        // Auto-refresh every 5 seconds
        setInterval(() => this.loadMarketStats(), this.updateInterval);
        setInterval(() => this.loadTopGainers(), this.updateInterval);
        setInterval(() => this.loadTopLosers(), this.updateInterval);
        setInterval(() => this.loadMostActive(), this.updateInterval);

        // OPTIONAL: update chart fake data every refresh (remove later)
        setInterval(() => this.updatePortfolioChartDemo(), 15000);
    }

    // ================== PORTFOLIO CHART ==================
    initPortfolioChart() {
        const canvas = document.getElementById('portfolioChart');
        if (!canvas || typeof Chart === "undefined") return;

        const ctx = canvas.getContext('2d');

        this.portfolioChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [118000, 119200, 121500, 120300, 124580],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointBackgroundColor: '#10b981'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: {
                        grid: { color: '#eef2f7' },
                        ticks: {
                            callback: (value) => 'Rs ' + Number(value).toLocaleString()
                        }
                    }
                }
            }
        });
    }

    // Demo chart update (remove when you add real portfolio API)
    updatePortfolioChartDemo() {
        if (!this.portfolioChart) return;

        const last = this.portfolioChart.data.datasets[0].data.slice(-1)[0];
        const next = Math.max(50000, last + Math.round((Math.random() - 0.4) * 3000));

        this.portfolioChart.data.labels.push('Now');
        this.portfolioChart.data.datasets[0].data.push(next);

        // keep last 12 points
        if (this.portfolioChart.data.labels.length > 12) {
            this.portfolioChart.data.labels.shift();
            this.portfolioChart.data.datasets[0].data.shift();
        }

        this.portfolioChart.update();
    }

    // ================== MARKET STATS ==================
    loadMarketStats() {
        fetch(`${this.apiBase}/stats/`)
            .then(res => res.json())
            .then(data => this.updateMarketStats(data))
            .catch(err => console.error('Error loading stats:', err));
    }

    updateMarketStats(data) {
        const totalStocks = document.getElementById('total-stocks');
        const gainers = document.getElementById('gainers-count');
        const losers = document.getElementById('losers-count');
        const unchanged = document.getElementById('unchanged-count');

        if (totalStocks) totalStocks.textContent = data.total ?? 0;
        if (gainers) gainers.textContent = data.gainers ?? 0;
        if (losers) losers.textContent = data.losers ?? 0;
        if (unchanged) unchanged.textContent = data.unchanged ?? 0;
    }

    // ================== TOP GAINERS ==================
    loadTopGainers() {
        fetch(`${this.apiBase}/gainers/`)
            .then(res => res.json())
            .then(data => this.updateTopGainers(data))
            .catch(err => console.error('Error loading gainers:', err));
    }

    updateTopGainers(data) {
        const container = document.getElementById('top-gainers-list');
        if (!container) return;

        const arr = Array.isArray(data?.data) ? data.data.slice(0, 5) : [];

        if (arr.length < 1) {
            container.innerHTML = `<div class="p-3 text-center text-muted">No data</div>`;
            return;
        }

        container.innerHTML = arr.map(stock => this.marketRow(stock, true)).join('');
    }

    // ================== TOP LOSERS ==================
    loadTopLosers() {
        fetch(`${this.apiBase}/losers/`)
            .then(res => res.json())
            .then(data => this.updateTopLosers(data))
            .catch(err => console.error('Error loading losers:', err));
    }

    updateTopLosers(data) {
        const container = document.getElementById('top-losers-list');
        if (!container) return;

        const arr = Array.isArray(data?.data) ? data.data.slice(0, 5) : [];

        if (arr.length < 1) {
            container.innerHTML = `<div class="p-3 text-center text-muted">No data</div>`;
            return;
        }

        container.innerHTML = arr.map(stock => this.marketRow(stock, false)).join('');
    }

    // ================== MOST ACTIVE (TOP 5 BY VOLUME) ==================
    loadMostActive() {
        fetch(`${this.apiBase}/latest/`)
            .then(res => res.json())
            .then(data => this.updateMostActive(data))
            .catch(err => console.error('Error loading most active:', err));
    }

    updateMostActive(data) {
        const container = document.getElementById('most-active-list');
        if (!container) return;

        const stocks = Array.isArray(data?.data) ? data.data : [];
        if (!stocks.length) {
            container.innerHTML = `<div class="p-3 text-center text-muted">No data</div>`;
            return;
        }

        const arr = stocks
            .slice()
            .sort((a, b) => Number(b.volume || 0) - Number(a.volume || 0))
            .slice(0, 5);

        container.innerHTML = arr.map(stock => `
            <div class="market-item">
                <div>
                    <div class="market-symbol">${this.safe(stock.symbol)}</div>
                    <small class="text-muted">${this.formatVolume(stock.volume)} shares</small>
                </div>
                <div class="text-end">
                    <i class="fas fa-bolt text-warning"></i>
                </div>
            </div>
        `).join('');
    }

    // ================== UI ROW HELPERS ==================
    marketRow(stock, isGainer) {
        const symbol = this.safe(stock?.symbol);
        const ltp = this.formatPrice(stock?.ltp);
        const pct = this.formatPct(stock?.change_pct);
        const vol = this.formatVolume(stock?.volume);

        const cls = isGainer ? 'text-success' : 'text-danger';
        const icon = isGainer ? 'fa-arrow-up' : 'fa-arrow-down';
        const sign = isGainer ? '+' : ''; // losers already negative

        return `
            <div class="market-item">
                <div>
                    <div class="market-symbol">${symbol}</div>
                    <small class="text-muted">${symbol} Co.</small>
                </div>
                <div class="text-end">
                    <div class="market-price">Rs ${ltp}</div>
                    <div class="market-change ${cls}">
                        <i class="fas ${icon} me-1"></i>${sign}${pct}%
                    </div>
                </div>
            </div>
        `;
    }

    safe(v) {
        return (v ?? '').toString().replace(/[<>]/g, '');
    }

    formatVolume(volume) {
        const v = Number(volume || 0);
        if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'M';
        if (v >= 1_000) return (v / 1_000).toFixed(1) + 'K';
        return v.toLocaleString();
    }

    formatPrice(price) {
        const p = Number(price || 0);
        return p.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    formatPct(pct) {
        const x = Number(pct || 0);
        return x.toFixed(2);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new NepseDashboard();
});
