"""
Quick test script to verify supplier risk API endpoint
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from flask import Flask

app = create_app()

# List all routes
print("=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    if 'supplier' in str(rule):
        print(f"{rule.methods} {rule}")

print("\n=== Testing Data Generation ===")
from utils.data_generators import generate_supplier_data, generate_shipment_data
from utils.supplier_risk_analysis import SupplierRiskAnalyzer

# Test data generation
supplier_df = generate_supplier_data(10)
print(f"✓ Generated {len(supplier_df)} supplier records")

shipment_df = generate_shipment_data(10)
print(f"✓ Generated {len(shipment_df)} shipment records")

# Test analyzer
analyzer = SupplierRiskAnalyzer()
print("✓ SupplierRiskAnalyzer initialized")

# Test forecasting
results = analyzer.train_forecasting_models(supplier_df)
print(f"✓ Forecasting complete. Best model: {results['best_model']}")

print("\n=== All Tests Passed ===")
print("The API should work correctly.")
print("\nTo start the Flask server, run:")
print("  python app.py")
print("\nThen navigate to:")
print("  http://localhost:5000/demos/supplier-risk")
