"""Reshape t's foot, the C, G and S terminals and P's bowl to match the mockups, and set
f's and t's stems where they're heavier than the master's other lowercase stems.

These are the places where Inter's construction differs from the mockups', rather than
its curves:

- t: the mockups end the stem in a flat foot with an upright cut, like f's top
  (`_part.f_base`), where Inter curves it up into a hook. `_part.t_base`, which t and t.1
  share, becomes 12 points: the stem's left edge and top stay, and FOOT gives the foot's
  bottom and top, how far it reaches past the stem's right edge, and its two curves. The
  foot now reaches past the crossbar, as in the mockups, so t, t.1 and every glyph built
  on them keep their right sidebearings and get wider.
- f and t stems: STEM sets them in masters where they came out heavier than the other
  lowercase stems, by moving the stem's right edge and everything on it (f's inner
  corner, t's foot, and t's crossbar, which tools/redraw.py places from the stem's edges).
  The left edge, f's terminal and f's crossbar stay where they are.
- C, G and S: the mockups cut the terminals at an angle (8-20 degrees), where Inter's are
  flat. Each terminal is cut along the mockup's line from TERMINALS: the curves on either
  side are trimmed, or extended along their own path, to meet it, so the letter keeps its
  points. Thin's screenshot is too blurred to show its terminals, so Thin tilts each of
  its own cuts about its middle to Regular's angle.
- P: the mockups' bowl is shorter. Its lower bar moves up to P_BAR's heights, and the
  bowl's outer and inner curves are scaled between the bar and their tops.

Every master gets the same points, so the masters stay compatible, and every changed
glyph keeps its right sidebearing. Running it again changes nothing.

Usage: python tools/reshape.py source/PlaceholderSans-*.ufo
"""

import os
import re
import sys

import numpy as np
import ufoLib2
from fontTools.ufoLib.glifLib import GlyphSet
from ufoLib2.objects import Point

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import redraw  # noqa: E402

# f's and t's stem width where it differs from the master's other lowercase stems. Black's
# came out 373 (f) and 374 (t), against 350-357 for i, l, n, r and the rest, and the
# mockup's 352 for both.
STEM = {"Black": 352}

# t's foot, from mockup.svg (Regular) and mockup-black.svg (Black): its bottom and top, how
# far it reaches past the stem's right edge, and its outer curve (leaving the stem, down to
# the bottom; from the stem's left edge and the bottom) and inner curve (leaving the foot's
# top, up to the stem; from the stem's right edge and the top). Black's curves are single
# cubics fitted to the SVG's two (within 1.3 units). Thin's screenshot only shows the foot
# reaching 25 units past the crossbar, so its curves are a 46-unit stroke turning the
# corner the screenshot's does.
FOOT = {
    "Thin": dict(bottom=-4, top=42, reach=296.7,
                 outer=((0, 213), (0, 85.2), (69.2, 0), (173, 0)),
                 inner=((127, 0), (50.8, 0), (0, 66.8), (0, 167))),
    "Regular": dict(bottom=-4.1, top=173.9, reach=281.5,
                    outer=((0, 267), (0, 101.4), (97.3, 0), (281.4, 0)),
                    inner=((113.8, 0), (35.2, 0), (0, 33.1), (0, 107.6))),
    "Black": dict(bottom=-4, top=315, reach=269,
                  outer=((0, 381), (0, 45.9), (243.5, 0), (385, 0)),
                  inner=((100, 0), (67.6, 0), (0, 4.1), (0, 93))),
}

# The mockups' terminal cuts, one line per terminal in contour order, each from the end of
# the curve before the cut to the start of the curve after it. x is from the letter's left
# edge (C, G) or right edge (S), which the cuts don't move.
TERMINALS = {
    "C": ("left", {"Regular": [((1351.1, 502.9), (1150.4, 550.5)), ((1154.5, 941.6), (1355.3, 974.7))],
                   "Black": [((1437, 515), (1050, 573)), ((1045, 917), (1432, 975))]}),
    "G": ("left", {"Regular": [((1140.3, 1034.7), (1349.1, 1080.3))],
                   "Black": [((1062, 969), (1443, 1051))]}),
    "S": ("right", {"Regular": [((-249.9, 1061.6), (-42.9, 1111.3)), ((-982.5, 461.5), (-1191.5, 416.0))],
                    "Black": [((-439, 1035), (-75, 1161)), ((-900, 480), (-1279, 346))]}),
}

# P's lower bar (bottom, top). Regular's and Black's are the SVGs'; Thin's is centred on its
# screenshot's bar, which is drawn heavier.
P_BAR = {"Thin": (687, 733), "Regular": (617, 803), "Black": (513, 840)}


def lerp(a, b, t):
    return tuple(p + t * (q - p) for p, q in zip(a, b))


def bezier(P, t):
    return lerp(lerp(lerp(P[0], P[1], t), lerp(P[1], P[2], t), t),
                lerp(lerp(P[1], P[2], t), lerp(P[2], P[3], t), t), t)


def head(P, t):
    """Cubic P from 0 to t (t > 1 extends it)."""
    return [P[0], lerp(P[0], P[1], t), lerp(lerp(P[0], P[1], t), lerp(P[1], P[2], t), t), bezier(P, t)]


def tail(P, t):
    """Cubic P from t to 1 (t < 0 extends it)."""
    return [bezier(P, t), lerp(lerp(P[1], P[2], t), lerp(P[2], P[3], t), t), lerp(P[2], P[3], t), P[3]]


def crossing(P, a, b, near):
    """Where cubic P meets the line through a and b: the parameter nearest `near`."""
    nx, ny = a[1] - b[1], b[0] - a[0]
    s0, s1, s2, s3 = (nx * (p[0] - a[0]) + ny * (p[1] - a[1]) for p in P)
    roots = np.roots([-s0 + 3 * s1 - 3 * s2 + s3, 3 * s0 - 6 * s1 + 3 * s2, 3 * s1 - 3 * s0, s0])
    ts = [r.real for r in roots if abs(r.imag) < 1e-9 and -0.5 < r.real < 1.5]
    return min(ts, key=lambda t: abs(t - near))


def terminals(contour):
    """Indices of each cut's first point: a curve's end, then a line to a curve, meeting at
    a corner (S's spine has smooth lines between curves too)."""
    pts, n = contour.points, len(contour.points)
    def corner(i):
        h, q, p = pts[i - 1], pts[i], pts[(i + 1) % n]
        u, v = (q.x - h.x, q.y - h.y), (p.x - q.x, p.y - q.y)
        return abs(u[0] * v[1] - u[1] * v[0]) > 0.5 * np.hypot(*u) * np.hypot(*v)
    return [i for i in range(n) if pts[i].type == "curve" and pts[(i + 1) % n].type == "line"
            and pts[(i + 2) % n].type is None and corner(i)]


def cut(contour, i, a, b):
    """Trim or extend the curves on either side of the cut at i to meet the line a-b."""
    pts, n = contour.points, len(contour.points)
    before = [(i - k) % n for k in (3, 2, 1, 0)]
    after = [(i + k) % n for k in (1, 2, 3, 4)]
    if pts[before[0]].type is None or pts[after[3]].type != "curve":
        raise ValueError("terminal: expected a cubic on each side of the cut")
    nx, ny = a[1] - b[1], b[0] - a[0]
    if all(abs(nx * (pts[k].x - a[0]) + ny * (pts[k].y - a[1])) <= np.hypot(nx, ny)
           for k in (i, (i + 1) % n)):
        return  # already cut there, give or take rounding
    for idx, part, near in ((before, head, 1), (after, tail, 0)):
        P = [(pts[k].x, pts[k].y) for k in idx]
        for k, (x, y) in zip(idx, part(P, crossing(P, a, b, near))):
            pts[k].x, pts[k].y = round(x), round(y)


def set_terminals(font, glyph, master):
    side, lines = TERMINALS[glyph.name]
    box = glyph.getBounds(font)
    edge = box.xMin if side == "left" else box.xMax
    contour = glyph.contours[0]
    cuts = terminals(contour)
    if len(cuts) != len(lines["Regular"]):
        raise ValueError(f"{glyph.name}: expected {len(lines['Regular'])} terminals")
    for k, i in enumerate(cuts):
        if master in lines:
            a, b = ((edge + x, y) for x, y in lines[master][k])
        else:
            (ax, ay), (bx, by) = lines["Regular"][k]
            q, p = contour.points[i], contour.points[i + 1]
            a = ((q.x + p.x) / 2, (q.y + p.y) / 2)
            b = (a[0] + bx - ax, a[1] + by - ay)
        cut(contour, i, a, b)


def set_foot(glyph, foot, stem=None):
    pts = glyph.contours[0].points
    (left, top), (right, top_right) = (pts[0].x, pts[0].y), (pts[-1].x, pts[-1].y)
    if len(glyph.contours) != 1 or top != top_right:
        raise ValueError("_part.t_base: expected one contour from the stem's top-left to its top-right")
    if stem:
        right = left + stem
    bottom, foot_top, end = foot["bottom"], foot["top"], right + foot["reach"]
    o = [(left + x, bottom + y) for x, y in foot["outer"]]
    i = [(right + x, foot_top + y) for x, y in foot["inner"]]
    shape = [(left, top, "line"), (*o[0], "line"), (*o[1], None), (*o[2], None), (*o[3], "curve"),
             (end, bottom, "line"), (end, foot_top, "line"),
             (*i[0], "line"), (*i[1], None), (*i[2], None), (*i[3], "curve"), (right, top, "line")]
    smooth = {1, 4, 7, 10}  # where the curves meet the stem and the foot
    pts[:] = [Point(round(x), round(y), t, k in smooth) for k, (x, y, t) in enumerate(shape)]


def set_f_stem(glyph, stem):
    """Move the right edge of f's stem, with its inner corner, to make the stem `stem` wide."""
    pts = glyph.contours[0].points
    if len(glyph.contours) != 1 or len(pts) != 12 or pts[0].y != 0 or pts[1].y != 0:
        raise ValueError("_part.f_base: expected the 12-point flat-topped f, from the stem's foot")
    shift = pts[0].x + stem - pts[1].x
    for p in pts[1:6]:  # the stem's right edge, up its inner corner to the top's underside
        p.x += shift


def set_bowl(glyph, bar):
    """Move P's lower bar to `bar`, scaling the bowl's outer and inner curves to fit."""
    pts = glyph.contours[0].points
    if len(glyph.contours) != 1 or len(pts) != 20:
        raise ValueError("P: expected Inter's 20-point outline")
    bottom, top = bar
    inner_top, outer_top = pts[2].y, pts[19].y        # the counter's top, the cap height
    old_top, old_bottom = pts[9].y, pts[11].y         # the bar's
    for k, p in enumerate(pts):
        if 2 <= k <= 10:
            p.y = round(inner_top - (inner_top - p.y) * (inner_top - top) / (inner_top - old_top))
        elif 11 <= k <= 19:
            p.y = round(outer_top - (outer_top - p.y) * (outer_top - bottom) / (outer_top - old_bottom))


def users(font, names):
    """The glyphs named and every glyph built on them, through components at any depth."""
    out, grew = set(names), True
    while grew:
        grew = False
        for g in font:
            if g.name not in out and any(c.baseGlyph in out for c in g.components):
                out.add(g.name)
                grew = True
    return out


def outline(font, name):
    g = font[name]
    return (g.width, [[(p.x, p.y, p.type, p.smooth) for p in c.points] for c in g.contours])


def apply(ufo, master):
    """Reshape the letters in `ufo`; returns the names of the glyphs that changed."""
    touched = users(ufo, ("_part.t_base", "_part.f_base", "P", *TERMINALS))
    before = {name: outline(ufo, name) for name in touched}
    right = {name: ufo[name].getBounds(ufo).xMax for name in touched if ufo[name].getBounds(ufo)}
    stem = STEM.get(master)
    set_foot(ufo["_part.t_base"], FOOT[master], stem)
    if stem:
        set_f_stem(ufo["_part.f_base"], stem)
        redraw.set_t_bar(ufo, ufo["t"], redraw.T_BAR[master])   # placed from the stem's edges
    for name in TERMINALS:
        set_terminals(ufo, ufo[name], master)
    set_bowl(ufo["P"], P_BAR[master])
    for name in right:
        if not name.startswith("_part."):
            ufo[name].width += round(ufo[name].getBounds(ufo).xMax - right[name])
    return sorted(name for name in touched if outline(ufo, name) != before[name])


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {', '.join(changed) or 'nothing'} reshaped ({master})")


if __name__ == "__main__":
    main(sys.argv[1:])
