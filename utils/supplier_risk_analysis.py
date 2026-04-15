"""
Supplier Risk Analysis Module
Implements 4 core components:
1. Risk Forecasting (4 ML models)
2. Anomaly Detection (Isolation Forest)
3. Route Optimization (Heuristic-based)
4. Fraud Detection (Deep Neural Network)
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, confusion_matrix
from sklearn.neural_network import MLPRegressor
from imblearn.over_sampling import SMOTE
import xgboost as xgb
# TensorFlow is imported lazily in detect_fraud() to avoid slow server restarts
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')



class SupplierRiskAnalyzer:
    """Main class for supplier risk assessment and analysis"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.models = {}
        self.fraud_model = None
        
    def train_forecasting_models(self, df: pd.DataFrame) -> Dict:
        """
        Train 4 regression models for demand forecasting
        
        Args:
            df: DataFrame with supplier features and future_demand target
            
        Returns:
            Dictionary with model results and metrics
        """
        # Prepare features and target
        feature_cols = [
            'historical_demand', 'delivery_performance', 'financial_health_score',
            'geopolitical_risk_score', 'weather_risk_index', 'price_volatility',
            'shipment_anomaly_score', 'news_sentiment_score', 'lead_time_days',
            'quality_score', 'contract_compliance'
        ]
        
        X = df[feature_cols].values
        y = df['future_demand'].values
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        results = {
            'models': {},
            'feature_names': feature_cols,
            'test_actual': y_test.tolist(),
            'test_indices': list(range(len(y_test)))
        }
        
        # 1. Linear Regression
        lr = LinearRegression()
        lr.fit(X_train_scaled, y_train)
        lr_pred = lr.predict(X_test_scaled)
        
        results['models']['Linear Regression'] = {
            'mae': float(mean_absolute_error(y_test, lr_pred)),
            'mse': float(mean_squared_error(y_test, lr_pred)),
            'r2': float(r2_score(y_test, lr_pred)),
            'predictions': lr_pred.tolist(),
            'feature_importance': {
                'features': feature_cols,
                'importances': np.abs(lr.coef_).tolist()
            }
        }
        
        # 2. Random Forest Regressor
        rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        rf_pred = rf.predict(X_test)
        
        results['models']['Random Forest'] = {
            'mae': float(mean_absolute_error(y_test, rf_pred)),
            'mse': float(mean_squared_error(y_test, rf_pred)),
            'r2': float(r2_score(y_test, rf_pred)),
            'predictions': rf_pred.tolist(),
            'feature_importance': {
                'features': feature_cols,
                'importances': rf.feature_importances_.tolist()
            }
        }
        
        # 3. XGBoost Regressor
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        xgb_model.fit(X_train, y_train)
        xgb_pred = xgb_model.predict(X_test)
        
        results['models']['XGBoost'] = {
            'mae': float(mean_absolute_error(y_test, xgb_pred)),
            'mse': float(mean_squared_error(y_test, xgb_pred)),
            'r2': float(r2_score(y_test, xgb_pred)),
            'predictions': xgb_pred.tolist(),
            'feature_importance': {
                'features': feature_cols,
                'importances': xgb_model.feature_importances_.tolist()
            }
        }
        
        # 4. Multi-Layer Perceptron
        mlp = MLPRegressor(
            hidden_layer_sizes=(64, 32, 16),
            activation='relu',
            max_iter=500,
            random_state=42,
            early_stopping=True
        )
        mlp.fit(X_train_scaled, y_train)
        mlp_pred = mlp.predict(X_test_scaled)
        
        results['models']['MLP'] = {
            'mae': float(mean_absolute_error(y_test, mlp_pred)),
            'mse': float(mean_squared_error(y_test, mlp_pred)),
            'r2': float(r2_score(y_test, mlp_pred)),
            'predictions': mlp_pred.tolist(),
            'feature_importance': None  # MLP doesn't have direct feature importance
        }
        
        # Find best model
        best_model_name = min(
            results['models'].keys(),
            key=lambda k: results['models'][k]['mae']
        )
        results['best_model'] = best_model_name

        model_lookup = {
            'Linear Regression': ('lr', True),
            'Random Forest': ('rf', False),
            'XGBoost': ('xgb', False),
            'MLP': ('mlp', True)
        }
        selected_key, use_scaled = model_lookup[best_model_name]
        full_features = self.scaler.transform(X) if use_scaled else X
        full_predictions = self.models.get('forecasting', {}).get(selected_key)
        if full_predictions is None:
            full_predictions = lr if selected_key == 'lr' else rf if selected_key == 'rf' else xgb_model if selected_key == 'xgb' else mlp
        projected_demand = full_predictions.predict(full_features)

        supplier_view = df[['supplier_id', 'future_demand', 'risk_category', 'lead_time_days', 'delivery_performance']].copy()
        supplier_view['projected_demand'] = projected_demand
        supplier_view['priority_score'] = (
            (df['geopolitical_risk_score'] / 10) * 0.3 +
            (df['weather_risk_index'] / 10) * 0.2 +
            df['shipment_anomaly_score'] * 0.2 +
            ((100 - df['financial_health_score']) / 100) * 0.3
        ) * projected_demand

        top_suppliers = (
            supplier_view.sort_values('priority_score', ascending=False)
            .head(8)
            .to_dict('records')
        )

        risk_counts = df['risk_category'].value_counts().to_dict()
        results['business_view'] = {
            'projected_total_demand': float(np.sum(projected_demand)),
            'average_projected_demand': float(np.mean(projected_demand)),
            'high_risk_suppliers': int(risk_counts.get('High', 0)),
            'medium_risk_suppliers': int(risk_counts.get('Medium', 0)),
            'low_risk_suppliers': int(risk_counts.get('Low', 0)),
            'top_suppliers': [
                {
                    'supplier_id': row['supplier_id'],
                    'risk_category': str(row['risk_category']),
                    'projected_demand': float(row['projected_demand']),
                    'lead_time_days': float(row['lead_time_days']),
                    'delivery_performance': float(row['delivery_performance'])
                }
                for row in top_suppliers
            ]
        }
        
        # Store models
        self.models['forecasting'] = {
            'lr': lr,
            'rf': rf,
            'xgb': xgb_model,
            'mlp': mlp
        }
        
        return results
    
    def detect_anomalies(self, df: pd.DataFrame, contamination: float = 0.1) -> Dict:
        """
        Detect anomalies using Isolation Forest
        
        Args:
            df: DataFrame with shipment features
            contamination: Expected proportion of anomalies
            
        Returns:
            Dictionary with anomaly detection results
        """
        feature_cols = [
            'price_spike_percentage', 'delivery_delay_days', 'sentiment_score',
            'weather_disruption_index', 'geopolitical_event_flag', 'quality_deviation'
        ]
        
        X = df[feature_cols].values
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        
        # Predict anomalies (-1 for anomalies, 1 for normal)
        predictions = iso_forest.fit_predict(X)
        anomaly_scores = iso_forest.score_samples(X)
        
        # Convert predictions to binary (1 for anomaly, 0 for normal)
        anomaly_labels = (predictions == -1).astype(int)
        
        # Calculate metrics if ground truth available
        metrics = {}
        if 'is_anomaly' in df.columns:
            true_labels = df['is_anomaly'].values
            metrics = {
                'accuracy': float(accuracy_score(true_labels, anomaly_labels)),
                'precision': float(precision_score(true_labels, anomaly_labels, zero_division=0)),
                'recall': float(recall_score(true_labels, anomaly_labels, zero_division=0)),
                'detected_anomalies': int(anomaly_labels.sum()),
                'true_anomalies': int(true_labels.sum())
            }
        else:
            metrics = {
                'detected_anomalies': int(anomaly_labels.sum())
            }
        
        # Feature contribution analysis (approximate)
        feature_importance = np.abs(X[anomaly_labels == 1].mean(axis=0) - X[anomaly_labels == 0].mean(axis=0))
        feature_importance = feature_importance / feature_importance.sum()
        
        results = {
            'metrics': metrics,
            'anomaly_labels': anomaly_labels.tolist(),
            'anomaly_scores': anomaly_scores.tolist(),
            'feature_importance': {
                'features': feature_cols,
                'importances': feature_importance.tolist()
            },
            'data': {
                'features': X.tolist(),
                'feature_names': feature_cols
            },
            'top_alerts': (
                df.assign(anomaly_label=anomaly_labels, anomaly_score=anomaly_scores)
                .loc[lambda frame: frame['anomaly_label'] == 1]
                .sort_values('anomaly_score')
                .head(10)[[
                    'shipment_id',
                    'price_spike_percentage',
                    'delivery_delay_days',
                    'weather_disruption_index',
                    'geopolitical_event_flag'
                ]]
                .to_dict('records')
            )
        }
        
        self.models['anomaly'] = iso_forest
        
        return results
    
    def optimize_routes(self, route_df: pd.DataFrame) -> Dict:
        """
        Optimize routes using heuristic scoring
        
        Args:
            route_df: DataFrame with route options and features
            
        Returns:
            Dictionary with route recommendations
        """
        # Calculate comprehensive scores if not already present
        if 'overall_score' not in route_df.columns:
            # Normalize metrics
            route_df['fuel_cost_norm'] = (
                route_df['total_fuel_cost'] / route_df['total_fuel_cost'].max()
            )
            route_df['time_norm'] = (
                route_df['total_time_hours'] / route_df['total_time_hours'].max()
            )
            
            # Calculate overall score (lower is better)
            route_df['overall_score'] = (
                route_df['fuel_cost_norm'] * 0.3 +
                route_df['time_norm'] * 0.3 +
                route_df['risk_score'] * 0.4
            )
        
        # Sort by overall score
        route_df_sorted = route_df.sort_values('overall_score').reset_index(drop=True)
        
        # Prepare results
        results = {
            'recommended_route': route_df_sorted.iloc[0]['route_name'],
            'routes': []
        }
        
        for idx, row in route_df_sorted.iterrows():
            route_info = {
                'rank': idx + 1,
                'name': row['route_name'],
                'distance_km': float(row['distance_km']),
                'total_fuel_cost': float(row['total_fuel_cost']),
                'total_time_hours': float(row['total_time_hours']),
                'risk_score': float(row['risk_score']),
                'overall_score': float(row['overall_score']),
                'weather_risk': float(row['weather_risk']),
                'geopolitical_risk': float(row['geopolitical_risk']),
                'traffic_index': float(row['traffic_index'])
            }
            results['routes'].append(route_info)
        
        # Calculate savings compared to worst route
        worst_score = route_df_sorted.iloc[-1]['overall_score']
        best_score = route_df_sorted.iloc[0]['overall_score']
        results['improvement_percentage'] = float(
            ((worst_score - best_score) / worst_score) * 100
        )
        
        return results
    
    def detect_fraud(self, df: pd.DataFrame, epochs: int = 20) -> Dict:
        """
        Detect fraudulent transactions using Deep Neural Network
        Falls back to scikit-learn if TensorFlow is unavailable.
        
        Args:
            df: DataFrame with transaction features
            epochs: Number of training epochs
            
        Returns:
            Dictionary with fraud detection results
        """
        # Try TensorFlow first, fall back to scikit-learn if unavailable
        tensorflow_available = False
        try:
            from tensorflow import keras
            from tensorflow.keras import layers
            tensorflow_available = True
        except ImportError:
            # TensorFlow not available, will use scikit-learn fallback
            pass
        
        # Prepare features
        categorical_cols = ['device_type', 'merchant_category']
        numerical_cols = [
            'transaction_amount', 'supplier_age_days', 'transaction_hour',
            'historical_fraud_count', 'amount_deviation_from_avg',
            'transaction_frequency_last_24h', 'ip_country_match'
        ]
        
        # Encode categorical variables
        df_encoded = df.copy()
        for col in categorical_cols:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                df_encoded[col] = self.label_encoders[col].fit_transform(df[col])
            else:
                df_encoded[col] = self.label_encoders[col].transform(df[col])
        
        # Prepare feature matrix
        feature_cols = numerical_cols + categorical_cols
        X = df_encoded[feature_cols].values
        y = df_encoded['is_fraud'].values
        
        # Train-test split
        indices = np.arange(len(df_encoded))
        X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
            X, y, indices, test_size=0.2, random_state=42, stratify=y
        )
        
        # Apply SMOTE to balance classes
        smote = SMOTE(random_state=42)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_balanced)
        X_test_scaled = scaler.transform(X_test)
        
        # Use TensorFlow if available, otherwise use scikit-learn
        if tensorflow_available:
            # Build Deep Neural Network with TensorFlow
            model = keras.Sequential([
                layers.Dense(64, activation='relu', input_shape=(X_train_scaled.shape[1],)),
                layers.Dropout(0.3),
                layers.Dense(32, activation='relu'),
                layers.Dropout(0.2),
                layers.Dense(16, activation='relu'),
                layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(
                optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', keras.metrics.Precision(), keras.metrics.Recall()]
            )
            
            # Train with early stopping
            early_stop = keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=5,
                restore_best_weights=True
            )
            
            history = model.fit(
                X_train_scaled, y_train_balanced,
                epochs=epochs,
                batch_size=32,
                validation_split=0.2,
                callbacks=[early_stop],
                verbose=0
            )
            
            # Predictions
            y_pred_proba = model.predict(X_test_scaled, verbose=0).flatten()
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            training_history = {
                'loss': [float(x) for x in history.history['loss']],
                'val_loss': [float(x) for x in history.history['val_loss']],
                'accuracy': [float(x) for x in history.history['accuracy']],
                'val_accuracy': [float(x) for x in history.history['val_accuracy']]
            }
            
            self.fraud_model = model
        else:
            # Fallback: Use scikit-learn MLPClassifier
            from sklearn.neural_network import MLPClassifier
            model = MLPClassifier(
                hidden_layer_sizes=(64, 32, 16),
                max_iter=epochs,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.2,
                n_iter_no_change=5,
                alpha=0.0001
            )
            
            model.fit(X_train_scaled, y_train_balanced)
            
            # Predictions
            y_pred = model.predict(X_test_scaled)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            
            # Create mock training history for consistency
            training_history = {
                'loss': [float(0)],
                'val_loss': [float(0)],
                'accuracy': [float(0)],
                'val_accuracy': [float(0)]
            }
            
            self.fraud_model = model
        
        # Calculate metrics
        cm = confusion_matrix(y_test, y_pred)
        
        results = {
            'metrics': {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, zero_division=0)),
                'auc': float(roc_auc_score(y_test, y_pred_proba)),
                'total_transactions': len(y_test),
                'fraud_detected': int(y_pred.sum()),
                'actual_fraud': int(y_test.sum())
            },
            'confusion_matrix': {
                'tn': int(cm[0, 0]),
                'fp': int(cm[0, 1]),
                'fn': int(cm[1, 0]),
                'tp': int(cm[1, 1])
            },
            'predictions': {
                'y_true': y_test.tolist(),
                'y_pred': y_pred.tolist(),
                'y_pred_proba': y_pred_proba.tolist()
            },
            'training_history': training_history
        }

        test_frame = df.iloc[idx_test].copy()
        test_frame['fraud_probability'] = y_pred_proba
        test_frame['predicted_fraud'] = y_pred
        results['top_alerts'] = (
            test_frame.loc[test_frame['predicted_fraud'] == 1, ['transaction_id', 'transaction_amount', 'device_type', 'merchant_category', 'fraud_probability']]
            .sort_values('fraud_probability', ascending=False)
            .head(10)
            .to_dict('records')
        )
        
        return results


if __name__ == '__main__':
    # Test the analyzer
    from utils.data_generators import (
        generate_supplier_data,
        generate_shipment_data,
        generate_transaction_data,
        generate_route_data
    )
    
    print("Testing Supplier Risk Analyzer...")
    analyzer = SupplierRiskAnalyzer()
    
    # Test forecasting
    print("\n1. Testing Risk Forecasting...")
    supplier_df = generate_supplier_data(200)
    forecast_results = analyzer.train_forecasting_models(supplier_df)
    print(f"Best model: {forecast_results['best_model']}")
    for model_name, metrics in forecast_results['models'].items():
        print(f"  {model_name}: MAE={metrics['mae']:.2f}, R²={metrics['r2']:.3f}")
    
    # Test anomaly detection
    print("\n2. Testing Anomaly Detection...")
    shipment_df = generate_shipment_data(100)
    anomaly_results = analyzer.detect_anomalies(shipment_df)
    print(f"Detected {anomaly_results['metrics']['detected_anomalies']} anomalies")
    if 'accuracy' in anomaly_results['metrics']:
        print(f"Accuracy: {anomaly_results['metrics']['accuracy']:.3f}")
    
    # Test route optimization
    print("\n3. Testing Route Optimization...")
    route_df = generate_route_data(5)
    route_results = analyzer.optimize_routes(route_df)
    print(f"Recommended route: {route_results['recommended_route']}")
    print(f"Improvement: {route_results['improvement_percentage']:.1f}%")
    
    # Test fraud detection
    print("\n4. Testing Fraud Detection...")
    transaction_df = generate_transaction_data(1000)
    fraud_results = analyzer.detect_fraud(transaction_df, epochs=10)
    print(f"Accuracy: {fraud_results['metrics']['accuracy']:.4f}")
    print(f"AUC: {fraud_results['metrics']['auc']:.4f}")
    
    print("\nAll tests completed successfully!")
