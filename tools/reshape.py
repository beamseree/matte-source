"""Reshape t's foot, the C, G, S and s terminals and P's bowl to match the mockups, and set
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
- Crossbars: the mockups' f and t bars are the same height. f's, f.1's and t.1's take t's
  (Black's came out 24 units deeper than t's, which tools/redraw.py sets to the mockup's).
- C, G, S and s: the mockups cut the terminals at an angle (8-22 degrees), where Inter's
  are flat (or, in s, shallower). Each terminal is cut along the mockup's line from
  TERMINALS: the curves on either side are trimmed, or extended along their own path, to
  meet it, so the letter keeps its points. Thin's screenshot is too blurred to show its
  terminals' cuts, so Thin tilts each of its own C and G cuts about its middle to Regular's
  angle; its S and s cuts are at Regular's angles where the screenshot's strokes end.
- S and s: the curves either side of each cut, from its corners to the extremes either
  side, take the mockup's shape (ARMS, Regular and Black). Inter's arms came down more
  steeply into the terminals, so they were up to 70 units deeper there, and its s
  terminals stopped short of the mockups', the lower one most.
- P: the mockups' bowl is shorter. Its lower bar moves up to P_BAR's heights, and the
  bowl's outer and inner curves are scaled between the bar and their tops.

Every master gets the same points, so the masters stay compatible, and every changed
glyph keeps its right sidebearing. Running it again changes nothing.

Usage: python tools/reshape.py source/PlaceholderSans-*.ufo
       python tools/reshape.py --fit [source]    # print ARMS fitted to the mockups
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
# cubics fitted to the SVG's two (within 1.3 units). In both mockups t's foot is f's top
# upside down, within a few units; Thin's screenshot is too blurred to measure, so Thin's
# foot is its own f top (`_part.f_base`) turned upside down: the same curves, reach and
# 46-unit thickness.
FOOT = {
    "Thin": dict(bottom=-4, top=42, reach=298,
                 outer=((0, 213), (0, 80), (82, 0), (235, 0)),
                 inner=((189, 0), (66, 0), (0, 63), (0, 167))),
    "Regular": dict(bottom=-4.1, top=173.9, reach=281.5,
                    outer=((0, 267), (0, 101.4), (97.3, 0), (281.4, 0)),
                    inner=((113.8, 0), (35.2, 0), (0, 33.1), (0, 107.6))),
    "Black": dict(bottom=-4, top=315, reach=269,
                  outer=((0, 381), (0, 45.9), (243.5, 0), (385, 0)),
                  inner=((100, 0), (67.6, 0), (0, 4.1), (0, 93))),
}

# The mockups' terminal cuts, one line per terminal in contour order, each from the end of
# the curve before the cut to the start of the curve after it. x is from the letter's left
# edge (C, G) or right edge (S, s), which the cuts don't move. Thin's S and s cuts are at
# Regular's angles, where its screenshot's strokes end: thinned to 46 units, they reach
# further round than Inter's, by 60 units at S's lower terminal, 30 and 34 at s's lower and
# upper ones (give or take 20); S's upper one is where it was.
TERMINALS = {
    "C": ("left", {"Regular": [((1351.1, 502.9), (1150.4, 550.5)), ((1154.5, 941.6), (1355.3, 974.7))],
                   "Black": [((1437, 515), (1050, 573)), ((1045, 917), (1432, 975))]}),
    "G": ("left", {"Regular": [((1140.3, 1034.7), (1349.1, 1080.3))],
                   "Black": [((1062, 969), (1443, 1051))]}),
    "S": ("right", {"Thin": [((-69, 1113), (-23, 1123)), ((-999, 416), (-1047, 406))],
                    "Regular": [((-249.9, 1061.6), (-42.9, 1111.3)), ((-982.5, 461.5), (-1191.5, 416.0))],
                    "Black": [((-439, 1035), (-75, 1161)), ((-900, 480), (-1279, 346))]}),
    "s": ("right", {"Thin": [((-48, 803), (-2, 818)), ((-757, 289), (-803, 275))],
                    "Regular": [((-217.3, 757.4), (-31.1, 817.4)), ((-714.0, 351.8), (-906.4, 295.9))],
                    "Black": [((-368.3, 718.1), (-53.8, 827.8)), ((-672.6, 360.1), (-991.3, 229.7))]}),
}

# S's and s's terminals, fitted to the mockups by `--fit`: {master: {glyph: [(point, x from
# the right edge, y)]}}. Each cut's corners are the mockup's, and the curves from them to the
# extremes either side (the top, the bottom and the counters' top and bottom, which stay)
# have their handles fitted by least squares to the mockup's outline.
ARMS = {
    "Regular": {
        "S": [(14, -386.6, 1318), (15, -286.5, 1182), (16, -249.9, 1062), (17, -42.9, 1111),
            (18, -115.5, 1395), (19, -357.1, 1510), (34, -721.3, 168), (35, -922.5, 210),
            (36, -982.5, 462), (37, -1191.5, 416), (38, -1092.6, 21), (39, -749.8, -25)],
        "s": [(14, -395.6, 921), (15, -272.9, 907), (16, -217.3, 757), (17, -31.1, 817),
            (18, -115.5, 1093), (19, -408.9, 1101), (34, -472.7, 151), (35, -667.3, 158),
            (36, -714.0, 352), (37, -906.4, 296), (38, -818.6, 14), (39, -578.5, -23)],
    },
    "Black": {
        "S": [(14, -585.3, 1177), (15, -510.0, 1177), (16, -439.0, 1035), (17, -75.0, 1161),
            (18, -160.0, 1405), (19, -404.8, 1510), (34, -728.1, 315), (35, -821.5, 315),
            (36, -900.0, 480), (37, -1279.0, 346), (38, -1145.5, -18), (39, -787.5, -18)],
        "s": [(14, -488.7, 822), (15, -400.6, 804), (16, -368.3, 718), (17, -53.8, 828),
            (18, -116.6, 980), (19, -272.5, 1101), (34, -533.8, 252), (35, -621.6, 252),
            (36, -672.6, 360), (37, -991.3, 230), (38, -886.9, -20), (39, -595.2, -20)],
    },
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


def arm_curves(contour, i):
    """The curves either side of the cut at i, each from its extreme to the cut's corner."""
    n = len(contour.points)
    return [[(i - k) % n for k in (3, 2, 1, 0)], [(i + k) % n for k in (4, 3, 2, 1)]]


def set_arms(font, glyph, master):
    edge = glyph.getBounds(font).xMax
    for i, dx, y in ARMS[master][glyph.name]:
        p = glyph.contours[0].points[i]
        p.x, p.y = round(edge + dx), y


def fit_arms(master, src):
    """ARMS for one master: the mockup's corners, and handles fitted to its outline."""
    import joints  # its least-squares helpers (it imports this module, so not at the top)
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.transformPen import TransformPen

    font = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
    table = {}
    for name in ("S", "s"):
        glyph, rows = font[name], []
        set_terminals(font, glyph, master)
        edge = glyph.getBounds(font).xMax
        bp = BoundsPen(None)
        joints.mockup(master, name)(bp)
        rec = RecordingPen()                        # the mockup, on our right edge
        joints.mockup(master, name)(TransformPen(rec, (1, 0, 0, 1, edge - bp.bounds[2], 0)))
        segs = joints.segments(rec)
        pts = glyph.contours[0].points
        for k, i in enumerate(terminals(glyph.contours[0])):
            corners = [(edge + x, y) for x, y in TERMINALS[name][1][master][k]]
            for idx, corner in zip(arm_curves(glyph.contours[0], i), corners):
                E, H, _, _ = [np.array((pts[j].x, pts[j].y), float) for j in idx]
                C = np.array(corner)
                # the mockup's outline from this corner, away from the cut, to its extreme
                j = next(j for j, s in enumerate(segs) if len(s) == 2 and
                         min(np.hypot(*(np.array(p) - C)) for p in s) < 1 and
                         max(np.hypot(*(np.array(p) - C)) for p in s) > 50)
                step = 1 if np.hypot(*(np.array(segs[j][1]) - C)) < 1 else -1
                stretch = []
                while True:
                    j = (j + step) % len(segs)
                    seg = segs[j] if step == 1 else segs[j][::-1]
                    stretch.append(joints.bezier(seg, np.linspace(0, 1, 150)) if len(seg) == 4
                                   else np.linspace(seg[0], seg[1], 50))
                    if len(seg) == 4 and abs(seg[2][1] - seg[3][1]) < 0.5:
                        break                       # a horizontal tangent: the extreme
                stretch = np.vstack(stretch)
                # only up to our own extreme, which stays
                stretch = stretch[(stretch[:, 0] - E[0]) * np.sign(C[0] - E[0]) >= 0]
                u = (H - E) / np.hypot(*(H - E))
                span = abs(C[0] - E[0])
                lo, hi = np.minimum(E, C), np.maximum(E, C)   # so the extremes stay extremes
                build = lambda x, E=E, u=u, span=span, C=C: [E, E + x[0] * span * u, (x[1], x[2]), C]
                x0 = [np.hypot(*(H - E)) / span, *(np.array((pts[idx[2]].x, pts[idx[2]].y)))]
                Q, err = joints.solve(x0, ([0.05, lo[0], lo[1]], [1.5, hi[0], hi[1]]), build, stretch)
                print(f"  {master} {name} {idx}: {len(stretch)} targets, rms {np.sqrt(np.mean(err ** 2)):.1f}, "
                      f"max {err.max():.1f}", file=sys.stderr)
                for j, q in zip(idx[1:], Q[1:]):
                    rows.append((j, round(float(q[0]) - edge, 1), round(float(q[1]))))
        table[name] = sorted(rows)
    return table


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


def match_bars(font, names):
    """Give the crossbars of `names` (each glyph's one four-point contour) t's height."""
    bar = font["t"].contours[0].points
    bottom, top = min(p.y for p in bar), max(p.y for p in bar)
    for name in names:
        if len(font[name].contours) != 1 or len(font[name].contours[0]) != 4:
            raise ValueError(f"{name}: expected one four-point crossbar")
        points = font[name].contours[0].points
        low = min(p.y for p in points)
        for p in points:
            p.y = bottom if p.y == low else top


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
    match_bars(ufo, ("f", "f.1", "t.1"))
    for name in TERMINALS:
        set_terminals(ufo, ufo[name], master)
    for name in ARMS.get(master, {}):
        set_arms(ufo, ufo[name], master)
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
    if sys.argv[1:2] == ["--fit"]:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        src = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "source")
        print({m: fit_arms(m, src) for m in ("Regular", "Black")})
    else:
        main(sys.argv[1:])
