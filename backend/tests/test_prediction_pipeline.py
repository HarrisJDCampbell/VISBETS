import pytest
import numpy as np
from app.models.data_prep import DataPreprocessor
from app.models.ensemble import EnsemblePredictor

@pytest.fixture
def sample_data():
    return {
        'games_played': 10,
        'minutes_played': 30,
        'points': 25,
        'assists': 7,
        'rebounds': 8,
        'steals': 1,
        'blocks': 1,
        'turnovers': 2,
        'personal_fouls': 2,
        'field_goals_made': 10,
        'field_goals_attempted': 20,
        'three_pointers_made': 3,
        'three_pointers_attempted': 8,
        'free_throws_made': 2,
        'free_throws_attempted': 3
    }

def test_data_preprocessor(sample_data):
    preprocessor = DataPreprocessor()
    
    # Test feature preparation
    features = preprocessor.prepare_single_player(sample_data)
    assert features.shape == (1, len(preprocessor.feature_columns))
    
    # Test normalization
    X = np.array([[1, 2, 3], [4, 5, 6]])
    X_normalized, ranges = preprocessor.normalize_features(X)
    assert X_normalized.shape == X.shape
    assert all(0 <= x <= 1 for x in X_normalized.flatten())

def test_ensemble_predictor(sample_data):
    preprocessor = DataPreprocessor()
    ensemble = EnsemblePredictor()
    
    # Prepare sample data
    features = preprocessor.prepare_single_player(sample_data)
    features_normalized, _ = preprocessor.normalize_features(features)
    
    # Test prediction
    prediction = ensemble.predict(features_normalized)
    assert prediction.shape[1] == 3  # points, assists, rebounds
    
    # Test weight updates
    new_weights = {
        'neural_net': 0.5,
        'xgboost': 0.3,
        'random_forest': 0.2
    }
    ensemble.update_weights(new_weights)
    assert ensemble.weights == new_weights

def test_invalid_weights():
    ensemble = EnsemblePredictor()
    invalid_weights = {
        'neural_net': 0.5,
        'xgboost': 0.3,
        'random_forest': 0.1  # Sum < 1.0
    }
    
    with pytest.raises(ValueError):
        ensemble.update_weights(invalid_weights) 