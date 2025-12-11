import pytest
from fastapi.testclient import TestClient
import fastapi.testclient
print("FASTAPI TESTCLIENT FILE:", fastapi.testclient.__file__)
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime
import asyncio
from app.main import app
from app.services.nba_service import NBAGameService
from app.config import Settings

# Test client
client = TestClient(app)

# Mock data
MOCK_GAME_DATA = {
    "type": "gi",
    "gameId": "12345",
    "homeTeam": "Lakers",
    "awayTeam": "Warriors",
    "score": {
        "home": 98,
        "away": 95
    }
}

MOCK_TEAM_STATS = {
    "type": "te",
    "gameId": "12345",
    "homeTeam": {
        "points": 98,
        "rebounds": 45,
        "assists": 25
    },
    "awayTeam": {
        "points": 95,
        "rebounds": 42,
        "assists": 23
    }
}

MOCK_EVENT = {
    "type": "ev",
    "gameId": "12345",
    "eventType": "SCORE",
    "description": "3-point field goal made"
}

@pytest.fixture
def mock_settings():
    return Settings(
        NBA_API_KEY="test_key",
        NBA_API_BASE_URL="wss://test.api.com"
    )

@pytest.fixture
def mock_nba_service():
    service = NBAGameService(api_key="test_key")
    service.websocket = AsyncMock()
    return service

# Test NBA API Configuration
def test_nba_api_configuration():
    """Test NBA API configuration loading"""
    response = client.get("/test-nba-api")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["success", "error"]

# Test WebSocket Connection
@pytest.mark.asyncio
async def test_websocket_connection(mock_nba_service):
    """Test WebSocket connection and message handling"""
    with patch("app.routers.nba.NBAGameService", return_value=mock_nba_service):
        with client.websocket_connect("/api/nba/ws/12345") as websocket:
            # Simulate receiving game info
            mock_nba_service.websocket.recv.return_value = json.dumps(MOCK_GAME_DATA)
            data = websocket.receive_json()
            assert data["type"] == "gi"
            assert data["gameId"] == "12345"

# Test Game Info Endpoint
def test_get_game_info(mock_nba_service):
    """Test getting game information"""
    with patch("app.routers.nba.NBAGameService", return_value=mock_nba_service):
        response = client.get("/api/nba/game/12345")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

# Test Team Stats Endpoint
def test_get_team_stats(mock_nba_service):
    """Test getting team statistics"""
    with patch("app.routers.nba.NBAGameService", return_value=mock_nba_service):
        response = client.get("/api/nba/game/12345/stats")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

# Test NBA Service Methods
@pytest.mark.asyncio
async def test_nba_service_connect(mock_nba_service):
    """Test NBA service connection"""
    await mock_nba_service.connect(game_id="12345")
    assert mock_nba_service.websocket.send.called
    assert mock_nba_service._running

@pytest.mark.asyncio
async def test_nba_service_disconnect(mock_nba_service):
    """Test NBA service disconnection"""
    await mock_nba_service.disconnect()
    assert not mock_nba_service._running
    assert mock_nba_service.websocket.close.called

@pytest.mark.asyncio
async def test_nba_service_message_handling(mock_nba_service):
    """Test NBA service message handling"""
    handler_called = False
    
    async def test_handler(data):
        nonlocal handler_called
        handler_called = True
        assert data["type"] == "gi"
    
    mock_nba_service.register_handler("gi", test_handler)
    await mock_nba_service._listen_for_messages()
    assert handler_called

# Test Error Handling
def test_invalid_game_id():
    """Test handling of invalid game ID"""
    response = client.get("/api/nba/game/invalid")
    assert response.status_code in [400, 404]

@pytest.mark.asyncio
async def test_websocket_error_handling(mock_nba_service):
    """Test WebSocket error handling"""
    mock_nba_service.websocket.recv.side_effect = Exception("Connection error")
    with pytest.raises(Exception):
        await mock_nba_service._listen_for_messages()

# Test Message Types
@pytest.mark.asyncio
async def test_game_info_message(mock_nba_service):
    """Test handling of game info message type"""
    handler_called = False
    
    async def test_handler(data):
        nonlocal handler_called
        handler_called = True
        assert data["type"] == "gi"
        assert "gameId" in data
    
    mock_nba_service.register_handler("gi", test_handler)
    mock_nba_service.websocket.recv.return_value = json.dumps(MOCK_GAME_DATA)
    await mock_nba_service._listen_for_messages()
    assert handler_called

@pytest.mark.asyncio
async def test_team_stats_message(mock_nba_service):
    """Test handling of team stats message type"""
    handler_called = False
    
    async def test_handler(data):
        nonlocal handler_called
        handler_called = True
        assert data["type"] == "te"
        assert "homeTeam" in data
        assert "awayTeam" in data
    
    mock_nba_service.register_handler("te", test_handler)
    mock_nba_service.websocket.recv.return_value = json.dumps(MOCK_TEAM_STATS)
    await mock_nba_service._listen_for_messages()
    assert handler_called

@pytest.mark.asyncio
async def test_event_message(mock_nba_service):
    """Test handling of event message type"""
    handler_called = False
    
    async def test_handler(data):
        nonlocal handler_called
        handler_called = True
        assert data["type"] == "ev"
        assert "eventType" in data
        assert "description" in data
    
    mock_nba_service.register_handler("ev", test_handler)
    mock_nba_service.websocket.recv.return_value = json.dumps(MOCK_EVENT)
    await mock_nba_service._listen_for_messages()
    assert handler_called

# Test Configuration Loading
def test_settings_loading(mock_settings):
    """Test settings loading from environment"""
    assert mock_settings.NBA_API_KEY == "test_key"
    assert mock_settings.NBA_API_BASE_URL == "wss://test.api.com"

# Test WebSocket Connection Management
@pytest.mark.asyncio
async def test_websocket_connection_management():
    """Test WebSocket connection management"""
    with client.websocket_connect("/api/nba/ws/12345") as websocket:
        # Test connection is established
        assert websocket.client_state.connected
        
        # Test connection is closed properly
        websocket.close()
        assert not websocket.client_state.connected

# Test Multiple Message Types
@pytest.mark.asyncio
async def test_multiple_message_types(mock_nba_service):
    """Test handling of multiple message types"""
    messages_received = []
    
    async def test_handler(data):
        messages_received.append(data["type"])
    
    mock_nba_service.register_handler("gi", test_handler)
    mock_nba_service.register_handler("te", test_handler)
    mock_nba_service.register_handler("ev", test_handler)
    
    # Simulate receiving multiple message types
    mock_nba_service.websocket.recv.side_effect = [
        json.dumps(MOCK_GAME_DATA),
        json.dumps(MOCK_TEAM_STATS),
        json.dumps(MOCK_EVENT)
    ]
    
    await mock_nba_service._listen_for_messages()
    assert "gi" in messages_received
    assert "te" in messages_received
    assert "ev" in messages_received 