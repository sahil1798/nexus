from mcp.server.fastmcp import FastMCP

mcp = FastMCP("test-server")

@mcp.tool()
def hello(name: str) -> str:
    """Says hello to someone. A simple test tool."""
    return f"Hello, {name}! MCP is working."

if __name__ == "__main__":
    mcp.run(transport="stdio")
