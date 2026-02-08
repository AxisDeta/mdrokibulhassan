/**
 * Carbon Reduction Calculator - Interactive Frontend
 * Based on Walmart Supply Chain Research (2019-2021)
 */

document.addEventListener('DOMContentLoaded', function () {
    const configForm = document.getElementById('carbonConfigForm');
    const runScenarioBtn = document.getElementById('runScenarioBtn');

    // Handle initial form submission
    if (configForm) {
        configForm.addEventListener('submit', function (e) {
            e.preventDefault();
            calculateFootprint();
        });
    }

    // Handle scenario run (scroll to comparison)
    if (runScenarioBtn) {
        runScenarioBtn.addEventListener('click', () => {
            document.getElementById('detailedCharts').scrollIntoView({ behavior: 'smooth' });
        });
    }

    // Initialize Theme Observer
    initThemeObserver();
});

/**
 * Get current theme colors from CSS variables
 */
function getThemeColors() {
    const style = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    return {
        primary: style.getPropertyValue('--primary-color').trim() || '#2563eb',
        text: style.getPropertyValue('--text-primary').trim() || (isDark ? '#f1f5f9' : '#0f172a'),
        secondaryText: style.getPropertyValue('--text-secondary').trim() || (isDark ? '#cbd5e1' : '#475569'),
        grid: style.getPropertyValue('--border-color').trim() || (isDark ? '#334155' : '#e2e8f0'),
        accent: style.getPropertyValue('--secondary-color').trim() || '#f59e0b',
        success: '#10b981',
        danger: '#ef4444'
    };
}

// Watch for theme changes
function initThemeObserver() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                setTimeout(() => {
                    calculateFootprint(false); // Re-render without loading state
                }, 50);
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
}

/**
 * Calculate the emissions based on simulated logic
 */
function calculateFootprint(showLoading = true) {
    const activity = parseFloat(document.getElementById('activityLevel').value) || 0;
    const energy = parseFloat(document.getElementById('energyConsumption').value) || 0;
    const fuel = document.getElementById('fuelType').value;
    const weather = document.getElementById('weatherCondition').value;

    const initial = document.getElementById('dashboardInitial');
    const loading = document.getElementById('dashboardLoading');
    const results = document.getElementById('dashboardResults');
    const detailedCharts = document.getElementById('detailedCharts');

    if (showLoading) {
        if (initial) initial.style.display = 'none';
        if (loading) loading.style.display = 'block';
        if (results) results.style.display = 'none';
        if (detailedCharts) detailedCharts.style.display = 'none';
    }

    // Simulation Factors
    const fuelFactors = { 'Diesel': 2.68, 'Gasoline': 2.31, 'Natural Gas': 1.9, 'Grid Electricity': 0.45 };
    const weatherFactors = { 'Sunny': 1.0, 'Rainy': 1.05, 'Snowy': 1.15, 'Extreme': 1.25 };

    // Logic: Energy * Factor * (Activity/100) * Weather
    const baseEmission = energy * (fuelFactors[fuel] || 0.5);
    const totalEmission = baseEmission * (activity / 100) * (weatherFactors[weather] || 1.0);

    // Optimization potential (RF predicted improvement)
    const optimizedEmission = totalEmission * 0.85; // ~15% reduction

    // Simulate delay
    setTimeout(() => {
        // Update Metrics
        document.getElementById('totalEmissionsVal').textContent = Math.round(totalEmission).toLocaleString();
        const reduction = totalEmission - optimizedEmission;
        document.getElementById('reductionVal').textContent = `-${Math.round(reduction).toLocaleString()} kg`;

        // Render Charts
        renderROCCurve();
        renderComparisonChart();

        if (showLoading) {
            if (loading) loading.style.display = 'none';
            if (results) results.style.display = 'block';
            if (detailedCharts) detailedCharts.style.display = 'block';
            results.scrollIntoView({ behavior: 'smooth' });
        }
    }, showLoading ? 800 : 0);
}

/**
 * Render ROC Curve (Fig 2 from Paper)
 */
function renderROCCurve() {
    const colors = getThemeColors();

    // Simulated ROC Curves based on AUC values
    // RF: 0.92, XGB: 0.92, Bagging: 0.90

    const traceRF = {
        x: [0, 0.05, 0.1, 0.2, 0.4, 0.7, 1],
        y: [0, 0.6, 0.85, 0.92, 0.96, 0.99, 1],
        mode: 'lines',
        name: 'Random Forest (AUC 0.92)',
        line: { color: colors.success, width: 3 } // Green for best
    };

    const traceXGB = {
        x: [0, 0.05, 0.15, 0.25, 0.45, 0.75, 1],
        y: [0, 0.55, 0.82, 0.90, 0.94, 0.98, 1],
        mode: 'lines',
        name: 'XG-Boost (AUC 0.92)',
        line: { color: colors.accent, width: 2, dash: 'dash' }
    };

    const traceBagging = {
        x: [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1],
        y: [0, 0.5, 0.75, 0.85, 0.91, 0.96, 1],
        mode: 'lines',
        name: 'Bagging (AUC 0.90)',
        line: { color: colors.secondaryText, width: 2, dash: 'dot' }
    };

    const layout = {
        title: { text: 'ROC Curve Analysis', font: { color: colors.text } },
        xaxis: { title: 'False Positive Rate', gridcolor: colors.grid, zerolinecolor: colors.grid, color: colors.text },
        yaxis: { title: 'True Positive Rate', gridcolor: colors.grid, zerolinecolor: colors.grid, color: colors.text },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        legend: { x: 0.6, y: 0.1, font: { color: colors.text } },
        margin: { t: 40, b: 40, l: 50, r: 20 },
        height: 300
    };

    Plotly.newPlot('rocChart', [traceRF, traceXGB, traceBagging], layout, { responsive: true, displayModeBar: false });
}

/**
 * Render Comparison Chart (Table 1 & 2 Data)
 */
function renderComparisonChart() {
    const colors = getThemeColors();

    // Metrics: Precision, Recall, AUC
    const models = ['Random Forest', 'XG-Boost', 'Bagging'];

    // Normalized execution time for visualization (1 = fast, 0 = slow)
    // RF: 11.8ms (Fast), XGB: 154ms (Slow)

    const tracePrecision = {
        x: models,
        y: [92.5, 92.1, 91.5],
        name: 'Precision (%)',
        type: 'bar',
        marker: { color: colors.primary }
    };

    const traceError = {
        x: models,
        y: [7.5, 8.5, 7.9], // Error Rate * 100 for scale
        name: 'Error Rate (x100)',
        type: 'bar',
        marker: { color: colors.danger }
    };

    const layout = {
        barmode: 'group',
        title: { text: 'Model Performance Metrics', font: { color: colors.text } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: colors.text },
        xaxis: { gridcolor: colors.grid, color: colors.text },
        yaxis: { title: 'Score', gridcolor: colors.grid, color: colors.text },
        legend: { orientation: 'h', y: -0.2 },
        margin: { t: 40, b: 40, l: 50, r: 20 },
        height: 400
    };

    Plotly.newPlot('comparisonChart', [tracePrecision, traceError], layout, { responsive: true, displayModeBar: false });
}
