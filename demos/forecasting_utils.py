"""
Advanced Demand Forecasting Utilities
Based on research: "Developing and implementing AI-driven models for demand forecasting in US supply chains"

Features:
- Multi-feature regression (20+ features)
- Feature engineering: PCA, OneHotEncoding, MinMaxScaler
- Models: Linear Regression, Random Forest
- Evaluation: RMSE, MAE, R²
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import json

# Expected features from research paper
EXPECTED_FEATURES = [
    'Product_ID', 'Category', 'Price', 'Promotion', 'Discount', 'Shelf_Life',
    'Inventory_Level', 'Units_Sold', 'Stockouts', 'Lead_Time', 
    'Supplier_Reliability', 'Month', 'Holiday', 'Temperature', 'Rainfall',
    'GDP', 'Inflation_Rate', 'Unemployment_Rate', 'Customer_Age_Group',
    'Customer_Income', 'Customer_Location', 'Lag_Sales_1'
]

CATEGORICAL_FEATURES = ['Category', 'Customer_Age_Group', 'Customer_Location']
NUMERICAL_FEATURES = [f for f in EXPECTED_FEATURES if f not in CATEGORICAL_FEATURES + ['Product_ID']]

def validate_dataset(df):
    """Validate uploaded dataset has required columns"""
    if 'Target_Sales' not in df.columns:
        return False, "CSV must have 'Target_Sales' column"
    
    # Check for at least some key features
    required_min = ['Price', 'Units_Sold', 'Month']
    missing = [col for col in required_min if col not in df.columns]
    
    if missing:
        return False, f"Missing required columns: {', '.join(missing)}"
    
    return True, "Valid"

def preprocess_data(df, variance_threshold=0.95):
    """
    Preprocess data following research methodology:
    1. Handle missing values (mean imputation)
    2. Encode categorical variables (OneHotEncoding)
    3. Normalize features (MinMaxScaler)
    4. Apply PCA for dimensionality reduction
    """
    try:
        # Separate target and features
        if 'Target_Sales' not in df.columns:
            return None, "Target_Sales column not found"
        
        y = df['Target_Sales'].values
        X = df.drop(['Target_Sales'], axis=1)
        
        # Drop Product_ID if present (not used for modeling)
        if 'Product_ID' in X.columns:
            X = X.drop(['Product_ID'], axis=1)
        
        # Identify categorical and numerical columns in the dataset
        categorical_cols = [col for col in X.columns if col in CATEGORICAL_FEATURES]
        numerical_cols = [col for col in X.columns if col not in categorical_cols]
        
        # Handle missing values in numerical columns (mean imputation)
        for col in numerical_cols:
            if X[col].isnull().any():
                X[col].fillna(X[col].mean(), inplace=True)
        
        # Create preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', MinMaxScaler(), numerical_cols),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), categorical_cols)
            ],
            remainder='passthrough'
        )
        
        # Fit and transform
        X_processed = preprocessor.fit_transform(X)
        
        # Apply PCA to retain 95% variance (as per research)
        pca = PCA(n_components=variance_threshold)
        X_pca = pca.fit_transform(X_processed)
        
        # Get feature importance info
        n_components = pca.n_components_
        explained_variance = pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)
        
        preprocessing_info = {
            'original_features': len(X.columns),
            'processed_features': X_processed.shape[1],
            'pca_components': n_components,
            'variance_retained': float(cumulative_variance[-1]),
            'categorical_features': categorical_cols,
            'numerical_features': numerical_cols
        }
        
        return {
            'X': X_pca,
            'y': y,
            'preprocessor': preprocessor,
            'pca': pca,
            'info': preprocessing_info
        }, None
        
    except Exception as e:
        return None, str(e)

def train_models(X, y, test_size=0.2, random_state=42):
    """
    Train Linear Regression and Random Forest models
    Returns trained models and evaluation metrics
    """
    try:
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Initialize models
        models = {
            'Linear Regression': LinearRegression(),
            'Random Forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=random_state,
                n_jobs=-1
            )
        }
        
        results = {}
        
        for name, model in models.items():
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # Calculate metrics
            train_metrics = {
                'RMSE': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
                'MAE': float(mean_absolute_error(y_train, y_pred_train)),
                'R2': float(r2_score(y_train, y_pred_train))
            }
            
            test_metrics = {
                'RMSE': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
                'MAE': float(mean_absolute_error(y_test, y_pred_test)),
                'R2': float(r2_score(y_test, y_pred_test))
            }
            
            results[name] = {
                'model': model,
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'predictions': {
                    'y_test': y_test.tolist()[:50],  # First 50 for visualization
                    'y_pred': y_pred_test.tolist()[:50]
                }
            }
        
        return results, None
        
    except Exception as e:
        return None, str(e)

def process_demand_forecast(file_content):
    """
    Main processing function for demand forecasting
    """
    try:
        # Read CSV
        df = pd.read_csv(file_content)
        
        # Validate dataset
        is_valid, message = validate_dataset(df)
        if not is_valid:
            return {'error': message}
        
        # Get basic statistics
        stats = {
            'total_records': int(len(df)),
            'target_mean': float(df['Target_Sales'].mean()),
            'target_std': float(df['Target_Sales'].std()),
            'target_min': float(df['Target_Sales'].min()),
            'target_max': float(df['Target_Sales'].max()),
            'features_count': int(len(df.columns) - 1)  # Excluding Target_Sales
        }
        
        # Preprocess data
        preprocessed, error = preprocess_data(df)
        if error:
            return {'error': f'Preprocessing error: {error}'}
        
        # Ensure preprocessing info uses native types
        preprocessing_info = preprocessed['info']
        preprocessing_info['original_features'] = int(preprocessing_info['original_features'])
        preprocessing_info['processed_features'] = int(preprocessing_info['processed_features'])
        preprocessing_info['pca_components'] = int(preprocessing_info['pca_components'])
        
        # Train models
        model_results, error = train_models(preprocessed['X'], preprocessed['y'])
        if error:
            return {'error': f'Training error: {error}'}
        
        # Prepare response
        response = {
            'success': True,
            'stats': stats,
            'preprocessing': preprocessed['info'],
            'models': {}
        }
        
        # Add model results (without the model objects)
        for model_name, result in model_results.items():
            response['models'][model_name] = {
                'train_metrics': result['train_metrics'],
                'test_metrics': result['test_metrics'],
                'predictions': result['predictions']
            }
        
        return sanitize_for_json(response)
        
    except Exception as e:
        return {'error': f'Processing error: {str(e)}'}

def sanitize_for_json(obj):
    """Recursively convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    else:
        return obj

def generate_sample_dataset(n_samples=1000):
    """Generate sample dataset matching research paper structure"""
    np.random.seed(42)
    
    categories = ['Electronics', 'Clothing', 'Food', 'Home', 'Sports']
    age_groups = ['18-25', '26-35', '36-45', '46-55', '56+']
    locations = ['Urban', 'Suburban', 'Rural']
    
    data = {
        'Product_ID': range(1, n_samples + 1),
        'Category': np.random.choice(categories, n_samples),
        'Price': np.random.uniform(10, 500, n_samples),
        'Promotion': np.random.choice([0, 1], n_samples),
        'Discount': np.random.uniform(0, 0.5, n_samples),
        'Shelf_Life': np.random.randint(30, 365, n_samples),
        'Inventory_Level': np.random.randint(0, 1000, n_samples),
        'Units_Sold': np.random.randint(0, 500, n_samples),
        'Stockouts': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'Lead_Time': np.random.randint(1, 30, n_samples),
        'Supplier_Reliability': np.random.uniform(0.5, 1.0, n_samples),
        'Month': np.random.randint(1, 13, n_samples),
        'Holiday': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'Temperature': np.random.uniform(-10, 40, n_samples),
        'Rainfall': np.random.uniform(0, 200, n_samples),
        'GDP': np.random.uniform(20000, 25000, n_samples),
        'Inflation_Rate': np.random.uniform(0.01, 0.05, n_samples),
        'Unemployment_Rate': np.random.uniform(0.03, 0.08, n_samples),
        'Customer_Age_Group': np.random.choice(age_groups, n_samples),
        'Customer_Income': np.random.uniform(30000, 150000, n_samples),
        'Customer_Location': np.random.choice(locations, n_samples),
        'Lag_Sales_1': np.random.randint(0, 500, n_samples)
    }
    
    # Generate Target_Sales with some correlation to features
    target_sales = (
        data['Price'] * 0.5 +
        data['Units_Sold'] * 2 +
        data['Promotion'] * 50 +
        data['Discount'] * 100 +
        data['Inventory_Level'] * 0.1 +
        np.random.normal(0, 50, n_samples)
    )
    
    data['Target_Sales'] = np.maximum(0, target_sales)
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False)
