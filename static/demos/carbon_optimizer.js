document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('carbonConfigForm').addEventListener('submit', function (event) {
        event.preventDefault();
        calculateFootprint();
    });
});

function calculateFootprint() {
    const activity = Number(document.getElementById('activityLevel').value || 0);
    const energy = Number(document.getElementById('energyConsumption').value || 0);
    const fuel = document.getElementById('fuelType').value;
    const condition = document.getElementById('weatherCondition').value;

    const initial = document.getElementById('dashboardInitial');
    const loading = document.getElementById('dashboardLoading');
    const results = document.getElementById('dashboardResults');
    const detail = document.getElementById('detailedCharts');

    if (initial) initial.style.display = 'none';
    if (results) results.style.display = 'none';
    if (detail) detail.style.display = 'none';
    if (loading) loading.style.display = 'block';

    const fuelFactors = { Diesel: 2.68, Gasoline: 2.31, 'Natural Gas': 1.9, 'Grid Electricity': 0.45 };
    const conditionFactors = { Sunny: 1.0, Rainy: 1.05, Snowy: 1.15, Extreme: 1.25 };

    const currentEmission = energy * (fuelFactors[fuel] || 0.5) * (activity / 100) * (conditionFactors[condition] || 1.0);
    const optimizedEmission = currentEmission * 0.85;
    const reduction = currentEmission - optimizedEmission;
    const intensity = activity > 0 ? currentEmission / activity : 0;

    setTimeout(() => {
        document.getElementById('totalEmissionsVal').textContent = Math.round(currentEmission).toLocaleString();
        document.getElementById('reductionVal').textContent = Math.round(reduction).toLocaleString();
        document.getElementById('intensityVal').textContent = intensity.toFixed(1);

        renderComparisonChart(currentEmission, optimizedEmission);
        if (loading) loading.style.display = 'none';
        if (results) results.style.display = 'block';
        if (detail) detail.style.display = 'block';

        requestBusinessInsight({
            demoId: 'carbon-optimizer',
            context: {
                activity_level: activity,
                energy_consumption: energy,
                fuel_type: fuel,
                operating_condition: condition,
                current_emissions: currentEmission,
                optimized_emissions: optimizedEmission,
                reduction_potential: reduction,
                emission_intensity: intensity
            },
            fallbackInsight: buildCarbonFallback(activity, energy, fuel, condition, currentEmission, optimizedEmission, reduction, intensity),
            containerId: 'businessInsightContainer'
        });
    }, 500);
}

function buildCarbonFallback(activity, energy, fuel, condition, currentEmission, optimizedEmission, reduction, intensity) {
    const priority = reduction > 5000 || condition === 'Extreme' ? 'High' : reduction > 2000 ? 'Medium' : 'Monitor';
    const recommendations = [];

    if (fuel !== 'Grid Electricity') {
        recommendations.push('Review whether part of the operating load can shift to lower-carbon energy sources.');
    }
    if (condition === 'Extreme' || condition === 'Snowy') {
        recommendations.push('Adjust operating plans for disruption-heavy conditions because emissions are likely to rise under friction.');
    }
    recommendations.push(`Target a first-pass reduction of about ${Math.round(reduction).toLocaleString()} kg CO2e from the current operating profile.`);

    return {
        headline: `The current operating profile is generating about ${Math.round(currentEmission).toLocaleString()} kg CO2e, with a realistic near-term reduction opportunity of ${Math.round(reduction).toLocaleString()} kg CO2e.`,
        priority,
        recommendations,
        interpretation: [
            `Emission intensity is approximately ${intensity.toFixed(1)} kg CO2e per activity point.`,
            'Higher activity and more disruptive conditions materially increase the footprint and the cost of keeping operations running.'
        ],
        business_impact: [
            'This output helps operations and sustainability teams prioritize where a reduction plan can lower both emissions and operating friction.',
            'Reduction potential is useful for internal planning, reporting discussions, and supplier engagement.'
        ],
        watchouts: [
            'High reduction potential often points to process inefficiency, not just energy source choice.',
            'Extreme operating conditions can erode improvement plans unless they are built into contingency planning.'
        ]
    };
}

function renderComparisonChart(currentEmission, optimizedEmission) {
    Plotly.newPlot('comparisonChart', [{
        x: ['Current Setup', 'Improved Scenario'],
        y: [currentEmission, optimizedEmission],
        type: 'bar',
        marker: { color: ['#ef4444', '#10b981'] }
    }], {
        title: 'Emissions Comparison',
        xaxis: { title: 'Scenario' },
        yaxis: { title: 'kg CO2e' },
        margin: { t: 40, r: 20, b: 50, l: 60 }
    }, { responsive: true, displayModeBar: false });
}
