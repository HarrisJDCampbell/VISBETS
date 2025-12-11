import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Tuple
import joblib
import os

class PlayerPredictorNN(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, output_size: int = 3):
        super(PlayerPredictorNN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, output_size)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

class NeuralNetTrainer:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
    def train(self, X: torch.Tensor, y: torch.Tensor, 
             epochs: int = 100, batch_size: int = 32) -> Dict:
        """
        Train the neural network model
        """
        input_size = X.shape[1]
        model = PlayerPredictorNN(input_size=input_size)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Convert data to PyTorch tensors
        X = torch.FloatTensor(X)
        y = torch.FloatTensor(y)
        
        # Training loop
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(X)
            loss = criterion(outputs, y)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f'Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.4f}')
        
        # Save the model
        model_path = os.path.join(self.model_dir, 'neural_net.pth')
        torch.save(model.state_dict(), model_path)
        
        return {
            'model_path': model_path,
            'input_size': input_size
        }
    
    def predict(self, X: torch.Tensor, model_path: str) -> torch.Tensor:
        """
        Make predictions using the trained model
        """
        # Load model
        model_info = joblib.load(os.path.join(self.model_dir, 'model_info.joblib'))
        model = PlayerPredictorNN(input_size=model_info['input_size'])
        model.load_state_dict(torch.load(model_path))
        model.eval()
        
        # Make prediction
        with torch.no_grad():
            X = torch.FloatTensor(X)
            predictions = model(X)
        
        return predictions.numpy() 