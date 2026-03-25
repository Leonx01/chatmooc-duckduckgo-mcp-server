"""
Example: Using DuckDuckGo MCP Server with LangGraph via HTTP transport.

This demonstrates how to connect to the MCP server running in Docker
using the streamable-http transport.
"""

import asyncio
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI


# MCP server URL (Docker default)
MCP_SERVER_URL = "http://localhost:8000/mcp"


async def test_http_tools_only():
    """Test loading MCP tools via HTTP transport."""

    client = MultiServerMCPClient(
        connections={
            "duckduckgo": {
                "transport": "streamable_http",
                "url": MCP_SERVER_URL,
                # Optional: Add headers for authentication
                # "headers": {
                #     "Authorization": "Bearer YOUR_TOKEN"
                # }
            }
        }
    )

    # Get tools using the HTTP transport
    tools = await client.get_tools()
    print(f"\nLoaded {len(tools)} MCP tools via HTTP transport:")
    print("-" * 40)

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description[:80]}...")

    return tools


async def test_http_direct_tool_usage():
    """Test direct tool invocation via HTTP transport."""

    client = MultiServerMCPClient(
        connections={
            "duckduckgo": {
                "transport": "streamable_http",
                "url": MCP_SERVER_URL,
            }
        }
    )

    tools = await client.get_tools()
    search_tool = next((t for t in tools if t.name == "search"), None)

    if not search_tool:
        print("Error: search tool not found")
        return

    print("\n" + "=" * 60)
    print("Search via HTTP transport: 'Python asyncio tutorial'")
    print("=" * 60)

    result = await search_tool.ainvoke({
        "query": "Python asyncio tutorial",
        "max_results": 3
    })
    print(result)


async def test_http_with_agent():
    """Test LangGraph agent with HTTP transport."""

    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("Skipping agent test: OPENAI_API_KEY not set")
        return

    client = MultiServerMCPClient(
        connections={
            "duckduckgo": {
                "transport": "streamable_http",
                "url": MCP_SERVER_URL,
            }
        }
    )

    tools = await client.get_tools()

    # Create LangGraph ReAct agent
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(model, tools)

    print("\n" + "=" * 60)
    print("Agent query: 'What are the latest AI news?'")
    print("=" * 60)

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "What are the latest AI news? Search and summarize."}]
    })

    for msg in result["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"\n{msg.__class__.__name__}: {msg.content[:500]}...")


if __name__ == "__main__":
    print("Testing DuckDuckGo MCP Server with LangGraph (HTTP Transport)")
    print("=" * 60)
    print(f"Server URL: {MCP_SERVER_URL}")
    print()

    # Test 1: Load tools
    print("[1] Testing HTTP tool loading...")
    try:
        tools = asyncio.run(test_http_tools_only())
        print(f"\n[OK] Successfully loaded {len(tools)} tools via HTTP")
    except Exception as e:
        print(f"\n[FAIL] Failed: {e}")
        print("\nMake sure the MCP server is running:")
        print("  docker compose up --build -d")
        print("  or")
        print("  python -m duckduckgo_mcp_server.server --transport streamable-http --host 0.0.0.0")
        sys.exit(1)

    # Test 2: Direct tool usage
    print("\n[2] Testing direct tool invocation via HTTP...")
    try:
        asyncio.run(test_http_direct_tool_usage())
        print("\n[OK] Direct tool usage test completed")
    except Exception as e:
        print(f"\n[FAIL] Failed: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Agent (optional, requires OPENAI_API_KEY)
    print("\n[3] Testing LangGraph agent via HTTP...")
    try:
        asyncio.run(test_http_with_agent())
        print("\n[OK] Agent test completed")
    except Exception as e:
        print(f"\n[SKIP] {e}")
