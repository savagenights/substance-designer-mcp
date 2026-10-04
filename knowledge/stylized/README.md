# Stylized Substance Knowledge Base

**Center of gravity = project art-bibles** (`knowledge/projects/`).
The mined reference corpus is an optional topology donor shelf — not the brand, not the look.

## What matters

| Priority | Path | Role |
|----------|------|------|
| **1** | `../projects/<id>/` | Art bible, scenes, ensemble, palette DNA (LOOK) |
| **2** | `../../domains/*.md` | Production domain scope (3D/game application rules) |
| **3** | `design_concepts.md` | Designer D1 authoring + D2 ensemble theory |
| **4** | `playbook.md` / patterns / catalog | Category topology stats from reference corpus |
| **5** | Level B recipes / Level C clone | Build machinery (always regrade to bible) |

## Files here

| File | Purpose |
|------|---------|
| `design_concepts.md` | Beauty rules, frequency, hierarchy, ensemble laws |
| `playbook.md` | Per-category graph grammar (mined patterns) |
| `catalog.json` | Search index for reference donors |
| `materials.jsonl` | Full fingerprints (`specialty_filters`, patterns, params) |
| `patterns.json` | Aggregated category stats |

## Rebuild reference mine (optional)

```powershell
cd F:\AI\PROJECTS\sbs-stylized-scraper
python mine_stylized_kb.py
```

Miner should emit `specialty_filters` / `top_specialty_filters`.

## Agent order of operations

```
project_set_active → project_get_art_bible          # LOOK context first
domain_get(...)                                     # pipeline scope only
stylized_design_brief(...)
  → MUST honor art_bible_lock.color_card + scene_grade
  → production_domain is pipeline only (not colors)
  → (optional) category_guide / search / clone donor for TOPOLOGY
  → build → IMMEDIATELY apply color_card + roughness
  → validate_material_against_project (ship_gate)
  → project_register_material only if status != fail
  → test with ensemble under target light (not beauty sphere only)
```

### Level B — fresh recipe
```
build_material_graph(graph_name="FABL_FORGE_x", recipe_name="stylized_brick")
```

### Level C — optional donor clone
```
clone_stylized_reference(material_id="stylized_cobblestone_pavement")
# then IMMEDIATELY regrade to active art bible
```

### Level D — coherence (required)
```
stylized_design_brief(...)
validate_material_against_project(...)
project_register_material(...)
```

Logic: `server/project_kb.py`
