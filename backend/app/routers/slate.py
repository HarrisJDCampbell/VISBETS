from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from ..db.database import get_async_db
from ..db.models import Player, Game, SportsbookLine
from ..services.metrics_service import MetricsService


router = APIRouter(prefix="/api", tags=["slate"])


class MarketData(BaseModel):
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


class SlatePlayer(BaseModel):
    player_id: int
    name: str
    team: str
    position: Optional[str]
    opponent: str
    image_url: Optional[str]
    markets: List[MarketData]


class SlateResponse(BaseModel):
    date: str
    players: List[SlatePlayer]


@router.get("/slate", response_model=SlateResponse)
async def get_daily_slate(
    date_str: Optional[str] = Query(None, description="Date in YYYY-MM-DD format, defaults to today"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get the daily slate of players with games on a specific date.
    Returns players with their stats, lines, and derived metrics.
    """
    # Parse date or use today
    if date_str:
        try:
            slate_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        slate_date = datetime.now()

    # Get all games for this date
    games_query = select(Game).where(
        and_(
            Game.date >= slate_date.replace(hour=0, minute=0, second=0),
            Game.date < slate_date.replace(hour=23, minute=59, second=59)
        )
    )
    games_result = await db.execute(games_query)
    games = games_result.scalars().all()

    if not games:
        return SlateResponse(
            date=slate_date.strftime("%Y-%m-%d"),
            players=[]
        )

    # Get all players with lines for this date
    lines_query = select(SportsbookLine).where(
        and_(
            SportsbookLine.date >= slate_date.replace(hour=0, minute=0, second=0),
            SportsbookLine.date < slate_date.replace(hour=23, minute=59, second=59)
        )
    )
    lines_result = await db.execute(lines_query)
    lines = lines_result.scalars().all()

    # Group lines by player
    player_ids = list(set([line.player_id for line in lines]))

    slate_players = []

    for player_id in player_ids:
        # Get player details
        player_query = select(Player).where(Player.id == player_id)
        player_result = await db.execute(player_query)
        player = player_result.scalar_one_or_none()

        if not player:
            continue

        # Find opponent for this player
        opponent = "TBD"
        for game in games:
            if player.team and player.team.abbreviation:
                if game.home_team == player.team.abbreviation:
                    opponent = game.away_team
                    break
                elif game.away_team == player.team.abbreviation:
                    opponent = game.home_team
                    break

        # Get market data for this player
        markets_data = await MetricsService.get_player_markets_data(db, player_id, slate_date)

        slate_players.append(SlatePlayer(
            player_id=player.id,
            name=player.full_name,
            team=player.team.abbreviation if player.team else "N/A",
            position=player.position,
            opponent=opponent,
            image_url=player.image_url,
            markets=[MarketData(**market) for market in markets_data]
        ))

    return SlateResponse(
        date=slate_date.strftime("%Y-%m-%d"),
        players=slate_players
    )
