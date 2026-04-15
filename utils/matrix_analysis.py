
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

class FashionDataGenerator:
    """
    Generates synthetic data for a Fashion & Beauty supply chain
    mimicking the research paper's dataset characteristics.
    """
    def __init__(self, n_samples=150):
        self.n = n_samples
        self.suppliers = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        self.categories = ['Cosmetics', 'Skincare', 'Haircare', 'Fragrance', 'Apparel']
        self.genders = ['Female', 'Male', 'Unisex']
        self.types = ['Development', 'Prototype', 'Mass Production']
        
    def generate(self):
        np.random.seed(42) # Reproducibility
        
        data = {
            'Supplier': np.random.choice(self.suppliers, self.n),
            'Category': np.random.choice(self.categories, self.n),
            'Gender': np.random.choice(self.genders, self.n),
            'Type': np.random.choice(self.types, self.n),
            'Quantity': np.random.randint(50, 5000, self.n),
            'Lead_Time_Days': np.random.randint(7, 60, self.n),
            'Defect_Rate': np.random.uniform(0, 0.05, self.n),
            'Cost_Per_Unit': np.random.uniform(5, 150, self.n)
        }
        
        df = pd.DataFrame(data)
        
        # Synthetic Target: Sustainability Rating (Low, Medium, High)
        # Logic: High Quantity + Fast Lead Time -> Low Sustainability
        #        Supplier A, B are "Green" -> High Sustainability
        #        Prototype -> Medium Sustainability
        
        ratings = []
        for _, row in df.iterrows():
            score = 0
            # Supplier Factor
            if row['Supplier'] in ['A', 'B']: score += 3
            elif row['Supplier'] in ['C', 'D']: score += 2
            else: score += 1
            
            # Category Factor
            if row['Category'] in ['Apparel', 'Cosmetics']: score -= 1 # More validation needed
            
            # Type Factor
            if row['Type'] == 'Prototype': score += 1 # Less waste
            
            # Quantity Factor
            if row['Quantity'] > 3000: score -= 1
            
            # Normalize to classes
            if score >= 3: ratings.append('High')
            elif score >= 1: ratings.append('Medium')
            else: ratings.append('Low')
            
        df['Sustainability_Rating'] = ratings
        return df

class MatrixModelEngine:
    """
    Manages the training and evaluation of 4 ML models:
    KNN, Naive Bayes, Random Forest, Neural Network
    """
    def __init__(self):
        self.models = {
            'KNN': KNeighborsClassifier(n_neighbors=5),
            'Naive Bayes': GaussianNB(),
            'Random Forest': RandomForestClassifier(n_estimators=200, random_state=42),
            'Neural Network': MLPClassifier(hidden_layer_sizes=(100,), max_iter=500, random_state=42)
        }
        self.encoders = {}
        self.scaler = StandardScaler()
        
    def preprocess(self, df):
        """
        Preprocesses data according to research methodology:
        1. Label Encoding (implicitly handled by getting dummies for binary/nominal)
        2. One-Hot Encoding for categorical features
        3. Scaling for KNN/NN
        """
        X = df.drop('Sustainability_Rating', axis=1)
        y = df['Sustainability_Rating']
        
        # Encode Target (Methodology 3.2: Label Encoding for target)
        le_y = LabelEncoder()
        y_encoded = le_y.fit_transform(y)
        self.target_names = le_y.classes_
        
        # One-Hot Encoding for Features (Methodology 3.2)
        # "Afterward, one-hot encoding was employed..."
        categorical_cols = ['Supplier', 'Category', 'Gender', 'Type']
        X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
        
        # Scale (Important for KNN and Neural Networks)
        X_scaled = self.scaler.fit_transform(X_encoded)
        
        return X_scaled, y_encoded, le_y
        
    def run_analysis(self, df):
        """Trains models and returns performance metrics"""
        X, y, le_y = self.preprocess(df)
        
        # Split 80:20 as per paper
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        results = {}
        
        for name, model in self.models.items():
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred = model.predict(X_test)
            
            # Metrics
            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
            rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
            cm = confusion_matrix(y_test, y_pred)
            
            results[name] = {
                'accuracy': float(acc),
                'precision': float(prec),
                'recall': float(rec),
                'confusion_matrix': cm.tolist()
            }
            
        rating_rank = {'High': 3, 'Medium': 2, 'Low': 1}
        supplier_summary = []
        for supplier, frame in df.groupby('Supplier'):
            dominant_rating = frame['Sustainability_Rating'].mode().iloc[0]
            supplier_summary.append({
                'supplier': supplier,
                'dominant_rating': dominant_rating,
                'records': int(len(frame)),
                'avg_lead_time': float(frame['Lead_Time_Days'].mean()),
                'avg_defect_rate': float(frame['Defect_Rate'].mean()),
                'avg_cost_per_unit': float(frame['Cost_Per_Unit'].mean())
            })

        supplier_summary.sort(key=lambda item: (rating_rank.get(item['dominant_rating'], 0), -item['records']), reverse=True)

        category_summary = []
        for category, frame in df.groupby('Category'):
            low_share = float((frame['Sustainability_Rating'] == 'Low').mean() * 100)
            category_summary.append({
                'category': category,
                'low_share': low_share,
                'avg_lead_time': float(frame['Lead_Time_Days'].mean()),
                'avg_defect_rate': float(frame['Defect_Rate'].mean())
            })

        category_summary.sort(key=lambda item: item['low_share'], reverse=True)

        return {
            'metrics': results,
            'classes': self.target_names.tolist(),
            'dataset_summary': {
                'total_samples': len(df),
                'train_size': len(X_train),
                'test_size': len(X_test),
                'features': list(df.drop('Sustainability_Rating', axis=1).columns)
            },
            'portfolio_summary': {
                'rating_counts': {
                    'High': int((df['Sustainability_Rating'] == 'High').sum()),
                    'Medium': int((df['Sustainability_Rating'] == 'Medium').sum()),
                    'Low': int((df['Sustainability_Rating'] == 'Low').sum())
                },
                'avg_lead_time': float(df['Lead_Time_Days'].mean()),
                'avg_defect_rate': float(df['Defect_Rate'].mean()),
                'avg_cost_per_unit': float(df['Cost_Per_Unit'].mean()),
                'top_suppliers': supplier_summary[:6],
                'priority_categories': category_summary[:5]
            }
        }
