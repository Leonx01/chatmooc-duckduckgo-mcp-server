# ChatMooc DuckDuckGo Search MCP Server

[![Python versions](https://img.shields.io/pypi/pyversions/duckduckgo-mcp-server)](https://pypi.org/project/duckduckgo-mcp-server/)

## 项目简介

这是一个基于 **Model Context Protocol (MCP)** 的 DuckDuckGo 搜索服务，提供 **网页搜索** 与 **网页内容抓取** 两个工具，并内置速率限制与安全过滤配置。项目使用 FastMCP 框架构建，适用于 Claude Desktop、Claude Code 或其他 MCP 客户端。

本仓库基于 [nickclyde/duckduckgo-mcp-server](https://github.com/nickclyde/duckduckgo-mcp-server) 派生，增加了 LangGraph Client 适配以及 HTTP 传输支持的示例与说明。

## Docker 部署（推荐）

```bash
docker compose up --build -d

# 或使用原生 Docker
docker build -t duckduckgo-mcp-server .
docker run -d -p 8000:8000 \
  -e DDG_SAFE_SEARCH=MODERATE \
  -e DDG_REGION= \
  duckduckgo-mcp-server
```

HTTP 端点：`http://localhost:8000/mcp`

## 功能特性

- DuckDuckGo 网页搜索（解析 HTML 结果）
- 网页正文抓取（移除脚本/样式/导航等非正文元素）
- 速率限制：搜索 30 次/分钟，抓取 20 次/分钟
- SafeSearch 与地区/语言配置
- 适配 LangGraph 客户端（支持 stdio 与 HTTP 连接）

## 架构概览

核心实现位于 `src/duckduckgo_mcp_server/server.py`：

- `DuckDuckGoSearcher`：向 `https://html.duckduckgo.com/html` 发送 POST 请求并解析结果
- `WebContentFetcher`：抓取网页并提取纯文本内容（默认最大 8000 字符）
- `RateLimiter`：滑动窗口限流

对外暴露两个 MCP 工具：`search` 与 `fetch_content`。

## 快速开始

```bash
uvx duckduckgo-mcp-server
```

## 安装

```bash
uv pip install duckduckgo-mcp-server
```

## 使用方式

### Claude Desktop

配置文件路径：

- macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows：`%APPDATA%\Claude\claude_desktop_config.json`

基础配置：

```json
{
    "mcpServers": {
        "ddg-search": {
            "command": "uvx",
            "args": ["duckduckgo-mcp-server"]
        }
    }
}
```

带 SafeSearch 和地区配置：

```json
{
    "mcpServers": {
        "ddg-search": {
            "command": "uvx",
            "args": ["duckduckgo-mcp-server"],
            "env": {
                "DDG_SAFE_SEARCH": "STRICT",
                "DDG_REGION": "cn-zh"
            }
        }
    }
}
```

修改配置后请重启 Claude Desktop。

### Claude Code

```bash
claude mcp add ddg-search uvx duckduckgo-mcp-server
```

## 传输方式（Transport）

默认使用 `stdio`。如需 HTTP 传输，可选择 SSE 或 Streamable HTTP。

```bash
# SSE
uvx duckduckgo-mcp-server --transport sse

# Streamable HTTP（适合 Docker/远程）
uvx duckduckgo-mcp-server --transport streamable-http --host 0.0.0.0 --port 8000
```

HTTP 端点为：`http://localhost:8000/mcp`。

## LangGraph Client 适配

通过 `langchain-mcp-adapters` 的 `MultiServerMCPClient` 即可接入 LangGraph。

注意命名差异：

- 服务端 CLI 传输参数：`--transport streamable-http`
- 客户端 transport 键：`streamable_http`

### stdio 示例

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    connections={
        "duckduckgo": {
            "command": "uvx",
            "args": ["duckduckgo-mcp-server"],
            "transport": "stdio",
        }
    }
)
```

### HTTP 示例

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    connections={
        "duckduckgo": {
            "transport": "streamable_http",
            "url": "http://localhost:8000/mcp",
        }
    }
)
```

可参考示例文件：

- `tests/example_langgraph_direct.py`
- `tests/example_langgraph_http.py`
- `tests/test_langgraph_integration.py`

## MCP 工具说明

### 1) search

```python
async def search(query: str, max_results: int = 10, region: str = "") -> str
```

参数说明：

- `query`：搜索关键词
- `max_results`：最多返回结果数（默认 10，建议 1-20）
- `region`：地区/语言代码（可覆盖默认值）

返回值为格式化文本，包含标题、链接与摘要。

### 2) fetch_content

```python
async def fetch_content(url: str, start_index: int = 0, max_length: int = 8000) -> str
```

参数说明：

- `url`：网页 URL（需以 http/https 开头）
- `start_index`：内容起始字符位置（分页使用）
- `max_length`：最大返回字符数（默认 8000）

返回值为清洗后的正文文本，并附带分页元信息。

## 配置项（启动时读取）

- `DDG_SAFE_SEARCH`：`STRICT` / `MODERATE`（默认）/ `OFF`
- `DDG_REGION`：默认地区/语言代码，例如 `us-en`、`cn-zh`、`jp-ja`、`wt-wt`

## 开发与测试

```bash
# 安装依赖
uv sync

# 本地运行
uv run duckduckgo-mcp-server

# MCP Inspector
mcp dev src/duckduckgo_mcp_server/server.py

# 全部测试
uv run python -m pytest src/duckduckgo_mcp_server/ -v

# 单元测试
uv run python -m pytest src/duckduckgo_mcp_server/test_server.py -v

# E2E 测试
uv run python -m pytest src/duckduckgo_mcp_server/test_e2e.py -v

# LangGraph 集成测试（需要 OPENAI_API_KEY）
python tests/test_langgraph_integration.py
```

## 常见问题

- LangGraph 代理测试需要设置 `OPENAI_API_KEY`，否则只会运行工具加载测试。
- 如果使用 HTTP 传输，请确保服务端以 `streamable-http` 启动，并访问 `/mcp` 端点。

## 致谢

- [nickclyde/duckduckgo-mcp-server](https://github.com/nickclyde/duckduckgo-mcp-server) 原始项目
- DuckDuckGo 搜索服务
- MCP 与 FastMCP 框架
- `httpx`、`beautifulsoup4` 等关键依赖
- LangGraph 与 `langchain-mcp-adapters`
