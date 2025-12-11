import torch
import torch.nn as nn
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PlayerPredictionModel(nn.Module):
    def __init__(self, input_size: int = 10, hidden_size: int = 64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, 5)  # 5 outputs: points, assists, rebounds, 3PM, PAR
        )
        
    def forward(self, x):
        return self.network(x)

class NNModel:
    def __init__(self):
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.feature_names = [
            'games_played', 'minutes_played', 'points_avg', 'assists_avg',
            'rebounds_avg', 'three_pointers_avg', 'field_goal_pct',
            'three_point_pct', 'free_throw_pct', 'plus_minus_avg'
        ]
        
    def load_model(self, model_path: str = "models/nn_model.pt"):
        """Load the PyTorch model"""
        try:
            self.model = PlayerPredictionModel()
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            logger.info("Neural network model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading neural network model: {e}")
            self.model = None
    
    def preprocess_features(self, player_stats: dict) -> torch.Tensor:
        """Convert player stats to model features"""
        features = []
        for feature in self.feature_names:
            value = player_stats.get(feature, 0.0)
            features.append(float(value))
        return torch.FloatTensor(features).unsqueeze(0).to(self.device)
    
    def predict(self, player_stats: dict) -> dict:
        """Make predictions for all stats"""
        if self.model is None:
            logger.warning("No model loaded")
            return {}
            
        try:
            features = self.preprocess_features(player_stats)
            with torch.no_grad():
                predictions = self.model(features)
            
            # Convert predictions to dictionary
            stats = ['points', 'assists', 'rebounds', 'three_pointers', 'par']
            return {
                stat: float(pred.item())
                for stat, pred in zip(stats, predictions[0])
            }
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return {} 