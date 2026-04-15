let currentResults = null;

document.addEventListener('DOMContentLoaded', function () {
    initializeForm();
    initializeSliders();
    initializeTabs();
    initializeRadioButtons();
});

function initializeForm() {
    document.getElementById('riskAnalysisForm').addEventListener('submit', async function (event) {
        event.preventDefault();
        await runAnalysis();
    });
}

function initializeSliders() {
    [
        { id: 'contamination', valueId: 'contaminationValue' },
        { id: 'epochs', valueId: 'epochsValue' }
    ].forEach(({ id, valueId }) => {
        const input = document.getElementById(id);
        const display = document.getElementById(valueId);
        if (!input || !display) return;
        input.addEventListener('input', () => {
            display.textContent = input.value;
        });
    });

    const showAdvanced = document.getElementById('showAdvanced');
    const advancedOptions = document.getElementById('advancedOptions');
    if (showAdvanced && advancedOptions) {
        showAdvanced.addEventListener('change', () => {
            advancedOptions.style.display = showAdvanced.checked ? 'block' : 'none';
        });
    }
}

function initializeTabs() {
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });
}

function initializeRadioButtons() {
    const fileSection = document.getElementById('fileUploadSection');
    document.querySelectorAll('input[name="use_sample_data"]').forEach(radio => {
        radio.addEventListener('change', function () {
            fileSection.style.display = this.value === 'false' ? 'block' : 'none';
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
        const response = await fetch('/demos/api/supplier-risk-analysis', {
            method: 'POST',
            body: new FormData(document.getElementById('riskAnalysisForm'))
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Risk analysis failed.');
        }

        currentResults = data;
        displayResults(data);
        showState('results');
    } catch (error) {
        console.error('Risk analysis error:', error);
        document.getElementById('errorMessage').textContent = error.message;
        showState('error');
    }
}

function formatInt(value) {
    return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function buildSupplierFallback(data) {
    const recommendations = [];
    let priority = 'Monitor';

    if (data.forecasting?.business_view?.high_risk_suppliers > 0) {
        recommendations.push(`Escalate the ${data.forecasting.business_view.high_risk_suppliers} suppliers currently sitting in the high-risk tier.`);
        priority = 'High';
    }
    if (data.anomaly?.metrics?.detected_anomalies > 0) {
        recommendations.push(`Investigate the ${data.anomaly.metrics.detected_anomalies} flagged shipment anomalies before they affect service levels.`);
        if (priority === 'Monitor') priority = 'Medium';
    }
    if (data.routing?.recommended_route) {
        recommendations.push(`Use ${data.routing.recommended_route} as the preferred route while monitoring cost and disruption conditions.`);
    }
    if (data.fraud?.metrics?.fraud_detected > 0) {
        recommendations.push(`Review the ${data.fraud.metrics.fraud_detected} transactions flagged as suspicious before approval or payment release.`);
        priority = 'High';
    }

    return {
        headline: 'The radar is highlighting where supplier, shipment, routing, and transaction risk need attention first.',
        priority,
        recommendations,
        interpretation: [
            'Use supplier exposure to decide where sourcing teams need escalation.',
            'Use shipment and route views to prevent service disruption before it reaches customers.'
        ],
        business_impact: [
            'This output helps reduce continuity risk, late delivery exposure, compliance issues, and avoidable review workload.',
            'The best value comes from acting on concentrated risk rather than spreading effort evenly across every supplier.'
        ],
        watchouts: [
            'High disruption counts should trigger action even when the overall network still appears stable.',
            'Fraud review should be prioritized by suspicious probability and transaction value, not only by count.'
        ]
    };
}

function displayResults(data) {
    displaySummary(data);
    if (data.forecasting) displayForecastingTab(data.forecasting);
    if (data.anomaly) displayAnomalyTab(data.anomaly);
    if (data.routing) displayRoutingTab(data.routing);
    if (data.fraud) displayFraudTab(data.fraud);

    requestBusinessInsight({
        demoId: 'supplier-risk',
        context: {
            supplier_exposure: data.forecasting?.business_view || null,
            shipment_alerts: data.anomaly?.metrics || null,
            route_decision: data.routing || null,
            transaction_review: data.fraud?.metrics || null
        },
        fallbackInsight: buildSupplierFallback(data),
        containerId: 'businessInsightContainer'
    });
}

function displaySummary(data) {
    const container = document.getElementById('summaryContent');
    const sections = [];

    if (data.forecasting?.business_view) {
        const view = data.forecasting.business_view;
        sections.push(`
            <div class="summary-section">
                <h3><i class="fas fa-chart-line"></i> Supplier Exposure</h3>
                <div class="summary-metrics">
                    <div class="summary-metric warning">
                        <div class="summary-label">High Risk Suppliers</div>
                        <div class="summary-value">${formatInt(view.high_risk_suppliers)}</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">Projected Total Demand</div>
                        <div class="summary-value">${formatInt(view.projected_total_demand)}</div>
                    </div>
                </div>
            </div>
        `);
    }

    if (data.anomaly?.metrics) {
        sections.push(`
            <div class="summary-section">
                <h3><i class="fas fa-exclamation-triangle"></i> Shipment Alerts</h3>
                <div class="summary-metrics">
                    <div class="summary-metric warning">
                        <div class="summary-label">Alerts Detected</div>
                        <div class="summary-value">${formatInt(data.anomaly.metrics.detected_anomalies)}</div>
                    </div>
                </div>
            </div>
        `);
    }

    if (data.routing) {
        sections.push(`
            <div class="summary-section">
                <h3><i class="fas fa-route"></i> Route Decision</h3>
                <div class="summary-metrics">
                    <div class="summary-metric success">
                        <div class="summary-label">Preferred Route</div>
                        <div class="summary-value-text">${escapeHtml(data.routing.recommended_route)}</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">Improvement</div>
                        <div class="summary-value">${Number(data.routing.improvement_percentage || 0).toFixed(1)}%</div>
                    </div>
                </div>
            </div>
        `);
    }

    if (data.fraud?.metrics) {
        sections.push(`
            <div class="summary-section">
                <h3><i class="fas fa-user-shield"></i> Transaction Review</h3>
                <div class="summary-metrics">
                    <div class="summary-metric warning">
                        <div class="summary-label">Flagged Transactions</div>
                        <div class="summary-value">${formatInt(data.fraud.metrics.fraud_detected)}</div>
                    </div>
                    <div class="summary-metric">
                        <div class="summary-label">Transactions Reviewed</div>
                        <div class="summary-value">${formatInt(data.fraud.metrics.total_transactions)}</div>
                    </div>
                </div>
            </div>
        `);
    }

    container.innerHTML = sections.join('');
}

function displayForecastingTab(forecasting) {
    const container = document.getElementById('forecastingTab');
    const suppliers = forecasting.business_view?.top_suppliers || [];

    container.innerHTML = `
        <div class="tab-section">
            <h3>Suppliers Requiring Attention</h3>
            <div id="supplierExposureChart"></div>
        </div>
        <div class="tab-section">
            <h3>Priority Supplier List</h3>
            <div class="route-table-container">
                <table class="route-table">
                    <thead>
                        <tr>
                            <th>Supplier</th>
                            <th>Risk Tier</th>
                            <th>Projected Demand</th>
                            <th>Lead Time</th>
                            <th>Delivery Performance</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${suppliers.map(item => `
                            <tr>
                                <td><strong>${escapeHtml(item.supplier_id)}</strong></td>
                                <td>${escapeHtml(item.risk_category)}</td>
                                <td>${formatInt(item.projected_demand)}</td>
                                <td>${Number(item.lead_time_days || 0).toFixed(1)} days</td>
                                <td>${Number(item.delivery_performance || 0).toFixed(1)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    Plotly.newPlot('supplierExposureChart', [{
        x: suppliers.map(item => item.supplier_id),
        y: suppliers.map(item => item.projected_demand),
        type: 'bar',
        marker: {
            color: suppliers.map(item => item.risk_category === 'High' ? '#ef4444' : item.risk_category === 'Medium' ? '#f59e0b' : '#10b981')
        }
    }], {
        title: 'Projected Demand Exposure For Priority Suppliers',
        xaxis: { title: 'Supplier' },
        yaxis: { title: 'Projected Demand' },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    }, { responsive: true });
}

function displayAnomalyTab(anomaly) {
    const container = document.getElementById('anomalyTab');
    const alerts = anomaly.top_alerts || [];

    container.innerHTML = `
        <div class="tab-section">
            <h3>Shipment Alert Distribution</h3>
            <div id="anomalyScoreChart"></div>
        </div>
        <div class="tab-section">
            <h3>Highest-Priority Shipment Alerts</h3>
            <div class="route-table-container">
                <table class="route-table">
                    <thead>
                        <tr>
                            <th>Shipment</th>
                            <th>Delay</th>
                            <th>Price Spike</th>
                            <th>Weather Risk</th>
                            <th>Geo Flag</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map(item => `
                            <tr>
                                <td><strong>${escapeHtml(item.shipment_id)}</strong></td>
                                <td>${Number(item.delivery_delay_days || 0).toFixed(1)} days</td>
                                <td>${Number(item.price_spike_percentage || 0).toFixed(1)}%</td>
                                <td>${Number(item.weather_disruption_index || 0).toFixed(1)}</td>
                                <td>${item.geopolitical_event_flag ? 'Yes' : 'No'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    const scores = anomaly.anomaly_scores || [];
    const labels = anomaly.anomaly_labels || [];
    Plotly.newPlot('anomalyScoreChart', [{
        x: scores.filter((_, index) => labels[index] === 0),
        type: 'histogram',
        name: 'Normal Shipments',
        marker: { color: '#10b981' },
        opacity: 0.75
    }, {
        x: scores.filter((_, index) => labels[index] === 1),
        type: 'histogram',
        name: 'Flagged Shipments',
        marker: { color: '#ef4444' },
        opacity: 0.75
    }], {
        title: 'Shipment Alert Score Distribution',
        xaxis: { title: 'Alert Score' },
        yaxis: { title: 'Count' },
        barmode: 'overlay',
        margin: { t: 40, r: 20, b: 50, l: 50 }
    }, { responsive: true });
}

function displayRoutingTab(routing) {
    const container = document.getElementById('routingTab');

    container.innerHTML = `
        <div class="tab-section">
            <h3>Recommended Route</h3>
            <div class="info-box">
                <p><strong>${escapeHtml(routing.recommended_route)}</strong> provides the best balance of risk, time, and cost in the current scenario.</p>
                <p><strong>Improvement vs least-favorable route:</strong> ${Number(routing.improvement_percentage || 0).toFixed(1)}%</p>
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
                            <th>Fuel Cost</th>
                            <th>Time</th>
                            <th>Risk Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${routing.routes.map(route => `
                            <tr class="${route.rank === 1 ? 'best-route' : ''}">
                                <td>${route.rank}</td>
                                <td><strong>${escapeHtml(route.name)}</strong></td>
                                <td>$${Number(route.total_fuel_cost || 0).toFixed(2)}</td>
                                <td>${Number(route.total_time_hours || 0).toFixed(1)} hrs</td>
                                <td>${Number(route.risk_score || 0).toFixed(3)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="tab-section">
            <h3>Route Risk Comparison</h3>
            <div id="routeRiskChart"></div>
        </div>
    `;

    Plotly.newPlot('routeRiskChart', [{
        x: routing.routes.map(route => route.name),
        y: routing.routes.map(route => route.risk_score),
        type: 'bar',
        marker: {
            color: routing.routes.map(route => route.rank === 1 ? '#10b981' : '#f59e0b')
        }
    }], {
        title: 'Route Risk Scores',
        xaxis: { title: 'Route' },
        yaxis: { title: 'Risk Score' },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    }, { responsive: true });
}

function displayFraudTab(fraud) {
    const container = document.getElementById('fraudTab');
    const alerts = fraud.top_alerts || [];

    container.innerHTML = `
        <div class="tab-section">
            <h3>Highest-Priority Transactions</h3>
            <div id="fraudProbabilityChart"></div>
        </div>
        <div class="tab-section">
            <h3>Manual Review Queue</h3>
            <div class="route-table-container">
                <table class="route-table">
                    <thead>
                        <tr>
                            <th>Transaction</th>
                            <th>Amount</th>
                            <th>Device</th>
                            <th>Category</th>
                            <th>Suspicion</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map(item => `
                            <tr>
                                <td><strong>${escapeHtml(item.transaction_id)}</strong></td>
                                <td>$${formatInt(item.transaction_amount)}</td>
                                <td>${escapeHtml(item.device_type)}</td>
                                <td>${escapeHtml(item.merchant_category)}</td>
                                <td>${(Number(item.fraud_probability || 0) * 100).toFixed(1)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    Plotly.newPlot('fraudProbabilityChart', [{
        x: alerts.map(item => item.transaction_id),
        y: alerts.map(item => Number(item.fraud_probability || 0) * 100),
        type: 'bar',
        marker: { color: '#ef4444' }
    }], {
        title: 'Suspicion Level For Flagged Transactions',
        xaxis: { title: 'Transaction' },
        yaxis: { title: 'Suspicion %' },
        margin: { t: 40, r: 20, b: 60, l: 60 }
    }, { responsive: true });
}
