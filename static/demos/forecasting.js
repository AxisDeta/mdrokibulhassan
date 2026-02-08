// Advanced AI Demand Forecasting Demo JavaScript

let forecastResults = null;
let currentModel = 'Linear Regression';

// File upload handling
const fileInput = document.getElementById('dataFile');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileName = document.getElementById('fileName');

// Redundant click handler removed - input[type="file"] covers the area
// fileUploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileName.textContent = `Selected: ${e.target.files[0].name}`;
        fileName.style.display = 'block';
    }
});

// Drag and drop
fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('drag-over');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('drag-over');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');

    if (e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        fileName.textContent = `Selected: ${e.dataTransfer.files[0].name}`;
        fileName.style.display = 'block';
    }
});

// Form submission
document.getElementById('forecastForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);

    // Show loading state
    showState('loading');

    try {
        const response = await fetch('/demos/demand-forecasting', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to process forecast');
        }

        // Store results
        forecastResults = data;

        // Display results
        displayResults(data);
        showState('results');

    } catch (error) {
        showError(error.message);
    }
});

function showState(state) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('resultsState').style.display = 'none';
    document.getElementById('resultsCharts').style.display = 'none';
    document.getElementById('initialState').style.display = 'none';

    if (state === 'loading') {
        document.getElementById('loadingState').style.display = 'flex';
    } else if (state === 'error') {
        document.getElementById('errorState').style.display = 'flex';
    } else if (state === 'results') {
        document.getElementById('resultsState').style.display = 'block';
        document.getElementById('resultsCharts').style.display = 'block';
        // Trigger resize to ensure charts fit container
        window.dispatchEvent(new Event('resize'));
    } else {
        document.getElementById('initialState').style.display = 'flex';
    }
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    showState('error');
}

function displayResults(data) {
    // Update dataset statistics
    document.getElementById('statRecords').textContent = data.stats.total_records;
    document.getElementById('statFeatures').textContent = data.stats.features_count;
    document.getElementById('statMean').textContent = data.stats.target_mean.toFixed(2);
    document.getElementById('statStd').textContent = data.stats.target_std.toFixed(2);

    // Update feature engineering info
    document.getElementById('origFeatures').textContent = data.preprocessing.original_features;
    document.getElementById('processedFeatures').textContent = data.preprocessing.processed_features;
    document.getElementById('pcaComponents').textContent = data.preprocessing.pca_components;
    document.getElementById('varianceRetained').textContent = (data.preprocessing.variance_retained * 100).toFixed(1) + '%';

    // Display comparison table
    displayComparisonTable(data);

    // Display predictions charts for current model
    displayForecastChart(currentModel);
    displayFitChart(currentModel);
}

function displayComparisonTable(data) {
    const models = data.models;
    const modelNames = Object.keys(models);

    // Check if we have both models
    if (modelNames.length < 2) return;

    const lr = models['Linear Regression'];
    const rf = models['Random Forest'];

    const html = `
        <div class="table-responsive">
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th style="text-align: left;">Metric</th>
                        <th>Linear Regression</th>
                        <th>Random Forest</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="section-row"><td colspan="3">Training Set Performance</td></tr>
                    <tr>
                        <td class="metric-name">RMSE</td>
                        <td>${lr.train_metrics.RMSE.toFixed(4)}</td>
                        <td>${rf.train_metrics.RMSE.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td class="metric-name">MAE</td>
                        <td>${lr.train_metrics.MAE.toFixed(4)}</td>
                        <td>${rf.train_metrics.MAE.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td class="metric-name">R²</td>
                        <td>${lr.train_metrics.R2.toFixed(4)}</td>
                        <td>${rf.train_metrics.R2.toFixed(4)}</td>
                    </tr>
                    <tr class="section-row"><td colspan="3">Test Set Performance (Verification)</td></tr>
                    <tr>
                        <td class="metric-name">RMSE</td>
                        <td class="highlight-val">${lr.test_metrics.RMSE.toFixed(4)}</td>
                        <td class="highlight-val">${rf.test_metrics.RMSE.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td class="metric-name">MAE</td>
                        <td>${lr.test_metrics.MAE.toFixed(4)}</td>
                        <td>${rf.test_metrics.MAE.toFixed(4)}</td>
                    </tr>
                    <tr>
                        <td class="metric-name">R²</td>
                        <td>${lr.test_metrics.R2.toFixed(4)}</td>
                        <td>${rf.test_metrics.R2.toFixed(4)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div class="metrics-explanation">
            <p><strong>RMSE/MAE</strong>: Lower is better. <strong>R²</strong>: Higher is better (max 1.0).</p>
        </div>
    `;

    document.getElementById('modelMetrics').innerHTML = html;
}

function displayForecastChart(modelName) {
    if (!forecastResults) return;

    const model = forecastResults.models[modelName];
    if (!model) return;

    const predictions = model.predictions;
    // Use first 50 points for clarity
    const displayCount = Math.min(predictions.y_test.length, 50);
    const indices = Array.from({ length: displayCount }, (_, i) => i + 1);
    const y_test = predictions.y_test.slice(0, displayCount);
    const y_pred = predictions.y_pred.slice(0, displayCount);

    const actualTrace = {
        x: indices,
        y: y_test,
        name: 'Actual Sales',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#3b82f6', width: 2 },
        marker: { size: 6 }
    };

    const predictedTrace = {
        x: indices,
        y: y_pred,
        name: 'Predicted Sales',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#10b981', width: 2, dash: 'dot' },
        marker: { size: 6, symbol: 'x' }
    };

    const isMobile = window.innerWidth < 768;

    const layout = {
        title: {
            text: `Forecast: Actual vs Predicted (First ${displayCount} Samples)`,
            font: { size: isMobile ? 14 : 16 },
            x: 0,
            xanchor: 'left',
            y: 0.98
        },
        autosize: true,
        height: 450,
        margin: isMobile ? { t: 80, r: 20, b: 60, l: 40 } : { t: 80, r: 40, b: 60, l: 60 },
        legend: {
            orientation: 'h',
            y: 1.15,
            x: 0,
            xanchor: 'left',
            bgcolor: 'rgba(255,255,255,0.9)'
        },
        xaxis: {
            title: 'Sample Index',
            automargin: true,
            gridcolor: '#e5e7eb'
        },
        yaxis: {
            title: 'Sales Volume',
            automargin: true,
            gridcolor: '#e5e7eb'
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff'
    };

    const config = { responsive: true, displayModeBar: false };
    Plotly.newPlot('forecastChart', [actualTrace, predictedTrace], layout, config);
}

function displayFitChart(modelName) {
    if (!forecastResults) return;

    const model = forecastResults.models[modelName];
    if (!model) return;

    const predictions = model.predictions;

    const trace = {
        x: predictions.y_test,
        y: predictions.y_pred,
        mode: 'markers',
        type: 'scatter',
        marker: {
            color: '#6366f1',
            size: 8,
            opacity: 0.6
        },
        name: 'Prediction'
    };

    // Ideal line (y=x)
    const maxVal = Math.max(...predictions.y_test, ...predictions.y_pred);
    const minVal = Math.min(...predictions.y_test, ...predictions.y_pred);

    const lineTrace = {
        x: [minVal, maxVal],
        y: [minVal, maxVal],
        mode: 'lines',
        type: 'scatter',
        line: { color: '#ef4444', width: 2, dash: 'dash' },
        name: 'Perfect Fit'
    };

    const isMobile = window.innerWidth < 768;

    const layout = {
        title: {
            text: 'Model Fit: Prediction Accuracy',
            font: { size: isMobile ? 14 : 16 },
            x: 0,
            xanchor: 'left',
            y: 0.98
        },
        autosize: true,
        height: 450,
        margin: isMobile ? { t: 80, r: 20, b: 60, l: 40 } : { t: 80, r: 40, b: 60, l: 60 },
        xaxis: {
            title: 'Actual Sales',
            automargin: true,
            gridcolor: '#e5e7eb'
        },
        yaxis: {
            title: 'Predicted Sales',
            scaleanchor: "x",
            scaleratio: 1,
            automargin: true,
            gridcolor: '#e5e7eb'
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: 1.15,
            x: 0,
            xanchor: 'left',
            bgcolor: 'rgba(255,255,255,0.9)'
        },
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff'
    };

    const config = { responsive: true, displayModeBar: false };
    Plotly.newPlot('fitChart', [trace, lineTrace], layout, config);
}

// Handle window resize for chart responsiveness
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        if (forecastResults && document.getElementById('resultsState').style.display !== 'none') {
            displayForecastChart(currentModel);
            displayFitChart(currentModel);
        }
    }, 250);
});

// Model tab switching
document.querySelectorAll('.model-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.model-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentModel = tab.dataset.model;
        // Comparison table is static, no need to update
        displayForecastChart(currentModel);
        displayFitChart(currentModel);
    });
});

// Export functionality
document.getElementById('exportBtn').addEventListener('click', () => {
    if (!forecastResults) return;

    // Create comprehensive results report
    const report = {
        dataset_stats: forecastResults.stats,
        preprocessing: forecastResults.preprocessing,
        models: {}
    };

    // Add model results
    for (const [modelName, modelData] of Object.entries(forecastResults.models)) {
        report.models[modelName] = {
            train_metrics: modelData.train_metrics,
            test_metrics: modelData.test_metrics
        };
    }

    // Convert to JSON and download
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `demand_forecast_results_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
});
