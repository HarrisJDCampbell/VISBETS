import json
import asyncio
import websockets
from typing import Optional, Dict, Any, Callable
from datetime import datetime

class NBAGameService:
    def __init__(self, api_key: str, base_url: str = "wss://api.geniussports.com/nbangss/stream"):
        self.api_key = api_key
        self.base_url = base_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.message_handlers: Dict[str, Callable] = {}
        self._running = False

    async def connect(self, game_id: Optional[str] = None, message_types: str = "sc,ev,gi,te"):
        """Connect to the NBA Game Distribution API WebSocket"""
        query_params = f"?format=json&types={message_types}"
        if game_id:
            query_params += f"&gameId={game_id}"

        self.websocket = await websockets.connect(f"{self.base_url}{query_params}")
        
        # Send authentication message
        auth_message = {
            "type": "authentication",
            "apikey": self.api_key
        }
        await self.websocket.send(json.dumps(auth_message))
        
        # Start listening for messages
        self._running = True
        asyncio.create_task(self._listen_for_messages())

    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            while self._running and self.websocket:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Handle the message based on its type
                message_type = data.get("type")
                if message_type in self.message_handlers:
                    await self.message_handlers[message_type](data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error in WebSocket listener: {e}")

    def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler

    async def disconnect(self):
        """Disconnect from the WebSocket"""
        self._running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def get_game_info(self, game_id: str) -> Dict[str, Any]:
        """Get information about a specific game"""
        if not self.websocket:
            raise ConnectionError("Not connected to WebSocket")
        
        # Request game info
        request = {
            "type": "request",
            "requestType": "gi",
            "gameId": game_id
        }
        await self.websocket.send(json.dumps(request))
        
        # Wait for response (implementation depends on your needs)
        # This is a simplified version
        return {}

    async def get_team_stats(self, game_id: str) -> Dict[str, Any]:
        """Get team statistics for a specific game"""
        if not self.websocket:
            raise ConnectionError("Not connected to WebSocket")
        
        # Request team stats
        request = {
            "type": "request",
            "requestType": "te",
            "gameId": game_id
        }
        await self.websocket.send(json.dumps(request))
        
        # Wait for response (implementation depends on your needs)
        # This is a simplified version
        return {} 