# Changelog

All notable changes to the Substance Designer MCP Plugin are documented here.

---

## [Unreleased] — Domains + art-bible look lock

### Production domains (`domains/`)
- New folder of production-scope context docs (above Designer craft, below art bible)
- Shipped: `domains/stylized_materials.md` — Stylized Materials for Video Game Development (3D Model Application)
- Live filesystem discovery (`_scan_domains`) — **no static domain registry**
- Optional Meta routing: `Id`, `Default`, `Aliases`, `Categories`, `Category prefixes`
- MCP: `domain_list`, `domain_get`, `domain_get_section`

### Art bible LOOK lock (critical)
- **Bugfix:** scene `local_palette` wiped entire master role lists → leather could become courtyard greystone
- **Fix:** `_merge_palette_role` keeps master swatches; scene entries win on same name only
- `stylized_design_brief` now leads with `art_bible_lock.color_card` + `scene_grade` (mandatory grade)
- `look_authority=art_bible_and_scene`, `donor_policy=topology_only`, `forbid_domain_as_palette`
- Palette prefer same-category ensemble colors, then bible swatches (category-scored)
- Validation ship gate: dirt-language drift fail, category allow-list, ensemble primary drift, `ship_gate.may_register`
- Skill v3.2: domain = pipeline only; bible/scene = color/feel

Authority stack: **Art bible (look) > Domain context (production) > design_concepts (D1/D2 craft) > general realtime**

---

## [1.0.0] — 2026-02-19 — First Public Release

### Plugin (v3.1.0)
- Complete MCP integration for Adobe Substance 3D Designer 15.x
- 16 MCP tools (11 core + 5 recipe/builder tools)
- Thread-safe Qt dispatch via Signal/Slot queued connection
- PySide6 path injection (SD ships its own PySide6, not in sys.path)
- Length-prefix TCP framing protocol (4-byte big-endian + JSON)
- Fresh-socket-per-command connection model (no stale state)

### Recipe System (v5.0 — 79 recipes)
- **Pro architecture family**: pro_granite, pro_limestone, pro_sandstone, pro_basalt, pro_slate, pro_steel, pro_iron, pro_copper, pro_concrete, pro_concrete_aged, pro_concrete_smooth (37–44 nodes each)
- **Core materials**: wood×5, rock×6, metal×7, organic×9, soil×5, water_ice×4, gems×5
- **Specialty**: concrete, brick, lava, asphalt, plaster, fabric, tile, specialty
- **Heightmap styles** (8): cliff, rock, sand, cracked, mud, mountain, cobblestone, terrain
- **MainShape** reconstruction (pro architecture, 11 nodes from live data)
- Pro node chain: clouds_2 → slope_blur×2 → edge_detect → flood_fill → flood_fill_to_gradient_2 → multi_directional_warp×2 → directionalwarp×3 → highpass → histogram_scan
- All 79 recipes validated: 0 port failures, 0 crashes

### Bridge Server (v2.0.0)
- BUG-B01: `_send_lock` no longer held across retry loop — prevents 360-second deadlock
- BUG-B03: Default port corrected to 9881 (was 9880)
- BUG-B04: `directionalwarp` warp-map port corrected to `inputintensity` (was `inputgradient`)
- BUG-B05: FastMCP lifespan set at constructor, not post-construction
- BUG-B06: `ctx: Context` kept for FastMCP 1.4.1+ compatibility
- BUG-B07: `None` results return `"{}"` not `"null"`; NaN/Inf handled via `_json_safe`
- BUG-B08: Retry logic applies to connection failures only, not SD operation timeouts
- Async serialization via `threading.Lock` + `asyncio.to_thread`

### Critical Bug Fixes (SD 15.x)
- `SDValueInt2/3/4` on float params crashes SD silently → `_infer_type` always returns float2/3/4 for lists
- `SDValueFloat` on enum/int SD properties crashes SD silently → `_coerce_type()` reads actual SD type
- `_set_node_params` reads property type via `getType().getId()` and coerces accordingly
- `build_heightmap_graph`: builders return dict, not tuple — fixed unpacking
- `SDPackage.deleteResource()` does not exist — correct API is `resource.delete()`

### Confirmed SD 15.0.3 API Facts
- Library node outputs ≠ `"unique_filter_output"` (each has its own ID)
- `SDUsage.sNew()` hangs SD 15 permanently — removed
- `newNode(unknown_def)` hangs SD 15 permanently — validated before call
- `arrange_nodes()` destroys all connections — use `move_node()` instead
- `directionalwarp` warp-map input = `inputintensity` (NOT `inputgradient`)

---

## Internal Versions (not publicly released)

- **v3.1.0** (2026-02-18): SD crash fixes, build_heightmap bug fix, SD API notes
- **v3.0.0** (2026-02-15): Full recipe engine, smart builder, 34 initial materials
- **v2.x.x** (2026-02-10): PySide6 injection, Signal/Slot dispatcher
- **v1.x.x** (2026-02-01): Initial prototype
