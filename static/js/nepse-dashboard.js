// File: static/js/nepse-portfolio.js
// ✅ Uses the same API base patterns as your dashboard.
// Assumption: you have a holdings endpoint that returns user's holdings.
// If you don’t yet, this will still render charts with demo data safely.

class NepsePortfolioPage {
    constructor() {
        this.apiBase = '/api';
        this.updateInterval = 10000;

        this.valueChart = null;
        this.allocationChart = null;

        this.range = '1W'; // default view
        this.init();
    }

    init() {
        this.initCharts();
        this.bindRangeButtons();

        this.loadAll();
        setInterval(() => this.loadAll(), this.updateInterval);
    }

    // ---------- Helpers ----------
    fmtNumber(n, digits = 2) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        return Number(n).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }

    fmtInt(n) {
        if (n === null || n === undefined || isNaN(n)) return '—';
        return Number(n).toLocaleString();
    }

    setText(id, val) {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    }

    // ---------- Charts ----------
    initCharts() {
        // Portfolio Value chart
        const valueCanvas = document.getElementById('portfolioValueChart');
        if (valueCanvas && typeof Chart !== 'undefined') {
            const ctx = valueCanvas.getContext('2d');
            this.valueChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Portfolio Value',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16,185,129,0.15)',
                        fill: true,
                        tension: 0.35,
                        pointRadius: 2,
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
                                callback: (v) => 'Rs ' + Number(v).toLocaleString()
                            }
                        }
                    }
                }
            });
        }

        // Allocation chart (doughnut)
        const allocCanvas = document.getElementById('allocationChart');
        if (allocCanvas && typeof Chart !== 'undefined') {
            const ctx2 = allocCanvas.getContext('2d');
            this.allocationChart = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        // no fixed colors required; Chart.js will auto-generate if you omit
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                    cutout: '60%'
                }
            });
        }
    }

    bindRangeButtons() {
        const map = [
            ['btnRange1D', '1D'],
            ['btnRange1W', '1W'],
            ['btnRange1M', '1M'],
        ];

        map.forEach(([id, value]) => {
            const btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener('click', () => {
                this.range = value;
                this.loadPortfolioSeries(); // reload chart series when range changes
            });
        });
    }

    // ---------- Loaders ----------
    async loadAll() {
        await this.loadHoldingsAndSummary();
        await this.loadPortfolioSeries();
        this.setText('portfolioAsOf', new Date().toLocaleString());
    }

    // 1) Holdings + live LTP merge
    async loadHoldingsAndSummary() {
        const tbody = document.getElementById('holdingsTbody');
        if (!tbody) return;

        try {
            // You should implement this API in Django:
            // GET /api/portfolio/holdings/
            // returns: { success:true, data:[{symbol:"NBL", qty:100, avg_buy:250.5}, ...] }
            const hRes = await fetch(`${this.apiBase}/portfolio/holdings/`);
            const hJson = await hRes.json();
            const holdings = Array.isArray(hJson?.data) ? hJson.data : [];

            // Latest live prices: your existing endpoint
            const lRes = await fetch(`${this.apiBase}/latest/`);
            const lJson = await lRes.json();
            const latest = Array.isArray(lJson?.data) ? lJson.data : [];

            const priceMap = new Map(latest.map(x => [String(x.symbol), x]));

            if (!holdings.length) {
                // fallback demo if no holdings endpoint yet
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-muted p-4">
                            No holdings data yet. Create <code>/api/portfolio/holdings/</code> to show real portfolio.
                        </td>
                    </tr>
                `;

                this.updateSummary([], priceMap);
                this.updateAllocation([], priceMap);
                return;
            }

            // Render holdings rows
            let totalValue = 0;
            let totalPL = 0;

            const rows = holdings.map(h => {
                const sym = String(h.symbol);
                const qty = Number(h.qty || 0);
                const avg = Number(h.avg_buy || 0);

                const live = priceMap.get(sym);
                const ltp = Number(live?.ltp || 0);

                const value = qty * ltp;
                const pl = (ltp - avg) * qty;

                totalValue += value;
                totalPL += pl;

                const plCls = pl >= 0 ? 'text-success' : 'text-danger';
                const plSign = pl >= 0 ? '+' : '';

                return `
                    <tr>
                        <td class="ps-3"><span class="symbol-pill">${sym}</span></td>
                        <td>${this.fmtInt(qty)}</td>
                        <td>Rs ${this.fmtNumber(avg, 2)}</td>
                        <td>Rs ${ltp ? this.fmtNumber(ltp, 2) : '—'}</td>
                        <td>Rs ${this.fmtNumber(value, 2)}</td>
                        <td class="text-end pe-3 ${plCls}">${plSign}Rs ${this.fmtNumber(pl, 2)}</td>
                    </tr>
                `;
            }).join('');

            tbody.innerHTML = rows;

            // Summary + allocation
            this.updateSummary(holdings, priceMap);
            this.updateAllocation(holdings, priceMap);
        } catch (e) {
            console.error('Portfolio holdings load error:', e);
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted p-4">Error loading portfolio.</td></tr>`;
        }
    }

    updateSummary(holdings, priceMap) {
        const n = holdings.length;

        let totalValue = 0;
        let totalCost = 0;

        for (const h of holdings) {
            const sym = String(h.symbol);
            const qty = Number(h.qty || 0);
            const avg = Number(h.avg_buy || 0);

            const live = priceMap.get(sym);
            const ltp = Number(live?.ltp || 0);

            totalValue += qty * ltp;
            totalCost += qty * avg;
        }

        const overallPL = totalValue - totalCost;
        const overallPLPct = totalCost > 0 ? (overallPL / totalCost) * 100 : 0;

        this.setText('sumTotalValue', `Rs ${this.fmtNumber(totalValue, 2)}`);
        this.setText('sumHoldings', `${n}`);

        const plCls = overallPL >= 0 ? 'text-success' : 'text-danger';
        const plSign = overallPL >= 0 ? '+' : '';

        const plEl = document.getElementById('sumOverallPL');
        const plPctEl = document.getElementById('sumOverallPLPct');
        if (plEl) {
            plEl.classList.remove('text-success', 'text-danger');
            plEl.classList.add(plCls);
            plEl.textContent = `${plSign}Rs ${this.fmtNumber(overallPL, 2)}`;
        }
        if (plPctEl) {
            plPctEl.classList.remove('text-success', 'text-danger');
            plPctEl.classList.add(plCls);
            plPctEl.textContent = `${plSign}${this.fmtNumber(overallPLPct, 2)}%`;
        }

        // Today's P/L placeholder (needs portfolio history; keep simple)
        this.setText('sumTodayPL', '—');
        this.setText('sumTodayPLPct', 'connect later');
    }

    updateAllocation(holdings, priceMap) {
        if (!this.allocationChart) return;

        const items = holdings.map(h => {
            const sym = String(h.symbol);
            const qty = Number(h.qty || 0);
            const ltp = Number(priceMap.get(sym)?.ltp || 0);
            return { sym, value: qty * ltp };
        }).filter(x => x.value > 0);

        items.sort((a, b) => b.value - a.value);

        const top = items.slice(0, 8);
        const labels = top.map(x => x.sym);
        const data = top.map(x => Math.round(x.value));

        this.allocationChart.data.labels = labels;
        this.allocationChart.data.datasets[0].data = data;
        this.allocationChart.update();
    }

    // 2) Portfolio value series (Live)
    async loadPortfolioSeries() {
        if (!this.valueChart) return;

        try {
            // Recommended API:
            // GET /api/portfolio/value-series/?range=1D|1W|1M
            // returns: { success:true, data:{ labels:[...], values:[...] , perf:{d1:2.3,w1:5.7,m1:-1.2} } }
            const res = await fetch(`${this.apiBase}/portfolio/value-series/?range=${encodeURIComponent(this.range)}`);
            const json = await res.json();

            const labels = json?.data?.labels || [];
            const values = json?.data?.values || [];

            // If endpoint not ready, do demo series
            const useDemo = !labels.length || !values.length;
            const demo = this.makeDemoSeries(this.range);

            this.valueChart.data.labels = useDemo ? demo.labels : labels;
            this.valueChart.data.datasets[0].data = useDemo ? demo.values : values;
            this.valueChart.update();

            // Update performance (1D/1W/1M)
            const perf = json?.data?.perf || demo.perf;
            this.applyPerf('perf1d', perf.d1);
            this.applyPerf('perf1w', perf.w1);
            this.applyPerf('perf1m', perf.m1);
        } catch (e) {
            console.error('Portfolio series load error:', e);
        }
    }

    applyPerf(elId, pct) {
        const el = document.getElementById(elId);
        if (!el) return;

        if (pct === null || pct === undefined || isNaN(pct)) {
            el.textContent = '—';
            el.classList.remove('text-success', 'text-danger');
            el.classList.add('text-muted');
            return;
        }

        const cls = Number(pct) >= 0 ? 'text-success' : 'text-danger';
        const sign = Number(pct) >= 0 ? '+' : '';

        el.classList.remove('text-success', 'text-danger', 'text-muted');
        el.classList.add(cls);
        el.textContent = `${sign}${Number(pct).toFixed(2)}%`;
    }

    makeDemoSeries(range) {
        // quick demo; replace when your /api/portfolio/value-series/ works
        const base = 120000;
        let points = 7;
        if (range === '1D') points = 12;
        if (range === '1M') points = 30;

        const labels = [];
        const values = [];
        let v = base;

        for (let i = 0; i < points; i++) {
            labels.push(range === '1D' ? `T${i + 1}` : `D${i + 1}`);
            v = Math.max(50000, v + Math.round((Math.random() - 0.45) * 2500));
            values.push(v);
        }

        return {
            labels,
            values,
            perf: { d1: 2.30, w1: 5.70, m1: -1.20 }
        };
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new NepsePortfolioPage();
});
