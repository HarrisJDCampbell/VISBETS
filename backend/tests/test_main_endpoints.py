import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession
import json

# Test client
client = TestClient(app)

# Mock data
MOCK_PLAYER = {
    "id": 2544,
    "name": "LeBron James",
    "team": "Los Angeles Lakers",
    "imageUrl": "https://cdn.nba.com/headshots/nba/latest/1040x760/2544.png",
    "predictions": {
        "points": 25.5,
        "assists": 7.2,
        "rebounds": 8.1
    }
}

MOCK_TEAM = {
    "id": 14,
    "name": "Los Angeles Lakers",
    "nickname": "Lakers",
    "code": "LAL",
    "city": "Los Angeles",
    "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Los_Angeles_Lakers_logo.svg/1200px-Los_Angeles_Lakers_logo.svg.png"
}

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_settings():
    return Settings(
        API_SPORTS_KEY="test_key",
        NBA_API_KEY="test_key"
    )

# Test Root Endpoint
def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "VisBets API Running"}

# Test Teams Endpoint
def test_get_teams(mock_db):
    """Test getting all teams"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/teams")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

# Test Players Endpoint
def test_get_players(mock_db):
    """Test getting players with pagination"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/players?page=1&per_page=20")
        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "pagination" in data

# Test Player Details Endpoint
def test_get_player_details(mock_db):
    """Test getting player details"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/players/2544/details")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "id" in data
        assert "name" in data
        assert "predictions" in data

# Test Team Details Endpoint
def test_get_team_details(mock_db):
    """Test getting team details"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/teams/14")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "info" in data
        assert "roster" in data

# Test Top Scorers Endpoint
def test_get_top_scorers(mock_db):
    """Test getting top scorers"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/top-scorers?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 20

# Test Model Training Endpoint
def test_train_models():
    """Test model training endpoint"""
    response = client.post("/train")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Training started in background" in data["message"]

# Test Database Initialization
def test_initialize_database(mock_db):
    """Test database initialization"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/init-db")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["success", "info"]

# Test Error Handling
def test_invalid_player_id():
    """Test handling of invalid player ID"""
    response = client.get("/players/invalid")
    assert response.status_code in [400, 404]

def test_invalid_team_id():
    """Test handling of invalid team ID"""
    response = client.get("/teams/invalid")
    assert response.status_code in [400, 404]

# Test Pagination
def test_players_pagination(mock_db):
    """Test players endpoint pagination"""
    with patch("app.main.get_async_db", return_value=mock_db):
        # Test first page
        response1 = client.get("/players?page=1&per_page=10")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["players"]) <= 10

        # Test second page
        response2 = client.get("/players?page=2&per_page=10")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["players"]) <= 10

        # Verify different pages return different results
        assert data1["players"] != data2["players"]

# Test API Configuration
def test_api_configuration(mock_settings):
    """Test API configuration endpoint"""
    with patch("app.main.get_settings", return_value=mock_settings):
        response = client.get("/test-api")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "api_host" in data

# Test CORS
def test_cors_headers():
    """Test CORS headers"""
    response = client.options("/")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

# Test Cache Management
@pytest.mark.asyncio
async def test_cache_management(mock_db):
    """Test cache management"""
    with patch("app.main.get_async_db", return_value=mock_db):
        # Test cached response
        response1 = client.get("/players/2544")
        assert response1.status_code == 200
        
        # Test cache expiration
        # This would require mocking the time or waiting for cache to expire
        pass

# Test Background Tasks
def test_background_tasks():
    """Test background tasks"""
    # Test model training background task
    response = client.post("/train")
    assert response.status_code == 200
    assert "Training started in background" in response.json()["message"]

# Test Database Session Management
@pytest.mark.asyncio
async def test_database_session(mock_db):
    """Test database session management"""
    with patch("app.main.get_async_db", return_value=mock_db):
        response = client.get("/teams")
        assert response.status_code == 200
        assert mock_db.close.called 