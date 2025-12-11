import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
import logging
from pathlib import Path
import joblib
from typing import Tuple, Dict, List
import asyncio
from datetime import datetime, timedelta
import os
import sys

# Configure logging for both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)

class NBADataCollector:
    def __init__(self):
        self.seasons = ['2022-23', '2023-24']
        self.feature_columns = [
            'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'PTS', 'AST', 'REB',
            'FG3M', 'FG3A', 'FG_PCT', 'FT_PCT', 'PLUS_MINUS'
        ]
        self.api_key = os.getenv('NBA_API_KEY')
        if not self.api_key:
            raise ValueError("NBA_API_KEY environment variable is required")
        
    def get_active_players(self) -> List[Dict]:
        """Get list of active NBA players"""
        try:
            active_players = players.get_active_players()
            logger.info(f"Successfully retrieved {len(active_players)} active players")
            return active_players
        except Exception as e:
            logger.error(f"Error getting active players: {e}")
            raise
    
    def get_player_game_logs(self, player_id: int) -> pd.DataFrame:
        """Get game logs for a player from last 2 seasons"""
        all_logs = []
        
        for season in self.seasons:
            try:
                gamelog = playergamelog.PlayerGameLog(
                    player_id=player_id,
                    season=season
                )
                df = gamelog.get_data_frames()[0]
                all_logs.append(df)
                logger.info(f"Retrieved {len(df)} games for player {player_id} in {season}")
            except Exception as e:
                logger.error(f"Error getting game logs for player {player_id}: {e}")
                continue
        
        if not all_logs:
            logger.warning(f"No game logs found for player {player_id}")
            return pd.DataFrame()
            
        combined_df = pd.concat(all_logs, ignore_index=True)
        logger.info(f"Total games for player {player_id}: {len(combined_df)}")
        return combined_df

class DataPreprocessor:
    def __init__(self):
        self.rolling_window = 10
        
    def calculate_rolling_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate rolling averages for key stats"""
        rolling_stats = [
            'PTS', 'AST', 'REB', 'FG3M', 'FG3A', 'FG_PCT', 'FT_PCT', 'PLUS_MINUS'
        ]
        
        for stat in rolling_stats:
            df[f'{stat}_avg'] = df[stat].rolling(window=self.rolling_window, min_periods=1).mean()
        
        return df
    
    def add_game_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features like home/away and opponent"""
        df['is_home'] = df['MATCHUP'].str.contains('vs.').astype(int)
        df['opponent'] = df['MATCHUP'].str.split().str[-1]
        return df
    
    def calculate_par(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Points + Assists + Rebounds"""
        df['PAR'] = df['PTS'] + df['AST'] + df['REB']
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and targets for model training"""
        feature_cols = [
            'PTS_avg', 'AST_avg', 'REB_avg', 'FG3M_avg', 'FG3A_avg',
            'FG_PCT_avg', 'FT_PCT_avg', 'PLUS_MINUS_avg', 'is_home'
        ]
        
        X = df[feature_cols].values
        y_points = df['PTS'].values
        y_par = df['PAR'].values
        
        return X, y_points, y_par

class XGBoostTrainer:
    def __init__(self):
        self.model = None
        self.params = {
            'objective': 'reg:squarederror',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8
        }
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train XGBoost model"""
        self.model = xgb.XGBRegressor(**self.params)
        self.model.fit(X_train, y_train)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        return {'mae': mae, 'rmse': rmse}
    
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        joblib.dump(self.model, path)

class PyTorchTrainer:
    def __init__(self, input_size: int = 9, hidden_size: int = 64):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, 1)
        ).to(self.device)
        
        self.criterion = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray, y_val: np.ndarray,
              epochs: int = 100, batch_size: int = 32) -> None:
        """Train PyTorch model"""
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).reshape(-1, 1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val).reshape(-1, 1).to(self.device)
        
        train_dataset = torch.utils.data.TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(epochs):
            self.model.train()
            for X_batch, y_batch in train_loader:
                self.optimizer.zero_grad()
                y_pred = self.model(X_batch)
                loss = self.criterion(y_pred, y_batch)
                loss.backward()
                self.optimizer.step()
            
            # Validation
            self.model.eval()
            with torch.no_grad():
                y_val_pred = self.model(X_val_tensor)
                val_loss = self.criterion(y_val_pred, y_val_tensor)
                
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance"""
        self.model.eval()
        with torch.no_grad():
            X_test_tensor = torch.FloatTensor(X_test).to(self.device)
            y_pred = self.model(X_test_tensor).cpu().numpy()
            
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        return {'mae': mae, 'rmse': rmse}
    
    def save_model(self, path: str) -> None:
        """Save model to disk"""
        torch.save(self.model.state_dict(), path)

def main():
    try:
        # Initialize components
        collector = NBADataCollector()
        preprocessor = DataPreprocessor()
        xgb_trainer = XGBoostTrainer()
        nn_trainer = PyTorchTrainer()
        
        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        logger.info(f"Using models directory: {models_dir.absolute()}")
        
        # Get active players
        active_players = collector.get_active_players()
        logger.info(f"Found {len(active_players)} active players")
        
        # Collect and process data
        all_data = []
        for player in active_players[:50]:  # Limit to 50 players for testing
            df = collector.get_player_game_logs(player['id'])
            if not df.empty:
                df = preprocessor.calculate_rolling_stats(df)
                df = preprocessor.add_game_features(df)
                df = preprocessor.calculate_par(df)
                all_data.append(df)
                logger.info(f"Processed data for player {player['id']}")
        
        if not all_data:
            logger.error("No data collected")
            sys.exit(1)
        
        # Combine all player data
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Total training samples: {len(combined_data)}")
        
        X, y_points, y_par = preprocessor.prepare_features(combined_data)
        
        # Split data
        X_train, X_test, y_points_train, y_points_test = train_test_split(
            X, y_points, test_size=0.2, random_state=42
        )
        _, _, y_par_train, y_par_test = train_test_split(
            X, y_par, test_size=0.2, random_state=42
        )
        
        # Train XGBoost model for points
        logger.info("Training XGBoost model for points...")
        xgb_trainer.train(X_train, y_points_train)
        xgb_metrics = xgb_trainer.evaluate(X_test, y_points_test)
        xgb_trainer.save_model("models/model_xgb.json")
        logger.info("XGBoost model saved successfully")
        
        # Train PyTorch model for PAR
        logger.info("Training PyTorch model for PAR...")
        X_train, X_val, y_par_train, y_par_val = train_test_split(
            X_train, y_par_train, test_size=0.2, random_state=42
        )
        nn_trainer.train(X_train, y_par_train, X_val, y_par_val)
        nn_metrics = nn_trainer.evaluate(X_test, y_par_test)
        nn_trainer.save_model("models/model_nn.pt")
        logger.info("PyTorch model saved successfully")
        
        # Print results
        logger.info("\nModel Performance Metrics:")
        logger.info("XGBoost Points Model:")
        logger.info(f"MAE: {xgb_metrics['mae']:.2f}")
        logger.info(f"RMSE: {xgb_metrics['rmse']:.2f}")
        logger.info("\nPyTorch PAR Model:")
        logger.info(f"MAE: {nn_metrics['mae']:.2f}")
        logger.info(f"RMSE: {nn_metrics['rmse']:.2f}")
        
        # Verify model files exist
        if not Path("models/model_xgb.json").exists() or not Path("models/model_nn.pt").exists():
            logger.error("Model files were not created successfully")
            sys.exit(1)
            
        logger.info("Training completed successfully")
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 