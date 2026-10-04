import ast
import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PLUGIN_SRC = ROOT / "plugin"
DEST = (
    Path.home()
    / "Documents"
    / "Adobe"
    / "Adobe Substance 3D Designer"
    / "python"
    / "sduserplugins"
    / "sd_mcp_plugin"
)

print(f"DEST exists={DEST.exists()} -> {DEST}", flush=True)
DEST.mkdir(parents=True, exist_ok=True)

for name in ("stylized_recipes.py", "recipes.py", "__init__.py"):
    src = PLUGIN_SRC / name
    dst = DEST / name
    shutil.copy2(src, dst)
    print(f"copied {name} ({src.stat().st_size} -> {dst})", flush=True)

for p in [
    PLUGIN_SRC / "stylized_recipes.py",
    PLUGIN_SRC / "recipes.py",
    PLUGIN_SRC / "__init__.py",
    ROOT / "server" / "sd_mcp_bridge.py",
]:
    ast.parse(p.read_text(encoding="utf-8"))
    print(f"AST OK {p.name}", flush=True)

spec = importlib.util.spec_from_file_location(
    "stylized_recipes", PLUGIN_SRC / "stylized_recipes.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
keys = m.list_stylized_recipe_keys()
print(f"unique stylized recipes={len(keys)}", flush=True)
print(keys, flush=True)
r = m.get_stylized_recipe("stylized_gold")
print(
    f"gold nodes={len(r['nodes'])} conns={len(r['connections'])} style={r.get('style')}",
    flush=True,
)
print("deployed files:", [p.name for p in DEST.iterdir()], flush=True)
print("DONE", flush=True)
