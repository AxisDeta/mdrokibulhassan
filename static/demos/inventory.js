/**
 * AI Inventory Optimization Tool - JavaScript
 * Handles form submission, API calls, and result visualization
 */

// Global state
let currentResults = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function () {
    initializeSliders();
    initializeForm();
    initializeTabs();
});

/**
 * Initialize slider value displays
 */
function initializeSliders() {
    const sliders = [
        { id: 'forecastDays', valueId: 'forecastDaysValue' },
        { id: 'leadTime', valueId: 'leadTimeValue' },
        { id: 'serviceLevel', valueId: 'serviceLevelValue' },
        { id: 'simDays', valueId: 'simDaysValue' }
    ];

    sliders.forEach(slider => {
        const input = document.getElementById(slider.id);
        const display = document.getElementById(slider.valueId);

        input.addEventListener('input', function () {
            display.textContent = this.value;
        });
    });
}

/**
 * Initialize form submission
 */
function initializeForm() {
    const form = document.getElementById('inventoryForm');

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        await runAnalysis();
    });
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
 * Run comprehensive inventory analysis
 */
async function runAnalysis() {
    const form = document.getElementById('inventoryForm');
    const formData = new FormData(form);

    // Show loading state
    showState('loading');

    try {
        const response = await fetch('/demos/api/inventory-analysis', {
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
    displayHistoricalTab(data.historical);
    displayForecastingTab(data.ets_forecast, data.lgb_forecast);
    displayPolicyTab(data.policy);
    displaySimulationTab(data.simulation);
    displayExplainabilityTab(data.explainability);
}

/**
 * Display summary content in right panel
 */
function displaySummary(data) {
    const container = document.getElementById('summaryContent');

    const policy = data.policy.parameters;
    const lgb = data.lgb_forecast;
    const sim = data.simulation.metrics;

    let html = `
        <div class="summary-section">
            <h3><i class="fas fa-boxes"></i> Inventory Policy</h3>
            <div class="summary-metrics">
                <div class="summary-metric">
                    <div class="summary-label">Reorder Point (s)</div>
                    <div class="summary-value">${policy.s}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Order-up-to (S)</div>
                    <div class="summary-value">${policy.S}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Safety Stock</div>
                    <div class="summary-value">${policy.safety_stock}</div>
                </div>
            </div>
        </div>
    `;

    if (lgb.success) {
        html += `
            <div class="summary-section">
                <h3><i class="fas fa-chart-line"></i> Forecast Accuracy</h3>
                <div class="summary-metrics">
                    <div class="summary-metric">
                        <div class="summary-label">MAPE</div>
                        <div class="summary-value">${lgb.metrics.mape.toFixed(2)}%</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">Next Day</div>
                        <div class="summary-value">${lgb.metrics.next_day_forecast.toFixed(0)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    html += `
        <div class="summary-section">
            <h3><i class="fas fa-play-circle"></i> Simulation Results</h3>
            <div class="summary-metrics">
                <div class="summary-metric ${sim.service_level_achieved >= 90 ? 'success' : 'warning'}">
                    <div class="summary-label">Service Level</div>
                    <div class="summary-value">${sim.service_level_achieved.toFixed(1)}%</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Total Orders</div>
                    <div class="summary-value">${sim.total_orders}</div>
                </div>
                <div class="summary-metric ${sim.total_stockouts === 0 ? 'success' : 'warning'}">
                    <div class="summary-label">Stockouts</div>
                    <div class="summary-value">${sim.total_stockouts}</div>
                </div>
            </div>
        </div>
        
        <div class="info-box">
            <p><strong>Tip:</strong> Scroll down to view detailed visualizations for each analysis component.</p>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * Display Historical Analysis Tab
 */
function displayHistoricalTab(historical) {
    const container = document.getElementById('historicalTab');

    const html = `
        <div class="tab-section">
            <h3>Demand Statistics</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Mean Demand</div>
                    <div class="metric-value">${historical.stats.mean.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Median Demand</div>
                    <div class="metric-value">${historical.stats.median.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Std Deviation</div>
                    <div class="metric-value">${historical.stats.std.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Min / Max</div>
                    <div class="metric-value">${historical.stats.min.toFixed(0)} / ${historical.stats.max.toFixed(0)}</div>
                </div>
            </div>
        </div>

        <div class="tab-section">
            <h3>Demand Distribution</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">25th Percentile</div>
                    <div class="metric-value">${historical.quantiles.q25.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">75th Percentile</div>
                    <div class="metric-value">${historical.quantiles.q75.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">90th Percentile</div>
                    <div class="metric-value">${historical.quantiles.q90.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">95th Percentile</div>
                    <div class="metric-value">${historical.quantiles.q95.toFixed(2)}</div>
                </div>
            </div>
        </div>

        <div class="tab-section">
            <h3>Historical Demand Pattern</h3>
            <div id="historicalChart"></div>
        </div>

        <div class="tab-section">
            <div class="info-box">
                <strong>Data Range:</strong> ${historical.date_range.start} to ${historical.date_range.end} 
                (${historical.total_days} days)
            </div>
        </div>
    `;

    container.innerHTML = html;

    // Render chart
    renderHistoricalChart(historical.time_series);
}

/**
 * Render historical demand chart
 */
function renderHistoricalChart(timeSeries) {
    const trace = {
        x: timeSeries.dates,
        y: timeSeries.demand,
        type: 'scatter',
        mode: 'lines',
        name: 'Demand',
        line: { color: '#3b82f6', width: 2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(59, 130, 246, 0.1)'
    };

    const layout = {
        title: 'Historical Demand Over Time',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        showlegend: false,
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot('historicalChart', [trace], layout, { responsive: true });
}

/**
 * Display Forecasting Tab
 */
function displayForecastingTab(ets, lgb) {
    const container = document.getElementById('forecastingTab');

    let html = '<div class="tab-section"><h3>Forecast Comparison</h3>';

    // ETS Results
    if (ets.success) {
        html += `
            <div class="forecast-model-section">
                <h4><i class="fas fa-chart-line"></i> ETS (Exponential Smoothing)</h4>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">MAE</div>
                        <div class="metric-value">${ets.metrics.mae.toFixed(2)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">RMSE</div>
                        <div class="metric-value">${ets.metrics.rmse.toFixed(2)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">MAPE</div>
                        <div class="metric-value">${ets.metrics.mape.toFixed(2)}%</div>
                    </div>
                </div>
                <div id="etsChart"></div>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-warning">
                <strong>ETS Model:</strong> ${ets.message || ets.error}
            </div>
        `;
    }

    // LightGBM Results
    if (lgb.success) {
        html += `
            <div class="forecast-model-section">
                <h4><i class="fas fa-brain"></i> LightGBM (Machine Learning)</h4>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">MAE</div>
                        <div class="metric-value">${lgb.metrics.mae.toFixed(2)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">RMSE</div>
                        <div class="metric-value">${lgb.metrics.rmse.toFixed(2)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">MAPE</div>
                        <div class="metric-value">${lgb.metrics.mape.toFixed(2)}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Next Day Forecast</div>
                        <div class="metric-value">${lgb.metrics.next_day_forecast.toFixed(2)}</div>
                    </div>
                </div>
                <div id="lgbChart"></div>
                <div id="featureImportanceChart"></div>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-warning">
                <strong>LightGBM Model:</strong> ${lgb.message || lgb.error}
            </div>
        `;
    }

    html += '</div>';
    container.innerHTML = html;

    // Render charts
    if (ets.success) {
        renderForecastChart('etsChart', ets.visualization, 'ETS Forecast');
    }
    if (lgb.success) {
        renderLGBChart(lgb.visualization);
        renderFeatureImportance(lgb.feature_importance);
    }
}

/**
 * Render forecast chart
 */
function renderForecastChart(elementId, viz, title) {
    const trainTrace = {
        x: viz.train_dates,
        y: viz.train_values,
        type: 'scatter',
        mode: 'lines',
        name: 'Training Data',
        line: { color: '#6b7280', width: 1 }
    };

    const actualTrace = {
        x: viz.test_dates,
        y: viz.test_actual,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual',
        line: { color: '#3b82f6', width: 2 },
        marker: { size: 4 }
    };

    const forecastTrace = {
        x: viz.test_dates,
        y: viz.test_forecast,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Forecast',
        line: { color: '#10b981', width: 2, dash: 'dash' },
        marker: { size: 4 }
    };

    const layout = {
        title: title,
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot(elementId, [trainTrace, actualTrace, forecastTrace], layout, { responsive: true });
}

/**
 * Render LightGBM chart
 */
function renderLGBChart(viz) {
    const actualTrace = {
        x: viz.test_indices,
        y: viz.test_actual,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Actual',
        line: { color: '#3b82f6', width: 2 },
        marker: { size: 4 }
    };

    const forecastTrace = {
        x: viz.test_indices,
        y: viz.test_forecast,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Forecast',
        line: { color: '#10b981', width: 2, dash: 'dash' },
        marker: { size: 4 }
    };

    const layout = {
        title: 'LightGBM Forecast vs Actual',
        xaxis: { title: 'Test Period Index' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot('lgbChart', [actualTrace, forecastTrace], layout, { responsive: true });
}

/**
 * Render feature importance chart
 */
function renderFeatureImportance(featureImportance) {
    const trace = {
        x: featureImportance.importances,
        y: featureImportance.features,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#8b5cf6' }
    };

    const layout = {
        title: 'Feature Importance',
        xaxis: { title: 'Importance Score' },
        yaxis: { title: 'Feature' },
        margin: { t: 40, r: 20, b: 40, l: 100 }
    };

    Plotly.newPlot('featureImportanceChart', [trace], layout, { responsive: true });
}

/**
 * Display Policy Tab
 */
function displayPolicyTab(policy) {
    const container = document.getElementById('policyTab');
    const params = policy.parameters;
    const inputs = policy.inputs;

    const html = `
        <div class="tab-section">
            <h3>Inventory Policy Parameters</h3>
            <div class="policy-params-grid">
                <div class="policy-card highlight">
                    <div class="policy-label">Reorder Point (s)</div>
                    <div class="policy-value">${params.s}</div>
                    <div class="policy-description">Order when inventory drops to this level</div>
                </div>
                <div class="policy-card highlight">
                    <div class="policy-label">Order-up-to Level (S)</div>
                    <div class="policy-value">${params.S}</div>
                    <div class="policy-description">Target inventory level after ordering</div>
                </div>
                <div class="policy-card">
                    <div class="policy-label">Safety Stock</div>
                    <div class="policy-value">${params.safety_stock}</div>
                    <div class="policy-description">Buffer to prevent stockouts</div>
                </div>
                <div class="policy-card">
                    <div class="policy-label">Avg Order Quantity</div>
                    <div class="policy-value">${params.avg_order_quantity}</div>
                    <div class="policy-description">Typical order size (S - s)</div>
                </div>
            </div>
        </div>

        <div class="tab-section">
            <h3>Policy Visualization</h3>
            <div id="policyChart"></div>
        </div>

        <div class="tab-section">
            <h3>Configuration Summary</h3>
            <div class="info-box">
                <ul>
                    <li><strong>Lead Time:</strong> ${inputs.lead_time} days</li>
                    <li><strong>Service Level:</strong> ${(inputs.service_level * 100).toFixed(0)}%</li>
                    <li><strong>Expected Lead Time Demand:</strong> ${params.expected_lead_time_demand} units</li>
                    <li><strong>Average Daily Demand:</strong> ${inputs.mu.toFixed(2)} units</li>
                    <li><strong>Demand Std Deviation:</strong> ${inputs.sigma.toFixed(2)} units</li>
                </ul>
            </div>
        </div>
    `;

    container.innerHTML = html;
    renderPolicyChart(policy.visualization, params.s, params.S, inputs.mu);
}

/**
 * Render policy visualization chart
 */
function renderPolicyChart(viz, s, S, mu) {
    const inventoryTrace = {
        x: viz.days,
        y: viz.inventory_levels,
        type: 'scatter',
        mode: 'lines',
        name: 'Inventory Level',
        line: { color: '#3b82f6', width: 2 }
    };

    const sLine = {
        x: [0, viz.days.length - 1],
        y: [s, s],
        type: 'scatter',
        mode: 'lines',
        name: 'Reorder Point (s)',
        line: { color: '#f59e0b', width: 2, dash: 'dash' }
    };

    const SLine = {
        x: [0, viz.days.length - 1],
        y: [S, S],
        type: 'scatter',
        mode: 'lines',
        name: 'Order-up-to (S)',
        line: { color: '#10b981', width: 2, dash: 'dash' }
    };

    const muLine = {
        x: [0, viz.days.length - 1],
        y: [mu, mu],
        type: 'scatter',
        mode: 'lines',
        name: 'Avg Demand',
        line: { color: '#6b7280', width: 1, dash: 'dot' }
    };

    const layout = {
        title: '(s,S) Policy Simulation',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Inventory Level' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot('policyChart', [inventoryTrace, sLine, SLine, muLine], layout, { responsive: true });
}

/**
 * Display Simulation Tab
 */
function displaySimulationTab(simulation) {
    const container = document.getElementById('simulationTab');
    const metrics = simulation.metrics;
    const viz = simulation.visualization;

    const html = `
        <div class="tab-section">
            <h3>Simulation Results</h3>
            <div class="metrics-grid">
                <div class="metric-card ${metrics.stockout_rate < 10 ? 'success' : 'warning'}">
                    <div class="metric-label">Stockout Rate</div>
                    <div class="metric-value">${metrics.stockout_rate.toFixed(2)}%</div>
                </div>
                <div class="metric-card ${metrics.service_level_achieved >= 90 ? 'success' : 'warning'}">
                    <div class="metric-label">Service Level Achieved</div>
                    <div class="metric-value">${metrics.service_level_achieved.toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Orders</div>
                    <div class="metric-value">${metrics.total_orders}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Order Size</div>
                    <div class="metric-value">${metrics.avg_order_size.toFixed(2)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Stockouts</div>
                    <div class="metric-value">${metrics.total_stockouts}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Inventory</div>
                    <div class="metric-value">${metrics.avg_inventory_level.toFixed(2)}</div>
                </div>
            </div>
        </div>

        <div class="tab-section">
            <h3>Inventory Level Simulation</h3>
            <div id="simInventoryChart"></div>
        </div>

        <div class="tab-section">
            <h3>Demand Pattern</h3>
            <div id="simDemandChart"></div>
        </div>
    `;

    container.innerHTML = html;
    renderSimulationCharts(viz);
}

/**
 * Render simulation charts
 */
function renderSimulationCharts(viz) {
    // Inventory level chart
    const inventoryTrace = {
        x: viz.days,
        y: viz.inventory_levels,
        type: 'scatter',
        mode: 'lines',
        name: 'Inventory',
        line: { color: '#3b82f6', width: 2 }
    };

    const sLine = {
        x: [0, viz.days.length - 1],
        y: [viz.s, viz.s],
        type: 'scatter',
        mode: 'lines',
        name: 'Reorder Point (s)',
        line: { color: '#f59e0b', width: 2, dash: 'dash' }
    };

    const SLine = {
        x: [0, viz.days.length - 1],
        y: [viz.S, viz.S],
        type: 'scatter',
        mode: 'lines',
        name: 'Order-up-to (S)',
        line: { color: '#10b981', width: 2, dash: 'dash' }
    };

    const muLine = {
        x: [0, viz.days.length - 1],
        y: [viz.mu, viz.mu],
        type: 'scatter',
        mode: 'lines',
        name: 'Avg Demand',
        line: { color: '#6b7280', width: 1, dash: 'dot' }
    };

    // Stockout markers
    const stockoutTrace = {
        x: viz.stockout_days,
        y: viz.stockout_days.map(() => 0),
        type: 'scatter',
        mode: 'markers',
        name: 'Stockouts',
        marker: { color: '#ef4444', size: 10, symbol: 'x' }
    };

    // Order markers
    const orderTrace = {
        x: viz.order_days,
        y: viz.order_levels,
        type: 'scatter',
        mode: 'markers',
        name: 'Orders Placed',
        marker: { color: '#10b981', size: 8, symbol: 'triangle-up' }
    };

    const invLayout = {
        title: 'Inventory Levels Over Time',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Inventory Level' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot('simInventoryChart',
        [inventoryTrace, sLine, SLine, muLine, stockoutTrace, orderTrace],
        invLayout,
        { responsive: true }
    );

    // Demand chart
    const demandTrace = {
        x: viz.days,
        y: viz.demand,
        type: 'bar',
        name: 'Daily Demand',
        marker: { color: '#8b5cf6' }
    };

    const demandLayout = {
        title: 'Daily Demand Pattern',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Demand' },
        margin: { t: 40, r: 20, b: 40, l: 50 }
    };

    Plotly.newPlot('simDemandChart', [demandTrace], demandLayout, { responsive: true });
}

/**
 * Display Explainability Tab
 */
function displayExplainabilityTab(explainability) {
    const container = document.getElementById('explainabilityTab');

    if (!explainability.success) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i>
                ${explainability.message || 'Explainability analysis not available'}
            </div>
        `;
        return;
    }

    const surrogate = explainability.surrogate;

    // Build formula
    let formula = `Predicted Demand ≈ ${surrogate.intercept.toFixed(2)}`;
    surrogate.formula_parts.forEach(part => {
        const sign = part.coefficient >= 0 ? '+' : '';
        formula += ` ${sign} ${part.coefficient.toFixed(3)} × ${part.feature}`;
    });

    const html = `
        <div class="tab-section">
            <h3>SHAP Feature Importance</h3>
            <div id="shapChart"></div>
            <p class="chart-description">
                Shows which features have the most impact on predictions. 
                Higher values indicate greater importance.
            </p>
        </div>

        <div class="tab-section">
            <h3>Surrogate Linear Model</h3>
            <div class="formula-box">
                <code>${formula}</code>
            </div>
            <div class="info-box">
                <strong>R² Score:</strong> ${(surrogate.r2_score * 100).toFixed(2)}% 
                (how well the simple formula approximates the complex ML model)
            </div>
        </div>

        <div class="tab-section">
            <h3>Coefficient Breakdown</h3>
            <div id="coefficientChart"></div>
        </div>
    `;

    container.innerHTML = html;
    renderShapChart(explainability.shap);
    renderCoefficientChart(surrogate);
}

/**
 * Render SHAP importance chart
 */
function renderShapChart(shap) {
    const trace = {
        x: shap.importance,
        y: shap.feature_names,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#ef4444' }
    };

    const layout = {
        title: 'Mean Absolute SHAP Values',
        xaxis: { title: 'Importance' },
        yaxis: { title: 'Feature' },
        margin: { t: 40, r: 20, b: 40, l: 100 }
    };

    Plotly.newPlot('shapChart', [trace], layout, { responsive: true });
}

/**
 * Render coefficient chart
 */
function renderCoefficientChart(surrogate) {
    const features = surrogate.formula_parts.map(p => p.feature);
    const coefficients = surrogate.formula_parts.map(p => p.coefficient);

    const colors = coefficients.map(c => c >= 0 ? '#10b981' : '#ef4444');

    const trace = {
        x: features,
        y: coefficients,
        type: 'bar',
        marker: { color: colors }
    };

    const layout = {
        title: 'Linear Model Coefficients',
        xaxis: { title: 'Feature' },
        yaxis: { title: 'Coefficient' },
        margin: { t: 40, r: 20, b: 60, l: 50 }
    };

    Plotly.newPlot('coefficientChart', [trace], layout, { responsive: true });
}
