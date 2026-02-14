"""
NEXUS — The Intelligent MCP Broker
===================================
Entry point for the NEXUS backend API server.
Run: uv run python main.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "nexus_core.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
