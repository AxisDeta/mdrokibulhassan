"""
Inventory Analysis Utilities
Provides comprehensive inventory optimization analysis including:
- Historical demand analysis
- Forecasting (ETS + LightGBM)
- Inventory policy optimization (s,S)
- Inventory simulation
- Model explainability (SHAP + surrogate models)
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import lightgbm as lgb
from sklearn.linear_model import LinearRegression
import shap
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class InventoryAnalyzer:
    """
    Comprehensive inventory analysis for a single SKU
    """
    
    def __init__(self, sku_df: pd.DataFrame):
        """
        Initialize analyzer with SKU data
        
        Args:
            sku_df: DataFrame with columns: date, demand, sell_price, and optional lag features
        """
        self.sku_df = sku_df.copy()
        self.sku_df['date'] = pd.to_datetime(self.sku_df['date'])
        self.sku_df = self.sku_df.sort_values('date').reset_index(drop=True)
        
        # Cache for trained models
        self.lgb_model = None
        self.feature_cols = ["lag_1", "lag_7", "lag_14", "rmean_7", "rmean_14", "rstd_7"]
        
    def historical_analysis(self) -> Dict:
        """
        Analyze historical demand patterns
        
        Returns:
            Dictionary containing:
            - stats: Basic statistics (mean, median, std, min, max)
            - quantiles: Percentile values
            - distribution: Skewness and kurtosis
            - time_series: Date and demand arrays for plotting
        """
        demand = self.sku_df['demand']
        
        return {
            'stats': {
                'mean': float(demand.mean()),
                'median': float(demand.median()),
                'std': float(demand.std()),
                'min': float(demand.min()),
                'max': float(demand.max()),
                'variance': float(demand.var())
            },
            'quantiles': {
                'q25': float(demand.quantile(0.25)),
                'q50': float(demand.quantile(0.50)),
                'q75': float(demand.quantile(0.75)),
                'q90': float(demand.quantile(0.90)),
                'q95': float(demand.quantile(0.95))
            },
            'distribution': {
                'skewness': float(demand.skew()),
                'kurtosis': float(demand.kurtosis())
            },
            'time_series': {
                'dates': self.sku_df['date'].dt.strftime('%Y-%m-%d').tolist(),
                'demand': demand.tolist()
            },
            'total_days': len(self.sku_df),
            'date_range': {
                'start': self.sku_df['date'].min().strftime('%Y-%m-%d'),
                'end': self.sku_df['date'].max().strftime('%Y-%m-%d')
            }
        }
    
    def forecast_ets(self, forecast_days: int = 28) -> Dict:
        """
        Exponential Smoothing (ETS) forecast
        
        Args:
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with predictions, metrics, and visualization data
        """
        try:
            # Split data
            train = self.sku_df["demand"][:-forecast_days]
            test = self.sku_df["demand"][-forecast_days:]
            train_dates = self.sku_df["date"][:-forecast_days]
            test_dates = self.sku_df["date"][-forecast_days:]
            
            # Train ETS model
            ets = ExponentialSmoothing(
                train,
                trend="add",
                seasonal="add",
                seasonal_periods=7
            )
            ets_fit = ets.fit()
            ets_forecast = ets_fit.forecast(len(test))
            
            # Calculate metrics
            mae = float(np.mean(np.abs(test.values - ets_forecast)))
            rmse = float(np.sqrt(np.mean((test.values - ets_forecast) ** 2)))
            mape = float(np.mean(np.abs((test.values - ets_forecast) / (test.values + 1))) * 100)
            
            # Prepare visualization data (last 180 days of training + forecast)
            display_days = min(180, len(train))
            train_display = train.iloc[-display_days:]
            train_dates_display = train_dates.iloc[-display_days:]
            
            return {
                'success': True,
                'metrics': {
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape
                },
                'visualization': {
                    'train_dates': train_dates_display.dt.strftime('%Y-%m-%d').tolist(),
                    'train_values': train_display.tolist(),
                    'test_dates': test_dates.dt.strftime('%Y-%m-%d').tolist(),
                    'test_actual': test.tolist(),
                    'test_forecast': ets_forecast.tolist()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'ETS model requires sufficient data with seasonality. Try a different SKU or adjust parameters.'
            }
    
    def _create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create lag and rolling features for ML model"""
        df = df.copy()
        df["lag_1"] = df["demand"].shift(1)
        df["lag_7"] = df["demand"].shift(7)
        df["lag_14"] = df["demand"].shift(14)
        df["rmean_7"] = df["demand"].rolling(7).mean()
        df["rmean_14"] = df["demand"].rolling(14).mean()
        df["rstd_7"] = df["demand"].rolling(7).std()
        return df.dropna()
    
    def forecast_lightgbm(self, forecast_days: int = 28) -> Dict:
        """
        LightGBM machine learning forecast
        
        Args:
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary with predictions, metrics, feature importance, and next-day prediction
        """
        try:
            # Create features
            feat_df = self._create_features(self.sku_df)
            
            if len(feat_df) < 50:
                return {
                    'success': False,
                    'error': 'Insufficient data',
                    'message': 'Need at least 50 observations after feature engineering.'
                }
            
            # Split data
            train_feat = feat_df.iloc[:-forecast_days] if len(feat_df) > forecast_days else feat_df.iloc[:-28]
            test_feat = feat_df.iloc[-forecast_days:] if len(feat_df) > forecast_days else feat_df.iloc[-28:]
            
            X_train = train_feat[self.feature_cols]
            y_train = train_feat["demand"]
            X_test = test_feat[self.feature_cols]
            y_test = test_feat["demand"]
            
            # Train LightGBM
            self.lgb_model = lgb.LGBMRegressor(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=5,
                random_state=42,
                verbose=-1
            )
            self.lgb_model.fit(X_train, y_train)
            
            # Make predictions
            lgb_predictions = self.lgb_model.predict(X_test)
            
            # Calculate metrics
            mae = float(np.mean(np.abs(y_test.values - lgb_predictions)))
            rmse = float(np.sqrt(np.mean((y_test.values - lgb_predictions) ** 2)))
            mape = float(np.mean(np.abs((y_test.values - lgb_predictions) / (y_test.values + 1))) * 100)
            
            # Next-day prediction
            X_full = feat_df[self.feature_cols]
            next_day_pred = float(self.lgb_model.predict(X_full.iloc[-1:].values)[0])
            
            # Feature importance
            feature_importance = {
                'features': self.feature_cols,
                'importances': self.lgb_model.feature_importances_.tolist()
            }
            
            return {
                'success': True,
                'metrics': {
                    'mae': mae,
                    'rmse': rmse,
                    'mape': mape,
                    'next_day_forecast': next_day_pred
                },
                'visualization': {
                    'test_indices': list(range(len(y_test))),
                    'test_actual': y_test.tolist(),
                    'test_forecast': lgb_predictions.tolist()
                },
                'feature_importance': feature_importance
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'LightGBM training failed: {str(e)}'
            }
    
    def calculate_inventory_policy(self, lead_time: int = 7, service_level: float = 0.95) -> Dict:
        """
        Calculate (s, S) inventory policy parameters
        
        Args:
            lead_time: Days between ordering and receiving products
            service_level: Target service level (0.80 to 0.99)
            
        Returns:
            Dictionary with s, S, safety stock, and visualization data
        """
        # Calculate demand statistics
        mu = float(self.sku_df["demand"].mean())
        sigma = float(self.sku_df["demand"].std())
        
        # Z-score mapping for service levels
        z_map = {
            0.80: 0.84,
            0.85: 1.04,
            0.90: 1.28,
            0.95: 1.65,
            0.975: 1.96,
            0.99: 2.33
        }
        z = z_map[min(z_map.keys(), key=lambda x: abs(x - service_level))]
        
        # Calculate policy parameters
        safety_stock = z * sigma * np.sqrt(lead_time)
        s = mu * lead_time + safety_stock  # Reorder point
        S = s + mu * lead_time  # Order-up-to level
        
        # Simulate inventory for visualization
        np.random.seed(42 + int(lead_time) + int(service_level * 100))
        days = 90
        inventory = [S]
        for i in range(days - 1):
            daily_demand = max(0, np.random.normal(mu, sigma))
            new_inventory = inventory[-1] - daily_demand
            if new_inventory <= s:
                new_inventory = S
            inventory.append(new_inventory)
        
        return {
            'parameters': {
                's': int(s),
                'S': int(S),
                'safety_stock': int(safety_stock),
                'expected_lead_time_demand': int(mu * lead_time),
                'avg_order_quantity': int(S - s)
            },
            'inputs': {
                'lead_time': lead_time,
                'service_level': service_level,
                'mu': mu,
                'sigma': sigma
            },
            'visualization': {
                'inventory_levels': inventory,
                'days': list(range(days))
            }
        }
    
    def simulate_inventory(self, s: float, S: float, lead_time: int, sim_days: int = 90) -> Dict:
        """
        Simulate inventory performance with given policy
        
        Args:
            s: Reorder point
            S: Order-up-to level
            lead_time: Lead time in days
            sim_days: Simulation period
            
        Returns:
            Dictionary with simulation results and metrics
        """
        mu = float(self.sku_df["demand"].mean())
        sigma = float(self.sku_df["demand"].std())
        
        # Set seed for reproducibility
        sim_seed = 42 + int(lead_time) + int(s) + sim_days
        np.random.seed(sim_seed)
        
        # Generate demand (synthetic)
        sim_demand = np.maximum(0, np.random.normal(mu, sigma, sim_days))
        
        # Run simulation
        inventory = [S]
        orders = []
        stockouts = []
        pending_orders = []  # (arrival_day, quantity)
        
        for i, d in enumerate(sim_demand):
            # Start with previous inventory
            current_inv = inventory[-1]
            
            # Receive pending orders
            arrived_qty = sum([qty for arrival_day, qty in pending_orders if arrival_day == i])
            if arrived_qty > 0:
                current_inv = min(current_inv + arrived_qty, S)
                pending_orders = [(day, qty) for day, qty in pending_orders if day != i]
            
            # Subtract demand
            current_inv = current_inv - d
            
            # Check for stockout
            if current_inv < 0:
                stockouts.append(i)
                current_inv = 0
            
            # Check if reorder needed
            has_pending = len(pending_orders) > 0
            if current_inv <= s and not has_pending:
                order_qty = S - current_inv
                orders.append((i, order_qty))
                if lead_time > 0:
                    arrival_day = i + lead_time
                    pending_orders.append((arrival_day, order_qty))
                else:
                    current_inv = S
            
            inventory.append(current_inv)
        
        # Remove last inventory value (extra from loop)
        inventory = inventory[:-1]
        
        # Calculate metrics
        total_stockouts = len(stockouts)
        stockout_rate = total_stockouts / len(sim_demand) * 100
        service_level_actual = (len(sim_demand) - total_stockouts) / len(sim_demand) * 100
        avg_order = np.mean([o[1] for o in orders]) if orders else 0
        
        return {
            'metrics': {
                'total_stockouts': total_stockouts,
                'stockout_rate': float(stockout_rate),
                'service_level_achieved': float(service_level_actual),
                'total_orders': len(orders),
                'avg_order_size': float(avg_order),
                'total_demand': float(np.sum(sim_demand)),
                'avg_daily_demand': float(np.mean(sim_demand)),
                'avg_inventory_level': float(np.mean(inventory))
            },
            'visualization': {
                'inventory_levels': inventory,
                'demand': sim_demand.tolist(),
                'days': list(range(len(inventory))),
                'stockout_days': stockouts,
                'order_days': [o[0] for o in orders],
                'order_levels': [inventory[o[0]] for o in orders],
                's': s,
                'S': S,
                'mu': mu
            }
        }
    
    def explain_model(self) -> Dict:
        """
        Generate model explainability using SHAP and surrogate models
        
        Returns:
            Dictionary with SHAP values, surrogate model, and coefficients
        """
        if self.lgb_model is None:
            return {
                'success': False,
                'error': 'No trained model',
                'message': 'Run LightGBM forecast first to train a model.'
            }
        
        try:
            # Prepare data
            feat_df = self._create_features(self.sku_df)
            X_full = feat_df[self.feature_cols]
            
            # Sample for SHAP (to speed up computation)
            sample_size = min(200, len(X_full))
            sample_X = X_full.sample(sample_size, random_state=42)
            
            # Calculate SHAP values
            explainer = shap.TreeExplainer(self.lgb_model)
            shap_values = explainer.shap_values(sample_X)
            
            # Get mean absolute SHAP values for feature importance
            shap_importance = np.abs(shap_values).mean(axis=0)
            
            # Train surrogate linear model
            lin = LinearRegression()
            lin.fit(X_full, self.lgb_model.predict(X_full))
            r2_score = float(lin.score(X_full, self.lgb_model.predict(X_full)))
            
            # Get predictions for comparison
            ml_pred = self.lgb_model.predict(X_full)
            surrogate_pred = lin.predict(X_full)
            
            return {
                'success': True,
                'shap': {
                    'feature_names': self.feature_cols,
                    'importance': shap_importance.tolist(),
                    'values': shap_values.tolist(),
                    'sample_features': sample_X.values.tolist()
                },
                'surrogate': {
                    'intercept': float(lin.intercept_),
                    'coefficients': {
                        name: float(coef) 
                        for name, coef in zip(self.feature_cols, lin.coef_)
                    },
                    'r2_score': r2_score,
                    'formula_parts': [
                        {'feature': name, 'coefficient': float(coef)}
                        for name, coef in zip(self.feature_cols, lin.coef_)
                    ]
                },
                'comparison': {
                    'ml_predictions': ml_pred.tolist()[:100],  # Limit for JSON size
                    'surrogate_predictions': surrogate_pred.tolist()[:100]
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Explainability analysis failed: {str(e)}'
            }


def load_sku_data(sku_id: str, csv_path: str = 'data/inventory/sku_timeseries.csv') -> pd.DataFrame:
    """
    Load data for a specific SKU
    
    Args:
        sku_id: SKU identifier
        csv_path: Path to CSV file
        
    Returns:
        DataFrame filtered for the specified SKU
    """
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    sku_df = df[df['id'] == sku_id].sort_values('date').reset_index(drop=True)
    return sku_df


def get_available_skus(csv_path: str = 'data/inventory/sku_timeseries.csv') -> List[str]:
    """
    Get list of available SKUs from the dataset
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of SKU identifiers
    """
    df = pd.read_csv(csv_path)
    return sorted(df['id'].unique().tolist())
