"""
Entrypoint for the standalone MCP server.

    python -m app.mcp              stdio (for clients that spawn a process)
    python -m app.mcp --http       stateless streamable HTTP on 127.0.0.1:8765

Most users need neither: the running OmniDev engine already serves the same
tools at /mcp, so the app being open is the whole installation. This exists
for clients that insist on owning the process, and for running the MCP
surface without the rest of the engine.
"""

import os
import sys

from app.mcp.server import mcp

if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.settings.host = os.environ.get("OMNIDEV_MCP_HOST", "127.0.0.1")
        mcp.settings.port = int(os.environ.get("OMNIDEV_MCP_PORT", "8765"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
