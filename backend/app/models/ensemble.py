import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from typing import Dict, List, Any

class EnsemblePredictor:
    def __init__(self):
        self.models = {
            'rf': RandomForestRegressor(n_estimators=100, random_state=42),
            'nn': MLPRegressor(hidden_layer_sizes=(50, 25), max_iter=1000, random_state=42)
        }
        self.is_fitted = False

    def prepare_features(self, recent_games: List[Dict[str, Any]]) -> np.ndarray:
        """Convert recent games into feature matrix"""
        features = []
        for game in recent_games:
            game_features = [
                float(game.get('points', 0)),
                float(game.get('assists', 0)),
                float(game.get('totReb', 0)),
                float(game.get('minutes', 0)),
                float(game.get('fgm', 0)),
                float(game.get('fga', 0)),
                float(game.get('ftm', 0)),
                float(game.get('fta', 0))
            ]
            features.append(game_features)
        return np.array(features)

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train all models in the ensemble"""
        for name, model in self.models.items():
            model.fit(X, y)
        self.is_fitted = True

    def predict(self, recent_games: List[Dict[str, Any]]) -> Dict[str, float]:
        """Make predictions using the ensemble"""
        if not self.is_fitted:
            # Return default predictions if models aren't trained
            return {
                'points': 20.0,
                'assists': 5.0,
                'rebounds': 5.0
            }

        X = self.prepare_features(recent_games)
        if len(X) == 0:
            return {
                'points': 20.0,
                'assists': 5.0,
                'rebounds': 5.0
            }

        # Make predictions for each stat
        predictions = {}
        for stat in ['points', 'assists', 'rebounds']:
            stat_predictions = []
            for model in self.models.values():
                pred = model.predict(X)
                stat_predictions.append(pred[-1])  # Use last prediction
            predictions[stat] = float(np.mean(stat_predictions))

        return predictions 