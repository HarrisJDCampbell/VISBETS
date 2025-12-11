from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from dotenv import load_dotenv
import aiohttp
import json
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import ssl
import certifi
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VisBets API",
    description="API for VisBets sports betting analytics platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import local modules after app creation
from .config import get_settings, Settings
from .utils.api_helpers import get_api_headers
from .services.api_sports import APISportsService, get_api_service
from .routes import predictions
from .routers import nba, scraper, slate, player_detail, mock_slate
from .services.prediction_service import PredictionService
from .services.data_collector import DataCollector
from .db.database import get_async_db, init_db, init_db_sync, AsyncSessionLocal
from .db.service import DatabaseService

# NBA API configuration
NBA_API_KEY = os.getenv("NBA_API_KEY")
NBA_API_HOST = os.getenv("NBA_API_HOST", "api-nba-v1.p.rapidapi.com")
NBA_API_BASE_URL = os.getenv("NBA_API_BASE_URL", "https://api-nba-v1.p.rapidapi.com")

if not NBA_API_KEY:
    logger.error("NBA_API_KEY not found in environment variables!")
    raise ValueError("NBA_API_KEY environment variable is required")

# Initialize services
prediction_service = PredictionService()
data_collector = DataCollector()

# Create SSL context with verification disabled (for development only)
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Initialize database synchronously (for startup)
init_db_sync()

# Cache for API responses
cache = {}
CACHE_DURATION = timedelta(hours=1)

# Mock data for testing
MOCK_PLAYERS = [
    {
        "id": 2544,
        "name": "LeBron James",
        "team": "Los Angeles Lakers",
        "imageUrl": "https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png",
        "predictions": {
            "points": 25.5,
            "assists": 7.2,
            "rebounds": 8.1
        }
    },
    {
        "id": 201939,
        "name": "Stephen Curry",
        "team": "Golden State Warriors",
        "imageUrl": "https://cdn.nba.com/headshots/nba/latest/1040x760/201939.png",
        "predictions": {
            "points": 28.3,
            "assists": 6.5,
            "rebounds": 5.2
        }
    },
    {
        "id": 203507,
        "name": "Giannis Antetokounmpo",
        "team": "Milwaukee Bucks",
        "imageUrl": "https://cdn.nba.com/headshots/nba/latest/1040x760/203507.png",
        "predictions": {
            "points": 31.2,
            "assists": 5.8,
            "rebounds": 12.4
        }
    }
]

class Player(BaseModel):
    id: int
    name: str
    team: str
    imageUrl: str
    predictions: dict
    season_stats: Optional[dict] = None
    recent_games: Optional[List[dict]] = None

async def get_nba_api_headers():
    return {
        "X-RapidAPI-Key": NBA_API_KEY,
        "X-RapidAPI-Host": NBA_API_HOST
    }

async def fetch_from_nba_api(endpoint: str, params: dict = None, db: AsyncSession = None):
    """Fetch data from NBA API with database caching"""
    try:
        if db:
            # Try to get cached response from database
            cached_response = await DatabaseService.get_cached_api_response(db, endpoint, params)
            if cached_response:
                logger.info(f"Using cached response for {endpoint}")
                return cached_response
        
        # If no cached response, fetch from API
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = await get_nba_api_headers()
            async with session.get(f"{NBA_API_BASE_URL}/{endpoint}", headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"NBA API error: {error_text}")
                    raise HTTPException(status_code=response.status, detail=f"NBA API request failed: {error_text}")
                
                data = await response.json()
                
                # Cache the response in database if db session is provided
                if db:
                    await DatabaseService.cache_api_response(db, endpoint, params, data)
                
                return data
    except Exception as e:
        logger.error(f"Error fetching from NBA API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"status": "VisBets API Running"}

@app.get("/test-nba-api")
async def test_nba_api():
    """Test endpoint to verify NBA API connection"""
    try:
        logger.info("Testing NBA API connection...")
        logger.info(f"Using API Key: {NBA_API_KEY[:10]}...")
        
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                "X-RapidAPI-Key": NBA_API_KEY,
                "X-RapidAPI-Host": NBA_API_HOST
            }
            
            # Get current season
            logger.info("Getting current season...")
            season_url = f"{NBA_API_BASE_URL}/seasons"
            logger.info(f"Season URL: {season_url}")
            
            async with session.get(season_url, headers=headers) as season_response:
                if season_response.status != 200:
                    error_text = await season_response.text()
                    logger.error(f"NBA API error getting seasons: {error_text}")
                    return {
                        "status": "error",
                        "message": f"NBA API returned status {season_response.status}",
                        "details": error_text,
                        "request_info": {
                            "url": season_url,
                            "headers": {k: v[:10] + "..." if k == "X-RapidAPI-Key" else v for k, v in headers.items()}
                        }
                    }
                
                season_data = await season_response.json()
                logger.info(f"Season data: {season_data}")
                current_season = "2023"  # Use the correct season format
                logger.info(f"Current season: {current_season}")
            
            # Then, get active players
            logger.info("Getting active players...")
            players_url = f"{NBA_API_BASE_URL}/players"
            params = {
                "season": current_season,
                "team": "1"  # Start with Atlanta Hawks (team ID 1)
            }
            logger.info(f"Players URL: {players_url}")
            logger.info(f"Params: {params}")
            
            async with session.get(players_url, headers=headers, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"NBA API error getting players: {error_text}")
                    return {
                        "status": "error",
                        "message": f"NBA API returned status {response.status}",
                        "details": error_text,
                        "request_info": {
                            "url": players_url,
                            "params": params,
                            "headers": {k: v[:10] + "..." if k == "X-RapidAPI-Key" else v for k, v in headers.items()}
                        }
                    }
                
                players_data = await response.json()
                logger.info(f"Successfully retrieved {len(players_data.get('response', []))} players")
                
                return {
                    "status": "success",
                    "message": "NBA API connection successful",
                    "data": {
                        "season": current_season,
                        "players_count": len(players_data.get('response', [])),
                        "sample_player": players_data.get('response', [])[0] if players_data.get('response') else None
                    }
                }
    except Exception as e:
        logger.error(f"Error testing NBA API: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/teams")
async def get_teams(db: AsyncSession = Depends(get_async_db)):
    """Get all NBA teams from database or API"""
    try:
        logger.info("Fetching all NBA teams")
        
        # Try to get teams from database first
        teams = await DatabaseService.fetch_teams_from_db(db)
        
        # If no teams in database, fetch from API and store them
        if not teams:
            logger.info("No teams found in database, fetching from API")
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
                
                async with session.get(teams_url, headers=headers, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"NBA API error: {error_text}")
                        raise HTTPException(status_code=500, detail=f"NBA API error: {error_text}")
                    
                    data = await response.json()
                    api_teams = data.get("response", [])
                    logger.info(f"Found {len(api_teams)} teams in API")
                    
                    # Store teams in database
                    teams = await DatabaseService.fetch_and_store_teams(db, api_teams)
        
        return teams
                
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players")
async def get_players(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """Get players from database or API"""
    try:
        logger.info(f"Fetching players - page: {page}, per_page: {per_page}")
        
        # Try to get players from database first
        players_data = await DatabaseService.fetch_players_from_db(db, page, per_page)
        
        # If no players in database, fetch a sample team from API
        if not players_data["players"]:
            logger.info("No players found in database, fetching from API")
            
            # First get teams
            teams = await get_teams(db)
            
            # Get players for first team
            if teams:
                nba_teams = [team for team in teams if team.get("nbaFranchise", True)]
                
                if nba_teams:
                    team = nba_teams[0]
                    team_id = team["id"]
                    
                    # Fetch players from API
                    timeout = aiohttp.ClientTimeout(total=30)
                    connector = aiohttp.TCPConnector(ssl=ssl_context)
                    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                        headers = {
                            "X-RapidAPI-Key": NBA_API_KEY,
                            "X-RapidAPI-Host": NBA_API_HOST
                        }
                        
                        params = {
                            "season": "2023",
                            "team": str(team_id)
                        }
                        
                        async with session.get(
                            f"{NBA_API_BASE_URL}/players",
                            headers=headers,
                            params=params
                        ) as response:
                            if response.status != 200:
                                logger.error(f"Failed to get players for team {team_id}")
                                return {"players": [], "pagination": players_data["pagination"]}
                            
                            data = await response.json()
                            players = data.get("response", [])
                            
                            # Store players in database
                            players_list = await DatabaseService.fetch_and_store_players(db, players, team)
                            
                            # Update players data
                            players_data["players"] = players_list
        
        return players_data
                
    except Exception as e:
        logger.error(f"Error in get_players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/{player_id}")
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get detailed information for a specific player"""
    try:
        # Check if we have a cached API response
        cached_data = await DatabaseService.get_cached_api_response(
            db, 
            f"player/{player_id}", 
            {"full": "true"}
        )
        
        if cached_data:
            return cached_data
        
        # Get player info from API
        player_data = await fetch_from_nba_api("players", {"id": player_id}, db)
        player = player_data.get("response", [{}])[0]
        
        # Get team info
        team_id = player.get("team", {}).get("id")
        team_data = await fetch_from_nba_api("teams", {"id": team_id}, db)
        team = team_data.get("response", [{}])[0]
        
        # Get season stats
        stats_data = await fetch_from_nba_api("players/statistics", {
            "player": player_id,
            "season": "2023"
        }, db)
        
        # Get recent games
        games_data = await fetch_from_nba_api("games", {
            "team": team_id,
            "season": "2023"
        }, db)
        
        # Generate predictions
        stats = stats_data.get("response", [])
        recent_games = stats[:10] if len(stats) >= 10 else stats
        predictions = prediction_service.predict(recent_games)
        
        # Create detailed player object
        player_obj = Player(
            id=player["id"],
            name=f"{player['firstname']} {player['lastname']}",
            team=team.get("name", "Unknown"),
            imageUrl=f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player['id']}.png",
            predictions=predictions,
            season_stats=stats,
            recent_games=games_data.get("response", [])[:10]
        )
        
        result = player_obj.dict()
        
        # Cache the result in the database
        await DatabaseService.cache_api_response(db, f"player/{player_id}", {"full": "true"}, result)
        
        return result
    except Exception as e:
        logger.error(f"Error in get_player: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/{player_id}/details")
async def get_player_details(
    player_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get comprehensive player details including predictions"""
    try:
        # Check for cached response
        cached_data = await DatabaseService.get_cached_api_response(
            db, 
            f"player/{player_id}/details", 
            {}
        )
        
        if cached_data:
            return cached_data
        
        # Get basic player info
        player = await get_player(player_id, db)
        
        # Get more detailed predictions
        predictions = prediction_service.predict(player["recent_games"])
        
        # Add model confidence
        predictions["model_confidence"] = 0.85  # This would be calculated based on model performance
        
        player["predictions"] = predictions
        
        # Cache the result
        await DatabaseService.cache_api_response(db, f"player/{player_id}/details", {}, player)
        
        return player
    except Exception as e:
        logger.error(f"Error in get_player_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_models(background_tasks: BackgroundTasks):
    """Train prediction models with latest data"""
    async def train_models_task():
        try:
            # Collect training data
            training_data = await data_collector.collect_training_data()
            
            # Train models
            prediction_service.train(training_data)
            
            print("Models trained successfully")
        except Exception as e:
            print(f"Error training models: {str(e)}")
    
    # Start training in background
    background_tasks.add_task(train_models_task)
    
    return {"message": "Training started in background"}

@app.get("/test-api")
async def test_api(settings: Settings = Depends(get_settings)):
    """
    Test endpoint to verify API key configuration
    """
    headers = get_api_headers()
    return {
        "message": "API configuration loaded successfully",
        "api_host": headers["X-RapidAPI-Host"]
    }

@app.get("/teams/{team_id}")
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_async_db),
    api_service: APISportsService = Depends(get_api_service)
):
    """
    Get team information and roster
    """
    try:
        # Check for cached response
        cached_data = await DatabaseService.get_cached_api_response(
            db, 
            f"team/{team_id}", 
            {"full": "true"}
        )
        
        if cached_data:
            return cached_data
        
        team_info = await api_service.get_team_info(team_id)
        team_players = await api_service.get_team_players(team_id)
        
        result = {
            "info": team_info,
            "roster": team_players
        }
        
        # Cache the result
        await DatabaseService.cache_api_response(db, f"team/{team_id}", {"full": "true"}, result)
        
        return result
    except Exception as e:
        logger.error(f"Error in get_team: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/top-scorers")
async def get_top_scorers(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """Get top scorers from the database or fetch from API if not available."""
    try:
        # Try to get top scorers from database
        top_scorers = await DatabaseService.get_top_scorers(db, limit=limit)
        
        if not top_scorers:
            logger.info("No top scorers found in database, fetching from API...")
            
            # Fetch from API
            api_data = await fetch_from_nba_api("players/statistics", {
                "season": "2023",
                "sort": "points",
                "order": "desc",
                "limit": limit
            }, db)
            
            if not api_data or "response" not in api_data:
                logger.warning("No data from API, returning mock data")
                return MOCK_PLAYERS[:limit]
            
            # Process API data
            players_data = api_data["response"]
            top_scorers = []
            
            for player_data in players_data:
                player = player_data.get("player", {})
                stats = player_data.get("statistics", {})
                
                if not player or not stats:
                    continue
                
                top_scorers.append({
                    "id": player.get("id"),
                    "name": f"{player.get('firstname', '')} {player.get('lastname', '')}".strip(),
                    "team": player.get("team", {}).get("name", "Unknown"),
                    "imageUrl": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player.get('id')}.png",
                    "predictions": {
                        "points": float(stats.get("points", 0)),
                        "assists": float(stats.get("assists", 0)),
                        "rebounds": float(stats.get("totReb", 0))
                    }
                })
            
            if not top_scorers:
                logger.warning("No valid players found in API response, returning mock data")
                return MOCK_PLAYERS[:limit]
        
        return top_scorers
    except Exception as e:
        logger.error(f"Error getting top scorers: {e}")
        return MOCK_PLAYERS[:limit]

@app.get("/init-db")
async def initialize_database(
    force: bool = Query(False, description="Force reinitialization of database"),
    db: AsyncSession = Depends(get_async_db)
):
    """Initialize or reinitialize the database."""
    try:
        if force:
            logger.info("Force reinitializing database...")
            # Drop all tables and recreate them
            async with db.begin():
                await db.run_sync(lambda conn: Base.metadata.drop_all(conn))
                await db.run_sync(lambda conn: Base.metadata.create_all(conn))
            
            # Start background task to fetch and store data
            background_tasks = BackgroundTasks()
            background_tasks.add_task(init_db_task)
            
            return {
                "status": "success",
                "message": "Database reinitialization started in background",
                "note": "This process may take several minutes to complete"
            }
        else:
            # Check if database is already initialized
            teams = await DatabaseService.fetch_teams_from_db(db)
            if teams:
                return {
                    "status": "info",
                    "message": "Database is already initialized",
                    "teams_count": len(teams),
                    "note": "Use force=true to reinitialize"
                }
            
            # Initialize database
            await init_db()
            return {
                "status": "success",
                "message": "Database initialized successfully"
            }
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def init_db_task():
    """Background task to initialize database with data."""
    try:
        logger.info("Starting database initialization task...")
        
        # Get current season
        season_data = await fetch_from_nba_api("seasons")
        current_season = "2023"  # Use the correct season format
        
        # Fetch and store teams
        teams_data = await fetch_from_nba_api("teams")
        if teams_data and "response" in teams_data:
            async with AsyncSessionLocal() as db:
                await DatabaseService.fetch_and_store_teams(db, teams_data["response"])
        
        # Fetch and store players for each team
        async with AsyncSessionLocal() as db:
            teams = await DatabaseService.fetch_teams_from_db(db)
            for team in teams:
                players_data = await fetch_from_nba_api("players", {
                    "season": current_season,
                    "team": team["id"]
                })
                if players_data and "response" in players_data:
                    await DatabaseService.fetch_and_store_players(db, players_data["response"], team)
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error in database initialization task: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks on startup."""
    try:
        # Initialize database
        await init_db()
        
        # Start background task to clear expired cache
        asyncio.create_task(clear_expired_cache_task())
    except Exception as e:
        logger.error(f"Error in startup event: {e}")

async def clear_expired_cache_task():
    """Background task to periodically clear expired cache entries."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                cleared = await DatabaseService.clear_expired_cache(db)
                if cleared > 0:
                    logger.info(f"Cleared {cleared} expired cache entries")
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
        
        # Wait for 1 hour before next cleanup
        await asyncio.sleep(3600)

# Include routers
app.include_router(predictions.router)
app.include_router(nba.router)
app.include_router(scraper.router)
app.include_router(slate.router)
app.include_router(player_detail.router)
app.include_router(mock_slate.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 