#!/bin/bash
# Substance Designer MCP Auto-Install Script
# Cross-platform auto-install that:
#   1. Checks file locations relative to project root
#   2. Copies plugin files to SD user directory if needed
#   3. Installs dependencies (uv, mcp[cli])

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$PROJECT_ROOT/plugin"
SERVER_DIR="$PROJECT_ROOT/server"
SD_PLUGIN_DEST="${HOME}/Documents/Adobe/Adobe Substance 3D Designer/python/sduserplugins/sd_mcp_plugin"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Substance Designer MCP Auto-Install"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# === STEP 1: Install UV (if not present) ===
echo -e "\n[1/4] Installing uv package manager..."
if ! command -v uv &> /dev/null; then
    echo "    Installing uv from pip..."
    pip install uv || pip3 install uv
else
    echo "    uv already installed"
fi

# === STEP 2: Setup Bridge Server (uv sync) ===
echo -e "\n[2/4] Setting up bridge server..."
cd "$SERVER_DIR"

if [ ! -d ".venv" ]; then
    echo "    Creating virtual environment with uv..."
    uv venv --python 3.12 || uv venv --python python3
fi

if [ ! -d ".venv/lib/python*/site-packages/mcp" ]; then
    echo "    Installing mcp[cli] into .venv..."
    uv sync --python 3.12 || uv sync --python python3
else
    echo "    mcp[cli] already installed"
fi

echo "    Bridge server ready at: $SERVER_DIR"

# === STEP 3: Deploy SD Plugin ===
echo -e "\n[3/4] Deploying SD plugin to Substance Designer..."

# Create destination directory if it doesn't exist
DEST_DIR=$(dirname "$SD_PLUGIN_DEST")
if [ ! -d "$DEST_DIR" ]; then
    echo "    Creating plugin destination directory..."
    mkdir -p "$DEST_DIR"
fi

PLUGIN_ALREADY_INSTALLED=false
if [ -d "$SD_PLUGIN_DEST" ]; then
    # Plugin exists, check if it's the same content using file timestamps
    EXISTING_INIT=""
    NEW_INIT_MTIME=""
    
    if [ -f "$SD_PLUGIN_DEST/__init__.py" ]; then
        EXISTING_INIT=$SD_PLUGIN_DEST/__init__.py
        NEW_INIT_MTIME=$(stat -c %y "$PLUGIN_DIR/__init__.py" | cut -d'.' -f1)
    fi
    
    # Get existing file mtime if it exists
    if [ -n "$EXISTING_INIT" ]; then
        EXISTING_MTIME=$(stat -c %Y "$EXISTING_INIT" 2>/dev/null || echo "0")
        CURRENT_INIT_MTIME=$(stat -c %Y "$PLUGIN_DIR/__init__.py" 2>/dev/null || echo "0")
        NEW_RECIPES_MTIME=$(stat -c %Y "$PLUGIN_DIR/recipes.py" 2>/dev/null || echo "0")
        
        # Check if files are newer than installed version
        if [ "$EXISTING_MTIME" != "$CURRENT_INIT_MTIME" ] || [ "$(stat -c %Y $PLUGIN_DIR/recipes.py 2>/dev/null || echo 0)" != "$(stat -c %Y $SD_PLUGIN_DEST/recipes.py 2>/dev/null || echo 0)" ]; then
            echo "    Updating plugin (content changed)..."
            cp "$PLUGIN_DIR/__init__.py" "$SD_PLUGIN_DEST/" -f
            cp "$PLUGIN_DIR/recipes.py" "$SD_PLUGIN_DEST/" -f
            # Copy other files if they exist
            for file in "$PLUGIN_DIR"/*; do
                filename=$(basename "$file")
                if [ "$filename" != "__init__.py" ] && [ "$filename" != "recipes.py" ]; then
                    cp "$file" "$SD_PLUGIN_DEST/" -f
                fi
            done
        else
            echo "    Plugin already installed and up-to-date!"
        fi
    else
        echo "    Installing plugin files..."
        cp "$PLUGIN_DIR/"* "$SD_PLUGIN_DEST/" -f
        PLUGIN_ALREADY_INSTALLED=true
    fi
else
    echo "    Creating plugin directory and installing files..."
    mkdir -p "$SD_PLUGIN_DEST"
    cp "$PLUGIN_DIR/"* "$SD_PLUGIN_DEST/" -f
    PLUGIN_ALREADY_INSTALLED=true
fi

if [ -d "$SD_PLUGIN_DEST" ]; then
    echo "    Plugin deployed to: $SD_PLUGIN_DEST"
    echo "    Contents:"
    ls -1 "$SD_PLUGIN_DEST" 2>/dev/null | while read file; do
        echo "      - $file"
    done
fi

# === STEP 4: Print Configuration Instructions ===
echo -e "\n[4/4] Configuration Complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " INSTALLATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo " SD Plugin Location:"
echo "$SD_PLUGIN_DEST"
echo ""
echo " Bridge Server Location:"
echo "$SERVER_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  CRITICAL: START SUBSTANCE DESIGNER FIRST!"
echo ""
echo "    SD must be running before your AI client starts."
echo "      (The plugin binds TCP:9881 on SD startup)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " HOW TO START THE BRIDGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option A - Using uv (recommended):"
echo -e "  cd $SERVER_DIR"
echo -e "  .venv/bin/activate"
echo -e "  uv run python sd_mcp_bridge.py --port 9881"
echo ""
echo "Option B - Direct Python:"
echo -e "  cd $SERVER_DIR"
echo -e "  .venv/bin/python sd_mcp_bridge.py --port 9881"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " CLAUDE CODE CONFIGURATION EXAMPLE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Add to ~/.claude/settings.json:"
echo '  {"mcpServers": {"substance_designer": {'
echo '    "command": "uv",'
echo '    "args": ['
echo '      "run",'
echo '      "--directory",'
echo '      "'$SERVER_DIR'",'
echo '      "python",'
echo '      "sd_mcp_bridge.py",'
echo '      "--port",'
echo '      "9881"'
echo '    ]'
echo '  }}'
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " TROUBLESHOOTING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Bridge can't connect to SD:"
echo -e "  → Start Substance Designer first!"
echo -e "  → Check logs: ~/.config/Adobe/Adobe Substance 3D Designer/log.txt"
echo ""
echo "Plugin not loading:"
echo -e "  → Delete .venv/__pycache__ if it exists and restart SD"
echo ""
echo "Wrong port (9881):"
echo -e "  → Use --port 9881 with bridge (or change in both places)"
echo ""

echo -e "\n Installation complete! Remember to start SD before your AI client."
