import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta
import time
from ..config import get_settings

logger = logging.getLogger(__name__)

class NBAScraper:
    def __init__(self):
        self.base_url = "https://www.nba.com/stats"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.settings = get_settings()
        self.delay = self.settings.SCRAPING_DELAY
        self.max_retries = self.settings.MAX_RETRIES

    async def _make_request(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Make a request with retry logic and rate limiting"""
        if retry_count >= self.max_retries:
            logger.error(f"Max retries reached for URL: {url}")
            return None

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                await asyncio.sleep(self.delay)  # Rate limiting
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Too Many Requests
                        wait_time = int(response.headers.get('Retry-After', self.delay * 2))
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(url, retry_count + 1)
                    else:
                        logger.error(f"Request failed with status {response.status} for URL: {url}")
                        return None
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            await asyncio.sleep(self.delay * 2)
            return await self._make_request(url, retry_count + 1)

    async def get_player_stats(self, player_id: str) -> Optional[Dict]:
        """Get detailed player statistics from NBA.com"""
        url = f"{self.base_url}/player/{player_id}"
        html = await self._make_request(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Extract player stats from the page
            # Note: This is a basic implementation. You'll need to adjust selectors based on actual page structure
            stats = {
                "season_averages": self._extract_season_averages(soup),
                "game_log": self._extract_game_log(soup),
                "advanced_stats": self._extract_advanced_stats(soup)
            }
            return stats
        except Exception as e:
            logger.error(f"Error parsing player stats: {str(e)}")
            return None

    async def get_team_stats(self, team_id: str) -> Optional[Dict]:
        """Get team statistics from NBA.com"""
        url = f"{self.base_url}/team/{team_id}"
        html = await self._make_request(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Extract team stats from the page
            stats = {
                "team_stats": self._extract_team_stats(soup),
                "roster": self._extract_team_roster(soup),
                "schedule": self._extract_team_schedule(soup)
            }
            return stats
        except Exception as e:
            logger.error(f"Error parsing team stats: {str(e)}")
            return None

    def _extract_season_averages(self, soup: BeautifulSoup) -> Dict:
        """Extract season averages from player page"""
        # Implement based on actual page structure
        return {}

    def _extract_game_log(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract game log from player page"""
        # Implement based on actual page structure
        return []

    def _extract_advanced_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract advanced statistics from player page"""
        # Implement based on actual page structure
        return {}

    def _extract_team_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract team statistics from team page"""
        # Implement based on actual page structure
        return {}

    def _extract_team_roster(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team roster from team page"""
        # Implement based on actual page structure
        return []

    def _extract_team_schedule(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract team schedule from team page"""
        # Implement based on actual page structure
        return []

    async def get_player_game_log(self, player_id: str, season: str = None) -> Optional[List[Dict]]:
        """Get detailed game log for a player"""
        if not season:
            season = datetime.now().year
        url = f"{self.base_url}/player/{player_id}/games?Season={season}"
        html = await self._make_request(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            return self._extract_game_log(soup)
        except Exception as e:
            logger.error(f"Error parsing player game log: {str(e)}")
            return None

    async def get_team_game_log(self, team_id: str, season: str = None) -> Optional[List[Dict]]:
        """Get detailed game log for a team"""
        if not season:
            season = datetime.now().year
        url = f"{self.base_url}/team/{team_id}/games?Season={season}"
        html = await self._make_request(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')
            return self._extract_team_schedule(soup)
        except Exception as e:
            logger.error(f"Error parsing team game log: {str(e)}")
            return None 