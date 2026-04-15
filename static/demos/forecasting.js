let forecastResults = null;

const fileInput = document.getElementById('dataFile');
const fileUploadArea = document.getElementById('fileUploadArea');
const fileName = document.getElementById('fileName');
const horizonInput = document.getElementById('forecastHorizon');
const horizonValue = document.getElementById('forecastHorizonValue');

if (fileInput) {
    fileInput.addEventListener('change', (event) => {
        if (event.target.files.length > 0) {
            fileName.textContent = `Selected: ${event.target.files[0].name}`;
            fileName.style.display = 'block';
        }
    });
}

if (fileUploadArea) {
    fileUploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        fileUploadArea.classList.add('drag-over');
    });

    fileUploadArea.addEventListener('dragleave', () => {
        fileUploadArea.classList.remove('drag-over');
    });

    fileUploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        fileUploadArea.classList.remove('drag-over');
        if (event.dataTransfer.files.length > 0) {
            fileInput.files = event.dataTransfer.files;
            fileName.textContent = `Selected: ${event.dataTransfer.files[0].name}`;
            fileName.style.display = 'block';
        }
    });
}

if (horizonInput && horizonValue) {
    horizonInput.addEventListener('input', () => {
        horizonValue.textContent = horizonInput.value;
    });
}

document.getElementById('forecastForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    showState('loading');

    try {
        const response = await fetch('/demos/demand-forecasting', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate demand outlook.');
        }

        forecastResults = data;
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
    } else {
        document.getElementById('initialState').style.display = 'flex';
    }
}

function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    showState('error');
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function formatPercent(value) {
    const sign = Number(value) > 0 ? '+' : '';
    return `${sign}${Number(value || 0).toFixed(1)}%`;
}

function buildFallbackInsight(data) {
    const trend = Number(data.forecast.trend_percent || 0);
    const volatility = Number(data.forecast.volatility_percent || 0);
    const risk = data.forecast.planning_risk || 'Monitor';
    const peakPeriod = data.forecast.peak_period;
    const lowPeriod = data.forecast.low_period;

    const recommendations = [];
    if (trend >= 10) {
        recommendations.push(`Increase purchasing and replenishment cover ahead of ${peakPeriod}.`);
    } else if (trend <= -10) {
        recommendations.push('Trim buying plans and avoid overcommitting inventory into the next cycle.');
    } else {
        recommendations.push('Keep the current demand plan broadly steady and monitor the next cycle closely.');
    }

    if (volatility >= 18) {
        recommendations.push('Carry extra safety stock and tighten supplier follow-up because demand swings are elevated.');
    } else {
        recommendations.push('Use normal replenishment controls because the forecast remains relatively stable.');
    }

    recommendations.push(`Prepare a commercial and staffing response around the projected peak in ${peakPeriod}.`);

    return {
        headline: `Projected demand is ${trend >= 0 ? 'moving above' : 'tracking below'} the recent baseline, with a ${risk.toLowerCase()} planning priority for the next ${data.forecast_horizon} periods.`,
        priority: risk,
        recommendations,
        interpretation: [
            `The strongest demand point is expected in ${peakPeriod}, while the softest point appears in ${lowPeriod}.`,
            `The projected average period demand is ${formatNumber(data.forecast.projected_average)} against a recent historical average of ${formatNumber(data.stats.historical_average)}.`
        ],
        business_impact: [
            'This output is most useful for inventory positioning, purchasing cadence, labor planning, and promotion timing.',
            'Demand trend and volatility together indicate how aggressively the business should commit stock and capacity.'
        ],
        watchouts: [
            'A rising trend with high volatility can increase stockout pressure if supply response is slow.',
            'A falling trend can create excess inventory risk if buys are not adjusted early.'
        ]
    };
}

function displayResults(data) {
    document.getElementById('projectedTotal').textContent = formatNumber(data.forecast.projected_total);
    document.getElementById('projectedAverage').textContent = formatNumber(data.forecast.projected_average);
    document.getElementById('peakPeriod').textContent = `${data.forecast.peak_period} (${formatNumber(data.forecast.peak_value)})`;
    document.getElementById('planningRisk').textContent = data.forecast.planning_risk;
    document.getElementById('historicalAverage').textContent = formatNumber(data.stats.historical_average);
    document.getElementById('trendPercent').textContent = formatPercent(data.forecast.trend_percent);
    document.getElementById('volatilityPercent').textContent = `${Number(data.forecast.volatility_percent || 0).toFixed(1)}%`;
    document.getElementById('recordCount').textContent = formatNumber(data.stats.total_records);

    renderForecastChart(data);

    const aiContext = {
        forecast_horizon: data.forecast_horizon,
        projected_total: data.forecast.projected_total,
        projected_average: data.forecast.projected_average,
        peak_period: data.forecast.peak_period,
        peak_value: data.forecast.peak_value,
        low_period: data.forecast.low_period,
        low_value: data.forecast.low_value,
        trend_percent: data.forecast.trend_percent,
        volatility_percent: data.forecast.volatility_percent,
        planning_risk: data.forecast.planning_risk,
        historical_average: data.stats.historical_average,
        records_analyzed: data.stats.total_records
    };

    requestBusinessInsight({
        demoId: 'demand-forecasting',
        context: aiContext,
        fallbackInsight: buildFallbackInsight(data),
        containerId: 'businessInsightContainer'
    });
}

function renderForecastChart(data) {
    const historyLabels = data.historical.labels;
    const forecastLabels = data.forecast.labels;

    const historyTrace = {
        x: historyLabels,
        y: data.historical.values,
        name: 'Recent Demand',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#3b82f6', width: 2 },
        marker: { size: 5 }
    };

    const forecastTrace = {
        x: forecastLabels,
        y: data.forecast.values,
        name: 'Projected Demand',
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#10b981', width: 3, dash: 'dash' },
        marker: { size: 6 }
    };

    const layout = {
        title: 'Recent Demand and Forward Projection',
        xaxis: { title: 'Planning Window' },
        yaxis: { title: 'Demand' },
        hovermode: 'x unified',
        margin: { t: 50, r: 20, b: 50, l: 50 },
        legend: { orientation: 'h', y: 1.12, x: 0 }
    };

    Plotly.newPlot('forecastChart', [historyTrace, forecastTrace], layout, { responsive: true, displayModeBar: false });
}

document.getElementById('exportBtn').addEventListener('click', () => {
    if (!forecastResults) return;

    const exportPayload = {
        historical_average: forecastResults.stats.historical_average,
        forecast_horizon: forecastResults.forecast_horizon,
        projected_total: forecastResults.forecast.projected_total,
        projected_average: forecastResults.forecast.projected_average,
        peak_period: forecastResults.forecast.peak_period,
        peak_value: forecastResults.forecast.peak_value,
        low_period: forecastResults.forecast.low_period,
        low_value: forecastResults.forecast.low_value,
        trend_percent: forecastResults.forecast.trend_percent,
        volatility_percent: forecastResults.forecast.volatility_percent,
        planning_risk: forecastResults.forecast.planning_risk,
        forecast_values: forecastResults.forecast.values
    };

    const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `demand_planning_summary_${new Date().toISOString().split('T')[0]}.json`;
    anchor.click();
    window.URL.revokeObjectURL(url);
});
