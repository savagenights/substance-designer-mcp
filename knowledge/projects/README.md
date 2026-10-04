# Project Art Bibles

Per-production constraints so stylized materials **fit the same movie/game**, not just look cool alone.

## Layout

```
knowledge/projects/
  README.md
  _index.json                 # registry of projects
  <project_id>/
    project.json              # master art bible + palette + pillars
    scenes/
      <scene_id>.json         # local mood, overrides, ensemble
    materials_log.jsonl       # optional: approved material snapshots
```

## Workflow

1. `project_create` / edit `project.json`
2. `project_set_scene` for biomes/shots
3. Before each material: `domain_get` (production scope) + `project_get_art_bible` + `stylized_design_brief`
4. Build (Level B recipe or Level C clone)
5. `validate_material_against_project` → fix role colors
6. `project_register_material` so the ensemble grows

## Color roles

`primary` · `secondary` · `shadow` · `highlight` · `accent` · `emissive` · `foam_or_edge` · `dirt`

See `domains/` for production domain context (3D/game application rules) and
`knowledge/stylized/design_concepts.md` for Designer D1/D2 craft theory.
