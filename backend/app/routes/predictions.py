from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
import numpy as np
from ..services.api_sports import APISportsService, get_api_service
from ..models.data_prep import DataPreprocessor
from ..models.ensemble import EnsemblePredictor
import httpx
from datetime import datetime

router = APIRouter(prefix="/predict", tags=["predictions"])

@router.get("/{player_id}")
async def predict_player_stats(
    player_id: int,
    api_service: APISportsService = Depends(get_api_service)
) -> Dict:
    """
    Get predicted statistics for a player using the ensemble model
    """
    try:
        # Initialize components
        preprocessor = DataPreprocessor()
        ensemble = EnsemblePredictor()
        
        # Fetch player data
        player_stats = await api_service.get_player_stats(player_id)
        if not player_stats or 'response' not in player_stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        # Get the most recent game stats for prediction
        recent_stats = player_stats['response'][0] if player_stats['response'] else {}
        
        # Prepare features
        features = preprocessor.prepare_single_player(recent_stats)
        features_normalized, _ = preprocessor.normalize_features(features)
        
        # Get ensemble prediction
        prediction = ensemble.predict(features_normalized)
        
        # Format prediction results
        prediction_results = {
            "player_id": player_id,
            "predictions": {
                "points": float(prediction[0][0]),
                "assists": float(prediction[0][1]),
                "rebounds": float(prediction[0][2])
            },
            "confidence": {
                "model_weights": ensemble.weights
            }
        }
        
        return prediction_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playoff-games")
async def get_upcoming_playoff_games(
    api_service: APISportsService = Depends(get_api_service)
) -> Dict:
    """
    Get upcoming playoff games and their associated players
    """
    try:
        # Get current date
        current_date = datetime.now()
        
        # Fetch games from API
        games_url = f"{api_service.BASE_URL}/games"
        params = {
            "season": api_service.current_season,
            "league": "standard",
            "type": "playoffs",
            "date": current_date.strftime("%Y-%m-%d")
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                games_url,
                headers=api_service.headers,
                params=params
            )
            response.raise_for_status()
            games_data = response.json()
            
            if not games_data.get("response"):
                return {"games": [], "message": "No upcoming playoff games found"}
            
            # Process games and get player information
            upcoming_games = []
            for game in games_data["response"]:
                # Get team IDs
                home_team_id = game["teams"]["home"]["id"]
                away_team_id = game["teams"]["away"]["id"]
                
                # Get players for both teams
                home_players = await api_service.get_team_players(home_team_id)
                away_players = await api_service.get_team_players(away_team_id)
                
                game_info = {
                    "id": game["id"],
                    "date": game["date"],
                    "time": game["time"],
                    "status": game["status"]["long"],
                    "home_team": {
                        "id": home_team_id,
                        "name": game["teams"]["home"]["name"],
                        "players": home_players
                    },
                    "away_team": {
                        "id": away_team_id,
                        "name": game["teams"]["away"]["name"],
                        "players": away_players
                    }
                }
                upcoming_games.append(game_info)
            
            return {
                "games": upcoming_games,
                "total_games": len(upcoming_games)
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playoff-players")
async def get_playoff_players(
    api_service: APISportsService = Depends(get_api_service)
) -> Dict:
    """
    Get all players who have upcoming playoff games
    """
    try:
        # Get upcoming playoff games
        games_response = await get_upcoming_playoff_games(api_service)
        games = games_response.get("games", [])
        
        # Collect unique players from all games
        playoff_players = set()
        for game in games:
            for player in game["home_team"]["players"]:
                playoff_players.add(player["id"])
            for player in game["away_team"]["players"]:
                playoff_players.add(player["id"])
        
        # Get detailed player information
        players_with_predictions = []
        for player_id in playoff_players:
            # Get player stats and generate predictions
            player_stats = await api_service.get_player_stats(player_id)
            if player_stats and "response" in player_stats:
                recent_stats = player_stats["response"][0] if player_stats["response"] else {}
                
                # Initialize components for prediction
                preprocessor = DataPreprocessor()
                ensemble = EnsemblePredictor()
                
                # Prepare features and get prediction
                features = preprocessor.prepare_single_player(recent_stats)
                features_normalized, _ = preprocessor.normalize_features(features)
                prediction = ensemble.predict(features_normalized)
                
                # Get player info
                player_info = await api_service.get_player_info(player_id)
                
                player_data = {
                    "id": player_id,
                    "name": f"{player_info['firstname']} {player_info['lastname']}",
                    "team": player_info.get("team", {}).get("name"),
                    "photo": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png",
                    "predictions": {
                        "points": float(prediction[0][0]),
                        "assists": float(prediction[0][1]),
                        "rebounds": float(prediction[0][2])
                    },
                    "confidence": {
                        "model_weights": ensemble.weights
                    }
                }
                players_with_predictions.append(player_data)
        
        return {
            "players": players_with_predictions,
            "total_players": len(players_with_predictions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 