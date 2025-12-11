"""
Data Ingestion Service

This module handles ingesting NBA data from BallDontLie API into our local database.
All functions are idempotent - they can be run multiple times safely using upserts.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy import select

from app.db.models import Team, Player, Game, PlayerGameStats
from app.services.balldontlie_client import BallDontLieClient
from app.services.player_images import get_player_image_url

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Service for ingesting data from BallDontLie API into our database.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = BallDontLieClient()

    def ingest_teams(self) -> int:
        """
        Ingest all NBA teams from BallDontLie.

        This function is idempotent - it upserts teams by their API ID.

        Returns:
            Number of teams upserted
        """
        logger.info("Starting teams ingestion")

        teams_data = self.client.get_teams()
        count = 0

        for team_data in teams_data:
            # Prepare team record
            team_record = {
                'api_id': team_data['id'],
                'name': team_data['name'],
                'full_name': team_data['full_name'],
                'abbreviation': team_data['abbreviation'],
                'city': team_data['city'],
                'conference': team_data['conference'],
                'division': team_data['division'],
                'is_nba': True,
                'updated_at': datetime.utcnow()
            }

            # Upsert (insert or update on conflict)
            stmt = sqlite_insert(Team).values(**team_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=['api_id'],
                set_=team_record
            )

            self.db.execute(stmt)
            count += 1

        self.db.commit()
        logger.info(f"Teams ingestion complete: {count} teams upserted")
        return count

    def ingest_players(self, team_ids: Optional[List[int]] = None) -> int:
        """
        Ingest NBA players from BallDontLie.

        Args:
            team_ids: Optional list of team IDs to filter by

        Returns:
            Number of players upserted
        """
        logger.info(f"Starting players ingestion (team_ids={team_ids})")

        players_data = self.client.get_players(team_ids=team_ids)
        count = 0

        # Create mapping of API team ID to our internal team ID
        team_map = self._get_team_id_mapping()

        for player_data in players_data:
            # Get our internal team ID
            api_team_id = player_data.get('team', {}).get('id')
            internal_team_id = team_map.get(api_team_id)

            if not internal_team_id and api_team_id:
                logger.warning(f"Team ID {api_team_id} not found in database for player {player_data['id']}")
                # Still insert player, but without team reference
                internal_team_id = None

            # Prepare player record
            first_name = player_data.get('first_name', '')
            last_name = player_data.get('last_name', '')
            player_api_id = player_data['id']

            player_record = {
                'api_id': player_api_id,
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}".strip(),
                'position': player_data.get('position'),
                'height': player_data.get('height'),
                'weight': player_data.get('weight'),
                'team_id': internal_team_id,
                'image_url': get_player_image_url(player_api_id),  # Use NBA CDN with player ID
                'updated_at': datetime.utcnow()
            }

            # Upsert
            stmt = sqlite_insert(Player).values(**player_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=['api_id'],
                set_=player_record
            )

            self.db.execute(stmt)
            count += 1

            if count % 100 == 0:
                logger.info(f"Processed {count} players...")
                self.db.commit()  # Commit in batches

        self.db.commit()
        logger.info(f"Players ingestion complete: {count} players upserted")
        return count

    def ingest_games(
        self,
        season: int,
        team_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        postseason: bool = False
    ) -> int:
        """
        Ingest games for a given season.

        Args:
            season: Season year (e.g., 2024 for 2024-25 season)
            team_ids: Optional team IDs to filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            postseason: True for playoff games, False for regular season

        Returns:
            Number of games upserted
        """
        logger.info(f"Starting games ingestion for season {season}")

        games_data = self.client.get_games(
            seasons=[season],
            team_ids=team_ids,
            start_date=start_date,
            end_date=end_date,
            postseason=postseason
        )

        count = 0
        team_map = self._get_team_id_mapping()

        for game_data in games_data:
            # Map API team IDs to internal IDs
            home_api_id = game_data['home_team']['id']
            visitor_api_id = game_data['visitor_team']['id']
            home_team_id = team_map.get(home_api_id)
            visitor_team_id = team_map.get(visitor_api_id)

            # Parse date
            game_date = datetime.fromisoformat(game_data['date'].replace('Z', '+00:00'))

            # Prepare game record
            game_record = {
                'api_id': game_data['id'],
                'date': game_date,
                'season': game_data['season'],
                'home_team_id': home_team_id,
                'visitor_team_id': visitor_team_id,
                'home_team_score': game_data.get('home_team_score'),
                'visitor_team_score': game_data.get('visitor_team_score'),
                'status': game_data.get('status', 'scheduled'),
                'postseason': game_data.get('postseason', False),
                # Legacy fields
                'home_team': game_data['home_team']['abbreviation'],
                'away_team': game_data['visitor_team']['abbreviation'],
                'home_score': game_data.get('home_team_score'),
                'away_score': game_data.get('visitor_team_score'),
                'updated_at': datetime.utcnow()
            }

            # Upsert
            stmt = sqlite_insert(Game).values(**game_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=['api_id'],
                set_=game_record
            )

            self.db.execute(stmt)
            count += 1

            if count % 100 == 0:
                logger.info(f"Processed {count} games...")
                self.db.commit()

        self.db.commit()
        logger.info(f"Games ingestion complete: {count} games upserted")
        return count

    def ingest_stats(
        self,
        season: int,
        game_ids: Optional[List[int]] = None,
        player_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        postseason: bool = False
    ) -> int:
        """
        Ingest player game stats (box scores) for a season.

        Args:
            season: Season year
            game_ids: Optional specific game IDs
            player_ids: Optional specific player IDs
            start_date: Optional start date
            end_date: Optional end date
            postseason: True for playoff stats

        Returns:
            Number of stat records upserted
        """
        logger.info(f"Starting stats ingestion for season {season}")

        stats_data = self.client.get_stats(
            game_ids=game_ids,
            player_ids=player_ids,
            seasons=[season],
            start_date=start_date,
            end_date=end_date,
            postseason=postseason
        )

        count = 0
        player_map = self._get_player_id_mapping()
        game_map = self._get_game_id_mapping()

        for stat_data in stats_data:
            # Map API IDs to internal IDs
            player_api_id = stat_data['player']['id']
            game_api_id = stat_data['game']['id']

            internal_player_id = player_map.get(player_api_id)
            internal_game_id = game_map.get(game_api_id)

            if not internal_player_id:
                logger.warning(f"Player {player_api_id} not found in database, skipping stat")
                continue

            if not internal_game_id:
                logger.warning(f"Game {game_api_id} not found in database, skipping stat")
                continue

            # Parse game date
            game_date = datetime.fromisoformat(stat_data['game']['date'].replace('Z', '+00:00'))

            # Prepare stat record
            stat_record = {
                'player_id': internal_player_id,
                'game_id': internal_game_id,
                'date': game_date,
                'minutes': stat_data.get('min'),
                'points': stat_data.get('pts') or 0,
                'rebounds': stat_data.get('reb') or 0,
                'assists': stat_data.get('ast') or 0,
                'steals': stat_data.get('stl') or 0,
                'blocks': stat_data.get('blk') or 0,
                'turnovers': stat_data.get('turnover') or 0,
                'fgm': stat_data.get('fgm') or 0,
                'fga': stat_data.get('fga') or 0,
                'fg_pct': stat_data.get('fg_pct'),
                'fg3m': stat_data.get('fg3m') or 0,
                'fg3a': stat_data.get('fg3a') or 0,
                'fg3_pct': stat_data.get('fg3_pct'),
                'ftm': stat_data.get('ftm') or 0,
                'fta': stat_data.get('fta') or 0,
                'ft_pct': stat_data.get('ft_pct'),
                'oreb': stat_data.get('oreb') or 0,
                'dreb': stat_data.get('dreb') or 0,
                'pf': stat_data.get('pf') or 0,
                # Legacy fields
                'field_goals_made': stat_data.get('fgm') or 0,
                'field_goals_attempted': stat_data.get('fga') or 0,
                'three_pointers_made': stat_data.get('fg3m') or 0,
                'three_pointers_attempted': stat_data.get('fg3a') or 0,
                'free_throws_made': stat_data.get('ftm') or 0,
                'free_throws_attempted': stat_data.get('fta') or 0,
                'updated_at': datetime.utcnow()
            }

            # Upsert using unique constraint on (player_id, game_id)
            stmt = sqlite_insert(PlayerGameStats).values(**stat_record)
            stmt = stmt.on_conflict_do_update(
                index_elements=['player_id', 'game_id'],
                set_=stat_record
            )

            self.db.execute(stmt)
            count += 1

            if count % 500 == 0:
                logger.info(f"Processed {count} stat records...")
                self.db.commit()

        self.db.commit()
        logger.info(f"Stats ingestion complete: {count} stat records upserted")
        return count

    # ===== Helper Methods =====

    def _get_team_id_mapping(self) -> Dict[int, int]:
        """
        Get mapping of BallDontLie team API ID to our internal team ID.

        Returns:
            Dict mapping API ID -> internal DB ID
        """
        stmt = select(Team.api_id, Team.id)
        result = self.db.execute(stmt)
        return {api_id: internal_id for api_id, internal_id in result}

    def _get_player_id_mapping(self) -> Dict[int, int]:
        """
        Get mapping of BallDontLie player API ID to our internal player ID.

        Returns:
            Dict mapping API ID -> internal DB ID
        """
        stmt = select(Player.api_id, Player.id)
        result = self.db.execute(stmt)
        return {api_id: internal_id for api_id, internal_id in result}

    def _get_game_id_mapping(self) -> Dict[int, int]:
        """
        Get mapping of BallDontLie game API ID to our internal game ID.

        Returns:
            Dict mapping API ID -> internal DB ID
        """
        stmt = select(Game.api_id, Game.id)
        result = self.db.execute(stmt)
        return {api_id: internal_id for api_id, internal_id in result}

    def close(self):
        """Close the BallDontLie client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
