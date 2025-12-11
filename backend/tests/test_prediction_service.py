import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.prediction_service import PredictionService
import numpy as np
import pandas as pd

@pytest.fixture
def prediction_service():
    return PredictionService()

@pytest.fixture
def mock_player_data():
    return [
        {
            "points": 25,
            "assists": 7,
            "rebounds": 8,
            "minutes": 35,
            "fieldGoalsMade": 10,
            "fieldGoalsAttempted": 20,
            "threePointersMade": 3,
            "threePointersAttempted": 8,
            "freeThrowsMade": 2,
            "freeThrowsAttempted": 3,
            "offensiveRebounds": 2,
            "defensiveRebounds": 6,
            "steals": 1,
            "blocks": 1,
            "turnovers": 3,
            "fouls": 2
        }
    ]

@pytest.fixture
def mock_training_data():
    return pd.DataFrame({
        'points': np.random.normal(20, 5, 100),
        'assists': np.random.normal(5, 2, 100),
        'rebounds': np.random.normal(7, 3, 100),
        'minutes': np.random.normal(30, 5, 100),
        'fieldGoalsMade': np.random.normal(8, 3, 100),
        'fieldGoalsAttempted': np.random.normal(16, 4, 100),
        'threePointersMade': np.random.normal(2, 1, 100),
        'threePointersAttempted': np.random.normal(6, 2, 100),
        'freeThrowsMade': np.random.normal(3, 1, 100),
        'freeThrowsAttempted': np.random.normal(4, 1, 100),
        'offensiveRebounds': np.random.normal(1, 1, 100),
        'defensiveRebounds': np.random.normal(5, 2, 100),
        'steals': np.random.normal(1, 0.5, 100),
        'blocks': np.random.normal(0.5, 0.5, 100),
        'turnovers': np.random.normal(2, 1, 100),
        'fouls': np.random.normal(2, 1, 100)
    })

# Test Prediction Service Initialization
def test_prediction_service_init(prediction_service):
    """Test prediction service initialization"""
    assert prediction_service is not None
    assert hasattr(prediction_service, 'models')
    assert hasattr(prediction_service, 'scaler')

# Test Model Training
def test_train_models(prediction_service, mock_training_data):
    """Test model training"""
    prediction_service.train(mock_training_data)
    assert prediction_service.models is not None
    assert len(prediction_service.models) > 0

# Test Predictions
def test_predict(prediction_service, mock_player_data):
    """Test making predictions"""
    predictions = prediction_service.predict(mock_player_data)
    assert isinstance(predictions, dict)
    assert "points" in predictions
    assert "assists" in predictions
    assert "rebounds" in predictions
    assert all(isinstance(v, (int, float)) for v in predictions.values())

# Test Data Preprocessing
def test_preprocess_data(prediction_service, mock_player_data):
    """Test data preprocessing"""
    processed_data = prediction_service._preprocess_data(mock_player_data)
    assert isinstance(processed_data, pd.DataFrame)
    assert not processed_data.empty
    assert all(col in processed_data.columns for col in [
        'points', 'assists', 'rebounds', 'minutes',
        'fieldGoalsMade', 'fieldGoalsAttempted'
    ])

# Test Model Evaluation
def test_evaluate_models(prediction_service, mock_training_data):
    """Test model evaluation"""
    # Split data into train and test
    train_data = mock_training_data.iloc[:80]
    test_data = mock_training_data.iloc[80:]
    
    # Train models
    prediction_service.train(train_data)
    
    # Evaluate models
    evaluation = prediction_service.evaluate_models(test_data)
    assert isinstance(evaluation, dict)
    assert all(metric in evaluation for metric in ['mse', 'mae', 'r2'])

# Test Feature Importance
def test_feature_importance(prediction_service, mock_training_data):
    """Test feature importance calculation"""
    prediction_service.train(mock_training_data)
    importance = prediction_service.get_feature_importance()
    assert isinstance(importance, dict)
    assert len(importance) > 0
    assert all(isinstance(v, float) for v in importance.values())

# Test Model Persistence
def test_save_load_models(prediction_service, mock_training_data, tmp_path):
    """Test saving and loading models"""
    # Train models
    prediction_service.train(mock_training_data)
    
    # Save models
    model_path = tmp_path / "models"
    prediction_service.save_models(str(model_path))
    assert model_path.exists()
    
    # Load models
    new_service = PredictionService()
    new_service.load_models(str(model_path))
    assert new_service.models is not None
    assert len(new_service.models) == len(prediction_service.models)

# Test Prediction Confidence
def test_prediction_confidence(prediction_service, mock_player_data):
    """Test prediction confidence calculation"""
    predictions = prediction_service.predict(mock_player_data)
    confidence = prediction_service.get_prediction_confidence(predictions)
    assert isinstance(confidence, dict)
    assert all(0 <= v <= 1 for v in confidence.values())

# Test Data Validation
def test_validate_input_data(prediction_service, mock_player_data):
    """Test input data validation"""
    is_valid = prediction_service._validate_input_data(mock_player_data)
    assert is_valid

def test_validate_input_data_invalid():
    """Test input data validation with invalid data"""
    service = PredictionService()
    invalid_data = [{"invalid": "data"}]
    is_valid = service._validate_input_data(invalid_data)
    assert not is_valid

# Test Model Performance Metrics
def test_model_performance_metrics(prediction_service, mock_training_data):
    """Test model performance metrics calculation"""
    # Split data into train and test
    train_data = mock_training_data.iloc[:80]
    test_data = mock_training_data.iloc[80:]
    
    # Train models
    prediction_service.train(train_data)
    
    # Get performance metrics
    metrics = prediction_service.get_model_performance_metrics(test_data)
    assert isinstance(metrics, dict)
    assert all(metric in metrics for metric in ['accuracy', 'precision', 'recall'])

# Test Prediction Thresholds
def test_prediction_thresholds(prediction_service, mock_player_data):
    """Test prediction threshold validation"""
    predictions = prediction_service.predict(mock_player_data)
    thresholds = {
        'points': 20,
        'assists': 5,
        'rebounds': 7
    }
    is_valid = prediction_service._validate_prediction_thresholds(predictions, thresholds)
    assert is_valid

# Test Data Normalization
def test_data_normalization(prediction_service, mock_player_data):
    """Test data normalization"""
    normalized_data = prediction_service._normalize_data(mock_player_data)
    assert isinstance(normalized_data, pd.DataFrame)
    assert not normalized_data.empty
    assert all(col in normalized_data.columns for col in mock_player_data[0].keys()) 