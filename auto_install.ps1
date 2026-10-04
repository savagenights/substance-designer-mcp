#!/usr/bin/env pwsh
# Substance Designer MCP Auto-Install (ASCII-only)
# 1) Ensures uv + bridge deps
# 2) Deploys SD plugin (OneDrive-aware)
# 3) Wires Code Puppy MCP configs + agent binding
#
# Run:
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\auto_install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host " Substance Designer MCP Auto-Install " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$projectRoot  = $PSScriptRoot
$pluginDir    = Join-Path $projectRoot "plugin"
$serverDir    = Join-Path $projectRoot "server"
$codePuppyDir = Join-Path $env:USERPROFILE ".code_puppy"

# Resolve SD plugin destination (OneDrive first, then Documents)
$candidateParents = @(
    (Join-Path $env:USERPROFILE "OneDrive\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins"),
    (Join-Path $env:USERPROFILE "Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins")
)

$sdPluginParent = $null
foreach ($base in $candidateParents) {
    if (Test-Path $base) {
        $sdPluginParent = $base
        break
    }
}
if (-not $sdPluginParent) {
    if (Test-Path (Join-Path $env:USERPROFILE "OneDrive\Documents")) {
        $sdPluginParent = Join-Path $env:USERPROFILE "OneDrive\Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins"
    } else {
        $sdPluginParent = Join-Path $env:USERPROFILE "Documents\Adobe\Adobe Substance 3D Designer\python\sduserplugins"
    }
}
$sdPluginDest = Join-Path $sdPluginParent "sd_mcp_plugin"

# Resolve uv.exe
$uvCandidates = @(
    (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\Scripts\uv.exe"),
    "uv.exe",
    "uv"
)
$uvExe = $null
foreach ($c in $uvCandidates) {
    if (($c -eq "uv") -or ($c -eq "uv.exe")) {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd) {
            $uvExe = $cmd.Source
            break
        }
    } elseif (Test-Path $c) {
        $uvExe = (Resolve-Path $c).Path
        break
    }
}

# === STEP 1: uv ===
Write-Host ""
Write-Host "[1/4] Checking uv package manager..." -ForegroundColor Yellow
if (-not $uvExe) {
    Write-Host "    uv not found - trying winget, then pip..." -ForegroundColor Gray
    try { winget install astral-sh.uv --silent 2>&1 | Out-Null } catch {}
    $cmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($cmd) {
        $uvExe = $cmd.Source
    } else {
        try {
            pip install uv
            $cmd = Get-Command uv -ErrorAction SilentlyContinue
            if ($cmd) { $uvExe = $cmd.Source }
        } catch {}
    }
}
if ($uvExe) {
    Write-Host "    uv: $uvExe" -ForegroundColor Green
} else {
    Write-Host "    WARNING: uv not found. Install from https://github.com/astral-sh/uv" -ForegroundColor Yellow
}

# === STEP 2: Bridge server ===
Write-Host ""
Write-Host "[2/4] Setting up bridge server..." -ForegroundColor Yellow
if (-not (Test-Path $serverDir)) {
    throw "Server directory missing: $serverDir"
}
Push-Location $serverDir
try {
    if (-not (Test-Path ".venv")) {
        Write-Host "    Creating .venv with uv..." -ForegroundColor Gray
        if ($uvExe) {
            & $uvExe venv --python 3.12
        } else {
            python -m venv .venv
        }
    } else {
        Write-Host "    Virtual environment exists" -ForegroundColor Green
    }
    if ($uvExe) {
        Write-Host "    uv sync..." -ForegroundColor Gray
        & $uvExe sync --python 3.12
    } else {
        Write-Host "    pip install mcp[cli]..." -ForegroundColor Gray
        & ".\.venv\Scripts\python.exe" -m pip install "mcp[cli]>=1.4.1"
    }
    Write-Host "    Bridge ready: $serverDir" -ForegroundColor Green
} finally {
    Pop-Location
}

# === STEP 3: Deploy SD plugin ===
Write-Host ""
Write-Host "[3/4] Deploying SD plugin..." -ForegroundColor Yellow
if (-not (Test-Path $pluginDir)) {
    throw "Plugin directory missing: $pluginDir"
}
Write-Host "    Destination: $sdPluginDest" -ForegroundColor Gray
New-Item -ItemType Directory -Force -Path $sdPluginDest | Out-Null
Get-ChildItem -Path $pluginDir -File | ForEach-Object {
    Copy-Item $_.FullName (Join-Path $sdPluginDest $_.Name) -Force
    Write-Host "    + $($_.Name)" -ForegroundColor Gray
}
$deployed = @(Get-ChildItem -Path $sdPluginDest -File | Select-Object -ExpandProperty Name)
Write-Host "    Deployed: $($deployed -join ', ')" -ForegroundColor Green

# === STEP 4: Code Puppy MCP wiring ===
Write-Host ""
Write-Host "[4/4] Wiring Code Puppy MCP..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $codePuppyDir | Out-Null

if (-not $uvExe) { $uvExe = "uv" }

# Build server entry as a nested hashtable (ConvertTo-Json friendly)
$serverEntry = @{
    type    = "stdio"
    command = $uvExe
    args    = @(
        "run",
        "--directory",
        $serverDir,
        "python",
        "sd_mcp_bridge.py",
        "--port",
        "9881"
    )
    cwd     = $serverDir
    timeout = 120
    enabled = $true
}

# --- mcp_servers.json (source of truth) ---
$mcpServersPath = Join-Path $codePuppyDir "mcp_servers.json"
$serversMap = @{}
if (Test-Path $mcpServersPath) {
    try {
        $existing = Get-Content $mcpServersPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($existing.mcp_servers) {
            $existing.mcp_servers.PSObject.Properties | ForEach-Object {
                # Keep other servers as hashtables when possible
                $serversMap[$_.Name] = $_.Value
            }
        }
    } catch {
        Write-Host "    WARNING: could not parse existing mcp_servers.json; rewriting" -ForegroundColor Yellow
    }
}
$serversMap["substance_designer"] = $serverEntry
$mcpServersObj = @{ mcp_servers = $serversMap }
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($mcpServersPath, ($mcpServersObj | ConvertTo-Json -Depth 12), $utf8NoBom)
Write-Host "    Wrote $mcpServersPath" -ForegroundColor Green

# --- mcp_registry.json ---
$mcpRegistryPath = Join-Path $codePuppyDir "mcp_registry.json"
$registryMap = @{}
if (Test-Path $mcpRegistryPath) {
    try {
        $existingReg = Get-Content $mcpRegistryPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $existingReg.PSObject.Properties | ForEach-Object {
            $registryMap[$_.Name] = $_.Value
        }
    } catch {
        Write-Host "    WARNING: could not parse existing mcp_registry.json; rewriting entry only" -ForegroundColor Yellow
    }
}
$registryMap["substance_designer"] = @{
    id      = "substance_designer"
    name    = "substance_designer"
    type    = "stdio"
    enabled = $true
    config  = $serverEntry
}
[System.IO.File]::WriteAllText($mcpRegistryPath, ($registryMap | ConvertTo-Json -Depth 12), $utf8NoBom)
Write-Host "    Wrote $mcpRegistryPath" -ForegroundColor Green

# --- mcp_agent_bindings.json ---
$bindingsPath = Join-Path $codePuppyDir "mcp_agent_bindings.json"
$bindingsRoot = @{ bindings = @{} }
if (Test-Path $bindingsPath) {
    try {
        $existingB = Get-Content $bindingsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($existingB.bindings) {
            $bindingsRoot.bindings = @{}
            $existingB.bindings.PSObject.Properties | ForEach-Object {
                $agentName = $_.Name
                $agentMap = @{}
                $_.Value.PSObject.Properties | ForEach-Object {
                    $agentMap[$_.Name] = $_.Value
                }
                $bindingsRoot.bindings[$agentName] = $agentMap
            }
        }
    } catch {
        Write-Host "    WARNING: could not parse existing mcp_agent_bindings.json" -ForegroundColor Yellow
    }
}

# Detect default agent from puppy.cfg
$defaultAgent = "Code-Puppy"
$puppyCfg = Join-Path $codePuppyDir "puppy.cfg"
if (Test-Path $puppyCfg) {
    $cfgLine = Select-String -Path $puppyCfg -Pattern "^\s*default_agent\s*=" | Select-Object -First 1
    if ($cfgLine) {
        $defaultAgent = ($cfgLine.Line -split "=", 2)[1].Trim()
    }
}

if (-not $bindingsRoot.bindings.ContainsKey($defaultAgent)) {
    $bindingsRoot.bindings[$defaultAgent] = @{}
}
$bindingsRoot.bindings[$defaultAgent]["substance_designer"] = @{ auto_start = $true }

[System.IO.File]::WriteAllText($bindingsPath, ($bindingsRoot | ConvertTo-Json -Depth 12), $utf8NoBom)
Write-Host "    Bound substance_designer -> agent '$defaultAgent' (auto_start=true)" -ForegroundColor Green
Write-Host "    Wrote $bindingsPath" -ForegroundColor Green

# === Summary ===
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " INSTALLATION SUMMARY" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " SD Plugin:      $sdPluginDest"
Write-Host " Bridge server:  $serverDir"
Write-Host " uv:             $uvExe"
Write-Host " Code Puppy dir: $codePuppyDir"
Write-Host " Bound agent:    $defaultAgent"
Write-Host ""
Write-Host " CRITICAL: Start Substance Designer BEFORE Code Puppy." -ForegroundColor Red
Write-Host " The SD plugin binds TCP 9881 on SD startup." -ForegroundColor Gray
Write-Host ""
Write-Host " In Code Puppy:" -ForegroundColor White
Write-Host "   /mcp status" -ForegroundColor Yellow
Write-Host "   /mcp start substance_designer" -ForegroundColor Yellow
Write-Host ""
Write-Host " Done." -ForegroundColor Green
