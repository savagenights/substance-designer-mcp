"""
project_kb.py — Level D: project art-bibles, scene coherence, design briefs.

Pure local logic (no SD TCP). Used by sd_mcp_bridge tools:
  project_list, project_get_art_bible, project_set_active, project_upsert,
  project_set_scene, project_register_material, stylized_design_concepts,
  stylized_design_brief, validate_material_against_project,
  suggest_palette_for_material, domain_list, domain_get, domain_get_section

Domain context files live in domains/ and supply production-scope rules
(e.g. stylized game materials for 3D models) that sit ABOVE Designer craft.
"""
from __future__ import annotations

import json
import os
import re
import colorsys
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_SERVER_DIR, ".."))
_PROJECTS_DIR = os.path.join(_ROOT, "knowledge", "projects")
_STYLIZED_DIR = os.path.join(_ROOT, "knowledge", "stylized")
_DOMAINS_DIR = os.path.join(_ROOT, "domains")
_STATE_PATH = os.path.join(_PROJECTS_DIR, "_active_state.json")
_INDEX_PATH = os.path.join(_PROJECTS_DIR, "_index.json")
_CONCEPTS_PATH = os.path.join(_STYLIZED_DIR, "design_concepts.md")

# Category → hue window key in project.hue_windows
_CATEGORY_HUE_KEY = {
    "stone_pavement": "stone",
    "stone_rock": "stone",
    "brick": "stone",
    "terracotta": "stone",
    "concrete": "stone",
    "marble": "stone",
    "terrazzo": "stone",
    "wood_planks": "wood",
    "wood_parquet": "wood",
    "wood_generic": "wood",
    "water": "water",
    "ground_grass": "vegetation",
    "ground_soil": "stone",
    "metal_iron": "metal_cool",
    "metal_generic": "metal_cool",
    "metal_silver": "metal_cool",
    "metal_aluminum": "metal_cool",
    "metal_gold": "heat_accent",
    "metal_copper": "heat_accent",
    "corrupted": "magic_accent",
    "scifi": "metal_cool",
    "crystal": "magic_accent",
    "lava": "heat_accent",
    "leather": "leather",
    "fabric_cloth": "wood",
    "fabric_carpet": "wood",
    "fabric_wool": "wood",
}

# Param name hints → color role
_PARAM_ROLE_HINTS = [
    (re.compile(r"emissive|lava_color|corruption_color|heat|glow", re.I), "emissive"),
    (re.compile(r"foam", re.I), "foam_or_edge"),
    (re.compile(r"dirt|grout|joint|mortar|interstice", re.I), "dirt"),
    (re.compile(r"shadow|cavity|ao_color", re.I), "shadow"),
    (re.compile(r"highlight|edge_color|top_edge|rim", re.I), "highlight"),
    (re.compile(r"moss|accent|second|secondary|variation|patina|rust|tarnish", re.I), "secondary"),
    (re.compile(r"obsidian|crust|base$|base_|stone_color|wood_color|water_color|color$|primary|bricks_color|cliff", re.I), "primary"),
]


# ---------------------------------------------------------------------------
# Color math
# ---------------------------------------------------------------------------
def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(x)))


def rgb_to_hex(rgb: List[float]) -> str:
    r, g, b = [_clamp(c) for c in rgb[:3]]
    return "#{:02X}{:02X}{:02X}".format(int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5))


def hex_to_rgb(h: str) -> List[float]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]


def rgb_to_hsv(rgb: List[float]) -> Tuple[float, float, float]:
    r, g, b = [_clamp(c) for c in rgb[:3]]
    return colorsys.rgb_to_hsv(r, g, b)


def hsv_to_rgb(h: float, s: float, v: float) -> List[float]:
    r, g, b = colorsys.hsv_to_rgb(_clamp(h), _clamp(s), _clamp(v))
    return [r, g, b]


def relative_luminance(rgb: List[float]) -> float:
    """sRGB relative luminance (approx)."""
    def lin(c: float) -> float:
        c = _clamp(c)
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb[:3]
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def saturation_hsv(rgb: List[float]) -> float:
    return rgb_to_hsv(rgb)[1]


def hue_hsv(rgb: List[float]) -> float:
    return rgb_to_hsv(rgb)[0]


def hue_distance(h1: float, h2: float) -> float:
    """Shortest distance on hue circle, both in [0,1]."""
    d = abs(h1 - h2) % 1.0
    return min(d, 1.0 - d)


def color_distance(a: List[float], b: List[float]) -> float:
    """Cheap perceptual-ish distance in RGB."""
    return (
        (a[0] - b[0]) ** 2 * 0.3
        + (a[1] - b[1]) ** 2 * 0.5
        + (a[2] - b[2]) ** 2 * 0.2
    ) ** 0.5


def ensure_rgb(val: Any) -> Optional[List[float]]:
    if val is None:
        return None
    if isinstance(val, str):
        if val.startswith("#"):
            return hex_to_rgb(val)
        return None
    if isinstance(val, (list, tuple)) and len(val) >= 3:
        return [_clamp(float(val[0])), _clamp(float(val[1])), _clamp(float(val[2]))]
    if isinstance(val, dict):
        if "rgb" in val:
            return ensure_rgb(val["rgb"])
        if "hex" in val:
            return ensure_rgb(val["hex"])
        if all(k in val for k in ("r", "g", "b")):
            return [_clamp(val["r"]), _clamp(val["g"]), _clamp(val["b"])]
    return None


# ---------------------------------------------------------------------------
# FS helpers
# ---------------------------------------------------------------------------
def _read_json(path: str, default: Any = None) -> Any:
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Active state
# ---------------------------------------------------------------------------
def get_active_state() -> Dict[str, Any]:
    st = _read_json(_STATE_PATH, {}) or {}
    return {
        "project_id": st.get("project_id") or "fabl_forge",
        "scene_id": st.get("scene_id") or "keep_courtyard_overcast",
        "updated": st.get("updated"),
    }


def set_active_state(project_id: Optional[str] = None, scene_id: Optional[str] = None) -> Dict[str, Any]:
    st = get_active_state()
    if project_id:
        st["project_id"] = project_id
    if scene_id:
        st["scene_id"] = scene_id
    st["updated"] = _now()
    _write_json(_STATE_PATH, st)
    return st


# ---------------------------------------------------------------------------
# Project / scene load
# ---------------------------------------------------------------------------
def list_projects() -> Dict[str, Any]:
    idx = _read_json(_INDEX_PATH, {"version": 1, "projects": {}}) or {}
    active = get_active_state()
    rows = []
    for pid, meta in (idx.get("projects") or {}).items():
        ppath = os.path.join(_PROJECTS_DIR, meta.get("path") or f"{pid}/project.json")
        proj = _read_json(ppath, {}) or {}
        scenes_dir = os.path.join(_PROJECTS_DIR, pid, "scenes")
        scenes = []
        if os.path.isdir(scenes_dir):
            scenes = sorted(
                f[:-5] for f in os.listdir(scenes_dir) if f.endswith(".json")
            )
        rows.append(
            {
                "id": pid,
                "title": proj.get("title") or meta.get("title") or pid,
                "default_scene": proj.get("default_scene") or meta.get("default_scene"),
                "tags": meta.get("tags") or [],
                "scenes": scenes,
                "harmony_mode": proj.get("harmony_mode"),
                "is_active": pid == active.get("project_id"),
            }
        )
    return {"active": active, "projects": rows, "projects_dir": _PROJECTS_DIR}


def _project_dir(project_id: str) -> str:
    return os.path.join(_PROJECTS_DIR, project_id)


def _project_path(project_id: str) -> str:
    return os.path.join(_project_dir(project_id), "project.json")


def _scene_path(project_id: str, scene_id: str) -> str:
    return os.path.join(_project_dir(project_id), "scenes", f"{scene_id}.json")


def load_project(project_id: str) -> Dict[str, Any]:
    path = _project_path(project_id)
    data = _read_json(path)
    if not data:
        return {"error": f"project not found: {project_id}", "path": path}
    data["_path"] = path
    return data


def load_scene(project_id: str, scene_id: str) -> Dict[str, Any]:
    path = _scene_path(project_id, scene_id)
    data = _read_json(path)
    if not data:
        return {"error": f"scene not found: {project_id}/{scene_id}", "path": path}
    data["_path"] = path
    return data


def get_art_bible(project_id: Optional[str] = None, scene_id: Optional[str] = None) -> Dict[str, Any]:
    active = get_active_state()
    pid = project_id or active["project_id"]
    sid = scene_id or active["scene_id"]
    proj = load_project(pid)
    if proj.get("error"):
        return proj
    scene = load_scene(pid, sid) if sid else {}
    if scene.get("error"):
        # fall back to default scene
        sid = proj.get("default_scene") or ""
        scene = load_scene(pid, sid) if sid else {}
    return {
        "project_id": pid,
        "scene_id": scene.get("id") or sid,
        "project": {k: v for k, v in proj.items() if not k.startswith("_")},
        "scene": {k: v for k, v in (scene or {}).items() if not k.startswith("_")},
        "merged_guidance": _merge_guidance(proj, scene if not scene.get("error") else {}),
        "active": active,
    }


def _merge_palette_role(project_swatches: Any, scene_swatches: Any) -> List[Any]:
    """Scene swatches win on same name, but NEVER wipe the master role list.

    Old bug: scene local_palette.primary = [courtyard_stone] replaced the entire
    master primary list, so leather/water/wood briefs could only see greystone.
    """
    base = list(project_swatches or []) if isinstance(project_swatches, list) else []
    local = list(scene_swatches or []) if isinstance(scene_swatches, list) else []
    if not local:
        return base
    if not base:
        return local

    def _name(s: Any) -> str:
        if isinstance(s, dict):
            return (s.get("name") or "").strip().lower()
        return ""

    scene_names = {_name(s) for s in local if _name(s)}
    kept = [s for s in base if _name(s) not in scene_names]
    # scene first (priority for generic picks), then remaining master swatches
    return list(local) + kept


def _merge_guidance(project: Dict[str, Any], scene: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the rules an agent should obey right now.

    LOOK authority = project art bible + scene mood/palette.
    Domain context is production scope only — never a color source.
    """
    master = deepcopy(project.get("master_palette") or {})
    local = (scene or {}).get("local_palette") or {}
    palette: Dict[str, Any] = {}
    roles = set(list(master.keys()) + list(local.keys()))
    for role in roles:
        palette[role] = _merge_palette_role(master.get(role), local.get(role))

    dna = deepcopy(project.get("style_dna") or {})
    # scene may override DNA strands
    for k in (
        "shape_language",
        "detail_density",
        "wear_philosophy",
        "albedo_lighting_policy",
        "frequency_policy",
        "scale_notes",
    ):
        if (scene or {}).get(k) is not None:
            dna[k] = scene[k]

    families = deepcopy(project.get("material_families") or {})

    return {
        "harmony_mode": (scene or {}).get("harmony_mode_override") or project.get("harmony_mode"),
        "white_balance": (scene or {}).get("white_balance_bias") or project.get("white_balance"),
        "shadow_temperature": project.get("shadow_temperature"),
        "key_light_temperature": project.get("key_light_temperature"),
        "saturation_budget": project.get("saturation_budget"),
        "saturation_scale": (scene or {}).get("saturation_scale", 1.0),
        "value_range": project.get("value_range") or {"min": 0.02, "max": 0.98},
        "value_lift": (scene or {}).get("value_lift", 0.0),
        "wetness": (scene or {}).get("wetness", 0.0),
        "dust": (scene or {}).get("dust", 0.0),
        "emissive_allowed": (scene or {}).get("emissive_allowed", project.get("emissive_policy") != "restricted"),
        "emissive_policy": project.get("emissive_policy"),
        "accent_surface_ratio_max": project.get("accent_surface_ratio_max", 0.15),
        "hue_windows": project.get("hue_windows") or {},
        "roughness_guidance": project.get("roughness_guidance") or {},
        "roughness_bias": (scene or {}).get("roughness_bias") or {},
        "palette": palette,
        "master_palette": master,
        "scene_local_palette": local,
        "art_pillars": project.get("art_pillars") or [],
        "style_dna": dna,
        "shape_language": dna.get("shape_language") or project.get("shape_language") or "readable_stylized",
        "detail_density": dna.get("detail_density") or "fewer_and_larger",
        "wear_philosophy": dna.get("wear_philosophy") or "contact_logical",
        "albedo_lighting_policy": dna.get("albedo_lighting_policy") or "soft_baked_cues_ok",
        "frequency_policy": dna.get("frequency_policy") or {
            "low": "required_structure",
            "mid": "sculpt_and_wear",
            "high": "restrained",
        },
        "material_families": families,
        "mood_tags": (scene or {}).get("mood_tags") or [],
        "camera_notes": (scene or {}).get("camera_notes"),
        "time_of_day": (scene or {}).get("time_of_day"),
        "weather": (scene or {}).get("weather"),
        "biome": (scene or {}).get("biome"),
        "do": list(project.get("do") or []) + list((scene or {}).get("do") or []),
        "dont": list(project.get("dont") or []) + list((scene or {}).get("dont") or []),
        "preferred_categories": (scene or {}).get("preferred_categories")
        or project.get("allowed_categories")
        or [],
        "allowed_categories": project.get("allowed_categories") or [],
        "hero_accent_allowed": (scene or {}).get("hero_accent_allowed") or [],
        "ensemble": (scene or {}).get("ensemble") or [],
        "core_hue_count_target": project.get("core_hue_count_target") or 4,
        "test_together_required": project.get("test_together_required", True),
        "look_rule": (
            "Art bible + active scene decide color/feel/mood. "
            "Production domain decides pipeline rules only. "
            "Reference donors are topology only — never final grade."
        ),
    }


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------
def upsert_project(project_id: str, patch: Dict[str, Any], create_if_missing: bool = True) -> Dict[str, Any]:
    path = _project_path(project_id)
    existing = _read_json(path, None)
    if existing is None:
        if not create_if_missing:
            return {"error": f"project missing: {project_id}"}
        existing = {
            "id": project_id,
            "title": patch.get("title") or project_id,
            "version": 1,
            "art_pillars": [],
            "harmony_mode": "analogous",
            "master_palette": {},
            "hue_windows": {},
            "do": [],
            "dont": [],
            "default_scene": patch.get("default_scene") or "main",
        }
    # shallow+dict merge
    for k, v in (patch or {}).items():
        if k in ("master_palette", "hue_windows", "roughness_guidance") and isinstance(v, dict):
            base = existing.get(k) or {}
            base.update(v)
            existing[k] = base
        else:
            existing[k] = v
    existing["id"] = project_id
    existing["updated"] = _now()
    _write_json(path, existing)

    # index
    idx = _read_json(_INDEX_PATH, {"version": 1, "projects": {}}) or {"version": 1, "projects": {}}
    idx.setdefault("projects", {})[project_id] = {
        "title": existing.get("title") or project_id,
        "path": f"{project_id}/project.json",
        "default_scene": existing.get("default_scene"),
        "tags": existing.get("tags") or idx.get("projects", {}).get(project_id, {}).get("tags") or [],
    }
    _write_json(_INDEX_PATH, idx)

    # ensure default scene shell
    sid = existing.get("default_scene") or "main"
    sp = _scene_path(project_id, sid)
    if not os.path.isfile(sp):
        _write_json(
            sp,
            {
                "id": sid,
                "project_id": project_id,
                "title": sid.replace("_", " ").title(),
                "mood_tags": [],
                "local_palette": {},
                "ensemble": [],
                "emissive_allowed": existing.get("emissive_policy") != "restricted",
            },
        )
    return {"ok": True, "project": existing, "path": path}


def upsert_scene(project_id: str, scene_id: str, patch: Dict[str, Any], create_if_missing: bool = True) -> Dict[str, Any]:
    if load_project(project_id).get("error"):
        return {"error": f"project not found: {project_id}"}
    path = _scene_path(project_id, scene_id)
    existing = _read_json(path, None)
    if existing is None:
        if not create_if_missing:
            return {"error": f"scene missing: {scene_id}"}
        existing = {
            "id": scene_id,
            "project_id": project_id,
            "title": scene_id.replace("_", " ").title(),
            "mood_tags": [],
            "local_palette": {},
            "ensemble": [],
        }
    for k, v in (patch or {}).items():
        if k == "local_palette" and isinstance(v, dict):
            base = existing.get("local_palette") or {}
            base.update(v)
            existing["local_palette"] = base
        elif k == "ensemble" and isinstance(v, list):
            existing["ensemble"] = v
        else:
            existing[k] = v
    existing["id"] = scene_id
    existing["project_id"] = project_id
    existing["updated"] = _now()
    _write_json(path, existing)
    return {"ok": True, "scene": existing, "path": path}


def register_material(
    project_id: str,
    scene_id: str,
    material_id: str,
    *,
    category: str = "",
    path: str = "",
    roles: Optional[Dict[str, Any]] = None,
    status: str = "approved",
    notes: str = "",
    add_to_ensemble: bool = True,
) -> Dict[str, Any]:
    roles_rgb: Dict[str, List[float]] = {}
    for rk, rv in (roles or {}).items():
        rgb = ensure_rgb(rv)
        if rgb:
            roles_rgb[rk] = [round(c, 4) for c in rgb]

    entry = {
        "material_id": material_id,
        "project_id": project_id,
        "scene_id": scene_id,
        "category": category,
        "path": path,
        "roles": roles_rgb,
        "status": status,
        "notes": notes,
        "registered_at": _now(),
    }

    log_path = os.path.join(_project_dir(project_id), "materials_log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    scene_result = None
    if add_to_ensemble:
        scene = load_scene(project_id, scene_id)
        if not scene.get("error"):
            ens = list(scene.get("ensemble") or [])
            ens = [e for e in ens if e.get("material_id") != material_id]
            ens.append(
                {
                    "material_id": material_id,
                    "path": path,
                    "category": category,
                    "roles": roles_rgb,
                    "notes": notes,
                }
            )
            scene_result = upsert_scene(project_id, scene_id, {"ensemble": ens})

    return {"ok": True, "entry": entry, "log_path": log_path, "scene_update": scene_result}


# ---------------------------------------------------------------------------
# Markdown helpers (shared by design concepts + domains)
# ---------------------------------------------------------------------------
def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _slice_markdown_section(text: str, section: str = "", max_chars: int = 40000) -> str:
    """Return full text or heading-bounded slices matching `section` (case-insensitive).

    Prefer heading matches. Body-only matches are a fallback so short queries still work,
    but a single incidental word in a paragraph won't steal the wrong chapter.
    """
    sec = (section or "").strip().lower()
    if not sec:
        return text if len(text) < max_chars else text[:max_chars] + "\n\n...[truncated]..."

    heading_chunks: List[str] = []
    body_chunks: List[str] = []
    current: List[str] = []
    head_hit = False
    body_hit = False

    def _flush() -> None:
        nonlocal current, head_hit, body_hit
        if not current:
            return
        block = "\n".join(current)
        if head_hit:
            heading_chunks.append(block)
        elif body_hit:
            body_chunks.append(block)
        current = []
        head_hit = False
        body_hit = False

    for line in text.splitlines():
        if line.startswith("#"):
            _flush()
            current = [line]
            head_hit = sec in line.lower()
            body_hit = False
        else:
            current.append(line)
            if sec in line.lower():
                body_hit = True
    _flush()

    chunks = heading_chunks or body_chunks
    if not chunks:
        lines = [ln for ln in text.splitlines() if sec in ln.lower()]
        return "\n".join(lines[:100]) if lines else f"No section matched '{section}'."
    return "\n\n".join(chunks)[:max_chars]


def _extract_bullets_under_heading(text: str, heading_substr: str, limit: int = 12) -> List[str]:
    """Grab `- ` / `* ` bullets under the first heading OR bold label containing heading_substr.

    Supports both:
      ## Constraints & Non-Negotiables
      - bullet

    and nested labels inside a section:
      **In scope:**
      - bullet
    """
    needle = (heading_substr or "").lower()
    if not needle:
        return []
    lines = text.splitlines()
    capturing = False
    bullets: List[str] = []
    started_at_heading = False

    def _is_label(s: str) -> bool:
        # **In scope:** or **Explicitly out of scope:**
        t = s.strip()
        return t.startswith("**") and t.endswith(":**")

    for line in lines:
        stripped = line.strip()
        if line.startswith("#"):
            if capturing and started_at_heading:
                break
            if capturing and not started_at_heading:
                # hit a real heading after a bold-label capture → stop
                break
            capturing = needle in line.lower()
            started_at_heading = capturing
            continue
        if _is_label(stripped):
            label_txt = stripped.strip("*").rstrip(":").strip().lower()
            if capturing and not started_at_heading:
                # next bold label ends previous label block
                break
            if needle in label_txt:
                capturing = True
                started_at_heading = False
                continue
            if capturing and started_at_heading:
                # inside a ## section; a non-matching label doesn't end the section
                pass
            continue
        if not capturing:
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullets.append(stripped[2:].strip())
            if len(bullets) >= limit:
                break
    return bullets


def _extract_meta_table(text: str) -> Dict[str, str]:
    """Parse simple markdown pipe tables near the top for Domain meta fields."""
    meta: Dict[str, str] = {}
    for line in text.splitlines()[:80]:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        key, val = cells[0], cells[1]
        if not key or key.startswith("-") or key.lower() in ("field", "---"):
            continue
        if val.startswith("-"):
            continue
        meta[key.lower().replace(" ", "_")] = val
    return meta


# ---------------------------------------------------------------------------
# Design concepts
# ---------------------------------------------------------------------------
def load_design_concepts(section: str = "") -> str:
    if not os.path.isfile(_CONCEPTS_PATH):
        return "design_concepts.md missing"
    return _slice_markdown_section(_read_text(_CONCEPTS_PATH), section)


# ---------------------------------------------------------------------------
# Production domains (domains/*.md) — fully dynamic discovery
# Drop any domains/<snake_id>.md and it is live on next list/get/brief.
# Optional Meta table fields drive routing (no Python edits required):
#   Id | Aliases | Categories | Category prefixes | Default | Agent checklist heading
# ---------------------------------------------------------------------------
_TRUTHY = {"1", "true", "yes", "y", "on", "default"}


def _domain_id_from_filename(filename: str) -> str:
    base = os.path.splitext(os.path.basename(filename))[0]
    return re.sub(r"[^a-z0-9_]+", "_", base.lower()).strip("_")


def _split_meta_list(raw: Optional[str]) -> List[str]:
    """Split comma/semicolon/pipe/newline lists from a meta table cell."""
    if not raw:
        return []
    parts = re.split(r"[,;|\n]+", str(raw))
    out: List[str] = []
    seen = set()
    for p in parts:
        s = p.strip().lower()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _meta_flag(meta: Dict[str, str], *keys: str) -> bool:
    for k in keys:
        val = (meta.get(k) or "").strip().lower()
        if val in _TRUTHY:
            return True
    return False


def _slugify_alias(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


def _domain_aliases(domain_id: str, meta: Dict[str, str], title: str) -> List[str]:
    """Aliases = id + title forms + optional Meta `Aliases` list. No hardcoded domain names."""
    aliases = {domain_id}
    name = (meta.get("domain_name") or title or "").strip()
    if name:
        aliases.add(name.lower())
        slug = _slugify_alias(name)
        if slug:
            aliases.add(slug)
        # first 2-4 significant words as a short alias (e.g. "stylized materials")
        words = [w for w in re.split(r"[^a-z0-9]+", name.lower()) if w and w not in {
            "for", "and", "the", "of", "a", "an", "to", "in", "on", "3d", "application", "development"
        }]
        if len(words) >= 2:
            aliases.add(" ".join(words[:2]))
            aliases.add("_".join(words[:2]))
        if len(words) >= 3:
            aliases.add(" ".join(words[:3]))
            aliases.add("_".join(words[:3]))
    for key in ("aliases", "alias", "also_known_as", "aka"):
        for a in _split_meta_list(meta.get(key)):
            aliases.add(a)
            slug = _slugify_alias(a)
            if slug:
                aliases.add(slug)
    # optional explicit id override already counted via domain_id
    return sorted(a for a in aliases if a)


def _domain_categories(meta: Dict[str, str]) -> List[str]:
    cats: List[str] = []
    for key in ("categories", "category", "material_categories", "applies_to_categories"):
        cats.extend(_split_meta_list(meta.get(key)))
    # de-dupe preserve order
    seen = set()
    out = []
    for c in cats:
        c2 = c.replace(" ", "_")
        if c2 and c2 not in seen:
            seen.add(c2)
            out.append(c2)
    return out


def _domain_category_prefixes(meta: Dict[str, str]) -> List[str]:
    prefs: List[str] = []
    for key in ("category_prefixes", "category_prefix", "prefixes"):
        prefs.extend(_split_meta_list(meta.get(key)))
    return [p.replace(" ", "_") for p in prefs if p]


def _parse_domain_file(path: str) -> Optional[Dict[str, Any]]:
    """Parse one domains/*.md into a registry record. Returns None if unreadable."""
    try:
        text = _read_text(path)
        mtime = os.path.getmtime(path)
    except OSError:
        return None
    name = os.path.basename(path)
    meta = _extract_meta_table(text)
    title_line = next(
        (ln.lstrip("# ").strip() for ln in text.splitlines() if ln.startswith("# ")),
        name,
    )
    # Meta Id overrides filename stem when present
    file_id = _domain_id_from_filename(name)
    meta_id = _slugify_alias(meta.get("id") or meta.get("domain_id") or "")
    domain_id = meta_id or file_id
    is_default = _meta_flag(meta, "default", "is_default", "default_domain")
    return {
        "id": domain_id,
        "file": name,
        "path": path,
        "title": meta.get("domain_name") or title_line,
        "version": meta.get("version"),
        "last_verified": meta.get("last_verified"),
        "owner": meta.get("owner"),
        "aliases": _domain_aliases(domain_id, meta, title_line),
        "categories": _domain_categories(meta),
        "category_prefixes": _domain_category_prefixes(meta),
        "is_default": is_default,
        "chars": len(text),
        "mtime": mtime,
        "meta": meta,
        "_text": text,  # internal; stripped before public list_domains return
    }


def _discover_domain_files() -> List[str]:
    """All domain markdown paths under domains/ (non-recursive, skip README)."""
    if not os.path.isdir(_DOMAINS_DIR):
        return []
    paths: List[str] = []
    try:
        names = os.listdir(_DOMAINS_DIR)
    except OSError:
        return []
    for name in sorted(names):
        if not name.lower().endswith(".md"):
            continue
        if name.upper().startswith("README"):
            continue
        if name.startswith("."):
            continue
        paths.append(os.path.join(_DOMAINS_DIR, name))
    return paths


def _scan_domains(include_text: bool = False) -> Dict[str, Any]:
    """
    Live filesystem scan of domains/*.md.

    No static registry. New/renamed/deleted .md files are visible on the next call.
    """
    records: List[Dict[str, Any]] = []
    for path in _discover_domain_files():
        rec = _parse_domain_file(path)
        if not rec:
            continue
        if not include_text:
            rec = {k: v for k, v in rec.items() if k != "_text"}
        records.append(rec)

    # category → domain_id (first declared wins; later domains can still be explicit)
    category_map: Dict[str, str] = {}
    prefix_map: List[Tuple[str, str]] = []  # (prefix, domain_id)
    defaults: List[str] = []
    for rec in records:
        for cat in rec.get("categories") or []:
            category_map.setdefault(cat, rec["id"])
        for pref in rec.get("category_prefixes") or []:
            prefix_map.append((pref, rec["id"]))
        if rec.get("is_default"):
            defaults.append(rec["id"])

    # default = explicit Default:yes, else sole domain, else first by filename
    if defaults:
        default_id = defaults[0]
    elif len(records) == 1:
        default_id = records[0]["id"]
    elif records:
        default_id = records[0]["id"]
    else:
        default_id = ""

    return {
        "ok": bool(records) or os.path.isdir(_DOMAINS_DIR),
        "domains_dir": _DOMAINS_DIR,
        "count": len(records),
        "domains": records,
        "default_domain_id": default_id,
        "category_map": category_map,
        "category_prefixes": prefix_map,
        "authority": (
            "Project Style Guide/Art Bible > Domain Context > "
            "Designer craft concepts (design_concepts.md) > general realtime practice"
        ),
        "discovery": "live_filesystem",
        "hint": (
            "Add domains/<snake_id>.md — auto-discovered. "
            "Optional Meta: Aliases, Categories, Category prefixes, Default=yes"
        ),
    }


def list_domains() -> Dict[str, Any]:
    """Inventory of production domain context files under domains/ (live scan)."""
    scan = _scan_domains(include_text=False)
    if not os.path.isdir(_DOMAINS_DIR):
        return {
            "ok": False,
            "error": f"domains dir missing: {_DOMAINS_DIR}",
            "domains_dir": _DOMAINS_DIR,
            "domains": [],
            "count": 0,
            "default_domain_id": "",
            "category_map": {},
            "discovery": "live_filesystem",
        }
    # public payload — drop internal-only noise from each record
    public_domains = []
    for d in scan.get("domains") or []:
        public_domains.append({
            "id": d["id"],
            "file": d["file"],
            "path": d["path"],
            "title": d["title"],
            "version": d.get("version"),
            "last_verified": d.get("last_verified"),
            "owner": d.get("owner"),
            "aliases": d.get("aliases") or [],
            "categories": d.get("categories") or [],
            "category_prefixes": d.get("category_prefixes") or [],
            "is_default": bool(d.get("is_default")),
            "chars": d.get("chars"),
            "mtime": d.get("mtime"),
        })
    return {
        "ok": True,
        "domains_dir": scan["domains_dir"],
        "count": len(public_domains),
        "domains": public_domains,
        "default_domain_id": scan.get("default_domain_id") or "",
        "category_map": scan.get("category_map") or {},
        "authority": scan.get("authority"),
        "discovery": "live_filesystem",
        "hint": scan.get("hint"),
    }


def get_default_domain_id() -> str:
    """Live default domain id (Default:yes meta, else sole/first discovered file)."""
    return (_scan_domains(include_text=False).get("default_domain_id") or "").strip()


def resolve_domain_id(domain: Optional[str] = None, category: str = "") -> str:
    """
    Resolve a domain id from explicit name/alias or material category.

    Resolution order:
      1. explicit domain id / alias / title substring (against live scan)
      2. exact category match from domain Meta `Categories`
      3. category prefix match from Meta `Category prefixes`
      4. live default domain (Default:yes / sole file / first file)
    """
    scan = _scan_domains(include_text=False)
    known = scan.get("domains") or []
    explicit = (domain or "").strip().lower()

    if explicit:
        explicit_slug = _slugify_alias(explicit)
        for d in known:
            aliases = [a.lower() for a in (d.get("aliases") or [])]
            if explicit == d["id"] or explicit_slug == d["id"]:
                return d["id"]
            if explicit in aliases or explicit_slug in aliases:
                return d["id"]
            title = (d.get("title") or "").lower()
            if explicit and explicit in title:
                return d["id"]
        # unknown explicit still normalized — load_domain will 404 with available list
        return explicit_slug or explicit

    cat = (category or "").lower().strip().replace(" ", "_")
    if cat:
        cmap = scan.get("category_map") or {}
        if cat in cmap:
            return cmap[cat]
        # prefix match (longest prefix wins)
        best_id = ""
        best_len = -1
        for pref, did in scan.get("category_prefixes") or []:
            if cat == pref or cat.startswith(pref.rstrip("_") + "_") or cat.startswith(pref):
                if len(pref) > best_len:
                    best_len = len(pref)
                    best_id = did
        if best_id:
            return best_id

    return (scan.get("default_domain_id") or "").strip()


def _build_agent_checklist(text: str, non_negotiables: List[str], success: List[str]) -> List[str]:
    """Prefer domain-authored checklist; else compress non-negotiables / success criteria."""
    for heading in (
        "Agent checklist",
        "AI Assistant checklist",
        "Agent habit",
        "Pre-ship checklist",
        "Standard Workflows",
    ):
        bullets = _extract_bullets_under_heading(text, heading, limit=12)
        if bullets:
            return bullets
    # fall back: non-negotiables are the real law; keep them short
    if non_negotiables:
        return non_negotiables[:10]
    if success:
        return success[:10]
    return [
        "Confirm project art style before inventing a new material",
        "Stay inside domain scope and non-negotiables (domain_get)",
        "Prefer reuse / variants over unique one-offs when the domain says so",
        "Validate under project lighting / real use conditions, not beauty sphere only",
        "Flag requests that break readability, consistency, or technical budgets",
    ]


def load_domain(domain: Optional[str] = None, section: str = "", category: str = "") -> Dict[str, Any]:
    """
    Load a production domain context markdown (+ optional section slice).

    Fully dynamic: resolves against a live scan of domains/*.md.
    Domains do NOT replace project art-bibles (look) or design_concepts.md (craft).
    """
    scan = _scan_domains(include_text=True)
    domain_id = resolve_domain_id(domain, category=category)
    if not domain_id:
        return {
            "ok": False,
            "error": "no domains discovered and none requested",
            "domain_id": "",
            "available": [],
            "hint": f"Add a markdown file under { _DOMAINS_DIR }",
        }

    match = next((d for d in (scan.get("domains") or []) if d["id"] == domain_id), None)
    if not match:
        # path fallback if id is a fresh filename stem not yet inconsistent
        path_guess = os.path.join(_DOMAINS_DIR, f"{domain_id}.md")
        if os.path.isfile(path_guess):
            match = _parse_domain_file(path_guess)
        if not match:
            available = [d["id"] for d in (scan.get("domains") or [])]
            return {
                "ok": False,
                "error": f"domain not found: {domain_id}",
                "domain_id": domain_id,
                "available": available,
                "hint": "Add domains/<id>.md or pass a known domain id/alias from domain_list",
            }

    path = match["path"]
    text = match.get("_text") or _read_text(path)
    meta = match.get("meta") or _extract_meta_table(text)
    title_line = match.get("title") or domain_id
    body = _slice_markdown_section(text, section)

    non_negotiables = _extract_bullets_under_heading(text, "Constraints & Non-Negotiables", limit=14)
    if not non_negotiables:
        non_negotiables = _extract_bullets_under_heading(text, "Non-Negotiables", limit=14)
    success = _extract_bullets_under_heading(text, "Success Criteria", limit=12)
    in_scope = _extract_bullets_under_heading(text, "In scope", limit=12)
    out_scope = _extract_bullets_under_heading(text, "Explicitly out of scope", limit=10)
    if not out_scope:
        out_scope = _extract_bullets_under_heading(text, "out of scope", limit=10)
    agent_checklist = _build_agent_checklist(text, non_negotiables, success)

    return {
        "ok": True,
        "domain_id": match["id"],
        "path": path,
        "title": meta.get("domain_name") or title_line,
        "version": meta.get("version"),
        "last_verified": meta.get("last_verified"),
        "owner": meta.get("owner"),
        "section": section or None,
        "meta": meta,
        "aliases": match.get("aliases") or _domain_aliases(match["id"], meta, title_line),
        "categories": match.get("categories") or _domain_categories(meta),
        "category_prefixes": match.get("category_prefixes") or _domain_category_prefixes(meta),
        "is_default": bool(match.get("is_default")),
        "authority_stack": [
            "Project Style Guide / Art Bible (knowledge/projects) — primary LOOK",
            f"Domain Context ({match['id']}) — production scope, reuse, validation contract",
            "design_concepts.md — Designer D1 authoring + D2 ensemble craft",
            "Realtime best practices — secondary technical limits",
        ],
        "in_scope": in_scope,
        "out_of_scope": out_scope,
        "non_negotiables": non_negotiables,
        "success_criteria": success,
        "agent_checklist": agent_checklist,
        "content": body,
        "content_chars": len(body),
        "discovery": "live_filesystem",
    }


def domain_guidance_for_brief(
    category: str = "",
    domain: Optional[str] = None,
    max_excerpt_chars: int = 1800,
) -> Dict[str, Any]:
    """Compact domain payload embedded into stylized_design_brief (live resolve)."""
    loaded = load_domain(domain=domain, category=category, section="")
    if not loaded.get("ok"):
        return loaded
    # Prefer constraints + workflows slices for the excerpt (actionable)
    constraints = load_domain(domain=loaded["domain_id"], section="constraint")
    workflows = load_domain(domain=loaded["domain_id"], section="workflow")
    excerpt_parts: List[str] = []
    for block in (constraints, workflows):
        if block.get("ok") and block.get("content") and "No section matched" not in block["content"]:
            excerpt_parts.append(block["content"].strip())
    excerpt = "\n\n".join(excerpt_parts).strip()
    if not excerpt:
        excerpt = (loaded.get("content") or "")[:max_excerpt_chars]
    if len(excerpt) > max_excerpt_chars:
        excerpt = excerpt[:max_excerpt_chars] + "\n..."

    return {
        "ok": True,
        "domain_id": loaded["domain_id"],
        "title": loaded.get("title"),
        "version": loaded.get("version"),
        "path": loaded.get("path"),
        "is_default": loaded.get("is_default"),
        "categories": loaded.get("categories") or [],
        "authority_stack": loaded.get("authority_stack"),
        "non_negotiables": loaded.get("non_negotiables") or [],
        "success_criteria": (loaded.get("success_criteria") or [])[:8],
        "agent_checklist": loaded.get("agent_checklist") or [],
        "in_scope_sample": (loaded.get("in_scope") or [])[:6],
        "out_of_scope_sample": (loaded.get("out_of_scope") or [])[:5],
        "excerpt": excerpt,
        "discovery": "live_filesystem",
        "tools": {
            "list": "domain_list",
            "get": "domain_get",
            "section": "domain_get_section",
        },
    }


# ---------------------------------------------------------------------------
# Palette suggestion + validation
# ---------------------------------------------------------------------------
def _palette_swatches(guidance: Dict[str, Any], role: str) -> List[Dict[str, Any]]:
    pal = guidance.get("palette") or {}
    out = []
    for s in pal.get(role) or []:
        if isinstance(s, dict):
            rgb = ensure_rgb(s)
            if rgb:
                out.append({"name": s.get("name"), "rgb": rgb, "hex": s.get("hex") or rgb_to_hex(rgb)})
        else:
            rgb = ensure_rgb(s)
            if rgb:
                out.append({"name": None, "rgb": rgb, "hex": rgb_to_hex(rgb)})
    return out


def _nearest_swatch(rgb: List[float], swatches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not swatches:
        return None
    best = None
    best_d = 1e9
    for s in swatches:
        d = color_distance(rgb, s["rgb"])
        if d < best_d:
            best_d = d
            best = {**s, "distance": round(d, 4)}
    return best


def infer_param_role(param_name: str) -> str:
    for rx, role in _PARAM_ROLE_HINTS:
        if rx.search(param_name or ""):
            return role
    return "primary"


def _swatch_matches_category(sw: Dict[str, Any], cat: str, hue_key: str, window: Dict[str, Any]) -> float:
    """Higher score = better swatch for this category."""
    name = (sw.get("name") or "").lower()
    rgb = sw.get("rgb") or [0, 0, 0]
    h, s, v = rgb_to_hsv(rgb)
    score = 0.0

    # name keywords
    cat_keywords = {
        "water": ["ocean", "water", "sea", "abyss", "foam"],
        "stone_pavement": ["stone", "keep", "courtyard", "cobble", "limestone", "mortar", "dirt"],
        "stone_rock": ["stone", "cliff", "rock", "basalt", "soot", "wet_cliff", "obsidian"],
        "brick": ["brick", "stone", "clay"],
        "wood_planks": ["timber", "wood", "plank", "oak"],
        "wood_parquet": ["timber", "wood"],
        "metal_iron": ["iron", "metal", "soot"],
        "metal_gold": ["gold", "ember", "heat"],
        "metal_copper": ["copper", "patina"],
        "ground_grass": ["moss", "grass", "vegetation"],
        "ground_soil": ["dirt", "soil", "ash"],
        "leather": ["leather", "hide", "worn", "strap", "belt"],
        "fabric_cloth": ["cloth", "fabric", "banner", "sail", "textile"],
    }
    for kw in cat_keywords.get(cat, [hue_key]):
        if kw in name:
            score += 3.0

    # reject obvious cross-family names for body roles later
    anti = {
        "water": ["timber", "iron", "lava", "banner"],
        "stone_pavement": ["ocean", "lava", "foam", "kelp", "leather"],
        "stone_rock": ["ocean", "foam", "timber", "banner", "leather"],
        "wood_planks": ["ocean", "lava", "iron"],
        "metal_iron": ["ocean", "moss", "timber"],
        "leather": ["ocean", "stone", "courtyard", "moss", "lava", "iron", "foam"],
    }
    for kw in anti.get(cat, []):
        if kw in name:
            score -= 4.0

    # hue window membership
    if window and s > 0.06:
        center = float(window.get("center", 0))
        width = float(window.get("width", 0.5))
        dist = hue_distance(h, center)
        if dist <= width:
            score += 2.0 * (1.0 - dist / max(width, 1e-6))
        else:
            score -= 2.0

    # water likes deeper values for primary-ish darks
    if cat == "water" and v < 0.35:
        score += 1.0
    return score


def _family_for_category(g: Dict[str, Any], category: str) -> Dict[str, Any]:
    families = g.get("material_families") or {}
    cat = (category or "").lower().strip()
    if cat in families and isinstance(families[cat], dict):
        return families[cat]
    # prefix soft match (metal_iron → metal family if present)
    for key, fam in families.items():
        if cat.startswith(str(key).lower()) or str(key).lower() in cat:
            if isinstance(fam, dict):
                return fam
    return {}


def _ensemble_role_colors(g: Dict[str, Any], category: str) -> Dict[str, List[float]]:
    """Pull role colors from same-category ensemble entries (scene memory)."""
    cat = (category or "").lower().strip()
    out: Dict[str, List[float]] = {}
    for e in reversed(list(g.get("ensemble") or [])):
        if (e.get("category") or "").lower().strip() != cat:
            continue
        roles = e.get("roles") or {}
        for role, raw in roles.items():
            if role in out:
                continue
            rgb = ensure_rgb(raw)
            if rgb:
                out[role] = rgb
        if out:
            break
    return out


def suggest_palette_for_material(
    category: str,
    *,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    hero: bool = False,
    wants_emissive: bool = False,
) -> Dict[str, Any]:
    """Suggest role colors STRICTLY from the active art bible + scene palette.

    Domain context is not consulted. Donor defaults are not consulted.
    """
    bible = get_art_bible(project_id, scene_id)
    if bible.get("error"):
        return bible
    g = bible["merged_guidance"]
    cat = (category or "").lower().strip()
    hue_key = _CATEGORY_HUE_KEY.get(cat, "stone")
    window = (g.get("hue_windows") or {}).get(hue_key) or {}
    family = _family_for_category(g, cat)
    ens_roles = _ensemble_role_colors(g, cat)

    def pick(role: str, fallback_role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        # 1) same-category ensemble memory wins (scene-proven colors)
        if role in ens_roles:
            rgb = ens_roles[role]
            return {
                "name": f"ensemble_{cat}_{role}",
                "rgb": [round(c, 4) for c in rgb],
                "hex": rgb_to_hex(rgb),
                "source": "ensemble_same_category",
            }

        sw = list(_palette_swatches(g, role))
        if not sw and fallback_role:
            sw = list(_palette_swatches(g, fallback_role))
        if not sw:
            return None

        if role == "emissive":
            for s in sw:
                if s.get("name") and any(k in (s["name"] or "").lower() for k in ("lava", "forge", "glow", "ember")):
                    return {**s, "source": "bible_palette"}
            return {**sw[0], "source": "bible_palette"}

        if role == "foam_or_edge":
            for s in sw:
                if s.get("name") and "foam" in (s["name"] or "").lower():
                    return {**s, "source": "bible_palette"}
            return {**sw[0], "source": "bible_palette"}

        # score swatches for category fit (body/support roles)
        ranked = sorted(
            sw,
            key=lambda s: _swatch_matches_category(s, cat, hue_key, window),
            reverse=True,
        )
        best = ranked[0]
        # Prefer a non-negative category score; if all negative, still return best
        # but mark source so agents know validation may fight it.
        score = _swatch_matches_category(best, cat, hue_key, window)
        return {**best, "source": "bible_palette", "category_fit_score": round(score, 3)}

    roles = {
        "primary": pick("primary"),
        "secondary": pick("secondary", "primary"),
        "shadow": pick("shadow"),
        "highlight": pick("highlight"),
        "dirt": pick("dirt", "shadow"),
        "accent": pick("accent") if hero else None,
        "foam_or_edge": pick("foam_or_edge", "highlight") if cat == "water" else None,
        "emissive": pick("emissive") if wants_emissive and g.get("emissive_allowed") else None,
    }

    # roughness suggestion — family override > roughness_guidance > defaults
    rg = g.get("roughness_guidance") or {}
    wet = float(g.get("wetness") or 0)
    rough_key = {
        "stone_pavement": "stone_wet" if wet > 0.5 else "stone_dry",
        "stone_rock": "stone_wet" if wet > 0.5 else "stone_dry",
        "brick": "stone_wet" if wet > 0.5 else "stone_dry",
        "wood_planks": "wood_raw",
        "wood_parquet": "wood_raw",
        "water": "water_body",
        "metal_iron": "metal_iron",
        "metal_gold": "metal_gold",
        "metal_copper": "metal_iron",
        "leather": "leather",
        "fabric_cloth": "wood_raw",
    }.get(cat, "stone_dry")
    r_range = list(family.get("roughness") or rg.get(rough_key) or [0.5, 0.8])
    r_bias = 0.0
    rb = g.get("roughness_bias") or {}
    if "stone" in cat or cat in ("brick", "concrete", "terracotta", "marble"):
        r_bias = float(rb.get("stone") or 0)
    elif "wood" in cat:
        r_bias = float(rb.get("wood") or 0)
    elif "metal" in cat:
        r_bias = float(rb.get("metal") or 0)
    elif cat == "water":
        r_bias = float(rb.get("water") or 0)
    elif cat == "leather":
        r_bias = float(rb.get("leather") or 0)
    r_mid = (float(r_range[0]) + float(r_range[1])) / 2.0 + r_bias
    r_mid = _clamp(r_mid)

    # scene grade note for agents
    grade_bits = []
    if g.get("mood_tags"):
        grade_bits.append("mood=" + ",".join(g.get("mood_tags") or []))
    if g.get("white_balance"):
        grade_bits.append(f"wb={g.get('white_balance')}")
    if g.get("wetness"):
        grade_bits.append(f"wetness={g.get('wetness')}")
    if g.get("dust"):
        grade_bits.append(f"dust={g.get('dust')}")
    if g.get("saturation_scale") not in (None, 1, 1.0):
        grade_bits.append(f"sat_scale={g.get('saturation_scale')}")

    return {
        "project_id": bible["project_id"],
        "scene_id": bible["scene_id"],
        "category": cat,
        "look_authority": "art_bible_and_scene",
        "look_rule": g.get("look_rule"),
        "hue_window_key": hue_key,
        "hue_window": (g.get("hue_windows") or {}).get(hue_key),
        "harmony_mode": g.get("harmony_mode"),
        "mood_tags": g.get("mood_tags"),
        "scene_grade": ", ".join(grade_bits),
        "white_balance": g.get("white_balance"),
        "emissive_allowed": g.get("emissive_allowed"),
        "family_dna": family or None,
        "suggested_roles": {k: v for k, v in roles.items() if v},
        "suggested_roughness": round(r_mid, 3),
        "roughness_range": r_range,
        "metallic": family.get("metallic"),
        "wetness": wet,
        "dust": g.get("dust"),
        "art_pillars": g.get("art_pillars"),
        "do": g.get("do"),
        "dont": g.get("dont"),
        "ensemble_count": len(g.get("ensemble") or []),
        "ensemble_same_category_colors": ens_roles or None,
        "param_mapping_hints": {
            "stone_color|base_color|color|water_color|wood_color|obsidian_color|leather_color": "primary",
            "color_variation|secondary|moss|second_color|undertone": "secondary",
            "shadow_color|joint|dirt": "shadow or dirt",
            "highlight_color|foam_color|worn_edge": "highlight or foam_or_edge",
            "lava_color|corruption_color|emissive": "emissive",
            "roughness|water_roughness|obsidian_roughness|lava_roughness": "use suggested_roughness / dual",
        },
        "must_apply_bible_colors": True,
        "forbid_donor_default_colors": True,
    }


def validate_colors_against_project(
    proposed_colors: Dict[str, Any],
    *,
    category: str = "",
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    wants_emissive: bool = False,
    material_id: str = "",
) -> Dict[str, Any]:
    """
    proposed_colors: { role_or_param_name: [r,g,b] or {rgb/hex} }
    """
    bible = get_art_bible(project_id, scene_id)
    if bible.get("error"):
        return bible
    g = bible["merged_guidance"]
    cat = (category or "").lower().strip()
    hue_key = _CATEGORY_HUE_KEY.get(cat, "stone")
    window = (g.get("hue_windows") or {}).get(hue_key) or {}
    vrange = g.get("value_range") or {"min": 0.02, "max": 0.98}
    sat_scale = float(g.get("saturation_scale") or 1.0)
    issues: List[Dict[str, Any]] = []
    fixes: Dict[str, Any] = {}
    normalized: Dict[str, Any] = {}

    # normalize keys to roles when possible
    for key, raw in (proposed_colors or {}).items():
        rgb = ensure_rgb(raw)
        if not rgb:
            issues.append({"level": "warn", "code": "unparsed_color", "key": key, "msg": f"Could not parse color for {key}"})
            continue
        role = key if key in (
            "primary", "secondary", "shadow", "highlight", "accent",
            "emissive", "dirt", "foam_or_edge"
        ) else infer_param_role(key)
        normalized[key] = {
            "rgb": [round(c, 4) for c in rgb],
            "hex": rgb_to_hex(rgb),
            "role": role,
            "hsv": [round(x, 4) for x in rgb_to_hsv(rgb)],
            "luminance": round(relative_luminance(rgb), 4),
        }

        h, s, v = rgb_to_hsv(rgb)
        lum = relative_luminance(rgb)

        # value range
        if lum < float(vrange.get("min", 0.02)) - 0.01 and role not in ("shadow", "dirt", "emissive"):
            issues.append({
                "level": "warn",
                "code": "too_dark",
                "key": key,
                "role": role,
                "msg": f"{key} luminance {lum:.3f} below project floor {vrange.get('min')}",
            })
        if lum > float(vrange.get("max", 0.98)) + 0.01 and role not in ("highlight", "foam_or_edge", "emissive"):
            issues.append({
                "level": "warn",
                "code": "too_bright",
                "key": key,
                "role": role,
                "msg": f"{key} luminance {lum:.3f} above project ceiling {vrange.get('max')}",
            })

        # emissive policy
        if role == "emissive" or "emissive" in key.lower() or "lava_color" in key.lower():
            if not g.get("emissive_allowed") and not wants_emissive:
                issues.append({
                    "level": "fail",
                    "code": "emissive_not_allowed",
                    "key": key,
                    "role": role,
                    "msg": f"Scene '{bible['scene_id']}' disallows emissive — remove or move mat to forge/heat scene",
                })

        # hue window for body roles
        # Low-sat greys have unstable hue — skip hue membership when chroma is weak.
        # Secondary on stone may be moss/patina (vegetation window) — allow either.
        hue_sat_floor = 0.18 if hue_key in ("stone", "metal_cool") else 0.10
        if role in ("primary", "secondary") and window and s > hue_sat_floor:
            centers = [float(window.get("center", 0.0))]
            widths = [float(window.get("width", 0.5))]
            if role == "secondary" and hue_key == "stone":
                veg = (g.get("hue_windows") or {}).get("vegetation") or {}
                if veg:
                    centers.append(float(veg.get("center", 0.28)))
                    widths.append(float(veg.get("width", 0.10)))
            dists = [hue_distance(h, c) for c in centers]
            # pick best matching window
            best_i = min(range(len(dists)), key=lambda i: dists[i] / max(widths[i], 1e-6))
            dist, center, width = dists[best_i], centers[best_i], widths[best_i]
            if dist > width:
                level = "fail" if role == "primary" else "warn"
                # loud wrong hues (teal lawn on stone, etc.) stay fail; mild misses warn
                if role == "primary" and dist < width * 2.5 and s < 0.35:
                    level = "warn"
                issues.append({
                    "level": level,
                    "code": "hue_out_of_window",
                    "key": key,
                    "role": role,
                    "msg": (
                        f"{key} hue {h:.3f} is {dist:.3f} from window center {center:.3f} "
                        f"(allowed width {width:.3f} for '{hue_key}')"
                    ),
                    "suggested_hue": center,
                })
                fix_rgb = hsv_to_rgb(center, min(s, float(window.get("sat_max", 1.0))) * sat_scale, v)
                fixes[key] = {
                    "rgb": [round(c, 4) for c in fix_rgb],
                    "hex": rgb_to_hex(fix_rgb),
                    "reason": f"shift hue toward {hue_key} window center",
                }

        if role in ("primary", "secondary") and window:
            sat_max = float(window.get("sat_max", 1.0)) * sat_scale
            if s > sat_max + 0.02 and role == "primary":
                issues.append({
                    "level": "warn",
                    "code": "over_saturated",
                    "key": key,
                    "role": role,
                    "msg": f"{key} sat {s:.3f} > window sat_max {sat_max:.3f}",
                })
                if key not in fixes:
                    fix_rgb = hsv_to_rgb(h, sat_max, v)
                    fixes[key] = {
                        "rgb": [round(c, 4) for c in fix_rgb],
                        "hex": rgb_to_hex(fix_rgb),
                        "reason": "clamp saturation to project/scene budget",
                    }

        # snap suggestion to nearest palette swatch for role
        swatches = _palette_swatches(g, role if role != "dirt" else "dirt")
        if not swatches and role == "dirt":
            swatches = _palette_swatches(g, "shadow")
        near = _nearest_swatch(rgb, swatches) if swatches else None
        if near and near["distance"] > 0.18 and role in ("primary", "shadow", "dirt", "highlight"):
            issues.append({
                "level": "warn",
                "code": "far_from_palette",
                "key": key,
                "role": role,
                "msg": f"{key} is far from nearest bible swatch '{near.get('name')}' (d={near['distance']})",
                "nearest": near,
            })
            if key not in fixes:
                fixes[key] = {
                    "rgb": near["rgb"],
                    "hex": near["hex"],
                    "reason": f"snap to palette swatch {near.get('name')}",
                }

    # shared dirt language — dirt/shadow should stay near scene shared_dirt / joint_dirt
    dirt_refs = _palette_swatches(g, "dirt") or _palette_swatches(g, "shadow")
    for key, n in list(normalized.items()):
        if n["role"] not in ("dirt", "shadow"):
            continue
        near = _nearest_swatch(n["rgb"], dirt_refs) if dirt_refs else None
        if near and near["distance"] > 0.22:
            issues.append({
                "level": "fail" if n["role"] == "dirt" else "warn",
                "code": "dirt_language_drift",
                "key": key,
                "role": n["role"],
                "msg": (
                    f"{key} drifts from scene shared dirt/shadow language "
                    f"(nearest '{near.get('name')}' d={near['distance']}). "
                    "Reuse shared_dirt / joint_dirt — do not invent a new grunge dialect."
                ),
                "nearest": near,
            })
            if key not in fixes:
                fixes[key] = {
                    "rgb": near["rgb"],
                    "hex": near["hex"],
                    "reason": "snap to scene shared dirt/shadow language",
                }

    # category allow-list (project art bible)
    allowed = [c.lower() for c in (g.get("allowed_categories") or [])]
    preferred = [c.lower() for c in (g.get("preferred_categories") or [])]
    if cat and allowed and cat not in allowed:
        # soft if it matches a preferred prefix / family
        ok_prefix = any(cat.startswith(a.split("_")[0]) for a in allowed)
        issues.append({
            "level": "warn" if ok_prefix else "fail",
            "code": "category_not_in_bible",
            "key": "category",
            "msg": (
                f"category '{cat}' is not in project allowed_categories {allowed}. "
                "Update the art bible or pick an allowed family."
            ),
        })
    elif cat and preferred and cat not in preferred:
        issues.append({
            "level": "info",
            "code": "category_not_preferred_in_scene",
            "key": "category",
            "msg": f"'{cat}' allowed by project but not preferred in scene '{bible['scene_id']}' ({preferred})",
        })

    # ensemble clash: primary too close in hue to a forbidden loud neighbor? soft check
    ens = g.get("ensemble") or []
    primary_keys = [k for k, n in normalized.items() if n["role"] == "primary"]
    if primary_keys and ens:
        pref = normalized[primary_keys[0]]["rgb"]
        for e in ens:
            eroles = e.get("roles") or {}
            e_primary = ensure_rgb(eroles.get("primary") or eroles.get("water_color"))
            if not e_primary:
                continue
            # flag if luminance contrast extreme for same category family
            if cat and e.get("category") == cat:
                if abs(relative_luminance(pref) - relative_luminance(e_primary)) > 0.45:
                    issues.append({
                        "level": "info",
                        "code": "ensemble_value_gap",
                        "key": primary_keys[0],
                        "msg": (
                            f"Value gap vs ensemble mat {e.get('material_id')} is large — "
                            "confirm intentional hierarchy"
                        ),
                    })
                # same-category primary hue drift vs approved ensemble
                d = color_distance(pref, e_primary)
                if d > 0.28:
                    issues.append({
                        "level": "warn",
                        "code": "ensemble_primary_drift",
                        "key": primary_keys[0],
                        "msg": (
                            f"Primary drifts from approved ensemble '{e.get('material_id')}' "
                            f"(d={d:.3f}). Regrade toward scene-proven colors."
                        ),
                    })
                    if primary_keys[0] not in fixes:
                        fixes[primary_keys[0]] = {
                            "rgb": [round(c, 4) for c in e_primary],
                            "hex": rgb_to_hex(e_primary),
                            "reason": f"snap toward ensemble {e.get('material_id')} primary",
                        }

    fails = sum(1 for i in issues if i["level"] == "fail")
    warns = sum(1 for i in issues if i["level"] == "warn")
    status = "fail" if fails else ("warn" if warns else "pass")

    return {
        "status": status,
        "material_id": material_id,
        "project_id": bible["project_id"],
        "scene_id": bible["scene_id"],
        "category": cat,
        "look_authority": "art_bible_and_scene",
        "hue_window_key": hue_key,
        "issues": issues,
        "fixes": fixes,
        "normalized": normalized,
        "summary": f"{status.upper()}: {fails} fail, {warns} warn, {len(issues)} total",
        "ship_gate": {
            "may_register": status != "fail",
            "must_regrade_if_fail": True,
            "rule": "Never ship / register on validation fail. Domain pass ≠ bible pass.",
        },
        "guidance_snapshot": {
            "harmony_mode": g.get("harmony_mode"),
            "emissive_allowed": g.get("emissive_allowed"),
            "wetness": g.get("wetness"),
            "dust": g.get("dust"),
            "mood_tags": g.get("mood_tags"),
            "white_balance": g.get("white_balance"),
            "dont": (g.get("dont") or [])[:8],
            "look_rule": g.get("look_rule"),
        },
    }


def design_brief(
    material_name: str,
    category: str,
    *,
    project_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    structure_intent: str = "",
    story_wear: str = "",
    hero: bool = False,
    wants_emissive: bool = False,
    build_path: str = "auto",
    notes: str = "",
    domain: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full pre-build brief: production domain + concepts + palette + validation + path advice.
    """
    bible = get_art_bible(project_id, scene_id)
    if bible.get("error"):
        return bible
    g = bible["merged_guidance"]
    cat = (category or "").lower().strip()
    domain_payload = domain_guidance_for_brief(category=cat, domain=domain)
    palette = suggest_palette_for_material(
        cat,
        project_id=bible["project_id"],
        scene_id=bible["scene_id"],
        hero=hero,
        wants_emissive=wants_emissive,
    )

    # build path advice
    path = build_path
    if path == "auto":
        # emissive / complex signature → prefer Level C clone donors
        if wants_emissive or cat in ("water", "stone_pavement", "marble"):
            path = "level_C_clone_then_regrade"
        else:
            path = "level_B_recipe_then_regrade"

    donor_hints = {
        "stone_pavement": ["stylized_cobblestone_pavement", "stone_pavement_mossy_stylized"],
        "water": ["stylized_ocean_water"],
        "stone_rock": ["stylized_lava_cracked", "stylized_basalt_rock", "corrupted_lava_rock"],
        "brick": ["stylized_bricks", "stylized_mossy_brick_wall"],
        "wood_planks": ["stylized_wood_planks", "stylized_cracked_wood_planks"],
        "metal_gold": ["stylized_cast_gold", "stylized_aged_gold"],
        "metal_copper": ["stylized_cast_copper", "stylized_hammered_copper"],
        "metal_iron": ["stylized_cast_iron", "stylized_battered_iron"],
        "ground_grass": ["stylized_lawn_grass", "stylized_earth_and_grass"],
        "scifi": ["stylized_scifi_floor_panel"],
        "leather": ["stylized_leather"],
    }

    role_colors = {}
    for role, sw in (palette.get("suggested_roles") or {}).items():
        if sw and sw.get("rgb"):
            role_colors[role] = sw["rgb"]

    # validate suggested colors against same bible (should pass)
    pre_val = validate_colors_against_project(
        role_colors,
        category=cat,
        project_id=bible["project_id"],
        scene_id=bible["scene_id"],
        wants_emissive=wants_emissive,
        material_id=material_name,
    )

    concepts_snip = load_design_concepts("domain")
    if "Domain" not in concepts_snip and "domain" not in concepts_snip.lower():
        concepts_snip = load_design_concepts("beautiful")
    if len(concepts_snip) > 2200:
        concepts_snip = concepts_snip[:2200] + "\n..."

    hierarchy_tier = "hero" if hero else "world"
    if hero:
        hierarchy_note = "Primary/hero surface — richer masks OK, accents allowed within bible"
    else:
        hierarchy_note = "World/secondary surface — quieter sat, restrained HF, reuse ensemble dirt/edge"

    freq = g.get("frequency_policy") or {}
    domain1_checklist = [
        "Define style: shape language + color limits + detail density (bible DNA)",
        "Block PRIMARY SHAPES in height first (low frequency) — must read in grayscale",
        "Sculpt mid frequency (warp/slope-blur/levels) without killing silhouette",
        "Restrain high frequency — fewer and larger; no photoreal pore soup",
        "Build masks from height (histogram_scan/select, height_blend)",
        "Color blocks via uniform/HSL/quantize — limited palette roles from this brief",
        "Story wear only where contact is logical (shared dirt/edge language)",
        "Simplify roughness/metallic; emissive only if scene allows",
        "Normal from height + HBAO; optional soft baked edge/AO cues in albedo if DNA allows",
        "Expose params: colors, wear, density, roughness — enable scene variants / instances",
        "Export mindset: tileable, parameter-driven (.sbsar-ready) for master/instance reuse",
    ]
    domain2_checklist = [
        f"Hierarchy tier = {hierarchy_tier}: {hierarchy_note}",
        f"Match shape language: {g.get('shape_language')}",
        f"Match detail density: {g.get('detail_density')}",
        f"Match wear philosophy: {g.get('wear_philosophy')}",
        "Hue/sat/value inside project windows (run validate_material_against_project)",
        "Reuse scene dirt/shadow/edge language — do not invent a new grunge dialect",
        "Feature scale compatible with ensemble neighbors at target camera",
        "Roughness family coherent with scene wetness/dust and neighbors",
        "Accent budget respected; no extra emissive unless scene allows",
        "Test beside ensemble mats under target lighting/camera before final approve",
    ]

    # Production-domain checklist (game/3D application layer) — from domains/*.md
    domain_prod_checklist = list(domain_payload.get("agent_checklist") or [])
    if hero:
        domain_prod_checklist = [
            "Hero/unique asset: higher detail budget OK but still obey style language + texel rules",
            "Document any unique master / exception in project notes",
        ] + domain_prod_checklist
    else:
        domain_prod_checklist = [
            "World/environment class: prefer shared masters, atlases, quieter variation",
        ] + domain_prod_checklist

    domain_id = domain_payload.get("domain_id") or resolve_domain_id(domain, category=cat)
    family = _family_for_category(g, cat)

    # Compact mandatory color card — agents must apply these, not donor defaults
    color_card: Dict[str, Any] = {}
    for role, sw in (palette.get("suggested_roles") or {}).items():
        if not sw:
            continue
        color_card[role] = {
            "rgb": sw.get("rgb"),
            "hex": sw.get("hex"),
            "name": sw.get("name"),
            "source": sw.get("source") or "bible_palette",
        }

    art_bible_lock = {
        "authority": "art_bible_and_scene",
        "rule": g.get("look_rule") or (
            "Art bible + active scene decide color/feel/mood. "
            "Domain decides pipeline only. Donors are topology only."
        ),
        "project_id": bible["project_id"],
        "scene_id": bible["scene_id"],
        "must_apply_these_colors": True,
        "forbid_donor_default_colors": True,
        "forbid_domain_as_palette": True,
        "color_card": color_card,
        "roughness": palette.get("suggested_roughness"),
        "roughness_range": palette.get("roughness_range"),
        "metallic": palette.get("metallic"),
        "hue_window_key": palette.get("hue_window_key"),
        "hue_window": palette.get("hue_window"),
        "scene_grade": {
            "mood_tags": g.get("mood_tags") or [],
            "white_balance": g.get("white_balance"),
            "shadow_temperature": g.get("shadow_temperature"),
            "key_light_temperature": g.get("key_light_temperature"),
            "saturation_budget": g.get("saturation_budget"),
            "saturation_scale": g.get("saturation_scale"),
            "wetness": g.get("wetness"),
            "dust": g.get("dust"),
            "time_of_day": g.get("time_of_day"),
            "weather": g.get("weather"),
            "biome": g.get("biome"),
            "camera_notes": g.get("camera_notes"),
            "emissive_allowed": g.get("emissive_allowed"),
        },
        "family_dna": family or None,
        "shared_dirt": (color_card.get("dirt") or color_card.get("shadow")),
        "ensemble": g.get("ensemble") or [],
        "pre_validation_status": pre_val.get("status"),
        "ship_gate": (
            "Build with color_card → validate_material_against_project → "
            "register only if status != fail → lookdev beside ensemble"
        ),
    }

    return {
        "material_name": material_name,
        "project_id": bible["project_id"],
        "scene_id": bible["scene_id"],
        "category": cat,
        "domain_id": domain_id,
        # LOOK first — never optional
        "look_authority": "art_bible_and_scene",
        "art_bible_lock": art_bible_lock,
        "structure_intent": structure_intent,
        "story_wear": story_wear,
        "hero": hero,
        "hierarchy_tier": hierarchy_tier,
        "wants_emissive": wants_emissive,
        "build_path": path,
        "donor_hints": donor_hints.get(cat, []),
        "donor_policy": {
            "allowed_for": "topology_structure_only",
            "forbidden_for": ["final_colors", "final_roughness", "scene_grade", "dirt_hue"],
            "rule": "Clone/recipe scaffolds nodes. Art bible color_card is the grade. Regrade immediately.",
        },
        "harmony_mode": g.get("harmony_mode"),
        "mood_tags": g.get("mood_tags"),
        "art_pillars": g.get("art_pillars"),
        "style_dna": {
            "shape_language": g.get("shape_language"),
            "detail_density": g.get("detail_density"),
            "wear_philosophy": g.get("wear_philosophy"),
            "albedo_lighting_policy": g.get("albedo_lighting_policy"),
            "frequency_policy": freq,
            "core_hue_count_target": g.get("core_hue_count_target"),
            "scale_notes": (g.get("style_dna") or {}).get("scale_notes"),
        },
        "map_priority": [
            "height (form driver)",
            "normal (readable volume)",
            "basecolor (blocks + optional baked cues) — FROM art_bible_lock.color_card",
            "roughness/metallic (simplified) — FROM art_bible_lock",
            "ao/emissive/masks as needed",
        ],
        "frequency_plan": {
            "low": freq.get("low", "required_structure"),
            "mid": freq.get("mid", "sculpt_and_wear"),
            "high": freq.get("high", "restrained"),
            "rule": "HF is a privilege after grayscale silhouette reads",
        },
        "palette": palette.get("suggested_roles"),
        "roughness": palette.get("suggested_roughness"),
        "roughness_range": palette.get("roughness_range"),
        "param_mapping_hints": palette.get("param_mapping_hints"),
        "expose_params_suggested": [
            "primary/secondary/shadow/highlight colors",
            "wear_intensity / dirt_amount",
            "pattern_density / stones_scale / wave_density",
            "roughness",
            "normal_intensity",
        ],
        "reuse_strategy": {
            "prefer": "master_plus_instances",
            "variants_to_plan": ["clean", "dirty", "wet", "damaged"] if not hero else ["hero_clean", "hero_worn"],
            "share": ["maps where possible", "dirt/edge language", "parameter names/ranges across family"],
            "note": "Domain rule: prefer Master+Instance over unique one-offs; expose params for variants",
        },
        "ensemble": g.get("ensemble"),
        "production_domain": domain_payload,
        "domain_production_checklist": domain_prod_checklist,
        "domain1_authoring_checklist": domain1_checklist,
        "domain2_ensemble_checklist": domain2_checklist,
        "do": g.get("do"),
        "dont": g.get("dont"),
        "pre_validation": {
            "status": pre_val.get("status"),
            "summary": pre_val.get("summary"),
            "issues": pre_val.get("issues"),
            "fixes": pre_val.get("fixes"),
            "ship_gate": pre_val.get("ship_gate"),
        },
        "workflow": [
            "1. Confirm project/scene (project_set_active) — LOOK context",
            "2. Read art_bible_lock.color_card + scene_grade — MANDATORY grade source",
            "3. Read production domain (pipeline rules only, NOT colors)",
            "4. Read D1+D2 checklists + stylized_design_concepts (craft)",
            "5. Optional: category_guide / search / clone donor for TOPOLOGY only",
            "6. Author height-first; protect fewer-and-larger frequency plan",
            "7. IMMEDIATELY apply art_bible_lock.color_card + roughness (never donor defaults)",
            "8. Reuse shared_dirt / joint_dirt from color_card — no new grunge dialect",
            "9. Expose key params for master/instance scene variants",
            "10. validate_material_against_project with FINAL colors (fail = do not ship)",
            "11. project_register_material only on pass/warn",
            "12. Spot-check WITH ensemble under target light/camera (lookdev, not beauty sphere only)",
        ],
        "concepts_excerpt": concepts_snip,
        "notes": notes,
    }
