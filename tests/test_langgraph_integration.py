"""
Test DuckDuckGo MCP Server integration with LangGraph.

This test demonstrates how to use the DuckDuckGo MCP server tools
(search, fetch_content) within a LangGraph agent workflow.

Requirements:
    pip install langchain-mcp-adapters langgraph langchain-openai
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.client import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI


async def test_langgraph_mcp_integration():
    """Test DuckDuckGo MCP server with LangGraph agent."""

    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Skipping agent execution.")
        print("Set the environment variable to run the full test.")
        return

    # Create MCP client
    # Get the current Python executable and project root
    python_exe = sys.executable
    project_root = Path(__file__).parent.parent
    server_script = project_root / "src" / "duckduckgo_mcp_server" / "server.py"

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

    # Get MCP tools using the new API
    tools = await client.get_tools()
    print(f"\nLoaded {len(tools)} MCP tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # Create LangGraph ReAct agent
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(model, tools)

    # Test 1: Search query
    print("\n" + "=" * 60)
    print("Test 1: Search Query")
    print("=" * 60)

    query1 = "What is the latest news about AI agents?"
    print(f"Query: {query1}")

    result1 = await agent.ainvoke({
        "messages": [{"role": "user", "content": query1}]
    })

    print("\nAgent Response:")
    for msg in result1["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"{msg.__class__.__name__}: {msg.content[:500]}...")

    # Test 2: Search + Fetch content
    print("\n" + "=" * 60)
    print("Test 2: Search and Fetch Content")
    print("=" * 60)

    query2 = "Search for Python asyncio tutorial and summarize the first result"
    print(f"Query: {query2}")

    result2 = await agent.ainvoke({
        "messages": [{"role": "user", "content": query2}]
    })

    print("\nAgent Response:")
    for msg in result2["messages"]:
        if hasattr(msg, "content") and msg.content:
            print(f"{msg.__class__.__name__}: {msg.content[:500]}...")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


async def test_mcp_tools_only():
    """Test loading MCP tools without an LLM agent."""

    # Get the current Python executable and project root
    python_exe = sys.executable
    project_root = Path(__file__).parent.parent
    server_script = project_root / "src" / "duckduckgo_mcp_server" / "server.py"

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

    # Get tools using the new API
    tools = await client.get_tools()
    print(f"\nLoaded {len(tools)} MCP tools from DuckDuckGo server:")
    print("-" * 40)

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        if hasattr(tool, "args_schema") and tool.args_schema:
            if hasattr(tool.args_schema, "model_json_schema"):
                schema = tool.args_schema.model_json_schema()
            else:
                schema = tool.args_schema
            print(f"Args Schema: {schema}")

    return tools


async def test_with_session():
    """Test using session-based approach."""

    # Get the current Python executable and project root
    python_exe = sys.executable
    project_root = Path(__file__).parent.parent
    server_script = project_root / "src" / "duckduckgo_mcp_server" / "server.py"

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

    async with client.session("duckduckgo") as session:
        tools = await load_mcp_tools(session)
        print(f"\nLoaded {len(tools)} MCP tools via session:")
        for tool in tools:
            print(f"  - {tool.name}")
        return tools


if __name__ == "__main__":
    print("Testing DuckDuckGo MCP Server with LangGraph")
    print("=" * 60)

    # First test: just load tools using get_tools()
    print("\n[1] Testing MCP tool loading (get_tools API)...")
    try:
        tools = asyncio.run(test_mcp_tools_only())
        print(f"\n[OK] Successfully loaded {len(tools)} tools")
    except Exception as e:
        print(f"\n[FAIL] Failed to load tools: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Second test: load tools using session
    print("\n[2] Testing MCP tool loading (session API)...")
    try:
        tools = asyncio.run(test_with_session())
        print(f"\n[OK] Successfully loaded {len(tools)} tools via session")
    except Exception as e:
        print(f"\n[FAIL] Session test failed: {e}")
        import traceback
        traceback.print_exc()

    # Third test: run with agent (requires OpenAI API key)
    print("\n[3] Testing LangGraph agent integration...")
    if os.getenv("OPENAI_API_KEY"):
        try:
            asyncio.run(test_langgraph_mcp_integration())
            print("\n[OK] LangGraph integration test completed")
        except Exception as e:
            print(f"\n[FAIL] LangGraph test failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[SKIP] Skipping agent test (OPENAI_API_KEY not set)")
        print("  Set OPENAI_API_KEY environment variable to run full test")
