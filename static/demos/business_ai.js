function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderBusinessList(items) {
    if (!Array.isArray(items) || !items.length) {
        return '<p class="business-empty">No additional guidance available.</p>';
    }

    return `
        <ul class="business-list">
            ${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
    `;
}

function renderBusinessInsight(containerId, insight) {
    const container = document.getElementById(containerId);
    if (!container || !insight) return;

    const priorityClass = String(insight.priority || 'Monitor').toLowerCase();

    container.innerHTML = `
        <div class="business-insight-panel">
            <div class="business-insight-header">
                <div>
                    <p class="business-eyebrow">AI Recommendations</p>
                    <h3 class="business-headline">${escapeHtml(insight.headline || 'Business guidance is ready.')}</h3>
                </div>
                <span class="business-priority ${escapeHtml(priorityClass)}">${escapeHtml(insight.priority || 'Monitor')}</span>
            </div>
            <div class="business-insight-grid">
                <div class="business-card">
                    <h4>Recommended Actions</h4>
                    ${renderBusinessList(insight.recommendations)}
                </div>
                <div class="business-card">
                    <h4>How To Read This</h4>
                    ${renderBusinessList(insight.interpretation)}
                </div>
                <div class="business-card">
                    <h4>Business Impact</h4>
                    ${renderBusinessList(insight.business_impact)}
                </div>
                <div class="business-card">
                    <h4>Watchouts</h4>
                    ${renderBusinessList(insight.watchouts)}
                </div>
            </div>
        </div>
    `;
}

async function requestBusinessInsight({ demoId, context, fallbackInsight, containerId }) {
    renderBusinessInsight(containerId, fallbackInsight);

    try {
        const response = await fetch('/demos/api/business-insight', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                demo_id: demoId,
                context,
                fallback: fallbackInsight
            })
        });

        const data = await response.json();
        if (!response.ok || !data || !data.insight) {
            return;
        }

        renderBusinessInsight(containerId, data.insight);
    } catch (error) {
        console.error('Business insight request failed:', error);
    }
}
