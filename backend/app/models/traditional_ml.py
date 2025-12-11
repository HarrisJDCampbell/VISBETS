from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
import joblib
import os
from typing import Dict, List
import numpy as np

class TraditionalMLTrainer:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
    def train_xgboost(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train XGBoost model
        """
        model = XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(self.model_dir, 'xgboost.joblib')
        joblib.dump(model, model_path)
        
        return {
            'model_path': model_path,
            'model_type': 'xgboost'
        }
    
    def train_random_forest(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """
        Train Random Forest model
        """
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        model.fit(X, y)
        
        # Save model
        model_path = os.path.join(self.model_dir, 'random_forest.joblib')
        joblib.dump(model, model_path)
        
        return {
            'model_path': model_path,
            'model_type': 'random_forest'
        }
    
    def predict_xgboost(self, X: np.ndarray, model_path: str) -> np.ndarray:
        """
        Make predictions using XGBoost model
        """
        model = joblib.load(model_path)
        return model.predict(X)
    
    def predict_random_forest(self, X: np.ndarray, model_path: str) -> np.ndarray:
        """
        Make predictions using Random Forest model
        """
        model = joblib.load(model_path)
        return model.predict(X) 