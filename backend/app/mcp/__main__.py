"""Entrypoint: `python -m app.mcp` (run from backend/, stdio transport)."""

from app.mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
