from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any
from ..services.nba_service import NBAGameService
from ..config import get_settings

router = APIRouter(prefix="/api/nba", tags=["nba"])

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    active_connections[game_id] = websocket
    
    settings = get_settings()
    nba_service = NBAGameService(api_key=settings.NBA_API_KEY)
    
    try:
        # Connect to NBA API
        await nba_service.connect(game_id=game_id)
        
        # Register handlers for different message types
        async def handle_game_info(data: Dict[str, Any]):
            await websocket.send_json(data)
            
        async def handle_team_stats(data: Dict[str, Any]):
            await websocket.send_json(data)
            
        async def handle_events(data: Dict[str, Any]):
            await websocket.send_json(data)
            
        nba_service.register_handler("gi", handle_game_info)
        nba_service.register_handler("te", handle_team_stats)
        nba_service.register_handler("ev", handle_events)
        
        # Keep connection alive
        while True:
            try:
                # Wait for client messages
                data = await websocket.receive_text()
                # Process client messages if needed
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        # Cleanup
        if game_id in active_connections:
            del active_connections[game_id]
        await nba_service.disconnect()

@router.get("/game/{game_id}")
async def get_game_info(game_id: str):
    settings = get_settings()
    nba_service = NBAGameService(api_key=settings.NBA_API_KEY)
    
    try:
        await nba_service.connect(game_id=game_id)
        game_info = await nba_service.get_game_info(game_id)
        return game_info
    finally:
        await nba_service.disconnect()

@router.get("/game/{game_id}/stats")
async def get_team_stats(game_id: str):
    settings = get_settings()
    nba_service = NBAGameService(api_key=settings.NBA_API_KEY)
    
    try:
        await nba_service.connect(game_id=game_id)
        team_stats = await nba_service.get_team_stats(game_id)
        return team_stats
    finally:
        await nba_service.disconnect() 