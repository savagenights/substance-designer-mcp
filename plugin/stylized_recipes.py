"""
Stylized material recipes — Level B.

Built from mined patterns across 637 stylized reference SBS graphs.
Uses only SD built-in atomic + common library nodes (no ad_/st_ custom
filters which live inside library packages and aren't globally available).

Design grammar (from playbook):
  shape first → histogram carve → directional warp relief →
  levels tame → uniform+HSL color blocks → blend stacks →
  height→normal / simple roughness / AO

Recipe keys are registered as:
  stylized_<category>   e.g. stylized_metal_gold, stylized_brick
  plus short aliases    e.g. stylized_gold, stylized_wood
"""
from __future__ import annotations

# Shared library URLs (confirmed in recipes.py / SD 15-16)
LIB = {
    "perlin_noise": "pkg:///perlin_noise?dependency=1563156574",
    "cells_1": "pkg:///cells_1?dependency=1563150890",
    "cells_2": "pkg:///cells_2?dependency=1563253418",
    "clouds_2": "pkg:///clouds_2?dependency=1563158662",
    "crystal_1": "pkg:///crystal_1?dependency=1563153565",
    "polygon_2": "pkg:///polygon_2?dependency=1563151369",
    "blur_hq_grayscale": "pkg:///blur_hq_grayscale?dependency=1299236171",
    "slope_blur_grayscale_2": "pkg:///slope_blur_grayscale_2?dependency=1563154333",
    "non_uniform_blur_grayscale": "pkg:///non_uniform_blur_grayscale?dependency=1502209989",
    "multi_directional_warp_grayscale": "pkg:///multi_directional_warp_grayscale?dependency=1563187562",
    "invert_grayscale": "pkg:///invert_grayscale?dependency=1177447620",
    "highpass_grayscale": "pkg:///highpass_grayscale?dependency=1563447639",
    "histogram_scan": "pkg:///histogram_scan?dependency=1563254078",
    "edge_detect": "pkg:///edge_detect?dependency=1563645680",
    "tile_random": "pkg:///tile_random?dependency=1508386588",
    "gradient_linear_1": "pkg:///gradient_linear_1?dependency=1563150839",
}


def _pbr_stylized(
    height_alias,
    color_a,
    color_b=None,
    roughness=0.55,
    metallic=0.0,
    normal_intensity=4.0,
    shadow_factor=0.62,
    highlight_factor=1.18,
):
    """Stylized PBR finish: 2-tone basecolor from height, simple rough/metal/AO/normal."""
    if color_b is None:
        # slightly cooler/darker secondary
        color_b = (
            max(0.0, color_a[0] * 0.72),
            max(0.0, color_a[1] * 0.72),
            max(0.0, min(1.0, color_a[2] * 0.78)),
        )
    r, g, b = color_a
    r2, g2, b2 = color_b
    # peak / valley modulation
    hr = min(1.0, r * highlight_factor)
    hg = min(1.0, g * highlight_factor)
    hb = min(1.0, b * highlight_factor)
    sr = max(0.0, r2 * shadow_factor / 0.72) if r2 else r * shadow_factor
    sg = max(0.0, g2 * shadow_factor / 0.72) if g2 else g * shadow_factor
    sb = max(0.0, b2 * shadow_factor / 0.72) if b2 else b * shadow_factor
    # ensure shadow uses color_b directly as the "zone B"
    sr, sg, sb = r2, g2, b2

    rl = max(0.0, roughness - 0.12)
    rh = min(1.0, roughness + 0.18)

    nodes = [
        {
            "id_alias": "out_height",
            "definition_id": "sbs::compositing::output",
            "usage": "height",
            "label": "Height",
            "position": [2800, 0],
        },
        {
            "id_alias": "pbr_normal",
            "definition_id": "sbs::compositing::normal",
            "position": [2800, -180],
            "parameters": {"intensity": normal_intensity},
        },
        {
            "id_alias": "out_normal",
            "definition_id": "sbs::compositing::output",
            "usage": "normal",
            "label": "Normal",
            "position": [3000, -180],
        },
        {
            "id_alias": "pbr_rough",
            "definition_id": "sbs::compositing::levels",
            "position": [2800, -360],
            "parameters": {
                "levelinlow": [0.0, 0.0, 0.0, 0.0],
                "levelinhigh": [1.0, 1.0, 1.0, 1.0],
                "leveloutlow": [rl, rl, rl, rl],
                "levelouthigh": [rh, rh, rh, rh],
            },
        },
        {
            "id_alias": "out_roughness",
            "definition_id": "sbs::compositing::output",
            "usage": "roughness",
            "label": "Roughness",
            "position": [3000, -360],
        },
        {
            "id_alias": "pbr_ao",
            "definition_id": "sbs::compositing::levels",
            "position": [2800, -540],
            "parameters": {
                "levelinlow": [0.0, 0.0, 0.0, 0.0],
                "levelinhigh": [0.55, 0.55, 0.55, 0.55],
                "leveloutlow": [0.15, 0.15, 0.15, 0.15],
                "levelouthigh": [1.0, 1.0, 1.0, 1.0],
            },
        },
        {
            "id_alias": "out_ao",
            "definition_id": "sbs::compositing::output",
            "usage": "ambientOcclusion",
            "label": "Ambient Occlusion",
            "position": [3000, -540],
        },
        {
            "id_alias": "pbr_metallic",
            "definition_id": "sbs::compositing::uniform",
            "position": [2800, -720],
            "parameters": {"outputcolor": [metallic, metallic, metallic, 1.0]},
        },
        {
            "id_alias": "out_metallic",
            "definition_id": "sbs::compositing::output",
            "usage": "metallic",
            "label": "Metallic",
            "position": [3000, -720],
        },
        # 2-tone stylized color
        {
            "id_alias": "pbr_color_a",
            "definition_id": "sbs::compositing::uniform",
            "position": [2400, -900],
            "parameters": {"outputcolor": [hr, hg, hb, 1.0]},
        },
        {
            "id_alias": "pbr_color_b",
            "definition_id": "sbs::compositing::uniform",
            "position": [2400, -1060],
            "parameters": {"outputcolor": [sr, sg, sb, 1.0]},
        },
        {
            "id_alias": "pbr_color_mask",
            "definition_id": "sbs::compositing::levels",
            "position": [2400, -740],
            "parameters": {
                "levelinlow": [0.25, 0.25, 0.25, 0.25],
                "levelinhigh": [0.75, 0.75, 0.75, 0.75],
            },
        },
        {
            "id_alias": "pbr_color",
            "definition_id": "sbs::compositing::blend",
            "position": [2600, -900],
            "parameters": {"blendingmode": 0, "opacitymult": 1.0},
        },
        {
            "id_alias": "pbr_color_hsl",
            "definition_id": "sbs::compositing::hsl",
            "position": [2800, -900],
            "parameters": {"hue": 0.5, "saturation": 0.55, "luminosity": 0.5},
        },
        {
            "id_alias": "out_basecolor",
            "definition_id": "sbs::compositing::output",
            "usage": "baseColor",
            "label": "Base Color",
            "position": [3000, -900],
        },
    ]
    conns = [
        {
            "from": height_alias,
            "to": "out_height",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
        {
            "from": height_alias,
            "to": "pbr_normal",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "pbr_normal",
            "to": "out_normal",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
        {
            "from": height_alias,
            "to": "pbr_rough",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "pbr_rough",
            "to": "out_roughness",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
        {
            "from": height_alias,
            "to": "pbr_ao",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "pbr_ao",
            "to": "out_ao",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
        {
            "from": "pbr_metallic",
            "to": "out_metallic",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
        {
            "from": height_alias,
            "to": "pbr_color_mask",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "pbr_color_a",
            "to": "pbr_color",
            "from_output": "unique_filter_output",
            "to_input": "source",
        },
        {
            "from": "pbr_color_b",
            "to": "pbr_color",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {
            "from": "pbr_color_mask",
            "to": "pbr_color",
            "from_output": "unique_filter_output",
            "to_input": "opacity",
        },
        {
            "from": "pbr_color",
            "to": "pbr_color_hsl",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "pbr_color_hsl",
            "to": "out_basecolor",
            "from_output": "unique_filter_output",
            "to_input": "inputNodeOutput",
        },
    ]
    return nodes, conns


def _finish(nodes, conns, height_alias, color_a, color_b=None, **pbr_kw):
    pn, pc = _pbr_stylized(height_alias, color_a, color_b, **pbr_kw)
    return {
        "nodes": nodes + pn,
        "connections": conns + pc,
        "height_alias": height_alias,
        "color": color_a,
        "style": "stylized",
    }


# ─────────────────────────────────────────────────────────────────────────────
# HEIGHT BUILDERS (stylized shape language)
# ─────────────────────────────────────────────────────────────────────────────


def _height_tile_structure(
    cells_scale=6,
    perlin_scale=10,
    hist_pos=0.45,
    hist_contrast=0.55,
    warp_intensity=0.22,
    slope_intensity=0.28,
    dir_warp=0.14,
    y_off=0,
):
    """Readable tile/cell structure → histogram carve → slope/dir warp → levels."""
    yo = y_off
    nodes = [
        {
            "id_alias": "st_cells",
            "resource_url": LIB["cells_2"],
            "position": [-900, yo],
            "parameters": {
                "scale": {"value": cells_scale, "type": "int"},
                "disorder": {"value": 0.35, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_perlin",
            "resource_url": LIB["perlin_noise"],
            "position": [-900, yo + 220],
            "parameters": {
                "scale": {"value": perlin_scale, "type": "int"},
                "disorder": {"value": 0.15, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_hist",
            "resource_url": LIB["histogram_scan"],
            "position": [-650, yo],
            "parameters": {
                "Position": {"value": hist_pos, "type": "float"},
                "Contrast": {"value": hist_contrast, "type": "float"},
            },
        },
        {
            "id_alias": "st_blur_slope",
            "resource_url": LIB["blur_hq_grayscale"],
            "position": [-650, yo + 220],
            "parameters": {
                "Intensity": {"value": 2.5, "type": "float"},
                "Quality": {"value": 0, "type": "int"},
            },
        },
        {
            "id_alias": "st_slope",
            "resource_url": LIB["slope_blur_grayscale_2"],
            "position": [-400, yo],
            "parameters": {
                "Samples": {"value": 8, "type": "int"},
                "Intensity": {"value": slope_intensity, "type": "float"},
            },
        },
        {
            "id_alias": "st_dirwarp",
            "definition_id": "sbs::compositing::directionalwarp",
            "position": [-150, yo],
            "parameters": {"intensity": dir_warp},
        },
        {
            "id_alias": "st_detail",
            "resource_url": LIB["perlin_noise"],
            "position": [-150, yo + 220],
            "parameters": {
                "scale": {"value": 28, "type": "int"},
                "disorder": {"value": 0.2, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_detail_blur",
            "resource_url": LIB["blur_hq_grayscale"],
            "position": [50, yo + 220],
            "parameters": {
                "Intensity": {"value": 1.5, "type": "float"},
                "Quality": {"value": 0, "type": "int"},
            },
        },
        {
            "id_alias": "st_warp2",
            "definition_id": "sbs::compositing::warp",
            "position": [100, yo],
            "parameters": {"intensity": warp_intensity},
        },
        {
            "id_alias": "st_edge",
            "resource_url": LIB["edge_detect"],
            "position": [300, yo + 220],
            "parameters": {
                "edge_width": {"value": 0.5, "type": "float"},
                "edge_roundness": {"value": 0.3, "type": "float"},
            },
        },
        {
            "id_alias": "st_edge_blend",
            "definition_id": "sbs::compositing::blend",
            "position": [350, yo],
            "parameters": {"blendingmode": 2, "opacitymult": 0.35},  # subtract edges
        },
        {
            "id_alias": "st_levels",
            "definition_id": "sbs::compositing::levels",
            "position": [550, yo],
            "parameters": {
                "levelinlow": [0.08, 0.08, 0.08, 0.08],
                "levelinhigh": [0.92, 0.92, 0.92, 0.92],
            },
        },
    ]
    # histogram_scan ports: Output / Input_1 (from recipes.py docs)
    # blur_hq: Blur_HQ / Source
    # slope_blur: Slope_Blur / Source, Effect
    # edge_detect: output / input
    conns = [
        {"from": "st_cells", "to": "st_hist", "from_output": "output", "to_input": "Input_1"},
        {"from": "st_perlin", "to": "st_blur_slope", "from_output": "output", "to_input": "Source"},
        {"from": "st_hist", "to": "st_slope", "from_output": "Output", "to_input": "Source"},
        {"from": "st_blur_slope", "to": "st_slope", "from_output": "Blur_HQ", "to_input": "Effect"},
        {
            "from": "st_slope",
            "to": "st_dirwarp",
            "from_output": "Slope_Blur",
            "to_input": "input1",
        },
        {
            "from": "st_blur_slope",
            "to": "st_dirwarp",
            "from_output": "Blur_HQ",
            "to_input": "inputintensity",
        },
        {"from": "st_detail", "to": "st_detail_blur", "from_output": "output", "to_input": "Source"},
        {
            "from": "st_dirwarp",
            "to": "st_warp2",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "st_detail_blur",
            "to": "st_warp2",
            "from_output": "Blur_HQ",
            "to_input": "inputgradient",
        },
        {
            "from": "st_warp2",
            "to": "st_edge",
            "from_output": "unique_filter_output",
            "to_input": "input",
        },
        {
            "from": "st_edge",
            "to": "st_edge_blend",
            "from_output": "output",
            "to_input": "source",
        },
        {
            "from": "st_warp2",
            "to": "st_edge_blend",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {
            "from": "st_edge_blend",
            "to": "st_levels",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
    ]
    return nodes, conns, "st_levels"


def _height_organic_flow(
    clouds_scale=4,
    perlin_scale=12,
    multi_warp=0.35,
    dir_warp=0.2,
    y_off=0,
):
    """Soft organic / grass / soil / water stylized height."""
    yo = y_off
    nodes = [
        {
            "id_alias": "st_clouds",
            "resource_url": LIB["clouds_2"],
            "position": [-900, yo],
            "parameters": {
                "scale": {"value": clouds_scale, "type": "int"},
                "disorder": {"value": 0.55, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_perlin",
            "resource_url": LIB["perlin_noise"],
            "position": [-900, yo + 220],
            "parameters": {
                "scale": {"value": perlin_scale, "type": "int"},
                "disorder": {"value": 0.25, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_blend_base",
            "definition_id": "sbs::compositing::blend",
            "position": [-650, yo],
            "parameters": {"blendingmode": 1, "opacitymult": 0.45},  # add
        },
        {
            "id_alias": "st_blur",
            "resource_url": LIB["blur_hq_grayscale"],
            "position": [-650, yo + 220],
            "parameters": {
                "Intensity": {"value": 3.0, "type": "float"},
                "Quality": {"value": 0, "type": "int"},
            },
        },
        {
            "id_alias": "st_mdw",
            "resource_url": LIB["multi_directional_warp_grayscale"],
            "position": [-400, yo],
            "parameters": {
                "intensity": {"value": multi_warp, "type": "float"},
                "directions": {"value": 4, "type": "int"},
            },
        },
        {
            "id_alias": "st_dirwarp",
            "definition_id": "sbs::compositing::directionalwarp",
            "position": [-150, yo],
            "parameters": {"intensity": dir_warp},
        },
        {
            "id_alias": "st_nub",
            "resource_url": LIB["non_uniform_blur_grayscale"],
            "position": [100, yo],
            "parameters": {
                "Intensity": {"value": 0.4, "type": "float"},
                "Anisotropy": {"value": 0.5, "type": "float"},
            },
        },
        {
            "id_alias": "st_levels",
            "definition_id": "sbs::compositing::levels",
            "position": [350, yo],
            "parameters": {
                "levelinlow": [0.1, 0.1, 0.1, 0.1],
                "levelinhigh": [0.9, 0.9, 0.9, 0.9],
            },
        },
    ]
    conns = [
        {"from": "st_clouds", "to": "st_blend_base", "from_output": "output", "to_input": "source"},
        {
            "from": "st_perlin",
            "to": "st_blend_base",
            "from_output": "output",
            "to_input": "destination",
        },
        {"from": "st_perlin", "to": "st_blur", "from_output": "output", "to_input": "Source"},
        {
            "from": "st_blend_base",
            "to": "st_mdw",
            "from_output": "unique_filter_output",
            "to_input": "input",
        },
        {"from": "st_blur", "to": "st_mdw", "from_output": "Blur_HQ", "to_input": "intensity_input"},
        {
            "from": "st_mdw",
            "to": "st_dirwarp",
            "from_output": "output",
            "to_input": "input1",
        },
        {
            "from": "st_blur",
            "to": "st_dirwarp",
            "from_output": "Blur_HQ",
            "to_input": "inputintensity",
        },
        {
            "from": "st_dirwarp",
            "to": "st_nub",
            "from_output": "unique_filter_output",
            "to_input": "Source",
        },
        {
            "from": "st_blur",
            "to": "st_nub",
            "from_output": "Blur_HQ",
            "to_input": "Effect",
        },
        {
            "from": "st_nub",
            "to": "st_levels",
            "from_output": "Non_Uniform_Blur",
            "to_input": "input1",
        },
    ]
    return nodes, conns, "st_levels"


def _height_metal_hammer(
    perlin_scale=18,
    cells_scale=8,
    hist_pos=0.5,
    warp=0.12,
    y_off=0,
):
    """Hammered / cast metal stylized relief."""
    yo = y_off
    nodes = [
        {
            "id_alias": "st_cells",
            "resource_url": LIB["cells_1"],
            "position": [-900, yo],
            "parameters": {
                "scale": {"value": cells_scale, "type": "int"},
                "disorder": {"value": 0.4, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_perlin",
            "resource_url": LIB["perlin_noise"],
            "position": [-900, yo + 220],
            "parameters": {
                "scale": {"value": perlin_scale, "type": "int"},
                "disorder": {"value": 0.08, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_hist",
            "resource_url": LIB["histogram_scan"],
            "position": [-650, yo],
            "parameters": {
                "Position": {"value": hist_pos, "type": "float"},
                "Contrast": {"value": 0.4, "type": "float"},
            },
        },
        {
            "id_alias": "st_blend",
            "definition_id": "sbs::compositing::blend",
            "position": [-400, yo],
            "parameters": {"blendingmode": 0, "opacitymult": 0.55},
        },
        {
            "id_alias": "st_blur",
            "resource_url": LIB["blur_hq_grayscale"],
            "position": [-400, yo + 220],
            "parameters": {
                "Intensity": {"value": 2.0, "type": "float"},
                "Quality": {"value": 0, "type": "int"},
            },
        },
        {
            "id_alias": "st_dirwarp",
            "definition_id": "sbs::compositing::directionalwarp",
            "position": [-150, yo],
            "parameters": {"intensity": warp},
        },
        {
            "id_alias": "st_highpass",
            "resource_url": LIB["highpass_grayscale"],
            "position": [100, yo + 220],
            "parameters": {"Radius": {"value": 8.0, "type": "float"}},
        },
        {
            "id_alias": "st_micro",
            "definition_id": "sbs::compositing::blend",
            "position": [100, yo],
            "parameters": {"blendingmode": 1, "opacitymult": 0.25},
        },
        {
            "id_alias": "st_levels",
            "definition_id": "sbs::compositing::levels",
            "position": [350, yo],
            "parameters": {
                "levelinlow": [0.15, 0.15, 0.15, 0.15],
                "levelinhigh": [0.85, 0.85, 0.85, 0.85],
            },
        },
    ]
    conns = [
        {"from": "st_cells", "to": "st_hist", "from_output": "output", "to_input": "Input_1"},
        {"from": "st_hist", "to": "st_blend", "from_output": "Output", "to_input": "source"},
        {"from": "st_perlin", "to": "st_blend", "from_output": "output", "to_input": "destination"},
        {"from": "st_perlin", "to": "st_blur", "from_output": "output", "to_input": "Source"},
        {
            "from": "st_blend",
            "to": "st_dirwarp",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "st_blur",
            "to": "st_dirwarp",
            "from_output": "Blur_HQ",
            "to_input": "inputintensity",
        },
        {
            "from": "st_dirwarp",
            "to": "st_highpass",
            "from_output": "unique_filter_output",
            "to_input": "Source",
        },
        {
            "from": "st_highpass",
            "to": "st_micro",
            "from_output": "Highpass",
            "to_input": "source",
        },
        {
            "from": "st_dirwarp",
            "to": "st_micro",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {
            "from": "st_micro",
            "to": "st_levels",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
    ]
    return nodes, conns, "st_levels"


def _height_wood_grain(perlin_scale=14, ring_scale=7, warp=0.28, y_off=0):
    """Stylized wood grain — stretched perlin + rings + dir warp."""
    yo = y_off
    nodes = [
        {
            "id_alias": "st_grain",
            "resource_url": LIB["perlin_noise"],
            "position": [-900, yo],
            "parameters": {
                "scale": {"value": perlin_scale, "type": "int"},
                "disorder": {"value": 0.06, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_stretch",
            "definition_id": "sbs::compositing::transformation",
            "position": [-650, yo],
            "parameters": {"matrix22": [2.4, 0.0, 0.0, 0.22], "offset": [0.0, 0.0]},
        },
        {
            "id_alias": "st_rings",
            "resource_url": LIB["perlin_noise"],
            "position": [-900, yo + 220],
            "parameters": {
                "scale": {"value": ring_scale, "type": "int"},
                "disorder": {"value": 0.18, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_blend",
            "definition_id": "sbs::compositing::blend",
            "position": [-400, yo],
            "parameters": {"blendingmode": 1, "opacitymult": 0.4},
        },
        {
            "id_alias": "st_blur",
            "resource_url": LIB["blur_hq_grayscale"],
            "position": [-400, yo + 220],
            "parameters": {
                "Intensity": {"value": 2.5, "type": "float"},
                "Quality": {"value": 0, "type": "int"},
            },
        },
        {
            "id_alias": "st_dirwarp",
            "definition_id": "sbs::compositing::directionalwarp",
            "position": [-150, yo],
            "parameters": {"intensity": warp},
        },
        {
            "id_alias": "st_hist",
            "resource_url": LIB["histogram_scan"],
            "position": [100, yo + 220],
            "parameters": {
                "Position": {"value": 0.4, "type": "float"},
                "Contrast": {"value": 0.35, "type": "float"},
            },
        },
        {
            "id_alias": "st_plank",
            "definition_id": "sbs::compositing::blend",
            "position": [100, yo],
            "parameters": {"blendingmode": 2, "opacitymult": 0.3},
        },
        {
            "id_alias": "st_levels",
            "definition_id": "sbs::compositing::levels",
            "position": [350, yo],
            "parameters": {
                "levelinlow": [0.12, 0.12, 0.12, 0.12],
                "levelinhigh": [0.88, 0.88, 0.88, 0.88],
            },
        },
    ]
    conns = [
        {"from": "st_grain", "to": "st_stretch", "from_output": "output", "to_input": "input1"},
        {
            "from": "st_rings",
            "to": "st_blend",
            "from_output": "output",
            "to_input": "source",
        },
        {
            "from": "st_stretch",
            "to": "st_blend",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {"from": "st_rings", "to": "st_blur", "from_output": "output", "to_input": "Source"},
        {
            "from": "st_blend",
            "to": "st_dirwarp",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
        {
            "from": "st_blur",
            "to": "st_dirwarp",
            "from_output": "Blur_HQ",
            "to_input": "inputintensity",
        },
        {
            "from": "st_dirwarp",
            "to": "st_hist",
            "from_output": "unique_filter_output",
            "to_input": "Input_1",
        },
        {"from": "st_hist", "to": "st_plank", "from_output": "Output", "to_input": "source"},
        {
            "from": "st_dirwarp",
            "to": "st_plank",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {
            "from": "st_plank",
            "to": "st_levels",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
    ]
    return nodes, conns, "st_levels"


def _height_scifi_panel(y_off=0):
    """Hard-edge sci-fi panel — cells + heavy histogram + light bevel feel via levels."""
    yo = y_off
    nodes = [
        {
            "id_alias": "st_cells",
            "resource_url": LIB["cells_2"],
            "position": [-900, yo],
            "parameters": {
                "scale": {"value": 5, "type": "int"},
                "disorder": {"value": 0.05, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_hist",
            "resource_url": LIB["histogram_scan"],
            "position": [-650, yo],
            "parameters": {
                "Position": {"value": 0.5, "type": "float"},
                "Contrast": {"value": 0.85, "type": "float"},
            },
        },
        {
            "id_alias": "st_edge",
            "resource_url": LIB["edge_detect"],
            "position": [-400, yo],
            "parameters": {
                "edge_width": {"value": 0.8, "type": "float"},
                "edge_roundness": {"value": 0.1, "type": "float"},
            },
        },
        {
            "id_alias": "st_panel",
            "definition_id": "sbs::compositing::blend",
            "position": [-150, yo],
            "parameters": {"blendingmode": 1, "opacitymult": 0.5},
        },
        {
            "id_alias": "st_detail",
            "resource_url": LIB["perlin_noise"],
            "position": [-400, yo + 220],
            "parameters": {
                "scale": {"value": 40, "type": "int"},
                "disorder": {"value": 0.05, "type": "float"},
                "non_square_expansion": {"value": True, "type": "bool"},
            },
        },
        {
            "id_alias": "st_micro",
            "definition_id": "sbs::compositing::blend",
            "position": [100, yo],
            "parameters": {"blendingmode": 1, "opacitymult": 0.15},
        },
        {
            "id_alias": "st_levels",
            "definition_id": "sbs::compositing::levels",
            "position": [350, yo],
            "parameters": {
                "levelinlow": [0.05, 0.05, 0.05, 0.05],
                "levelinhigh": [0.95, 0.95, 0.95, 0.95],
            },
        },
    ]
    conns = [
        {"from": "st_cells", "to": "st_hist", "from_output": "output", "to_input": "Input_1"},
        {"from": "st_hist", "to": "st_edge", "from_output": "Output", "to_input": "input"},
        {"from": "st_edge", "to": "st_panel", "from_output": "output", "to_input": "source"},
        {"from": "st_hist", "to": "st_panel", "from_output": "Output", "to_input": "destination"},
        {
            "from": "st_detail",
            "to": "st_micro",
            "from_output": "output",
            "to_input": "source",
        },
        {
            "from": "st_panel",
            "to": "st_micro",
            "from_output": "unique_filter_output",
            "to_input": "destination",
        },
        {
            "from": "st_micro",
            "to": "st_levels",
            "from_output": "unique_filter_output",
            "to_input": "input1",
        },
    ]
    return nodes, conns, "st_levels"


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY RECIPES
# ─────────────────────────────────────────────────────────────────────────────


def _recipe(name, description, category, height_fn, color_a, color_b=None, **pbr_kw):
    nodes, conns, h = height_fn()
    r = _finish(nodes, conns, h, color_a, color_b, **pbr_kw)
    r["name"] = name
    r["description"] = description
    r["category"] = category
    r["style"] = "stylized"
    r["kb_category"] = category.replace("stylized_", "")
    return r


def _build_all():
    R = {}

    def add(key, recipe, *aliases):
        R[key] = recipe
        for a in aliases:
            R[a] = recipe

    # --- METALS ---
    add(
        "stylized_metal_gold",
        _recipe(
            "stylized_metal_gold",
            "Stylized gold — hammered relief, warm 2-tone, high metal",
            "stylized_metal",
            lambda: _height_metal_hammer(perlin_scale=22, cells_scale=7, warp=0.1),
            (0.86, 0.68, 0.22),
            (0.55, 0.35, 0.10),
            roughness=0.28,
            metallic=1.0,
            normal_intensity=3.2,
        ),
        "stylized_gold",
    )
    add(
        "stylized_metal_copper",
        _recipe(
            "stylized_metal_copper",
            "Stylized copper — hammered, warm orange + green tarnish zone",
            "stylized_metal",
            lambda: _height_metal_hammer(perlin_scale=16, cells_scale=6, warp=0.14),
            (0.78, 0.42, 0.22),
            (0.25, 0.48, 0.35),
            roughness=0.4,
            metallic=0.95,
            normal_intensity=3.5,
        ),
        "stylized_copper",
    )
    add(
        "stylized_metal_iron",
        _recipe(
            "stylized_metal_iron",
            "Stylized cast/battered iron — rough relief, cool dark metal",
            "stylized_metal",
            lambda: _height_metal_hammer(perlin_scale=12, cells_scale=5, warp=0.18),
            (0.32, 0.30, 0.30),
            (0.18, 0.14, 0.12),
            roughness=0.62,
            metallic=0.9,
            normal_intensity=4.0,
        ),
        "stylized_iron",
        "stylized_metal",
    )

    # --- STONE / TILE ---
    add(
        "stylized_marble",
        _recipe(
            "stylized_marble",
            "Stylized marble — soft veins, high blend count language, pale 2-tone",
            "stylized_stone",
            lambda: _height_tile_structure(
                cells_scale=3,
                perlin_scale=5,
                hist_pos=0.4,
                hist_contrast=0.35,
                warp_intensity=0.35,
                slope_intensity=0.2,
                dir_warp=0.25,
            ),
            (0.90, 0.88, 0.84),
            (0.55, 0.52, 0.50),
            roughness=0.25,
            metallic=0.0,
            normal_intensity=2.8,
        ),
    )
    add(
        "stylized_brick",
        _recipe(
            "stylized_brick",
            "Stylized bricks — clear cell structure, mortar valleys, warm clay colors",
            "stylized_brick",
            lambda: _height_tile_structure(
                cells_scale=8,
                perlin_scale=14,
                hist_pos=0.48,
                hist_contrast=0.65,
                warp_intensity=0.12,
                slope_intensity=0.22,
                dir_warp=0.1,
            ),
            (0.62, 0.28, 0.18),
            (0.72, 0.68, 0.60),
            roughness=0.78,
            metallic=0.0,
            normal_intensity=4.5,
        ),
        "stylized_bricks",
    )
    add(
        "stylized_stone_pavement",
        _recipe(
            "stylized_stone_pavement",
            "Stylized stone pavement — tile generator language, heavy blends",
            "stylized_stone",
            lambda: _height_tile_structure(
                cells_scale=5,
                perlin_scale=9,
                hist_pos=0.46,
                hist_contrast=0.6,
                warp_intensity=0.15,
                slope_intensity=0.3,
                dir_warp=0.12,
            ),
            (0.55, 0.52, 0.48),
            (0.35, 0.32, 0.28),
            roughness=0.82,
            metallic=0.0,
            normal_intensity=4.2,
        ),
        "stylized_pavement",
        "stylized_cobble",
    )
    add(
        "stylized_stone_rock",
        _recipe(
            "stylized_stone_rock",
            "Stylized rock/cliff — organic breakup + slope blur flow",
            "stylized_stone",
            lambda: _height_organic_flow(
                clouds_scale=3, perlin_scale=8, multi_warp=0.4, dir_warp=0.22
            ),
            (0.48, 0.44, 0.40),
            (0.28, 0.26, 0.24),
            roughness=0.88,
            metallic=0.0,
            normal_intensity=5.0,
        ),
        "stylized_rock",
        "stylized_cliff",
    )
    add(
        "stylized_terrazzo",
        _recipe(
            "stylized_terrazzo",
            "Stylized terrazzo — dense cell chips in pale binder",
            "stylized_stone",
            lambda: _height_tile_structure(
                cells_scale=12,
                perlin_scale=6,
                hist_pos=0.42,
                hist_contrast=0.5,
                warp_intensity=0.1,
                slope_intensity=0.15,
                dir_warp=0.08,
            ),
            (0.85, 0.82, 0.78),
            (0.45, 0.35, 0.30),
            roughness=0.45,
            metallic=0.0,
            normal_intensity=3.0,
        ),
    )
    add(
        "stylized_terracotta",
        _recipe(
            "stylized_terracotta",
            "Stylized terracotta / ceramic — soft clay body, warm orange",
            "stylized_ceramic",
            lambda: _height_tile_structure(
                cells_scale=4,
                perlin_scale=11,
                hist_pos=0.5,
                hist_contrast=0.4,
                warp_intensity=0.18,
                slope_intensity=0.2,
                dir_warp=0.12,
            ),
            (0.72, 0.38, 0.22),
            (0.55, 0.30, 0.18),
            roughness=0.7,
            metallic=0.0,
            normal_intensity=3.2,
        ),
        "stylized_ceramic",
    )
    add(
        "stylized_concrete",
        _recipe(
            "stylized_concrete",
            "Stylized concrete — large soft cells, cool gray, cracks via edges",
            "stylized_stone",
            lambda: _height_tile_structure(
                cells_scale=3,
                perlin_scale=7,
                hist_pos=0.5,
                hist_contrast=0.3,
                warp_intensity=0.1,
                slope_intensity=0.18,
                dir_warp=0.08,
            ),
            (0.62, 0.62, 0.60),
            (0.45, 0.45, 0.44),
            roughness=0.85,
            metallic=0.0,
            normal_intensity=3.0,
        ),
    )

    # --- WOOD ---
    add(
        "stylized_wood_planks",
        _recipe(
            "stylized_wood_planks",
            "Stylized wood planks — stretched grain, plank cuts, warm timber",
            "stylized_wood",
            lambda: _height_wood_grain(perlin_scale=14, ring_scale=7, warp=0.3),
            (0.48, 0.30, 0.14),
            (0.28, 0.16, 0.08),
            roughness=0.72,
            metallic=0.0,
            normal_intensity=3.8,
        ),
        "stylized_wood",
        "stylized_planks",
    )
    add(
        "stylized_wood_parquet",
        _recipe(
            "stylized_wood_parquet",
            "Stylized parquet — tighter grain pattern, polished timber",
            "stylized_wood",
            lambda: _height_wood_grain(perlin_scale=18, ring_scale=10, warp=0.18),
            (0.55, 0.35, 0.16),
            (0.35, 0.20, 0.10),
            roughness=0.48,
            metallic=0.0,
            normal_intensity=3.0,
        ),
        "stylized_parquet",
    )

    # --- GROUND / ORGANIC ---
    add(
        "stylized_ground_grass",
        _recipe(
            "stylized_ground_grass",
            "Stylized lawn/grass — soft multi-dir warp clumps, green 2-tone",
            "stylized_ground",
            lambda: _height_organic_flow(
                clouds_scale=5, perlin_scale=16, multi_warp=0.45, dir_warp=0.25
            ),
            (0.28, 0.52, 0.18),
            (0.15, 0.32, 0.10),
            roughness=0.9,
            metallic=0.0,
            normal_intensity=4.0,
        ),
        "stylized_grass",
    )
    add(
        "stylized_ground_soil",
        _recipe(
            "stylized_ground_soil",
            "Stylized dirt/soil/sand — soft mounds, warm earth tones",
            "stylized_ground",
            lambda: _height_organic_flow(
                clouds_scale=3, perlin_scale=10, multi_warp=0.35, dir_warp=0.18
            ),
            (0.45, 0.32, 0.18),
            (0.28, 0.20, 0.12),
            roughness=0.92,
            metallic=0.0,
            normal_intensity=3.5,
        ),
        "stylized_soil",
        "stylized_dirt",
        "stylized_sand",
    )
    add(
        "stylized_water",
        _recipe(
            "stylized_water",
            "Stylized ocean/water — soft waves, cool blue, low roughness",
            "stylized_water",
            lambda: _height_organic_flow(
                clouds_scale=2, perlin_scale=6, multi_warp=0.5, dir_warp=0.3
            ),
            (0.15, 0.42, 0.65),
            (0.08, 0.22, 0.40),
            roughness=0.12,
            metallic=0.05,
            normal_intensity=5.5,
        ),
        "stylized_ocean",
    )

    # --- SCIFI / FANTASY ---
    add(
        "stylized_scifi",
        _recipe(
            "stylized_scifi",
            "Stylized sci-fi panel — hard edges, histogram panels, cool metal-paint",
            "stylized_scifi",
            lambda: _height_scifi_panel(),
            (0.35, 0.40, 0.48),
            (0.12, 0.14, 0.18),
            roughness=0.45,
            metallic=0.35,
            normal_intensity=3.5,
        ),
        "stylized_sci_fi",
    )
    add(
        "stylized_corrupted",
        _recipe(
            "stylized_corrupted",
            "Stylized corrupted fantasy surface — multi-dir warp, dark + accent",
            "stylized_fantasy",
            lambda: _height_organic_flow(
                clouds_scale=4, perlin_scale=9, multi_warp=0.55, dir_warp=0.28
            ),
            (0.22, 0.10, 0.28),
            (0.55, 0.12, 0.18),
            roughness=0.7,
            metallic=0.15,
            normal_intensity=5.0,
        ),
        "stylized_corruption",
    )
    add(
        "stylized_fabric",
        _recipe(
            "stylized_fabric",
            "Stylized fabric/wool/carpet — soft warp weave feel",
            "stylized_fabric",
            lambda: _height_organic_flow(
                clouds_scale=8, perlin_scale=20, multi_warp=0.25, dir_warp=0.2
            ),
            (0.45, 0.22, 0.18),
            (0.28, 0.14, 0.12),
            roughness=0.88,
            metallic=0.0,
            normal_intensity=2.5,
        ),
        "stylized_wool",
        "stylized_carpet",
    )
    add(
        "stylized_crystal",
        _recipe(
            "stylized_crystal",
            "Stylized crystal/gem — faceted cells, saturated color, low rough",
            "stylized_crystal",
            lambda: _height_tile_structure(
                cells_scale=4,
                perlin_scale=3,
                hist_pos=0.55,
                hist_contrast=0.7,
                warp_intensity=0.05,
                slope_intensity=0.1,
                dir_warp=0.05,
            ),
            (0.55, 0.25, 0.75),
            (0.25, 0.10, 0.40),
            roughness=0.15,
            metallic=0.05,
            normal_intensity=6.0,
        ),
        "stylized_gem",
    )

    return R


STYLIZED_RECIPE_REGISTRY = _build_all()


def list_stylized_recipe_keys():
    # unique by identity
    seen = set()
    keys = []
    for k, v in STYLIZED_RECIPE_REGISTRY.items():
        i = id(v)
        if i in seen:
            continue
        seen.add(i)
        keys.append(k)
    return sorted(keys)


def get_stylized_recipe(name: str):
    if not name:
        return None
    key = name.lower().replace(" ", "_").replace("-", "_")
    if key in STYLIZED_RECIPE_REGISTRY:
        return STYLIZED_RECIPE_REGISTRY[key]
    # allow dropping stylized_ prefix miss
    if not key.startswith("stylized_"):
        return STYLIZED_RECIPE_REGISTRY.get("stylized_" + key)
    return None
