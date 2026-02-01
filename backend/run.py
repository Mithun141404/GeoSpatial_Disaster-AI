"""
DisasterAI Backend - Run Script
Quick start script for development
"""

import uvicorn
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Run the development server"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🛰️  DisasterAI Geospatial Intelligence Backend  🛰️        ║
║                                                               ║
║     Starting development server...                            ║
║     API Docs: http://localhost:8000/docs                      ║
║     ReDoc:    http://localhost:8000/redoc                     ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
