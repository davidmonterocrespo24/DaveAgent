"""
API module for DaveAgent Web Interface
Provides WebSocket and REST endpoints for frontend communication
"""

from src.api.event_emitter import EventEmitter
from src.api.server import app

__all__ = ["EventEmitter", "app"]
