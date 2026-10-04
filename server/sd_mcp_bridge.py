#!/usr/bin/env python
"""
sd_mcp_bridge.py - Substance Designer MCP Bridge v2.0.0

Relay between Claude (stdio/FastMCP) and the SD plugin (TCP).

Architecture: Claude -> stdio -> this bridge -> TCP localhost:<port> -> SD plugin

Protocol: Length-prefix framing [4-byte big-endian length][JSON payload]
Connection: Fresh TCP socket per command (no persistent connection)

Fixes in v2.0.0:
  BUG-B01: _send_lock no longer held across full retry loop (prevents 360s deadlock)
  BUG-B03: Default port corrected to 9881 (was 9880)
  BUG-B04: directionalwarp warp input corrected to "inputintensity" (was "inputgradient")
  BUG-B05: FastMCP lifespan set at constructor, not post-construction attribute
  BUG-B06: ctx: Context kept for FastMCP compatibility (injection works in 1.4.1+)
  BUG-B07: None result returns "{}" not "null"; float nan/inf handled via SD plugin _json_safe
  BUG-B08: Retry logic documented correctly (retries connection errors only, not timeouts)

Usage:
    uv run --directory E:/Create/Build/DCC/MCP/SubstanceDesignerMCP/server \\
           python sd_mcp_bridge.py --port 9881
"""
import sys
import os
import json
import struct
import socket
import logging
import argparse
import asyncio
import time
import threading
from typing import Any, List, Optional
from contextlib import asynccontextmanager

# Ensure venv site-packages on path
script_dir = os.path.dirname(os.path.abspath(__file__))
venv_site = os.path.join(script_dir, '.venv', 'Lib', 'site-packages')
if os.path.exists(venv_site):
    sys.path.insert(0, venv_site)

from mcp.server.fastmcp import FastMCP, Context

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SD_MCP_Bridge")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TIMEOUT = 120          # SD can be slow on heavy operations
CONNECT_TIMEOUT = 5    # timeout for initial TCP connection
HEADER_SIZE = 4
MAX_RETRIES = 2        # only for connection failures, not SD operation timeouts
RETRY_DELAY = 1.0      # seconds between retry attempts

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_sd_port: int = 9881   # BUG-B03 fix: default matches SD plugin DEFAULT_PORTS
# BUG-B01 fix: lock is NOT held across the retry loop — only during the actual
# socket operation. This prevents a single timeout from blocking the bridge for
# 3 x 120 = 360 seconds. Each _send_command call acquires its own lock window.
_send_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Length-prefix protocol
# ---------------------------------------------------------------------------
def _send_framed(sock: socket.socket, data: bytes) -> None:
    sock.sendall(struct.pack(">I", len(data)) + data)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """Read exactly n bytes. Returns b"" on clean disconnect."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf += chunk
    return buf


def _recv_framed(sock: socket.socket, timeout: float) -> bytes:
    sock.settimeout(timeout)
    header = _recv_exact(sock, HEADER_SIZE)
    if not header:
        raise ConnectionAbortedError("Connection closed while reading header.")
    msg_len = struct.unpack(">I", header)[0]
    if msg_len == 0:
        return b""
    if msg_len > 100 * 1024 * 1024:
        raise ValueError(f"Message too large: {msg_len} bytes")
    payload = _recv_exact(sock, msg_len)
    if not payload:
        raise ConnectionAbortedError("Connection closed while reading payload.")
    return payload


# ---------------------------------------------------------------------------
# Send command — BUG-B01 fix: lock held only for the socket operation
# ---------------------------------------------------------------------------
def _send_command_locked(cmd_type: str, params: dict = None) -> dict:
    """
    Open fresh TCP connection, send one command, receive one response.
    Lock is acquired INSIDE this function for the duration of the socket op.
    This prevents a single timeout from holding the lock for 120+ seconds.
    """
    command = {"type": cmd_type, "params": params or {}}
    data_out = json.dumps(command).encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT)
    try:
        sock.connect(("localhost", _sd_port))
    except Exception as e:
        sock.close()
        raise ConnectionError(
            f"Cannot connect to Substance Designer on localhost:{_sd_port}. "
            f"Is SD running with the MCP plugin loaded? ({e})")

    # Acquire lock AFTER connection is established — only for the send/recv cycle
    with _send_lock:
        try:
            _send_framed(sock, data_out)
            response_bytes = _recv_framed(sock, TIMEOUT)
            if not response_bytes:
                return {"status": "error", "message": f"Empty response from SD on '{cmd_type}'."}
            return json.loads(response_bytes.decode("utf-8"))
        except socket.timeout:
            return {"status": "error",
                    "message": f"Timeout ({TIMEOUT}s) waiting for SD on '{cmd_type}'. "
                               f"SD may be busy — try again."}
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Invalid JSON from SD: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Communication error: {e}"}
        finally:
            try:
                sock.close()
            except Exception:
                pass


def _send(cmd_type: str, params: dict = None) -> str:
    """
    Send with retry for connection errors only.
    BUG-B01 fix: retry loop is OUTSIDE the lock (lock is inside _send_command_locked).
    BUG-B08 clarification: timeouts do NOT retry (would just re-queue a stuck SD op).
    Returns formatted result string for MCP tool response.
    """
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = _send_command_locked(cmd_type, params)
            if response.get("status") == "error":
                msg = response.get("message", "Unknown error")
                # Only retry on connection errors (SD not yet started, transient)
                is_connect_err = "Cannot connect" in msg or "connect" in msg.lower()
                if is_connect_err and attempt < MAX_RETRIES:
                    last_error = msg
                    logger.warning(f"Attempt {attempt+1} failed (connect): {msg}. Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                    continue
                # Non-retryable errors (timeout, SD errors, validation) — return immediately
                return f"Error: {msg}"
            result = response.get("result")
            # BUG-B07 fix: None result returns "{}" not "null"
            if result is None:
                result = {}
            return json.dumps(result, indent=2)
        except ConnectionError as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                logger.warning(f"Attempt {attempt+1} failed (connection): {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue
            return f"Connection Error: {e}"
        except Exception as e:
            logger.error(f"Unexpected error in {cmd_type}: {e}", exc_info=True)
            return f"Error: {e}"
    return f"Error: All {MAX_RETRIES+1} attempts failed. Last: {last_error}"


async def _async_send(cmd_type: str, params: dict = None) -> str:
    return await asyncio.to_thread(_send, cmd_type, params)


# ---------------------------------------------------------------------------
# FastMCP Server — BUG-B05 fix: lifespan passed at constructor
# ---------------------------------------------------------------------------
@asynccontextmanager
async def _lifespan(app: FastMCP):
    logger.info(f"Substance Designer MCP Bridge v2.0.0 -> SD plugin on port {_sd_port}")
    logger.info("Ensure Substance Designer is running with the MCP plugin loaded.")
    yield {}
    logger.info("Substance Designer MCP bridge shutting down.")


# BUG-B05 fix: pass lifespan at construction (not post-construction attribute)
mcp = FastMCP("SubstanceDesignerMCP", lifespan=_lifespan)


# ======================================================================
# MCP TOOLS
# BUG-B06 note: ctx: Context kept — FastMCP 1.4.1+ injects it correctly.
# If a future version drops injection, remove ctx parameter from all tools.
# ======================================================================

@mcp.tool()
async def get_scene_info(ctx: Context) -> str:
    """
    Get info about loaded packages and graphs in Substance Designer.
    Returns packages, graphs, node counts, current graph, and SD version.
    """
    return await _async_send("get_scene_info")


@mcp.tool()
async def create_package(ctx: Context) -> str:
    """
    Create a new empty package in Substance Designer.
    Use save_package to save it to disk afterward.
    """
    return await _async_send("create_package")


@mcp.tool()
async def create_graph(ctx: Context,
                       package_index: int = 0,
                       graph_name: str = "MCP_Graph",
                       package_path: Optional[str] = None) -> str:
    """
    Create a new SBS Compositing Graph in Substance Designer.
    - package_index: which loaded package (0 = first/current)
    - graph_name: identifier for the new graph
    - package_path: optional full path to specific .sbs file

    IMPORTANT: graph_name should use only letters, digits, underscores.
    Spaces and special characters are automatically sanitized.
    """
    return await _async_send("create_graph", {
        "package_index": package_index,
        "graph_name": graph_name,
        "package_path": package_path,
    })


@mcp.tool()
async def delete_graph(ctx: Context,
                       graph_identifier: str,
                       package_index: int = 0) -> str:
    """Delete a graph from a package."""
    return await _async_send("delete_graph", {
        "graph_identifier": graph_identifier,
        "package_index": package_index,
    })


@mcp.tool()
async def open_graph(ctx: Context, graph_identifier: str) -> str:
    """Open a graph in the Substance Designer UI editor."""
    return await _async_send("open_graph", {"graph_identifier": graph_identifier})


@mcp.tool()
async def get_graph_info(ctx: Context,
                         graph_identifier: Optional[str] = None,
                         node_limit: int = 100,
                         include_connections: bool = True) -> str:
    """
    Get detailed info about a graph including all nodes and connections.
    - graph_identifier: graph identifier (None = current active graph)
    - node_limit: max nodes to return in detail (default 100; use 0 for summary/count only)
    - include_connections: whether to include connection data per node (default True)

    For large graphs (100+ nodes), use node_limit=0 to get just the count,
    then query specific nodes with get_node_info.
    """
    return await _async_send("get_graph_info", {
        "graph_identifier": graph_identifier,
        "node_limit": node_limit,
        "include_connections": include_connections,
    })


@mcp.tool()
async def list_node_definitions(ctx: Context,
                                filter_text: str = "",
                                graph_identifier: Optional[str] = None,
                                limit: int = 500) -> str:
    """
    List available node definitions in Substance Designer.
    - filter_text: search filter (e.g. 'blur', 'cells', 'perlin', 'blend')
    - graph_identifier: optional graph to query from
    - limit: max results (default 500)

    Common sbs::compositing:: definitions:
      uniform, blend, levels, normal, curve, hsl, gradient, blur, sharpen,
      warp, directionalwarp, emboss, transformation, distance, grayscaleconversion,
      shuffle, pixelprocessor, fxmaps, bitmap, output, input_color, input_grayscale
    """
    return await _async_send("list_node_definitions", {
        "filter_text": filter_text,
        "graph_identifier": graph_identifier,
        "limit": limit,
    })


@mcp.tool()
async def create_node(ctx: Context,
                      definition_id: str,
                      graph_identifier: Optional[str] = None,
                      position: Optional[List[float]] = None) -> str:
    """
    Create an atomic node in a Substance Designer graph.
    - definition_id: e.g. 'sbs::compositing::blend', 'sbs::compositing::levels'
    - graph_identifier: target graph (None = current active graph)
    - position: [x, y] position in graph editor

    Common definition_ids:
      sbs::compositing::uniform        - Solid color/grayscale
      sbs::compositing::blend          - Blend two inputs (modes: Copy=0, Add=1, Subtract=2, Multiply=3, etc.)
      sbs::compositing::levels         - Levels adjustment
      sbs::compositing::normal         - Height to Normal map
      sbs::compositing::curve          - Curve adjustment
      sbs::compositing::hsl            - Hue/Saturation/Luminosity
      sbs::compositing::blur           - Gaussian blur
      sbs::compositing::sharpen        - Sharpen
      sbs::compositing::warp           - Warp/distortion
      sbs::compositing::directionalwarp - Directional warp
      sbs::compositing::emboss         - Emboss
      sbs::compositing::transformation - 2D transform
      sbs::compositing::distance       - Distance field
      sbs::compositing::grayscaleconversion - RGB to grayscale
      sbs::compositing::shuffle        - Channel shuffle
      sbs::compositing::bitmap         - Bitmap input
      sbs::compositing::fxmaps         - FX-Map (pattern generator)
      sbs::compositing::pixelprocessor - Per-pixel math
      sbs::compositing::passthrough    - Pass-through
      sbs::compositing::input_color    - Color input parameter
      sbs::compositing::input_grayscale - Grayscale input parameter

    Returns node_id which is used in connect_nodes, set_parameter, etc.
    """
    return await _async_send("create_node", {
        "definition_id": definition_id,
        "graph_identifier": graph_identifier,
        "position": position,
    })


@mcp.tool()
async def create_instance_node(ctx: Context,
                               resource_url: str,
                               graph_identifier: Optional[str] = None,
                               position: Optional[List[float]] = None) -> str:
    """
    Create an instance of a library node (Cells, Perlin Noise, etc.).
    First use get_library_nodes to find the resource_url.
    - resource_url: URL like 'pkg:///cells_1?dependency=1563150890'
    - graph_identifier: target graph (None = current)
    - position: [x, y]

    IMPORTANT: After creating, call get_node_info(node_id) to find the exact
    output/input port IDs before connecting. Library nodes do NOT use
    'unique_filter_output' — they have custom output names.
    """
    return await _async_send("create_instance_node", {
        "resource_url": resource_url,
        "graph_identifier": graph_identifier,
        "position": position,
    })


@mcp.tool()
async def create_output_node(ctx: Context,
                             usage: str = "baseColor",
                             label: Optional[str] = None,
                             graph_identifier: Optional[str] = None,
                             position: Optional[List[float]] = None) -> str:
    """
    Create an output node with a specific PBR usage in Substance Designer.
    - usage: baseColor, normal, height, roughness, metallic, ambientOcclusion, emissive, opacity
    - label: display label (defaults to usage name)
    - graph_identifier: target graph (None = current)
    - position: [x, y]
    """
    return await _async_send("create_output_node", {
        "usage": usage,
        "label": label,
        "graph_identifier": graph_identifier,
        "position": position,
    })


@mcp.tool()
async def connect_nodes(ctx: Context,
                        from_node_id: str,
                        to_node_id: str,
                        from_output: str = "unique_filter_output",
                        to_input: str = "input1",
                        graph_identifier: Optional[str] = None) -> str:
    """
    Connect two nodes in a Substance Designer graph.
    - from_node_id: source node identifier (from create_node result)
    - to_node_id: destination node identifier
    - from_output: output slot on source (always 'unique_filter_output' for atomic nodes)
    - to_input: input slot - CRITICAL, must match target node type exactly:

    NODE TYPE              to_input
    blur               ->  "input1"
    levels             ->  "input1"
    normal             ->  "input1"
    curve              ->  "input1"
    hsl                ->  "input1"
    sharpen            ->  "input1"
    grayscaleconversion->  "input1"
    transformation     ->  "input1"
    emboss             ->  "input1"
    warp               ->  "input1" (image), "inputgradient" (warp map)
    directionalwarp    ->  "input1" (image), "inputintensity" (warp map — NOT inputgradient!)
    distance           ->  "input1"
    blend              ->  "source" (fg), "destination" (bg), "opacity" (mask)
    output             ->  "inputNodeOutput"

    For library nodes (Cells, Perlin, Polygon, etc.): ALWAYS run get_node_info
    first to discover exact input/output IDs. Never guess.

    - graph_identifier: target graph (None = current)
    """
    return await _async_send("connect_nodes", {
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "from_output": from_output,
        "to_input": to_input,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def disconnect_nodes(ctx: Context,
                           node_id: str,
                           input_id: str,
                           graph_identifier: Optional[str] = None) -> str:
    """
    Disconnect all connections to a specific input of a node.
    - node_id: target node
    - input_id: input property to disconnect (e.g. 'input1', 'source')
    - graph_identifier: target graph (None = current)
    """
    return await _async_send("disconnect_nodes", {
        "node_id": node_id,
        "input_id": input_id,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def set_parameter(ctx: Context,
                        node_id: str,
                        parameter_id: str,
                        value: Any,
                        value_type: str = "float",
                        graph_identifier: Optional[str] = None) -> str:
    """
    Set a parameter on a node in Substance Designer.
    - node_id: target node identifier
    - parameter_id: parameter name

    Common parameter IDs:
      '$outputsize'  - Resolution as int2, e.g. [11,11] for 2048x2048
      'intensity'    - Blur/sharpen/normal intensity (float)
      'blendingmode' - Blend mode (int): 0=Copy, 1=Add, 2=Subtract, 3=Multiply, 9=Overlay
      'opacitymult'  - Blend opacity multiplier (float 0-1)
      'outputcolor'  - Uniform color output (color [r,g,b,a])
      'levelinlow'   - Levels input low (float4)
      'levelinhigh'  - Levels input high (float4)
      'leveloutlow'  - Levels output low (float4)
      'levelouthigh' - Levels output high (float4)
      'hue'          - HSL hue shift (float 0-1, 0.5=no shift)
      'saturation'   - HSL saturation (float 0-1, 0.5=no change)
      'luminosity'   - HSL luminosity (float 0-1, 0.5=no change)
      'matrix22'     - Transformation matrix (float4)
      'offset'       - Transformation offset (float2)
      'channelsweights' - Grayscale channel weights (float4)

    - value: the value to set
    - value_type: 'float', 'int', 'bool', 'string', 'float2', 'float3', 'float4',
                  'color' (RGBA 0-1), 'int2', 'int3', 'int4'
    - graph_identifier: target graph (None = current)
    """
    return await _async_send("set_parameter", {
        "node_id": node_id,
        "parameter_id": parameter_id,
        "value": value,
        "value_type": value_type,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def get_node_info(ctx: Context,
                        node_id: str,
                        graph_identifier: Optional[str] = None) -> str:
    """
    Get detailed info about a node (properties, connections, position).
    - node_id: node identifier
    - graph_identifier: target graph (None = current)

    IMPORTANT: Call this for ANY library node before connecting it.
    The response includes exact input/output port IDs and whether it's a library node.
    """
    return await _async_send("get_node_info", {
        "node_id": node_id,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def delete_node(ctx: Context,
                      node_id: str,
                      graph_identifier: Optional[str] = None) -> str:
    """
    Delete a node from a Substance Designer graph.
    - node_id: node identifier to delete
    - graph_identifier: target graph (None = current)
    """
    return await _async_send("delete_node", {
        "node_id": node_id,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def move_node(ctx: Context,
                    node_id: str,
                    position: List[float],
                    graph_identifier: Optional[str] = None) -> str:
    """
    Move a node to a new position in the graph.
    - node_id: node to move
    - position: [x, y] new position
    - graph_identifier: target graph (None = current)

    PREFER move_node over arrange_nodes — arrange_nodes DESTROYS all connections in SD 15.
    """
    return await _async_send("move_node", {
        "node_id": node_id,
        "position": position,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def duplicate_node(ctx: Context,
                         node_id: str,
                         offset: Optional[List[float]] = None,
                         graph_identifier: Optional[str] = None) -> str:
    """
    Duplicate an ATOMIC node (creates a new node of the same type).
    - node_id: node to duplicate (must be atomic, not a library instance node)
    - offset: [dx, dy] position offset from original (default [100, 0])
    - graph_identifier: target graph (None = current)

    WARNING: Library nodes (Cells, Perlin, Polygon, etc.) CANNOT be duplicated
    via this method. Use create_instance_node with the same resource_url instead.
    """
    return await _async_send("duplicate_node", {
        "node_id": node_id,
        "offset": offset,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def set_graph_output_size(ctx: Context,
                                width_log2: int = 11,
                                height_log2: int = 11,
                                graph_identifier: Optional[str] = None) -> str:
    """
    Set the output resolution of a graph.
    - width_log2: log2 of width (9=512, 10=1024, 11=2048, 12=4096)
    - height_log2: log2 of height
    - graph_identifier: target graph (None = current)
    """
    return await _async_send("set_graph_output_size", {
        "width_log2": width_log2,
        "height_log2": height_log2,
        "graph_identifier": graph_identifier,
    })


@mcp.tool()
async def save_package(ctx: Context,
                       package_index: int = 0,
                       file_path: Optional[str] = None,
                       package_path: Optional[str] = None) -> str:
    """
    Save a package to disk.
    - package_index: which user package (0 = first)
    - file_path: if given, Save As to this path (.sbs) — directories created automatically
    - package_path: identify package by existing file path
    """
    return await _async_send("save_package", {
        "package_index": package_index,
        "file_path": file_path,
        "package_path": package_path,
    })


@mcp.tool()
async def get_library_nodes(ctx: Context,
                            filter_text: str = "",
                            limit: int = 200) -> str:
    """
    Get available library nodes from Substance Designer's built-in packages.
    Returns resource URLs for use with create_instance_node.
    - filter_text: search filter (e.g. 'cell', 'perlin', 'noise', 'grunge', 'polygon')
    - limit: max results

    After getting a URL, use create_instance_node(resource_url=url) to add it,
    then get_node_info(node_id) to discover its port IDs before connecting.
    """
    return await _async_send("get_library_nodes", {
        "filter_text": filter_text,
        "limit": limit,
    })


@mcp.tool()
async def arrange_nodes(ctx: Context,
                        graph_identifier: Optional[str] = None,
                        start_x: float = -1000,
                        start_y: float = 0,
                        node_spacing_x: float = 200,
                        node_spacing_y: float = 150) -> str:
    """
    Auto-arrange all nodes in a graph in a grid layout.
    - graph_identifier: target graph (None = current)
    - start_x, start_y: starting position
    - node_spacing_x, node_spacing_y: spacing between nodes

    WARNING: In SD 15, arrange_nodes DESTROYS all node connections.
    Use move_node() instead to reposition nodes without losing connections.
    Only use this tool when you don't mind reconnecting all nodes manually.
    """
    return await _async_send("arrange_nodes", {
        "graph_identifier": graph_identifier,
        "start_x": start_x,
        "start_y": start_y,
        "node_spacing_x": node_spacing_x,
        "node_spacing_y": node_spacing_y,
    })


@mcp.tool()
async def execute_sd_code(ctx: Context, code: str) -> str:
    """
    Execute arbitrary Python code in Substance Designer's main thread (safe).
    Variables available: sd, app, pkg_mgr, ui_mgr, open_in_editor
    Returns stdout, stderr, and any error.

    WARNING: No timeout protection. Blocking code will hang SD indefinitely.
    Keep code short, simple, and non-blocking.
    """
    return await _async_send("execute_code", {"code": code})


@mcp.tool()
async def create_batch_graph(ctx: Context,
                             graph_name: str,
                             package_index: int = 0,
                             nodes: Optional[List[dict]] = None,
                             connections: Optional[List[dict]] = None,
                             output_size_log2: int = 11,
                             open_in_editor: bool = True,
                             package_path: Optional[str] = None) -> str:
    """
    Create a complete graph from a descriptor in ONE call. Most efficient for complex graphs.

    nodes: list of node descriptors:
      {
        "id_alias": "my_blur",           # reference name for connections
        "definition_id": "sbs::compositing::blur",
        "position": [0, 0],              # optional
        "usage": "height",               # for output nodes only
        "label": "Height Output",        # for output nodes
        "resource_url": "pkg:///...",    # for library nodes (use get_library_nodes first)
        "parameters": {                  # optional parameter overrides
          "intensity": 10.0,             # shorthand (auto-detects float)
          "$outputsize": {"value": [11,11], "type": "int2"}  # explicit type
        }
      }

    connections: list of connection descriptors:
      {
        "from": "my_blur",                  # from node alias
        "to": "height_output",              # to node alias
        "from_output": "unique_filter_output",  # optional (default for atomic nodes)
        "to_input": "inputNodeOutput"       # required for output nodes
      }

    IMPORTANT for library nodes in batch:
      - Use "resource_url" (not "definition_id") for library nodes
      - You MUST know the output port IDs in advance
        (run create_instance_node + get_node_info first in test mode)
      - Batch does NOT validate library node port IDs automatically

    Returns: node_map {alias -> actual_node_id} + creation stats
    """
    return await _async_send("create_batch_graph", {
        "graph_name": graph_name,
        "package_index": package_index,
        "nodes": nodes or [],
        "connections": connections or [],
        "output_size_log2": output_size_log2,
        "open_in_editor": open_in_editor,
        "package_path": package_path,
    })


# ---------------------------------------------------------------------------
# Recipe tools
# ---------------------------------------------------------------------------

@mcp.tool()
async def list_recipes(ctx: Context) -> str:
    """
    List all built-in material recipes available in the SD MCP plugin.
    Returns material recipes (metals, rocks, organic, soils, water/ice, gems)
    and heightmap styles (cliff, rock, sand, cracked, mountain, cobblestone).
    """
    return await _async_send("list_recipes", {})


@mcp.tool()
async def get_recipe_info(ctx: Context, recipe_name: str) -> str:
    """
    Get detailed info about a specific material recipe.
    recipe_name: e.g. 'steel', 'marble', 'gold', 'wood_oak', 'ice', 'diamond'
    """
    return await _async_send("get_recipe_info", {"recipe_name": recipe_name})


@mcp.tool()
async def build_material_graph(ctx: Context,
                                graph_name: str,
                                recipe_name: str,
                                package_index: int = 0,
                                overrides: Optional[dict] = None,
                                output_size_log2: int = 11,
                                open_in_editor: bool = True,
                                package_path: Optional[str] = None) -> str:
    """
    Build a complete PBR material graph from a named recipe in ONE call.

    Available recipes: steel, iron, copper, gold, silver, aluminum,
    granite, marble, sandstone, limestone, slate,
    wood, wood_oak, oak, moss, bone,
    sand, mud, gravel, clay,
    ice, snow, frost, water,
    diamond, ruby, sapphire, emerald, amethyst.

    Each recipe generates: Height + Normal + Roughness + AO + BaseColor + Metallic outputs.

    overrides: optional dict to override node parameters, keyed by node alias.
    output_size_log2: 10=1024, 11=2048, 12=4096
    """
    return await _async_send("build_material_graph", {
        "graph_name": graph_name,
        "recipe_name": recipe_name,
        "package_index": package_index,
        "overrides": overrides,
        "output_size_log2": output_size_log2,
        "open_in_editor": open_in_editor,
        "package_path": package_path,
    })


@mcp.tool()
async def build_heightmap_graph(ctx: Context,
                                 graph_name: str,
                                 style: str,
                                 package_index: int = 0,
                                 output_size_log2: int = 11,
                                 open_in_editor: bool = True,
                                 detail_level: int = 2,
                                 scale: float = 5.0,
                                 disorder: float = 0.5,
                                 package_path: Optional[str] = None) -> str:
    """
    Build a heightmap-only graph for terrain/rock/cliff.

    Available styles: cliff, rock, sand, cracked, mud, mountain, cobblestone, terrain.

    detail_level: 1=basic, 2=standard, 3=high detail
    scale: overall scale factor (1.0 to 10.0)
    disorder: amount of irregularity/warping (0.0 to 1.0)
    """
    return await _async_send("build_heightmap_graph", {
        "graph_name": graph_name,
        "style": style,
        "package_index": package_index,
        "output_size_log2": output_size_log2,
        "open_in_editor": open_in_editor,
        "detail_level": detail_level,
        "scale": scale,
        "disorder": disorder,
        "package_path": package_path,
    })


@mcp.tool()
async def apply_recipe(ctx: Context,
                        recipe_name: str,
                        graph_identifier: Optional[str] = None,
                        position_offset: Optional[List[float]] = None,
                        overrides: Optional[dict] = None) -> str:
    """
    Apply a recipe to an EXISTING graph (adds nodes + connections to current graph).
    Useful for layering multiple materials or adding detail passes.

    recipe_name: any key from list_recipes
    graph_identifier: target graph (None = current active graph)
    position_offset: [x, y] to offset all node positions (avoid overlapping with existing nodes)
    overrides: dict of node parameter overrides keyed by node alias
    """
    return await _async_send("apply_recipe", {
        "recipe_name": recipe_name,
        "graph_identifier": graph_identifier,
        "position_offset": position_offset,
        "overrides": overrides,
    })


@mcp.tool()
async def list_documentation(ctx: Context,
                              category: str = "all",
                              filter_text: str = "",
                              node_name: str = "",
                              action: str = "",
                              query: str = "") -> str:
    """
    Browse the SD MCP embedded documentation knowledge base.
    No internet required — all knowledge is built into the plugin.

    Available categories:
      all                — everything (large response, use filter_text)
      atomic_nodes       — built-in nodes: blend, levels, blur, normal, warp, etc.
      library_nodes      — library nodes: cells, perlin, flood_fill, histogram_scan, etc.
      blend_modes        — all blend mode integers and descriptions
      port_reference     — input/output port names for every node type
      pbr_outputs        — PBR output usage tags and conventions
      workflow           — step-by-step usage rules and best practices
      concepts           — SD concepts: recipes, pro recipes, graph structure
      shortcuts          — SD keyboard shortcuts
      connection_patterns — common node chains (e.g. height→normal→AO)
      node_categories    — node families and groupings
      parameters         — parameter reference for common nodes

    Special actions:
      action="categories"         → list all available categories
      action="search", query="X"  → search all docs for keyword X

    Examples:
      list_documentation(category="atomic_nodes", node_name="blend")
      list_documentation(category="port_reference")
      list_documentation(action="search", query="directionalwarp")
      list_documentation(category="workflow")
      list_documentation(category="pbr_outputs")
    """
    return await _async_send("list_documentation", {
        "category": category,
        "filter_text": filter_text,
        "node_name": node_name,
        "action": action,
        "query": query,
    })


# ---------------------------------------------------------------------------
# Stylized knowledge base (local — no SD TCP required)
# Mined from F:\SUBSTANCE_DESIGNER\SBS\STYLIZED_EXTRACTED via mine_stylized_kb.py
# ---------------------------------------------------------------------------
_KB_DIR = os.path.normpath(
    os.path.join(script_dir, "..", "knowledge", "stylized")
)
_kb_catalog_cache: Optional[dict] = None
_kb_patterns_cache: Optional[dict] = None
_kb_playbook_cache: Optional[str] = None
_kb_materials_cache: Optional[list] = None


def _kb_load_catalog() -> dict:
    global _kb_catalog_cache
    if _kb_catalog_cache is None:
        path = os.path.join(_KB_DIR, "catalog.json")
        if not os.path.exists(path):
            return {"error": f"stylized KB missing at {path} — run mine_stylized_kb.py"}
        with open(path, "r", encoding="utf-8") as f:
            _kb_catalog_cache = json.load(f)
    return _kb_catalog_cache


def _kb_load_patterns() -> dict:
    global _kb_patterns_cache
    if _kb_patterns_cache is None:
        path = os.path.join(_KB_DIR, "patterns.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            _kb_patterns_cache = json.load(f)
    return _kb_patterns_cache


def _kb_load_playbook() -> str:
    global _kb_playbook_cache
    if _kb_playbook_cache is None:
        path = os.path.join(_KB_DIR, "playbook.md")
        if not os.path.exists(path):
            return "playbook.md missing — run mine_stylized_kb.py"
        with open(path, "r", encoding="utf-8") as f:
            _kb_playbook_cache = f.read()
    return _kb_playbook_cache


def _kb_load_materials() -> list:
    """Full material fingerprints (heavier). Loaded lazily."""
    global _kb_materials_cache
    if _kb_materials_cache is None:
        path = os.path.join(_KB_DIR, "materials.jsonl")
        rows = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
        _kb_materials_cache = rows
    return _kb_materials_cache


def _kb_specialty(item: dict) -> list:
    """Specialty library filters (ad_*/st_*). New key specialty_filters; legacy adobe_filters."""
    return item.get("specialty_filters") or item.get("adobe_filters") or []


def _kb_score(item: dict, tokens: List[str]) -> int:
    blob = " ".join(
        [
            item.get("id", ""),
            item.get("title", ""),
            item.get("category", ""),
            " ".join(item.get("patterns") or []),
            " ".join(_kb_specialty(item)),
            " ".join(item.get("color_params") or []),
        ]
    ).lower()
    score = 0
    for t in tokens:
        if t in blob:
            score += 2 if t in (item.get("id", "") + " " + item.get("category", "")).lower() else 1
    return score


@mcp.tool()
async def stylized_list_categories(ctx: Context) -> str:
    """
    List stylized reference material categories mined from the local STYLIZED_EXTRACTED library.
    Returns category name, material count, and avg graph structure (nodes/blends/levels/warps).
    Use this BEFORE building a stylized material to pick the right design language.
    """
    cat = _kb_load_catalog()
    if cat.get("error"):
        return json.dumps(cat)
    pats = _kb_load_patterns()
    rows = []
    for name, count in (cat.get("categories") or {}).items():
        p = pats.get(name) or {}
        rows.append(
            {
                "category": name,
                "count": count,
                "avg_nodes": p.get("avg_nodes"),
                "avg_blends": p.get("avg_blends"),
                "avg_levels": p.get("avg_levels"),
                "avg_hsl": p.get("avg_hsl"),
                "avg_warps": p.get("avg_warps"),
                "top_patterns": [x[0] for x in (p.get("top_patterns") or [])[:6]],
                "top_specialty_filters": [
                    x[0]
                    for x in (
                        p.get("top_specialty_filters")
                        or p.get("top_adobe_filters")
                        or []
                    )[:6]
                ],
                "examples": (p.get("examples") or [])[:5],
            }
        )
    rows.sort(key=lambda r: -(r.get("count") or 0))
    return json.dumps({"total_materials": cat.get("total"), "categories": rows}, indent=2)


@mcp.tool()
async def stylized_search(ctx: Context,
                           query: str,
                           category: str = "",
                           limit: int = 12) -> str:
    """
    Search the stylized reference material knowledge base.

    query: free text e.g. 'gold tarnish', 'brick mossy', 'wood parquet', 'scifi floor'
    category: optional hard filter e.g. 'metal_gold', 'brick', 'wood_planks', 'marble'
    limit: max results (default 12)

    Returns matching materials with sbs_path, preview_path, patterns, specialty filters,
    and color params so you can open references in SD or mimic their graph structure.
    """
    cat = _kb_load_catalog()
    if cat.get("error"):
        return json.dumps(cat)
    tokens = [t.lower() for t in (query or "").replace("_", " ").split() if t.strip()]
    cat_f = (category or "").strip().lower()
    hits = []
    for item in cat.get("index") or []:
        if cat_f and item.get("category", "").lower() != cat_f:
            continue
        score = _kb_score(item, tokens) if tokens else 1
        if cat_f and not tokens:
            score = 1
        if score <= 0:
            continue
        hits.append((score, item))
    hits.sort(key=lambda x: (-x[0], x[1].get("id", "")))
    limit = max(1, min(int(limit or 12), 50))
    results = []
    for score, item in hits[:limit]:
        results.append({**item, "score": score})
    return json.dumps(
        {
            "query": query,
            "category": category,
            "result_count": len(results),
            "results": results,
        },
        indent=2,
    )


@mcp.tool()
async def stylized_get_material(ctx: Context, material_id: str) -> str:
    """
    Get full fingerprint for one mined stylized material.

    material_id: slug id e.g. 'stylized_cast_gold', 'stylized_bricks'

    Returns node counts, filter histogram, library instances, specialty library filters,
    exposed params, design patterns, and absolute sbs/preview paths.
    Open sbs_path in Substance Designer to study the real graph.
    """
    mid = (material_id or "").strip().lower()
    if not mid:
        return json.dumps({"error": "material_id required"})
    for row in _kb_load_materials():
        if row.get("id", "").lower() == mid:
            return json.dumps(row, indent=2)
    # fuzzy contains
    fuzzy = [r for r in _kb_load_materials() if mid in r.get("id", "").lower()]
    if len(fuzzy) == 1:
        return json.dumps(fuzzy[0], indent=2)
    if fuzzy:
        return json.dumps(
            {
                "error": "ambiguous",
                "matches": [r.get("id") for r in fuzzy[:20]],
            },
            indent=2,
        )
    return json.dumps({"error": f"not found: {material_id}"})


@mcp.tool()
async def stylized_category_guide(ctx: Context, category: str) -> str:
    """
    Get the design pattern guide for one stylized category.

    category: e.g. 'metal_gold', 'brick', 'wood_planks', 'marble', 'scifi',
              'ground_grass', 'water', 'corrupted', 'stone_rock', 'terracotta'

    Returns avg graph structure, top filters/instances, specialty filters, color params,
    example material ids, and the build checklist for that look.
    CALL THIS before inventing a new stylized graph in that family.
    """
    pats = _kb_load_patterns()
    key = (category or "").strip().lower()
    if not key:
        return json.dumps({"error": "category required", "available": sorted(pats.keys())})
    if key not in pats:
        # fuzzy
        fuzzy = [k for k in pats if key in k or k in key]
        if len(fuzzy) == 1:
            key = fuzzy[0]
        else:
            return json.dumps(
                {"error": f"unknown category {category}", "available": sorted(pats.keys()), "close": fuzzy},
                indent=2,
            )
    info = dict(pats[key])
    info["category"] = key
    info["build_checklist"] = [
        "Block out primary shape (tile/pattern/noise -> histogram_scan).",
        "Warp/slope-blur for stylized relief; levels to tame ranges.",
        "Flat uniform colors + HSL; blend color zones with shape masks.",
        "Edge/dirt/tarnish as extra blend layers (curvature/highpass optional).",
        "Roughness simple; metallic only if metal category.",
        "Normal from height; HBAO; wire basecolor/normal/roughness/height/ao outputs.",
        "Name exposed params descriptively: wood_color, gold_roughness, wave_density...",
    ]
    # attach example previews/sbs from catalog index
    cat = _kb_load_catalog()
    ex = []
    for item in cat.get("index") or []:
        if item.get("category") == key:
            ex.append(
                {
                    "id": item.get("id"),
                    "sbs_path": item.get("sbs_path"),
                    "preview_path": item.get("preview_path"),
                    "node_count": item.get("node_count"),
                }
            )
            if len(ex) >= 8:
                break
    info["example_refs"] = ex
    return json.dumps(info, indent=2)


@mcp.tool()
async def stylized_playbook(ctx: Context, section: str = "") -> str:
    """
    Read the stylized reference design playbook mined from 600+ real SBS graphs.

    section: optional keyword to extract a slice (e.g. 'marble', 'metal', 'global',
             'checklist', 'agent'). Empty = full playbook (large).

    ALWAYS consult this (or stylized_category_guide) when the user asks for a
    stylized material — do not fall back to photoreal recipe defaults.
    """
    text = _kb_load_playbook()
    sec = (section or "").strip().lower()
    if not sec:
        # cap huge dumps a bit for context safety — still generous
        if len(text) > 60000:
            return text[:60000] + "\n\n...[truncated — pass section='marble' etc for a slice]..."
        return text
    # slice by markdown headings containing the keyword
    chunks = []
    current = []
    keep = False
    for line in text.splitlines():
        if line.startswith("#"):
            if current and keep:
                chunks.append("\n".join(current))
            current = [line]
            keep = sec in line.lower()
        else:
            current.append(line)
            if sec in line.lower():
                keep = True
    if current and keep:
        chunks.append("\n".join(current))
    if not chunks:
        # fallback: any lines with keyword
        lines = [ln for ln in text.splitlines() if sec in ln.lower()]
        return "\n".join(lines[:80]) if lines else f"No section matched '{section}'."
    return "\n\n".join(chunks)[:40000]


@mcp.tool()
async def stylized_open_reference(ctx: Context,
                                   material_id: str,
                                   open_in_editor: bool = True) -> str:
    """
    Open a mined reference stylized .sbs package in Substance Designer as a reference.

    material_id: e.g. 'stylized_cast_gold'
    open_in_editor: if True, also open the main graph in the SD UI

    Use AFTER stylized_search / stylized_get_material when you want the live graph
    on screen to study node topology while building a new material.
    """
    mid = (material_id or "").strip().lower()
    cat = _kb_load_catalog()
    if cat.get("error"):
        return json.dumps(cat)
    match = None
    for item in cat.get("index") or []:
        if item.get("id", "").lower() == mid:
            match = item
            break
    if not match:
        fuzzy = [i for i in (cat.get("index") or []) if mid in i.get("id", "").lower()]
        if len(fuzzy) == 1:
            match = fuzzy[0]
        else:
            return json.dumps(
                {
                    "error": f"not found: {material_id}",
                    "matches": [i.get("id") for i in fuzzy[:15]],
                }
            )
    sbs_path = match.get("sbs_path") or ""
    if not sbs_path or not os.path.exists(sbs_path):
        return json.dumps({"error": f"sbs missing on disk: {sbs_path}", "material": match})

    # Open via SD plugin execute_sd_code if available
    open_line = "open_in_editor(g)" if open_in_editor else "pass"
    # Forward slashes avoid Windows escape hell; SD accepts them.
    sbs_fwd = sbs_path.replace(chr(92), "/")
    code = (
        f"path = r'{sbs_fwd}'\n"
        "pkg = pkg_mgr.loadUserPackage(path, True, True)\n"
        "graphs = list(pkg.getChildrenResources(True)) if pkg else []\n"
        "gids = []\n"
        "for g in graphs:\n"
        "    try:\n"
        "        gid = g.getIdentifier()\n"
        "        gids.append(gid)\n"
        f"        {open_line}\n"
        "    except Exception:\n"
        "        pass\n"
        "print({'path': path, 'graphs': gids, 'ok': pkg is not None})\n"
    )
    try:
        result = await _async_send("execute_sd_code", {"code": code})
        return json.dumps(
            {"material": match, "opened": sbs_path, "sd_result": result},
            indent=2,
        )
    except Exception as exc:
        return json.dumps(
            {
                "material": match,
                "sbs_path": sbs_path,
                "note": "Could not auto-open in SD; open the path manually.",
                "error": str(exc),
            },
            indent=2,
        )


@mcp.tool()
async def clone_stylized_reference(ctx: Context,
                                    material_id: str,
                                    dest_path: Optional[str] = None,
                                    open_in_editor: bool = True) -> str:
    """
    Level C: Clone a mined reference stylized SBS into an editable working copy.

    material_id: e.g. 'stylized_cast_gold', 'stylized_bricks'
    dest_path: optional Save-As path (.sbs). Default: {id}_clone.sbs near source.
    open_in_editor: open the clone's main graph in SD UI

    Use when you want high-fidelity donor topology as a starting point — then
    tweak colors/params rather than rebuilding from scratch.
    Prefer stylized_* recipes (Level B) for fresh builds; use clone for fidelity.
    """
    return await _async_send("clone_stylized_reference", {
        "material_id": material_id,
        "dest_path": dest_path,
        "open_in_editor": open_in_editor,
    })


# ---------------------------------------------------------------------------
# Level D — Project art-bibles, design concepts, ensemble coherence
# Local only (no SD TCP). See knowledge/stylized/design_concepts.md
# Production domains: domains/*.md (scope above Designer craft)
# ---------------------------------------------------------------------------
try:
    import project_kb as _pkb
except ImportError:
    # allow running from other CWDs
    sys.path.insert(0, script_dir)
    import project_kb as _pkb  # type: ignore


@mcp.tool()
async def domain_list(ctx: Context) -> str:
    """
    Live-scan production domain context files under domains/*.md.

    FULLY DYNAMIC — drop/rename/delete any .md and the next call sees it.
    No static registry; no bridge restart required for new domain files.

    Domains define SCOPE for material work (workflows, non-negotiables, reuse,
    lookdev). Authority stack:
      Art Bible (look) > Domain Context (production rules) > design_concepts (D1/D2 craft)

    Returns: domains[], default_domain_id, category_map, aliases per domain, hint.
    Optional per-file Meta fields: Id, Default, Aliases, Categories, Category prefixes.
    """
    return json.dumps(_pkb.list_domains(), indent=2)


@mcp.tool()
async def domain_get(ctx: Context,
                      domain: str = "",
                      category: str = "",
                      section: str = "") -> str:
    """
    Load a production domain context (full text or section slice) + parsed checklists.

    domain: id or alias from domain_list (blank → resolve via category or live default)
    category: optional material category; routes via domain Meta Categories / prefixes
    section: optional slice e.g. 'constraint', 'workflow', 'success', 'scope', 'glossary'

    Returns authority stack, non-negotiables, agent_checklist, success_criteria, content.
    ALWAYS consult before freestyling production-facing material specs.
    New domains/*.md files are picked up automatically — no code changes.
    """
    return json.dumps(
        _pkb.load_domain(domain=domain or None, section=section, category=category),
        indent=2,
    )


@mcp.tool()
async def domain_get_section(ctx: Context,
                              section: str,
                              domain: str = "") -> str:
    """
    Convenience: return only the markdown slice for a domain section.

    domain blank → live default domain from domain_list.
    section examples: 'constraint', 'workflow', 'success', 'scope', 'edge',
    'output', 'glossary', 'roles', 'overview'
    """
    loaded = _pkb.load_domain(domain=domain or None, section=section)
    if not loaded.get("ok"):
        return json.dumps(loaded, indent=2)
    return loaded.get("content") or f"No section matched '{section}'."


@mcp.tool()
async def project_list(ctx: Context) -> str:
    """
    List art-bible projects and the active project/scene.
    Projects live under knowledge/projects/ and constrain material color/mood.
    """
    return json.dumps(_pkb.list_projects(), indent=2)


@mcp.tool()
async def project_set_active(ctx: Context,
                              project_id: str = "",
                              scene_id: str = "") -> str:
    """
    Set the active project and/or scene for subsequent design briefs & validation.

    project_id: e.g. 'fabl_forge'
    scene_id: e.g. 'keep_courtyard_overcast', 'coastal_cliffs_dusk', 'forge_heart_night'
    """
    st = _pkb.set_active_state(
        project_id=project_id or None,
        scene_id=scene_id or None,
    )
    bible = _pkb.get_art_bible(st.get("project_id"), st.get("scene_id"))
    return json.dumps({"active": st, "art_bible_summary": {
        "project_title": (bible.get("project") or {}).get("title"),
        "scene_title": (bible.get("scene") or {}).get("title"),
        "harmony_mode": (bible.get("merged_guidance") or {}).get("harmony_mode"),
        "mood_tags": (bible.get("merged_guidance") or {}).get("mood_tags"),
        "emissive_allowed": (bible.get("merged_guidance") or {}).get("emissive_allowed"),
        "ensemble_count": len((bible.get("merged_guidance") or {}).get("ensemble") or []),
    }}, indent=2)


@mcp.tool()
async def project_get_art_bible(ctx: Context,
                                 project_id: str = "",
                                 scene_id: str = "") -> str:
    """
    Load the full art bible for a project (+ optional scene overrides).

    Returns master palette, hue windows, art pillars, do/don't, scene mood,
    local palette overrides, and current ensemble materials.
    ALWAYS call before building materials that must fit a film/game/look.
    """
    return json.dumps(
        _pkb.get_art_bible(project_id or None, scene_id or None),
        indent=2,
    )


@mcp.tool()
async def project_upsert(ctx: Context,
                          project_id: str,
                          patch_json: str) -> str:
    """
    Create or update a project art bible.

    project_id: slug e.g. 'my_game'
    patch_json: JSON object fields to merge (title, art_pillars, harmony_mode,
                master_palette, hue_windows, do, dont, default_scene, ...)
    """
    try:
        patch = json.loads(patch_json) if isinstance(patch_json, str) else patch_json
    except Exception as exc:
        return json.dumps({"error": f"invalid patch_json: {exc}"})
    if not isinstance(patch, dict):
        return json.dumps({"error": "patch_json must be a JSON object"})
    return json.dumps(_pkb.upsert_project(project_id, patch), indent=2)


@mcp.tool()
async def project_set_scene(ctx: Context,
                             project_id: str,
                             scene_id: str,
                             patch_json: str = "{}") -> str:
    """
    Create or update a scene under a project (biome/shot mood + local palette + ensemble).

    patch_json fields: title, mood_tags, wetness, dust, emissive_allowed,
    local_palette, preferred_categories, do, dont, roughness_bias, ...
    """
    try:
        patch = json.loads(patch_json) if patch_json else {}
    except Exception as exc:
        return json.dumps({"error": f"invalid patch_json: {exc}"})
    if not isinstance(patch, dict):
        return json.dumps({"error": "patch_json must be a JSON object"})
    result = _pkb.upsert_scene(project_id, scene_id, patch)
    # auto-activate
    if result.get("ok"):
        _pkb.set_active_state(project_id=project_id, scene_id=scene_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def project_register_material(ctx: Context,
                                     material_id: str,
                                     category: str = "",
                                     path: str = "",
                                     roles_json: str = "{}",
                                     project_id: str = "",
                                     scene_id: str = "",
                                     status: str = "approved",
                                     notes: str = "") -> str:
    """
    Register a built material into the project log + scene ensemble.

    roles_json: JSON map of role -> [r,g,b] or #hex
      e.g. '{"primary":[0.42,0.4,0.37],"shadow":[0.16,0.15,0.13]}'
    Call AFTER validate_material_against_project passes.
    """
    active = _pkb.get_active_state()
    pid = project_id or active["project_id"]
    sid = scene_id or active["scene_id"]
    try:
        roles = json.loads(roles_json) if roles_json else {}
    except Exception as exc:
        return json.dumps({"error": f"invalid roles_json: {exc}"})
    return json.dumps(
        _pkb.register_material(
            pid,
            sid,
            material_id,
            category=category,
            path=path,
            roles=roles,
            status=status,
            notes=notes,
        ),
        indent=2,
    )


@mcp.tool()
async def stylized_design_concepts(ctx: Context, section: str = "") -> str:
    """
    Read the Level D stylized design-concepts guide (beauty rules, color roles,
    harmony, ensemble logic, anti-patterns).

    section: optional slice e.g. 'beautiful', 'color', 'ensemble', 'anti', 'project'
    This is Designer D1/D2 CRAFT theory. For production scope / 3D-game application
    rules (master/instance, texel density, lookdev), use domain_get instead.
    """
    return _pkb.load_design_concepts(section)


@mcp.tool()
async def stylized_design_brief(ctx: Context,
                                 material_name: str,
                                 category: str,
                                 project_id: str = "",
                                 scene_id: str = "",
                                 structure_intent: str = "",
                                 story_wear: str = "",
                                 hero: bool = False,
                                 wants_emissive: bool = False,
                                 build_path: str = "auto",
                                 notes: str = "",
                                 domain: str = "") -> str:
    """
    Level D: Produce a full pre-build design brief bound to the project/scene ART BIBLE
    (look/color/mood) AND the production domain (pipeline rules only).

    LOOK AUTHORITY = art bible + active scene. Domain is NOT a palette.
    Returns art_bible_lock.color_card that MUST be applied after any recipe/clone.

    Returns:
      - art_bible_lock (mandatory color_card, scene_grade, ship_gate) ← LOOK
      - production_domain / domain_production_checklist ← pipeline only
      - domain1_authoring_checklist + domain2_ensemble_checklist ← Designer craft
      - palette, roughness, donor_hints (topology only), ensemble, pre_validation

    CALL THIS before clone/recipe. After build: apply color_card, then
    validate_material_against_project — never ship on fail.
    category: stone_pavement, water, stone_rock, wood_planks, metal_iron, leather, ...
    domain: optional override id/alias (blank → live resolve via category Meta / default)
    build_path: auto | level_B_recipe_then_regrade | level_C_clone_then_regrade
    """
    return json.dumps(
        _pkb.design_brief(
            material_name,
            category,
            project_id=project_id or None,
            scene_id=scene_id or None,
            structure_intent=structure_intent,
            story_wear=story_wear,
            hero=hero,
            wants_emissive=wants_emissive,
            build_path=build_path,
            notes=notes,
            domain=domain or None,
        ),
        indent=2,
    )


@mcp.tool()
async def suggest_palette_for_material(ctx: Context,
                                        category: str,
                                        project_id: str = "",
                                        scene_id: str = "",
                                        hero: bool = False,
                                        wants_emissive: bool = False) -> str:
    """
    Suggest role colors + roughness for a material category from the active art bible.

    Roles: primary, secondary, shadow, highlight, dirt, accent, emissive, foam_or_edge.
    Use these values when setting exposed params after clone/recipe.
    """
    return json.dumps(
        _pkb.suggest_palette_for_material(
            category,
            project_id=project_id or None,
            scene_id=scene_id or None,
            hero=hero,
            wants_emissive=wants_emissive,
        ),
        indent=2,
    )


@mcp.tool()
async def validate_material_against_project(ctx: Context,
                                             proposed_colors_json: str,
                                             category: str = "",
                                             project_id: str = "",
                                             scene_id: str = "",
                                             material_id: str = "",
                                             wants_emissive: bool = False) -> str:
    """
    Validate proposed material colors against the project/scene ART BIBLE (look gate).

    This is the ship gate for color/feel — production domain compliance is separate.
    proposed_colors_json: role OR param name -> color
      e.g. '{"primary":[0.32,0.18,0.12],"dirt":"#29241C","highlight_color":[0.52,0.4,0.28]}'

    Returns status pass|warn|fail, issues[], fixes{}, ship_gate.may_register.
    MUST run before project_register_material. Never ship on fail.
    Fails on: hue outside bible window, emissive in non-emissive scene,
    dirt-language drift, category not in bible, etc.
    """
    try:
        colors = json.loads(proposed_colors_json) if isinstance(proposed_colors_json, str) else proposed_colors_json
    except Exception as exc:
        return json.dumps({"error": f"invalid proposed_colors_json: {exc}"})
    if not isinstance(colors, dict):
        return json.dumps({"error": "proposed_colors_json must be a JSON object"})
    return json.dumps(
        _pkb.validate_colors_against_project(
            colors,
            category=category,
            project_id=project_id or None,
            scene_id=scene_id or None,
            wants_emissive=wants_emissive,
            material_id=material_id,
        ),
        indent=2,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global _sd_port

    parser = argparse.ArgumentParser(description="Substance Designer MCP Bridge v2.0.0")
    parser.add_argument("--port", type=int, default=9881,  # BUG-B03 fix: default is 9881
                        help="TCP port to connect to the SD plugin (default: 9881)")
    args = parser.parse_args()
    _sd_port = args.port

    logger.info(f"SD MCP Bridge v2.0.0 -> SD plugin on port {_sd_port}")
    mcp.run()


if __name__ == "__main__":
    main()
