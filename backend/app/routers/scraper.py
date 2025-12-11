from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..services.nba_scraper import NBAScraper
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import get_async_db
from ..db.service import DatabaseService
import logging

router = APIRouter(
    prefix="/scraper",
    tags=["scraper"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)
scraper = NBAScraper()

@router.get("/player/{player_id}")
async def get_player_stats(
    player_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed player statistics from NBA.com"""
    try:
        # Try to get from cache first
        cached_data = await DatabaseService.get_cached_scraper_data(db, f"player_{player_id}")
        if cached_data:
            return cached_data

        # If not in cache, scrape the data
        stats = await scraper.get_player_stats(player_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Player stats not found")

        # Cache the scraped data
        await DatabaseService.cache_scraper_data(db, f"player_{player_id}", stats)
        return stats
    except Exception as e:
        logger.error(f"Error getting player stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team/{team_id}")
async def get_team_stats(
    team_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get team statistics from NBA.com"""
    try:
        # Try to get from cache first
        cached_data = await DatabaseService.get_cached_scraper_data(db, f"team_{team_id}")
        if cached_data:
            return cached_data

        # If not in cache, scrape the data
        stats = await scraper.get_team_stats(team_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Team stats not found")

        # Cache the scraped data
        await DatabaseService.cache_scraper_data(db, f"team_{team_id}", stats)
        return stats
    except Exception as e:
        logger.error(f"Error getting team stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/player/{player_id}/game-log")
async def get_player_game_log(
    player_id: str,
    season: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed game log for a player"""
    try:
        # Try to get from cache first
        cache_key = f"player_game_log_{player_id}_{season}"
        cached_data = await DatabaseService.get_cached_scraper_data(db, cache_key)
        if cached_data:
            return cached_data

        # If not in cache, scrape the data
        game_log = await scraper.get_player_game_log(player_id, season)
        if not game_log:
            raise HTTPException(status_code=404, detail="Player game log not found")

        # Cache the scraped data
        await DatabaseService.cache_scraper_data(db, cache_key, game_log)
        return game_log
    except Exception as e:
        logger.error(f"Error getting player game log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team/{team_id}/game-log")
async def get_team_game_log(
    team_id: str,
    season: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed game log for a team"""
    try:
        # Try to get from cache first
        cache_key = f"team_game_log_{team_id}_{season}"
        cached_data = await DatabaseService.get_cached_scraper_data(db, cache_key)
        if cached_data:
            return cached_data

        # If not in cache, scrape the data
        game_log = await scraper.get_team_game_log(team_id, season)
        if not game_log:
            raise HTTPException(status_code=404, detail="Team game log not found")

        # Cache the scraped data
        await DatabaseService.cache_scraper_data(db, cache_key, game_log)
        return game_log
    except Exception as e:
        logger.error(f"Error getting team game log: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 