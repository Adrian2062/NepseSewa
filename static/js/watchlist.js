// Watchlist & Recommendation Logic

async function fetchWatchlist() {
    try {
        const response = await fetch('/api/recommendations/');
        const result = await response.json();

        if (result.success) {
            renderWatchlist(result.data);
            updateKPIs(result.data);
        } else {
            showError('Failed to fetch recommendations');
        }
    } catch (error) {
        console.error('Error fetching watchlist:', error);
        showError('Network error while fetching watchlist');
    }
}

function renderWatchlist(data) {
    const tbody = document.getElementById('watchlistBody');
    if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-muted fw-bold">Your watchlist is empty. Add some stocks to see recommendations!</td></tr>`;
        return;
    }

    tbody.innerHTML = data.map(item => `
        <tr data-symbol="${item.symbol}" data-signal="${item.recommendation}">
            <td class="ps-3 fw-bold underline-hover"><a href="/trade/?symbol=${item.symbol}" class="text-decoration-none text-dark">${item.symbol}</a></td>
            <td class="fw-bold">Rs ${item.current_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td class="fw-bold text-primary">Rs ${item.predicted_price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
            <td class="fw-bold ${getPriceColor(item.current_price, item.predicted_price)}">
                ${calculateChange(item.current_price, item.predicted_price)}%
            </td>
            <td>
                <span class="signal-pill ${getSignalClass(item.recommendation)}">
                    ${item.recommendation_str}
                </span>
            </td>
            <td>
                <div class="small text-muted fw-bold">RMSE: ${item.rmse ? item.rmse.toFixed(4) : 'N/A'}</div>
                <div class="small text-muted">MAE: ${item.mae ? item.mae.toFixed(4) : 'N/A'}</div>
            </td>
            <td class="text-end pe-3">
                <button class="btn btn-sm btn-light me-1 refresh-stock" title="Refresh Prediction" data-symbol="${item.symbol}">
                    <i class="fas fa-sync-alt"></i>
                </button>
                <button class="btn btn-sm btn-light text-danger remove-stock" title="Remove" data-symbol="${item.symbol}">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');

    attachEventListeners();
}

function getSignalClass(rec) {
    if (rec === 1) return 'sig-buy';
    if (rec === -1) return 'sig-sell';
    return 'sig-hold';
}

function getPriceColor(curr, pred) {
    if (pred > curr * 1.015) return 'text-success';
    if (pred < curr * 0.985) return 'text-danger';
    return 'text-muted';
}

function calculateChange(curr, pred) {
    const change = ((pred - curr) / curr) * 100;
    return (change > 0 ? '+' : '') + change.toFixed(2);
}

function updateKPIs(data) {
    document.getElementById('kpiWatchCount').textContent = data.length;
    document.getElementById('kpiBuyCount').textContent = data.filter(i => i.recommendation === 1).length;
    document.getElementById('kpiSellCount').textContent = data.filter(i => i.recommendation === -1).length;
}

function attachEventListeners() {
    document.querySelectorAll('.remove-stock').forEach(btn => {
        btn.onclick = () => toggleWatchlist(btn.dataset.symbol);
    });

    document.querySelectorAll('.refresh-stock').forEach(btn => {
        btn.onclick = () => refreshRecommendation(btn.dataset.symbol);
    });
}

async function toggleWatchlist(symbol) {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return;

    try {
        const response = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const result = await response.json();
        if (result.success) {
            fetchWatchlist();
        }
    } catch (e) {
        console.error(e);
    }
}

async function refreshRecommendation(symbol) {
    const btn = document.querySelector(`.refresh-stock[data-symbol="${symbol}"]`);
    if (btn) btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';

    try {
        const response = await fetch('/api/recommendations/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const result = await response.json();
        if (result.success) {
            fetchWatchlist();
        } else {
            alert(result.message);
            fetchWatchlist(); // Reset button
        }
    } catch (e) {
        console.error(e);
        fetchWatchlist();
    }
}

// Add Stock Form
document.getElementById('addStockForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const symbol = document.getElementById('stockSymbolInput').value.trim().toUpperCase();
    const btn = document.getElementById('addSubmitBtn');

    btn.disabled = true;
    btn.querySelector('.spinner-border').classList.remove('d-none');

    try {
        // 1. Add to watchlist
        const resToggle = await fetch('/api/watchlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ symbol })
        });
        const toggleResult = await resToggle.json();

        if (toggleResult.success && toggleResult.action === 'added') {
            // 2. Trigger initial recommendation
            const resRefresh = await fetch('/api/recommendations/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ symbol })
            });
            const refreshResult = await resRefresh.json();

            if (!refreshResult.success) {
                alert(`Added to watchlist, but recommendation failed: ${refreshResult.message}`);
            }
        }

        // Cleanup
        bootstrap.Modal.getInstance(document.getElementById('addStockModal')).hide();
        document.getElementById('addStockForm').reset();
        fetchWatchlist();
    } catch (err) {
        console.error(err);
    } finally {
        btn.disabled = false;
        btn.querySelector('.spinner-border').classList.add('d-none');
    }
});

// Refresh All
document.getElementById('refreshAllBtn')?.addEventListener('click', async () => {
    const symbols = Array.from(document.querySelectorAll('#watchlistBody tr[data-symbol]'))
        .map(tr => tr.dataset.symbol);

    if (!symbols.length) return;

    const btn = document.getElementById('refreshAllBtn');
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Refreshing...';
    btn.disabled = true;

    for (const sym of symbols) {
        await refreshRecommendation(sym);
    }

    btn.innerHTML = originalHtml;
    btn.disabled = false;
});

// Filtering
document.getElementById('wlSearch')?.addEventListener('input', applyFilters);
document.getElementById('wlSignal')?.addEventListener('change', applyFilters);

function applyFilters() {
    const q = (document.getElementById('wlSearch')?.value || '').trim().toUpperCase();
    const sig = (document.getElementById('wlSignal')?.value || '').trim();

    const rows = document.querySelectorAll('#watchlistBody tr[data-symbol]');
    rows.forEach(r => {
        const okQ = !q || r.dataset.symbol.includes(q);
        const okSig = !sig || r.dataset.signal === sig;
        r.style.display = (okQ && okSig) ? '' : 'none';
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showError(msg) {
    const tbody = document.getElementById('watchlistBody');
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-5 text-danger fw-bold">${msg}</td></tr>`;
}

document.addEventListener('DOMContentLoaded', fetchWatchlist);
