import asyncio
import logging
import aiohttp
import json
import os
import sys
import ssl
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import modules
from app.db.database import AsyncSessionLocal, init_db
from app.db.service import DatabaseService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NBA API configuration
NBA_API_KEY = os.getenv("NBA_API_KEY")
NBA_API_HOST = os.getenv("NBA_API_HOST", "api-nba-v1.p.rapidapi.com")
NBA_API_BASE_URL = os.getenv("NBA_API_BASE_URL", "https://api-nba-v1.p.rapidapi.com")

# SSL context for API requests
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def fetch_teams():
    """Fetch all NBA teams and store them in the database."""
    logger.info("Fetching teams from NBA API")
    
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        headers = {
            "X-RapidAPI-Key": NBA_API_KEY,
            "X-RapidAPI-Host": NBA_API_HOST
        }
        
        teams_url = f"{NBA_API_BASE_URL}/teams"
        params = {
            "league": "standard"
        }
        
        try:
            async with session.get(teams_url, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"NBA API error: {error_text}")
                    return []
                
                data = await response.json()
                teams = data.get("response", [])
                logger.info(f"Found {len(teams)} teams")
                
                # Store teams in database
                async with AsyncSessionLocal() as db:
                    return await DatabaseService.fetch_and_store_teams(db, teams)
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            return []

async def fetch_team_players(team_id: int, team_name: str):
    """Fetch players for a specific team and store them in the database."""
    logger.info(f"Fetching players for team {team_name} (ID: {team_id})")
    
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        headers = {
            "X-RapidAPI-Key": NBA_API_KEY,
            "X-RapidAPI-Host": NBA_API_HOST
        }
        
        try:
            # First get team details
            team_url = f"{NBA_API_BASE_URL}/teams"
            team_params = {"id": team_id}
            
            async with session.get(team_url, headers=headers, params=team_params) as team_response:
                if team_response.status != 200:
                    logger.error(f"Failed to get team details for team {team_id}")
                    return []
                
                team_data = await team_response.json()
                team_details = team_data.get("response", [{}])[0]
            
            # Then get players for this team
            players_url = f"{NBA_API_BASE_URL}/players"
            players_params = {
                "season": "2023",
                "team": str(team_id)
            }
            
            async with session.get(players_url, headers=headers, params=players_params) as response:
                if response.status != 200:
                    logger.error(f"Failed to get players for team {team_id}")
                    return []
                
                data = await response.json()
                players = data.get("response", [])
                logger.info(f"Found {len(players)} players for team {team_name}")
                
                # Store players in database
                async with AsyncSessionLocal() as db:
                    return await DatabaseService.fetch_and_store_players(db, players, team_details)
        except Exception as e:
            logger.error(f"Error fetching team players: {e}")
            return []

async def fetch_player_stats(player_id: int, player_name: str):
    """Fetch statistics for a specific player and store them in the database."""
    logger.info(f"Fetching statistics for player {player_name} (ID: {player_id})")
    
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        headers = {
            "X-RapidAPI-Key": NBA_API_KEY,
            "X-RapidAPI-Host": NBA_API_HOST
        }
        
        try:
            stats_url = f"{NBA_API_BASE_URL}/players/statistics"
            stats_params = {
                "id": player_id,
                "season": "2023"
            }
            
            async with session.get(stats_url, headers=headers, params=stats_params) as response:
                if response.status != 200:
                    logger.error(f"Failed to get statistics for player {player_id}")
                    return None
                
                data = await response.json()
                stats = data.get("response", [])
                logger.info(f"Found {len(stats)} statistics records for player {player_name}")
                
                # Store statistics in database
                async with AsyncSessionLocal() as db:
                    return await DatabaseService.store_player_stats(db, player_id, stats)
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return None

async def initialize_database():
    """Initialize the database with data from the NBA API."""
    logger.info("Initializing database with NBA data")
    
    try:
        # Initialize database schema
        await init_db()
        
        # Fetch teams
        teams = await fetch_teams()
        
        # Only process NBA teams (first 10 for testing)
        nba_teams = [team for team in teams if team.get("nbaFranchise", False)][:10]
        
        # Fetch players for each team
        all_players = []
        for team in nba_teams:
            team_id = team.get("id")
            team_name = team.get("name")
            if team_id:
                players = await fetch_team_players(team_id, team_name)
                all_players.extend(players)
        
        # Fetch statistics for each player (first 30 for testing)
        for player in all_players[:30]:
            player_id = player.get("id")
            player_name = player.get("name")
            if player_id:
                await fetch_player_stats(player_id, player_name)
        
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise

if __name__ == "__main__":
    if not NBA_API_KEY:
        logger.error("NBA_API_KEY not found in environment variables!")
        sys.exit(1)
    
    # Run the initialization
    asyncio.run(initialize_database()) 