import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from ..services.api_sports import APISportsService

class DataPreprocessor:
    def __init__(self):
        self.feature_columns = [
            'games_played', 'minutes_played', 'points', 'assists',
            'rebounds', 'steals', 'blocks', 'turnovers', 'personal_fouls',
            'field_goals_made', 'field_goals_attempted',
            'three_pointers_made', 'three_pointers_attempted',
            'free_throws_made', 'free_throws_attempted'
        ]
        
        self.target_columns = ['points', 'assists', 'rebounds']

    async def fetch_training_data(self, api_service: APISportsService, season: str = "2023") -> pd.DataFrame:
        """
        Fetch and combine player statistics for training
        """
        # Fetch all teams
        teams_response = await api_service.get_team_info(1)  # Start with first team
        teams = teams_response.get('response', [])
        
        all_players_data = []
        
        # Fetch players from each team
        for team in teams:
            team_id = team['id']
            players = await api_service.get_team_players(team_id)
            
            for player in players.get('response', []):
                player_id = player['id']
                stats = await api_service.get_player_stats(player_id)
                
                if stats and 'response' in stats:
                    for game_stats in stats['response']:
                        all_players_data.append(game_stats)
        
        return pd.DataFrame(all_players_data)

    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare features and targets for model training
        """
        # Handle missing values
        df = df.fillna(0)
        
        # Extract features and targets
        X = df[self.feature_columns].values
        y = df[self.target_columns].values
        
        return X, y

    def normalize_features(self, X: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Normalize features using min-max scaling
        """
        feature_ranges = {}
        X_normalized = np.zeros_like(X)
        
        for i in range(X.shape[1]):
            min_val = np.min(X[:, i])
            max_val = np.max(X[:, i])
            feature_ranges[i] = {'min': min_val, 'max': max_val}
            
            if max_val > min_val:
                X_normalized[:, i] = (X[:, i] - min_val) / (max_val - min_val)
            else:
                X_normalized[:, i] = 0
                
        return X_normalized, feature_ranges

    def prepare_single_player(self, player_stats: Dict) -> np.ndarray:
        """
        Prepare features for a single player prediction
        """
        features = []
        for col in self.feature_columns:
            features.append(player_stats.get(col, 0))
        return np.array(features).reshape(1, -1) 