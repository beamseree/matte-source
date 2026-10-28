"""Thicken the joints where arches and bowls leave their stems, to match the mockups.

In the mockups an arch or bowl gets heavier toward the stem it leaves: its inner curve
leaves the stem lower (higher, at the foot of u and a) and its outer curve meets the
stem higher, at a small flat notch. Inter's arches stay the same weight there or thin
out. At 15 units from the stem's edge, Regular's n, h, m and u were 80-85 units thinner
than mockup.svg's, a 100, r 70 and the bowls of b, d, p and q 25; Black's 30-45 thinner
than mockup-black.svg's, and Black r's whole arm 20-30. So in Regular and Black the
curves either side of each joint take the mockup's shape near the stem:

- "inner": the inner curve's end slides along the stem, with its handle; the far
  handle slides along its own direction, so the arch's top keeps its tangent.
- "counter": b's, p's and þ's counters leave the stem at their extremum, which stays;
  its handle slides along the stem.
- "notch": the outer curve ends where the mockup's does, at its notch, measured from the
  stem's edge, and the notch's line into the stem follows it in y. Inter's n, h, m and u
  ran the curve on into the stem and back out along that line instead; in Thin they
  still do. Neither shape is one ufo2ft's eraseOpenCorners filter changes, in any master.
- "valley": m's second arch keeps its end, where the first arch's outer curve also
  starts; only its handles move.
- "arm": Black r's lower edge from the stem to the terminal, both curves, moves to the
  mockup's; the terminal's foot slides along the cut.

Every curve keeps its far end (the top or bottom of the arch or bowl). POINTS holds the
moved points, as x from the stem's edge and y. `--fit` makes POINTS: each curve is fitted
by least squares to the mockup's ink edge up to NEAR units from the stem, aligned on the
stem's edge (STEMS), and to its own present outline from FAR units on, so it keeps its
shape further out. Black's counters reach 28 units less high than the mockup's (n's
arch is 339 units deep at the top, the mockup's 310), so its inner curves can only follow
the mockup's for about 60 units, and its outer curves come back to their own by 130.
d and q are b and p mirrored. The mockup has no þ, so þ takes the mockup's b. Thin keeps
Inter's joints: at its 46-unit strokes its screenshot can't show them.

No points are added or removed, so the masters stay compatible. Each changed glyph keeps
its right sidebearing. Running it again changes nothing.

Usage: python tools/joints.py source/PlaceholderSans-*.ufo   # move the points to POINTS
       python tools/joints.py --fit                           # print POINTS fitted to the mockups
       python tools/joints.py --check [source]                # joint widths, ours against the mockups
"""

import os
import re
import sys

import numpy as np
import ufoLib2
from fontTools.pens.pointInsidePen import PointInsidePen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import reshape  # noqa: E402
import strokes  # noqa: E402

N_LIKE = [("inner", 0, (0, 1, 2, 3)), ("notch", 0, (15, 14, 13, 12), 16)]
B_LIKE = [("counter", 1, (3, 4, 5, 6)), ("counter", 1, (3, 2, 1, 0)),
          ("notch", 0, (9, 8, 7, 6), 10), ("notch", 0, (16, 17, 18, 0), 15)]
P_LIKE = [("counter", 1, (3, 4, 5, 6)), ("counter", 1, (3, 2, 1, 0)),
          ("notch", 0, (15, 14, 13, 12), 16), ("notch", 0, (3, 4, 5, 6), 2)]

# Each glyph's mockup letter and its stems: the stem's edge on the joint's side, in our
# outline a point that nothing here moves (contour, point) and in the mockup's a scanline
# (y, run, edge: 0 left, 1 right); +1 if the joint is right of the stem (-1 left); and the
# joint's curves: (kind, contour, the curve's points from its stem end, and for notches the
# other end of the notch's line). Point numbers are the same in every master.
STEMS = {
    "n": ("n", [((0, 20), (300, 0, 1), +1, N_LIKE)]),
    "h": ("h", [((0, 20), (300, 0, 1), +1, N_LIKE)]),
    "m": ("m", [((0, 1), (300, 0, 1), +1, [("inner", 0, (2, 3, 4, 5)), ("notch", 0, (33, 32, 31, 30), 34)]),
                ((0, 10), (300, 1, 1), +1, [("inner", 0, (11, 12, 13, 14)), ("valley", 0, (26, 25, 24, 23))])]),
    "u": ("u", [((0, 8), (750, -1, 0), -1, [("inner", 0, (9, 10, 11, 12)), ("notch", 0, (3, 2, 1, 0), 4)])]),
    "a": ("a", [((1, 9), (680, -1, 0), -1, [("inner", 1, (10, 11, 12, 0)), ("notch", 0, (3, 2, 1, 0), 4)])]),
    "r": ("r", [((0, 1), (300, 0, 1), +1, [("inner", 0, (2, 3, 4, 5)), ("notch", 0, (15, 14, 13, 12), 16)])]),
    "b": ("b", [((1, 3), (538, 0, 1), +1, B_LIKE)]),
    "p": ("p", [((1, 3), (538, 0, 1), +1, P_LIKE)]),
    "thorn": ("b", [((1, 3), (538, 0, 1), +1, B_LIKE)]),
}
# Black r's arm: its lower edge, from the stem to the terminal's foot (points 2-8).
ARM = {"Black": ("r", 0, (2, 3, 4, 5, 6, 7, 8))}
MASTERS = ("Regular", "Black")
NEAR, FAR = {"Regular": 100, "Black": 60}, {"Regular": 180, "Black": 130}

# Fitted by `--fit`: {master: {glyph: [(stem, contour, point, x from that stem's edge, y)]}}
POINTS = {
    "Regular": {
        "n": [(0, 0, 0, 0, 526), (0, 0, 1, 0, 850), (0, 0, 2, 135.1, 903),
            (0, 0, 13, 259.2, 1101), (0, 0, 14, 112.5, 1083), (0, 0, 15, 12.4, 948),
            (0, 0, 16, -7, 948)],
        "h": [(0, 0, 0, 0, 526), (0, 0, 1, 0, 850), (0, 0, 2, 135.5, 903),
            (0, 0, 13, 256.3, 1101), (0, 0, 14, 112.1, 1082), (0, 0, 15, 12.4, 948),
            (0, 0, 16, 0, 948)],
        "m": [(0, 0, 2, 0, 560), (0, 0, 3, 0, 867), (0, 0, 4, 130.1, 907), (1, 0, 11, 0, 563),
            (1, 0, 12, 0, 894), (1, 0, 13, 159.8, 907), (1, 0, 24, 145.8, 1106),
            (1, 0, 25, -21.7, 1019), (0, 0, 31, 278, 1106), (0, 0, 32, 112.2, 1097),
            (0, 0, 33, 12.4, 954), (0, 0, 34, -5, 954)],
        "u": [(0, 0, 1, -271.6, -14), (0, 0, 2, -101.9, -2), (0, 0, 3, -12.4, 128),
            (0, 0, 4, 8, 128), (0, 0, 9, 0, 549), (0, 0, 10, 0, 222), (0, 0, 11, -140.6, 172)],
        "a": [(0, 0, 1, -271.8, -24), (0, 0, 2, -122.5, -23), (0, 0, 3, -4.1, 151),
            (0, 0, 4, 13, 151), (0, 1, 10, 0, 520), (0, 1, 11, 0, 483), (0, 1, 12, -27.6, 147)],
        "r": [(0, 0, 2, 0, 503), (0, 0, 3, 0, 625), (0, 0, 4, 31.5, 893),
            (0, 0, 13, 252.1, 1103), (0, 0, 14, 121.7, 1094), (0, 0, 15, 12.4, 902),
            (0, 0, 16, -7, 902)],
        "b": [(0, 0, 7, 244.8, 1101), (0, 0, 8, 127.9, 1073), (0, 0, 9, 18.6, 935),
            (0, 0, 10, 2, 935), (0, 0, 15, -4, 141), (0, 0, 16, 18.6, 141),
            (0, 0, 17, 121.8, 2), (0, 0, 18, 250.7, -22), (0, 1, 1, 97.7, 161),
            (0, 1, 2, 0, 319), (0, 1, 4, 0, 744), (0, 1, 5, 78.2, 908)],
        "p": [(0, 0, 2, 2, 141), (0, 0, 3, 18.6, 141), (0, 0, 4, 119, 14),
            (0, 0, 5, 228.2, -22), (0, 0, 13, 273.8, 1101), (0, 0, 14, 132.1, 1087),
            (0, 0, 15, 18.6, 935), (0, 0, 16, -4, 935), (0, 1, 1, 207.7, 161),
            (0, 1, 2, 0, 206), (0, 1, 4, 0, 716), (0, 1, 5, 61, 908)],
        "thorn": [(0, 0, 7, 237.6, 1101), (0, 0, 8, 130.3, 1074), (0, 0, 9, 18.6, 935),
            (0, 0, 10, 3, 935), (0, 0, 15, 3, 141), (0, 0, 16, 18.6, 141),
            (0, 0, 17, 126.1, -1), (0, 0, 18, 249.3, -22), (0, 1, 1, 99.3, 161),
            (0, 1, 2, 0, 321), (0, 1, 4, 0, 699), (0, 1, 5, 50.8, 908)],
    },
    "Black": {
        "n": [(0, 0, 0, 0, 561), (0, 0, 1, 0, 762), (0, 0, 2, 74.4, 762),
            (0, 0, 13, 195.3, 1101), (0, 0, 14, 61.4, 1049), (0, 0, 15, 2.1, 923),
            (0, 0, 16, -15, 923)],
        "h": [(0, 0, 0, 0, 561), (0, 0, 1, 0, 762), (0, 0, 2, 74.8, 762),
            (0, 0, 13, 185.3, 1101), (0, 0, 14, 61.6, 1041), (0, 0, 15, 14.5, 940),
            (0, 0, 16, -9, 940)],
        "m": [(0, 0, 2, 0, 568), (0, 0, 3, 0, 764), (0, 0, 4, 85.3, 764), (1, 0, 11, 0, 568),
            (1, 0, 12, 0, 764), (1, 0, 13, 85.6, 764), (1, 0, 24, 214.5, 1100),
            (1, 0, 25, -66.2, 1053), (0, 0, 31, 240.9, 1100), (0, 0, 32, 69.7, 1079),
            (0, 0, 33, 2.1, 921), (0, 0, 34, -8, 921)],
        "u": [(0, 0, 1, -212.5, -14), (0, 0, 2, -58.6, 25), (0, 0, 3, -2.1, 153),
            (0, 0, 4, 15, 153), (0, 0, 9, 0, 521), (0, 0, 10, 0, 314), (0, 0, 11, -67.7, 314)],
        "a": [(0, 0, 1, -146, -17), (0, 0, 2, -59, 19), (0, 0, 3, 8.3, 139),
            (0, 0, 4, 33, 139), (0, 1, 10, 0, 440), (0, 1, 11, 0, 258), (0, 1, 12, -92.3, 236)],
        "r": [(0, 0, 2, 0, 447), (0, 0, 3, 0, 688), (0, 0, 4, 170.9, 725), (0, 0, 5, 274, 725),
            (0, 0, 6, 324, 725), (0, 0, 7, 392, 729), (0, 0, 8, 423, 725),
            (0, 0, 13, 111.6, 1101), (0, 0, 14, 32.7, 949), (0, 0, 15, 2.1, 819),
            (0, 0, 16, -10, 819)],
        "b": [(0, 0, 7, 127.1, 1101), (0, 0, 8, 59.5, 978), (0, 0, 9, 22.8, 923),
            (0, 0, 10, 8, 923), (0, 0, 15, 4, 155), (0, 0, 16, 18.6, 155),
            (0, 0, 17, 60.2, 93), (0, 0, 18, 120.7, -13), (0, 1, 1, 66.9, 296),
            (0, 1, 2, 0, 378), (0, 1, 4, 0, 718), (0, 1, 5, 84.5, 781)],
        "p": [(0, 0, 2, 8, 153), (0, 0, 3, 22.8, 153), (0, 0, 4, 61.5, 96),
            (0, 0, 5, 116.8, -13), (0, 0, 13, 130.5, 1101), (0, 0, 14, 58.3, 981),
            (0, 0, 15, 18.6, 921), (0, 0, 16, 4, 921), (0, 1, 1, 71.2, 296), (0, 1, 2, 0, 373),
            (0, 1, 4, 0, 707), (0, 1, 5, 74.2, 781)],
        "thorn": [(0, 0, 7, 127.2, 1101), (0, 0, 8, 57.6, 975), (0, 0, 9, 22.8, 923),
            (0, 0, 10, 8, 923), (0, 0, 15, 8, 155), (0, 0, 16, 18.6, 155), (0, 0, 17, 58, 96),
            (0, 0, 18, 119.4, -13), (0, 1, 1, 53.9, 296), (0, 1, 2, 0, 391), (0, 1, 4, 0, 671),
            (0, 1, 5, 43.3, 781)],
    },
}


# --- outlines ---------------------------------------------------------------------------

def ours(font, name):
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    return rec.replay


def mockup(master, char):
    """The mockup's letter in font units, from its left edge, on our baseline."""
    rec, (x0, _, _, _), baseline, s = strokes.svg_letters(os.path.join(strokes.ROOT, strokes.MOCKUPS[master]))[char]
    return lambda pen: rec.replay(TransformPen(pen, (s, 0, 0, -s, -s * x0, s * baseline)))


def stem_edge(replay, scan):
    y, run, side = scan
    return strokes.cut(replay, y + strokes.EPS)[run][side]


def vertical_runs(replay, x):
    return strokes.cut(lambda pen: replay(TransformPen(pen, (0, 1, 1, 0, 0, 0))), x + strokes.EPS)


# --- applying POINTS --------------------------------------------------------------------

def apply(ufo, master):
    """Move the joints' points in `ufo` to POINTS; returns the names of the glyphs that changed."""
    table = POINTS.get(master, {})
    touched = reshape.users(ufo, table)
    before = {name: reshape.outline(ufo, name) for name in touched}
    right = {name: ufo[name].getBounds(ufo).xMax for name in touched if ufo[name].getBounds(ufo)}
    for name, rows in table.items():
        glyph = ufo[name]
        edges = [glyph.contours[ci].points[i].x for (ci, i), *_ in STEMS[name][1]]
        for group, ci, i, dx, y in rows:
            p = glyph.contours[ci].points[i]
            p.x, p.y = round(edges[group] + dx), y
    for name in right:
        ufo[name].width += round(ufo[name].getBounds(ufo).xMax - right[name])
    return sorted(name for name in touched if reshape.outline(ufo, name) != before[name])


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {', '.join(changed) or 'no'} joints moved ({master})")


# --- fitting POINTS to the mockups ------------------------------------------------------

def bezier(P, t):
    P, t = np.asarray(P, float), np.asarray(t, float)[:, None]
    return (1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]


def distances(pts, poly):
    """Distance from each of pts to the polyline poly."""
    a, ab = poly[:-1], np.diff(poly, axis=0)
    t = np.clip(((pts[:, None] - a) * ab).sum(2) / np.maximum((ab ** 2).sum(1), 1e-9), 0, 1)
    return np.hypot(*(pts[:, None] - a - t[..., None] * ab).transpose(2, 0, 1)).min(1)


def segments(rec):
    """Each segment of a recorded outline as a list of points."""
    out, cur, start = [], None, None
    for op, args in rec.value:
        if op == "moveTo":
            cur = start = args[0]
        elif op == "closePath":
            if cur != start:
                out.append([cur, start])
        else:
            out.append([cur, *args])
            cur = args[-1]
    return out


def ink_edge(replay, step=3.0):
    """Points along an outline's filled (nonzero) boundary, every `step` units or so."""
    rec = RecordingPen()
    replay(rec)
    pts = []
    for seg in segments(rec):
        dense = bezier(seg, np.linspace(0, 1, 200)) if len(seg) == 4 else np.linspace(seg[0], seg[1], 200)
        steps = np.hypot(*np.diff(dense, axis=0).T)
        keep = np.searchsorted(np.cumsum(steps), np.arange(0, steps.sum(), step))
        for k in keep:
            p, t = dense[k], dense[k + 1] - dense[k]
            nrm = np.array([-t[1], t[0]]) / max(np.hypot(*t), 1e-9)
            sides = []
            for q in (p + nrm, p - nrm):
                pen = PointInsidePen(None, tuple(q))
                replay(pen)
                sides.append(pen.getWinding() != 0)
            if sides[0] != sides[1]:
                pts.append(p)
    return np.array(pts)


def labelled(glyph):
    """Points along each segment of a glyph's own contours, with (contour, end point)."""
    out = []
    for ci, c in enumerate(glyph.contours):
        pts, n = c.points, len(c.points)
        on = [i for i, p in enumerate(pts) if p.type]
        for s, e in zip(on[-1:] + on[:-1], on):
            seg = [(pts[(s + j) % n].x, pts[(s + j) % n].y) for j in range((e - s) % n + 1)]
            dense = bezier(seg, np.linspace(0, 1, 120)) if len(seg) == 4 else np.linspace(seg[0], seg[1], 60)
            out += [(x, y, ci, e) for x, y in dense]
    return np.array(out)


def free(kind, P, stop):
    """The free parameters of a curve P (stem end first), as (start, bounds, build).

    Handles are fractions of the way to the far end, so a curve can't overshoot it. An
    inner curve's or arm's end slides along the stem between `stop`, the other end of the
    stem's line into it, and the far end."""
    if kind == "arm":                                   # P: stem end to the terminal's foot, 7 points
        S, H3, H4, F, H6, H7, E = (np.array(p, float) for p in P)
        lo, hi = stop[1] + 5, F[1] + 100                # the second curve's handles keep their x
        return ([S[1], H3[1], H4[0], F[1], H7[1], E[1]],
                ([lo, lo, S[0] + 1, lo, lo, lo], [F[1], hi, F[0] - 1, hi, hi, hi]),
                lambda x: [(S[0], x[0]), (S[0], x[1]), (x[2], x[3]), (F[0], x[3]), (H6[0], x[3]), (H7[0], x[4]), (E[0], x[5])])
    S, HS, HF, F = (np.array(p, float) for p in P)
    u = (HF - F) / np.hypot(*(HF - F))
    span, sv = abs(F[0] - S[0]), np.sign(F[1] - S[1])
    f_far = np.hypot(*(HF - F)) / span
    if kind == "inner":                                 # S slides between the line's end and F
        lo, hi = sorted((stop[1] + sv * 5, F[1] - sv * 20))
        return ([S[1], abs(HS[1] - S[1]) / abs(F[1] - S[1]), f_far], ([lo, 0.1, 0.1], [hi, 1, 1]),
                lambda x: [(S[0], x[0]), (S[0], x[0] + x[1] * (F[1] - x[0])), F + x[2] * span * u, F])
    if kind == "counter":
        return ([abs(HS[1] - S[1]) / abs(F[1] - S[1]), f_far], ([0.1, 0.1], [1, 1]),
                lambda x: [S, (S[0], S[1] + x[0] * (F[1] - S[1])), F + x[1] * span * u, F])
    xs, ys = sorted((S[0], F[0])), sorted((S[1] - sv * 150, F[1]))
    return ([HS[0], HS[1], f_far], ([xs[0], ys[0], 0.1], [xs[1], ys[1], 1]),   # notch, valley: the end stays
            lambda x: [S, (x[0], x[1]), F + x[2] * span * u, F])


def mockup_notch(rec, near, edge, side):
    """The mockup's flat notch nearest `near`: (its end away from the stem, its y)."""
    best = None
    for seg in segments(rec):
        if len(seg) != 2 or abs(seg[0][1] - seg[1][1]) > 0.5 or not 5 < abs(seg[0][0] - seg[1][0]) < 30:
            continue
        end = max(seg, key=lambda p: (p[0] - edge) * side)
        if abs(end[0] - edge) < 30 and (best is None or np.hypot(end[0] - near[0], end[1] - near[1]) <
                                         np.hypot(best[0] - near[0], best[1] - near[1])):
            best = end
    return best


def solve(x0, bounds, build, targets, extra=lambda Q: []):
    from scipy.optimize import least_squares

    def resid(x):
        Q = build(x)
        t = np.linspace(0, 1, 300)
        curves = [bezier(Q[k:k + 4], t) for k in range(0, len(Q) - 1, 3)]
        return distances(targets, np.vstack([*extra(Q), *curves]))

    x0 = np.clip(x0, np.array(bounds[0]) + 1e-6, np.array(bounds[1]) - 1e-6)
    res = least_squares(resid, x0, bounds=bounds)
    return build(res.x), res.fun


def fit_master(master, src):
    font = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
    table = {}
    for name, (char, groups) in STEMS.items():
        glyph, lab, rows = font[name], labelled(font[name]), []
        for group, ((ec, ei), scan, side, curves) in enumerate(groups):
            edge = glyph.contours[ec].points[ei].x
            mock = mockup(master, char)
            off = edge - stem_edge(mock, scan)
            aligned = lambda pen, mock=mock, off=off: mock(TransformPen(pen, (1, 0, 0, 1, off, 0)))
            ink = ink_edge(aligned)
            rec = RecordingPen()
            aligned(rec)
            for kind, ci, idx, *line in curves:
                if kind == "inner" and ARM.get(master, (None,))[0] == name:
                    kind, ci, idx = "arm", *ARM[master][1:]
                line_end = line[0] if line else None
                pts, n = glyph.contours[ci].points, len(glyph.contours[ci].points)
                P = [(pts[i].x, pts[i].y) for i in idx]
                if kind == "notch":                     # the mockup's notch, from our stem's edge
                    P[0] = mockup_notch(rec, P[0], edge, side)
                forward = (idx[1] - idx[0]) % n == 1
                labels = {(ci, idx[3] if forward else idx[0])}
                if kind == "arm":
                    labels |= {(ci, idx[6])}
                if kind in ("inner", "arm"):            # and the stem's line into it
                    labels.add((ci, idx[0] if forward else (idx[0] + 1) % n))
                # the mockup's edge where our nearest outline is this curve, near the stem
                dd = ((ink[:, None] - lab[None, :, :2]) ** 2).sum(2)
                near = lab[dd.argmin(1)]
                d = (ink[:, 0] - edge) * side
                reach = min(NEAR[master], 0.7 * abs(P[3][0] - edge))
                if kind == "arm":                       # all the way to the terminal
                    reach = abs(P[-1][0] - edge) - 5
                ok = np.array([(int(a), int(b)) in labels for a, b in near[:, 2:]]) & (np.sqrt(dd.min(1)) < 90)
                if kind in ("inner", "arm"):            # the stem's line only where it's straight
                    ok &= (np.abs(ink[:, 0] - P[0][0]) < 8) | (d > 4)
                ok &= d <= reach
                if kind == "notch":                     # past the mockup's notch
                    ok &= d >= (P[0][0] - edge) * side + 2
                if kind == "valley":
                    ok &= d >= 14
                mine = bezier(P[:4], np.linspace(0, 1, 400))
                far = mine[(mine[:, 0] - edge) * side >= max(FAR[master], reach + 50)][::4]
                targets = np.vstack([ink[ok], far])
                stop, extra = None, lambda Q: []
                if kind in ("inner", "arm"):            # the stem's line is part of the outline fitted
                    k = pts[(idx[0] - 1) % n if forward else (idx[0] + 1) % n]
                    stop = (k.x, k.y)
                    extra = lambda Q, stop=stop: [np.array([stop, Q[0]])]
                Q, err = solve(*free(kind, P, stop), targets, extra)
                print(f"  {master} {name} {kind} {idx}: {ok.sum()} + {len(far)} targets, "
                      f"rms {np.sqrt(np.mean(err ** 2)):.1f}", file=sys.stderr)
                moved = idx if kind == "arm" else idx[:3]
                for i, q in zip(idx, Q):
                    if i in moved and (round(float(q[0])), round(float(q[1]))) != (pts[i].x, pts[i].y):
                        rows.append((group, ci, i, round(float(q[0]) - edge, 1), round(float(q[1]))))
                if line_end is not None:
                    rows.append((group, ci, line_end, round(pts[line_end].x - edge, 1), round(float(Q[0][1]))))
        table[name] = sorted(rows, key=lambda r: (r[1], r[2]))
    return table


# How the joints are measured (tools/joints.py --check): the stem is found on a horizontal
# scanline at y (its run, and +1 if the joint is right of it), and the joint is the top (-1)
# or bottom (0) run on vertical scanlines DISTANCES from the stem's edge.
CHECK = {"n": (500, 0, +1, (-1,)), "h": (500, 0, +1, (-1,)), "r": (500, 0, +1, (-1,)),
         "m": (500, 0, +1, (-1,)), "m.2": (500, 1, +1, (-1,)), "u": (500, -1, -1, (0,)),
         "a": (380, -1, -1, (0,)), "b": (500, 0, +1, (-1, 0)), "d": (500, -1, -1, (-1, 0)),
         "p": (500, 0, +1, (-1, 0)), "q": (500, -1, -1, (-1, 0)), "thorn": (500, 0, +1, (-1, 0))}
DISTANCES = (15, 40, 80, 140)


def widths(replay, spec, distances=DISTANCES):
    y, run, side, which = spec
    edge = strokes.cut(replay, y + strokes.EPS)[run][1 if side > 0 else 0]
    out = []
    for w in which:
        runs = [vertical_runs(replay, edge + side * d) for d in distances]
        out.append([r[w][1] - r[w][0] if r else float("nan") for r in runs])
    return out


def check(src="source"):
    for master in MASTERS:
        font = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
        for key, spec in CHECK.items():
            name = key.split(".")[0]
            far = (220, 280, 350) if name == "r" and master in ARM else ()
            o = widths(ours(font, name), spec, DISTANCES + far)
            m = widths(mockup(master, "b" if name == "thorn" else name), spec, DISTANCES + far)
            for w, ow, mw in zip(spec[3], o, m):
                cells = "  ".join(f"{a:4.0f}/{b:<4.0f}" for a, b in zip(ow, mw))
                print(f"{master:7s} {key:5s} {'top' if w else 'bottom':6s}  ours/mockup at {DISTANCES + far}:  {cells}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fit"]:
        print({m: fit_master(m, os.path.join(strokes.ROOT, "source")) for m in MASTERS})
    elif sys.argv[1:2] == ["--check"]:
        check(*sys.argv[2:])
    else:
        main(sys.argv[1:])
