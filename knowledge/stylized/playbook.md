# Stylized SBS — Design Playbook

Mined from the local stylized material reference library.
Use this when building **stylized** (not photoreal) Substance graphs.

- Total materials: **637**
- Categories: **30**

## Global stylized signature

Stylized graphs in the reference corpus share a visual grammar:

1. **Shape first** — clear readable forms (tiles, planks, cells, waves) via `tile_generator` / pattern nodes / simple geometry, NOT noisy photo breakup.
2. **Stylized color blocks** — few solid-ish color zones with HSL nudges; avoid micro-photo albedo noise.
3. **Soft sculpted height** — directional warps + non-uniform / slope blur for painterly relief; normals from height.
4. **Brush / material filters** — `ad_brush_stroke_generator`, `ad_material_filter`, `st_wood_fiber_generator` etc. push the hand-painted look.
5. **Histogram shaping** — `histogram_scan` / `histogram_select` / `levels` carve clean masks for layering.
6. **Blend stacks** — many `blend` nodes layer dirt, edge wear, color variation, AO.
7. **PBR finish** — roughness/metallic as simple maps; HBAO; pbr_converter outputs.

### Atomic nodes you will over-use

| Node | Role in stylized |
|------|------------------|
| blend | Layer masks, color, dirt, edges |
| levels | Remap masks/height into clean ranges |
| directionalwarp | Painterly distortion of shapes |
| hsl | Stylized hue/sat/value grading |
| uniform | Flat color bases |
| normal | Height → normal |
| warp / slope_blur | Organic flow on height |

### Library nodes that scream stylized

- `tile_generator` / `pattern_tile_generator` — structure
- `histogram_scan` / `histogram_select` / `auto_levels` — mask craft
- `non_uniform_blur_grayscale` / `blur_hq_grayscale` / `slope_blur_grayscale_2`
- `hbao_2` + `pbr_converter` — finish
- `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`
- `st_wood_fiber_generator`, `st_surfacing_filter`, `st_trimming_filter`

## Per-category recipes

### `marble`  (239 materials)

- avg nodes **129.5** · blends **19.1** · levels **13.9** · hsl **2.8** · warps **6.0**
- patterns: `directional_warp_detail`×239, `heavy_blend_stack`×239, `levels_remapping`×239, `hsl_color_styling`×239, `histogram_shape_control`×239, `slope_blur_flow`×239, `pbr_converter_outputs`×239, `height_to_normal`×239
- top filters: `blend`×4574, `levels`×3312, `uniform`×2243, `directionalwarp`×1185, `hsl`×678, `normal`×479, `distance`×476, `pixelprocessor`×391
- top instances: `switch_grayscale`×1824, `non_uniform_blur_grayscale`×1684, `safe_transform_grayscale`×1290, `invert_grayscale`×1069, `blur_hq_grayscale`×855, `tile_generator`×754, `histogram_range`×698, `histogram_scan`×584
- specialty filters: `st_stylized_look_filter`, `st_surfacing_filter`, `st_cracks_filter`, `st_trimming_filter`, `st_cuts_filter`
- color params: `channel_basecolor`, `hue_shift`, `veins_color`, `veins_color_intensity`, `stain_color`, `stain_color_intensity`, `marble_color_variation_intensity`, `large_break_color`
- examples: `stylized_antique_white_marble`, `stylized_antique_white_marble_alternating_tiles`, `stylized_antique_white_marble_argyle_tiles`, `stylized_antique_white_marble_diamond_tiles`, `stylized_antique_white_marble_fan_tiles`, `stylized_antique_white_marble_flemish_tiles`, `stylized_antique_white_marble_fluted_column`, `stylized_antique_white_marble_grid_tiles`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `stone_pavement`  (51 materials)

- avg nodes **146.1** · blends **38.5** · levels **13.2** · hsl **8.3** · warps **1.6**
- patterns: `heavy_blend_stack`×51, `hsl_color_styling`×51, `histogram_shape_control`×51, `pbr_converter_outputs`×51, `height_to_normal`×51, `levels_remapping`×49, `hbao_occlusion`×49, `tile_pattern_structure`×48
- top filters: `blend`×1966, `levels`×672, `hsl`×421, `uniform`×359, `passthrough`×302, `blur`×296, `transformation`×104, `normal`×104
- top instances: `histogram_scan`×219, `shadows`×188, `histogram_select`×158, `tile_generator`×109, `histogram_range`×105, `st_surfacing_filter`×100, `auto_levels`×99, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×90
- specialty filters: `st_surfacing_filter`, `st_trimming_filter`, `st_stylized_light_shadow`, `st_cracks_filter`, `st_height_variations_filter`, `st_cuts_filter`, `st_stylized_look_filter`, `st_pattern_filter`
- color params: `hue_shift`, `channel_basecolor`, `base_color`, `impact_color`, `second_color_intensity`, `second_color`, `dirt_color`, `shadow_color`
- examples: `stone_pavement_mossy_stylized`, `stylized_cobblestone_pavement`, `stylized_concrete_arcpaver_pavement`, `stylized_concrete_chevron_pavement`, `stylized_concrete_fanpaver_pavement`, `stylized_concrete_fish_scale_pavement`, `stylized_concrete_half_basket_weave_pavement`, `stylized_concrete_herringbone_pavement`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `wood_planks`  (37 materials)

- avg nodes **143.6** · blends **26.4** · levels **9.3** · hsl **4.4** · warps **5.9**
- patterns: `histogram_shape_control`×37, `pbr_converter_outputs`×37, `height_to_normal`×37, `directional_warp_detail`×36, `hbao_occlusion`×36, `warp_distortion`×36, `levels_remapping`×34, `hsl_color_styling`×32
- top filters: `blend`×978, `passthrough`×812, `levels`×343, `directionalwarp`×203, `hsl`×163, `uniform`×157, `transformation`×119, `blur`×103
- top instances: `invert_grayscale`×127, `histogram_select`×119, `histogram_scan`×117, `blur_hq_grayscale`×98, `auto_levels`×97, `tile_generator`×85, `safe_transform_grayscale`×80, `slope_blur_grayscale_2`×77
- specialty filters: `st_cuts_filter`, `st_stylized_look_filter`, `st_trimming_filter`, `st_wood_fiber_generator`, `st_mixing_filter`, `st_stylized_light_shadow`, `st_paint_filter`, `st_parquet_splatter`
- color params: `channel_basecolor`, `hue_shift`, `wood_color`, `shadow_color`, `wood_secondary_color`, `wood_secondary_color_intensity`, `wood_color_variation`, `wood_color_variation_intensity`
- examples: `corrupted_wood_bark`, `stylized_apple_tree_bark`, `stylized_barkless_pine_wood`, `stylized_corrupted_apple_tree_bark`, `stylized_corrupted_pine_tree_bark`, `stylized_cracked_wood_planks`, `stylized_damaged_painted_wood_planks_with_chassis`, `stylized_damaged_painted_wood_planks_with_reinforced_chassis`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `stone_rock`  (33 materials)

- avg nodes **145.8** · blends **28.9** · levels **8.1** · hsl **4.9** · warps **5.0**
- patterns: `histogram_shape_control`×33, `pbr_converter_outputs`×33, `height_to_normal`×33, `heavy_blend_stack`×30, `tile_pattern_structure`×30, `hbao_occlusion`×30, `slope_blur_flow`×28, `warp_distortion`×27
- top filters: `blend`×953, `levels`×266, `passthrough`×179, `transformation`×167, `hsl`×162, `uniform`×158, `curve`×141, `directionalwarp`×116
- top instances: `blur_hq_grayscale`×176, `slope_blur_grayscale_2`×127, `auto_levels`×115, `histogram_scan`×113, `invert_grayscale`×105, `tile_generator`×96, `histogram_select`×90, `histogram_range`×87
- specialty filters: `ad_brush_stroke_generator`, `ad_material_filter`, `st_pebbles_filter`, `st_stylized_look_filter`, `st_sand`, `st_cracks_filter`, `st_surfacing_filter`, `st_noise_to_grayscale_filter`
- color params: `channel_basecolor`, `hue_shift`, `base_color`, `color_base_variation`, `top_color`, `top_edge_color`, `bottom_color`, `cavity_color`
- examples: `corrupted_cliff`, `corrupted_fragmented_rock`, `corrupted_lava_rock`, `corrupted_rocks`, `corrupted_stone_floor`, `stylized_barnacle_covered_rock`, `stylized_basalt_rock`, `stylized_blocky_stone_cliff`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `wood_parquet`  (32 materials)

- avg nodes **97.6** · blends **10.9** · levels **8.9** · hsl **3.9** · warps **2.3**
- patterns: `directional_warp_detail`×32, `levels_remapping`×32, `hsl_color_styling`×32, `histogram_shape_control`×32, `wood_fiber_stylization`×32, `hbao_occlusion`×32, `pbr_converter_outputs`×32, `height_to_normal`×32
- top filters: `passthrough`×709, `blend`×350, `levels`×284, `hsl`×124, `uniform`×111, `blur`×88, `normal`×78, `directionalwarp`×59
- top instances: `histogram_scan`×85, `histogram_select`×59, `curvature_smooth`×55, `safe_transform_grayscale`×54, `tile_generator`×52, `auto_levels`×37, `invert_grayscale`×33, `histogram_range`×32
- specialty filters: `st_cuts_filter`, `st_parquet_splatter`, `st_stylized_look_filter`, `st_trimming_filter`, `st_wood_fiber_generator`, `st_height_variations_filter`, `st_stylized_light_shadow`, `st_surfacing_filter`
- color params: `wood_color`, `channel_basecolor`, `hue_shift`, `highlight_intensity_color`, `wood_color_variation`, `wood_color_variation_intensity`, `shadow_color`, `wood_secondary_color_intensity`
- examples: `stylized_aremberg_wood_parquet`, `stylized_chalosse_wood_parquet`, `stylized_chantilly_wood_parquet`, `stylized_damaged_wood_basket_parquet`, `stylized_damaged_wood_cambridge_parquet`, `stylized_damaged_wood_checkerboard_parquet`, `stylized_damaged_wood_echelle_parquet`, `stylized_damaged_wood_herringbone_parquet`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `terrazzo`  (28 materials)

- avg nodes **147.0** · blends **30.2** · levels **17.5** · hsl **2.0** · warps **5.0**
- patterns: `directional_warp_detail`×28, `heavy_blend_stack`×28, `levels_remapping`×28, `hsl_color_styling`×28, `histogram_shape_control`×28, `tile_pattern_structure`×28, `wood_fiber_stylization`×28, `non_uniform_blur`×28
- top filters: `blend`×846, `levels`×490, `uniform`×364, `directionalwarp`×112, `normal`×56, `hsl`×56, `distance`×56, `curve`×54
- top instances: `blur_hq_grayscale`×180, `histogram_range`×143, `non_uniform_blur_grayscale`×138, `safe_transform_grayscale`×124, `invert_grayscale`×112, `tile_generator`×92, `clouds_2`×82, `edge_detect`×70
- specialty filters: `st_stylized_look_filter`, `st_surfacing_filter`
- color params: `color_selection`, `terrazzo_color_1`, `terrazzo_color_1_intensity`, `terrazzo_color_2`, `terrazzo_color_2_intensity`, `terrazzo_color_3`, `terrazzo_color_3_intensity`, `terrazzo_inner_color`
- examples: `stylized_large_terrazzo`, `stylized_large_terrazzo_alternating_tiles`, `stylized_large_terrazzo_argyle_tiles`, `stylized_large_terrazzo_diamond_tiles`, `stylized_large_terrazzo_fan_tiles`, `stylized_large_terrazzo_flemish_tiles`, `stylized_large_terrazzo_grid_tiles`, `stylized_large_terrazzo_herringbone_tiles`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `metal_generic`  (24 materials)

- avg nodes **80.8** · blends **14.3** · levels **6.7** · hsl **2.4** · warps **2.1**
- patterns: `histogram_shape_control`×24, `pbr_converter_outputs`×24, `height_to_normal`×24, `tile_pattern_structure`×22, `hbao_occlusion`×21, `warp_distortion`×18, `directional_warp_detail`×17, `levels_remapping`×16
- top filters: `blend`×343, `levels`×160, `transformation`×105, `uniform`×93, `hsl`×57, `normal`×50, `passthrough`×47, `directionalwarp`×46
- top instances: `tile_generator`×59, `histogram_scan`×50, `blur_hq_grayscale`×48, `histogram_range`×48, `slope_blur_grayscale_2`×38, `invert_grayscale`×37, `auto_levels`×33, `safe_transform_grayscale`×25
- specialty filters: `st_stylized_look_filter`, `st_trimming_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `st_cuts_filter`, `st_surfacing_filter`, `ad_incandescent_filter`, `ad_pattern_effect_filter`
- color params: `channel_basecolor`, `hue_shift`, `metal_color`, `color`, `color_variation_1`, `color_variation_2`, `shadow_color`, `corruption_color`
- examples: `corrupted_damaged_hammered_metal`, `corrupted_damaged_metal`, `corrupted_metal`, `corrupted_structured_metal`, `stylized_ancient_chinese_armor`, `stylized_ancient_metal_tiles`, `stylized_cable_knit_wool`, `stylized_casting_melted_metal`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `misc`  (20 materials)

- avg nodes **278.4** · blends **68.7** · levels **6.4** · hsl **6.8** · warps **9.2**
- patterns: `histogram_shape_control`×20, `pbr_converter_outputs`×20, `height_to_normal`×20, `hbao_occlusion`×19, `directional_warp_detail`×16, `tile_pattern_structure`×16, `warp_distortion`×16, `heavy_blend_stack`×14
- top filters: `blend`×1374, `passthrough`×753, `transformation`×233, `directionalwarp`×160, `hsl`×135, `uniform`×129, `levels`×128, `blur`×122
- top instances: `histogram_scan`×164, `invert_grayscale`×150, `histogram_select`×128, `blur_hq_grayscale`×120, `histogram_range`×109, `tile_generator`×108, `auto_levels`×95, `safe_transform_grayscale`×71
- specialty filters: `ad_brush_stroke_generator`, `ad_material_filter`, `st_noise_to_grayscale_filter`, `st_impact_filter`, `st_stylized_look_filter`, `st_height_variations_filter`, `st_surfacing_filter`, `st_trimming_filter`
- color params: `channel_basecolor`, `hue_shift`, `wood_color`, `clay_color`, `add_color_base_variation`, `color_base_variation_intensity`, `color_base_variation`, `color_sharpen`
- examples: `shield_slate_tile_stylized`, `stylized_clay_mold`, `stylized_damaged_tree_trunk_cross_section`, `stylized_glass_window`, `stylized_inca_temple_wall`, `stylized_lava_cracked`, `stylized_light_bulb_screw_base`, `stylized_modelling_clay`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `metal_copper`  (20 materials)

- avg nodes **236.2** · blends **58.5** · levels **24.1** · hsl **10.0** · warps **3.1**
- patterns: `histogram_shape_control`×20, `tile_pattern_structure`×20, `non_uniform_blur`×20, `hbao_occlusion`×20, `pbr_converter_outputs`×20, `height_to_normal`×20, `warp_distortion`×20, `heavy_blend_stack`×19
- top filters: `blend`×1170, `passthrough`×786, `levels`×482, `uniform`×256, `hsl`×200, `blur`×86, `transformation`×64, `normal`×50
- top instances: `shadows`×124, `non_uniform_blur_grayscale`×124, `quantize_grayscale`×114, `safe_transform_grayscale`×103, `histogram_select`×92, `histogram_range`×52, `blur_hq_grayscale`×43, `histogram_scan`×43
- specialty filters: `st_stylized_look_filter`, `st_surfacing_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`, `ad_rust_filter`, `st_cuts_filter`, `st_pattern_filter`
- color params: `channel_basecolor`, `hue_shift`, `base_color`, `second_color_intensity`, `second_color`, `highlight_color`, `impact_color`, `scratches_color`
- examples: `stylized_battered_copper`, `stylized_cast_copper`, `stylized_clean_copper_wall_panel`, `stylized_copper`, `stylized_damaged_battered_copper`, `stylized_damaged_copper`, `stylized_damaged_grinded_copper`, `stylized_damaged_hammered_copper`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `terracotta`  (20 materials)

- avg nodes **122.3** · blends **24.9** · levels **8.8** · hsl **4.8** · warps **4.2**
- patterns: `histogram_shape_control`×20, `pbr_converter_outputs`×20, `height_to_normal`×20, `non_uniform_blur`×19, `slope_blur_flow`×19, `tile_pattern_structure`×18, `warp_distortion`×18, `directional_warp_detail`×17
- top filters: `blend`×498, `levels`×175, `uniform`×129, `passthrough`×112, `hsl`×95, `directionalwarp`×78, `normal`×54, `transformation`×52
- top instances: `blur_hq_grayscale`×83, `histogram_scan`×52, `invert_grayscale`×48, `slope_blur_grayscale_2`×46, `histogram_select`×46, `tile_generator`×42, `safe_transform_grayscale`×41, `histogram_range`×37
- specialty filters: `st_cuts_filter`, `st_stylized_look_filter`, `st_trimming_filter`, `ad_brush_stroke_generator`, `ad_impact_filter`, `ad_material_filter`, `ad_pattern_effect_filter`, `st_surfacing_filter`
- color params: `channel_basecolor`, `hue_shift`, `plaster_color`, `color`, `color_variation`, `shadow_color`, `plaster_second_color_intensity`, `plaster_second_color`
- examples: `stylized_brushed_ceramic`, `stylized_chinese_plaster`, `stylized_damaged_terracotta`, `stylized_damaged_terracotta_stretcher_bond`, `stylized_endshake_terracotta_roof_tiles`, `stylized_fish_scale_terracotta_roof_tiles`, `stylized_flat_terracotta_roof_tiles`, `stylized_flower_ceramic`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `metal_iron`  (18 materials)

- avg nodes **165.3** · blends **34.6** · levels **13.1** · hsl **6.1** · warps **3.2**
- patterns: `histogram_shape_control`×18, `non_uniform_blur`×18, `hbao_occlusion`×18, `pbr_converter_outputs`×18, `height_to_normal`×18, `levels_remapping`×17, `hsl_color_styling`×17, `tile_pattern_structure`×16
- top filters: `blend`×623, `passthrough`×435, `levels`×236, `uniform`×132, `hsl`×110, `normal`×57, `blur`×50, `transformation`×40
- top instances: `histogram_select`×89, `safe_transform_grayscale`×75, `non_uniform_blur_grayscale`×73, `histogram_scan`×71, `quantize_grayscale`×70, `histogram_range`×51, `tile_generator`×44, `shadows`×42
- specialty filters: `st_stylized_look_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`, `ad_rust_filter`, `ad_top_bottom_filter`, `ad_impact_filter`, `st_noise_to_grayscale_filter`
- color params: `channel_basecolor`, `hue_shift`, `base_color`, `second_color`, `highlight_color`, `second_color_intensity`, `impact_color`, `scratches_color`
- examples: `stylized_battered_iron`, `stylized_cast_iron`, `stylized_damaged_battered_iron`, `stylized_damaged_grinded_iron`, `stylized_damaged_iron`, `stylized_galvanized_steel`, `stylized_grinded_iron`, `stylized_hammered_cast_iron`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `scifi`  (17 materials)

- avg nodes **93.1** · blends **24.8** · levels **4.8** · hsl **1.0** · warps **0.1**
- patterns: `histogram_shape_control`×17, `hbao_occlusion`×17, `pbr_converter_outputs`×17, `height_to_normal`×17, `heavy_blend_stack`×14, `tile_pattern_structure`×14, `levels_remapping`×9, `edge_detect_ridges`×6
- top filters: `blend`×422, `transformation`×228, `levels`×81, `uniform`×59, `dirmotionblur`×33, `distance`×20, `normal`×17, `hsl`×17
- top instances: `histogram_scan`×125, `bevel`×63, `mirror_grayscale`×53, `invert_grayscale`×52, `tile_generator`×46, `shape`×35, `histogram_range`×17, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×17
- color params: `shadow_color`, `metal_color`, `channel_basecolor`, `hue_shift`, `first_stroke_color`, `second_stroke_color`, `metal_color_opacity`, `third_stroke_color`
- examples: `stylized_scifi_area_lock`, `stylized_scifi_corridor_structure`, `stylized_scifi_damaged_assembly`, `stylized_scifi_damaged_vent`, `stylized_scifi_exhaust_vent`, `stylized_scifi_factory_floor`, `stylized_scifi_factory_wall`, `stylized_scifi_floor_panel`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `wood_generic`  (14 materials)

- avg nodes **206.4** · blends **39.2** · levels **13.0** · hsl **4.6** · warps **5.7**
- patterns: `histogram_shape_control`×14, `pbr_converter_outputs`×14, `height_to_normal`×14, `levels_remapping`×13, `hbao_occlusion`×13, `directional_warp_detail`×12, `heavy_blend_stack`×12, `tile_pattern_structure`×12
- top filters: `passthrough`×576, `blend`×549, `levels`×182, `transformation`×112, `uniform`×97, `directionalwarp`×79, `hsl`×64, `curve`×47
- top instances: `blur_hq_grayscale`×102, `tile_generator`×62, `invert_grayscale`×58, `histogram_select`×55, `histogram_scan`×48, `histogram_range`×39, `shape`×39, `slope_blur_grayscale_2`×34
- specialty filters: `ad_brush_stroke_generator`, `ad_impact_filter`, `ad_material_filter`, `st_noise_to_grayscale_filter`, `ad_pattern_height_distribution`, `ad_knotty_wood_generator`, `ad_worn_wood_generator`, `ad_old_wood_generator`
- color params: `channel_basecolor`, `hue_shift`, `wood_color`, `highlight_color`, `shadow_color`, `pattern_color`, `wood_secondary_color_intensity`, `wood_secondary_color`
- examples: `corrupted_rotten_wood_01`, `stylized_damaged_rounded_wood_roof_tiles`, `stylized_damaged_squared_wood_roof_tiles`, `stylized_ocean_spray_swept_wood`, `stylized_old_rounded_wood_roof_tiles`, `stylized_pier_wood_pillar`, `stylized_pirate_ship_wood_trim_sheet`, `stylized_reclaimed_rounded_wood_roof_tiles`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `ground_grass`  (12 materials)

- avg nodes **90.7** · blends **14.0** · levels **6.4** · hsl **3.8** · warps **4.0**
- patterns: `histogram_shape_control`×12, `tile_pattern_structure`×12, `pbr_converter_outputs`×12, `height_to_normal`×12, `warp_distortion`×12, `directional_warp_detail`×11, `hsl_color_styling`×10, `non_uniform_blur`×10
- top filters: `blend`×168, `levels`×77, `transformation`×53, `hsl`×45, `uniform`×40, `normal`×29, `directionalwarp`×27, `warp`×21
- top instances: `blur_hq_grayscale`×57, `histogram_select`×36, `histogram_range`×27, `auto_levels`×26, `tile_generator`×23, `shape`×22, `height_blend`×22, `gaussian_noise`×20
- specialty filters: `st_stylized_look_filter`, `ad_brush_stroke_generator`, `ad_grass_filter`, `ad_material_filter`, `st_trimming_filter`, `st_height_variations_filter`
- color params: `channel_basecolor`, `hue_shift`, `color_blur`, `grass_color`, `color`, `color_1`, `color_2`, `color_3`
- examples: `stylized_autumnal_fallen_leaves`, `stylized_earth_and_grass`, `stylized_fallen_pine_needles`, `stylized_hay_ground`, `stylized_lawn_grass`, `stylized_long_field_grass`, `stylized_moving_lush_grass`, `stylized_moving_sea_kelp`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `metal_gold`  (9 materials)

- avg nodes **146.4** · blends **31.1** · levels **12.9** · hsl **4.7** · warps **2.8**
- patterns: `levels_remapping`×9, `histogram_shape_control`×9, `tile_pattern_structure`×9, `non_uniform_blur`×9, `hbao_occlusion`×9, `pbr_converter_outputs`×9, `height_to_normal`×9, `warp_distortion`×9
- top filters: `blend`×280, `passthrough`×195, `levels`×116, `uniform`×67, `hsl`×42, `blur`×23, `normal`×19, `directionalwarp`×16
- top instances: `safe_transform_grayscale`×38, `swirl_grayscale`×36, `quantize_grayscale`×32, `histogram_range`×29, `non_uniform_blur_grayscale`×29, `histogram_select`×28, `shadows`×23, `histogram_scan`×17
- specialty filters: `st_stylized_look_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `ad_rust_filter`, `ad_top_bottom_filter`, `ad_pattern_effect_filter`, `ad_emboss_filter`, `ad_pattern_master`
- color params: `channel_basecolor`, `hue_shift`, `base_color`, `second_color_intensity`, `second_color`, `impact_color`, `highlight_color`, `scratches_color`
- examples: `stylized_aged_gold`, `stylized_aged_gold_braided_cable`, `stylized_cast_gold`, `stylized_cast_gold (1)`, `stylized_damaged_gold`, `stylized_damaged_hammered_gold`, `stylized_gold`, `stylized_gold_coins`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `organic_fur`  (9 materials)

- avg nodes **70.6** · blends **8.2** · levels **5.0** · hsl **1.3** · warps **4.7**
- patterns: `directional_warp_detail`×9, `histogram_shape_control`×9, `non_uniform_blur`×9, `hbao_occlusion`×9, `pbr_converter_outputs`×9, `height_to_normal`×9, `warp_distortion`×9, `tile_pattern_structure`×8
- top filters: `blend`×74, `transformation`×60, `levels`×45, `directionalwarp`×39, `uniform`×36, `normal`×14, `hsl`×12, `dirmotionblur`×7
- top instances: `blur_hq_grayscale`×35, `auto_levels`×22, `invert_grayscale`×22, `histogram_range`×21, `tile_generator`×17, `non_uniform_blur_grayscale`×13, `histogram_scan`×11, `perlin_noise`×10
- specialty filters: `st_stylized_look_filter`
- color params: `channel_basecolor`, `hue_shift`, `fur_color_2`, `fur_color_3`, `fur_color_1`, `feather_color_1`, `feather_color_2`, `feather_color_3`
- examples: `stylized_bear_long_fur`, `stylized_bear_short_fur`, `stylized_great_horned_owl_feathers`, `stylized_phoenix_feather`, `stylized_raven_feathers`, `stylized_snow_owl_feathers`, `stylized_wolf_long_fur`, `stylized_wolf_short_fur`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `ground_soil`  (8 materials)

- avg nodes **147.2** · blends **32.2** · levels **10.0** · hsl **4.9** · warps **4.1**
- patterns: `hsl_color_styling`×8, `histogram_shape_control`×8, `pbr_converter_outputs`×8, `height_to_normal`×8, `levels_remapping`×7, `heavy_blend_stack`×6, `tile_pattern_structure`×5, `hbao_occlusion`×5
- top filters: `blend`×258, `levels`×80, `passthrough`×74, `uniform`×47, `transformation`×42, `hsl`×39, `gradient`×27, `directionalwarp`×25
- top instances: `blur_hq_grayscale`×37, `histogram_select`×29, `invert_grayscale`×28, `auto_levels`×26, `slope_blur_grayscale_2`×19, `histogram_range`×16, `safe_transform_grayscale`×16, `histogram_scan`×16
- specialty filters: `st_pebbles_filter`, `st_sand`, `st_stylized_look_filter`, `st_surfacing_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `st_noise_to_grayscale_filter`
- color params: `hue_shift`, `channel_basecolor`, `sand_color`, `color`, `corruption_color`, `basecolor`, `pebbles_color`, `shadow_color`
- examples: `corrupted_dirt_ground`, `corrupted_soil`, `forest_ground_stylized`, `stylized_desert_sand_ridge`, `stylized_fine_sand_beach`, `stylized_muddy_soil`, `stylized_pirate_island_beach_sand`, `stylized_sahara_dunes`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `brick`  (8 materials)

- avg nodes **153.6** · blends **33.8** · levels **16.9** · hsl **8.5** · warps **3.6**
- patterns: `directional_warp_detail`×8, `histogram_shape_control`×8, `tile_pattern_structure`×8, `non_uniform_blur`×8, `slope_blur_flow`×8, `hbao_occlusion`×8, `pbr_converter_outputs`×8, `height_to_normal`×8
- top filters: `blend`×270, `levels`×135, `hsl`×68, `uniform`×56, `transformation`×37, `normal`×30, `blur`×22, `passthrough`×19
- top instances: `slope_blur_grayscale_2`×49, `blur_hq_grayscale`×44, `tile_generator`×30, `histogram_select`×28, `histogram_scan`×24, `non_uniform_blur_grayscale`×24, `quantize_grayscale`×18, `shadows`×16
- specialty filters: `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`, `st_cracks_filter`, `st_cuts_filter`, `st_height_variations_filter`, `ad_impact_filter`, `ad_moss_filter`
- color params: `channel_basecolor`, `hue_shift`, `impact_color`, `plaster_color`, `bricks_color`, `color_variation`, `plaster_second_color_intensity`, `plaster_second_color`
- examples: `stylized_brick_overgrown`, `stylized_bricks`, `stylized_damaged_bricks`, `stylized_dirty_brick_chimney`, `stylized_mossy_brick_wall`, `stylized_old_brick_wall`, `stylized_old_bricks`, `stylized_plaster_and_brick_wall`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `concrete`  (6 materials)

- avg nodes **97.0** · blends **25.2** · levels **9.0** · hsl **6.3** · warps **0.8**
- patterns: `heavy_blend_stack`×6, `hsl_color_styling`×6, `histogram_shape_control`×6, `tile_pattern_structure`×6, `wood_fiber_stylization`×6, `hbao_occlusion`×6, `pbr_converter_outputs`×6, `height_to_normal`×6
- top filters: `blend`×151, `levels`×54, `hsl`×38, `uniform`×33, `blur`×21, `passthrough`×18, `normal`×10, `transformation`×8
- top instances: `histogram_scan`×17, `tile_generator`×16, `histogram_select`×15, `shadows`×14, `non_uniform_blur_grayscale`×11, `st_surfacing_filter`×10, `auto_levels`×9, `clouds_2`×8
- specialty filters: `st_surfacing_filter`, `st_cracks_filter`, `st_stylized_look_filter`, `st_trimming_filter`, `st_stylized_light_shadow`, `st_cuts_filter`, `st_pattern_filter`, `st_height_variations_filter`
- color params: `channel_basecolor`, `hue_shift`, `base_color`, `second_color`, `shadow_color`, `second_color_intensity`, `impact_color`, `custom_variation_color_1`
- examples: `stylized_bent_double_concrete_wall`, `stylized_concrete`, `stylized_damaged_concrete`, `stylized_eroded_concrete`, `stylized_overlay_lines_concrete_wall`, `stylized_square_concrete_tiles`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `organic_eye`  (6 materials)

- avg nodes **104.7** · blends **26.7** · levels **3.2** · hsl **2.2** · warps **5.7**
- patterns: `heavy_blend_stack`×6, `hsl_color_styling`×6, `histogram_shape_control`×6, `pbr_converter_outputs`×6, `height_to_normal`×6, `warp_distortion`×6, `directional_warp_detail`×4, `slope_blur_flow`×3
- top filters: `blend`×160, `uniform`×54, `transformation`×53, `warp`×30, `levels`×19, `hsl`×13, `normal`×6, `valueprocessor`×6
- top instances: `histogram_scan`×46, `splatter_circular`×30, `shape`×23, `blur_hq_grayscale`×19, `histogram_range`×12, `polygon_2`×7, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×6, `gaussian_noise`×6
- color params: `color`, `outline_color`, `pupil_color`, `color_blur`, `sclera_color`, `channel_basecolor`, `hue_shift`
- examples: `stylized_cat_eye_1`, `stylized_cat_eye_2`, `stylized_horse_eye`, `stylized_human_eye_1`, `stylized_human_eye_2`, `stylized_human_eye_3`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `paper`  (5 materials)

- avg nodes **90.4** · blends **12.0** · levels **5.4** · hsl **2.2** · warps **2.6**
- patterns: `directional_warp_detail`×5, `histogram_shape_control`×5, `tile_pattern_structure`×5, `brush_stroke_stylization`×5, `ad_material_filter`×5, `hbao_occlusion`×5, `pbr_converter_outputs`×5, `height_to_normal`×5
- top filters: `blend`×60, `passthrough`×51, `uniform`×28, `levels`×27, `transformation`×24, `hsl`×11, `directionalwarp`×9, `normal`×8
- top instances: `tile_generator`×23, `blur_hq_grayscale`×17, `invert_grayscale`×15, `multi_directional_warp_grayscale`×10, `ad_pattern_effect_filter`×8, `safe_transform_grayscale`×7, `height_blend`×6, `switch_grayscale`×6
- specialty filters: `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`, `ad_pattern_master`
- color params: `pattern_color_intensity`, `pattern_color`, `channel_basecolor`, `hue_shift`, `paper_color_1`, `paper_color_2`, `detail_color_intensity`, `detail_color`
- examples: `stylized_balloon_paper`, `stylized_book_paper`, `stylized_paper_lamp_shade`, `stylized_standard_paper`, `stylized_structural_paper_lamp_shade`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `fabric_carpet`  (5 materials)

- avg nodes **138.6** · blends **26.6** · levels **13.4** · hsl **2.0** · warps **7.2**
- patterns: `directional_warp_detail`×5, `heavy_blend_stack`×5, `levels_remapping`×5, `histogram_shape_control`×5, `tile_pattern_structure`×5, `hbao_occlusion`×5, `pbr_converter_outputs`×5, `height_to_normal`×5
- top filters: `blend`×133, `transformation`×81, `levels`×67, `uniform`×34, `passthrough`×30, `directionalwarp`×24, `blur`×18, `dyngradient`×12
- top instances: `histogram_scan`×16, `perlin_noise`×14, `blur_hq_grayscale`×12, `switch_grayscale`×10, `mirror_grayscale`×10, `shape`×9, `ScaleMatrix`×9, `ad_pattern_effect_filter`×8
- specialty filters: `ad_pattern_effect_filter`, `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_master`
- color params: `channel_basecolor`, `hue_shift`, `dust_color`, `dust_color_intensity`, `carpet_color_01`, `carpet_color_02`, `thread_color`, `color_01`
- examples: `stylized_rounded_carpet`, `stylized_traditional_geometric_carpet`, `stylized_traditional_patterned_carpet`, `stylized_traditional_rectangle_carpet`, `stylized_woven_carpet`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `fabric_cloth`  (4 materials)

- avg nodes **161.5** · blends **36.2** · levels **9.8** · hsl **3.0** · warps **4.2**
- patterns: `heavy_blend_stack`×4, `histogram_shape_control`×4, `tile_pattern_structure`×4, `hbao_occlusion`×4, `pbr_converter_outputs`×4, `height_to_normal`×4, `warp_distortion`×4, `levels_remapping`×3
- top filters: `blend`×145, `passthrough`×81, `levels`×39, `transformation`×31, `uniform`×21, `hsl`×12, `directionalwarp`×12, `gradient`×10
- top instances: `blur_hq_grayscale`×41, `histogram_range`×14, `tile_generator`×14, `histogram_select`×11, `invert_grayscale`×10, `slope_blur_grayscale_2`×10, `histogram_scan`×10, `safe_transform_grayscale`×9
- specialty filters: `ad_brush_stroke_generator`, `ad_material_filter`, `ad_pattern_effect_filter`, `ad_pattern_master`
- color params: `channel_basecolor`, `hue_shift`, `fabric_color`, `stitches_color`, `fabric_color_01`, `fabric_color_02`, `details_color`, `sails_color`
- examples: `stylized_cotton_skirt`, `stylized_denim_cut`, `stylized_fabric_cushion`, `stylized_pirate_ship_sails`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `fabric_wool`  (3 materials)

- avg nodes **86.7** · blends **18.0** · levels **9.0** · hsl **1.7** · warps **4.7**
- patterns: `directional_warp_detail`×3, `heavy_blend_stack`×3, `levels_remapping`×3, `histogram_shape_control`×3, `tile_pattern_structure`×3, `hbao_occlusion`×3, `pbr_converter_outputs`×3, `height_to_normal`×3
- top filters: `blend`×54, `transformation`×28, `levels`×27, `directionalwarp`×14, `uniform`×10, `normal`×6, `hsl`×5, `blur`×3
- top instances: `blur_hq_grayscale`×10, `swirl_grayscale`×9, `hbao`×8, `tile_generator`×8, `invert_grayscale`×7, `quantize_grayscale`×6, `anisotropic_noise`×6, `histogram_range`×3
- color params: `fabric_color`, `channel_basecolor`, `hue_shift`
- examples: `stylized_rib_knit_wool`, `stylized_wave_knit_wool`, `stylized_wool`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `crystal`  (2 materials)

- avg nodes **58.0** · blends **11.5** · levels **10.0** · hsl **5.5** · warps **0.5**
- patterns: `heavy_blend_stack`×2, `levels_remapping`×2, `hsl_color_styling`×2, `histogram_shape_control`×2, `tile_pattern_structure`×2, `pbr_converter_outputs`×2, `height_to_normal`×2, `directional_warp_detail`×1
- top filters: `blend`×23, `levels`×20, `hsl`×11, `normal`×6, `transformation`×4, `uniform`×3, `directionalwarp`×1
- top instances: `curvature_smooth`×4, `invert_grayscale`×4, `histogram_select`×3, `tile_generator`×3, `histogram_range`×2, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×2, `clouds_2`×2, `blur_hq_grayscale`×2
- color params: `crystal_color`, `channel_basecolor`, `hue_shift`
- examples: `stylized_amethyst_crystal`, `stylized_carved_crystal`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `organic_shell`  (2 materials)

- avg nodes **161.5** · blends **37.5** · levels **13.0** · hsl **8.5** · warps **5.5**
- patterns: `directional_warp_detail`×2, `heavy_blend_stack`×2, `hsl_color_styling`×2, `histogram_shape_control`×2, `tile_pattern_structure`×2, `hbao_occlusion`×2, `pbr_converter_outputs`×2, `height_to_normal`×2
- top filters: `blend`×75, `levels`×26, `transformation`×26, `hsl`×17, `blur`×9, `directionalwarp`×9, `uniform`×8, `normal`×7
- top instances: `invert_grayscale`×10, `blur_hq_grayscale`×9, `mirror_grayscale`×7, `bevel`×6, `histogram_scan`×6, `histogram_select`×5, `st_noise_to_grayscale_filter`×4, `shadows`×3
- specialty filters: `st_noise_to_grayscale_filter`, `st_cracks_filter`, `st_cuts_filter`, `st_height_variations_filter`, `st_pattern_filter`, `st_stylized_look_filter`, `st_surfacing_filter`, `st_trimming_filter`
- color params: `channel_basecolor`, `hue_shift`, `ground_color`, `bones_color`, `shell_color`
- examples: `stylized_grave_bones`, `stylized_tortoise_shell`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `water`  (2 materials)

- avg nodes **70.0** · blends **9.5** · levels **5.0** · hsl **2.5** · warps **1.5**
- patterns: `directional_warp_detail`×2, `hsl_color_styling`×2, `histogram_shape_control`×2, `tile_pattern_structure`×2, `non_uniform_blur`×2, `hbao_occlusion`×2, `pbr_converter_outputs`×2, `height_to_normal`×2
- top filters: `blend`×19, `uniform`×11, `levels`×10, `hsl`×5, `passthrough`×5, `transformation`×4, `normal`×4, `directionalwarp`×3
- top instances: `non_uniform_blur_grayscale`×9, `auto_levels`×6, `histogram_range`×3, `histogram_select`×3, `blur_hq_grayscale`×3, `slope_blur_grayscale_2`×2, `invert_grayscale`×2, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×2
- specialty filters: `st_stylized_look_filter`, `ad_brush_stroke_generator`, `ad_material_filter`
- color params: `channel_basecolor`, `hue_shift`, `ice_color`, `color_variation_1`, `color_variation_1_intensity`, `color_variation_2`, `color_variation_2_intensity`, `ground_color`
- examples: `stylized_ice_impact`, `stylized_ocean_water`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `corrupted`  (1 materials)

- avg nodes **97.0** · blends **11.0** · levels **9.0** · hsl **2.0** · warps **5.0**
- patterns: `directional_warp_detail`×1, `heavy_blend_stack`×1, `levels_remapping`×1, `hsl_color_styling`×1, `histogram_shape_control`×1, `tile_pattern_structure`×1, `non_uniform_blur`×1, `slope_blur_flow`×1
- top filters: `blend`×11, `levels`×9, `uniform`×5, `warp`×4, `normal`×3, `transformation`×3, `distance`×2, `hsl`×2
- top instances: `multi_directional_warp_grayscale`×8, `non_uniform_blur_grayscale`×6, `invert_grayscale`×6, `blur_hq_grayscale`×4, `edge_detect`×3, `perlin_noise`×3, `tile_generator`×2, `slope_blur_grayscale_2`×2
- color params: `color`, `secondary_color`, `channel_basecolor`, `hue_shift`
- examples: `corrupted_veins`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `column`  (1 materials)

- avg nodes **58.0** · blends **6.0** · levels **4.0** · hsl **2.0** · warps **2.0**
- patterns: `directional_warp_detail`×1, `hsl_color_styling`×1, `histogram_shape_control`×1, `tile_pattern_structure`×1, `slope_blur_flow`×1, `pbr_converter_outputs`×1, `voronoi_crystal_breakup`×1, `height_to_normal`×1
- top filters: `blend`×6, `levels`×4, `normal`×3, `uniform`×3, `hsl`×2, `gradient`×2, `curve`×2, `directionalwarp`×2
- top instances: `histogram_range`×3, `curvature_smooth_v2`×2, `quantize_grayscale`×2, `slope_blur_grayscale_2`×2, `blur_hq_grayscale`×2, `auto_levels`×2, `tile_generator`×2, `basecolor_metallic_roughness_to_diffuse_specular_glossiness`×1
- color params: `color`, `channel_basecolor`, `hue_shift`
- examples: `stylized_damaged_column`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

### `roof`  (1 materials)

- avg nodes **80.0** · blends **14.0** · levels **5.0** · hsl **4.0** · warps **0.0**
- patterns: `directional_warp_detail`×1, `heavy_blend_stack`×1, `levels_remapping`×1, `hsl_color_styling`×1, `histogram_shape_control`×1, `tile_pattern_structure`×1, `non_uniform_blur`×1, `slope_blur_flow`×1
- top filters: `blend`×14, `uniform`×6, `levels`×5, `hsl`×4, `normal`×3, `transformation`×3, `sharpen`×1, `blur`×1
- top instances: `histogram_scan`×4, `multi_directional_warp_grayscale`×4, `safe_transform_grayscale`×4, `quantize_grayscale`×2, `blur_hq_grayscale`×2, `curvature_smooth`×2, `auto_levels`×2, `histogram_range`×1
- specialty filters: `st_stylized_look_filter`, `st_trimming_filter`
- color params: `color`, `color_variation`, `color_variation_intensity`, `shadow_color`, `highlight_color`, `channel_basecolor`, `hue_shift`
- examples: `stylized_diamond_slate_roof_tiles`

**Build checklist:**
1. Block out primary shape (tile/pattern/noise → histogram_scan).
2. Warp/slope-blur for stylized relief; levels to tame.
3. Flat uniform colors + HSL; blend color zones with shape masks.
4. Edge/dirt/tarnish as extra blend layers (curvature or highpass optional).
5. Roughness simple; metallic only if metal category.
6. Normal from height; HBAO; wire PBR outputs.

## Agent usage rules

When the user asks for a **stylized** material:

1. Classify into a category above (metal_gold, brick, wood_planks, …).
2. Open 1–3 example SBS paths from the catalog for that category (reference, don't copy blindly).
3. Follow that category's avg structure (blend/levels/warp counts as budget).
4. Prefer readable shapes + few colors over photoreal noise.
5. Name exposed params descriptively: `wood_color`, `gold_roughness`, `wave_density`, `corruption_spread`.
6. Always emit basecolor, normal, roughness, height, ao; metallic when relevant.

## Catalog fields

Each material record has: `id`, `title`, `category`, `sbs_path`, `preview_path`,
`node_count`, `filters`, `instances`, `specialty_filters`, `exposed_params`, `patterns`.

---

## Authority note

This playbook describes **graph topology patterns** mined from a local reference corpus.
**Look, palette, wear language, and ensemble rules** come from `knowledge/projects/` art-bibles
and `design_concepts.md` — not from unmodified donor defaults.
