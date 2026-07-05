"""
Cwd-independent launcher for the OmniDev MCP server.

MCP clients spawn stdio servers from arbitrary working directories, where
`python -m app.mcp` cannot import the `app` package. This shim pins backend/
onto sys.path first, so registration works from anywhere:

    claude mcp add omnidev -- /path/to/omnidev/backend/.venv/bin/python \
        /path/to/omnidev/backend/mcp_server.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.mcp.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run()
