from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from ..utils.odds import OddsComparison
from ..models.xgb_model import XGBModel
from ..models.nn_model import NNModel
from ..db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = APIRouter(prefix="/compare", tags=["comparisons"])
logger = logging.getLogger(__name__)

# Initialize models and odds comparison
xgb_model = XGBModel()
nn_model = NNModel()
odds_comparison = OddsComparison()

class ComparisonRequest(BaseModel):
    player_id: int
    stat_type: str  # points, assists, rebounds, three_pointers, par
    use_neural_network: Optional[bool] = True

class ComparisonResponse(BaseModel):
    player: str
    game: str
    game_time: str
    bookmaker: str
    prop_type: str
    model_prediction: float
    betting_line: float
    confidence: float
    recommendation: str
    edge: float
    over_odds: Optional[int]
    under_odds: Optional[int]
    error: Optional[str]

@router.post("/player", response_model=ComparisonResponse)
async def compare_prediction(
    request: ComparisonRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Compare model prediction with betting line for a player
    """
    try:
        # Get player info from database
        from ..db.service import DatabaseService
        player_info = await DatabaseService.get_player_info(db, request.player_id)
        
        if not player_info:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Get player stats
        player_stats = await DatabaseService.get_player_stats(db, request.player_id)
        if not player_stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        # Get prediction from appropriate model
        if request.use_neural_network:
            predictions = nn_model.predict(player_stats)
        else:
            predictions = xgb_model.predict(player_stats)
        
        if not predictions or request.stat_type not in predictions:
            raise HTTPException(
                status_code=400,
                detail=f"No prediction available for {request.stat_type}"
            )
        
        # Compare with betting line
        comparison = odds_comparison.compare_prediction(
            player_info['name'],
            predictions[request.stat_type],
            request.stat_type
        )
        
        if 'error' in comparison:
            raise HTTPException(status_code=400, detail=comparison['error'])
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error in compare_prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 