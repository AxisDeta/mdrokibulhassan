let currentResults = null;

document.addEventListener('DOMContentLoaded', function () {
    initializeSliders();
    initializeForm();
    initializeTabs();
});

function initializeSliders() {
    const sliders = [
        { id: 'forecastDays', valueId: 'forecastDaysValue' },
        { id: 'leadTime', valueId: 'leadTimeValue' },
        { id: 'serviceLevel', valueId: 'serviceLevelValue' },
        { id: 'simDays', valueId: 'simDaysValue' }
    ];

    sliders.forEach(({ id, valueId }) => {
        const input = document.getElementById(id);
        const display = document.getElementById(valueId);
        if (!input || !display) return;
        input.addEventListener('input', () => {
            display.textContent = input.value;
        });
    });
}

function initializeForm() {
    document.getElementById('inventoryForm').addEventListener('submit', async function (event) {
        event.preventDefault();
        await runAnalysis();
    });
}

function initializeTabs() {
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}Tab`);
    });
}

function showState(state) {
    ['loading', 'error', 'results', 'initial'].forEach(name => {
        const element = document.getElementById(`${name}State`);
        if (element) {
            element.style.display = name === state ? 'block' : 'none';
        }
    });

    const chartsSection = document.getElementById('resultsCharts');
    if (chartsSection) {
        chartsSection.style.display = state === 'results' ? 'block' : 'none';
    }
}

async function runAnalysis() {
    showState('loading');

    try {
        const response = await fetch('/demos/api/inventory-analysis', {
            method: 'POST',
            body: new FormData(document.getElementById('inventoryForm'))
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Inventory analysis failed.');
        }

        currentResults = data;
        displayResults(data);
        showState('results');
    } catch (error) {
        console.error('Inventory analysis error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        showState('error');
    }
}

function formatMetric(value, digits = 0) {
    return Number(value || 0).toLocaleString(undefined, {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    });
}

function buildInventoryFallback(data) {
    const policy = data.policy.parameters;
    const simulation = data.simulation.metrics;
    const averageDemand = data.lgb_forecast.success
        ? data.lgb_forecast.summary.projected_average
        : data.ets_forecast.summary.projected_average;
    const priority = simulation.stockout_rate > 8 || simulation.service_level_achieved < 92 ? 'High' : simulation.stockout_rate > 3 ? 'Medium' : 'Monitor';

    const recommendations = [];
    if (simulation.stockout_rate > 8) {
        recommendations.push('Raise safety stock or reorder earlier because the current policy is still exposing the business to stockouts.');
    } else {
        recommendations.push('The current replenishment policy is broadly stable, so focus on execution discipline and supplier follow-up.');
    }
    recommendations.push(`Use a reorder trigger around ${policy.s} units and recover inventory toward ${policy.S} units when replenishment is placed.`);
    recommendations.push(`Plan supply cover against an average projected demand of ${formatMetric(averageDemand)} units per day over the selected horizon.`);

    return {
        headline: `The inventory plan is targeting a ${simulation.service_level_achieved.toFixed(1)}% achieved service level with ${simulation.total_stockouts} projected stockout events across the simulation window.`,
        priority,
        recommendations,
        interpretation: [
            `The reorder point of ${policy.s} units is the level where the business should act before service risk rises.`,
            `Safety stock of ${policy.safety_stock} units is the current protection buffer against demand uncertainty.`
        ],
        business_impact: [
            'This output helps purchasing decide when to reorder and helps operations understand the trade-off between service and carrying cost.',
            'Stockout rate and service level indicate whether the current replenishment policy is protecting revenue reliably enough.'
        ],
        watchouts: [
            'Longer lead times can turn a reasonable reorder point into a service problem if demand accelerates.',
            'A low stockout count with very high average inventory may still imply working-capital pressure.'
        ]
    };
}

function displayResults(data) {
    displaySummary(data);
    displayHistoricalTab(data.historical);
    displayForecastingTab(data.ets_forecast, data.lgb_forecast);
    displayPolicyTab(data.policy);
    displaySimulationTab(data.simulation);

    const aiContext = {
        sku_id: data.sku_id,
        reorder_point: data.policy.parameters.s,
        order_up_to_level: data.policy.parameters.S,
        safety_stock: data.policy.parameters.safety_stock,
        service_level_achieved: data.simulation.metrics.service_level_achieved,
        stockout_rate: data.simulation.metrics.stockout_rate,
        total_stockouts: data.simulation.metrics.total_stockouts,
        avg_inventory_level: data.simulation.metrics.avg_inventory_level,
        projected_average_demand: data.lgb_forecast.success ? data.lgb_forecast.summary.projected_average : data.ets_forecast.summary.projected_average,
        projected_total_demand: data.lgb_forecast.success ? data.lgb_forecast.summary.projected_total : data.ets_forecast.summary.projected_total
    };

    requestBusinessInsight({
        demoId: 'inventory-optimization',
        context: aiContext,
        fallbackInsight: buildInventoryFallback(data),
        containerId: 'businessInsightContainer'
    });
}

function displaySummary(data) {
    const container = document.getElementById('summaryContent');
    const policy = data.policy.parameters;
    const sim = data.simulation.metrics;
    const forecastSummary = data.lgb_forecast.success ? data.lgb_forecast.summary : data.ets_forecast.summary;

    container.innerHTML = `
        <div class="summary-section">
            <h3><i class="fas fa-boxes"></i> Replenishment Plan</h3>
            <div class="summary-metrics">
                <div class="summary-metric">
                    <div class="summary-label">Reorder Point</div>
                    <div class="summary-value">${formatMetric(policy.s)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Order-up-to Level</div>
                    <div class="summary-value">${formatMetric(policy.S)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Safety Stock</div>
                    <div class="summary-value">${formatMetric(policy.safety_stock)}</div>
                </div>
            </div>
        </div>

        <div class="summary-section">
            <h3><i class="fas fa-chart-line"></i> Demand Outlook</h3>
            <div class="summary-metrics">
                <div class="summary-metric">
                    <div class="summary-label">Projected Total</div>
                    <div class="summary-value">${formatMetric(forecastSummary.projected_total)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Projected Average</div>
                    <div class="summary-value">${formatMetric(forecastSummary.projected_average)}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Peak Demand</div>
                    <div class="summary-value">${formatMetric(forecastSummary.peak_forecast || forecastSummary.next_day_forecast || 0)}</div>
                </div>
            </div>
        </div>

        <div class="summary-section">
            <h3><i class="fas fa-play-circle"></i> Service Risk</h3>
            <div class="summary-metrics">
                <div class="summary-metric ${sim.service_level_achieved >= 95 ? 'success' : 'warning'}">
                    <div class="summary-label">Service Level</div>
                    <div class="summary-value">${sim.service_level_achieved.toFixed(1)}%</div>
                </div>
                <div class="summary-metric ${sim.total_stockouts === 0 ? 'success' : 'warning'}">
                    <div class="summary-label">Stockouts</div>
                    <div class="summary-value">${sim.total_stockouts}</div>
                </div>
                <div class="summary-metric">
                    <div class="summary-label">Avg Inventory</div>
                    <div class="summary-value">${formatMetric(sim.avg_inventory_level)}</div>
                </div>
            </div>
        </div>
    `;
}

function displayHistoricalTab(historical) {
    const container = document.getElementById('historicalTab');
    container.innerHTML = `
        <div class="tab-section">
            <h3>Demand History</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Average Daily Demand</div>
                    <div class="metric-value">${formatMetric(historical.stats.mean, 1)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Median Demand</div>
                    <div class="metric-value">${formatMetric(historical.stats.median, 1)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Demand Range</div>
                    <div class="metric-value">${formatMetric(historical.stats.min)} - ${formatMetric(historical.stats.max)}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">History Window</div>
                    <div class="metric-value">${historical.total_days}</div>
                </div>
            </div>
        </div>
        <div class="tab-section">
            <h3>Historical Demand Pattern</h3>
            <div id="historicalChart"></div>
        </div>
    `;

    Plotly.newPlot('historicalChart', [{
        x: historical.time_series.dates,
        y: historical.time_series.demand,
        type: 'scatter',
        mode: 'lines',
        line: { color: '#3b82f6', width: 2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(59, 130, 246, 0.1)'
    }], {
        title: 'Historical Demand Over Time',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    }, { responsive: true });
}

function displayForecastingTab(ets, lgb) {
    const container = document.getElementById('forecastingTab');
    const primary = lgb.success ? lgb : ets;
    const comparison = lgb.success && ets.success;

    container.innerHTML = `
        <div class="tab-section">
            <h3>Forward Demand Outlook</h3>
            <div class="info-box">
                <p>The chart below shows the most recent demand history and the projected demand path for the selected horizon.</p>
            </div>
            <div id="forecastingChart"></div>
        </div>
        ${comparison ? `
            <div class="tab-section">
                <h3>Scenario Snapshot</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Scenario A Total</div>
                        <div class="metric-value">${formatMetric(ets.summary.projected_total)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Scenario B Total</div>
                        <div class="metric-value">${formatMetric(lgb.summary.projected_total)}</div>
                    </div>
                </div>
            </div>
        ` : ''}
    `;

    const traces = [{
        x: primary.visualization.history_dates,
        y: primary.visualization.history_values,
        type: 'scatter',
        mode: 'lines',
        name: 'Recent Demand',
        line: { color: '#3b82f6', width: 2 }
    }, {
        x: primary.visualization.future_dates,
        y: primary.visualization.future_forecast,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Projected Demand',
        line: { color: '#10b981', width: 3, dash: 'dash' },
        marker: { size: 5 }
    }];

    if (comparison) {
        traces.push({
            x: ets.visualization.future_dates,
            y: ets.visualization.future_forecast,
            type: 'scatter',
            mode: 'lines',
            name: 'Scenario A',
            line: { color: '#f59e0b', width: 2, dash: 'dot' }
        });
        traces.push({
            x: lgb.visualization.future_dates,
            y: lgb.visualization.future_forecast,
            type: 'scatter',
            mode: 'lines',
            name: 'Scenario B',
            line: { color: '#8b5cf6', width: 2 }
        });
    }

    Plotly.newPlot('forecastingChart', traces, {
        title: 'Recent Demand and Forward Demand Window',
        xaxis: { title: 'Date' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    }, { responsive: true });
}

function displayPolicyTab(policy) {
    const container = document.getElementById('policyTab');
    const params = policy.parameters;
    const inputs = policy.inputs;

    container.innerHTML = `
        <div class="tab-section">
            <h3>Replenishment Guidance</h3>
            <div class="policy-params-grid">
                <div class="policy-card highlight">
                    <div class="policy-label">Reorder Point</div>
                    <div class="policy-value">${formatMetric(params.s)}</div>
                    <div class="policy-description">Place a replenishment order when stock approaches this level.</div>
                </div>
                <div class="policy-card highlight">
                    <div class="policy-label">Order-up-to Level</div>
                    <div class="policy-value">${formatMetric(params.S)}</div>
                    <div class="policy-description">Recover inventory to this level after an order is received.</div>
                </div>
                <div class="policy-card">
                    <div class="policy-label">Safety Stock</div>
                    <div class="policy-value">${formatMetric(params.safety_stock)}</div>
                    <div class="policy-description">Buffer stock protecting service levels during demand swings and lead time delays.</div>
                </div>
                <div class="policy-card">
                    <div class="policy-label">Lead Time Demand</div>
                    <div class="policy-value">${formatMetric(params.expected_lead_time_demand)}</div>
                    <div class="policy-description">Expected consumption while waiting for replenishment to arrive.</div>
                </div>
            </div>
        </div>
        <div class="tab-section">
            <h3>Inventory Positioning</h3>
            <div id="policyChart"></div>
        </div>
        <div class="tab-section">
            <div class="info-box">
                <ul>
                    <li><strong>Lead Time:</strong> ${inputs.lead_time} days</li>
                    <li><strong>Target Service Level:</strong> ${(inputs.service_level * 100).toFixed(0)}%</li>
                    <li><strong>Average Daily Demand:</strong> ${inputs.mu.toFixed(1)} units</li>
                    <li><strong>Demand Variation:</strong> ${inputs.sigma.toFixed(1)} units</li>
                </ul>
            </div>
        </div>
    `;

    Plotly.newPlot('policyChart', [{
        x: policy.visualization.days,
        y: policy.visualization.inventory_levels,
        type: 'scatter',
        mode: 'lines',
        name: 'Inventory Level',
        line: { color: '#3b82f6', width: 2 }
    }, {
        x: [0, policy.visualization.days.length - 1],
        y: [params.s, params.s],
        type: 'scatter',
        mode: 'lines',
        name: 'Reorder Point',
        line: { color: '#f59e0b', width: 2, dash: 'dash' }
    }, {
        x: [0, policy.visualization.days.length - 1],
        y: [params.S, params.S],
        type: 'scatter',
        mode: 'lines',
        name: 'Order-up-to Level',
        line: { color: '#10b981', width: 2, dash: 'dash' }
    }], {
        title: 'Illustrative Inventory Control Band',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Inventory Level' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    }, { responsive: true });
}

function displaySimulationTab(simulation) {
    const container = document.getElementById('simulationTab');
    const metrics = simulation.metrics;
    const viz = simulation.visualization;

    container.innerHTML = `
        <div class="tab-section">
            <h3>Service Risk Outlook</h3>
            <div class="metrics-grid">
                <div class="metric-card ${metrics.stockout_rate < 5 ? 'success' : 'warning'}">
                    <div class="metric-label">Stockout Rate</div>
                    <div class="metric-value">${metrics.stockout_rate.toFixed(1)}%</div>
                </div>
                <div class="metric-card ${metrics.service_level_achieved >= 95 ? 'success' : 'warning'}">
                    <div class="metric-label">Service Level Achieved</div>
                    <div class="metric-value">${metrics.service_level_achieved.toFixed(1)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Total Orders</div>
                    <div class="metric-value">${metrics.total_orders}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Average Inventory</div>
                    <div class="metric-value">${formatMetric(metrics.avg_inventory_level)}</div>
                </div>
            </div>
        </div>
        <div class="tab-section">
            <h3>Simulated Inventory Level</h3>
            <div id="simInventoryChart"></div>
        </div>
        <div class="tab-section">
            <h3>Demand Pressure Across The Window</h3>
            <div id="simDemandChart"></div>
        </div>
    `;

    Plotly.newPlot('simInventoryChart', [{
        x: viz.days,
        y: viz.inventory_levels,
        type: 'scatter',
        mode: 'lines',
        name: 'Inventory',
        line: { color: '#3b82f6', width: 2 }
    }, {
        x: viz.stockout_days,
        y: viz.stockout_days.map(() => 0),
        type: 'scatter',
        mode: 'markers',
        name: 'Stockouts',
        marker: { color: '#ef4444', size: 8, symbol: 'x' }
    }], {
        title: 'Inventory Level Across The Simulation Window',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Inventory Level' },
        hovermode: 'x unified',
        margin: { t: 40, r: 20, b: 40, l: 50 }
    }, { responsive: true });

    Plotly.newPlot('simDemandChart', [{
        x: viz.days,
        y: viz.demand,
        type: 'bar',
        marker: { color: '#8b5cf6' },
        name: 'Demand'
    }], {
        title: 'Demand Pattern In The Simulation',
        xaxis: { title: 'Day' },
        yaxis: { title: 'Demand' },
        margin: { t: 40, r: 20, b: 40, l: 50 }
    }, { responsive: true });
}
