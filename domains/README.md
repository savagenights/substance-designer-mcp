# Production Domains

Domain context files define **scope and production rules** for material work
aimed at real pipelines (e.g. stylized materials on 3D models for realtime games).

They sit in the authority stack **between** the project art bible and Designer craft:

```
1. Project Style Guide / Art Bible   (knowledge/projects/)   ← primary LOOK
2. Domain Context                    (domains/*.md)          ← production scope
3. Design Concepts D1/D2             (knowledge/stylized/)   ← Designer craft
4. General realtime best practices                           ← secondary limits
```

## What a domain is (and is not)

| Is                                                   | Is not                          |
|------------------------------------------------------|---------------------------------|
| Scope, workflows, non-negotiables, output contracts  | A color palette                 |
| Master/instance reuse, texel, packing, lookdev rules | A Substance node recipe         |
| Agent checklist for production-facing specs          | A replacement for the art bible |
| Pipeline / application law                           | Scene mood, hue windows, grade  |

**LOOK comes from `knowledge/projects/` (art bible + scene).**  
Domains never supply final colors, roughness grade, or dirt hue.

Conflict rule:  
**Project Style Guide / Art Bible (look) > Domain Context (pipeline) > general realtime practice.**

After any build: apply `stylized_design_brief → art_bible_lock.color_card`, then
`validate_material_against_project`. Domain checklist pass ≠ bible pass.

## Discovery (fully dynamic — no Python edits)

`server/project_kb.py` **live-scans** `domains/*.md` on every
`domain_list` / `domain_get` / `stylized_design_brief` call.

- New file → appears immediately
- Rename / delete → reflected immediately
- `README.md` and dotfiles are ignored
- **No static domain registry in code**

### Optional Meta table fields (routing without code changes)

| Field               | Purpose                                | Example                    |
|---------------------|----------------------------------------|----------------------------|
| `Id`                | Stable id (else filename stem)         | `stylized_materials`       |
| `Default`           | `yes` → fallback when category unknown | `yes`                      |
| `Aliases`           | comma list of alternate names          | `stylized, game_materials` |
| `Categories`        | exact category → this domain           | `leather, water, brick`    |
| `Category prefixes` | prefix match → this domain             | `metal_, stone_, fabric_`  |

Resolution order for briefs:
1. explicit `domain=` argument / alias
2. exact category from Meta `Categories`
3. longest Meta `Category prefixes` match
4. domain marked `Default: yes` (else sole file, else first filename)

If only one domain file exists, it is automatically the default even without the flag.

## Shipped domains

| File                    | Id                   | Purpose                                                              |
|-------------------------|----------------------|----------------------------------------------------------------------|
| `stylized_materials.md` | `stylized_materials` | Stylized Materials for Video Game Development (3D Model Application) |

## How the MCP server uses these

| Tool                    | Role                                              |
|-------------------------|---------------------------------------------------|
| `domain_list`           | Live inventory + aliases + category_map + default |
| `domain_get`            | Full domain (or section) + parsed checklists      |
| `domain_get_section`    | Markdown slice only                               |
| `stylized_design_brief` | Auto-resolves domain + embeds `production_domain` |

Logic: `server/project_kb.py` (`_scan_domains`, `list_domains`, `load_domain`, `resolve_domain_id`).

## Adding a new domain

1. Drop `domains/<snake_id>.md` (same section skeleton as `stylized_materials.md`
   is recommended: Meta, Overview, Scope, Glossary, Entities, Rules, Roles,
   Workflows, Constraints, Edge Cases, Output Expectations, Success Criteria).
2. Fill Meta at minimum: `Domain name`, optionally `Id`, `Default`, `Aliases`,
   `Categories`, `Category prefixes`.
3. Call `domain_list` — no bridge restart, no Python patch.
4. Agents pick it up via `domain_get` / brief `domain=` / category auto-route.

```markdown
| Field             | Value                           |
|-------------------|---------------------------------|
| Domain name       | Photoreal Environment Materials |
| Id                | photoreal_env                   |
| Default           | no                              |
| Aliases           | photoreal, realistic_pbr        |
| Categories        | asphalt, photo_concrete         |
| Category prefixes | photo_, scan_                   |
```

## Agent habit

```
domain_list                                      # see everything currently on disk
domain_get(domain="stylized_materials")          # or section="constraint"
project_set_active(...)
stylized_design_brief(...)                       # includes production_domain
# ... build ...
validate_material_against_project(...)
project_register_material(...)
```
