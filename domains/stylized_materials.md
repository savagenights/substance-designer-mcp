# Stylized Materials for Video Game Development (3D Model Application)

---

## 0. Meta
| Field                  | Value                                                                |
|------------------------|----------------------------------------------------------------------|
| Domain name            | Stylized Materials for Video Game Development (3D Model Application) |
| Id                     | stylized_materials                                                   |
| Version                | v1.1                                                                 |
| Last verified          | 2026-07-28                                                           |
| Owner                  | savagenights                                                         |
| Consuming AI system(s) | system prompt                                                        |
| Default                | yes                                                                  |
| Aliases                | stylized, stylized_game_materials, game_materials, video_game_materials, 3d_model_materials |
| Categories             | stone_pavement, stone_rock, brick, terracotta, concrete, marble, terrazzo, wood_planks, wood_parquet, wood_generic, water, ground_grass, ground_soil, metal_iron, metal_generic, metal_silver, metal_aluminum, metal_gold, metal_copper, corrupted, scifi, crystal, lava, leather, fabric, fabric_cloth, fabric_carpet, fabric_wool |
| Category prefixes      | stone_, wood_, metal_, ground_, fabric_                              |

---

## 1. Domain Overview

**Description:**  
This domain covers the creation, definition, and application of stylized surface materials (textures, shaders, color treatments, roughness, emission, etc.) that are applied to 3D models for real-time video games. The goal is non-photorealistic materials that reinforce a deliberate artistic style while remaining readable, performant, consistent, and reusable across characters, props, and environments when rendered in a 3D modeling package and later in a game engine.

**Primary objective for AI involvement:**  
Generate, critique, refine, or specify stylized material setups (including texture guidance, shader parameters, map conventions, reuse strategy, and application rules) that match a chosen stylized art direction and work correctly on 3D models inside a real production pipeline.

---

## 2. Scope & Boundaries
**In scope:**
- Material definition and parameterization for stylized looks (base color, roughness, metallic, normal, emission, opacity, custom parameters)
- Texture authoring guidance that supports stylization (hand-painted, procedural, hybrid)
- Map conventions, channel packing, and texel-density standards
- Material reuse architecture (master materials, instances, variants)
- Layering, masking, and vertex-color techniques
- Application of materials onto 3D models (UV considerations, material slots, layering)
- Consistency rules across asset types
- Real-time performance implications and concrete budgets
- Validation / lookdev requirements
- Alignment with overall game art style (shape language support via material treatment)
- Naming, organization, and hand-off conventions

**Explicitly out of scope:**
- Full character or environment modeling
- Animation or rigging
- Photorealistic / PBR-accurate material setups
- Engine-specific implementation details beyond general real-time constraints (unless specified)
- 2D sprite or purely hand-drawn art
- Full lighting and post-process setups (except where they directly interact with material response)

**Applicable jurisdiction/version/edition:**  
General real-time game material practices current as of 2026. Style-specific rules override generic PBR conventions.

---

## 3. Glossary / Terminology
| Term                        | Definition                                                                                                                                          | Aliases / Notes                               |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| Stylized material           | A surface treatment that deliberately departs from physical accuracy to support an artistic style while remaining functional in real-time rendering | Non-photorealistic material, graphic material |
| Shape language support      | How material color, value, and detail reinforce or clarify the underlying 3D forms                                                                  | —                                             |
| Readability                 | Ability of the material to keep the object clear and identifiable under gameplay conditions (distance, motion, varied lighting)                     | —                                             |
| Hand-painted texture        | Texture created primarily through direct painting rather than photographic or purely procedural means                                               | —                                             |
| Material consistency        | Uniform application of stylization rules across all assets so the world feels coherent                                                              | —                                             |
| Graphic treatment           | Intentional simplification or exaggeration of surface response (color blocking, reduced variation, stylized specular, etc.)                         | —                                             |
| PBR                         | Physically Based Rendering — used as a technical baseline but heavily modified or broken for stylization                                            | —                                             |
| Texel density               | The number of texture pixels per unit of world-space surface; must stay consistent within asset classes                                             | —                                             |
| Master material             | The parent shader/material that defines the full parameter set and logic; instances inherit from it                                                 | —                                             |
| Material instance / variant | A lightweight child that overrides specific parameters or maps of a master (clean, dirty, wet, damaged, team-color, etc.)                           | —                                             |
| Channel packing             | Combining multiple grayscale maps into the RGB/A channels of a single texture to save memory and samplers                                           | ORM, ARM, etc.                                |
| Lookdev                     | The process of validating a material under controlled lighting, distance, and motion conditions that approximate final gameplay                     | —                                             |

---

## 4. Key Entities & Relationships
**Entities:**
- `Material` — attributes: base color / albedo, roughness, metallic, normal/bump, emission, opacity, custom parameters, exposed instance parameters
- `Texture Set` — the maps that feed the material (diffuse/albedo, roughness, metallic, normal, packed masks, etc.)
- `Master Material` — the reusable parent that defines shader logic and default parameter ranges
- `Material Instance / Variant` — parameterized children of a master (dirt, wet, damaged, faction, etc.)
- `3D Model` — the geometry the material is applied to (requires clean UVs that meet texel-density targets)
- `Art Direction / Style Guide` — the governing visual rules the material must obey
- `Shader` — the code/graph that interprets the material parameters at render time

**Relationships:**
- A Material (or Instance) is applied to one or more Material slots on a 3D Model
- Texture Sets feed Materials and Masters
- Materials and Instances must conform to the Art Direction
- Shader capabilities and Master Material design constrain what a Material can express
- Variants inherit from Masters and share maps where possible
- Masks, vertex colors, and layer stacks modulate base materials

---

## 5. Governing Rules / Source of Truth
| Source                             | What it governs                                                                       | Authority level           | How to verify currency                          |
|------------------------------------|---------------------------------------------------------------------------------------|---------------------------|-------------------------------------------------|
| Project Style Guide / Art Bible    | Overall stylization rules, color palette, level of detail, material graphic treatment | Primary                   | Check latest version in project documentation   |
| This Domain Context                | Material-specific principles, technical conventions, and constraints                  | Primary for material work | Version number above                            |
| Real-time rendering best practices | Performance and technical limits                                                      | Secondary                 | Engine documentation / current hardware targets |
| Canonical reference games          | Successful examples of stylized materials                                             | Secondary / inspirational | Visual inspection of current shipping titles    |

**Conflict resolution rule:**  
Project Style Guide > this Domain Context > general real-time best practices. If a request conflicts with readability, consistency, or established technical conventions, flag it rather than silently break the style or pipeline.

---

## 6. Roles & Stakeholders
| Role                      | Goals                                                                                          | Permissions / limits                                                               |
|---------------------------|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| Art Director              | Maintain visual coherence and quality bar                                                      | Can override material decisions                                                    |
| Material / Texture Artist | Create and refine materials and texture sets                                                   | Primary creator                                                                    |
| 3D Artist / Modeler       | Apply materials cleanly to models and meet texel-density targets                               | Needs clear material instructions and density standards                            |
| Technical Artist          | Ensure performance, shader compatibility, master-material design, and packing conventions      | Can reject non-performant or non-compliant setups                                  |
| AI Assistant              | Generate, critique, or iterate material descriptions, parameters, and pipeline-compliant specs | Must stay within style, technical conventions, and reuse rules; escalate conflicts |

---

## 7. Standard Workflows

**Workflow: Define a new stylized material**
1. Confirm the target art style and any existing material examples or masters.
2. Determine the material’s role (character skin, cloth, metal, organic, hard-surface, etc.) and whether it should be a new Master or an Instance of an existing one.
3. Establish base color / value hierarchy and graphic treatment level.
4. Specify texture approach (hand-painted, procedural, hybrid), required maps, and packing scheme.
5. Define shader parameters that support the style (stylized roughness response, custom fresnel, limited variation, etc.) and which parameters are exposed for instancing.
6. Set texel-density target for the intended asset class.
7. Note application requirements (UV density, material slots, layering, vertex-color usage).
8. Plan expected variants (clean / dirty / wet / damaged / team-color) and how they will share maps.
9. Validate against readability, consistency, performance budgets, and naming conventions.

**Inputs required:** Style reference, object type, existing material library / master list, target platform budget  
**Output produced:** Clear material specification (description + parameter guidance + texture notes + reuse strategy + validation notes)  
**Human checkpoint:** Art Director or Material Artist + Technical Artist review before final implementation

**Workflow: Critique an existing material on a 3D model**
1. Evaluate silhouette and form support.
2. Check value and color hierarchy under neutral and varied lighting.
3. Assess consistency with the rest of the asset library and with any parent Master.
4. Verify texel density against project standards.
5. Check map conventions, packing, and whether variants could share more data.
6. Identify any readability, performance, or pipeline issues.
7. Propose specific, actionable improvements prioritized by impact.

**Inputs required:** Description or images of the material + model, style reference, current technical conventions  
**Output produced:** Structured critique + prioritized fix list  
**Human checkpoint:** None required for critique; implementation needs human approval

**Workflow: Create or extend a material variant**
1. Confirm the parent Master exists and is approved.
2. Override only the necessary parameters or maps.
3. Re-use existing textures wherever possible.
4. Validate the variant under the same lookdev conditions as the parent.
5. Update naming and documentation so the relationship is clear.

---

## 8. Constraints & Non-Negotiables
- Materials must never sacrifice silhouette readability or form clarity for surface detail.
- Stylization level must stay consistent across the project — no mixing high-frequency realistic detail with graphic simplification unless explicitly part of the style.
- All materials must remain viable in real-time (texture sizes, sampler counts, and shader complexity must respect published budgets).
- Do not default to photorealistic PBR responses; break physical accuracy deliberately when it serves the style.
- Never invent style rules that contradict the project’s established art direction.
- Prefer Master + Instance architecture over unique one-off materials.
- Texel density must stay within the approved range for the asset class.
- Maps must follow the project’s packing and naming conventions.
- Flag any request that would create inconsistency, break readability, or violate technical conventions.

**Technical Conventions (default starting points — override only with explicit project approval):**
- Texel density targets are defined per asset class (hero / character / prop / environment / distant) and must be measured and met.
- Preferred packing: combine grayscale data (roughness, metallic, ambient occlusion / cavity, etc.) into single textures to minimize samplers.
- Master materials expose a controlled set of parameters; artists and AI should prefer instancing over duplicating masters.
- Vertex color and mask layers are first-class tools for variation and should be used before creating additional unique textures.
- Materials must be authored and reviewed against the project’s actual lighting model, not only against a default PBR viewport.

---

## 9. Edge Cases & Exceptions
| Situation                                              | Why it's different                                     | Correct handling                                                                                                          |
|--------------------------------------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| Hero / unique asset                                    | Higher detail budget and more custom treatment allowed | Still obey overall style language and texel-density rules; document the exception and any unique master                   |
| Distant / background assets                            | Extreme simplification required                        | Reduce texture resolution, variation, and shader features aggressively while preserving silhouette; prefer shared atlases |
| Animated / deforming surfaces                          | Material must hold up under deformation                | Avoid high-frequency detail that breaks or swims; test under animation                                                    |
| Transparent or emissive materials                      | Special readability and overdraw concerns              | Prioritize clarity of underlying form, control bloom/overdraw, and respect transparency sorting budgets                   |
| Style that intentionally mixes realism and stylization | Hybrid rules apply                                     | Follow the specific hybrid guidelines in the style guide; do not invent the mix                                           |
| New material type with no existing Master              | Requires new parent                                    | Create the Master first, get Technical Artist sign-off, then generate instances                                           |

---

## 10. Output / Formatting Expectations
- Format: Clear structured prose or bullet points. Use parameter lists or simple tables when specifying material settings.
- Required fields or sections:  
  – Purpose / role of the material  
  – Key visual goals (what it should communicate)  
  – Base color / value approach  
  – Texture guidance (maps required, packing, hand-painted vs procedural notes)  
  – Shader / parameter notes (including which parameters are exposed for instancing)  
  – Reuse & variant strategy (Master vs Instance, expected variants, shared maps)  
  – Texel-density target and UV notes  
  – Application notes (slots, layering, vertex color)  
  – Performance notes against project budgets  
  – Consistency & readability checks  
  – Validation / lookdev requirements  
  – Naming suggestion following project conventions
- Citation/sourcing requirements: Reference the style guide, specific example assets, or existing Masters when making claims.
- Tone/register: Precise, practical, and production-aware. Avoid vague aesthetic language (“make it pretty”). Prefer actionable statements.

---

## 11. Success Criteria
- Materials clearly support the intended stylized art direction.
- Objects remain readable in silhouette and form under typical gameplay viewing conditions.
- Visual language stays consistent with the rest of the project’s material library.
- Specifications are specific enough that a material artist can implement them without guesswork.
- Materials follow Master/Instance reuse patterns and map-sharing rules where possible.
- Texel density, packing, and naming conventions are respected.
- Performance impact is within published budgets for the target platforms.
- Materials pass a defined lookdev checklist (neutral light, extreme light, distance, motion, project lighting model).
- Critiques correctly identify real problems (readability, consistency, style drift, pipeline violations) rather than subjective taste.

---

## 12. Versioning & Maintenance
- Review cadence: Re-check against project style guide and technical budgets at the start of each major art milestone or when new reference games or engine versions significantly influence the direction.
- Change log:

| Date       | Change                                                                                                                                                                                          | By |
|------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----|
| 2026-07-28 | Initial version created                                                                                                                                                                         |    |
| 2026-07-28 | v1.1 — Added texel density, material reuse/variants, map conventions, lookdev validation, layering/vertex color, concrete performance language, naming/hand-off, and lighting-model interaction |    |