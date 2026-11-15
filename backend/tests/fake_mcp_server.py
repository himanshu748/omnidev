"""A tiny stdio MCP server used by the MCP marketplace tests."""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("fake")


@mcp.tool()
def echo(text: str) -> str:
    """Echo the input back."""
    return f"echo: {text}"


@mcp.tool()
def fail() -> str:
    """Return a tool error for the marketplace's refusal-path test."""
    raise ToolError("fixture tool failed")


if __name__ == "__main__":
    mcp.run()
