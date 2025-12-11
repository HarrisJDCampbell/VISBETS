from typing import Dict, List, Optional
import numpy as np
from datetime import datetime, timedelta
import logging
from ..models.data_prep import DataPreprocessor
from ..models.ensemble import EnsemblePredictor

logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self):
        self.preprocessor = DataPreprocessor()
        self.ensemble = EnsemblePredictor()
        
    def predict(self, recent_games: List[Dict], opponent_team: Optional[Dict] = None) -> Dict:
        """
        Generate predictions for a player's next game, with optional opponent context
        """
        try:
            if not recent_games:
                return self._get_default_predictions()
            
            # Prepare features from recent games
            features = self.preprocessor.prepare_single_player(recent_games[0])
            features_normalized, _ = self.preprocessor.normalize_features(features)
            
            # Get base prediction
            base_prediction = self.ensemble.predict(features_normalized)
            
            # Calculate confidence based on recent performance consistency
            confidence = self._calculate_confidence(recent_games)
            
            # Adjust predictions based on opponent if provided
            if opponent_team:
                adjusted_prediction = self._adjust_for_opponent(base_prediction, opponent_team)
            else:
                adjusted_prediction = base_prediction
            
            # Format prediction results
            prediction_results = {
                "points": float(adjusted_prediction[0][0]),
                "assists": float(adjusted_prediction[0][1]),
                "rebounds": float(adjusted_prediction[0][2]),
                "confidence": confidence,
                "context": {
                    "is_playoff_game": True,  # Since we're focusing on playoff games
                    "recent_games_analyzed": len(recent_games),
                    "opponent_adjusted": bool(opponent_team)
                }
            }
            
            return prediction_results
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
            return self._get_default_predictions()
    
    def _calculate_confidence(self, recent_games: List[Dict]) -> float:
        """
        Calculate confidence score based on recent performance consistency
        """
        if len(recent_games) < 3:
            return 0.5  # Default confidence for limited data
            
        # Calculate standard deviation of key stats
        points = [game.get("points", 0) for game in recent_games]
        assists = [game.get("assists", 0) for game in recent_games]
        rebounds = [game.get("totReb", 0) for game in recent_games]
        
        # Calculate consistency scores (lower std dev = higher consistency)
        points_consistency = 1 - (np.std(points) / (np.mean(points) + 1e-6))
        assists_consistency = 1 - (np.std(assists) / (np.mean(assists) + 1e-6))
        rebounds_consistency = 1 - (np.std(rebounds) / (np.mean(rebounds) + 1e-6))
        
        # Weight the consistency scores
        weights = [0.5, 0.3, 0.2]  # Points, assists, rebounds weights
        confidence = (
            points_consistency * weights[0] +
            assists_consistency * weights[1] +
            rebounds_consistency * weights[2]
        )
        
        return min(max(confidence, 0.1), 0.95)  # Bound between 0.1 and 0.95
    
    def _adjust_for_opponent(self, base_prediction: np.ndarray, opponent_team: Dict) -> np.ndarray:
        """
        Adjust predictions based on opponent team's defensive stats
        """
        # Get opponent's defensive ratings (if available)
        opp_def_rating = opponent_team.get("defensive_rating", 100)  # Default to league average
        
        # Calculate adjustment factors
        def_factor = opp_def_rating / 100  # >1 means tougher defense
        
        # Apply adjustments
        adjusted = base_prediction.copy()
        adjusted[0][0] *= (1 / def_factor)  # Points
        adjusted[0][1] *= (1 / def_factor)  # Assists
        adjusted[0][2] *= (1 / def_factor)  # Rebounds
        
        return adjusted
    
    def _get_default_predictions(self) -> Dict:
        """
        Return default predictions when data is insufficient
        """
        return {
            "points": 15.0,
            "assists": 3.0,
            "rebounds": 4.0,
            "confidence": 0.3,
            "context": {
                "is_playoff_game": True,
                "recent_games_analyzed": 0,
                "opponent_adjusted": False,
                "note": "Default predictions due to insufficient data"
            }
        } 