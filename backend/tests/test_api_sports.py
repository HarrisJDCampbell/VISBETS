import pytest
from unittest.mock import Mock, patch
from app.services.api_sports import APISportsService
from app.utils.api_helpers import get_api_headers

@pytest.fixture
def mock_response():
    return {
        "response": [
            {
                "id": 1,
                "name": "Test Player",
                "team": "Test Team",
                "points": 25,
                "assists": 7,
                "rebounds": 8
            }
        ]
    }

@pytest.mark.asyncio
async def test_get_player_stats(mock_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: mock_response
        )
        
        service = APISportsService()
        result = await service.get_player_stats(1)
        
        assert result == mock_response
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_get_player_info(mock_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: mock_response
        )
        
        service = APISportsService()
        result = await service.get_player_info(1)
        
        assert result == mock_response
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_api_headers():
    headers = get_api_headers()
    assert "X-RapidAPI-Key" in headers
    assert "X-RapidAPI-Host" in headers
    assert headers["X-RapidAPI-Host"] == "api-nba-v1.p.rapidapi.com" 