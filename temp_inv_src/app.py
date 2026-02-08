import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
import os
from dotenv import load_dotenv

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
import lightgbm as lgb
import shap

# Load environment variables
load_dotenv()

# App configuration
st.set_page_config(
    page_title="AI-Powered Inventory Forecasting & Optimization",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header"> AI-Powered Inventory Forecasting & Optimization</div>', unsafe_allow_html=True)

# Helper function to get credentials from st.secrets or environment
def get_credential(key, default=None):
    """Get credential from Streamlit secrets or environment variables"""
    value = None
    
    # Try Streamlit secrets first (for cloud deployment)
    try:
        value = st.secrets.get(key, default)
    except:
        pass
    
    # Fall back to environment variables (for local development)
    if value is None:
        value = os.getenv(key, default)
    
    # Strip quotes if present (Streamlit Cloud adds them)
    if value and isinstance(value, str):
        value = value.strip().strip("'").strip('"')
    
    return value

# Auto-extend data function with GitHub integration
def auto_extend_data_github():
    """Automatically extend data and commit to GitHub if needed"""
    try:
        # Check if GitHub credentials are configured
        github_pat = get_credential('GITHUB_PAT')
        github_owner = get_credential('GITHUB_REPO_OWNER')
        github_repo = get_credential('GITHUB_REPO_NAME')
        github_branch = get_credential('GITHUB_BRANCH', 'main')
        
        # If GitHub is configured, use GitHub updater
        if github_pat and github_owner and github_repo:
            try:
                from github_updater import auto_update_data_in_github
                
                github_config = {
                    'pat': github_pat,
                    'owner': github_owner,
                    'repo_name': github_repo,
                    'branch': github_branch,
                    'file_path': 'data/sku_timeseries.csv'
                }
                
                # Update data in GitHub
                success = auto_update_data_in_github('data/sku_timeseries.csv', github_config)
                
                if success:
                    st.success("📊 Data automatically updated in GitHub repository")
                    st.cache_data.clear()  # Clear cache to reload from GitHub
                    return True
                return False
                
            except Exception as e:
                st.warning(f"GitHub update failed, using local data: {str(e)}")
                return False
        else:
            # Fall back to local extension
            from datetime import datetime, timedelta
            csv_path = "data/sku_timeseries.csv"
            
            if not os.path.exists(csv_path):
                return False
            
            df_check = pd.read_csv(csv_path)
            df_check["date"] = pd.to_datetime(df_check["date"])
            last_date = df_check["date"].max().date()
            yesterday = (datetime.now() - timedelta(days=1)).date()
            
            if last_date < yesterday:
                from data_simulator import extend_data
                extend_data(csv_path, target_date=yesterday, backup=True)
                st.cache_data.clear()
                st.success(f"📊 Data automatically extended from {last_date} to {yesterday}")
                return True
            return False
            
    except Exception as e:
        st.warning(f"Could not auto-extend data: {str(e)}")
        return False

# Run auto-extension
auto_extend_data_github()

# Load data with GitHub support
@st.cache_data
def load_data():
    """Load and prepare the SKU time series data from GitHub or local file"""
    # Try loading from GitHub first
    github_pat = get_credential('GITHUB_PAT')
    github_owner = get_credential('GITHUB_REPO_OWNER')
    github_repo = get_credential('GITHUB_REPO_NAME')
    github_branch = get_credential('GITHUB_BRANCH', 'main')
    
    if github_pat and github_owner and github_repo:
        try:
            from github_updater import load_data_from_github
            
            github_config = {
                'pat': github_pat,
                'owner': github_owner,
                'repo_name': github_repo,
                'branch': github_branch,
                'file_path': 'data/sku_timeseries.csv'
            }
            
            df = load_data_from_github(github_config)
            return df
        except Exception as e:
            st.warning(f"Could not load from GitHub, using local file: {str(e)}")
    
    # Fallback to local file
    df = pd.read_csv("data/sku_timeseries.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

try:
    df = load_data()
    
    # Sidebar configuration
    st.sidebar.header("📊 Configuration")
    
    # SKU selection
    available_skus = df["id"].unique()
    sku = st.sidebar.selectbox(
        "Select SKU",
        available_skus,
        help="Choose a SKU to analyze"
    )
    
    # Filter data for selected SKU
    sku_df = df[df["id"] == sku].sort_values("date").reset_index(drop=True)
    
    # Display basic info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Data Summary")
    st.sidebar.metric("Total Days", len(sku_df))
    st.sidebar.metric("Date Range", f"{sku_df['date'].min().date()} to {sku_df['date'].max().date()}")
    st.sidebar.metric("Average Demand", f"{sku_df['demand'].mean():.2f}")
    st.sidebar.metric("Demand Std Dev", f"{sku_df['demand'].std():.2f}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Historical Analysis",
        "🔮 Forecasting",
        "📦 Inventory Policy",
        "🎯 Simulation",
        "🧠 Explainability",
        "❓ Help & Guide"
    ])
    
    # Tab 1: Historical Analysis
    with tab1:
        st.markdown('<div class="sub-header">Historical Demand Analysis</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Demand", f"{sku_df['demand'].mean():.2f}")
        with col2:
            st.metric("Median Demand", f"{sku_df['demand'].median():.2f}")
        with col3:
            st.metric("Max Demand", f"{sku_df['demand'].max():.0f}")
        with col4:
            st.metric("Min Demand", f"{sku_df['demand'].min():.0f}")
        
        # Plot historical demand
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(sku_df["date"], sku_df["demand"], linewidth=1.5, color='#1f77b4')
        ax.fill_between(sku_df["date"], sku_df["demand"], alpha=0.3, color='#1f77b4')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Units Sold", fontsize=12)
        ax.set_title(f"Historical Demand for {sku}", fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        
        # Additional statistics
        st.markdown("### 📊 Demand Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Distribution Metrics**")
            stats_df = pd.DataFrame({
                'Metric': ['Mean', 'Std Dev', 'Variance', 'Skewness', 'Kurtosis'],
                'Value': [
                    f"{sku_df['demand'].mean():.2f}",
                    f"{sku_df['demand'].std():.2f}",
                    f"{sku_df['demand'].var():.2f}",
                    f"{sku_df['demand'].skew():.2f}",
                    f"{sku_df['demand'].kurtosis():.2f}"
                ]
            })
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("**Quantiles**")
            quantiles_df = pd.DataFrame({
                'Percentile': ['25%', '50%', '75%', '90%', '95%'],
                'Value': [
                    f"{sku_df['demand'].quantile(0.25):.2f}",
                    f"{sku_df['demand'].quantile(0.50):.2f}",
                    f"{sku_df['demand'].quantile(0.75):.2f}",
                    f"{sku_df['demand'].quantile(0.90):.2f}",
                    f"{sku_df['demand'].quantile(0.95):.2f}"
                ]
            })
            st.dataframe(quantiles_df, hide_index=True, use_container_width=True)
    
    # Tab 2: Forecasting
    with tab2:
        st.markdown('<div class="sub-header">Demand Forecasting</div>', unsafe_allow_html=True)
        
        # Forecast horizon
        forecast_days = st.slider("Forecast Horizon (days)", 7, 56, 28, help="Number of days to forecast")
        
        # Split data
        train = sku_df["demand"][:-forecast_days]
        test = sku_df["demand"][-forecast_days:]
        train_dates = sku_df["date"][:-forecast_days]
        test_dates = sku_df["date"][-forecast_days:]
        
        # ETS Forecast
        st.markdown("### 📈 ETS (Exponential Smoothing) Forecast")
        
        try:
            with st.spinner("Training ETS model..."):
                ets = ExponentialSmoothing(
                    train,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=7
                )
                ets_fit = ets.fit()
                ets_forecast = ets_fit.forecast(len(test))
            
            # Calculate metrics
            ets_mae = np.mean(np.abs(test.values - ets_forecast))
            ets_rmse = np.sqrt(np.mean((test.values - ets_forecast) ** 2))
            ets_mape = np.mean(np.abs((test.values - ets_forecast) / (test.values + 1))) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("MAE", f"{ets_mae:.2f}")
            with col2:
                st.metric("RMSE", f"{ets_rmse:.2f}")
            with col3:
                st.metric("MAPE", f"{ets_mape:.2f}%")
            
            # Plot ETS forecast (show only recent data for better visualization)
            fig, ax = plt.subplots(figsize=(14, 6))
            
            # Show only last 180 days of training data for cleaner visualization
            display_days = min(180, len(train))
            train_display = train.iloc[-display_days:]
            train_dates_display = train_dates.iloc[-display_days:]
            
            ax.plot(train_dates_display, train_display, label="Training Data (Recent)", linewidth=1.5, color='#1f77b4')
            ax.plot(test_dates, test, label="Actual", linewidth=1.5, color='#2ca02c')
            ax.plot(test_dates, ets_forecast, label="ETS Forecast", linewidth=1.5, color='#ff7f0e', linestyle='--')
            ax.fill_between(test_dates, ets_forecast, alpha=0.2, color='#ff7f0e')
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel("Demand", fontsize=12)
            ax.set_title(f"ETS Forecast vs Actual (Last {display_days} days + {forecast_days} day forecast)", fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Error in ETS forecasting: {str(e)}")
            st.info("ETS model requires sufficient data with seasonality. Try a different SKU or adjust parameters.")
        
        # LightGBM Forecast
        st.markdown("### 🤖 LightGBM Machine Learning Forecast")
        
        # Feature engineering
        def create_features(df):
            df = df.copy()
            df["lag_1"] = df["demand"].shift(1)
            df["lag_7"] = df["demand"].shift(7)
            df["lag_14"] = df["demand"].shift(14)
            df["rmean_7"] = df["demand"].rolling(7).mean()
            df["rmean_14"] = df["demand"].rolling(14).mean()
            df["rstd_7"] = df["demand"].rolling(7).std()
            return df.dropna()
        
        feat_df = create_features(sku_df)
        
        if len(feat_df) > 50:
            feature_cols = ["lag_1", "lag_7", "lag_14", "rmean_7", "rmean_14", "rstd_7"]
            
            # Split data for training (use same split as ETS)
            train_feat = feat_df.iloc[:-forecast_days] if len(feat_df) > forecast_days else feat_df.iloc[:-28]
            test_feat = feat_df.iloc[-forecast_days:] if len(feat_df) > forecast_days else feat_df.iloc[-28:]
            
            X_train = train_feat[feature_cols]
            y_train = train_feat["demand"]
            X_test = test_feat[feature_cols]
            y_test = test_feat["demand"]
            
            # Train LightGBM
            with st.spinner("Training LightGBM model..."):
                lgb_model = lgb.LGBMRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=5,
                    random_state=42,
                    verbose=-1
                )
                lgb_model.fit(X_train, y_train)
            
            # Make predictions on test set
            lgb_predictions = lgb_model.predict(X_test)
            
            # Calculate metrics
            lgb_mae = np.mean(np.abs(y_test.values - lgb_predictions))
            lgb_rmse = np.sqrt(np.mean((y_test.values - lgb_predictions) ** 2))
            lgb_mape = np.mean(np.abs((y_test.values - lgb_predictions) / (y_test.values + 1))) * 100
            
            # Next-day prediction (using most recent data)
            X_full = feat_df[feature_cols]
            next_day_pred = lgb_model.predict(X_full.iloc[-1:].values)[0]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Next-Day Forecast", f"{next_day_pred:.2f} units")
            with col2:
                st.metric("MAE", f"{lgb_mae:.2f}")
            with col3:
                st.metric("RMSE", f"{lgb_rmse:.2f}")
            with col4:
                st.metric("MAPE", f"{lgb_mape:.2f}%")
            
            # Plot LightGBM forecast vs actual
            st.markdown("#### LightGBM Forecast vs Actual")
            fig, ax = plt.subplots(figsize=(14, 6))
            test_dates_lgb = test_feat.index if hasattr(test_feat, 'index') else range(len(y_test))
            ax.plot(test_dates_lgb, y_test.values, label="Actual", linewidth=1.5, color='#2ca02c', marker='o')
            ax.plot(test_dates_lgb, lgb_predictions, label="LightGBM Forecast", linewidth=1.5, color='#d62728', linestyle='--', marker='s')
            ax.set_xlabel("Time Period", fontsize=12)
            ax.set_ylabel("Demand", fontsize=12)
            ax.set_title(f"LightGBM Forecast vs Actual ({forecast_days} days)", fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            
            # Feature importance
            st.markdown("#### Feature Importance")
            feature_importance = pd.DataFrame({
                'Feature': feature_cols,
                'Importance': lgb_model.feature_importances_
            }).sort_values('Importance', ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.barh(feature_importance['Feature'], feature_importance['Importance'], color='#2ca02c')
            ax.set_xlabel("Importance", fontsize=12)
            ax.set_title("Feature Importance", fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Insufficient data for LightGBM model. Need at least 50 observations after feature engineering.")
    
    # Tab 3: Inventory Policy
    with tab3:
        st.markdown('<div class="sub-header">Inventory Policy Optimization</div>', unsafe_allow_html=True)
        
        st.markdown("""
        This section calculates optimal inventory levels using the **(s, S)** policy:
        - **s (Reorder Point)**: When inventory falls to this level, place an order
        - **S (Order-up-to Level)**: Target inventory level after ordering
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            lead_time = st.slider(
                "Lead Time (days)",
                min_value=1,
                max_value=30,
                value=7,
                help="Time between placing an order and receiving it"
            )
        
        with col2:
            service_level = st.slider(
                "Service Level",
                min_value=0.80,
                max_value=0.99,
                value=0.95,
                step=0.01,
                help="Probability of not stocking out"
            )
        
        # Calculate inventory parameters
        mu = sku_df["demand"].mean()
        sigma = sku_df["demand"].std()
        
        # Z-score mapping
        z_map = {
            0.80: 0.84,
            0.85: 1.04,
            0.90: 1.28,
            0.95: 1.65,
            0.975: 1.96,
            0.99: 2.33
        }
        z = z_map[min(z_map.keys(), key=lambda x: abs(x - service_level))]
        
        # Calculate s and S
        safety_stock = z * sigma * np.sqrt(lead_time)
        R = mu * lead_time + safety_stock  # Reorder point
        S = R + mu * lead_time  # Order-up-to level
        
        # Display results
        st.markdown("### 📊 Calculated Policy Parameters")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Reorder Point (s)", f"{int(R)} units")
        with col2:
            st.metric("Order-up-to Level (S)", f"{int(S)} units")
        with col3:
            st.metric("Safety Stock", f"{int(safety_stock)} units")
        with col4:
            st.metric("Expected Lead Time Demand", f"{int(mu * lead_time)} units")
        
        # Visualization
        st.markdown("### 📈 Policy Visualization")
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Simulate inventory levels (with fixed seed for consistency)
        np.random.seed(42 + int(lead_time) + int(service_level * 100))  # Seed changes with parameters
        days = 90
        inventory = [S]
        for i in range(days - 1):
            daily_demand = max(0, np.random.normal(mu, sigma))
            new_inventory = inventory[-1] - daily_demand
            if new_inventory <= R:
                new_inventory = S
            inventory.append(new_inventory)
        
        ax.plot(inventory, linewidth=2, color='#1f77b4', label='Inventory Level')
        ax.axhline(y=R, color='#ff7f0e', linestyle='--', linewidth=2, label=f'Reorder Point (s={int(R)})')
        ax.axhline(y=S, color='#2ca02c', linestyle='--', linewidth=2, label=f'Order-up-to Level (S={int(S)})')
        ax.fill_between(range(days), 0, R, alpha=0.2, color='#d62728', label='Stockout Risk Zone')
        ax.fill_between(range(days), R, S, alpha=0.2, color='#2ca02c', label='Safe Zone')
        
        ax.set_xlabel("Days", fontsize=12)
        ax.set_ylabel("Inventory Level (units)", fontsize=12)
        ax.set_title("Inventory Policy Simulation", fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        
        # Additional insights
        st.markdown("### 💡 Policy Insights")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"""
            **Policy Interpretation:**
            - When inventory drops to **{int(R)} units**, place an order
            - Order quantity should bring inventory to **{int(S)} units**
            - Average order quantity: **{int(S - R)} units**
            - Safety stock buffer: **{int(safety_stock)} units**
            """)
        
        with col2:
            st.success(f"""
            **Expected Performance:**
            - Service level: **{service_level*100:.1f}%**
            - Stockout probability: **{(1-service_level)*100:.1f}%**
            - Lead time: **{lead_time} days**
            - Average daily demand: **{mu:.2f} units**
            """)
    
    # Tab 4: Simulation
    with tab4:
        st.markdown('<div class="sub-header">Inventory Simulation</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Simulate inventory performance using the calculated policy parameters.
        This helps validate the policy before implementation.
        """)
        
        # Simulation parameters
        sim_days = st.slider("Simulation Period (days)", 30, 365, 90, key="sim_days_slider")
        
        # Set random seed for reproducibility (changes with parameters)
        sim_seed = 42 + int(lead_time) + int(service_level * 100) + sim_days
        np.random.seed(sim_seed)
        
        # Use test data for simulation if available
        if len(test) > 0 and sim_days <= len(test):
            sim_demand = test.values[:sim_days]
            st.info(f"Using actual demand data for simulation ({len(sim_demand)} days)")
        else:
            # Generate synthetic demand with fixed seed
            sim_demand = np.maximum(0, np.random.normal(mu, sigma, sim_days))
            st.info(f"Using synthetic demand data for simulation ({sim_days} days)")
        
        # Run simulation
        def simulate_inventory(demand, s, S, lead_time_days=0):
            inventory = [S]
            orders = []
            stockouts = []
            pending_orders = []  # Track orders in transit (day_arrival, quantity)
            
            for i, d in enumerate(demand):
                # Start with previous inventory
                current_inv = inventory[-1]
                
                # Receive pending orders that have arrived
                arrived_qty = sum([qty for arrival_day, qty in pending_orders if arrival_day == i])
                if arrived_qty > 0:
                    current_inv = min(current_inv + arrived_qty, S)  # Cap at S
                    pending_orders = [(day, qty) for day, qty in pending_orders if day != i]
                
                # Subtract demand
                current_inv = current_inv - d
                
                # Check for stockout
                if current_inv < 0:
                    stockouts.append(i)
                    current_inv = 0
                
                # Check if reorder needed (only if no pending orders)
                has_pending = len(pending_orders) > 0
                if current_inv <= s and not has_pending:
                    order_qty = S - current_inv
                    orders.append((i, order_qty))
                    # Order arrives after lead time
                    if lead_time_days > 0:
                        arrival_day = i + lead_time_days
                        pending_orders.append((arrival_day, order_qty))
                    else:
                        current_inv = S  # Immediate delivery
                
                inventory.append(current_inv)
            
            return inventory[:-1], orders, stockouts
        
        inventory_levels, orders, stockouts = simulate_inventory(sim_demand, R, S, lead_time)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Stockouts", len(stockouts))
        with col2:
            st.metric("Stockout Rate", f"{len(stockouts)/len(sim_demand)*100:.2f}%")
        with col3:
            st.metric("Total Orders", len(orders))
        with col4:
            avg_order = np.mean([o[1] for o in orders]) if orders else 0
            st.metric("Avg Order Size", f"{avg_order:.0f} units")
        
        # Plot simulation results
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Inventory levels
        ax1.plot(inventory_levels, linewidth=1.5, color='#1f77b4', label='Inventory Level')
        ax1.axhline(y=R, color='#ff7f0e', linestyle='--', linewidth=2, label=f'Reorder Point ({int(R)})')
        ax1.axhline(y=S, color='#2ca02c', linestyle='--', linewidth=2, label=f'Order-up-to Level ({int(S)})')
        
        # Mark stockouts
        if stockouts:
            ax1.scatter(stockouts, [0]*len(stockouts), color='red', s=100, marker='x', 
                       label='Stockouts', zorder=5)
        
        # Mark orders
        if orders:
            order_days = [o[0] for o in orders]
            order_levels = [inventory_levels[o[0]] for o in orders]
            ax1.scatter(order_days, order_levels, color='green', s=100, marker='^', 
                       label='Orders Placed', zorder=5)
        
        ax1.set_xlabel("Days", fontsize=12)
        ax1.set_ylabel("Inventory Level (units)", fontsize=12)
        ax1.set_title("Inventory Level Simulation", fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Demand pattern
        ax2.bar(range(len(sim_demand)), sim_demand, color='#1f77b4', alpha=0.6, label='Daily Demand')
        ax2.axhline(y=mu, color='#ff7f0e', linestyle='--', linewidth=2, label=f'Mean Demand ({mu:.2f})')
        ax2.set_xlabel("Days", fontsize=12)
        ax2.set_ylabel("Demand (units)", fontsize=12)
        ax2.set_title("Demand Pattern", fontsize=14, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Simulation summary
        st.markdown("### 📊 Simulation Summary")
        
        total_demand = np.sum(sim_demand)
        total_stockout = len(stockouts)
        service_level_actual = (len(sim_demand) - total_stockout) / len(sim_demand)
        
        summary_df = pd.DataFrame({
            'Metric': [
                'Simulation Period',
                'Total Demand',
                'Average Daily Demand',
                'Total Stockouts',
                'Achieved Service Level',
                'Total Orders Placed',
                'Average Order Quantity',
                'Average Inventory Level'
            ],
            'Value': [
                f"{len(sim_demand)} days",
                f"{total_demand:.0f} units",
                f"{np.mean(sim_demand):.2f} units",
                f"{total_stockout} days",
                f"{service_level_actual*100:.2f}%",
                f"{len(orders)} orders",
                f"{avg_order:.0f} units",
                f"{np.mean(inventory_levels):.0f} units"
            ]
        })
        
        st.dataframe(summary_df, hide_index=True, use_container_width=True)
    
    # Tab 5: Explainability
    with tab5:
        st.markdown('<div class="sub-header">Model Explainability</div>', unsafe_allow_html=True)
        
        st.markdown("""
        Understanding how the ML model makes predictions is crucial for trust and deployment.
        This section provides interpretability through SHAP values and surrogate models.
        """)
        
        if len(feat_df) > 50:
            # SHAP Analysis
            st.markdown("### 🧠 SHAP (SHapley Additive exPlanations)")
            
            with st.spinner("Calculating SHAP values..."):
                # Sample data for SHAP (to speed up computation)
                # Use X_full from the LightGBM section
                X_full = feat_df[["lag_1", "lag_7", "lag_14", "rmean_7", "rmean_14", "rstd_7"]]
                sample_size = min(200, len(X_full))
                sample_X = X_full.sample(sample_size, random_state=42)
                
                explainer = shap.TreeExplainer(lgb_model)
                shap_values = explainer.shap_values(sample_X)
            
            # SHAP summary plot
            fig, ax = plt.subplots(figsize=(10, 6))
            shap.summary_plot(shap_values, sample_X, show=False)
            plt.title("SHAP Feature Importance", fontsize=14, fontweight='bold')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.info("""
            **SHAP Interpretation:**
            - Each dot represents a prediction
            - Red = high feature value, Blue = low feature value
            - Position on x-axis shows impact on prediction
            - Features are ranked by importance (top to bottom)
            """)
            
            # Surrogate Model
            st.markdown("### 🎯 Simple Surrogate Rule")
            
            st.markdown("""
            A linear approximation of the complex ML model for human understanding.
            This provides a simple rule that approximates the ML model's behavior.
            """)
            
            # Train surrogate model
            feature_cols = ["lag_1", "lag_7", "lag_14", "rmean_7", "rmean_14", "rstd_7"]
            X_full = feat_df[feature_cols]
            lin = LinearRegression()
            lin.fit(X_full, lgb_model.predict(X_full))
            
            # Calculate R² score
            r2_score = lin.score(X_full, lgb_model.predict(X_full))
            
            st.metric("Surrogate Model R² Score", f"{r2_score:.4f}")
            
            # Display coefficients
            st.markdown("#### Linear Approximation Formula:")
            
            formula = f"**Predicted Demand ≈ {lin.intercept_:.2f}**"
            for name, coef in zip(feature_cols, lin.coef_):
                sign = "+" if coef >= 0 else ""
                formula += f"\n- {sign} {coef:.2f} × {name}"
            
            st.code(formula)
            
            # Coefficient visualization
            coef_df = pd.DataFrame({
                'Feature': feature_cols,
                'Coefficient': lin.coef_
            }).sort_values('Coefficient', key=abs, ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            colors = ['#2ca02c' if c > 0 else '#d62728' for c in coef_df['Coefficient']]
            ax.barh(coef_df['Feature'], coef_df['Coefficient'], color=colors)
            ax.axvline(x=0, color='black', linewidth=0.8)
            ax.set_xlabel("Coefficient Value", fontsize=12)
            ax.set_title("Surrogate Model Coefficients", fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.success(f"""
            **Surrogate Model Insights:**
            - The linear model explains **{r2_score*100:.2f}%** of the ML model's predictions
            - Positive coefficients increase predicted demand
            - Negative coefficients decrease predicted demand
            - This rule can be used when ML model is unavailable
            """)
            
            # Model comparison
            st.markdown("### 📊 Model Predictions Comparison")
            
            # Get predictions
            ml_pred = lgb_model.predict(X_full)
            surrogate_pred = lin.predict(X_full)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(ml_pred, surrogate_pred, alpha=0.5, s=20)
            
            # Perfect prediction line
            min_val = min(ml_pred.min(), surrogate_pred.min())
            max_val = max(ml_pred.max(), surrogate_pred.max())
            ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Agreement')
            
            ax.set_xlabel("LightGBM Predictions", fontsize=12)
            ax.set_ylabel("Surrogate Model Predictions", fontsize=12)
            ax.set_title("ML vs Surrogate Model Predictions", fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            
        else:
            st.warning("Insufficient data for explainability analysis. Need at least 50 observations.")
    
    # Tab 6: Help & Guide
    with tab6:
        st.markdown('<div class="sub-header">📚 Welcome to Your Inventory Assistant!</div>', unsafe_allow_html=True)
        
        st.markdown("""
        This app helps you make **smart decisions** about your inventory - when to order products 
        and how much to keep in stock. Think of it as your personal inventory advisor! 🎯
        """)
        
        # What does this app do?
        st.markdown("---")
        st.markdown("## 🤔 What Does This App Do?")
        
        st.markdown("""
        Imagine you run a grocery store and sell apples 🍎. You need to answer two big questions:
        
        1. **How many apples will customers want tomorrow?** (Forecasting)
        2. **When should I order more apples, and how many?** (Inventory Management)
        
        This app helps you answer both questions using:
        - 📊 Your past sales data (history)
        - 🤖 Smart computer models (AI)
        - 📈 Mathematical formulas (statistics)
        """)
        
        # How each page works
        st.markdown("---")
        st.markdown("## 📖 How Each Page Works")
        
        # Page 1: Historical Analysis
        with st.expander("📊 **Page 1: Historical Analysis** - Understanding Your Past", expanded=True):
            st.markdown("""
            ### What It Does
            Shows you patterns in your past sales data - like looking at your store's sales history.
            
            ### Why It Matters
            Before predicting the future, you need to understand the past! This page shows:
            - **Trends**: Are sales going up or down?
            - **Patterns**: Do you sell more on weekends?
            - **Averages**: What's your typical daily sales?
            
            ### Real Example
            Let's say you're looking at apple sales:
            - **Average Demand**: 85 apples/day
            - **Pattern**: Sales spike on Saturdays (120 apples) and dip on Tuesdays (60 apples)
            - **Trend**: Sales have been growing 5% each month
            
            ### How to Use It
            1. Select your product (SKU) from the sidebar
            2. Look at the graph - does it go up and down regularly?
            3. Check the statistics - what's your average daily sales?
            4. Notice any patterns - weekends vs weekdays, seasons, etc.
            
            ### What to Look For
            - ✅ **Stable patterns** = easier to predict
            - ⚠️ **Wild swings** = harder to predict, need more safety stock
            - 📈 **Upward trend** = you're growing! Plan for more inventory
            """)
        
        # Page 2: Forecasting
        with st.expander("🔮 **Page 2: Forecasting** - Predicting the Future"):
            st.markdown("""
            ### What It Does
            Predicts how many items you'll sell in the coming days/weeks.
            
            ### Why It Matters
            You can't order inventory without knowing how much you'll need! Good forecasts mean:
            - ✅ Less waste (don't order too much)
            - ✅ Fewer stockouts (don't order too little)
            - ✅ Happy customers (products always available)
            
            ### Two Prediction Methods
            
            #### 1. ETS (Statistical Model) 📊
            - **What it is**: A traditional math formula that looks at trends and patterns
            - **Best for**: Products with regular, predictable patterns
            - **Think of it as**: A weather forecast based on historical patterns
            
            #### 2. LightGBM (AI Model) 🤖
            - **What it is**: An AI that learns from your data
            - **Best for**: Complex patterns, multiple factors
            - **Think of it as**: A smart assistant that notices subtle patterns you might miss
            
            ### Real Example
            **Scenario**: Predicting apple sales for next week
            
            - **ETS says**: "Based on the pattern, you'll sell 85 apples/day"
            - **LightGBM says**: "I noticed it's holiday week + good weather forecast = 95 apples/day"
            - **You decide**: Use both! If they agree, you're confident. If different, investigate why.
            
            ### How to Use It
            1. Choose forecast horizon (7-56 days)
            2. Compare both models - do they agree?
            3. Check accuracy metrics:
               - **MAE** (Mean Absolute Error): Average mistake size - lower is better
               - **RMSE**: Penalizes big mistakes - lower is better
               - **MAPE**: Percentage error - under 10% is excellent!
            
            ### What the Numbers Mean
            - **MAE = 5**: On average, predictions are off by 5 units
            - **MAPE = 8%**: Predictions are typically 8% off from actual
            - **Good forecast**: MAPE under 15%, predictions match reality closely
            """)
        
        # Page 3: Inventory Policy
        with st.expander("📦 **Page 3: Inventory Policy** - When and How Much to Order"):
            st.markdown("""
            ### What It Does
            Calculates two magic numbers:
            - **s (Reorder Point)**: When inventory drops to this level → ORDER NOW!
            - **S (Order-up-to Level)**: Order enough to reach this level
            
            ### Why It Matters
            These numbers prevent two disasters:
            - 😱 **Stockout**: "Sorry, we're out of apples!"
            - 💸 **Overstock**: Apples rotting in the warehouse
            
            ### Real Example
            **Your Apple Store:**
            - **Reorder Point (s) = 50 apples**
            - **Order-up-to Level (S) = 200 apples**
            
            **What This Means:**
            - When you have 50 apples left → Order immediately!
            - Order 150 apples (to bring total to 200)
            - This keeps you safe for the next delivery
            
            ### The Two Key Settings
            
            #### 1. Lead Time ⏰
            **What it is**: Days between ordering and receiving products
            - Supplier next door = 1 day
            - Overseas supplier = 14 days
            
            **Why it matters**: Longer lead time = need more safety stock
            
            #### 2. Service Level 🎯
            **What it is**: How often you want products in stock
            - 95% = Out of stock only 5% of the time (18 days/year)
            - 99% = Out of stock only 1% of the time (4 days/year)
            
            **Trade-off**: Higher service level = more inventory = higher costs
            
            ### How to Use It
            1. Set your **Lead Time** (how long delivery takes)
            2. Choose **Service Level** (how often you want stock available)
            3. Note the calculated numbers:
               - **Reorder Point**: Your "order now" trigger
               - **Safety Stock**: Your cushion for surprises
            
            ### Real Decision Example
            **Scenario**: You sell 100 apples/day, 7-day delivery
            
            - **95% service level**: Reorder at 800, keep 200 safety stock
            - **99% service level**: Reorder at 900, keep 300 safety stock
            
            **Your choice**: 99% means happier customers but 100 more apples sitting in storage!
            """)
        
        # Page 4: Simulation
        with st.expander("🎯 **Page 4: Simulation** - Test Before You Commit"):
            st.markdown("""
            ### What It Does
            Runs a "what-if" test of your inventory policy before you use it in real life.
            
            ### Why It Matters
            Would you buy a car without a test drive? Same idea here!
            - See how many stockouts you'd have
            - Check how often you'd order
            - Validate your policy works
            
            ### Real Example
            **Test Run**: 90-day simulation with your policy
            
            **Results:**
            - **Stockouts**: 3 days (3.3% of time)
            - **Orders Placed**: 12 times
            - **Average Order**: 150 apples
            - **Service Level Achieved**: 96.7% ✅
            
            **Interpretation:**
            - ✅ Close to target (95% service level)
            - ✅ Ordering frequency reasonable (every 7-8 days)
            - ✅ Policy works well!
            
            ### What You See
            
            #### Graph 1: Inventory Levels
            - **Blue line**: Your inventory over time
            - **Orange dashed line**: Reorder point (when you order)
            - **Green dashed line**: Order-up-to level (target)
            - **Red X marks**: Stockouts (ran out!)
            - **Green triangles**: Orders placed
            
            #### Graph 2: Demand Pattern
            - Shows actual customer demand each day
            - Helps you understand why stockouts happened
            
            ### How to Use It
            1. Set simulation period (30-365 days)
            2. Run the simulation
            3. Check results:
               - **Stockout rate** close to target? ✅
               - **Too many orders?** Maybe increase order quantity
               - **Too many stockouts?** Increase safety stock
            
            ### Red Flags 🚩
            - Stockout rate way higher than target → Increase safety stock
            - Ordering every day → Increase order quantity
            - Inventory always near max → Reduce order quantity
            """)
        
        # Page 5: Explainability
        with st.expander("🧠 **Page 5: Explainability** - Understanding the AI"):
            st.markdown("""
            ### What It Does
            Shows you **why** the AI makes its predictions - no black box magic!
            
            ### Why It Matters
            You wouldn't trust a doctor who says "take this medicine" without explaining why.
            Same with AI - you need to understand its reasoning!
            
            ### Two Ways We Explain
            
            #### 1. SHAP Analysis 🎯
            **What it shows**: Which factors matter most for predictions
            
            **Real Example:**
            ```
            Most Important Factors for Apple Sales:
            1. Yesterday's sales (lag_1) ⭐⭐⭐⭐⭐
            2. Same day last week (lag_7) ⭐⭐⭐⭐
            3. 7-day average (rmean_7) ⭐⭐⭐
            4. Price changes ⭐⭐
            ```
            
            **What this means**: Yesterday's sales are the best predictor of today's sales!
            
            #### 2. Simple Rule (Surrogate Model) 📝
            **What it shows**: A simple formula that approximates the AI
            
            **Real Example:**
            ```
            Predicted Sales ≈ 15 
                + 0.6 × (yesterday's sales)
                + 0.3 × (last week same day)
                + 0.1 × (7-day average)
            ```
            
            **How to use it**: When the AI is unavailable, use this simple formula!
            
            ### Real Scenario
            **Question**: Why did the AI predict 95 apples for tomorrow?
            
            **Answer from SHAP**:
            - Yesterday sold 90 apples → +40 impact
            - Last Tuesday sold 85 apples → +20 impact
            - 7-day average is 88 → +15 impact
            - Price increased slightly → -10 impact
            - **Total**: Base (50) + impacts = 95 apples
            
            ### How to Use It
            1. Look at SHAP chart - which features matter most?
            2. Check simple rule - does it make sense?
            3. Compare AI vs Simple rule - how close are they?
            4. Use insights to improve your business:
               - If price matters a lot → Be careful with price changes!
               - If weekday matters → Plan different stock for each day
            """)
        
        # Quick Start Guide
        st.markdown("---")
        st.markdown("## 🚀 Quick Start: Your First Analysis")
        
        st.markdown("""
        ### Step-by-Step Guide (5 minutes)
        
        #### Step 1: Pick Your Product 🛍️
        - Go to sidebar (left side)
        - Select a SKU from dropdown
        - See basic stats appear
        
        #### Step 2: Understand History 📊
        - Click "Historical Analysis" tab
        - Look at the graph - any patterns?
        - Check average demand
        
        #### Step 3: Get Predictions 🔮
        - Click "Forecasting" tab
        - Set forecast horizon (try 28 days)
        - Compare ETS vs LightGBM
        - Note the predictions
        
        #### Step 4: Set Your Policy 📦
        - Click "Inventory Policy" tab
        - Set lead time (how long delivery takes)
        - Choose service level (95% is good start)
        - Write down reorder point and order-up-to level
        
        #### Step 5: Test It! 🎯
        - Click "Simulation" tab
        - Run 90-day simulation
        - Check if stockout rate matches your target
        - Adjust if needed
        
        #### Step 6: Understand Why 🧠
        - Click "Explainability" tab
        - See what drives predictions
        - Learn from the patterns
        """)
        
        # Common Questions
        st.markdown("---")
        st.markdown("## ❓ Common Questions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### **Q: Which forecast should I trust?**
            **A:** Use both! 
            - If they agree → High confidence ✅
            - If they differ → Investigate why 🔍
            - Generally: ETS for stable patterns, LightGBM for complex ones
            
            ### **Q: What service level should I choose?**
            **A:** Depends on your product:
            - **Critical items** (medicine): 99%
            - **Regular items** (groceries): 95%
            - **Low-priority** (seasonal): 90%
            
            ### **Q: How often should I update forecasts?**
            **A:** 
            - **Weekly**: For most products
            - **Daily**: For fast-moving items
            - **Monthly**: For slow-moving items
            """)
        
        with col2:
            st.markdown("""
            ### **Q: What if I get too many stockouts?**
            **A:** Three options:
            1. Increase service level (95% → 99%)
            2. Reduce lead time (faster supplier)
            3. Increase safety stock manually
            
            ### **Q: What if I have too much inventory?**
            **A:** 
            1. Lower service level (99% → 95%)
            2. Reduce order quantity
            3. Check if forecasts are too high
            
            ### **Q: Can I trust the AI predictions?**
            **A:** Check these:
            - ✅ MAPE under 15%? Good!
            - ✅ Predictions match recent reality?
            - ✅ SHAP shows sensible factors?
            - If yes to all → Trust it! 🎯
            """)
        
        # Tips and Best Practices
        st.markdown("---")
        st.markdown("## 💡 Pro Tips")
        
        st.success("""
        **✅ DO:**
        - Start with historical analysis - understand before predicting
        - Compare multiple forecasts - don't rely on just one
        - Test policies in simulation before real use
        - Review explainability - understand the "why"
        - Adjust service level based on product importance
        """)
        
        st.warning("""
        **❌ DON'T:**
        - Skip the historical analysis
        - Use 99% service level for everything (expensive!)
        - Deploy without simulation testing
        - Ignore large forecast errors
        - Set lead time incorrectly (critical!)
        """)
        
        # Real-World Example
        st.markdown("---")
        st.markdown("## 🌟 Real-World Success Story")
        
        st.info("""
        **Scenario**: Small grocery store selling fresh bread 🍞
        
        **Problem**: 
        - Running out of bread on weekends (angry customers!)
        - Too much bread on Tuesdays (waste!)
        
        **Solution Using This App**:
        1. **Historical Analysis**: Discovered weekend sales 2x higher than weekdays
        2. **Forecasting**: LightGBM predicted weekend spikes accurately
        3. **Inventory Policy**: Set different reorder points for weekdays vs weekends
        4. **Simulation**: Tested policy - reduced stockouts from 15% to 3%
        5. **Result**: Happy customers, less waste, more profit! 📈
        
        **Key Insight from Explainability**: 
        Day of week was the #1 factor - led to day-specific ordering strategy!
        """)
        
        # Need More Help?
        st.markdown("---")     
        st.markdown("""
        **Remember**: This app is a tool to help YOU make better decisions. 
        It provides information and recommendations, but YOU are the expert on your business! 🎯
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🚀 AI-Powered Inventory Forecasting & Optimization System</p>
        <p>Built with Streamlit • Powered by LightGBM & Statistical Models</p>
    </div>
    """, unsafe_allow_html=True)

except FileNotFoundError:
    st.error("❌ Data file not found!")
    st.info("""
    Please ensure that `data/sku_timeseries.csv` exists in the application directory.
    
    Expected file structure:
    ```
    inventory_app/
    ├── app.py
    ├── data/
    │   └── sku_timeseries.csv
    └── requirements.txt
    ```
    """)
except Exception as e:
    st.error(f"❌ An error occurred: {str(e)}")
    st.exception(e)
