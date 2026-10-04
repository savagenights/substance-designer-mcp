# Stylized Material Design Concepts (Level D)

This is the **thinking layer** above cloning and recipes.
Cloning copies topology. Recipes scaffold nodes. **Concepts** decide *what beautiful means*
and whether a material belongs in a project / scene / film look.

Two domains, one pipeline:

1. **Domain 1 — Authoring stylized materials in Substance Designer**
2. **Domain 2 — Making materials look good *together* in a scene**

Use with project art-bibles (`knowledge/projects/`) and MCP tools:
`project_*`, `stylized_design_brief`, `validate_material_against_project`.

---

## 0. Domain map (read this first)

| Domain | Question it answers | Primary artifacts |
|--------|---------------------|-------------------|
| **D1 Authoring** | How do I build one readable stylized PBR graph? | node stack, frequency plan, masks, exposed params, `.sbsar` |
| **D2 Ensemble** | Will this mat belong with its neighbors under project lighting? | art bible, scene mood, hierarchy, shared DNA, validation |
| **Integration** | Every mat is authored *against the same style bible* | brief → build → validate → register → test together |

**Output goal (D1):** tileable, parameter-driven materials (ideally `.sbsar`) that match a defined art style and stay readable across distance and lighting.

**Output goal (D2):** a set of materials that share visual DNA, support storytelling hierarchy, and do not compete or clash in-frame.

---

## 1. What “beautiful stylized” actually is

Stylized beauty is **readable intention**, not noise density.
Stylized deliberately departs from photorealism toward artistic interpretation
(cartoon, painterly, hand-painted, toon, Ghibli-like, fantasy, graphic low-detail, etc.).

| Principle | Meaning | Fail mode |
|-----------|---------|-----------|
| **Silhouette of detail** | Forms read at arm’s length (tile, plank, wave, plate) | Micro-noise mush |
| **Fewer and larger** | Controlled detail density; restrained high frequency | Pore soup / photo breakup |
| **Value hierarchy** | Clear dark joints / mid body / light peaks (reads in grayscale) | Flat grey sludge |
| **Limited hue families** | 1–3 core hues + neutrals + rare accents | Rainbow junk drawer |
| **Material grammar** | Metal/wood/stone/water obey their own rules | Everything looks like plastic |
| **Controlled contrast** | Contrast sells shape; too much fractures the set | Disco normals / crunchy AO |
| **Shared world light** | All mats assume same grade (warm key, cool fill…) | One hero mat breaks the frame |
| **Wear tells story** | Dirt/edge/foam where contact happens | Random grunge stamps |
| **Scale honesty** | Texel density + feature size match camera + neighbors | Giant bricks next to pores |
| **Albedo may carry more** | Stylized often bakes shape/light cues into basecolor | Empty albedo + noisy normal only |

### Stylization vs realism ( Domains quick split )

| | Realism | Stylized |
|--|---------|----------|
| Noise | High-frequency, subtle | Low/mid first; HF restrained |
| Color | Micro-variation, photo breakup | Blocks, limited palette, posterization OK |
| Lighting in maps | Avoid baked lighting in albedo | Baked edge/AO/highlight cues often *desired* |
| PBR response | Energy-conserving, subtle | Simplified or exaggerated for graphic read |
| Randomness | Stochastic richness | **Controlled** randomness / deliberate Tile Sampler placement |

The reference corpus proves the topology: shape → mask carve → soft height → flat color blocks → simple roughness.

---

## 1b. Substance Designer — Domain 1 authoring model

Designer is a **node-based procedural** tool for tileable PBR materials.
Non-destructive, parametric, resolution-independent until export.

### Map hierarchy for stylized work

1. **Height** — primary driver of form and blends  
2. **Normal** — derived or hand-tuned for readable volume  
3. **Base color / albedo** — often carries more (gradients, painted light, color blocking)  
4. **Roughness / metallic** — simplified or exaggerated  
5. Optional: curvature, AO, emissive, custom masks  

### Detail frequency control

Author in **low / mid / high** bands. Protect global readability.
If HF fights the silhouette, kill HF — not the shape.

### Mask & blend toolkit (stylized staples)

- `histogram_scan` / `histogram_select` / `levels` — clean layer IDs  
- `height_blend` — logical material separation  
- `slope_blur` / `non_uniform_blur` / `warp` / `directional blur` — organic but controlled transitions  
- Tile Sampler / `tile_generator` with **pattern inputs** — deliberate placement > pure noise  
- Modern helpers (SD 14+): **Quantize Color**, **Kuwahara** (painterly anisotropic), better curvature/bevel  

### Key stylization techniques

| Technique | Why |
|-----------|-----|
| Slope blur + directional blur / Kuwahara | Brushy, hand-painted surfaces |
| Quantize Color | Limited palette, posterization |
| Gradient maps | Controlled value/color ramps |
| Baked edge highlights, corner wear, AO | Shape readability (classic hand-paint / 90s-game DNA) |
| Light info in albedo (when style asks) | Painterly / toon / Ghibli-adjacent |
| Modular sub-graphs | Reusable shapes, wear gens, pattern blocks |

### Workflow stages (always)

1. Reference gathering + **style definition** (shape language, color limits, detail density rules)  
2. Block out primary shapes in **height**  
3. Add mid/HF while preserving global read  
4. Masks from height for color / material separation  
5. Color + surface response (limited, harmonious, or high-contrast-on-purpose)  
6. **Expose parameters** (color, aging, density, wear)  
7. Test under multiple lights + in-engine (Unreal/Unity)  
8. Export optimized maps; presentation renders  

### Philosophy (practitioners)

- “Fewer and larger” details  
- Controlled randomness, not pure procedural noise  
- Albedo often does more heavy lifting than pure PBR textbooks allow  
- Maintain a **global look**; refuse photoreal micro-detail drift  
- Materials should be **modular and combinable** (ground + grass + snow blends, etc.)  

---

## 2. The stylized build stack (domain model)

Think in **layers of intent**, not random nodes:

```
A. STRUCTURE     tile/cells/planks/waves     → readable macro shape (LOW freq)
B. SCULPT        warp / slope-blur / levels  → painterly height (LOW→MID)
C. MASKS         histogram_scan/select       → clean layer IDs
D. COLOR BLOCKS  uniform + HSL + quantize    → 2–4 zone albedo
E. STORY WEAR    dirt / edge / foam / cracks → contact narrative (MID)
F. RESPONSE      roughness / metallic / emis → light behavior (simplified)
G. FINISH        normal from height, HBAO    → presentation
H. EXPOSE        artist params               → variation without graph edits
```

**Rule:** never start at F/G. Beauty dies when you polish noise.
**Rule:** HF detail is a privilege earned after A–C read in grayscale.

### Category grammar shortcuts

| Family | Structure bias | Color bias | Response bias |
|--------|----------------|------------|---------------|
| Stone / pavement | cells, tiles, mortar valleys | desat body + dirt joints | high rough, strong AO |
| Wood | stretched grain, plank cuts | warm body + darker rings | anisotropic-ish rough bands |
| Metal | hammer/panel, edge wear | hue-locked metal + oxide accent | high metallic, dual rough |
| Water | broad swells, foam crests | deep body + light foam | very low rough body |
| Lava | crust plates + molten channels | dark crust + hot accent | emis on molten, dual rough |
| Organic / ground | clumps, soft mounds | multi-green/brown blocks | soft rough, gentle AO |
| Sci-fi | hard panels, histogram edges | limited accents on neutrals | mixed metal/paint |
| Fabric | weave/macro folds | dyed flats + wear | mid-high rough |

---

## 3. Color theory that survives production

### 3.1 Work in roles, not hex souvenirs

Every material color should claim a **role**:

| Role | Job | Examples |
|------|-----|----------|
| `primary` | Dominant albedo body | stone body, wood plank, water mass |
| `secondary` | Variation / second species | lichen, second wood tone, coral sand |
| `shadow` | Joints, cavities, undersides | mortar, grooves, deep water |
| `highlight` | Worn tops, specular kiss zones | limestone lips, foam, metal edge |
| `accent` | Story color (rare) | moss, rust, banner dye, magic |
| `emissive` | Light emitter | lava, crystal, runes |
| `foam_or_edge` | Contact line treatment | wave foam, paint chips |

A project palette is a **set of allowed role swatches + hue windows**, not one flat list of pretty colors.

### 3.2 Harmony modes (pick one per project/scene)

| Mode | Rule of thumb | Feels like |
|------|----------------|------------|
| `analogous` | Hues within ~60° | Cohesive forest, ocean, desert |
| `complementary` | Base + opposite accent | Hero accent pops (lava on basalt) |
| `triadic` | 3 spaced hues, one dominant | Stylized cartoons, careful balance |
| `split_complementary` | Base + two near-opposites | Rich without chaos |
| `tetradic` | Two complement pairs | Only if one pair is muted |
| `monochrome` | One hue, value/sat play | Stone ruins, noir metal |
| `custom_locked` | Art-director swatches only | Film/game bible compliance |

### 3.3 Saturation & value discipline

- **World mats** (stone, dirt, wood): lower sat than props/heroes.
- **Hero props / emissive**: higher sat, still inside hue window.
- **Shared black & white**: scenes need a common shadow floor and highlight ceiling or materials won’t sit together.
- **Accent budget**: usually 5–15% of surface. More = carnival.

### 3.4 Temperature & grade

Art bibles should declare:

- `white_balance`: warm / neutral / cool
- `shadow_temperature`: often cooler than key
- `key_light_temperature`
- `saturation_budget`: low / medium / high
- `value_range`: e.g. avoid pure 0 and pure 1

When validating a material, shift proposed colors toward the bible **before** building.

---

## 4. Project → Scene → Material hierarchy

```
PROJECT (film / game / short)
  art_pillars: mood, references, harmony mode, global do/don't
  master_palette: role swatches + hue windows
  material_families: which categories exist in this world
  └── SCENE (level / shot / biome / interior)
        local_palette overrides (fog, time-of-day, biome shift)
        mood tags: wet, dusty, sacred, hostile, festive...
        ensemble: materials already approved for this scene
        └── MATERIAL INSTANCE
              category + structure intent
              role colors pulled from scene→project
              wear story fitting location
              validation report (pass/warn/fail)
```

**Coherence law:** a material can be gorgeous alone and still **wrong** if it breaks the ensemble.

Examples:
- Deep ocean water + warm tan cobble without a shared grade → two different movies.
- Lava heat accent in a monochrome monastery scene → unless the plot says so, fail.
- High-sat grass next to desaturated medieval stone → cartoon lawn on a grey set.

---

## 5. Ensemble logic (Domain 2 — materials that look good together)

Goal: materials feel like they belong to the **same world**, support storytelling and
readability, and do not compete or clash.

### 5.1 Shared style language / visual DNA

Every mat in a scene should share:

| DNA strand | Meaning |
|------------|---------|
| Shape language | Rounded vs angular, organic vs hard-surface |
| Detail density | Same “fewer and larger” budget; no hyper-detail next to flat |
| Feature scale | Brick/wood-grain/wave size compatible at target camera |
| Wear philosophy | Same edge definition, aging logic, dirt language |
| Surface response family | Roughness/metallic ranges that answer the same light |
| Art direction | All painterly / all toon / all graphic — no silent photoreal infiltrators |

### 5.2 Material hierarchy (primary / secondary / tertiary)

| Tier | Role in frame | Authorship bias |
|------|---------------|-----------------|
| **Hero / primary** | Focal surfaces, story props | More contrast, richer masks, allowed accents |
| **Secondary** | Supporting set dressing | Clear but quieter; reuse hero dirt/edge language |
| **Tertiary / world** | Large fills, distant ground | Lowest sat, simplest HF, stable values |

Texture & roughness contrast (smooth vs rough, matte vs specular) creates interest
**without** chaos — contrast is hierarchical, not random.

### 5.3 Color harmony & palette discipline (scene-level)

- Limited intentional palette: often **2–5 core hues + neutrals**
- Analogous = calm cohesion; complementary = focus; split-comp = richness with control
- Value hierarchy must survive **grayscale** (forms still read)
- Controlled sat/temperature shifts reinforce mood and depth (cool shadows, warm key, etc.)

### 5.4 Physical & lighting coherence

- Shared response to the same lighting setup (rough/metal ranges, baked-vs-realtime cue policy)
- Believable transitions: dirt, moss, wear, stylized blends that feel *logical* in the environment
- Extreme outliers only as intentional focal points (hero emissive, magic prop)

### 5.5 Composition & storytelling

- Materials reinforce narrative (weathered wood + aged stone = abandoned; polished = high-tech)
- Visual weight guided by material contrast
- Prefer modular/blendable systems (vertex paint, height blends, layers) so transitions feel native

### 5.6 Practical consistency rules

- Master material / template mindset: shared parameter *names* and ranges across a family
- Consistent stylized scale references (what is “1 cobble” vs “1 plank width”)
- Naming + library organization that keeps families coherent
- **Test materials together early** under project lighting and camera — not alone in a beauty sphere only

### 5.7 Pre-ship checklist (agent validation)

1. **Hue membership** — primary/secondary inside scene hue windows (or justified accent)
2. **Sat budget** — not louder than heroes unless it *is* the hero
3. **Value overlap** — body values on the same train as neighbors
4. **Roughness family** — wet scene ⇒ lower rough on stone/wood near water; desert ⇒ higher
5. **Wear language** — same dirt hue / edge color across set dressing
6. **Scale / density DNA** — feature size + detail density match ensemble
7. **Hierarchy tier** — hero vs world intentional
8. **Accent monopoly** — one loud accent family per frame unless directed
9. **Emissive policy** — only if scene flags allow
10. **Shape language** — not introducing a foreign geometry dialect

Validation tools return **actionable fixes**
(“desaturate primary 20%”, “shift hue toward navy bible”, “reuse scene dirt_color”,
“drop HF — density above scene budget”).

### 5.8 Common ensemble failure modes

- Clashing color temperatures or saturation levels
- Inconsistent detail density (one mat hyper-detailed, neighbor flat)
- Scale mismatches (wood grain / brick size wrong next to neighbor)
- Materials that ignore overall lighting or art direction
- Every mat inventing its own dirt hue / edge language
- Beauty-sphere heroes that break when placed in the real set

---

## 6. Intent capture (what the agent must ask / infer)

When user says “make X”, resolve:

| Field | Questions |
|-------|-----------|
| `project_id` | Which art bible? |
| `scene_id` | Which biome/shot? |
| `category` | stone_pavement / water / lava… |
| `structure_intent` | cobbles, planks, swells, crust plates… |
| `story_wear` | mossy, battle-scarred, pristine, flooded… |
| `hero_or_world` | background world mat vs hero prop |
| `camera_distance` | hero closeup vs environment tiling |
| `references` | film stills, hex swatches, existing SBS |
| `must_match_materials` | ensemble partners already in scene |

If project/scene missing → create or load defaults, don’t silently freestyle.

---

## 7. Design brief recipe (agent output before nodes)

Every build should be able to emit:

```yaml
project: fabl_forge
scene: coastal_keep_night
material: FABL_FORGE_stylized_wet_cobble
category: stone_pavement
structure: irregular cobbles, deep mortar
harmony: analogous cool
roles:
  primary:  # from scene stone window
  secondary: # moss allowed accent
  shadow:    # shared dirt
  highlight: # wet kiss from water scene link
response:
  roughness: 0.55  # wet bias from scene mood
  metallic: 0
  emissive: false
ensemble_links: [deep_ocean_water, keep_plaster]
validation: pass
build_path: level_B_or_C
```

Then — and only then — clone or recipe-build and apply role colors.

---

## 8. Anti-patterns (kill on sight)

**Domain 1 (authoring)**
- Photoreal noise recipes for stylized asks
- Starting with roughness/normal polish before height reads in grayscale
- Uncontrolled high-frequency detail (“more noise = better”)
- Pure randomness where deliberate Tile Sampler placement was needed
- Empty albedo that forces the normal to do all the storytelling in a painterly style
- No exposed params (dead-end graph, can’t fit scene variants)

**Domain 2 (ensemble)**
- Cloning reference defaults without regrading to project palette
- “Pretty alone” hero colors that ignore scene hue windows
- Every material with its own dirt hue / edge language
- Clashing temperature or sat vs neighbors
- Detail density or feature scale mismatches in the same shot
- Max heat / max foam / max cracks on everything
- Emissive cosplay on non-emissive worlds
- Skipping ensemble check because “we’ll fix in lighting”
- Treating palette as decoration instead of constraint
- Never testing mats together under target lighting/camera

---

## 9. Integration — one pipeline, two domains

When creating stylized materials in Designer **for a scene**:

1. Load **style bible** (project + scene): palette limits, detail rules, shape language, wear philosophy, hierarchy tier  
2. Emit **design brief** (roles, roughness, frequency plan, donor path, ensemble links)  
3. Author graph (D1 stack A→H) — Level B recipe or Level C clone as topology donor  
4. Regrade colors/response to bible (never ship unmodified donor grade)  
5. **Validate** against project/scene (+ ensemble DNA)  
6. **Register** into scene ensemble  
7. Spot-check with **multiple materials together** under target light/camera  

Parameter exposure + modular construction make families that harmonize by construction.
Final aesthetic success is judged in the **set**, not the solo sphere.

```
D1 craft ──────────────► single mat quality
D2 constraints ─────────► world membership
brief + validate + log ─► production memory
```

---

## 10. How knowledge sources fit together

| Source | Role | Authority |
|--------|------|-----------|
| `knowledge/projects/*.json` | Production art bible, scenes, ensemble, palette DNA | **Primary look** |
| **`domains/*.md`** | Production scope for 3D/game application (reuse, texel, lookdev, non-negotiables) | **Primary production rules** |
| **`design_concepts.md` (this file)** | D1 craft + D2 ensemble theory (Designer) | Primary craft theory |
| Level B recipes | Fast on-brand scaffolds | Build |
| Level C clone | Optional high-fidelity topology donor | Optional donor |
| `playbook.md` / `patterns.json` / `materials.jsonl` | Mined category topology & param names | Optional assist |
| Validation tools | Gatekeeping coherence | Required gate |

**Authority stack:** Project art bible > Domain context > this file > general realtime practice.

MCP: `domain_list` / `domain_get` / `domain_get_section` load `domains/`.
`stylized_design_brief` embeds `production_domain` + `domain_production_checklist` automatically.

Cloning without a bible = costume party.  
Bible without craft = empty rules.  
D1 without D2 = beautiful orphans.  
Domain without bible = generic pipeline cosplay.  
**Bible + Domain + D1 + D2 + validation = a pipeline.**
