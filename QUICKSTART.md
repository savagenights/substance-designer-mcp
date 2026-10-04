# MCP Bridge Server - Docker Dev Hot-Reload Edition

## Super Quick Start (The ONLY way you need!)

### Windows PowerShell:
```powershell
docker compose up -d
```

### Linux/macOS Bash:
```bash
docker compose up -d
```

That's it. Just run that ONE command and the server starts.

---

## What This Does Automatically

-  Builds fresh container with Python 3.12 + uv (no pre-existing .venv needed!)
-  Runs in **DEV HOT-RELOAD mode** - code changes auto-reload
-  Auto-starts on boot via systemd service
-  Works alongside Substance Designer on port 9881
-  Lightweight (~500MB) containerized deployment

See `README_DOCKER.md` for complete documentation.

---

## Daily Commands

| Command | Purpose |
|---------|---------|
| `docker compose up -d` | Start server |
| `docker compose ps` | Check status |
| `docker compose logs` | View logs |
| `docker compose restart` | Restart after code changes |
| `docker compose down` | Stop server |

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

## Auto-Start on Boot

Enable systemd service:
```powershell
docker compose enable
```

The container will restart automatically when your computer boots.

---

**Need help?** Check `README_DOCKER.md` for full documentation.
