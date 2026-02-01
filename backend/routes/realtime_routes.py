"""
DisasterAI Backend - Real-time Routes
WebSocket endpoints for real-time disaster monitoring
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging

from services.websocket_service import manager, get_websocket_service
from logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    categories: str = Query("disasters", description="Comma-separated list of categories to subscribe to")
):
    """
    WebSocket endpoint for real-time updates
    Categories: disasters, alerts, system
    """
    await manager.connect(websocket, client_id)

    try:
        # Parse and subscribe to requested categories
        category_list = [cat.strip() for cat in categories.split(',')]
        for category in category_list:
            if category in ['disasters', 'alerts', 'system']:
                manager.subscribe_to_category(client_id, category)

        logger.info(f"Client {client_id} connected and subscribed to: {category_list}")

        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "categories": category_list
        }))

        while True:
            # Listen for messages from client
            data = await websocket.receive_text()

            # Parse the message
            try:
                message = json.loads(data)

                if message.get('type') == 'subscribe':
                    category = message.get('category')
                    if category in ['disasters', 'alerts', 'system']:
                        manager.subscribe_to_category(client_id, category)
                        await websocket.send_text(json.dumps({
                            "type": "subscription",
                            "status": "subscribed",
                            "category": category
                        }))

                elif message.get('type') == 'unsubscribe':
                    category = message.get('category')
                    manager.unsubscribe_from_category(client_id, category)
                    await websocket.send_text(json.dumps({
                        "type": "subscription",
                        "status": "unsubscribed",
                        "category": category
                    }))

                elif message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from {client_id}: {data}")
            except Exception as e:
                logger.error(f"Error processing message from {client_id}: {e}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Unexpected error with client {client_id}: {e}")
        manager.disconnect(client_id)