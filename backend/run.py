"""
DisasterAI Backend - Run Script
Quick start script for development
"""

import uvicorn
import sys
import os
import asyncio
from threading import Thread

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.websocket_service import run_periodic_updates


def run_background_task():
    """Run the periodic updates in a background thread"""
    asyncio.run(run_periodic_updates())


def main():
    """Run the development server"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🛰️  DisasterAI Geospatial Intelligence Backend  🛰️        ║
║                                                               ║
║     Starting development server...                            ║
║     API Docs: http://localhost:8000/docs                      ║
║     ReDoc:    http://localhost:8000/redoc                     ║
║     WebSocket: ws://localhost:8000/api/ws                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    # Start the background task for periodic updates
    bg_thread = Thread(target=run_background_task, daemon=True)
    bg_thread.start()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
