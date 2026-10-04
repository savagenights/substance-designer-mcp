# Substance Designer MCP Bridge - Simple Docker Setup
# No pre-existing .venv needed - builds fresh every time!

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install uv for fast, reproducible Python installs
RUN pip install --no-cache-dir uv

# Copy server files
COPY server/ ./server/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_PORT=9881
ENV MCP_HOT_RELOAD=true

# Expose MCP bridge port
EXPOSE 9881

# Health check to verify server is alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.path.insert(0, '/app/server'); from sd_mcp_bridge import mcp; print('OK')" || exit 1

# Use uv to install and run - auto-detects pyproject.toml in server/
CMD ["uv", "run", "--directory", "/app/server", "python", "sd_mcp_bridge.py", "--port", "9881"]
