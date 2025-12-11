from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..db.models import Player, PlayerGameStats, SportsbookLine, Game


class MetricsService:
    """Service for computing derived metrics from player game stats."""

    @staticmethod
    async def compute_rolling_averages(
        db: AsyncSession,
        player_id: int,
        market: str,
        last_n_games: int = 5
    ) -> Optional[float]:
        """
        Compute rolling average for a specific market over last N games.

        Args:
            db: Database session
            player_id: Player ID
            market: Market name (points, rebounds, assists, pra)
            last_n_games: Number of recent games to average

        Returns:
            Rolling average or None if insufficient data
        """
        query = (
            select(PlayerGameStats)
            .where(PlayerGameStats.player_id == player_id)
            .order_by(PlayerGameStats.date.desc())
            .limit(last_n_games)
        )

        result = await db.execute(query)
        stats = result.scalars().all()

        if not stats:
            return None

        if market == 'points':
            values = [s.points for s in stats]
        elif market == 'rebounds':
            values = [s.rebounds for s in stats]
        elif market == 'assists':
            values = [s.assists for s in stats]
        elif market == 'pra':
            values = [s.points + s.rebounds + s.assists for s in stats]
        else:
            return None

        return sum(values) / len(values) if values else None

    @staticmethod
    async def compute_season_average(
        db: AsyncSession,
        player_id: int,
        market: str,
        season: str = "2024-25"
    ) -> Optional[float]:
        """
        Compute season average for a specific market.

        Args:
            db: Database session
            player_id: Player ID
            market: Market name (points, rebounds, assists, pra)
            season: Season year (e.g., "2024-25")

        Returns:
            Season average or None if no data
        """
        query = (
            select(PlayerGameStats)
            .where(PlayerGameStats.player_id == player_id)
        )

        result = await db.execute(query)
        stats = result.scalars().all()

        if not stats:
            return None

        if market == 'points':
            values = [s.points for s in stats]
        elif market == 'rebounds':
            values = [s.rebounds for s in stats]
        elif market == 'assists':
            values = [s.assists for s in stats]
        elif market == 'pra':
            values = [s.points + s.rebounds + s.assists for s in stats]
        else:
            return None

        return sum(values) / len(values) if values else None

    @staticmethod
    async def get_player_markets_data(
        db: AsyncSession,
        player_id: int,
        date: datetime
    ) -> List[Dict]:
        """
        Get all market data for a player including averages and deltas.

        Args:
            db: Database session
            player_id: Player ID
            date: Date for sportsbook lines

        Returns:
            List of market data dictionaries
        """
        markets_data = []
        markets = ['points', 'rebounds', 'assists', 'pra']

        for market in markets:
            # Get sportsbook line
            line_query = (
                select(SportsbookLine)
                .where(
                    and_(
                        SportsbookLine.player_id == player_id,
                        SportsbookLine.market == market,
                        SportsbookLine.date >= date.replace(hour=0, minute=0, second=0),
                        SportsbookLine.date < date.replace(hour=23, minute=59, second=59)
                    )
                )
            )
            line_result = await db.execute(line_query)
            line = line_result.scalar_one_or_none()

            if not line:
                continue

            # Compute averages
            season_avg = await MetricsService.compute_season_average(db, player_id, market)
            last5_avg = await MetricsService.compute_rolling_averages(db, player_id, market, 5)
            last10_avg = await MetricsService.compute_rolling_averages(db, player_id, market, 10)

            # Compute deltas
            delta_line_vs_season = line.line_value - season_avg if season_avg else None
            delta_line_vs_last5 = line.line_value - last5_avg if last5_avg else None

            pct_diff_line_vs_season = None
            pct_diff_line_vs_last5 = None

            if season_avg and season_avg != 0:
                pct_diff_line_vs_season = ((line.line_value - season_avg) / season_avg) * 100

            if last5_avg and last5_avg != 0:
                pct_diff_line_vs_last5 = ((line.line_value - last5_avg) / last5_avg) * 100

            markets_data.append({
                'market': market,
                'line_value': line.line_value,
                'book': line.book,
                'season_avg': round(season_avg, 1) if season_avg else None,
                'last5_avg': round(last5_avg, 1) if last5_avg else None,
                'last10_avg': round(last10_avg, 1) if last10_avg else None,
                'delta_line_vs_season': round(delta_line_vs_season, 1) if delta_line_vs_season else None,
                'delta_line_vs_last5': round(delta_line_vs_last5, 1) if delta_line_vs_last5 else None,
                'pct_diff_line_vs_season': round(pct_diff_line_vs_season, 1) if pct_diff_line_vs_season else None,
                'pct_diff_line_vs_last5': round(pct_diff_line_vs_last5, 1) if pct_diff_line_vs_last5 else None,
            })

        return markets_data

    @staticmethod
    async def get_game_logs(
        db: AsyncSession,
        player_id: int,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent game logs for a player.

        Args:
            db: Database session
            player_id: Player ID
            limit: Number of games to return

        Returns:
            List of game log dictionaries
        """
        query = (
            select(PlayerGameStats, Game)
            .join(Game, PlayerGameStats.game_id == Game.id)
            .where(PlayerGameStats.player_id == player_id)
            .order_by(PlayerGameStats.date.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        rows = result.all()

        game_logs = []
        for stat, game in rows:
            game_logs.append({
                'date': stat.date.strftime('%Y-%m-%d'),
                'opponent': game.away_team if game.home_team else game.home_team,  # Simplified
                'points': stat.points,
                'rebounds': stat.rebounds,
                'assists': stat.assists,
                'minutes': stat.minutes,
                'pra': stat.points + stat.rebounds + stat.assists,
            })

        return game_logs
