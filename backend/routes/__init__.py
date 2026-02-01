"""
DisasterAI Backend - Routes Package
"""

from routes.disaster_routes import router as disaster_router
from routes.realtime_routes import router as realtime_router

__all__ = [
    "disaster_router",
    "realtime_router"
]
