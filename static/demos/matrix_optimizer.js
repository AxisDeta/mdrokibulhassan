/**
 * Sustainable Supply Chain Matrix - Interactive Frontend
 */

let currentResults = null;

document.addEventListener('DOMContentLoaded', function () {
    const configForm = document.getElementById('matrixConfigForm');
    const cmSelector = document.getElementById('cmModelSelect');

    // Handle initial form submission
    if (configForm) {
        configForm.addEventListener('submit', function (e) {
            e.preventDefault();
            runMatrixAnalysis();
        });
    }

    // Handle CM Model Selection
    if (cmSelector) {
        cmSelector.addEventListener('change', function () {
            if (currentResults) {
                renderConfusionMatrix(this.value);
            }
        });
    }

    // Initialize Theme Observer (Reusing logic from other demos)
    initThemeObserver();
});

// Helper to get current theme colors from CSS variables
function getThemeColors() {
    const style = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    return {
        primary: style.getPropertyValue('--primary-color').trim() || '#2563eb',
        text: style.getPropertyValue('--text-primary').trim() || (isDark ? '#f1f5f9' : '#0f172a'),
        grid: style.getPropertyValue('--border-color').trim() || (isDark ? '#334155' : '#e2e8f0'),
        accent: style.getPropertyValue('--secondary-color').trim() || '#f59e0b'
    };
}

// Watch for theme changes
function initThemeObserver() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
                // Add a small delay to ensure CSS variables have updated
                setTimeout(() => {
                    if (currentResults) {
                        // Re-render charts with new theme
                        renderAccuracyChart(currentResults.metrics);
                        const selectedModel = document.getElementById('cmModelSelect').value;
                        renderConfusionMatrix(selectedModel);
                    }
                }, 50);
            }
        });
    });

    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
}

/**
 * Run Analysis API Call
 */
async function runMatrixAnalysis() {
    const nSamples = document.getElementById('sampleSize').value;
    const initial = document.getElementById('initialState');
    const loading = document.getElementById('loadingState');
    const completion = document.getElementById('completionState');
    const resultsSection = document.getElementById('resultsSection');

    // UI State
    if (initial) initial.style.display = 'none';
    if (loading) loading.style.display = 'block';
    if (completion) completion.style.display = 'none';
    if (resultsSection) resultsSection.style.display = 'none';

    try {
        const response = await fetch('/demos/api/matrix-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                n_samples: nSamples
            })
        });

        const data = await response.json();
        currentResults = data;

        if (data.error) throw new Error(data.error);

        // Render Main Charts
        renderAccuracyChart(data.metrics);
        renderConfusionMatrix('Random Forest'); // Default

        // Render Metric Cards
        renderMetricCards(data.metrics);

        // Show results
        if (loading) loading.style.display = 'none';
        if (completion) completion.style.display = 'block';
        if (resultsSection) resultsSection.style.display = 'block';

        // Scroll
        resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error('Matrix Analysis Error:', error);
        alert('Failed to run analysis: ' + error.message);
        if (loading) loading.style.display = 'none';
        if (initial) initial.style.display = 'block';
    }
}

/**
 * Render Bar Chart for Model Accuracy
 */
function renderAccuracyChart(metrics) {
    const colors = getThemeColors();
    const models = Object.keys(metrics);
    const accuracies = models.map(m => metrics[m].accuracy);

    // Color highlight the best model
    const maxAcc = Math.max(...accuracies);
    const barColors = accuracies.map(a => a === maxAcc ? colors.accent : '#94a3b8');

    const data = [{
        x: models,
        y: accuracies,
        type: 'bar',
        marker: { color: barColors },
        text: accuracies.map(a => (a * 100).toFixed(1) + '%'),
        textposition: 'auto',
        hovertemplate: '<b>%{x}</b><br>Accuracy: %{y:.3f}<extra></extra>',
        textfont: { color: colors.text }
    }];

    const layout = {
        title: {
            text: 'Model Accuracy Comparison',
            font: { color: colors.text }
        },
        margin: { t: 40, b: 40, l: 60, r: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: colors.text },
        yaxis: {
            title: 'Accuracy',
            range: [0, 1.1],
            gridcolor: colors.grid,
            zerolinecolor: colors.grid,
            tickcolor: colors.grid
        },
        xaxis: {
            gridcolor: colors.grid,
            tickcolor: colors.grid
        },
        autosize: true
    };

    Plotly.newPlot('accuracyChart', data, layout, { responsive: true, displayModeBar: false });
}

/**
 * Render Confusion Matrix Heatmap
 */
function renderConfusionMatrix(modelName) {
    if (!currentResults) return;

    const metric = currentResults.metrics[modelName];
    const cm = metric.confusion_matrix;
    const classes = currentResults.classes;
    const colors = getThemeColors();

    const data = [{
        z: cm,
        x: classes,
        y: classes,
        type: 'heatmap',
        colorscale: 'Blues',
        showscale: false,
        text: cm.map(row => row.map(String)), // Display values
        texttemplate: "%{text}",
        textfont: { color: 'black' } // Keep text readable on blue
    }];

    const layout = {
        margin: { t: 20, b: 40, l: 60, r: 20 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', color: colors.text },
        xaxis: { title: 'Predicted', tickcolor: colors.grid },
        yaxis: { title: 'Actual', tickcolor: colors.grid, automargin: true },
        autosize: true
    };

    Plotly.newPlot('confusionMatrixChart', data, layout, { responsive: true, displayModeBar: false });
}

/**
 * Render Detailed Metric Cards
 */
function renderMetricCards(metrics) {
    const container = document.getElementById('metricsGrid');
    if (!container) return;
    container.innerHTML = ''; // Clear previous

    Object.keys(metrics).forEach(model => {
        const m = metrics[model];
        const card = document.createElement('div');
        card.className = 'metric-card';
        card.innerHTML = `
            <div class="metric-header">
                <span class="metric-title">${model}</span>
                <i class="fas fa-chart-pie" style="color: var(--text-tertiary)"></i>
            </div>
            <div class="metric-score">${(m.accuracy * 100).toFixed(1)}%</div>
            <div class="metric-label">Accuracy</div>
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color); display: flex; justify-content: space-between;">
                <div>
                    <div style="font-weight: 700; color: var(--text-primary)">
                        ${(m.precision * 100).toFixed(1)}%
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary)">Precision</div>
                </div>
                <div>
                     <div style="font-weight: 700; color: var(--text-primary)">
                        ${(m.recall * 100).toFixed(1)}%
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary)">Recall</div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}
