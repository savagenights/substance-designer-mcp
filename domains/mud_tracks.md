# Mud Tracks Domain: Medieval Fantasy Courtyard Ground (3D Game Application)

**Domain ID**: `mud_tracks`  
**Version**: v1.0  
**Owner**: savagenights  
**Last Updated**: 2026-08-01  
**Parent Domain**: stylized_materials  
**Scope**: Medieval fantasy ground materials with mud/soil/clay characteristics for courtyard and path surfaces

## Metadata

| Field | Value |
|-------|-------|
| **Domain ID** | `mud_tracks` |
| **Version** | v1.0 |
| **Owner** | savagenights |
| **Last Updated** | 2026-08-01 |
| **Parent Domain** | stylized_materials |

## 0. Overview

Mud tracks domain defines the **visual grammar** for worn, wet, or compacted dirt surfaces in medieval fantasy environments. Focuses on:
- **Contact logic**: Horse hooves, foot traffic, rain runoff patterns
- **Moisture states**: Wet patches, dry dust edges, clay-hardened rims
- **Wear hierarchy**: Center of tracks (packed) vs edges (loose debris)
- **Shared dirt language**: Must harmonize with courtyard stone/wood/metal ensemble

**NOT FOR**: Photoreal soil sims, tropical rainforest mud, or magical emissive swamps (those belong in other domains).

---

## 1. Scope & Boundaries

### In Scope:
- Medieval courtyard ground with animal/foot traffic patterns
- Muddy paths leading to gates/barns/forges
- Wet clay edges around cobblestone borders
- Scattered debris (pebbles, twigs, straw) in natural decay
- Seasonal transitions: rain-washed mud → drying crust

### Out of Scope:
- Swamp/water-emissive materials (use water/lava domains)
- Tropical jungle mud (wrong color language)
- Magical corruption/acidic ground (use corrupted domain)
- Snow-mud slush mix (requires separate snow domain)

---

## 2. Production Constraints

### Non-Negotiables:
1. **Silhouette first**: Mud tracks must read as "dark wet paths" in grayscale; don't overdo HF texture that kills form clarity
2. **Shared dirt DNA**: Must use `shared_dirt` (RGB 0.16,0.14,0.11) or `joint_dirt` (RGB 0.16,0.15,0.13) from courtyard palette
3. **Moisture coherence**: Roughness matches scene wetness (keep_courtyard_overcast = slightly damp, not waterlogged)
4. **Master + Instance only**: Create parameterized masters (`wet/dry/clean/damaged`) rather than unique variants
5. **Fewer-and-larger frequency**: No photoreal pore soup; mid-freq mud clumps, high freq restrained

### Technical:
- **Texel density**: Environment class (hero props: 12-16 tex/cm², world: 8-12 tex/cm²)
- **Channel packing**: Grayscale maps (roughness/metallic/height variants) shared across courtyard ground family
- **Master architecture**: Expose params: `primary/secondary/shadow` colors, `wetness_intensity`, `track_depth`, `debris_amount`, `roughness_base`

---

## 3. Standard Workflows

### Define a New Mud Material (5 Steps):
1. **Confirm context**: Is this for courtyard ground? Path leading to forge? Gate area? Set project/scene active.
2. **Read authority**: Art bible palette > Domain constraints > Realtime practice. Validate against `keep_courtyard_overcast` mood (overcast, muted, damp stone).
3. **Topology donor**: Clone from `corrupted_dirt_ground` (best mud topology) or build height-first with `tile_generator` for track patterns.
4. **Apply art bible colors**: Use brief's suggested palette roles; never use donor defaults without color validation.
5. **Expose & validate**: Set exposed params for scene variants; run `validate_material_against_project`; register to ensemble on pass.

### Critique Existing Material (7 Steps):
1. Check silhouette in grayscale: Do tracks read as dark paths or muddy blobs?
2. Validate palette against bible: Are hues within courtyard window? Is shared_dirt used correctly?
3. Inspect frequency plan: Too much HF noise? Kill high-freq details.
4. Verify moisture coherence: Does roughness match overcast damp scene mood?
5. Test beside ensemble: Place next to `FABL_FORGE_stylized_medieval_cobblestone`; do they share dirt language?
6. Check master/instance: Is this parameterized for wet/dry/clean variants, or a unique one-off?
7. Evaluate performance: Texture size/sampler count within environment budget?

### Create Variant (3 Steps):
1. Duplicate master; only change exposed params (wetness_intensity, debris_amount, track_depth).
2. Validate against project bible with new params; fix hue/roughness drift if needed.
3. Register variant to scene ensemble if it fits hierarchy tier (world/secondary surface).

---

## 4. Success Criteria

 **Silhouette**: Mud tracks read as dark, wet paths in grayscale view  
 **Shared DNA**: Uses courtyard dirt/shadow colors; no new grunge dialect invented  
 **Moisture match**: Roughness coherent with overcast damp scene (not tropical wet or bone-dry)  
 **Master reuse**: Parameterized variants ready for instancing across courtyard paths  
 **Frequency plan**: Fewer-and-larger detail density; HF restrained  
 **Validation pass**: `validate_material_against_project` returns pass/warn (not fail); no hue/sat/window breaks  
 **Performance**: Within environment class texture budgets; grayscale maps packed where possible  

---

## 5. Do / Don't Guide

### DO:
- Reuse shared_dirt / joint_dirt across courtyard ground family
- Prefer cool greystone over warm tan for keep exteriors (matches bible)
- Keep foam/emissive as accents only (no swamp glow unless scene allows)
- Author height-first: Block macro structure in grayscale before sculpting color zones
- Expose wetness/depth/debris params for instance variants
- Test new mats beside `FABL_FORGE_stylized_medieval_cobblestone` under courtyard lighting

### DON'T:
- Invent tropical teal or high-sat green hues (wrong mood)
- Add random emissive sparkles on mundane mud (save for forge/fire)
- Default to photorealistic pore noise; keep stylized blocky forms
- Create shiny plastic roughness profiles (keep matte used-soil look)
- Mix wet-coastal grade with dry-interior scenes without explicit approval
- Use unique one-off variants; prefer master+instance architecture

---

## 6. Example Material Spec

```yaml
material_id: FABL_FORGE_courtyard_mud_tracks
category: ground_soil
roles:
  primary:   [0.42, 0.40, 0.37]  # courtyard_stone base (muted)
  secondary: [0.30, 0.34, 0.28]  # moss_patch undertone (desat)
  shadow:    [0.16, 0.15, 0.13]  # joint_dirt for track edges
  highlight: [0.58, 0.56, 0.50]  # limestone_kiss on worn clay rims
  dirt:      [0.16, 0.14, 0.11]  # shared_dirt (mandatory)
roughness_base: 0.835
wetness_intensity: 0.4  # exposed param (0-1; higher = wetter)
track_depth: 0.2       # exposed param (controls depth of darkened paths)
debris_amount: 0.15    # exposed param (scattered pebbles/twigs)
```

---

## 7. Authority Stack

1. **Project Style Guide / Art Bible** (`knowledge/projects/fabl_forge/*.md`) — PRIMARY LOOK lock
2. **Domain Context** (`domains/mud_tracks.md`) — Production scope, reuse rules, validation contract
3. **Designer Craft Concepts** (`design_concepts.md`) — D1 authoring + D2 ensemble grammar
4. **Realtime Best Practices** — Secondary technical limits (texel density, packing)

---

## 8. Glossary

- **Shared dirt**: The `#29241C` color used in joints/gaps/edges across courtyard materials
- **Master + Instance**: One param-rich base material + reusable variants; NOT unique textures
- **Silhouette readability**: Material reads clearly in grayscale; no HF noise breaking form
- **Fewer-and-larger**: Detail density philosophy (low/mid freq dominant; high freq minimal)
