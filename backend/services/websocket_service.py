"""
DisasterAI Backend - WebSocket Service
Handles real-time updates for disaster monitoring
"""

import asyncio
import json
from typing import Dict, List, Set
from datetime import datetime
import logging

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from logging_config import get_logger
from services.disaster_service import get_disaster_service
from services.alert_service import get_alert_service
from models import DisasterEvent, AlertMessage


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscribed_categories: Dict[str, Set[str]] = {}  # connection_id -> categories
        self.logger = get_logger(__name__)

    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscribed_categories[client_id] = set()
        self.logger.info(f"WebSocket client connected: {client_id}")

    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscribed_categories:
            del self.subscribed_categories[client_id]
        self.logger.info(f"WebSocket client disconnected: {client_id}")

    def subscribe_to_category(self, client_id: str, category: str):
        """Subscribe a client to a specific category of updates"""
        if client_id in self.subscribed_categories:
            self.subscribed_categories[client_id].add(category)

    def unsubscribe_from_category(self, client_id: str, category: str):
        """Unsubscribe a client from a specific category of updates"""
        if client_id in self.subscribed_categories:
            self.subscribed_categories[client_id].discard(category)

    async def broadcast_to_category(self, category: str, message: dict):
        """Broadcast a message to all clients subscribed to a category"""
        message['timestamp'] = datetime.utcnow().isoformat()
        message['category'] = category

        for client_id, websocket in list(self.active_connections.items()):
            if client_id in self.subscribed_categories:
                if category in self.subscribed_categories[client_id]:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        self.logger.error(f"Error sending message to {client_id}: {e}")
                        # Remove broken connection
                        self.disconnect(client_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        message['timestamp'] = datetime.utcnow().isoformat()

        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error sending message to {client_id}: {e}")
                # Remove broken connection
                self.disconnect(client_id)


# Global connection manager instance
manager = ConnectionManager()


class WebSocketNotificationService:
    """Service for sending real-time notifications via WebSocket"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.manager = manager

    async def notify_new_disaster(self, event: DisasterEvent):
        """Notify clients about a new disaster event"""
        message = {
            "type": "disaster_event",
            "action": "new",
            "data": {
                "event_id": event.event_id,
                "disaster_type": event.disaster_type.value,
                "location": event.location,
                "coordinates": event.coordinates,
                "timestamp": event.timestamp.isoformat(),
                "alert_level": event.alert_level.value,
                "magnitude": event.magnitude,
                "description": event.description
            }
        }

        await self.manager.broadcast_to_category("disasters", message)
        self.logger.info(f"Notified clients about new disaster: {event.event_id}")

    async def notify_disaster_update(self, event: DisasterEvent):
        """Notify clients about a disaster event update"""
        message = {
            "type": "disaster_event",
            "action": "update",
            "data": {
                "event_id": event.event_id,
                "disaster_type": event.disaster_type.value,
                "location": event.location,
                "coordinates": event.coordinates,
                "timestamp": event.timestamp.isoformat(),
                "alert_level": event.alert_level.value,
                "status": event.status,
                "magnitude": event.magnitude,
                "description": event.description
            }
        }

        await self.manager.broadcast_to_category("disasters", message)
        self.logger.info(f"Notified clients about disaster update: {event.event_id}")

    async def notify_new_alert(self, alert: AlertMessage):
        """Notify clients about a new alert"""
        message = {
            "type": "alert",
            "action": "new",
            "data": {
                "alert_id": alert.alert_id,
                "event_id": alert.event_id,
                "disaster_type": alert.disaster_type.value,
                "location": alert.location,
                "alert_level": alert.alert_level.value,
                "priority": alert.priority,
                "message": alert.message[:200] + "..." if len(alert.message) > 200 else alert.message,  # Truncate long messages
                "timestamp": alert.timestamp.isoformat()
            }
        }

        await self.manager.broadcast_to_category("alerts", message)
        self.logger.info(f"Notified clients about new alert: {alert.alert_id}")

    async def notify_system_stats(self, stats: dict):
        """Notify clients about system statistics"""
        message = {
            "type": "system_stats",
            "action": "update",
            "data": stats
        }

        await self.manager.broadcast_to_category("system", message)
        self.logger.info("Notified clients about system stats update")


# Singleton instance
_websocket_service: WebSocketNotificationService = None


def get_websocket_service() -> WebSocketNotificationService:
    """Get or create WebSocket notification service instance"""
    global _websocket_service
    if _websocket_service is None:
        _websocket_service = WebSocketNotificationService()
    return _websocket_service


# Background task for periodic updates
async def run_periodic_updates():
    """Run periodic updates to send stats and other information"""
    websocket_service = get_websocket_service()
    disaster_service = get_disaster_service()

    while True:
        try:
            # Get and broadcast system stats every 30 seconds
            stats = await disaster_service.get_summary_statistics()
            await websocket_service.notify_system_stats(stats)

            await asyncio.sleep(30)  # Wait 30 seconds
        except Exception as e:
            logging.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(30)  # Continue even if there's an error