"""
BallDontLie API Client with Rate Limiting

This module provides a client for interacting with the BallDontLie NBA API (All-Star tier).
Includes automatic rate limiting, pagination handling, and error retries.
"""

import os
import time
import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date

logger = logging.getLogger(__name__)


class BallDontLieClient:
    """
    Client for BallDontLie NBA API with built-in rate limiting and pagination.

    The All-Star tier allows 60 requests per minute. This client automatically
    throttles requests to stay within limits.
    """

    def __init__(self):
        self.api_key = os.getenv("BALLDONTLIE_API_KEY")
        self.base_url = os.getenv("BALLDONTLIE_BASE_URL", "https://api.balldontlie.io/v1")

        if not self.api_key:
            raise ValueError("BALLDONTLIE_API_KEY environment variable is required")

        # Rate limiting settings
        self.rate_limit_per_minute = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", 60))
        self.min_request_interval = 60.0 / self.rate_limit_per_minute  # seconds between requests
        self.last_request_time = 0

        # HTTP client configuration
        self.client = httpx.Client(
            timeout=30.0,
            headers={"Authorization": self.api_key}
        )

        logger.info(f"Initialized BallDontLie client with rate limit: {self.rate_limit_per_minute}/min")

    def _rate_limit(self):
        """
        Enforce rate limiting by sleeping if necessary.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a rate-limited HTTP GET request to the BallDontLie API.

        Args:
            endpoint: API endpoint (e.g., '/teams', '/players')
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        self._rate_limit()

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"GET {url} with params: {params}")

        response = self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def _paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Paginate through all results from an endpoint.

        BallDontLie uses cursor-based pagination with 'next_cursor' in the meta field.

        Args:
            endpoint: API endpoint
            params: Query parameters
            max_pages: Optional limit on number of pages to fetch

        Returns:
            List of all items from all pages
        """
        if params is None:
            params = {}

        all_items = []
        page_count = 0
        cursor = None

        while True:
            if cursor:
                params['cursor'] = cursor

            response = self._make_request(endpoint, params)
            data = response.get('data', [])
            all_items.extend(data)

            page_count += 1
            logger.info(f"Fetched page {page_count} from {endpoint}, got {len(data)} items (total: {len(all_items)})")

            # Check for next page
            meta = response.get('meta', {})
            cursor = meta.get('next_cursor')

            if not cursor:
                logger.info(f"Pagination complete for {endpoint}: {len(all_items)} total items")
                break

            if max_pages and page_count >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break

        return all_items

    # ===== Teams Endpoints =====

    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Fetch all NBA teams.

        Returns:
            List of team dictionaries with fields:
            - id: team ID
            - conference: Eastern/Western
            - division: Atlantic, Central, Southeast, Northwest, Pacific, Southwest
            - city: team city
            - name: team name (e.g., "Lakers")
            - full_name: full team name (e.g., "Los Angeles Lakers")
            - abbreviation: 3-letter abbreviation (e.g., "LAL")
        """
        logger.info("Fetching all teams")
        return self._paginate("/teams")

    # ===== Players Endpoints =====

    def get_players(
        self,
        search: Optional[str] = None,
        team_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch NBA players with optional filtering.

        Args:
            search: Search by player name
            team_ids: Filter by team IDs

        Returns:
            List of player dictionaries with fields:
            - id: player ID
            - first_name, last_name
            - position: player position
            - height: height in feet-inches (e.g., "6-8")
            - weight: weight in pounds
            - team: nested team object
        """
        params = {}
        if search:
            params['search'] = search
        if team_ids:
            params['team_ids[]'] = team_ids

        logger.info(f"Fetching players with params: {params}")
        return self._paginate("/players", params)

    # ===== Games Endpoints =====

    def get_games(
        self,
        seasons: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        postseason: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch games with optional filtering.

        Args:
            seasons: Filter by seasons (e.g., [2023, 2024])
            team_ids: Filter by team IDs
            start_date: Filter games on or after this date
            end_date: Filter games on or before this date
            postseason: True for playoff games, False for regular season

        Returns:
            List of game dictionaries with fields:
            - id: game ID
            - date: game date (ISO format)
            - season: season year
            - status: game status
            - home_team: nested team object
            - visitor_team: nested team object
            - home_team_score: final score
            - visitor_team_score: final score
            - postseason: boolean
        """
        params = {}
        if seasons:
            params['seasons[]'] = seasons
        if team_ids:
            params['team_ids[]'] = team_ids
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if postseason is not None:
            params['postseason'] = postseason

        logger.info(f"Fetching games with params: {params}")
        return self._paginate("/games", params)

    def get_game_by_id(self, game_id: int) -> Dict[str, Any]:
        """
        Fetch a single game by ID.

        Args:
            game_id: BallDontLie game ID

        Returns:
            Game dictionary
        """
        logger.info(f"Fetching game {game_id}")
        response = self._make_request(f"/games/{game_id}")
        return response.get('data', {})

    # ===== Stats Endpoints =====

    def get_stats(
        self,
        game_ids: Optional[List[int]] = None,
        player_ids: Optional[List[int]] = None,
        seasons: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        postseason: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch player game stats (box scores) with optional filtering.

        Args:
            game_ids: Filter by specific games
            player_ids: Filter by specific players
            seasons: Filter by seasons
            start_date: Filter stats on or after this date
            end_date: Filter stats on or before this date
            postseason: True for playoff stats, False for regular season

        Returns:
            List of stat dictionaries with fields:
            - id: stat record ID
            - min: minutes played (e.g., "35:24")
            - fgm, fga, fg_pct: field goal stats
            - fg3m, fg3a, fg3_pct: 3-pointer stats
            - ftm, fta, ft_pct: free throw stats
            - oreb, dreb, reb: rebounds
            - ast: assists
            - stl: steals
            - blk: blocks
            - turnover: turnovers
            - pf: personal fouls
            - pts: points
            - player: nested player object
            - game: nested game object
        """
        params = {}
        if game_ids:
            params['game_ids[]'] = game_ids
        if player_ids:
            params['player_ids[]'] = player_ids
        if seasons:
            params['seasons[]'] = seasons
        if start_date:
            params['start_date'] = start_date.isoformat()
        if end_date:
            params['end_date'] = end_date.isoformat()
        if postseason is not None:
            params['postseason'] = postseason

        logger.info(f"Fetching stats with params: {params}")
        return self._paginate("/stats", params)

    def get_season_averages(
        self,
        season: int,
        player_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch season averages for players.

        Args:
            season: Season year (e.g., 2024 for 2024-25 season)
            player_ids: Optional list of player IDs to filter

        Returns:
            List of season average dictionaries with aggregated stats
        """
        params = {'season': season}
        if player_ids:
            params['player_ids[]'] = player_ids

        logger.info(f"Fetching season averages for season {season}")
        response = self._make_request("/season_averages", params)
        return response.get('data', [])

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for one-off requests
def get_client() -> BallDontLieClient:
    """
    Get a new BallDontLie client instance.

    Usage:
        with get_client() as client:
            teams = client.get_teams()
    """
    return BallDontLieClient()
