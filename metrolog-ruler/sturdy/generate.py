#!/usr/bin/env python3
"""Sturdy sliding caliper-ruler, an original design in the spirit of the Craighill Metrolog.

Generates two STL files (both print flat, scale side up, no supports):
  sturdy_ruler_body.stl    34 x 200 x 12 mm bar with a dovetail channel
  sturdy_ruler_slider.stl  head (jaw) and dovetail rail in one piece, 226 mm long

Requires: pip install manifold3d numpy matplotlib
Usage:    python3 generate.py [output_dir]
All dimensions are millimetres. Edit the parameters below and re-run.
"""
import struct
import sys
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

# ---------------------------------------------------------------- parameters
W = 34.0            # overall width
T = 12.0            # body thickness
LB = 200.0          # body length
FLOOR = 4.0         # body material under the channel
HEAD_L = 30.0       # head length
HEAD_R = 15.0       # big head corner radius (30 mm circle template)
RAIL_L = 196.0      # rail length below the jaw face
RAIL_H = 7.75       # rail and head thickness
RAIL_TOP = 14.0     # rail width at the top face
RAIL_BASE = 20.0    # rail width at the dovetail base
BASE_H = 1.0        # height of the vertical part of the dovetail base
SIDE_GAP = 0.2      # clearance each side of the rail's top section
TAPER_GAP = 0.25    # clearance on the 45 degree dovetail faces
TRAVEL = 148.0      # jaw opening at the end stop

# Spring tongue in the body floor: end stop plus sliding friction.
TONGUE_W = 8.0
TONGUE_ROOT = LB - 4.0      # y of the fixed end
BUMP_FACE = LB - 39.0       # y of the bump's vertical stop face
BUMP_W = 6.0
BUMP_TOP = 2.05             # bump height above the channel floor
SLOT = 1.0                  # width of the U-slot around the tongue
RELIEF = 0.6                # recess under the tongue so it never touches the desk
GROOVE_W = 7.0              # groove under the rail that the bump runs in
GROOVE_D = 1.4

ENGRAVE = 0.6       # depth of ticks and numbers
TICK_W = 0.45
SCALE_Y0 = 5.0      # y of the zero mark of both body scales
EPS = 0.01


# ------------------------------------------------------------------ helpers
def prism_y(profile_xz, y0, y1):
    """Extrude an (x, z) profile along y from y0 to y1."""
    m = CrossSection([np.array(profile_xz, float)], FillRule.EvenOdd).extrude(y1 - y0)
    return m.transform(np.array([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]], float))


def prism_x(profile_yz, x0, x1):
    """Extrude a (y, z) profile along x from x0 to x1."""
    m = CrossSection([np.array(profile_yz, float)], FillRule.EvenOdd).extrude(x1 - x0)
    return m.transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]], float))


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def rect(x0, x1, y0, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)


def rounded_outline(x0, x1, y0, y1, radii, n=24):
    """Rectangle with per-corner radii (bl, br, tr, tl), counter-clockwise."""
    corners = [(x0, y0, 180), (x1, y0, 270), (x1, y1, 0), (x0, y1, 90)]
    pts = []
    for (cx, cy, a0), r in zip(corners, radii):
        if r <= 0:
            pts.append((cx, cy))
            continue
        ox = cx + (r if cx == x0 else -r)
        oy = cy + (r if cy == y0 else -r)
        for a in np.radians(np.linspace(a0, a0 + 90, n)):
            pts.append((ox + r * np.cos(a), oy + r * np.sin(a)))
    return np.array(pts, float)


_font = FontProperties(family="DejaVu Sans", weight="bold")
_digit_h = TextPath((0, 0), "0", size=10, prop=_font).get_extents().height


def text_contours(s, height, cx, cy):
    """Contours of string s, cap height `height`, rotated 90 deg, centred on (cx, cy)."""
    tp = TextPath((0, 0), s, size=10, prop=_font)
    k = height / _digit_h
    ext = tp.get_extents()
    mx, my = (ext.x0 + ext.x1) / 2, (ext.y0 + ext.y1) / 2
    out = []
    for poly in tp.to_polygons():
        p = (np.asarray(poly)[:-1] - [mx, my]) * k
        out.append(np.column_stack([cx - p[:, 1], cy + p[:, 0]]))  # rotate +90 deg
    return out


def engraving(rects, texts, z_top):
    """Solid to subtract: tick rectangles plus text, ENGRAVE deep below z_top."""
    parts = [CrossSection(rects, FillRule.Positive)]
    if texts:
        parts.append(CrossSection(texts, FillRule.EvenOdd))
    cs = CrossSection.batch_boolean(parts, OpType.Add)
    return cs.extrude(ENGRAVE + 1).translate([0, 0, z_top - ENGRAVE])


def tick(x_edge, length, y):
    """Tick starting at the outer edge x_edge and running towards the centre."""
    x_in = x_edge - np.sign(x_edge) * length
    return rect(min(x_edge, x_in), max(x_edge, x_in), y - TICK_W / 2, y + TICK_W / 2)


# --------------------------------------------------------------------- body
def make_body():
    body = CrossSection([rounded_outline(-W / 2, W / 2, 0, LB, (3, 3, 0, 0))]).extrude(T)

    # Dovetail channel, closed at the bottom end, open at the jaw end.
    hb = RAIL_BASE / 2 + TAPER_GAP          # half width at the floor
    ht = RAIL_TOP / 2 + SIDE_GAP            # half width at the top face
    z1 = FLOOR + BASE_H                     # taper starts
    z2 = z1 + (hb - ht)                     # taper ends (45 degrees)
    profile = [(-hb, FLOOR), (hb, FLOOR), (hb, z1), (ht, z2), (ht, T + 1),
               (-ht, T + 1), (-ht, z2), (-hb, z1)]
    body -= prism_y(profile, LB - RAIL_L - 0.5, LB + 1)

    # Spring tongue: U-slot through the floor, relief pocket underneath.
    tip = BUMP_FACE - 2.0
    hw = TONGUE_W / 2
    slot = box(-hw - SLOT, hw + SLOT, tip - SLOT, TONGUE_ROOT, -1, FLOOR + EPS)
    slot -= box(-hw, hw, tip, TONGUE_ROOT + 1, -2, FLOOR + 1)
    body -= slot
    body -= box(-hw - SLOT, hw + SLOT, tip - SLOT, TONGUE_ROOT, -1, RELIEF)

    # Bump: vertical stop face towards the bottom end, ramp towards the jaw end.
    zb = FLOOR + BUMP_TOP
    bump = prism_x([(BUMP_FACE, FLOOR - 0.5), (BUMP_FACE, zb), (BUMP_FACE + 2.5, zb),
                    (BUMP_FACE + 6.0, FLOOR), (BUMP_FACE + 6.0, FLOOR - 0.5)],
                   -BUMP_W / 2, BUMP_W / 2)
    body += bump

    # Scales: millimetres on the left edge, inches on the right edge.
    rects, texts = [], []
    for i in range(0, 191):
        length = 5.5 if i % 10 == 0 else 4.2 if i % 5 == 0 else 2.8
        rects.append(tick(-W / 2, length, SCALE_Y0 + i))
        if i % 10 == 0:
            label, h = (str(i // 10), 3.0) if i else ("cm", 2.4)
            texts += text_contours(label, h, -W / 2 + 7.6, SCALE_Y0 + i)
    for i in range(0, 121):                 # sixteenths up to 7.5 in
        length = (5.5 if i % 16 == 0 else 4.6 if i % 8 == 0 else 3.7 if i % 4 == 0
                  else 2.8 if i % 2 == 0 else 2.0)
        y = SCALE_Y0 + i * 25.4 / 16
        rects.append(tick(W / 2, length, y))
        if i % 16 == 0:
            label, h = (str(i // 16), 3.0) if i else ("in", 2.4)
            texts += text_contours(label, h, W / 2 - 7.6, y)
    body -= engraving(rects, texts, T)
    return body


# ------------------------------------------------------------------- slider
def make_slider():
    """Print coordinates: z = 0 is the rail underside, jaw face at y = 0, rail in y < 0."""
    head = CrossSection([rounded_outline(-W / 2, W / 2, 0, HEAD_L, (0, 0, 4, HEAD_R))])
    slider = head.extrude(RAIL_H)

    hb, ht, c = RAIL_BASE / 2, RAIL_TOP / 2, 0.3
    zt = BASE_H + (hb - ht)
    profile = [(-hb + c, 0), (hb - c, 0), (hb, c), (hb, BASE_H), (ht, zt), (ht, RAIL_H),
               (-ht, RAIL_H), (-ht, zt), (-hb, BASE_H), (-hb, c)]
    slider += prism_y(profile, -RAIL_L, 1.0)

    # Groove for the bump. Its closed tail end is the end stop.
    g0 = (LB - BUMP_FACE) - 7.5             # rail position of the groove start
    g1 = (LB - BUMP_FACE) + TRAVEL          # rail position of the stop wall
    slider -= box(-GROOVE_W / 2, GROOVE_W / 2, -g1, -g0, -1, GROOVE_D)
    # Lead-in under the tail so it rides over the bump during assembly.
    slider -= prism_x([(-RAIL_L - 1, -1), (-RAIL_L + 2.5, -1), (-RAIL_L + 2.5, 0),
                       (-RAIL_L - 1, 1.6)], -GROOVE_W / 2, GROOVE_W / 2)

    # Caliper scale on the rail, read where the rail leaves the body.
    rects, texts = [], []
    for i in range(1, int(TRAVEL) + 1):
        length = 5.5 if i % 10 == 0 else 4.2 if i % 5 == 0 else 2.8
        rects.append(tick(ht, length, -i))
        if i % 10 == 0:
            texts += text_contours(str(i // 10), 3.0, ht - 8.6, -i)
    # Thumb grooves on the head.
    for y in (8.0, 11.5, 15.0, 18.5):
        rects.append(rect(-9.0, 12.0, y - 0.6, y + 0.6))
    slider -= engraving(rects, texts, RAIL_H)
    return slider


# ------------------------------------------------------------------- output
def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float32)
    tris = v[np.asarray(mesh.tri_verts)]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tris
    with open(path, "wb") as f:
        f.write(b"sturdy sliding ruler".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.write(rec.tobytes())


def assembled(slider, opening, seated=True):
    """Slider moved into body coordinates at a given jaw opening."""
    lift = FLOOR + (TAPER_GAP if seated else 0.0)
    return slider.translate([0, LB + opening, lift])


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
    body, slider = make_body(), make_slider()
    for name, m in (("sturdy_ruler_body.stl", body), ("sturdy_ruler_slider.stl", slider)):
        write_stl(m, out / name)
        bb = m.bounding_box()
        size = [round(bb[i + 3] - bb[i], 2) for i in range(3)]
        print(f"{name}: {m.num_tri()} triangles, {size} mm, {m.volume() / 1000:.1f} cm3")
