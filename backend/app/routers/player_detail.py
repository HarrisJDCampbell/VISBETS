from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..db.database import get_async_db
from ..db.models import Player
from ..services.metrics_service import MetricsService


router = APIRouter(prefix="/api/player", tags=["player"])


class PlayerProfile(BaseModel):
    id: int
    name: str
    team: str
    position: Optional[str]
    image_url: Optional[str]
    height: Optional[str]
    weight: Optional[str]
    jersey_number: Optional[str]


class SeasonAverages(BaseModel):
    points: Optional[float]
    rebounds: Optional[float]
    assists: Optional[float]
    pra: Optional[float]


class RollingAverages(BaseModel):
    last5_points: Optional[float]
    last5_rebounds: Optional[float]
    last5_assists: Optional[float]
    last5_pra: Optional[float]
    last10_points: Optional[float]
    last10_rebounds: Optional[float]
    last10_assists: Optional[float]
    last10_pra: Optional[float]


class GameLog(BaseModel):
    date: str
    opponent: str
    points: float
    rebounds: float
    assists: float
    minutes: float
    pra: float


class CurrentLine(BaseModel):
    market: str
    line_value: float
    book: str
    season_avg: Optional[float]
    last5_avg: Optional[float]
    last10_avg: Optional[float]
    delta_line_vs_season: Optional[float]
    delta_line_vs_last5: Optional[float]
    pct_diff_line_vs_season: Optional[float]
    pct_diff_line_vs_last5: Optional[float]


class PlayerDetailResponse(BaseModel):
    player: PlayerProfile
    season_averages: SeasonAverages
    rolling_averages: RollingAverages
    game_logs: List[GameLog]
    current_lines: List[CurrentLine]


@router.get("/{player_id}", response_model=PlayerDetailResponse)
async def get_player_detail(
    player_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information for a specific player including:
    - Player profile
    - Season averages
    - Rolling averages (last 5, last 10)
    - Recent game logs
    - Current sportsbook lines with deltas
    """
    # Get player
    player_query = select(Player).where(Player.id == player_id)
    player_result = await db.execute(player_query)
    player = player_result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Build player profile
    player_profile = PlayerProfile(
        id=player.id,
        name=player.full_name,
        team=player.team.abbreviation if player.team else "N/A",
        position=player.position,
        image_url=player.image_url,
        height=player.height,
        weight=player.weight,
        jersey_number=player.jersey_number
    )

    # Compute season averages
    season_avg_points = await MetricsService.compute_season_average(db, player_id, 'points')
    season_avg_rebounds = await MetricsService.compute_season_average(db, player_id, 'rebounds')
    season_avg_assists = await MetricsService.compute_season_average(db, player_id, 'assists')
    season_avg_pra = await MetricsService.compute_season_average(db, player_id, 'pra')

    season_averages = SeasonAverages(
        points=round(season_avg_points, 1) if season_avg_points else None,
        rebounds=round(season_avg_rebounds, 1) if season_avg_rebounds else None,
        assists=round(season_avg_assists, 1) if season_avg_assists else None,
        pra=round(season_avg_pra, 1) if season_avg_pra else None
    )

    # Compute rolling averages
    last5_points = await MetricsService.compute_rolling_averages(db, player_id, 'points', 5)
    last5_rebounds = await MetricsService.compute_rolling_averages(db, player_id, 'rebounds', 5)
    last5_assists = await MetricsService.compute_rolling_averages(db, player_id, 'assists', 5)
    last5_pra = await MetricsService.compute_rolling_averages(db, player_id, 'pra', 5)

    last10_points = await MetricsService.compute_rolling_averages(db, player_id, 'points', 10)
    last10_rebounds = await MetricsService.compute_rolling_averages(db, player_id, 'rebounds', 10)
    last10_assists = await MetricsService.compute_rolling_averages(db, player_id, 'assists', 10)
    last10_pra = await MetricsService.compute_rolling_averages(db, player_id, 'pra', 10)

    rolling_averages = RollingAverages(
        last5_points=round(last5_points, 1) if last5_points else None,
        last5_rebounds=round(last5_rebounds, 1) if last5_rebounds else None,
        last5_assists=round(last5_assists, 1) if last5_assists else None,
        last5_pra=round(last5_pra, 1) if last5_pra else None,
        last10_points=round(last10_points, 1) if last10_points else None,
        last10_rebounds=round(last10_rebounds, 1) if last10_rebounds else None,
        last10_assists=round(last10_assists, 1) if last10_assists else None,
        last10_pra=round(last10_pra, 1) if last10_pra else None
    )

    # Get game logs
    game_logs_data = await MetricsService.get_game_logs(db, player_id, limit=10)
    game_logs = [GameLog(**log) for log in game_logs_data]

    # Get current lines (today's date)
    today = datetime.now()
    current_lines_data = await MetricsService.get_player_markets_data(db, player_id, today)
    current_lines = [CurrentLine(**line) for line in current_lines_data]

    return PlayerDetailResponse(
        player=player_profile,
        season_averages=season_averages,
        rolling_averages=rolling_averages,
        game_logs=game_logs,
        current_lines=current_lines
    )
