/**
 * Supplier Risk Assessment Tool - JavaScript
 * Handles 4 analysis types: Forecasting, Anomaly, Routing, Fraud
 */

// Global state
let currentResults = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function () {
    initializeForm();
    initializeSliders();
    initializeTabs();
    initializeRadioButtons();
});

/**
 * Initialize form submission
 */
function initializeForm() {
    const form = document.getElementById('riskAnalysisForm');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        await runAnalysis();
    });
}

/**
 * Initialize slider value displays
 */
function initializeSliders() {
    const sliders = [
        { id: 'contamination', valueId: 'contaminationValue' },
        { id: 'epochs', valueId: 'epochsValue' }
    ];

    sliders.forEach(slider => {
        const input = document.getElementById(slider.id);
        const display = document.getElementById(slider.valueId);

        if (input && display) {
            input.addEventListener('input', function () {
                display.textContent = this.value;
            });
        }
    });

    // Advanced options toggle
    const showAdvanced = document.getElementById('showAdvanced');
    const advancedOptions = document.getElementById('advancedOptions');

    if (showAdvanced && advancedOptions) {
        showAdvanced.addEventListener('change', function () {
            advancedOptions.style.display = this.checked ? 'block' : 'none';
        });
    }
}

/**
 * Initialize tab switching
 */
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(button => {
        button.addEventListener('click', function () {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

/**
 * Initialize radio buttons for data source
 */
function initializeRadioButtons() {
    const radios = document.querySelectorAll('input[name="use_sample_data"]');
    const fileSection = document.getElementById('fileUploadSection');

    radios.forEach(radio => {
        radio.addEventListener('change', function () {
            if (fileSection) {
                fileSection.style.display = this.value === 'false' ? 'block' : 'none';
            }
        });
    });
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update button states
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    // Update content visibility
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
}

/**
 * Show specific state
 */
function showState(state) {
    const states = ['loading', 'error', 'results', 'initial'];
    states.forEach(s => {
        const element = document.getElementById(s + 'State');
        if (element) {
            element.style.display = s === state ? 'block' : 'none';
        }
    });

    // Show/hide charts section
    const chartsSection = document.getElementById('resultsCharts');
    if (chartsSection) {
        chartsSection.style.display = state === 'results' ? 'block' : 'none';
    }
}

/**
 * Run comprehensive risk analysis
 */
async function runAnalysis() {
    const form = document.getElementById('riskAnalysisForm');
    const formData = new FormData(form);

    // Show loading state
    showState('loading');

    try {
        const response = await fetch('/demos/api/supplier-risk-analysis', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        currentResults = data;
        displayResults(data);
        showState('results');

    } catch (error) {
        console.error('Analysis error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        showState('error');
    }
}

/**
 * Display all results
 */
function displayResults(data) {
    // Display summary in right panel
    displaySummary(data);

    // Display detailed charts in full-width section
    if (data.forecasting) {
        displayForecastingTab(data.forecasting);
    }
    if (data.anomaly) {
        displayAnomalyTab(data.anomaly);
    }
    if (data.routing) {
        displayRoutingTab(data.routing);
    }
    if (data.fraud) {
        displayFraudTab(data.fraud);
    }
}

/**
 * Display summary content in right panel
 */
function displaySummary(data) {
    const container = document.getElementById('summaryContent');

    let html = '<div class="summary-sections">';

    // Forecasting summary
    if (data.forecasting) {
        const bestModel = data.forecasting.best_model;
        const bestMetrics = data.forecasting.models[bestModel];

        html += `
            <div class="summary-section">
                <h3><i class="fas fa-chart-line"></i> Risk Forecasting</h3>
                <div class="summary-metrics">
                    <div class="summary-metric">
                        <div class="summary-label">Best Model</div>
                        <div class="summary-value-text">${bestModel}</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">MAE</div>
                        <div class="summary-value">${bestMetrics.mae.toFixed(2)}</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">R²</div>
                        <div class="summary-value">${bestMetrics.r2.toFixed(3)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    // Anomaly summary
    if (data.anomaly) {
        const metrics = data.anomaly.metrics;
        html += `
            <div class="summary-section">
                <h3><i class="fas fa-exclamation-triangle"></i> Anomaly Detection</h3>
                <div class="summary-metrics">
                    <div class="summary-metric warning">
                        <div class="summary-label">Anomalies Found</div>
                        <div class="summary-value">${metrics.detected_anomalies}</div>
                    </div>
                    ${metrics.accuracy ? `
                        <div class="summary-metric success">
                            <div class="summary-label">Accuracy</div>
                            <div class="summary-value">${(metrics.accuracy * 100).toFixed(1)}%</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Routing summary
    if (data.routing) {
        html += `
            <div class="summary-section">
                <h3><i class="fas fa-route"></i> Route Optimization</h3>
                <div class="summary-metrics">
                    <div class="summary-metric">
                        <div class="summary-label">Best Route</div>
                        <div class="summary-value-text">${data.routing.recommended_route}</div>
                    </div>
                    <div class="summary-metric success">
                        <div class="summary-label">Improvement</div>
                        <div class="summary-value">${data.routing.improvement_percentage.toFixed(1)}%</div>
                    </div>
                </div>
            </div>
        `;
    }

    // Fraud summary
    if (data.fraud) {
        const metrics = data.fraud.metrics;
        html += `
            <div class="summary-section">
                <h3><i class="fas fa-user-shield"></i> Fraud Detection</h3>
                <div class="summary-metrics">
                    <div class="summary-metric ${metrics.accuracy > 0.95 ? 'success' : ''}">
                        <div class="summary-label">Accuracy</div>
                        <div class="summary-value">${(metrics.accuracy * 100).toFixed(2)}%</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">AUC</div>
                        <div class="summary-value">${metrics.auc.toFixed(3)}</div>
                    </div>
                    <div class="summary-metric warning">
                        <div class="summary-label">Fraud Detected</div>
                        <div class="summary-value">${metrics.fraud_detected}</div>
                    </div>
                </div>
            </div>
        `;
    }

    html += `
        <div class="info-box">
            <p><strong>Tip:</strong> Scroll down to view detailed visualizations for each analysis component.</p>
        </div>
    </div>`;

    container.innerHTML = html;
}

/**
 * Display Forecasting Tab
 */
function displayForecastingTab(forecasting) {
    const container = document.getElementById('forecastingTab');

    let html = `
        <div class="tab-section">
            <h3>Model Comparison</h3>
            <div id="modelComparisonChart"></div>
        </div>
        
        <div class="tab-section">
            <h3>Best Model: ${forecasting.best_model}</h3>
            <div id="predictionScatterChart"></div>
        </div>
        
        <div class="tab-section">
            <h3>Feature Importance (${forecasting.best_model})</h3>
            <div id="featureImportanceChart"></div>
        </div>
    `;

    container.innerHTML = html;

    // Render charts
    renderModelComparison(forecasting.models);
    renderPredictionScatter(forecasting);
    renderFeatureImportance(forecasting);
}

/**
 * Render model comparison chart
 */
function renderModelComparison(models) {
    const modelNames = Object.keys(models);
    const mae = modelNames.map(name => models[name].mae);
    const r2 = modelNames.map(name => models[name].r2);

    const trace1 = {
        x: modelNames,
        y: mae,
        name: 'MAE',
        type: 'bar',
        marker: { color: '#ef4444' },
        offsetgroup: 1
    };

    const trace2 = {
        x: modelNames,
        y: r2,
        name: 'R²',
        type: 'bar',
        yaxis: 'y2',
        marker: { color: '#10b981' },
        offsetgroup: 2
    };

    const layout = {
        title: 'Model Performance Comparison',
        xaxis: { title: 'Model' },
        yaxis: { title: 'MAE (lower is better)', side: 'left' },
        yaxis2: {
            title: 'R² (higher is better)',
            overlaying: 'y',
            side: 'right',
            range: [0, 1]
        },
        barmode: 'group',
        margin: { t: 40, r: 60, b: 60, l: 60 },
        legend: { orientation: 'h', y: -0.2 }
    };

    Plotly.newPlot('modelComparisonChart', [trace1, trace2], layout, { responsive: true });
}

/**
 * Render prediction vs actual scatter plot
 */
function renderPredictionScatter(forecasting) {
    const bestModel = forecasting.best_model;
    const predictions = forecasting.models[bestModel].predictions;
    const actual = forecasting.test_actual;

    const trace = {
        x: actual,
        y: predictions,
        mode: 'markers',
        type: 'scatter',
        name: 'Predictions',
        marker: { color: '#3b82f6', size: 6, opacity: 0.6 }
    };

    // Perfect prediction line
    const minVal = Math.min(...actual);
    const maxVal = Math.max(...actual);
    const perfectLine = {
        x: [minVal, maxVal],
        y: [minVal, maxVal],
        mode: 'lines',
        name: 'Perfect Prediction',
        line: { color: '#ef4444', dash: 'dash', width: 2 }
    };

    const layout = {
        title: `${bestModel}: Predicted vs Actual`,
        xaxis: { title: 'Actual Demand' },
        yaxis: { title: 'Predicted Demand' },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    };

    Plotly.newPlot('predictionScatterChart', [trace, perfectLine], layout, { responsive: true });
}

/**
 * Render feature importance chart
 */
function renderFeatureImportance(forecasting) {
    const bestModel = forecasting.best_model;
    const featureData = forecasting.models[bestModel].feature_importance;

    if (!featureData) {
        document.getElementById('featureImportanceChart').innerHTML =
            '<p class="info-box">Feature importance not available for MLP model</p>';
        return;
    }

    // Sort by importance
    const sorted = featureData.features.map((f, i) => ({
        feature: f,
        importance: featureData.importances[i]
    })).sort((a, b) => b.importance - a.importance);

    const trace = {
        x: sorted.map(d => d.importance),
        y: sorted.map(d => d.feature),
        type: 'bar',
        orientation: 'h',
        marker: { color: '#8b5cf6' }
    };

    const layout = {
        title: 'Feature Importance',
        xaxis: { title: 'Importance Score' },
        margin: { t: 40, r: 20, b: 40, l: 150 }
    };

    Plotly.newPlot('featureImportanceChart', [trace], layout, { responsive: true });
}

/**
 * Display Anomaly Detection Tab
 */
function displayAnomalyTab(anomaly) {
    const container = document.getElementById('anomalyTab');

    let html = `
        <div class="tab-section">
            <h3>Anomaly Detection Results</h3>
            <div class="metrics-grid">
                <div class="metric-card warning">
                    <div class="metric-label">Anomalies Detected</div>
                    <div class="metric-value">${anomaly.metrics.detected_anomalies}</div>
                </div>
    `;

    if (anomaly.metrics.accuracy) {
        html += `
                <div class="metric-card success">
                    <div class="metric-label">Accuracy</div>
                    <div class="metric-value">${(anomaly.metrics.accuracy * 100).toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Precision</div>
                    <div class="metric-value">${(anomaly.metrics.precision * 100).toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Recall</div>
                    <div class="metric-value">${(anomaly.metrics.recall * 100).toFixed(1)}%</div>
                </div>
        `;
    }

    html += `
            </div>
        </div>
        
        <div class="tab-section">
            <h3>Anomaly Score Distribution</h3>
            <div id="anomalyScoreChart"></div>
        </div>
        
        <div class="tab-section">
            <h3>Feature Contribution to Anomalies</h3>
            <div id="anomalyFeatureChart"></div>
        </div>
    `;

    container.innerHTML = html;

    // Render charts
    renderAnomalyScores(anomaly);
    renderAnomalyFeatures(anomaly.feature_importance);
}

/**
 * Render anomaly score distribution
 */
function renderAnomalyScores(anomaly) {
    const scores = anomaly.anomaly_scores;
    const labels = anomaly.anomaly_labels;

    const normalScores = scores.filter((s, i) => labels[i] === 0);
    const anomalyScores = scores.filter((s, i) => labels[i] === 1);

    const trace1 = {
        x: normalScores,
        type: 'histogram',
        name: 'Normal',
        marker: { color: '#10b981' },
        opacity: 0.7
    };

    const trace2 = {
        x: anomalyScores,
        type: 'histogram',
        name: 'Anomaly',
        marker: { color: '#ef4444' },
        opacity: 0.7
    };

    const layout = {
        title: 'Anomaly Score Distribution',
        xaxis: { title: 'Anomaly Score' },
        yaxis: { title: 'Count' },
        barmode: 'overlay',
        margin: { t: 40, r: 20, b: 60, l: 60 }
    };

    Plotly.newPlot('anomalyScoreChart', [trace1, trace2], layout, { responsive: true });
}

/**
 * Render anomaly feature contribution
 */
function renderAnomalyFeatures(featureImportance) {
    const trace = {
        x: featureImportance.importances,
        y: featureImportance.features,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#f59e0b' }
    };

    const layout = {
        title: 'Feature Contribution to Anomalies',
        xaxis: { title: 'Importance' },
        margin: { t: 40, r: 20, b: 40, l: 150 }
    };

    Plotly.newPlot('anomalyFeatureChart', [trace], layout, { responsive: true });
}

/**
 * Display Routing Tab
 */
function displayRoutingTab(routing) {
    const container = document.getElementById('routingTab');

    let html = `
        <div class="tab-section">
            <h3>Route Recommendations</h3>
            <div class="info-box">
                <p><strong>Recommended Route:</strong> ${routing.recommended_route}</p>
                <p><strong>Improvement vs Worst Route:</strong> ${routing.improvement_percentage.toFixed(1)}%</p>
            </div>
        </div>
        
        <div class="tab-section">
            <h3>Route Comparison</h3>
            <div class="route-table-container">
                <table class="route-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Route</th>
                            <th>Distance (km)</th>
                            <th>Fuel Cost ($)</th>
                            <th>Time (hrs)</th>
                            <th>Risk Score</th>
                            <th>Overall Score</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    routing.routes.forEach(route => {
        const rowClass = route.rank === 1 ? 'best-route' : '';
        html += `
                        <tr class="${rowClass}">
                            <td>${route.rank}</td>
                            <td><strong>${route.name}</strong></td>
                            <td>${route.distance_km.toFixed(0)}</td>
                            <td>$${route.total_fuel_cost.toFixed(2)}</td>
                            <td>${route.total_time_hours.toFixed(1)}</td>
                            <td>${route.risk_score.toFixed(3)}</td>
                            <td>${route.overall_score.toFixed(3)}</td>
                        </tr>
        `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="tab-section">
            <h3>Risk Score Comparison</h3>
            <div id="routeRiskChart"></div>
        </div>
    `;

    container.innerHTML = html;

    // Render chart
    renderRouteRiskChart(routing.routes);
}

/**
 * Render route risk comparison chart
 */
function renderRouteRiskChart(routes) {
    const trace = {
        x: routes.map(r => r.name),
        y: routes.map(r => r.risk_score),
        type: 'bar',
        marker: {
            color: routes.map(r => r.rank === 1 ? '#10b981' : '#f59e0b')
        }
    };

    const layout = {
        title: 'Route Risk Scores (Lower is Better)',
        xaxis: { title: 'Route' },
        yaxis: { title: 'Risk Score' },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    };

    Plotly.newPlot('routeRiskChart', [trace], layout, { responsive: true });
}

/**
 * Display Fraud Detection Tab
 */
function displayFraudTab(fraud) {
    const container = document.getElementById('fraudTab');

    const metrics = fraud.metrics;
    const cm = fraud.confusion_matrix;

    let html = `
        <div class="tab-section">
            <h3>Fraud Detection Performance</h3>
            <div class="metrics-grid">
                <div class="metric-card ${metrics.accuracy > 0.95 ? 'success' : ''}">
                    <div class="metric-label">Accuracy</div>
                    <div class="metric-value">${(metrics.accuracy * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Precision</div>
                    <div class="metric-value">${(metrics.precision * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Recall</div>
                    <div class="metric-value">${(metrics.recall * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">AUC</div>
                    <div class="metric-value">${metrics.auc.toFixed(4)}</div>
                </div>
            </div>
        </div>
        
        <div class="tab-section">
            <h3>Confusion Matrix</h3>
            <div id="confusionMatrixChart"></div>
        </div>
        
        <div class="tab-section">
            <h3>ROC Curve</h3>
            <div id="rocCurveChart"></div>
        </div>
        
        <div class="tab-section">
            <h3>Training History</h3>
            <div id="trainingHistoryChart"></div>
        </div>
    `;

    container.innerHTML = html;

    // Render charts
    renderConfusionMatrix(cm);
    renderROCCurve(fraud.predictions);
    renderTrainingHistory(fraud.training_history);
}

/**
 * Render confusion matrix
 */
function renderConfusionMatrix(cm) {
    const z = [
        [cm.tn, cm.fp],
        [cm.fn, cm.tp]
    ];

    const trace = {
        z: z,
        x: ['Predicted Legitimate', 'Predicted Fraud'],
        y: ['Actual Legitimate', 'Actual Fraud'],
        type: 'heatmap',
        colorscale: 'Blues',
        showscale: true,
        text: z,
        texttemplate: '%{text}',
        textfont: { size: 16 }
    };

    const layout = {
        title: 'Confusion Matrix',
        xaxis: { title: 'Predicted' },
        yaxis: { title: 'Actual' },
        margin: { t: 60, r: 20, b: 80, l: 100 }
    };

    Plotly.newPlot('confusionMatrixChart', [trace], layout, { responsive: true });
}

/**
 * Render ROC curve
 */
function renderROCCurve(predictions) {
    // Calculate ROC curve points
    const sorted = predictions.y_true.map((y, i) => ({
        true: y,
        prob: predictions.y_pred_proba[i]
    })).sort((a, b) => b.prob - a.prob);

    const tpr = [0];
    const fpr = [0];
    let tp = 0, fp = 0;
    const totalPositive = sorted.filter(d => d.true === 1).length;
    const totalNegative = sorted.length - totalPositive;

    sorted.forEach(d => {
        if (d.true === 1) tp++;
        else fp++;
        tpr.push(tp / totalPositive);
        fpr.push(fp / totalNegative);
    });

    const trace = {
        x: fpr,
        y: tpr,
        type: 'scatter',
        mode: 'lines',
        name: 'ROC Curve',
        line: { color: '#3b82f6', width: 2 }
    };

    const diagonalTrace = {
        x: [0, 1],
        y: [0, 1],
        type: 'scatter',
        mode: 'lines',
        name: 'Random',
        line: { color: '#ef4444', dash: 'dash', width: 1 }
    };

    const layout = {
        title: 'ROC Curve',
        xaxis: { title: 'False Positive Rate', range: [0, 1] },
        yaxis: { title: 'True Positive Rate', range: [0, 1] },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    };

    Plotly.newPlot('rocCurveChart', [trace, diagonalTrace], layout, { responsive: true });
}

/**
 * Render training history
 */
function renderTrainingHistory(history) {
    const epochs = history.loss.map((_, i) => i + 1);

    const lossTrace = {
        x: epochs,
        y: history.loss,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Training Loss',
        line: { color: '#ef4444' }
    };

    const valLossTrace = {
        x: epochs,
        y: history.val_loss,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Validation Loss',
        line: { color: '#f59e0b' }
    };

    const accTrace = {
        x: epochs,
        y: history.accuracy,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Training Accuracy',
        yaxis: 'y2',
        line: { color: '#10b981' }
    };

    const valAccTrace = {
        x: epochs,
        y: history.val_accuracy,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Validation Accuracy',
        yaxis: 'y2',
        line: { color: '#3b82f6' }
    };

    const layout = {
        title: 'Training History',
        xaxis: { title: 'Epoch' },
        yaxis: { title: 'Loss', side: 'left' },
        yaxis2: {
            title: 'Accuracy',
            overlaying: 'y',
            side: 'right',
            range: [0, 1]
        },
        margin: { t: 40, r: 60, b: 60, l: 60 }
    };

    Plotly.newPlot('trainingHistoryChart', [lossTrace, valLossTrace, accTrace, valAccTrace], layout, { responsive: true });
}
