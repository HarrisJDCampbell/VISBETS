import os
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class OddsAPI:
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        if not self.api_key:
            raise ValueError("ODDS_API_KEY environment variable is required")
        
        self.base_url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
        self.headers = {
            'x-api-key': self.api_key
        }
        
    def get_player_props(self, player_name: str) -> Optional[Dict]:
        """
        Get player props from The Odds API
        Returns the most recent odds for the player's next game
        """
        try:
            # Get all NBA games with odds
            params = {
                'regions': 'us',
                'markets': 'player_props',
                'oddsFormat': 'american'
            }
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"Odds API error: {response.text}")
                return None
                
            games = response.json()
            
            # Find props for the specific player
            for game in games:
                if 'bookmakers' not in game:
                    continue
                    
                for bookmaker in game['bookmakers']:
                    if 'markets' not in bookmaker:
                        continue
                        
                    for market in bookmaker['markets']:
                        if market['key'] != 'player_props':
                            continue
                            
                        for outcome in market['outcomes']:
                            if outcome['name'].lower() == player_name.lower():
                                return {
                                    'game_time': game['commence_time'],
                                    'home_team': game['home_team'],
                                    'away_team': game['away_team'],
                                    'bookmaker': bookmaker['title'],
                                    'prop_type': outcome['description'],
                                    'line': float(outcome['price']),
                                    'over_odds': outcome.get('over_odds', None),
                                    'under_odds': outcome.get('under_odds', None)
                                }
            
            logger.warning(f"No props found for player: {player_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching odds: {e}")
            return None
    
    def calculate_confidence(self, prediction: float, line: float) -> Dict:
        """
        Calculate confidence percentage for over/under
        Returns confidence percentage and recommended bet
        """
        diff = prediction - line
        confidence = abs(diff) / line * 100
        
        return {
            'prediction': prediction,
            'line': line,
            'difference': diff,
            'confidence': confidence,
            'recommendation': 'over' if diff > 0 else 'under',
            'edge': abs(diff)
        }

class OddsComparison:
    def __init__(self):
        self.odds_api = OddsAPI()
        
    def compare_prediction(self, player_name: str, prediction: float, stat_type: str) -> Dict:
        """
        Compare model prediction with betting line
        Returns comparison metrics and betting recommendation
        """
        # Get odds from API
        props = self.odds_api.get_player_props(player_name)
        
        if not props:
            return {
                'error': 'No odds available',
                'prediction': prediction
            }
        
        # Find matching prop type
        if stat_type.lower() not in props['prop_type'].lower():
            return {
                'error': f"No {stat_type} props available",
                'prediction': prediction,
                'available_props': props['prop_type']
            }
        
        # Calculate confidence
        comparison = self.odds_api.calculate_confidence(prediction, props['line'])
        
        return {
            'player': player_name,
            'game': f"{props['away_team']} @ {props['home_team']}",
            'game_time': props['game_time'],
            'bookmaker': props['bookmaker'],
            'prop_type': props['prop_type'],
            'model_prediction': prediction,
            'betting_line': props['line'],
            'confidence': comparison['confidence'],
            'recommendation': comparison['recommendation'],
            'edge': comparison['edge'],
            'over_odds': props['over_odds'],
            'under_odds': props['under_odds']
        } 