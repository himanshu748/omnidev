"""A tiny stdio MCP server used by the MCP marketplace tests."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("fake")


@mcp.tool()
def echo(text: str) -> str:
    """Echo the input back."""
    return f"echo: {text}"


if __name__ == "__main__":
    mcp.run()
