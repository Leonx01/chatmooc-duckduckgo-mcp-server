# DuckDuckGo MCP Server Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# Expose port for HTTP transport
EXPOSE 8000

# Environment variables with defaults
ENV DDG_SAFE_SEARCH=MODERATE
ENV DDG_REGION=

# Run the MCP server with streamable-http transport
CMD ["python", "-m", "duckduckgo_mcp_server.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
