from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from app.repositories.player_repository import PlayerRepository
from app.services.api_sports import get_api_service, APISportsService
from app.db.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/players", tags=["players"])
logger = logging.getLogger(__name__)

@router.get("/{player_id}/details")
async def get_player_details(
    player_id: int,
    session: AsyncSession = Depends(get_session),
    api_service: APISportsService = Depends(get_api_service)
):
    """
    Retrieve detailed information about a specific player.
    """
    try:
        # First check if we need to update season info
        await api_service.get_season_info(session)
        
        # Get player details
        player_repo = PlayerRepository(session, api_service)
        player_data = await player_repo.get_player_details(player_id)
        
        if not player_data:
            raise HTTPException(status_code=404, detail="Player not found")
            
        return player_data
    except Exception as e:
        logger.error(f"Error retrieving player details: {str(e)}")
        # Provide a consistent response format for errors
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving player details: {str(e)}"
        )

@router.get("/team/{team_id}")
async def get_players_by_team(
    team_id: int,
    session: AsyncSession = Depends(get_session),
    api_service: APISportsService = Depends(get_api_service)
):
    """
    Retrieve all players from a specific team.
    """
    try:
        player_repo = PlayerRepository(session, api_service)
        players = await player_repo.get_players_by_team(team_id)
        
        if not players:
            return {"message": "No players found for this team", "players": []}
            
        return {"players": players}
    except Exception as e:
        logger.error(f"Error retrieving players for team {team_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving team players: {str(e)}"
        )

@router.get("/search")
async def search_players(
    query: str = Query(..., min_length=2),
    session: AsyncSession = Depends(get_session),
    api_service: APISportsService = Depends(get_api_service)
):
    """
    Search for players by name.
    """
    try:
        player_repo = PlayerRepository(session, api_service)
        players = await player_repo.search_players(query)
        
        return {"players": players}
    except Exception as e:
        logger.error(f"Error searching for players with query '{query}': {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching for players: {str(e)}"
        )

@router.get("/top")
async def get_top_players(
    limit: Optional[int] = Query(10, gt=0, le=100),
    session: AsyncSession = Depends(get_session),
    api_service: APISportsService = Depends(get_api_service)
):
    """
    Get top players based on stats.
    """
    try:
        # First check if we need to update season info
        await api_service.get_season_info(session)
        
        player_repo = PlayerRepository(session, api_service)
        players = await player_repo.get_top_players(limit)
        
        if not players:
            # Return mock data if no players found
            players = [
                {
                    "id": 115,
                    "firstName": "LeBron",
                    "lastName": "James",
                    "position": "F",
                    "jerseyNumber": "23",
                    "photo": "https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png",
                    "stats": {
                        "pointsPerGame": 25.8,
                        "reboundsPerGame": 7.3,
                        "assistsPerGame": 8.3,
                        "season": "2023-2024"
                    },
                    "team": {
                        "id": 17,
                        "name": "Los Angeles Lakers",
                        "code": "LAL",
                        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Los_Angeles_Lakers_logo.svg/220px-Los_Angeles_Lakers_logo.svg.png"
                    }
                },
                {
                    "id": 79,
                    "firstName": "Kevin",
                    "lastName": "Durant",
                    "position": "F",
                    "jerseyNumber": "35",
                    "photo": "https://cdn.nba.com/headshots/nba/latest/1040x760/201142.png",
                    "stats": {
                        "pointsPerGame": 28.2,
                        "reboundsPerGame": 6.6,
                        "assistsPerGame": 5.5,
                        "season": "2023-2024"
                    },
                    "team": {
                        "id": 24,
                        "name": "Phoenix Suns",
                        "code": "PHX",
                        "logo": "https://upload.wikimedia.org/wikipedia/en/d/dc/Phoenix_Suns_logo.svg"
                    }
                },
                {
                    "id": 490,
                    "firstName": "Stephen",
                    "lastName": "Curry",
                    "position": "G",
                    "jerseyNumber": "30",
                    "photo": "https://cdn.nba.com/headshots/nba/latest/1040x760/201939.png",
                    "stats": {
                        "pointsPerGame": 26.4,
                        "reboundsPerGame": 4.5,
                        "assistsPerGame": 5.9,
                        "season": "2023-2024"
                    },
                    "team": {
                        "id": 11,
                        "name": "Golden State Warriors",
                        "code": "GSW",
                        "logo": "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg"
                    }
                }
            ][:limit]
            logger.warning(f"Using mock data for top {limit} players")
        
        return {"players": players}
    except Exception as e:
        logger.error(f"Error retrieving top players: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving top players: {str(e)}"
        ) 