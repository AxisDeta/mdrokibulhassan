"""
Business-facing demand forecasting utilities.
"""

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder


CATEGORICAL_FEATURES = ['Category', 'Customer_Age_Group', 'Customer_Location']


def validate_dataset(df):
    if 'Target_Sales' not in df.columns:
        return False, "CSV must include a 'Target_Sales' column."

    required_min = ['Price', 'Units_Sold', 'Month']
    missing = [col for col in required_min if col not in df.columns]
    if missing:
        return False, f"Missing required columns: {', '.join(missing)}"

    if len(df) < 24:
        return False, "Please upload at least 24 records so the forecast has enough history."

    return True, "Valid"


def sanitize_for_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [sanitize_for_json(v) for v in obj]
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    if isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return sanitize_for_json(obj.tolist())
    return obj


def _coerce_numeric(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _build_preprocessor(X: pd.DataFrame):
    categorical_cols = [col for col in X.columns if col in CATEGORICAL_FEATURES]
    numerical_cols = [col for col in X.columns if col not in categorical_cols]

    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', MinMaxScaler())
    ])

    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('encoder', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_pipeline, numerical_cols),
            ('cat', categorical_pipeline, categorical_cols)
        ]
    )

    return preprocessor, numerical_cols, categorical_cols


def _validation_split_size(record_count: int) -> int:
    proposed = max(6, int(round(record_count * 0.2)))
    return min(proposed, max(6, record_count - 6))


def _evaluate_models(X: pd.DataFrame, y: pd.Series):
    validation_size = _validation_split_size(len(X))
    split_index = len(X) - validation_size

    X_train = X.iloc[:split_index].copy()
    X_valid = X.iloc[split_index:].copy()
    y_train = y.iloc[:split_index].copy()
    y_valid = y.iloc[split_index:].copy()

    preprocessor, numerical_cols, categorical_cols = _build_preprocessor(X_train)
    X_train_processed = preprocessor.fit_transform(X_train)
    X_valid_processed = preprocessor.transform(X_valid)

    pca = PCA(n_components=0.95, svd_solver='full')
    X_train_reduced = pca.fit_transform(X_train_processed)
    X_valid_reduced = pca.transform(X_valid_processed)

    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(
            n_estimators=120,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
    }

    evaluations = {}
    best_model_name = None
    best_mae = None

    for model_name, model in models.items():
        model.fit(X_train_reduced, y_train)
        valid_predictions = model.predict(X_valid_reduced)
        mae = float(mean_absolute_error(y_valid, valid_predictions))
        evaluations[model_name] = {'mae': mae}

        if best_mae is None or mae < best_mae:
            best_mae = mae
            best_model_name = model_name

    full_preprocessor, full_numerical_cols, full_categorical_cols = _build_preprocessor(X)
    X_full_processed = full_preprocessor.fit_transform(X)
    full_pca = PCA(n_components=0.95, svd_solver='full')
    X_full_reduced = full_pca.fit_transform(X_full_processed)
    best_model = models[best_model_name]
    best_model.fit(X_full_reduced, y)

    preprocessing_info = {
        'original_features': len(X.columns),
        'processed_features': int(X_full_processed.shape[1]),
        'pca_components': int(full_pca.n_components_),
        'variance_retained': float(full_pca.explained_variance_ratio_.sum()),
        'categorical_features': categorical_cols,
        'numerical_features': numerical_cols
    }

    return {
        'model_name': best_model_name,
        'model': best_model,
        'preprocessor': full_preprocessor,
        'pca': full_pca,
        'evaluations': evaluations,
        'validation_size': validation_size,
        'preprocessing_info': preprocessing_info
    }


def _build_future_rows(feature_frame: pd.DataFrame, history_sales: list[float], forecast_horizon: int):
    last_row = feature_frame.iloc[-1].copy()
    month_anchor = int(_coerce_numeric(last_row['Month'], 1)) if 'Month' in feature_frame.columns else None
    future_rows = []

    for step in range(1, forecast_horizon + 1):
        next_row = last_row.copy()

        if 'Lag_Sales_1' in feature_frame.columns:
            next_row['Lag_Sales_1'] = history_sales[-1]

        if 'Units_Sold' in feature_frame.columns:
            next_row['Units_Sold'] = history_sales[-1]

        if 'Month' in feature_frame.columns and month_anchor is not None:
            next_row['Month'] = ((month_anchor - 1 + step) % 12) + 1

        if 'Holiday' in feature_frame.columns and 'Month' in feature_frame.columns:
            next_row['Holiday'] = 1 if int(next_row['Month']) in {11, 12} else 0

        if 'Inventory_Level' in feature_frame.columns:
            current_inventory = _coerce_numeric(next_row['Inventory_Level'], history_sales[-1] * 1.5)
            next_row['Inventory_Level'] = max(current_inventory - history_sales[-1] * 0.15, 0)

        future_rows.append(next_row.to_dict())
        last_row = next_row

    return pd.DataFrame(future_rows, columns=feature_frame.columns)


def _forecast_future(feature_frame: pd.DataFrame, target_sales: pd.Series, trained):
    history_sales = target_sales.astype(float).tolist()
    future_rows = _build_future_rows(feature_frame, history_sales, trained['forecast_horizon'])
    forecasts = []

    for row_index in range(len(future_rows)):
        row_df = future_rows.iloc[[row_index]].copy()
        transformed = trained['preprocessor'].transform(row_df)
        reduced = trained['pca'].transform(transformed)
        prediction = float(trained['model'].predict(reduced)[0])
        prediction = max(0.0, prediction)
        forecasts.append(prediction)

        history_sales.append(prediction)
        if row_index + 1 < len(future_rows):
            if 'Lag_Sales_1' in future_rows.columns:
                future_rows.at[row_index + 1, 'Lag_Sales_1'] = prediction
            if 'Units_Sold' in future_rows.columns:
                future_rows.at[row_index + 1, 'Units_Sold'] = prediction

    return forecasts


def process_demand_forecast(file_content, forecast_horizon=12):
    try:
        df = pd.read_csv(file_content)
        is_valid, message = validate_dataset(df)
        if not is_valid:
            return {'error': message}

        forecast_horizon = max(4, min(int(forecast_horizon or 12), 24))
        history = df.copy()
        target_sales = history['Target_Sales'].astype(float)
        feature_frame = history.drop(columns=['Target_Sales']).copy()
        if 'Product_ID' in feature_frame.columns:
            feature_frame = feature_frame.drop(columns=['Product_ID'])

        trained = _evaluate_models(feature_frame, target_sales)
        trained['forecast_horizon'] = forecast_horizon
        future_forecast = _forecast_future(feature_frame, target_sales, trained)

        recent_window = min(18, len(target_sales))
        recent_history = target_sales.tail(recent_window).tolist()
        baseline_window = min(12, len(target_sales))
        baseline_mean = float(target_sales.tail(baseline_window).mean())
        projected_total = float(np.sum(future_forecast))
        projected_average = float(np.mean(future_forecast))
        peak_index = int(np.argmax(future_forecast))
        trough_index = int(np.argmin(future_forecast))
        trend_percent = float(((projected_average - baseline_mean) / baseline_mean) * 100) if baseline_mean else 0.0
        volatility_percent = float((np.std(future_forecast) / projected_average) * 100) if projected_average else 0.0

        if abs(trend_percent) >= 15 or volatility_percent >= 20:
            planning_risk = 'High'
        elif abs(trend_percent) >= 8 or volatility_percent >= 12:
            planning_risk = 'Medium'
        else:
            planning_risk = 'Monitor'

        response = {
            'success': True,
            'stats': {
                'total_records': int(len(df)),
                'features_count': int(len(feature_frame.columns)),
                'historical_average': baseline_mean,
                'historical_peak': float(target_sales.max())
            },
            'preprocessing': trained['preprocessing_info'],
            'forecast_horizon': forecast_horizon,
            'historical': {
                'labels': [f'H-{recent_window - idx - 1}' for idx in range(recent_window)],
                'values': recent_history
            },
            'forecast': {
                'labels': [f'P+{idx + 1}' for idx in range(forecast_horizon)],
                'values': future_forecast,
                'projected_total': projected_total,
                'projected_average': projected_average,
                'peak_period': f'P+{peak_index + 1}',
                'peak_value': float(future_forecast[peak_index]),
                'low_period': f'P+{trough_index + 1}',
                'low_value': float(future_forecast[trough_index]),
                'trend_percent': trend_percent,
                'volatility_percent': volatility_percent,
                'planning_risk': planning_risk,
                'best_fit_window': int(trained['validation_size'])
            }
        }

        return sanitize_for_json(response)
    except Exception as exc:
        return {'error': f'Processing error: {str(exc)}'}


def generate_sample_dataset(n_samples=1000):
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
