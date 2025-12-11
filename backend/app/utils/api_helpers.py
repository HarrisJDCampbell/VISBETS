from typing import Dict
import os
from ..config import get_settings

def get_api_headers() -> Dict[str, str]:
    """
    Returns headers required for API-Sports API authentication.
    """
    settings = get_settings()
    return {
        "X-RapidAPI-Key": os.environ.get("NBA_API_KEY", settings.API_SPORTS_KEY),
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    } 