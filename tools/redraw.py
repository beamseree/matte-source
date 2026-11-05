"""Redraw N, K, k, w, A, V, v, W, M and Y with straight strokes, set E's and F's bars and
Q's tail, and set the t crossbar and the i/j dots, to match the mockups.

Inter joins N's diagonal and w's strokes with curved, overlapping "open corners", curves
K's arm into the stem, tapers w's inner strokes, and has a shorter t crossbar than the
mockups; A, V, v, W, M and Y have curved joints at their inner vertices too. The mockups
draw all of these as straight polygons with a small flat notch where one stroke meets
another. So:

- N, K, k and w become the mockups' polygons (12, 13, 13 and 16 points), built from the
  edge lines below. Each letter keeps its outer edges (xMin, xMax, height), so advance
  widths and spacing don't change: stems are set inward from the outer edges at their
  measured widths, and everything else is placed in proportion between xMin and xMax
  (N's diagonal keeps its measured horizontal width). Thin's lines are its own current
  strokes, so in Thin only the curved joints change.
- A, V, v, W, M and Y (8, 8, 8, 16, 16 and 10 points; A also has its bar), E and F, and
  Q's tail take the mockups' points from POLYGONS, placed in proportion on our frame.
  Thin keeps its own strokes: each curved joint becomes a flat notch where its edges meet.
  Q's tail then starts nearer the bowl (Q_TAIL_START) and reaches further below the
  baseline (Q_TAIL_DEPTH), in every master.
- The t crossbar reaches T_BAR's distances past the stem's edges, whatever the stem's
  weight or the fitted ink factor. Black's bar also takes the mockup's thickness.
- The i and j dots are centred over the stem and take DOTS's size and height, through
  the dotaccentcomb component's transform (other letters keep theirs).

Every master gets the same point structure, and no open corners are left for ufo2ft's
eraseOpenCorners filter to erase differently, so the masters stay compatible. Running it
again changes nothing.

Usage: python tools/redraw.py source/PlaceholderSans-*.ufo   # rewrites the letters in GLYPHS
"""

import math
import os
import re
import sys

import ufoLib2
from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ufoLib.glifLib import GlyphSet
from ufoLib2.objects import Point

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402
from straighten import redraw  # noqa: E402

GLYPHS = ("N", "K", "k", "w", "t", "i", "j", "A", "V", "v", "W", "M", "Y", "E", "F", "Q")

# Edge lines were fitted to ink runs on scanlines (tools/strokes.py), exactly, on
# mockup.svg (Regular), mockup-black.svg (Black) and Thin's own outline. Each is (x at the
# baseline, x at the top), in font units from the letter's left edge; the top is the cap
# height for N and K and the x-height for k and w. Notches are the mockups' flat steps
# where one stroke meets another; Thin's are small so it keeps its own shapes.

# N: stem widths (left, right), top flat (left edge to the diagonal's top-right corner),
# foot (the diagonal's bottom-left corner to the right edge), the diagonal's horizontal
# width, notches (top-left, bottom-right), and the letter's width.
N_SHAPES = {
    "Thin": ((46, 46), 44, 44, 54.7, (5, 5), 1104),
    "Regular": ((194.5, 194.5), 283.5, 302.1, 210.9, (18, 18), 1245.8),
    "Black": ((355.9, 355.9), 596, 596, 387.9, (22.8, 28.9), 1411.4),
}

# K and k: stem width, the arm's upper (U) and lower (D) edges, the leg's left and right
# edges, notch where the arm leaves the stem, and the letter's width.
ARMS = {
    "K": {
        "Thin": dict(stem=46, U=(-623.1, 1022), D=(-546.5, 1083), legL=(1025, -234.1),
                     legR=(1080, -168.7), notch=3, width=1083),
        "Regular": dict(stem=202.8, U=(-428.1, 910.6), D=(-187.5, 1179.6), legL=(970.6, -89.4),
                        legR=(1229.3, 150.1), notch=12, width=1229.3),
        "Black": dict(stem=376.6, U=(-299.8, 846.4), D=(51.3, 1324.5), legL=(920.9, -0.6),
                      legR=(1374.1, 397.2), notch=14.5, width=1374.1),
    },
    "k": {
        "Thin": dict(stem=47, U=(-553.4, 721), D=(-471.5, 789), legL=(749, -252.5),
                     legR=(808, -188.3), notch=6, width=808),
        "Regular": dict(stem=194.5, U=(-249.5, 670.4), D=(-27.8, 916.7), legL=(701.5, -52.6),
                        legR=(947.8, 149.1), notch=12, width=947.8),
        "Black": dict(stem=351.8, U=(-108.7, 618.7), D=(196.7, 1063.6), legL=(662.2, 46.7),
                      legR=(1094.7, 400.6), notch=16.5, width=1094.7),
    },
}

# w: the left (L) and right (R) edges of its four strokes, from the left; notches at the
# bottom-left, middle and bottom-right counters; the letter's width.
W_SHAPES = {
    "Thin": dict(s1L=(324, 0), s1R=(372.2, 47), s2L=(338.5, 703), s2R=(387, 753.1),
                 s3L=(1079, 714.3), s3R=(1127.5, 763), s4L=(1093.8, 1419), s4R=(1143, 1466),
                 notches=(5, 5, 5), width=1466),
    "Regular": dict(s1L=(314.5, 0), s1R=(503.9, 204.9), s2L=(387.6, 697.4), s2R=(571.1, 884.5),
                    s3L=(1057.4, 741.3), s3R=(1241.9, 937.5), s4L=(1122.9, 1429.9),
                    s4R=(1314, 1630.6), notches=(20, 17, 19), width=1630.6),
    "Black": dict(s1L=(300.1, 0), s1R=(621.7, 378.7), s2L=(425.6, 697.3), s2R=(713.9, 992.1),
                  s3L=(1076.1, 801.2), s3R=(1375.3, 1107.2), s4L=(1178.1, 1432),
                  s4R=(1492, 1790), notches=(20.7, 20.7, 22.7), width=1790),
}

# t: how far the crossbar reaches past the stem's left and right edges, and its thickness
# (None keeps it). Thin's are its mockup's: thinning the strokes evenly moves the bar's
# ends and the stem's edges inward by the same amount.
T_BAR = {"Thin": (215.9, 271.7, None), "Regular": (200.7, 260.8, None), "Black": (171.8, 248.3, 269)}

# i and j: dot width, height and top. The mockups' dots (Thin's 94 units, centred on its
# screenshot's), lowered by 15% of the space between them and the x-height: the user found
# the mockups' sat too high. Regular's mockup dot is 240 x 236 with its top at 1515, Black's
# 409.8 x 389.1 at 1552, Thin's top at 1481.
DOTS = {"Thin": (94, 94, 1434), "Regular": (240, 236, 1485), "Black": (409.8, 389.1, 1539)}

# A, V, v, W, M and Y as the mockups' straight polygons, with the same small flat notch at
# each inner vertex as N and w; E and F with the mockups' bar heights and arm lengths; and
# Q's tail as the mockups' rotated rectangle. Each is (frame width, frame top, {contour
# index: points}), the points in our order and in font units from the frame's left edge,
# where the frame is the mockup letter (for Q, its bowl). They're placed in proportion on
# our frame, so outer edges, widths and spacing don't move (Q's tail keeps its right
# sidebearing). Measured on mockup.svg (Regular) and mockup-black.svg (Black): A's bar
# overlaps the legs as ours does, Regular's ends halfway across each leg; mockup.svg merges
# Q's tail into the bowl, so its corners are those of the tail's two ends.
POLYGONS = {
    "A": {
        "Regular": (1388.6, 1490.0, {0: [(0.0, 0.0), (219.4, 0.0), (676.7, 1245.8), (701.5, 1245.8), (1161.0, 0.0), (1388.6, 0.0), (815.3, 1490.0), (573.2, 1490.0)], 1: [(285.5, 372.5), (1098.6, 372.5), (1098.6, 562.9), (285.5, 562.9)]}),
        "Black": (1537.6, 1490.0, {0: [(0.0, 0.0), (395.3, 0.0), (749.1, 1053.3), (769.8, 1053.3), (1121.6, 0.0), (1537.6, 0.0), (983.0, 1490.0), (560.8, 1490.0)], 1: [(314.6, 264.9), (1192.0, 264.9), (1192.0, 591.9), (314.6, 591.9)]}),
    },
    "V": {
        "Regular": (1421.7, 1490.0, {0: [(589.8, 0.0), (831.9, 0.0), (1421.7, 1490.0), (1202.4, 1490.0), (728.4, 244.2), (703.6, 244.2), (227.6, 1490.0), (0.0, 1490.0)]}),
        "Black": (1500.4, 1490.0, {0: [(540.1, 0.0), (960.2, 0.0), (1500.4, 1490.0), (1109.2, 1490.0), (771.9, 453.2), (751.2, 453.2), (411.8, 1490.0), (0.0, 1490.0)]}),
    },
    "v": {
        "Regular": (1055.4, 1076.1, {0: [(409.8, 0.0), (645.7, 0.0), (1055.4, 1076.1), (846.4, 1076.1), (544.3, 235.9), (519.4, 235.9), (217.3, 1076.1), (0.0, 1076.1)]}),
        "Black": (1200.2, 1076.1, {0: [(403.5, 0.0), (796.7, 0.0), (1200.2, 1076.1), (813.3, 1076.1), (610.4, 432.5), (589.8, 432.5), (399.4, 1076.1), (0.0, 1076.1)]}),
    },
    "W": {
        "Regular": (2106.7, 1490.0, {0: [(399.4, 0.0), (676.7, 0.0), (1040.9, 1221.0), (1063.7, 1221.0), (1427.9, 0.0), (1707.3, 0.0), (2106.7, 1490.0), (1899.7, 1490.0), (1574.9, 244.2), (1554.2, 244.2), (1187.8, 1490.0), (927.1, 1490.0), (556.7, 244.2), (533.9, 244.2), (213.1, 1490.0), (0.0, 1490.0)]}),
        "Black": (2204.0, 1490.0, {0: [(364.2, 0.0), (867.1, 0.0), (1086.4, 956.1), (1111.3, 956.1), (1326.5, 0.0), (1841.8, 0.0), (2204.0, 1490.0), (1808.7, 1490.0), (1597.6, 525.6), (1576.9, 525.6), (1330.6, 1490.0), (879.5, 1490.0), (633.3, 525.6), (612.6, 525.6), (413.9, 1490.0), (0.0, 1490.0)]}),
    },
    "M": {
        "Regular": (1554.2, 1490.0, {0: [(0.0, 0.0), (194.5, 0.0), (194.5, 1256.2), (219.4, 1256.2), (645.7, 0.0), (902.3, 0.0), (1326.5, 1256.2), (1351.3, 1256.2), (1351.3, 0.0), (1554.2, 0.0), (1554.2, 1490.0), (1206.5, 1490.0), (790.5, 244.2), (767.8, 244.2), (349.7, 1490.0), (0.0, 1490.0)]}),
        "Black": (1734.2, 1490.0, {0: [(0.0, 0.0), (355.9, 0.0), (355.9, 1072.0), (378.7, 1072.0), (620.8, 0.0), (1105.1, 0.0), (1334.8, 1072.0), (1357.6, 1072.0), (1357.6, 0.0), (1734.2, 0.0), (1734.2, 1490.0), (1098.9, 1490.0), (871.2, 409.8), (846.4, 409.8), (612.6, 1490.0), (0.0, 1490.0)]}),
    },
    "Y": {
        "Regular": (1262.4, 1490.0, {0: [(529.8, 0.0), (732.6, 0.0), (732.6, 596.0), (1262.4, 1490.0), (1030.6, 1490.0), (643.6, 817.4), (622.9, 817.4), (240.1, 1490.0), (0.0, 1490.0), (529.8, 596.0)]}),
        "Black": (1465.1, 1490.0, {0: [(544.2, 0.0), (920.9, 0.0), (920.9, 571.2), (1465.1, 1490.0), (1051.3, 1490.0), (749.1, 935.4), (726.4, 935.4), (436.6, 1490.0), (0.0, 1490.0), (544.2, 571.2)]}),
    },
    "E": {
        "Regular": (1034.8, 1490.0, {0: [(0.0, 0.0), (1034.8, 0.0), (1034.8, 190.4), (202.8, 190.4), (202.8, 662.2), (958.2, 662.2), (958.2, 852.6), (202.8, 852.6), (202.8, 1299.6), (1009.9, 1299.6), (1009.9, 1490.0), (0.0, 1490.0)]}),
        "Black": (1090.6, 1490, {0: [(0, 0), (1090.6, 0), (1090.6, 327.0), (376.6, 327.0), (376.6, 593.9), (1011.9, 593.9), (1011.9, 920.9), (376.6, 920.9), (376.6, 1163.0), (1067.8, 1163.0), (1067.8, 1490), (0, 1490)]}),
    },
    "F": {
        "Regular": (1012.0, 1490.0, {0: [(0.0, 0.0), (202.8, 0.0), (202.8, 662.2), (931.3, 662.2), (931.3, 852.6), (202.8, 852.6), (202.8, 1299.6), (1012.0, 1299.6), (1012.0, 1490.0), (0.0, 1490.0)]}),
        "Black": (1059.6, 1490, {0: [(0, 0), (376.6, 0), (376.6, 593.9), (964.4, 593.9), (964.4, 920.9), (376.6, 920.9), (376.6, 1163.0), (1059.6, 1163.0), (1059.6, 1490), (0, 1490)]}),
    },
    "Q": {
        "Regular": (1465.2, 1514.9, {0: [(676.7, 627.1), (867.1, 389.8), (1057.5, 152.5), (1247.9, -84.8), (1392.7, 39.3), (1203.0, 274.5), (1013.3, 509.8), (823.6, 745.0)]}),
        "Black": (1556.2, 1514.9, {0: [(701.5, 536.0), (894.0, 328.4), (1086.5, 120.7), (1278.9, -86.9), (1519.0, 126.3), (1326.5, 333.9), (1134.1, 541.5), (941.6, 749.2)]}),
    },
}

# Q's tail starts nearer the bowl than the mockups' at the user's request: its inner
# (top-left) end is pulled out along the tail toward the outer end, which stays, to
# Q_TAIL_START of the way from the bowl's centre to the counter's edge, measured on the
# tail's centre line. The mockups' tails start at the centre (Regular's 58 units past it,
# Black's 106, about 10% and 25% of the way); Thin's (Inter's) 278 past it, 40%. None
# keeps the mockups' tail.
Q_TAIL_START = 0.5

# Q's tail also reaches further below the baseline than the mockups' (85 in Regular, 87 in
# Black), at the user's request: its outer end is moved along the tail, keeping its cut,
# until the lowest corner is Q_TAIL_DEPTH below the baseline. The user chose a quarter of
# the way to Inter's depths (140 / 140 / 110), with Regular's rounded to 100. Thin's
# (Inter's own tail) stays at 140. None keeps a master's depth as it is.
Q_TAIL_DEPTH = {"Thin": 140, "Regular": 100, "Black": 93}

# Masters without a POLYGONS entry (Thin) keep their own strokes: these contours' curved
# joints become flat notches THIN_NOTCH wide where their edges meet.
JOINTED = {"A": [0], "V": [0], "v": [0], "W": [0], "M": [0], "Y": [0]}
THIN_NOTCH = 5

STEM_Y = 600  # a height that cuts only the stem of t, i and j


# An edge is x = a + b * y, as (a, b).
def edge(spec, left, scale, top):
    x0, x1 = spec
    return (left + scale * x0, scale * (x1 - x0) / top)


def x_on(e, y):
    return e[0] + e[1] * y


def y_on(e, x):
    return (x - e[0]) / e[1]


def meet(e, f):
    y = (f[0] - e[0]) / (e[1] - f[1])
    return (x_on(e, y), y)


def through(p, q):
    b = (q.x - p.x) / (q.y - p.y)
    return (p.x - b * p.y, b)


def y_apart(e, f, gap):
    """Height where edge f is `gap` to the right of edge e."""
    return (gap - (f[0] - e[0])) / (f[1] - e[1])


def frame(font, glyph, width):
    b = glyph.getBounds(font)
    return b.xMin, b.xMax, b.yMax, (b.xMax - b.xMin) / width


def stem(font, glyph):
    """Left and right edges of a glyph's stem, components included."""
    rec = DecomposingRecordingPen(font)
    glyph.draw(rec)
    return strokes.cut(rec.replay, STEM_Y + strokes.EPS)[0]


def build_N(font, glyph, shape):
    (sl, sr), top, foot, diag, (nt, nb), width = shape
    L0, R1, H, scale = frame(font, glyph, width)
    L1, R0 = L0 + sl, R1 - sr
    Dt, Db = L0 + scale * top, R1 - scale * foot
    slope = (Dt - Db - diag) / H
    left, right = (Db, slope), (Dt - slope * H, slope)
    yt, yb = y_on(left, L1 + nt), y_on(right, R0 - nb)
    redraw(glyph, [
        (L0, 0), (L1, 0), (L1, yt), (L1 + nt, yt), (Db, 0),           # left stem, diagonal
        (R1, 0), (R1, H), (R0, H), (R0, yb), (R0 - nb, yb), (Dt, H),  # right stem, diagonal
        (L0, H),
    ])


def build_arm(font, glyph, shape, top):
    """K / k: stem, an arm up to `top`, and a leg that starts on the arm."""
    L0, _, H, scale = frame(font, glyph, shape["width"])
    U, D, legL, legR = (edge(shape[k], L0, scale, top) for k in ("U", "D", "legL", "legR"))
    L1, notch = L0 + shape["stem"], shape["notch"]
    yU = y_on(U, L1 + notch)
    redraw(glyph, [
        (L0, 0), (L1, 0), (L1, y_on(D, L1)),                     # stem up to the arm
        meet(legL, D), (x_on(legL, 0), 0), (x_on(legR, 0), 0),   # leg
        meet(legR, D), (x_on(D, top), top), (x_on(U, top), top),  # arm
        (L1 + notch, yU), (L1, yU), (L1, H), (L0, H),             # notch, stem
    ])


def build_w(font, glyph, shape, top):
    L0, _, _, scale = frame(font, glyph, shape["width"])
    s1L, s1R, s2L, s2R, s3L, s3R, s4L, s4R = (
        edge(shape[k], L0, scale, top) for k in ("s1L", "s1R", "s2L", "s2R", "s3L", "s3R", "s4L", "s4R"))
    nL, nM, nR = shape["notches"]
    yL, yM, yR = y_apart(s1R, s2L, nL), y_apart(s2R, s3L, nM), y_apart(s3R, s4L, nR)
    redraw(glyph, [
        (x_on(s1L, 0), 0), (x_on(s2R, 0), 0),                     # left foot
        (x_on(s2R, yM), yM), (x_on(s3L, yM), yM),                 # middle notch
        (x_on(s3L, 0), 0), (x_on(s4R, 0), 0),                     # right foot
        (x_on(s4R, top), top), (x_on(s4L, top), top),
        (x_on(s4L, yR), yR), (x_on(s3R, yR), yR),                 # right notch
        (x_on(s3R, top), top), (x_on(s2L, top), top),
        (x_on(s2L, yL), yL), (x_on(s1R, yL), yL),                 # left notch
        (x_on(s1R, top), top), (x_on(s1L, top), top),
    ])


def set_t_bar(font, glyph, bar):
    """Move the crossbar's four points; its top stays."""
    past_left, past_right, thickness = bar
    if len(glyph.contours) != 1 or len(glyph.contours[0]) != 4:
        raise ValueError("t: expected one four-point crossbar")
    s0, s1 = stem(font, glyph)
    points = glyph.contours[0].points
    x_mid = sum(p.x for p in points) / 4
    y0, y1 = min(p.y for p in points), max(p.y for p in points)
    bottom = y1 - thickness if thickness else y0
    for p in points:
        p.x = round(s0 - past_left) if p.x < x_mid else round(s1 + past_right)
        p.y = y1 if p.y == y1 else round(bottom)


def set_dot(font, glyph, size):
    base = next(c for c in glyph.components if c.baseGlyph != "dotaccentcomb")
    dot = next(c for c in glyph.components if c.baseGlyph == "dotaccentcomb")
    s0, s1 = stem(font, font[base.baseGlyph])
    centre = base.transformation.dx + (s0 + s1) / 2
    b = font[dot.baseGlyph].getBounds(font)
    xx, _, _, yy, _, dy = dot.transformation
    if size:
        w, h, top = size
        xx, yy = round(w / (b.xMax - b.xMin), 4), round(h / (b.yMax - b.yMin), 4)
        dy = round(top - yy * b.yMax)
    dx = round(centre - xx * (b.xMin + b.xMax) / 2)
    dot.transformation = Transform(xx, 0, 0, yy, dx, dy)


def collapse(contour, notch):
    """On-curve corners of a contour, with each curved joint (an edge's end, a curve, a short
    flat, a curve) replaced by a flat notch where the joint's two edges are `notch` apart."""
    pts = contour.points
    n = len(pts)
    joint = ["line", None, None, "curve", "line", None, None, "curve"]
    starts = {i for i in range(n) if all(pts[(i + k) % n].type == t for k, t in enumerate(joint))}
    inside = {(i + k) % n for i in starts for k in range(8)}
    first = next(i for i in range(n) if i not in inside)
    on = lambda i, step: next(pts[(i + step * k) % n] for k in range(1, n) if pts[(i + step * k) % n].type)
    out, k = [], 0
    while k < n:
        i = (first + k) % n
        if i in starts:
            a = through(on(i, -1), pts[i])                    # the edge ending at the joint
            b = through(pts[(i + 7) % n], on((i + 7) % n, 1))  # the edge leaving it
            _, y_cross = meet(a, b)
            side = 1 if x_on(a, pts[i].y) > x_on(b, pts[i].y) else -1   # at the open end
            y = y_cross + side * notch / (a[1] - b[1])
            out += [(x_on(a, y), y), (x_on(b, y), y)]
            k += 8
        else:
            if pts[i].type:
                out.append((pts[i].x, pts[i].y))
            k += 1
    return out


def set_contour(glyph, index, poly):
    contour = glyph.contours[index]
    contour.points[:] = [Point(round(x), round(y), "line") for x, y in poly]


def build_polygons(font, glyph, shapes):
    """Redraw contours from a mockup's polygons, mapped onto our frame: the bounds of the
    contours left alone (Q's bowl), or of the whole glyph."""
    width, top, polys = shapes
    rest = [c.getBounds(font) for i, c in enumerate(glyph.contours) if i not in polys]
    rest += [c.getBounds(font) for c in glyph.components]
    if rest:
        x0, x1, y1 = min(q.xMin for q in rest), max(q.xMax for q in rest), max(q.yMax for q in rest)
    else:
        b = glyph.getBounds(font)
        x0, x1, y1 = b.xMin, b.xMax, b.yMax
    sx, sy = (x1 - x0) / width, y1 / top
    right = glyph.getBounds(font).xMax
    for index, poly in polys.items():
        set_contour(glyph, index, [(x0 + sx * x, sy * y) for x, y in poly])
    glyph.width += round(glyph.getBounds(font).xMax - right)   # keep the right sidebearing


def tail_line(pts):
    """The middles of Q's tail's inner and outer ends, its length and its unit direction."""
    inner = ((pts[0].x + pts[7].x) / 2, (pts[0].y + pts[7].y) / 2)
    outer = ((pts[3].x + pts[4].x) / 2, (pts[3].y + pts[4].y) / 2)
    length = math.dist(inner, outer)
    return inner, length, ((outer[0] - inner[0]) / length, (outer[1] - inner[1]) / length)


def trim_tail(font, glyph, start):
    """Pull Q's tail's inner end out toward its outer end, to `start` of the way from the
    bowl's centre to the counter's edge along the tail's centre line. The tail is 8 points:
    0-3 one side from the inner end out, 4-7 the other side back in; every point slides
    toward its side's outer end by the same fraction, so the tail keeps its width, angle,
    end cuts and point spacing, and its outer end doesn't move."""
    pts = glyph.contours[0].points
    if len(pts) != 8:
        raise ValueError("Q: expected an eight-point tail as the first contour")
    if start is None:
        return
    inner, length, (ux, uy) = tail_line(pts)
    rec = DecomposingRecordingPen(font)
    for component in glyph.components:                       # the bowl (O)
        component.draw(rec)
    b = BoundsPen(font)
    rec.replay(b)
    centre = ((b.bounds[0] + b.bounds[2]) / 2, (b.bounds[1] + b.bounds[3]) / 2)
    along = lambda q: (q[0] - inner[0]) * ux + (q[1] - inner[1]) * uy
    t_centre = along(centre)
    line = [(inner[0] + ux * t_centre, inner[1] + uy * t_centre),
            (inner[0] + ux * length, inner[1] + uy * length)]
    hits = []
    for op, args in rec.value:
        if op == "moveTo":
            first = last = args[0]
            continue
        if op == "endPath":
            continue
        if op == "closePath":
            seg, last = [last, first], first
        else:
            seg, last = [last, *args], args[-1]
        if len(seg) == 2:
            found = lineLineIntersections(*seg, *line)
        else:
            found = curveLineIntersections(seg, line)
        hits += [along(i.pt) for i in found if 0 <= i.t1 <= 1 and 0 <= i.t2 <= 1]
    t_edge = min(t for t in hits if t > t_centre)            # the counter's edge
    target = t_centre + start * (t_edge - t_centre)
    if target <= 0.5:
        return                                               # already starts there
    s = (length - target) / length
    right = glyph.getBounds(font).xMax
    for i, p in enumerate(pts):
        o = pts[3] if i < 4 else pts[4]
        x0, y0 = o.x, o.y
        p.x, p.y = round(x0 + s * (p.x - x0)), round(y0 + s * (p.y - y0))
    glyph.width += round(glyph.getBounds(font).xMax - right)   # keep the right sidebearing


def set_tail_depth(font, glyph, depth):
    """Move Q's tail's outer end along the tail until its lowest corner is `depth` below the
    baseline. Every point slides along its side, away from or toward that side's inner end,
    by the same fraction, so the tail keeps its width, angle, end cuts, point spacing and
    inner end."""
    pts = glyph.contours[0].points
    if len(pts) != 8:
        raise ValueError("Q: expected an eight-point tail as the first contour")
    a, b = (pts[0].x, pts[0].y), (pts[7].x, pts[7].y)          # the inner end
    low, start = min((pts[3], a), (pts[4], b), key=lambda e: e[0].y)
    if depth is None or low.y == -depth:
        return
    s = (start[1] + depth) / (start[1] - low.y)
    right = glyph.getBounds(font).xMax
    for i, p in enumerate(pts):
        x0, y0 = a if i < 4 else b
        p.x, p.y = round(x0 + s * (p.x - x0)), round(y0 + s * (p.y - y0))
    glyph.width += round(glyph.getBounds(font).xMax - right)   # keep the right sidebearing


def apply(ufo, master):
    x_height = ufo.info.xHeight
    for name, shapes in POLYGONS.items():
        if master in shapes:
            build_polygons(ufo, ufo[name], shapes[master])
        elif name in JOINTED:
            for index in JOINTED[name]:
                set_contour(ufo[name], index, collapse(ufo[name].contours[index], THIN_NOTCH))
    trim_tail(ufo, ufo["Q"], Q_TAIL_START)
    set_tail_depth(ufo, ufo["Q"], Q_TAIL_DEPTH.get(master))
    build_N(ufo, ufo["N"], N_SHAPES[master])
    build_arm(ufo, ufo["K"], ARMS["K"][master], ufo["K"].getBounds(ufo).yMax)
    build_arm(ufo, ufo["k"], ARMS["k"][master], x_height)
    build_w(ufo, ufo["w"], W_SHAPES[master], x_height)
    set_t_bar(ufo, ufo["t"], T_BAR[master])
    for name in ("i", "j"):
        set_dot(ufo, ufo[name], DOTS.get(master))


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in GLYPHS:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {', '.join(GLYPHS)} redrawn ({master})")


if __name__ == "__main__":
    main(sys.argv[1:])
