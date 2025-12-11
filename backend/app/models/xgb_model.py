import xgboost as xgb
import numpy as np
import joblib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class XGBModel:
    def __init__(self):
        self.models = {}
        self.feature_names = [
            'games_played', 'minutes_played', 'points_avg', 'assists_avg',
            'rebounds_avg', 'three_pointers_avg', 'field_goal_pct',
            'three_point_pct', 'free_throw_pct', 'plus_minus_avg'
        ]
        
    def load_models(self, model_dir: str = "models"):
        """Load XGBoost models for different predictions"""
        model_path = Path(model_dir)
        if not model_path.exists():
            logger.warning(f"Model directory {model_dir} does not exist")
            return
            
        for stat in ['points', 'assists', 'rebounds', 'three_pointers', 'par']:
            model_file = model_path / f"xgb_{stat}_model.joblib"
            if model_file.exists():
                try:
                    self.models[stat] = joblib.load(model_file)
                    logger.info(f"Loaded {stat} model successfully")
                except Exception as e:
                    logger.error(f"Error loading {stat} model: {e}")
            else:
                logger.warning(f"Model file for {stat} not found at {model_file}")
    
    def preprocess_features(self, player_stats: dict) -> np.ndarray:
        """Convert player stats to model features"""
        features = []
        for feature in self.feature_names:
            value = player_stats.get(feature, 0.0)
            features.append(float(value))
        return np.array(features).reshape(1, -1)
    
    def predict(self, player_stats: dict) -> dict:
        """Make predictions for all stats"""
        if not self.models:
            logger.warning("No models loaded")
            return {}
            
        features = self.preprocess_features(player_stats)
        predictions = {}
        
        for stat, model in self.models.items():
            try:
                pred = model.predict(features)[0]
                predictions[stat] = float(pred)
            except Exception as e:
                logger.error(f"Error predicting {stat}: {e}")
                predictions[stat] = 0.0
                
        return predictions 