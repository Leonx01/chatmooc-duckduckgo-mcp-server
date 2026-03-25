"""
Simple example showing how to use DuckDuckGo MCP tools in LangGraph without an LLM.

This demonstrates direct tool invocation.
"""

import asyncio
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient


async def main():
    """Run DuckDuckGo search using MCP tools loaded via LangGraph."""

    # Get the current Python executable and project root
    python_exe = sys.executable
    project_root = Path(__file__).parent.parent

    # Create MCP client connected to DuckDuckGo MCP server
    client = MultiServerMCPClient(
        connections={
            "duckduckgo": {
                "command": python_exe,
                "args": ["-m", "duckduckgo_mcp_server.server"],
                "transport": "stdio",
                "cwd": str(project_root),
            }
        }
    )

    # Get MCP tools
    tools = await client.get_tools()
    print(f"\nLoaded {len(tools)} MCP tools from DuckDuckGo server")

    # Find the search tool
    search_tool = next((t for t in tools if t.name == "search"), None)
    fetch_tool = next((t for t in tools if t.name == "fetch_content"), None)

    if not search_tool:
        print("Error: search tool not found")
        return

    # Test 1: Perform a search
    print("\n" + "=" * 60)
    print("Test 1: Search for 'Python asyncio tutorial'")
    print("=" * 60)

    result = await search_tool.ainvoke({
        "query": "Python asyncio tutorial",
        "max_results": 5
    })
    print(result)

    # Test 2: Fetch content from a URL (if fetch tool available)
    if fetch_tool:
        print("\n" + "=" * 60)
        print("Test 2: Fetch content from example.com")
        print("=" * 60)

        result = await fetch_tool.ainvoke({
            "url": "https://example.com",
            "max_length": 1000
        })
        print(result[:500] + "..." if len(result) > 500 else result)

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
