import json
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.sql import and_

from .repositories import TeamRepository, PlayerRepository, StatsRepository
from .models import Base, ApiCache

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations."""

    @staticmethod
    async def fetch_and_store_teams(db: AsyncSession, teams_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch and store teams from API data."""
        try:
            logger.info(f"Storing {len(teams_data)} teams in database")
            teams = await TeamRepository.save_teams_from_api(db, teams_data)
            await db.commit()
            return [
                {
                    "id": team.api_id,
                    "name": team.name,
                    "nbaFranchise": team.is_nba,
                    "city": team.city,
                    "conference": team.conference,
                    "division": team.division
                }
                for team in teams
            ]
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing teams: {e}")
            raise

    @staticmethod
    async def fetch_teams_from_db(db: AsyncSession, nba_only: bool = True) -> List[Dict[str, Any]]:
        """Fetch teams from database."""
        try:
            teams = await TeamRepository.get_all_teams(db, nba_only=nba_only)
            return [
                {
                    "id": team.api_id,
                    "name": team.name,
                    "nbaFranchise": team.is_nba,
                    "city": team.city,
                    "conference": team.conference,
                    "division": team.division
                }
                for team in teams
            ]
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            raise

    @staticmethod
    async def fetch_and_store_players(
        db: AsyncSession, 
        players_data: List[Dict[str, Any]], 
        team_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch and store players with team association from API data."""
        try:
            logger.info(f"Storing {len(players_data)} players for team {team_data.get('name', 'Unknown')} in database")
            players = await PlayerRepository.save_players_from_api(db, players_data, team_data)
            await db.commit()
            return [
                {
                    "id": player.api_id,
                    "name": player.full_name,
                    "team": player.team.name if player.team else "Unknown",
                    "imageUrl": player.image_url
                }
                for player in players
            ]
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing players: {e}")
            raise

    @staticmethod
    async def fetch_players_from_db(
        db: AsyncSession, 
        page: int = 1, 
        per_page: int = 20,
        team_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch players from database with pagination."""
        try:
            skip = (page - 1) * per_page
            players = await PlayerRepository.get_all_players(db, skip=skip, limit=per_page, team_id=team_id)
            
            # Get total count for pagination
            total_teams = len(await TeamRepository.get_all_teams(db))
            
            return {
                "players": [
                    {
                        "id": player.api_id,
                        "name": player.full_name,
                        "team": player.team.name if player.team else "Unknown",
                        "imageUrl": player.image_url
                    }
                    for player in players
                ],
                "pagination": {
                    "current_page": page,
                    "per_page": per_page,
                    "total_teams": total_teams,
                    "total_pages": (total_teams + per_page - 1) // per_page
                }
            }
        except Exception as e:
            logger.error(f"Error fetching players: {e}")
            raise

    @staticmethod
    async def store_player_stats(
        db: AsyncSession, 
        player_api_id: int, 
        stats_data: List[Dict[str, Any]],
        season: str = "2023"
    ) -> Dict[str, Any]:
        """Store player statistics from API data."""
        try:
            player = await PlayerRepository.get_player_by_api_id(db, player_api_id)
            if not player:
                logger.error(f"Player with API ID {player_api_id} not found in database")
                return None
                
            stats = await StatsRepository.create_or_update_player_stats(db, player.id, stats_data, season)
            if not stats:
                logger.error(f"Failed to create/update stats for player {player_api_id}")
                return None
                
            await db.commit()
            return {
                "player_id": player.api_id,
                "name": player.full_name,
                "season": stats.season,
                "points": stats.points,
                "assists": stats.assists,
                "rebounds": stats.rebounds,
                "steals": stats.steals,
                "blocks": stats.blocks,
                "games_played": stats.games_played,
                "minutes_played": stats.minutes_played,
                "last_updated": stats.updated_at.isoformat() if stats.updated_at else None
            }
        except Exception as e:
            await db.rollback()
            logger.error(f"Error storing player stats: {e}")
            raise

    @staticmethod
    async def get_top_scorers(db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top scorers from database."""
        try:
            return await PlayerRepository.get_top_scorers(db, limit=limit)
        except Exception as e:
            logger.error(f"Error getting top scorers: {e}")
            raise

    @staticmethod
    async def get_cached_response(db: AsyncSession, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached API response if it exists and is not expired."""
        try:
            params_str = json.dumps(params, sort_keys=True)
            result = await db.execute(
                select(ApiCache)
                .where(
                    ApiCache.endpoint == endpoint,
                    ApiCache.params == params_str,
                    ApiCache.expires_at > datetime.utcnow()
                )
            )
            cache_entry = result.scalars().first()
            
            if cache_entry:
                return json.loads(cache_entry.response)
            return None
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    @staticmethod
    async def cache_response(
        db: AsyncSession,
        endpoint: str,
        params: Dict[str, Any],
        response: Dict[str, Any],
        expires_in: int = 3600  # Default 1 hour
    ) -> None:
        """Cache API response with expiration."""
        try:
            params_str = json.dumps(params, sort_keys=True)
            response_str = json.dumps(response)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            cache_entry = ApiCache(
                endpoint=endpoint,
                params=params_str,
                response=response_str,
                expires_at=expires_at
            )
            
            db.add(cache_entry)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error caching response: {e}")
            raise

    @staticmethod
    async def cache_scraper_data(db: AsyncSession, key: str, data: dict):
        """Cache scraped data in the database"""
        try:
            cache_entry = {
                "key": key,
                "data": json.dumps(data),
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=24)  # Cache for 24 hours
            }
            
            # Check if entry exists
            existing = await db.execute(
                select(ApiCache).where(ApiCache.key == key)
            )
            existing_entry = existing.scalar_one_or_none()
            
            if existing_entry:
                # Update existing entry
                existing_entry.data = cache_entry["data"]
                existing_entry.expires_at = cache_entry["expires_at"]
            else:
                # Create new entry
                new_entry = ApiCache(**cache_entry)
                db.add(new_entry)
            
            await db.commit()
        except Exception as e:
            logger.error(f"Error caching scraper data: {str(e)}")
            await db.rollback()
            raise

    @staticmethod
    async def get_cached_scraper_data(db: AsyncSession, key: str) -> Optional[dict]:
        """Get cached scraped data from the database"""
        try:
            result = await db.execute(
                select(ApiCache).where(
                    and_(
                        ApiCache.key == key,
                        ApiCache.expires_at > datetime.utcnow()
                    )
                )
            )
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry and cache_entry.data:
                return json.loads(cache_entry.data)
            return None
        except Exception as e:
            logger.error(f"Error getting cached scraper data: {str(e)}")
            return None 