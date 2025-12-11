from typing import Dict, List, Optional
import httpx
import os
import logging
from datetime import datetime, timedelta
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ApiCache

logger = logging.getLogger(__name__)

class APISportsService:
    BASE_URL = "https://api-nba-v1.p.rapidapi.com"
    
    def __init__(self):
        self.headers = {
            "X-RapidAPI-Key": os.environ.get("NBA_API_KEY"),
            "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
        }
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=30.0
        )
        # Current season is 2023-2024, so use "2023"
        self.current_season = "2023"
        # Cache durations
        self.CACHE_DURATION = {
            "player_stats": timedelta(hours=12),    # Refresh stats twice daily
            "player_info": timedelta(days=3),       # Player info every 3 days
            "team_info": timedelta(days=7),         # Team info weekly
            "team_players": timedelta(days=2)       # Team players every 2 days
        }
        logger.info(f"Initialized API service with API key: {self.headers['X-RapidAPI-Key'][:10]}... for season {self.current_season}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _get_from_cache(self, session: AsyncSession, endpoint: str, params: Dict) -> Optional[Dict]:
        """Get cached response if available and not expired"""
        try:
            params_str = json.dumps(params, sort_keys=True)
            result = await session.execute(
                f"SELECT response, expiry FROM api_cache WHERE endpoint = '{endpoint}' AND params = '{params_str}'"
            )
            cache_item = result.fetchone()
            
            if cache_item and datetime.fromisoformat(cache_item[1]) > datetime.utcnow():
                logger.info(f"Cache hit for {endpoint} with params {params_str}")
                return json.loads(cache_item[0])
            return None
        except Exception as e:
            logger.error(f"Error checking cache: {str(e)}")
            return None

    async def _save_to_cache(self, session: AsyncSession, endpoint: str, params: Dict, response: Dict, cache_duration: timedelta) -> None:
        """Save response to cache with expiry time"""
        try:
            params_str = json.dumps(params, sort_keys=True)
            response_str = json.dumps(response)
            expiry = (datetime.utcnow() + cache_duration).isoformat()
            now = datetime.utcnow().isoformat()
            
            # Check if entry exists
            result = await session.execute(
                f"SELECT id FROM api_cache WHERE endpoint = '{endpoint}' AND params = '{params_str}'"
            )
            existing = result.fetchone()
            
            if existing:
                # Update existing entry
                await session.execute(
                    f"UPDATE api_cache SET response = '{response_str}', expiry = '{expiry}', updated_at = '{now}' WHERE id = {existing[0]}"
                )
            else:
                # Insert new entry
                await session.execute(
                    f"INSERT INTO api_cache (endpoint, params, response, expiry, created_at, updated_at) VALUES ('{endpoint}', '{params_str}', '{response_str}', '{expiry}', '{now}', '{now}')"
                )
            
            await session.commit()
            logger.info(f"Cached response for {endpoint} with expiry {expiry}")
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
            await session.rollback()

    async def get_player_stats(self, session: AsyncSession, player_id: int) -> Dict:
        """
        Fetch season statistics for a specific player.
        """
        endpoint = "/players/statistics"
        params = {
            "id": player_id,
            "season": self.current_season
        }
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            await self._save_to_cache(session, endpoint, params, data, self.CACHE_DURATION["player_stats"])
            
            return data
        except Exception as e:
            logger.error(f"Error fetching player stats: {str(e)}")
            return {"error": str(e)}

    async def get_recent_games(self, session: AsyncSession, player_id: int, last_n: int = 5) -> List[Dict]:
        """
        Fetch recent games statistics for a specific player.
        """
        endpoint = "/players/statistics"
        params = {
            "id": player_id,
            "season": self.current_season,
            "last": last_n
        }
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache with shorter duration
            await self._save_to_cache(session, endpoint, params, data, timedelta(hours=3))  # Recent games cache for 3 hours
            
            return data
        except Exception as e:
            logger.error(f"Error fetching recent games: {str(e)}")
            return {"error": str(e)}

    async def get_player_info(self, session: AsyncSession, player_id: int) -> Dict:
        """
        Fetch detailed player information including photo URL.
        """
        endpoint = "/players"
        params = {"id": player_id}
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            await self._save_to_cache(session, endpoint, params, data, self.CACHE_DURATION["player_info"])
            
            return data
        except Exception as e:
            logger.error(f"Error fetching player info: {str(e)}")
            return {"error": str(e)}

    async def get_team_info(self, session: AsyncSession, team_id: int) -> Dict:
        """
        Fetch team information.
        """
        endpoint = "/teams"
        params = {"id": team_id}
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            await self._save_to_cache(session, endpoint, params, data, self.CACHE_DURATION["team_info"])
            
            return data
        except Exception as e:
            logger.error(f"Error fetching team info: {str(e)}")
            return {"error": str(e)}

    async def get_team_players(self, session: AsyncSession, team_id: int) -> List[Dict]:
        """
        Fetch all players from a specific team.
        """
        endpoint = "/players"
        params = {
            "team": team_id,
            "season": self.current_season
        }
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache
            await self._save_to_cache(session, endpoint, params, data, self.CACHE_DURATION["team_players"])
            
            return data
        except Exception as e:
            logger.error(f"Error fetching team players: {str(e)}")
            return {"error": str(e)}

    async def get_all_teams(self, session: AsyncSession) -> Dict:
        """
        Fetch all NBA teams.
        """
        endpoint = "/teams"
        params = {"league": "standard"}
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Save to cache for long period
            await self._save_to_cache(session, endpoint, params, data, timedelta(days=30))  # Teams rarely change
            
            return data
        except Exception as e:
            logger.error(f"Error fetching all teams: {str(e)}")
            return {"error": str(e)}

    async def get_season_info(self, session: AsyncSession) -> Dict:
        """
        Fetch information about the current season.
        """
        endpoint = "/seasons"
        params = {}
        
        # Try to get from cache first
        cached = await self._get_from_cache(session, endpoint, params)
        if cached:
            return cached
        
        try:
            response = await self.client.get(
                endpoint,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Check if we have a more recent season than self.current_season
            if "response" in data and data["response"]:
                seasons = data["response"]
                seasons.sort(reverse=True)  # Sort in descending order
                if seasons and seasons[0] > self.current_season:
                    logger.info(f"Updating current season from {self.current_season} to {seasons[0]}")
                    self.current_season = seasons[0]
            
            # Save to cache
            await self._save_to_cache(session, endpoint, params, data, timedelta(days=1))  # Check daily for season updates
            
            return data
        except Exception as e:
            logger.error(f"Error fetching seasons info: {str(e)}")
            return {"error": str(e)}

# Helper function to create a service instance
async def get_api_service() -> APISportsService:
    service = APISportsService()
    yield service
    await service.client.aclose() 