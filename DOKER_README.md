# Docker Setup - Substance Designer MCP Bridge (Dev Hot-Reload)

## One-Line Start

```bash
docker compose up -d
```

That's it. Simple as that.

---

## What This Does

-   **Builds fresh** container with Python 3.12 + uv (no pre-existing .venv needed!)
-   **Runs in DEV HOT-RELOAD mode** - code changes auto-reload
-   **Auto-starts on boot** via systemd service
-   **Connects to Substance Designer** on port 9881
-   Lightweight (~500MB containerized deployment)

---

## Quick Start Commands

### Start the server:
```bash
docker compose up -d
```

### Check it's running:
```bash
docker compose ps
```

### View logs:
```bash
docker compose logs
```

### Restart after code changes:
```bash
docker compose restart
```

### Stop the server:
```bash
docker compose down
```

---

## Configuration (Optional)

Create `.env` file in project root to customize:

```bash
# .env file example
MCP_PORT=9881
MCP_HOT_RELOAD=true
SD_PLUGIN_DIR=%USERPROFILE%\Documents\Adobe\Adobe Substance 3D Designer\python\suserplugins
```

---

## Critical Reminder

**START SUBSTANCE DESIGNER FIRST!**

The SD plugin binds to TCP port 9881 when Substance Designer starts. If you start the AI client before SD, the bridge won't be able to connect.

**Correct workflow:**
1. Start Substance Designer 15.x
2. Wait for it to fully load (~30-60 seconds)
3. Run: `docker compose up -d`
4. Start your AI client (Claude/Cursor/CodePuppy)

---

## Auto-Start on Boot (Windows)

Enable systemd service:
```bash
docker compose enable
```

The container will restart automatically when your computer boots.

---

## Troubleshooting

### Container won't connect to SD plugin

```powershell
# Check if Substance Designer is running
# Make sure it started first with MCP plugin loaded
docker logs substance-designer-mcp-bridge
```

### View full error logs:
```bash
docker logs substance-designer-mcp-bridge --tail=100
```

### Rebuild after code changes:
```bash
docker compose down
docker compose build
docker compose up -d
```

---

## Common Issues

**Problem**: Bridge won't connect to SD  
**Solution**: Make sure Substance Designer is running first, then start the bridge.

**Problem**: Plugin not loading in SD  
**Solution**: Delete the entire `sd_mcp_plugin/` folder and restart SD. Or delete `__pycache__/` in the plugin directory.

---

See `README.md` for full documentation.
