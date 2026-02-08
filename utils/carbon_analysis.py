import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from typing import Dict, List, Tuple
from .data_generators import generate_epa_emission_data

class CarbonEmissionPredictor:
    """
    Predicts Greenhouse Gas Emission Factors using Random Forest
    Based on Section 3.2.1 of the research paper.
    """
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.feature_names = []
        self.industry_map = {}
        self.commodity_map = {}

    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        # Encode categorical variables
        df_encoded = df.copy()
        
        # Simple label encoding for demo purposes
        if not self.industry_map:
            self.industry_map = {name: i for i, name in enumerate(df['industry'].unique())}
            self.commodity_map = {name: i for i, name in enumerate(df['commodity'].unique())}
            
        df_encoded['industry_idx'] = df['industry'].map(self.industry_map)
        df_encoded['commodity_idx'] = df['commodity'].map(self.commodity_map)
        
        # Features: Industry, Commodity, Year, and Quality Scores (DQDQ)
        features = [
            'industry_idx', 'commodity_idx', 'year',
            'reliability', 'temporal_correlation', 'geographical_correlation',
            'technological_correlation', 'completeness'
        ]
        self.feature_names = features
        
        X = df_encoded[features].values
        y = df_encoded['emission_factor_with_margins'].values
        
        return X, y

    def train(self, df: pd.DataFrame = None) -> Dict:
        if df is None:
            df = generate_epa_emission_data(2000)
            
        X, y = self.prepare_data(df)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Feature Importance
        importances = dict(zip(self.feature_names, self.model.feature_importances_.tolist()))
        
        return {
            'mse': float(mse),
            'r2': float(r2),
            'feature_importance': importances,
            'train_size': len(X_train),
            'test_size': len(X_test)
        }

    def predict_emissions(self, industry: str, year: int, amount_usd: float) -> Dict:
        """Predict emissions for a specific operation"""
        if not self.is_trained:
            self.train()
            
        # Default quality scores (middle-ground)
        reliability = 3
        temporal = 3
        geo = 3
        tech = 3
        comp = 3
        
        # Map industry and commodity (use first commodity for that industry)
        industry_idx = self.industry_map.get(industry, 0)
        # Find a typical commodity index for this industry from the map (approximation)
        commodity_idx = 0 
        
        input_data = np.array([[
            industry_idx, commodity_idx, year,
            reliability, temporal, geo, tech, comp
        ]])
        
        # Predicted factor (kg CO2e / $)
        emission_factor = self.model.predict(input_data)[0]
        total_emissions = emission_factor * amount_usd
        
        return {
            'industry': industry,
            'year': year,
            'amount_usd': amount_usd,
            'emission_factor': float(emission_factor),
            'total_kg_co2e': float(total_emissions)
        }

    def scenario_analysis(self, current_config: Dict, sustainable_config: Dict) -> Dict:
        """
        Compare current supply chain vs a more sustainable version
        current_config: {'revenue': 1M, 'sectors': [{'name': 'Utilities', 'spend': 200k}, ...]}
        """
        results = {'current': {}, 'sustainable': {}}
        
        def calculate_impact(config):
            total_emissions = 0
            sector_breakdown = []
            for sector in config['sectors']:
                pred = self.predict_emissions(sector['name'], 2024, sector['spend'])
                total_emissions += pred['total_kg_co2e']
                sector_breakdown.append({
                    'name': sector['name'],
                    'emissions': pred['total_kg_co2e'],
                    'intensity': pred['emission_factor']
                })
            
            # Sustainability-Adjusted Growth Score (revenue / emissions_intensity)
            # Higher is better
            intensity = total_emissions / config['revenue']
            growth_score = (config['revenue'] / 1000000) * (1 / intensity) if intensity > 0 else 0
            
            return {
                'total_emissions': total_emissions,
                'intensity': intensity,
                'growth_score': growth_score,
                'sector_breakdown': sector_breakdown
            }

        results['current'] = calculate_impact(current_config)
        results['sustainable'] = calculate_impact(sustainable_config)
        
        # Calculate reduction %
        reduction = (results['current']['total_emissions'] - results['sustainable']['total_emissions']) / results['current']['total_emissions']
        results['reduction_percent'] = float(reduction * 100)
        
        return results

    def get_industry_benchmarks(self) -> List[Dict]:
        """Return average emission factors per industry for comparison"""
        if not self.is_trained:
            self.train()
            
        benchmarks = []
        for industry, idx in self.industry_map.items():
            # Use mid-range scores and 2024 for baseline
            input_data = np.array([[idx, 0, 2024, 3, 3, 3, 3, 3]])
            factor = self.model.predict(input_data)[0]
            benchmarks.append({
                'industry': industry,
                'average_factor': float(factor)
            })
            
        return sorted(benchmarks, key=lambda x: x['average_factor'], reverse=True)
