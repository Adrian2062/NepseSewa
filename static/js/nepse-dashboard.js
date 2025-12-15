// Create this file: static/js/nepse-dashboard.js

class NepseDashboard {
    constructor() {
        this.apiBase = '/api';
        this.updateInterval = 5000; // 5 seconds
        this.init();
    }

    init() {
        this.loadMarketStats();
        this.loadTopGainers();
        this.loadTopLosers();
        
        // Auto-refresh every 5 seconds
        setInterval(() => this.loadMarketStats(), this.updateInterval);
        setInterval(() => this.loadTopGainers(), this.updateInterval);
        setInterval(() => this.loadTopLosers(), this.updateInterval);
    }

    // Load market statistics
    loadMarketStats() {
        fetch(`${this.apiBase}/stats/`)
            .then(response => response.json())
            .then(data => this.updateMarketStats(data))
            .catch(error => console.error('Error loading stats:', error));
    }

    updateMarketStats(data) {
        const statsContainer = document.getElementById('market-stats');
        if (!statsContainer) return;

        // Update Market Stats card
        const totalStocks = document.getElementById('total-stocks');
        const gainers = document.getElementById('gainers-count');
        const losers = document.getElementById('losers-count');
        const unchanged = document.getElementById('unchanged-count');

        if (totalStocks) totalStocks.textContent = data.total || 0;
        if (gainers) gainers.textContent = data.gainers || 0;
        if (losers) losers.textContent = data.losers || 0;
        if (unchanged) unchanged.textContent = data.unchanged || 0;

        // Update news ticker
        const tickerContent = document.querySelector('.ticker-content');
        if (tickerContent) {
            const gainersPercent = ((data.gainers / data.total) * 100).toFixed(1);
            tickerContent.textContent = `📈 NEPSE Trading | 📊 Gainers: ${data.gainers} (${gainersPercent}%) | 📉 Losers: ${data.losers} | Total: ${data.total}`;
        }
    }

    // Load top gainers
    loadTopGainers() {
        fetch(`${this.apiBase}/gainers/`)
            .then(response => response.json())
            .then(data => this.updateTopGainers(data))
            .catch(error => console.error('Error loading gainers:', error));
    }

    updateTopGainers(data) {
        const container = document.getElementById('top-gainers-list');
        if (!container || !data.data || data.data.length === 0) return;

        container.innerHTML = data.data.slice(0, 4).map(stock => `
            <div class="market-item">
                <div>
                    <div class="market-symbol">${stock.symbol}</div>
                    <small class="text-muted">${this.formatVolume(stock.volume)}</small>
                </div>
                <div class="text-end">
                    <div class="market-price">Rs ${parseFloat(stock.ltp).toFixed(2)}</div>
                    <div class="market-change text-success">+${parseFloat(stock.change_pct).toFixed(2)}%</div>
                </div>
            </div>
        `).join('');
    }

    // Load top losers
    loadTopLosers() {
        fetch(`${this.apiBase}/losers/`)
            .then(response => response.json())
            .then(data => this.updateTopLosers(data))
            .catch(error => console.error('Error loading losers:', error));
    }

    updateTopLosers(data) {
        const container = document.getElementById('top-losers-list');
        if (!container || !data.data || data.data.length === 0) return;

        container.innerHTML = data.data.slice(0, 4).map(stock => `
            <div class="market-item">
                <div>
                    <div class="market-symbol">${stock.symbol}</div>
                    <small class="text-muted">${this.formatVolume(stock.volume)}</small>
                </div>
                <div class="text-end">
                    <div class="market-price">Rs ${parseFloat(stock.ltp).toFixed(2)}</div>
                    <div class="market-change text-danger">${parseFloat(stock.change_pct).toFixed(2)}%</div>
                </div>
            </div>
        `).join('');
    }

    // Format volume
    formatVolume(volume) {
        if (!volume) return '0';
        if (volume >= 1000000) return (volume / 1000000).toFixed(1) + 'M';
        if (volume >= 1000) return (volume / 1000).toFixed(0) + 'K';
        return volume.toFixed(0);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new NepseDashboard();
});