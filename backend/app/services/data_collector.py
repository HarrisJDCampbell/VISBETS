import aiohttp
from typing import List, Dict
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class DataCollector:
    def __init__(self):
        self.api_key = os.getenv("NBA_API_KEY")
        self.api_host = "api-nba-v1.p.rapidapi.com"
        self.base_url = "https://api-nba-v1.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
    
    async def fetch_with_retry(self, session: aiohttp.ClientSession, url: str, params: Dict = None, max_retries: int = 3) -> Dict:
        """Fetch data from API with retry logic"""
        for attempt in range(max_retries):
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 429:  # Rate limit
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise Exception(f"API request failed with status {response.status}")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
        return {}
    
    async def get_player_games(self, session: aiohttp.ClientSession, player_id: int, season: str) -> List[Dict]:
        """Get all games for a player in a season"""
        url = f"{self.base_url}/players/statistics"
        params = {
            "player": player_id,
            "season": season
        }
        data = await self.fetch_with_retry(session, url, params)
        return data.get("response", [])
    
    async def get_active_players(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get all active NBA players"""
        url = f"{self.base_url}/players"
        params = {"status": "active"}
        data = await self.fetch_with_retry(session, url, params)
        return data.get("response", [])
    
    def prepare_training_data(self, games: List[Dict], window_size: int = 10) -> List[Dict]:
        """Prepare training data from game statistics"""
        training_data = []
        
        # Sort games by date
        games.sort(key=lambda x: x.get("game", {}).get("date", ""))
        
        for i in range(len(games) - window_size):
            recent_games = games[i:i + window_size]
            next_game = games[i + window_size]
            
            # Extract relevant statistics
            training_example = {
                "recent_games": [{
                    "points": game.get("points", 0),
                    "assists": game.get("assists", 0),
                    "rebounds": game.get("totReb", 0),
                    "minutes": game.get("min", "0").split(":")[0],  # Convert "MM:SS" to minutes
                    "field_goals_made": game.get("fgm", 0),
                    "field_goals_attempted": game.get("fga", 0),
                    "three_pointers_made": game.get("tpm", 0),
                    "three_pointers_attempted": game.get("tpa", 0),
                    "free_throws_made": game.get("ftm", 0),
                    "free_throws_attempted": game.get("fta", 0)
                } for game in recent_games],
                "next_game": {
                    "points": next_game.get("points", 0),
                    "assists": next_game.get("assists", 0),
                    "rebounds": next_game.get("totReb", 0)
                }
            }
            training_data.append(training_example)
        
        return training_data
    
    async def collect_training_data(self, season: str = "2023") -> List[Dict]:
        """Collect training data for all active players"""
        async with aiohttp.ClientSession() as session:
            # Get all active players
            players = await self.get_active_players(session)
            
            all_training_data = []
            for player in players:
                try:
                    # Get player's games
                    games = await self.get_player_games(session, player["id"], season)
                    
                    # Prepare training data
                    player_training_data = self.prepare_training_data(games)
                    all_training_data.extend(player_training_data)
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Error collecting data for player {player['id']}: {str(e)}")
                    continue
            
            return all_training_data 