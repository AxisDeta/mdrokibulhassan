/**
 * Blockchain Retail Cybersecurity - Interactive Frontend
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initial State
    const simulationLab = document.getElementById('simulationLab');
    const ledgerLab = document.getElementById('ledgerLab');
    const simulationSummary = document.getElementById('simulationSummary');
    const ledgerView = document.getElementById('ledgerView');

    // 1. Initialize Labs (Tab Switching)
    initializeLabs();

    // 2. Initialize Blockchain (Genesis)
    let currentBlockchain = [];
    refreshLedger();

    // 3. Phishing Simulation Event
    document.getElementById('runSimulationBtn').addEventListener('click', runPhishingSimulation);

    // 4. Add Block Event
    document.getElementById('addBlockBtn').addEventListener('click', addNewBlock);
});

/**
 * Handle lab tab switching
 */
function initializeLabs() {
    const tabButtons = document.querySelectorAll('.lab-tab-btn');
    const contents = document.querySelectorAll('.lab-content');
    const summaryView = document.getElementById('simulationSummary');
    const ledgerView = document.getElementById('ledgerView');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            tabButtons.forEach(b => b.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));

            this.classList.add('active');
            const lab = this.dataset.lab;
            document.getElementById(lab + 'Lab').classList.add('active');

            // Toggle view visibility
            if (lab === 'simulation') {
                summaryView.style.display = 'block';
                ledgerView.style.display = 'none';
            } else {
                summaryView.style.display = 'none';
                ledgerView.style.display = 'block';
                refreshLedger(); // Ensure ledger is loaded
            }
        });
    });
}

/**
 * Run the 2,000 iteration simulation
 */
async function runPhishingSimulation() {
    const btn = document.getElementById('runSimulationBtn');
    const loading = document.getElementById('loadingState');
    const results = document.getElementById('resultsState');
    const initial = document.getElementById('initialState');

    // UI Feedback
    btn.disabled = true;
    initial.style.display = 'none';
    loading.style.display = 'block';
    results.style.display = 'none';

    try {
        const response = await fetch('/demos/api/blockchain-simulation', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Update UI
        document.getElementById('phishingCount').textContent = data.detected_phishing;
        renderSimulationChart(data);
        renderMessageLog(data.messages_sample);

        // Show results
        loading.style.display = 'none';
        results.style.display = 'block';
        btn.disabled = false;

    } catch (error) {
        console.error('Simulation error:', error);
        alert('Simulation failed: ' + error.message);
        loading.style.display = 'none';
        initial.style.display = 'block';
        btn.disabled = false;
    }
}

/**
 * Render detection pie chart
 */
function renderSimulationChart(data) {
    const chartData = [{
        values: [data.legitimate_messages, data.phishing_messages],
        labels: ['Legitimate Messages', 'Phishing Attacks'],
        type: 'pie',
        marker: {
            colors: ['#10b981', '#ef4444']
        },
        hoverinfo: 'label+percent',
        textinfo: 'value'
    }];

    const layout = {
        title: 'Retail Message Distribution',
        height: 300,
        margin: { t: 40, b: 10, l: 10, r: 10 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#6b7280' }
    };

    Plotly.newPlot('simulationChart', chartData, layout, { responsive: true, displayModeBar: false });
}

/**
 * Render message logs (scrolling terminal style)
 */
function renderMessageLog(messages) {
    const container = document.getElementById('messageLog');
    container.innerHTML = '';

    messages.forEach(msg => {
        const entry = document.createElement('div');
        entry.className = `log-entry ${msg.is_phishing ? 'phishing' : 'legitimate'}`;

        const type = msg.is_phishing ? 'BLOCKED' : 'VERIFIED';
        const icon = msg.is_phishing ? '✖' : '✔';

        entry.innerHTML = `
            <span class="timestamp">[${msg.timestamp.split(' ')[1]}]</span>
            <span class="status">${icon} ${type}:</span>
            <span class="sender">${msg.sender}</span>
            <span class="subject">- ${msg.subject}</span>
        `;
        container.appendChild(entry);
    });
}

/**
 * Logic for Dynamic Ledger Lab
 */
async function refreshLedger() {
    const container = document.getElementById('blockchainLedger');

    try {
        const response = await fetch('/demos/api/blockchain-ledger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'get_chain' })
        });
        const data = await response.json();

        container.innerHTML = '';
        data.chain.forEach(block => {
            const card = document.createElement('div');
            card.className = 'block-card';
            card.innerHTML = `
                <div class="block-title">BLOCK #${block.index}</div>
                <div class="block-field"><label>Timestamp:</label><span>${new Date(block.timestamp * 1000).toLocaleString()}</span></div>
                <div class="block-field"><label>Data:</label><span>${JSON.stringify(block.data)}</span></div>
                <div class="block-field"><label>Prev Hash:</label><span>${block.previous_hash}</span></div>
                <div class="block-field"><label>Block Hash:</label><span>${block.hash}</span></div>
            `;
            container.appendChild(card);
        });

    } catch (error) {
        console.error('Ledger error:', error);
    }
}

async function addNewBlock() {
    const dataInput = document.getElementById('blockData');
    const message = dataInput.value.trim();

    if (!message) {
        alert('Please enter some data for the block');
        return;
    }

    const btn = document.getElementById('addBlockBtn');
    btn.disabled = true;

    try {
        const response = await fetch('/demos/api/blockchain-ledger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'add_block',
                data: { message: message }
            })
        });

        if (response.ok) {
            dataInput.value = '';
            refreshLedger();
            // Show results state if hidden
            document.getElementById('initialState').style.display = 'none';
            document.getElementById('resultsState').style.display = 'block';
        }

    } catch (error) {
        alert('Failed to add block');
    } finally {
        btn.disabled = false;
    }
}
