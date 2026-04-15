"""
Demos Blueprint - Supply Chain Interactive Demos
"""
import time

from flask import Blueprint, render_template, request, jsonify, session
import pandas as pd
import numpy as np
from io import StringIO
from sqlalchemy import func

from models import Publication
from utils.demo_ai import generate_business_insight, gemini_enabled

demos_bp = Blueprint('demos', __name__, url_prefix='/demos')

DEMO_DEFINITIONS = [
    {
        'id': 'demand-forecasting',
        'title': 'Demand Forecaster',
        'description': 'Upload historical sales data to project future demand, interpret the outlook, and plan the next move.',
        'category': 'AI & Machine Learning',
        'icon': 'fa-chart-line',
        'color': '#3b82f6',
        'paper_lookup': 'demand forecasting in us supply chains',
        'legacy_paper_id': 11,
        'status': 'active'
    },
    {
        'id': 'inventory-optimization',
        'title': 'Inventory Planner',
        'description': 'Turn demand signals into replenishment guidance, service-risk visibility, and clearer inventory decisions.',
        'category': 'Optimization',
        'icon': 'fa-boxes',
        'color': '#10b981',
        'paper_lookup': 'inventory optimization models',
        'legacy_paper_id': 21,
        'status': 'active'
    },
    {
        'id': 'supplier-risk',
        'title': 'Supplier Risk Radar',
        'description': 'Surface supplier exposure, shipment alerts, route trade-offs, and transaction risks that need attention first.',
        'category': 'Risk Management',
        'icon': 'fa-shield-alt',
        'color': '#f59e0b',
        'paper_lookup': 'supplier risk management',
        'legacy_paper_id': 20,
        'status': 'active'
    },
    {
        'id': 'blockchain-security',
        'title': 'Blockchain Supply Chain Security',
        'description': 'Visualize how blockchain enhances supply chain integrity and transaction security.',
        'category': 'Security',
        'icon': 'fa-link',
        'color': '#8b5cf6',
        'paper_lookup': 'blockchain applications in retail cybersecurity',
        'legacy_paper_id': 2,
        'status': 'active'
    },
    {
        'id': 'carbon-optimizer',
        'title': 'Carbon Reduction Calculator',
        'description': 'Compare current emissions with a lower-carbon operating plan and focus on the changes with the strongest reduction potential.',
        'category': 'Sustainability',
        'icon': 'fa-leaf',
        'color': '#10b981',
        'paper_lookup': 'sustainable supply chain operations',
        'legacy_paper_id': 13,
        'status': 'active'
    },
    {
        'id': 'sustainability-matrix',
        'title': 'Sustainable Supply Chain Matrix',
        'description': 'Decision support tool for evaluating supply chain sustainability.',
        'category': 'Sustainability',
        'icon': 'fa-balance-scale',
        'color': '#14b8a6',
        'paper_lookup': 'optimizing sustainable supply chains',
        'legacy_paper_id': 8,
        'status': 'active'
    },
    {
        'id': 'route-optimizer',
        'title': 'Eco-Efficient Route Planner',
        'description': 'Plan delivery routes optimized for both cost and environmental impact.',
        'category': 'Optimization',
        'icon': 'fa-route',
        'color': '#06b6d4',
        'paper_lookup': 'sustainable logistics optimization',
        'legacy_paper_id': 12,
        'status': 'coming_soon'
    },
    {
        'id': 'quantum-predictive-analytics',
        'title': 'Quantum Scenario Forecaster',
        'description': 'Preview a next-generation forecasting capability that combines quantum acceleration with AI planning workflows.',
        'category': 'Advanced Analytics',
        'icon': 'fa-atom',
        'color': '#6366f1',
        'paper_lookup': 'leveraging quantum computing and ai for predictive analytics',
        'status': 'coming_soon'
    },
    {
        'id': 'green-blockchain-logistics',
        'title': 'Green Logistics Ledger',
        'description': 'See how traceability, optimization, and sustainability can work together in a greener logistics operation.',
        'category': 'Sustainable Systems',
        'icon': 'fa-network-wired',
        'color': '#0f766e',
        'paper_lookup': 'integrating blockchain with ai to develop green logistics models',
        'status': 'coming_soon'
    },
    {
        'id': 'predictive-supplier-analytics',
        'title': 'Supplier Risk Radar',
        'description': 'Preview an expanded supplier intelligence workflow for anticipating disruption, performance drift, and sourcing risk.',
        'category': 'Risk Management',
        'icon': 'fa-magnifying-glass-chart',
        'color': '#f97316',
        'paper_lookup': 'advanced predictive supplier analytics using machine learning',
        'status': 'coming_soon'
    },
    {
        'id': 'inventory-iot',
        'title': 'Live Inventory Tracker',
        'description': 'Monitor inventory conditions in real time with sensor-driven signals and faster replenishment decisions.',
        'category': 'Inventory Intelligence',
        'icon': 'fa-tower-cell',
        'color': '#0891b2',
        'paper_lookup': 'real-time inventory management with ai and iot',
        'status': 'coming_soon'
    },
    {
        'id': 'resilient-supply-networks',
        'title': 'Supply Chain Resilience Mapper',
        'description': 'Test resilience scenarios for supply networks facing volatility, disruption, and changing service expectations.',
        'category': 'Network Design',
        'icon': 'fa-diagram-project',
        'color': '#7c3aed',
        'paper_lookup': 'modeling resilient supply chain networks with ai',
        'status': 'coming_soon'
    },
    {
        'id': 'autonomous-route-networks',
        'title': 'Autonomous Route Planner',
        'description': 'Evaluate how autonomous planning systems can improve route efficiency, service reliability, and network responsiveness.',
        'category': 'Autonomous Operations',
        'icon': 'fa-truck-fast',
        'color': '#0ea5e9',
        'paper_lookup': 'autonomous supply chain networks with ai-driven route optimization',
        'status': 'coming_soon'
    }
]

DEMO_BY_ID = {demo['id']: demo for demo in DEMO_DEFINITIONS}


def resolve_demo_paper_id(demo):
    """Resolve a publication by title fragment, with a legacy ID fallback."""
    paper_lookup = demo.get('paper_lookup')
    if paper_lookup:
        publication = (
            Publication.query
            .filter(func.lower(Publication.title).contains(paper_lookup.lower()))
            .order_by(Publication.year.desc(), Publication.id.desc())
            .first()
        )
        if publication:
            return publication.id

    return demo.get('legacy_paper_id')


def hydrate_demo(demo):
    """Attach resolved paper metadata used by templates."""
    hydrated_demo = demo.copy()
    hydrated_demo['paper_id'] = resolve_demo_paper_id(demo)
    hydrated_demo['has_research_link'] = hydrated_demo['paper_id'] is not None
    return hydrated_demo


def get_demo(demo_id):
    return hydrate_demo(DEMO_BY_ID[demo_id])


def check_business_ai_rate_limit() -> str | None:
    now = time.time()
    count_key = 'demo_ai_request_count'
    reset_key = 'demo_ai_reset_at'

    if count_key not in session:
        session[count_key] = 0
        session[reset_key] = now

    if now - float(session.get(reset_key, now)) > 300:
        session[count_key] = 0
        session[reset_key] = now

    if int(session.get(count_key, 0)) >= 12:
        return 'AI interpretation rate limit reached. Please wait a few minutes and try again.'

    session[count_key] = int(session.get(count_key, 0)) + 1
    return None

@demos_bp.route('/')
def demos_landing():
    """Demos landing page showing all available demos"""
    demos = [hydrate_demo(demo) for demo in DEMO_DEFINITIONS]
    return render_template('demos/demos_landing.html', demos=demos)

@demos_bp.route('/demand-forecasting', methods=['GET', 'POST'])
def demand_forecasting():
    """AI Demand Forecasting Tool - Advanced Multi-Feature Forecasting"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'data_file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['data_file']
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not file.filename.endswith('.csv'):
                return jsonify({'error': 'Only CSV files are supported'}), 400
            
            # Process the forecast using advanced system
            from demos.forecasting_utils import process_demand_forecast
            from io import StringIO
            forecast_horizon = request.form.get('forecast_horizon', type=int, default=12)
            
            # Read file content
            file_content = StringIO(file.read().decode('utf-8'))
            
            result = process_demand_forecast(file_content, forecast_horizon=forecast_horizon)
            
            if 'error' in result:
                return jsonify(result), 400
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # GET request - show the form
    return render_template(
        'demos/demand_forecasting.html',
        related_paper_id=get_demo('demand-forecasting')['paper_id']
    )

@demos_bp.route('/demand-forecasting/sample-data')
def download_sample_data():
    """Generate and download sample dataset"""
    try:
        from demos.forecasting_utils import generate_sample_dataset
        from flask import Response
        
        csv_data = generate_sample_dataset(n_samples=1000)
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sample_demand_data.csv'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@demos_bp.route('/api/business-insight', methods=['POST'])
def business_insight_api():
    payload = request.get_json(silent=True) or {}
    demo_id = str(payload.get('demo_id') or '').strip()
    context = payload.get('context') or {}
    fallback = payload.get('fallback') or {}

    if not demo_id:
        return jsonify({'error': 'demo_id is required'}), 400

    if not isinstance(context, dict):
        return jsonify({'error': 'context must be an object'}), 400

    limit_error = check_business_ai_rate_limit()
    if limit_error:
        return jsonify({'error': limit_error}), 429

    demo = DEMO_BY_ID.get(demo_id, {'title': demo_id.replace('-', ' ').title()})
    insight = generate_business_insight(demo.get('title', demo_id), context, fallback=fallback)

    return jsonify({
        'success': True,
        'gemini_enabled': gemini_enabled(),
        'insight': insight
    })

@demos_bp.route('/inventory-optimization')
def inventory_optimization():
    """AI Inventory Optimization Tool - Comprehensive Inventory Analysis"""
    from utils.inventory_analysis import get_available_skus
    
    try:
        skus = get_available_skus()
        return render_template(
            'demos/inventory_optimization.html',
            skus=skus,
            related_paper_id=get_demo('inventory-optimization')['paper_id']
        )
    except Exception as e:
        # If data file doesn't exist, show template with error
        return render_template(
            'demos/inventory_optimization.html',
            skus=[],
            error=str(e),
            related_paper_id=get_demo('inventory-optimization')['paper_id']
        )

@demos_bp.route('/api/inventory-analysis', methods=['POST'])
def inventory_analysis_api():
    """API endpoint for inventory analysis"""
    try:
        from utils.inventory_analysis import load_sku_data, InventoryAnalyzer
        
        # Extract parameters
        sku_id = request.form.get('sku_id')
        forecast_days = int(request.form.get('forecast_days', 28))
        lead_time = int(request.form.get('lead_time', 7))
        service_level = float(request.form.get('service_level', 0.95))
        sim_days = int(request.form.get('sim_days', 90))
        
        # Validate parameters
        if not sku_id:
            return jsonify({'error': 'SKU ID is required'}), 400
        
        # Load data for SKU
        sku_df = load_sku_data(sku_id)
        
        if len(sku_df) == 0:
            return jsonify({'error': f'No data found for SKU: {sku_id}'}), 404
        
        # Create analyzer
        analyzer = InventoryAnalyzer(sku_df)
        
        # Run all analyses
        results = {
            'sku_id': sku_id,
            'historical': analyzer.historical_analysis(),
            'ets_forecast': analyzer.forecast_ets(forecast_days),
            'lgb_forecast': analyzer.forecast_lightgbm(forecast_days),
        }
        
        # Calculate inventory policy
        policy = analyzer.calculate_inventory_policy(lead_time, service_level)
        results['policy'] = policy
        
        # Run simulation with calculated policy
        s = policy['parameters']['s']
        S = policy['parameters']['S']
        results['simulation'] = analyzer.simulate_inventory(s, S, lead_time, sim_days)
        
        return jsonify(results)
        
    except FileNotFoundError:
        return jsonify({'error': 'Data file not found. Please ensure sku_timeseries.csv exists in data/inventory/'}), 404
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================
# SUPPLIER RISK ASSESSMENT ROUTES
# ============================================

@demos_bp.route('/supplier-risk')
def supplier_risk():
    """Render supplier risk assessment tool"""
    return render_template(
        'demos/supplier_risk.html',
        related_paper_id=get_demo('supplier-risk')['paper_id']
    )


@demos_bp.route('/api/supplier-risk-analysis', methods=['POST'])
def supplier_risk_analysis_api():
    """
    Comprehensive supplier risk analysis API
    Supports 4 analysis types: forecasting, anomaly, routing, fraud
    """
    try:
        from utils.supplier_risk_analysis import SupplierRiskAnalyzer
        from utils.data_generators import (
            generate_supplier_data,
            generate_shipment_data,
            generate_transaction_data,
            generate_route_data
        )
        
        # Get analysis type
        analysis_type = request.form.get('analysis_type', 'all')
        use_sample_data = request.form.get('use_sample_data', 'true') == 'true'
        
        # Initialize analyzer
        analyzer = SupplierRiskAnalyzer()
        
        results = {}
        
        # 1. Risk Forecasting
        if analysis_type in ['all', 'forecasting']:
            if use_sample_data:
                supplier_df = generate_supplier_data(1000)
            else:
                # Handle uploaded CSV
                if 'supplier_file' in request.files:
                    file = request.files['supplier_file']
                    supplier_df = pd.read_csv(file)
                else:
                    supplier_df = generate_supplier_data(1000)
            
            results['forecasting'] = analyzer.train_forecasting_models(supplier_df)
        
        # 2. Anomaly Detection
        if analysis_type in ['all', 'anomaly']:
            if use_sample_data:
                shipment_df = generate_shipment_data(500)
            else:
                if 'shipment_file' in request.files:
                    file = request.files['shipment_file']
                    shipment_df = pd.read_csv(file)
                else:
                    shipment_df = generate_shipment_data(500)
            
            # Convert contamination from percentage (5-20) to decimal (0.05-0.20)
            contamination = float(request.form.get('contamination', 10)) / 100.0
            results['anomaly'] = analyzer.detect_anomalies(shipment_df, contamination)
        
        # 3. Route Optimization
        if analysis_type in ['all', 'routing']:
            if use_sample_data:
                route_df = generate_route_data(5)
            else:
                if 'route_file' in request.files:
                    file = request.files['route_file']
                    route_df = pd.read_csv(file)
                else:
                    route_df = generate_route_data(5)
            
            results['routing'] = analyzer.optimize_routes(route_df)
        
        # 4. Fraud Detection
        if analysis_type in ['all', 'fraud']:
            if use_sample_data:
                transaction_df = generate_transaction_data(10000)
            else:
                if 'transaction_file' in request.files:
                    file = request.files['transaction_file']
                    transaction_df = pd.read_csv(file)
                else:
                    transaction_df = generate_transaction_data(10000)
            
            epochs = int(request.form.get('epochs', 20))
            try:
                results['fraud'] = analyzer.detect_fraud(transaction_df, epochs)
            except Exception as fraud_err:
                # If fraud detection fails, log but continue with other results
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Fraud detection analysis failed: {str(fraud_err)}')
                results['fraud'] = {
                    'error': f'Fraud detection unavailable: {str(fraud_err)}',
                    'metrics': None,
                    'warning': 'Fraud detection module is currently unavailable. This is not a critical error.'
                }
        
        return jsonify(results)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# ============================================
# BLOCKCHAIN CYBERSECURITY ROUTES
# ============================================

@demos_bp.route('/blockchain-security')
def blockchain_security():
    """Render the Blockchain Retail Cybersecurity demo page"""
    return render_template(
        'demos/blockchain_security.html',
        related_paper_id=get_demo('blockchain-security')['paper_id']
    )

@demos_bp.route('/api/blockchain-simulation', methods=['POST'])
def api_blockchain_simulation():
    """Run the 2,000 iteration phishing detection simulation"""
    try:
        from utils.blockchain_engine import PhishingSimulation
        sim = PhishingSimulation()
        results = sim.run_full_simulation()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@demos_bp.route('/api/blockchain-ledger', methods=['POST'])
def api_blockchain_ledger():
    """Interaction with a live blockchain instance"""
    try:
        from utils.blockchain_engine import Blockchain
        data = request.json
        action = data.get('action')
        
        # In a real app, this would use a persistent chain or session-based one
        # For the demo, we'll initialize or manipulate based on input
        bc = Blockchain()
        
        if action == 'get_chain':
            chain_data = []
            for block in bc.chain:
                chain_data.append({
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'data': block.data,
                    'hash': block.hash,
                    'previous_hash': block.previous_hash
                })
            return jsonify({'chain': chain_data})
            
        elif action == 'add_block':
            block_data = data.get('data', {})
            new_block = bc.add_block(block_data)
            return jsonify({
                'index': new_block.index,
                'hash': new_block.hash
            })
            
        return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# CARBON FOOTPRINT OPTIMIZER ROUTES
# ============================================

@demos_bp.route('/carbon-optimizer')
def carbon_optimizer():
    """Render the AI Carbon Footprint Optimizer demo page"""
    return render_template(
        'demos/carbon_optimizer.html',
        related_paper_id=get_demo('carbon-optimizer')['paper_id']
    )

@demos_bp.route('/api/carbon-analysis', methods=['POST'])
def api_carbon_analysis():
    """Analyze carbon emissions and provide benchmarking"""
    try:
        from utils.carbon_analysis import CarbonEmissionPredictor
        data = request.json
        industry = data.get('industry', 'Electronic Manufacturing')
        revenue = float(data.get('revenue', 1000000))
        spend = float(data.get('spend', 500000))
        
        predictor = CarbonEmissionPredictor()
        predictor.train() # Fast train on 2000 samples
        
        prediction = predictor.predict_emissions(industry, 2024, spend)
        benchmarks = predictor.get_industry_benchmarks()
        
        # Calculate growth score
        intensity = prediction['total_kg_co2e'] / revenue
        growth_score = (revenue / 1000000) * (1 / intensity) if intensity > 0 else 0
        
        return jsonify({
            'prediction': prediction,
            'benchmarks': benchmarks,
            'growth_score': float(growth_score),
            'revenue': revenue
        })
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@demos_bp.route('/api/carbon-simulation', methods=['POST'])
def api_carbon_simulation():
    """Run scenario analysis for carbon reduction"""
    try:
        from utils.carbon_analysis import CarbonEmissionPredictor
        data = request.json
        current_config = data.get('current')
        sustainable_config = data.get('sustainable')
        
        predictor = CarbonEmissionPredictor()
        predictor.train()
        
        results = predictor.scenario_analysis(current_config, sustainable_config)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# SUSTAINABLE SUPPLY CHAIN MATRIX ROUTES
# ============================================

@demos_bp.route('/sustainability-matrix')
def sustainability_matrix():
    """Render the Sustainable Supply Chain Matrix demo"""
    return render_template(
        'demos/sustainability_matrix.html',
        related_paper_id=get_demo('sustainability-matrix')['paper_id']
    )

@demos_bp.route('/api/matrix-analysis', methods=['POST'])
def api_matrix_analysis():
    """Run the 4-model matrix analysis on fashion data"""
    try:
        from utils.matrix_analysis import FashionDataGenerator, MatrixModelEngine
        
        # 1. Generate Data
        # Allow user to override n_samples
        n_samples = int(request.json.get('n_samples', 150))
        noise_level = float(request.json.get('noise', 0.1)) # Not used yet, but good for future
        
        generator = FashionDataGenerator(n_samples=n_samples)
        df = generator.generate()
        
        # 2. Train & Evaluate Models
        engine = MatrixModelEngine()
        results = engine.run_analysis(df)
        
        return jsonify(results)
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500
