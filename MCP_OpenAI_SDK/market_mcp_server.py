"""
Market Data MCP Server
======================
This module defines a custom MCP Server that exposes a tool to fetch
real-time or end-of-day share prices via Polygon.io integration.

It interacts with the core logic in `market_analyser.py` and makes the data
available to AI Agents through the Modular Component Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP
from market_analyser import get_share_price

# -------------------------------------------------------------
# Initialize MCP Server
# -------------------------------------------------------------
# Create a FastMCP server instance. The name identifies this
# server to clients (e.g., "market_mcp_server").

market_mcp_server = FastMCP(name="market_mcp_server")

# -------------------------------------------------------------
# Define MCP Tool
# -------------------------------------------------------------

@market_mcp_server.tool()
async def lookup_share_price(symbol: str) -> float:
    """
    MCP Tool to look up the share price for a given symbol.
    This function can be called by AI agents via the MCP protocol.

    Args:
        symbol (str): The stock ticker symbol to look up.
    """
    return get_share_price(symbol)

if __name__ == "__main__":
    print("Starting Market Data MCP Server...")
    print("Listening for requests on stdio transport.")
    market_mcp_server.run(transport='stdio')




