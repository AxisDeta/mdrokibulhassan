"""
Synthetic Data Generators for Supplier Risk Assessment
Generates realistic datasets for demonstration purposes
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_supplier_data(n_samples=1000, seed=42):
    """
    Generate synthetic supplier risk dataset
    
    Args:
        n_samples: Number of supplier records to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with supplier features and target variable
    """
    np.random.seed(seed)
    
    # Generate supplier IDs
    supplier_ids = [f"SUP{str(i).zfill(4)}" for i in range(1, n_samples + 1)]
    
    # Generate features with realistic distributions
    data = {
        'supplier_id': supplier_ids,
        
        # Historical demand (log-normal distribution, mean=5000, std=2000)
        'historical_demand': np.random.lognormal(mean=8.5, sigma=0.4, size=n_samples),
        
        # Delivery performance (beta distribution, skewed towards high performance)
        'delivery_performance': np.random.beta(a=8, b=2, size=n_samples) * 100,
        
        # Financial health score (normal distribution, mean=70, std=15)
        'financial_health_score': np.clip(np.random.normal(70, 15, n_samples), 0, 100),
        
        # Geopolitical risk score (exponential distribution, most low risk)
        'geopolitical_risk_score': np.clip(np.random.exponential(2, n_samples), 0, 10),
        
        # Weather risk index (gamma distribution)
        'weather_risk_index': np.clip(np.random.gamma(2, 1.5, n_samples), 0, 10),
        
        # Price volatility (absolute value of normal, mean=5%, std=10%)
        'price_volatility': np.abs(np.random.normal(5, 10, n_samples)),
        
        # Shipment anomaly score (beta distribution, most low anomaly)
        'shipment_anomaly_score': np.random.beta(a=2, b=8, size=n_samples),
        
        # News sentiment score (normal distribution, mean=0.1, std=0.3)
        'news_sentiment_score': np.clip(np.random.normal(0.1, 0.3, n_samples), -1, 1),
        
        # Lead time days (log-normal, mean=14 days)
        'lead_time_days': np.clip(np.random.lognormal(mean=2.6, sigma=0.4, size=n_samples), 1, 60),
        
        # Quality score (beta distribution, skewed towards high quality)
        'quality_score': np.random.beta(a=9, b=2, size=n_samples) * 100,
        
        # Contract compliance (beta distribution, high compliance)
        'contract_compliance': np.random.beta(a=10, b=1.5, size=n_samples) * 100,
    }
    
    df = pd.DataFrame(data)
    
    # Generate target variable (future demand) based on features with noise
    # Future demand influenced by historical demand, quality, and risk factors
    base_demand = df['historical_demand'] * 1.05  # 5% growth baseline
    quality_factor = (df['quality_score'] / 100) * 0.2 + 0.9  # Quality impact
    risk_penalty = 1 - (df['geopolitical_risk_score'] / 100) * 0.1  # Risk penalty
    weather_penalty = 1 - (df['weather_risk_index'] / 100) * 0.05  # Weather penalty
    
    df['future_demand'] = (
        base_demand * quality_factor * risk_penalty * weather_penalty * 
        np.random.normal(1, 0.1, n_samples)  # Add noise
    )
    
    # Derive risk category from features
    risk_score = (
        (df['geopolitical_risk_score'] / 10) * 0.3 +
        (df['weather_risk_index'] / 10) * 0.2 +
        (df['shipment_anomaly_score']) * 0.2 +
        ((100 - df['financial_health_score']) / 100) * 0.3
    )
    
    df['risk_category'] = pd.cut(
        risk_score, 
        bins=[0, 0.3, 0.6, 1.0], 
        labels=['Low', 'Medium', 'High']
    )
    
    return df


def generate_shipment_data(n_samples=500, contamination=0.1, seed=42):
    """
    Generate synthetic shipment data for anomaly detection
    
    Args:
        n_samples: Number of shipment records
        contamination: Proportion of anomalies (default 10%)
        seed: Random seed
        
    Returns:
        DataFrame with shipment features and anomaly labels
    """
    np.random.seed(seed)
    
    n_anomalies = int(n_samples * contamination)
    n_normal = n_samples - n_anomalies
    
    # Generate normal shipments
    normal_data = {
        'shipment_id': [f"SHIP{str(i).zfill(5)}" for i in range(1, n_normal + 1)],
        'price_spike_percentage': np.abs(np.random.normal(0, 5, n_normal)),
        'delivery_delay_days': np.clip(np.random.exponential(1, n_normal), 0, 10),
        'sentiment_score': np.random.normal(0.2, 0.2, n_normal),
        'weather_disruption_index': np.random.beta(2, 8, n_normal) * 10,
        'geopolitical_event_flag': np.random.binomial(1, 0.05, n_normal),
        'quality_deviation': np.abs(np.random.normal(0, 3, n_normal)),
        'is_anomaly': np.zeros(n_normal, dtype=int)
    }
    
    # Generate anomalous shipments (more extreme values)
    anomaly_data = {
        'shipment_id': [f"SHIP{str(i).zfill(5)}" for i in range(n_normal + 1, n_samples + 1)],
        'price_spike_percentage': np.abs(np.random.normal(25, 15, n_anomalies)),
        'delivery_delay_days': np.clip(np.random.exponential(8, n_anomalies), 5, 30),
        'sentiment_score': np.random.normal(-0.5, 0.3, n_anomalies),
        'weather_disruption_index': np.random.beta(8, 2, n_anomalies) * 10,
        'geopolitical_event_flag': np.random.binomial(1, 0.6, n_anomalies),
        'quality_deviation': np.abs(np.random.normal(15, 10, n_anomalies)),
        'is_anomaly': np.ones(n_anomalies, dtype=int)
    }
    
    # Combine and shuffle
    normal_df = pd.DataFrame(normal_data)
    anomaly_df = pd.DataFrame(anomaly_data)
    df = pd.concat([normal_df, anomaly_df], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Clip sentiment scores
    df['sentiment_score'] = np.clip(df['sentiment_score'], -1, 1)
    
    return df


def generate_transaction_data(n_samples=10000, fraud_rate=0.01, seed=42):
    """
    Generate synthetic transaction data for fraud detection
    
    Args:
        n_samples: Number of transaction records
        fraud_rate: Proportion of fraudulent transactions (default 1%)
        seed: Random seed
        
    Returns:
        DataFrame with transaction features and fraud labels
    """
    np.random.seed(seed)
    
    n_fraud = int(n_samples * fraud_rate)
    n_legitimate = n_samples - n_fraud
    
    # Device types and merchant categories
    device_types = ['Desktop', 'Mobile', 'API', 'Tablet']
    merchant_categories = ['Electronics', 'Raw Materials', 'Services', 'Equipment', 'Supplies']
    
    # Generate legitimate transactions
    legitimate_data = {
        'transaction_id': [f"TXN{str(i).zfill(6)}" for i in range(1, n_legitimate + 1)],
        
        # Transaction amount (log-normal, mean=$5000)
        'transaction_amount': np.random.lognormal(mean=8.5, sigma=0.8, size=n_legitimate),
        
        # Supplier age in days (uniform, 30-3650 days)
        'supplier_age_days': np.random.uniform(30, 3650, n_legitimate),
        
        # Transaction hour (normal around business hours)
        'transaction_hour': np.clip(np.random.normal(13, 4, n_legitimate), 0, 23).astype(int),
        
        # Device type (mostly desktop for legitimate)
        'device_type': np.random.choice(device_types, n_legitimate, p=[0.6, 0.25, 0.1, 0.05]),
        
        # Merchant category
        'merchant_category': np.random.choice(merchant_categories, n_legitimate),
        
        # Historical fraud count (mostly 0 for legitimate)
        'historical_fraud_count': np.random.poisson(0.1, n_legitimate),
        
        # Amount deviation from average (small for legitimate)
        'amount_deviation_from_avg': np.abs(np.random.normal(0, 15, n_legitimate)),
        
        # Transaction frequency last 24h (normal activity)
        'transaction_frequency_last_24h': np.random.poisson(2, n_legitimate),
        
        # IP country match (high match for legitimate)
        'ip_country_match': np.random.binomial(1, 0.95, n_legitimate),
        
        'is_fraud': np.zeros(n_legitimate, dtype=int)
    }
    
    # Generate fraudulent transactions (more suspicious patterns)
    fraud_data = {
        'transaction_id': [f"TXN{str(i).zfill(6)}" for i in range(n_legitimate + 1, n_samples + 1)],
        
        # Higher amounts for fraud
        'transaction_amount': np.random.lognormal(mean=9.5, sigma=1.2, size=n_fraud),
        
        # Newer suppliers for fraud
        'supplier_age_days': np.random.uniform(1, 180, n_fraud),
        
        # Odd hours for fraud
        'transaction_hour': np.random.choice([0, 1, 2, 3, 22, 23], n_fraud),
        
        # More API/Mobile for fraud
        'device_type': np.random.choice(device_types, n_fraud, p=[0.2, 0.3, 0.4, 0.1]),
        
        # Merchant category
        'merchant_category': np.random.choice(merchant_categories, n_fraud),
        
        # Higher historical fraud
        'historical_fraud_count': np.random.poisson(2, n_fraud),
        
        # Large deviation for fraud
        'amount_deviation_from_avg': np.abs(np.random.normal(50, 30, n_fraud)),
        
        # High frequency for fraud
        'transaction_frequency_last_24h': np.random.poisson(8, n_fraud),
        
        # Low IP match for fraud
        'ip_country_match': np.random.binomial(1, 0.2, n_fraud),
        
        'is_fraud': np.ones(n_fraud, dtype=int)
    }
    
    # Combine and shuffle
    legitimate_df = pd.DataFrame(legitimate_data)
    fraud_df = pd.DataFrame(fraud_data)
    df = pd.concat([legitimate_df, fraud_df], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    
    return df


def generate_route_data(n_routes=5, seed=42):
    """
    Generate synthetic route options for optimization
    
    Args:
        n_routes: Number of alternative routes
        seed: Random seed
        
    Returns:
        DataFrame with route features and scores
    """
    np.random.seed(seed)
    
    route_names = [f"Route {chr(65+i)}" for i in range(n_routes)]
    
    data = {
        'route_name': route_names,
        'distance_km': np.random.uniform(200, 800, n_routes),
        'fuel_cost_per_km': np.random.uniform(0.8, 1.5, n_routes),
        'traffic_index': np.random.uniform(0.3, 0.9, n_routes),  # 0=clear, 1=heavy
        'weather_risk': np.random.uniform(0, 0.7, n_routes),
        'geopolitical_risk': np.random.uniform(0, 0.5, n_routes),
        'estimated_delay_hours': np.random.uniform(0, 8, n_routes),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate total cost and risk score
    df['total_fuel_cost'] = df['distance_km'] * df['fuel_cost_per_km']
    df['total_time_hours'] = (df['distance_km'] / 80) * (1 + df['traffic_index']) + df['estimated_delay_hours']
    
    # Risk score (0-1, lower is better)
    df['risk_score'] = (
        df['weather_risk'] * 0.4 +
        df['geopolitical_risk'] * 0.4 +
        df['traffic_index'] * 0.2
    )
    
    # Overall score (lower is better, weighted combination)
    df['overall_score'] = (
        (df['total_fuel_cost'] / df['total_fuel_cost'].max()) * 0.3 +
        (df['total_time_hours'] / df['total_time_hours'].max()) * 0.3 +
        df['risk_score'] * 0.4
    )
    
    return df.sort_values('overall_score')


if __name__ == '__main__':
    # Test data generation
    print("Generating supplier data...")
    supplier_df = generate_supplier_data(100)
    print(f"Generated {len(supplier_df)} supplier records")
    print(supplier_df.head())
    
    print("\nGenerating shipment data...")
    shipment_df = generate_shipment_data(50)
    print(f"Generated {len(shipment_df)} shipment records")
    print(f"Anomalies: {shipment_df['is_anomaly'].sum()}")
    
    print("\nGenerating transaction data...")
    transaction_df = generate_transaction_data(1000)
    print(f"Generated {len(transaction_df)} transaction records")
    print(f"Fraudulent: {transaction_df['is_fraud'].sum()}")
    
    print("\nGenerating route data...")
    route_df = generate_route_data(5)
    print(f"Generated {len(route_df)} route options")
    print(route_df[['route_name', 'overall_score', 'risk_score']])

def generate_epa_emission_data(n_samples=2000, seed=42):
    """
    Generate synthetic EPA Greenhouse Gas Emission Factors dataset (2010-2016)
    
    Args:
        n_samples: Number of records (research uses 2,000)
        seed: Random seed
        
    Returns:
        DataFrame following the EPA USEEIO structure
    """
    np.random.seed(seed)
    
    industries = [
        'Electronic Manufacturing', 'Food Processing', 'Textile Mills', 
        'Chemical Manufacturing', 'Steel Production', 'Paper Mills',
        'Agriculture', 'Construction', 'Transportation Services',
        'Health Care', 'Retail Trade', 'Utilities'
    ]
    
    commodities = [
        'Semiconductors', 'Dairy Products', 'Grains', 
        'Basic Chemicals', 'Fabricated Metal', 'Newsprint',
        'Beef Cattle', 'Commercial Buildings', 'Truck Transportation',
        'Hospital Services', 'General Merchandise', 'Electric Power'
    ]

    data = {
        'year': np.random.randint(2010, 2017, n_samples),
        'industry': np.random.choice(industries, n_samples),
        'commodity': np.random.choice(commodities, n_samples),
        
        # Emission factors (kg CO2e / $) 
        # Research cites cradle-to-factory gate vs factory gate-to-shelf
        'emission_factor_no_margins': np.random.lognormal(mean=-2, sigma=0.8, size=n_samples),
        'margins_factor': np.random.lognormal(mean=-3, sigma=0.5, size=n_samples),
        
        # Data Quality scores (DQDQ) - 1 to 5, where 1 is best (counter-intuitive but common in EPA)
        # We'll use 1-5 scale
        'reliability': np.random.randint(1, 6, n_samples),
        'temporal_correlation': np.random.randint(1, 6, n_samples),
        'geographical_correlation': np.random.randint(1, 6, n_samples),
        'technological_correlation': np.random.randint(1, 6, n_samples),
        'completeness': np.random.randint(1, 6, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Calculate 'with margins' (total)
    df['emission_factor_with_margins'] = df['emission_factor_no_margins'] + df['margins_factor']
    
    # Add some noise/relationships for Random Forest to learn
    # e.g., Steel and Chemicals have higher emissions
    carbon_intensive = ['Steel Production', 'Chemical Manufacturing', 'Utilities', 'Transportation Services']
    mask = df['industry'].isin(carbon_intensive)
    df.loc[mask, 'emission_factor_with_margins'] *= np.random.uniform(2, 5, mask.sum())
    
    return df
