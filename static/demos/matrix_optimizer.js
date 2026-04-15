let currentResults = null;

document.addEventListener('DOMContentLoaded', function () {
    const configForm = document.getElementById('matrixConfigForm');
    if (configForm) {
        configForm.addEventListener('submit', function (event) {
            event.preventDefault();
            runMatrixAnalysis();
        });
    }

    initThemeObserver();
});

function getThemeColors() {
    const style = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    return {
        primary: style.getPropertyValue('--primary-color').trim() || '#2563eb',
        text: style.getPropertyValue('--text-primary').trim() || (isDark ? '#f1f5f9' : '#0f172a'),
        grid: style.getPropertyValue('--border-color').trim() || (isDark ? '#334155' : '#e2e8f0'),
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        neutral: '#94a3b8'
    };
}

function initThemeObserver() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme' && currentResults) {
                setTimeout(() => renderMatrixViews(currentResults), 50);
            }
        });
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
}

function formatInt(value) {
    return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function formatCurrency(value) {
    return `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatPercent(value) {
    return `${Number(value || 0).toFixed(1)}%`;
}

async function runMatrixAnalysis() {
    const initial = document.getElementById('initialState');
    const loading = document.getElementById('loadingState');
    const completion = document.getElementById('completionState');
    const resultsSection = document.getElementById('resultsSection');

    if (initial) initial.style.display = 'none';
    if (loading) loading.style.display = 'block';
    if (completion) completion.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';

    try {
        const response = await fetch('/demos/api/matrix-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                n_samples: document.getElementById('sampleSize').value
            })
        });

        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Matrix analysis failed.');
        }

        currentResults = data;
        renderSummary(data);
        renderMatrixViews(data);

        requestBusinessInsight({
            demoId: 'sustainability-matrix',
            context: {
                portfolio_summary: data.portfolio_summary || null,
                dataset_summary: data.dataset_summary || null
            },
            fallbackInsight: buildMatrixFallback(data),
            containerId: 'businessInsightContainer'
        });

        if (loading) loading.style.display = 'none';
        if (completion) completion.style.display = 'block';
        if (resultsSection) resultsSection.style.display = 'block';
        if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Matrix analysis error:', error);
        if (loading) loading.style.display = 'none';
        if (initial) initial.style.display = 'block';
        alert(`Failed to run analysis: ${error.message}`);
    }
}

function buildMatrixFallback(data) {
    const summary = data.portfolio_summary || {};
    const priorityCategory = (summary.priority_categories || [])[0];
    const topSupplier = (summary.top_suppliers || [])[0];
    const lowCount = Number(summary.rating_counts?.Low || 0);
    const mediumCount = Number(summary.rating_counts?.Medium || 0);
    let priority = 'Monitor';

    if (lowCount > mediumCount) {
        priority = 'High';
    } else if (lowCount > 0) {
        priority = 'Medium';
    }

    const recommendations = [];
    if (priorityCategory) {
        recommendations.push(`Start with ${priorityCategory.category}, where ${formatPercent(priorityCategory.low_share)} of records are rated Low.`);
    }
    if (topSupplier && topSupplier.dominant_rating === 'High') {
        recommendations.push(`Use supplier ${topSupplier.supplier} as a benchmark for sourcing and sustainability follow-up.`);
    }
    recommendations.push('Focus supplier development effort on the lowest-rated categories before expanding the program more broadly.');

    return {
        headline: 'The portfolio view shows where sustainability action should start and which suppliers are best positioned to support improvement.',
        priority,
        recommendations,
        interpretation: [
            'Use the rating mix to judge whether the supplier base is concentrated in stronger or weaker sustainability tiers.',
            'Use category hotspots to decide where procurement and supplier-development teams should spend time first.'
        ],
        business_impact: [
            'This helps target sustainability spend where it is most likely to reduce sourcing risk and improve portfolio quality.',
            'A focused rollout is more practical than treating every supplier and category as equally urgent.'
        ],
        watchouts: [
            'A strong overall rating mix can still hide weak categories that deserve immediate follow-up.',
            'Supplier averages should guide prioritization, but final actions should still consider contract criticality and volume.'
        ]
    };
}

function renderSummary(data) {
    const summary = data.portfolio_summary || {};
    const container = document.getElementById('matrixSummaryContent');
    if (!container) return;

    container.innerHTML = `
        <div class="summary-section">
            <h3><i class="fas fa-layer-group"></i> Portfolio Snapshot</h3>
            <div class="summary-metrics">
                <div class="summary-metric success">
                    <div class="summary-label">High Rated</div>
                    <div class="summary-value">${formatInt(summary.rating_counts?.High)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Medium Rated</div>
                    <div class="summary-value">${formatInt(summary.rating_counts?.Medium)}</div>
                </div>
                <div class="summary-metric warning">
                    <div class="summary-label">Low Rated</div>
                    <div class="summary-value">${formatInt(summary.rating_counts?.Low)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Average Lead Time</div>
                    <div class="summary-value">${Number(summary.avg_lead_time || 0).toFixed(1)} days</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Average Defect Rate</div>
                    <div class="summary-value">${formatPercent((summary.avg_defect_rate || 0) * 100)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Average Cost Per Unit</div>
                    <div class="summary-value">${formatCurrency(summary.avg_cost_per_unit)}</div>
                </div>
            </div>
        </div>
    `;
}

function renderMatrixViews(data) {
    renderRatingMixChart(data.portfolio_summary || {});
    renderCategoryChart(data.portfolio_summary || {});
    renderSupplierTable(data.portfolio_summary || {});
}

function renderRatingMixChart(summary) {
    const colors = getThemeColors();
    const counts = summary.rating_counts || {};

    Plotly.newPlot('ratingMixChart', [{
        labels: ['High', 'Medium', 'Low'],
        values: [
            Number(counts.High || 0),
            Number(counts.Medium || 0),
            Number(counts.Low || 0)
        ],
        type: 'pie',
        hole: 0.55,
        marker: {
            colors: [colors.success, colors.warning, colors.danger]
        },
        textinfo: 'label+percent',
        hovertemplate: '<b>%{label}</b><br>Suppliers: %{value}<extra></extra>'
    }], {
        margin: { t: 20, b: 20, l: 20, r: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: colors.text }
    }, { responsive: true, displayModeBar: false });
}

function renderCategoryChart(summary) {
    const colors = getThemeColors();
    const categories = summary.priority_categories || [];

    Plotly.newPlot('categoryChart', [{
        x: categories.map(item => item.category),
        y: categories.map(item => Number(item.low_share || 0)),
        type: 'bar',
        marker: {
            color: categories.map((item, index) => index === 0 ? colors.danger : colors.warning)
        },
        text: categories.map(item => formatPercent(item.low_share)),
        textposition: 'auto',
        hovertemplate: '<b>%{x}</b><br>Low-rated share: %{y:.1f}%<extra></extra>'
    }], {
        margin: { t: 20, b: 60, l: 60, r: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: colors.text },
        yaxis: {
            title: 'Low-Rated Share (%)',
            gridcolor: colors.grid,
            tickcolor: colors.grid
        },
        xaxis: {
            gridcolor: colors.grid,
            tickcolor: colors.grid
        }
    }, { responsive: true, displayModeBar: false });
}

function renderSupplierTable(summary) {
    const container = document.getElementById('supplierMatrixTable');
    if (!container) return;

    const suppliers = summary.top_suppliers || [];
    container.innerHTML = `
        <div class="route-table-container">
            <table class="route-table">
                <thead>
                    <tr>
                        <th>Supplier</th>
                        <th>Dominant Rating</th>
                        <th>Records</th>
                        <th>Average Lead Time</th>
                        <th>Average Defect Rate</th>
                        <th>Average Cost Per Unit</th>
                    </tr>
                </thead>
                <tbody>
                    ${suppliers.map(item => `
                        <tr>
                            <td><strong>${escapeHtml(item.supplier)}</strong></td>
                            <td>${escapeHtml(item.dominant_rating)}</td>
                            <td>${formatInt(item.records)}</td>
                            <td>${Number(item.avg_lead_time || 0).toFixed(1)} days</td>
                            <td>${formatPercent((item.avg_defect_rate || 0) * 100)}</td>
                            <td>${formatCurrency(item.avg_cost_per_unit)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}
