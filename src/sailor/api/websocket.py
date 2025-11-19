"""
WebSocket connection management for real-time features.
"""

from typing import Dict, Set, List
from fastapi import WebSocket
import json


class ConnectionManager:
    """Manages WebSocket connections and rooms."""
    
    def __init__(self):
        # Active connections
        self.active_connections: List[WebSocket] = []
        # Room memberships
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Connection to rooms mapping
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and track a new connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_rooms[websocket] = set()
    
    def disconnect(self, websocket: WebSocket):
        """Remove a connection and clean up room memberships."""
        self.active_connections.remove(websocket)
        
        # Remove from all rooms
        if websocket in self.connection_rooms:
            for room in self.connection_rooms[websocket]:
                if room in self.rooms:
                    self.rooms[room].discard(websocket)
                    if not self.rooms[room]:
                        del self.rooms[room]
            del self.connection_rooms[websocket]
    
    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Connection might be closed
                pass
    
    async def join_room(self, websocket: WebSocket, room: str):
        """Add a connection to a room."""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        self.connection_rooms[websocket].add(room)
    
    async def leave_room(self, websocket: WebSocket, room: str):
        """Remove a connection from a room."""
        if room in self.rooms:
            self.rooms[room].discard(websocket)
            if not self.rooms[room]:
                del self.rooms[room]
        
        if websocket in self.connection_rooms:
            self.connection_rooms[websocket].discard(room)
    
    async def broadcast_to_room(self, message: dict, room: str, exclude: WebSocket = None):
        """Broadcast a message to all connections in a room."""
        if room in self.rooms:
            for connection in self.rooms[room]:
                if connection != exclude:
                    try:
                        await connection.send_json(message)
                    except:
                        # Connection might be closed
                        pass
    
    def get_room_connections(self, room: str) -> List[WebSocket]:
        """Get all connections in a room."""
        return list(self.rooms.get(room, []))
    
    def get_connection_rooms(self, websocket: WebSocket) -> List[str]:
        """Get all rooms a connection is in."""
        return list(self.connection_rooms.get(websocket, []))