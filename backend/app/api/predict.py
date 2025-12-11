from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
from ..models.xgb_model import XGBModel
from ..models.nn_model import NNModel
from ..db.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = APIRouter(prefix="/predict", tags=["predictions"])
logger = logging.getLogger(__name__)

# Initialize models
xgb_model = XGBModel()
nn_model = NNModel()

class PredictionRequest(BaseModel):
    player_id: int
    use_neural_network: Optional[bool] = True

class PredictionResponse(BaseModel):
    player_id: int
    predictions: Dict[str, float]
    model_used: str

@router.post("/player", response_model=PredictionResponse)
async def predict_player_stats(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Predict player statistics using either XGBoost or Neural Network model
    """
    try:
        # Get player stats from database
        from ..db.service import DatabaseService
        player_stats = await DatabaseService.get_player_stats(db, request.player_id)
        
        if not player_stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        # Make predictions using selected model
        if request.use_neural_network:
            predictions = nn_model.predict(player_stats)
            model_used = "neural_network"
        else:
            predictions = xgb_model.predict(player_stats)
            model_used = "xgboost"
        
        if not predictions:
            raise HTTPException(status_code=500, detail="Failed to generate predictions")
        
        return PredictionResponse(
            player_id=request.player_id,
            predictions=predictions,
            model_used=model_used
        )
        
    except Exception as e:
        logger.error(f"Error in predict_player_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 