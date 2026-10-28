"""Thicken the joints where arches and bowls leave their stems, and set the depth of their
tops, to match the mockups.

In the mockups an arch or bowl gets heavier toward the stem it leaves: its inner curve
leaves the stem lower (higher, at the foot of u and a) and its outer curve meets the
stem higher, at a small flat notch. Inter's arches stay the same weight there or thin
out. At 15 units from the stem's edge, Regular's n, h, m and u were 80-85 units thinner
than mockup.svg's, a 100, r 70 and the bowls of b, d, p and q 25; Black's 30-45 thinner
than mockup-black.svg's, and Black r's whole arm 20-30. Further out the arches and bowls
were too heavy: the counters didn't reach as high (as low, in u and at the foot of the
bowls) as the mockups'. Regular n's arch was 198 units deep at the top, the mockup's
178; Black's 339, the mockup's 310. So in Regular and Black the curves either side of
each joint take the mockup's shape near the stem, and the inner curves its shape all
the way across:

- "inner": the inner curve's end slides along the stem, with its handle. It is fitted
  with the curve beyond the counter's top (bottom, in u): the top moves, its handles
  staying level, and the curve goes on to the far stem, sliding along it to where the
  mockup's leaves it, or in r to the terminal's foot, which stays.
- "counter": b's, p's and þ's counters leave the stem at their extremum, which stays;
  its handle slides along the stem. Each is fitted with the curve beyond the counter's
  top or bottom, on to the counter's far extremum, which moves across to the mockup's
  (so the far side's stroke is the mockup's weight, from our outer edge; þ's stays).
  Each of these curves keeps its two handles about the same fraction of its box
  (BALANCE), as the mockups' and Inter's counters do.
- "notch": the outer curve ends where the mockup's does, at its notch, measured from the
  stem's edge, and the notch's line into the stem follows it in y. Inter's n, h, m and u
  ran the curve on into the stem and back out along that line instead; in Thin they
  still do. Neither shape is one ufo2ft's eraseOpenCorners filter changes, in any master.
- "valley": m's second arch keeps its end, where the first arch's outer curve also
  starts; only its handles move.
- "arm": r's lower edge, from the stem to the terminal, is the mockups': a curve out of the
  stem and a flat run to the terminal's foot, which slides along the cut. Its end was
  drooping (Regular's underside fell from 906 to 882, Black's top from 1101 to 1073).
- "level": r's top is flat from the arch to the terminal, at the mockup's top (1101), so
  the terminal is cut square, as in the mockups.

The outer curves keep their far ends (the top or bottom of the arch or bowl), so the
x-height and overshoot stay. POINTS holds the moved points, as x from the stem's edge and
y. `--fit` makes POINTS by least squares against the mockup's ink edge, aligned on the
stem's edge (STEMS). The inner curves and counters, with the curves beyond them, are
fitted to it all the way across, each point moved up or down by how far our outer edge
is from the mockup's at that x, so they keep the mockup's depth under our outer edge (our
u and bowls overshoot 13-22 units at the baseline, the mockups' 25; at the x-height both
overshoot 25). The other curves are fitted to it up to NEAR units from the stem and to
their own present outline from FAR units on, so they keep their shape further out.
Black's NEAR is shorter: it was set when Black's counters reached 28 units less high
than the mockup's. Now only the outer curves use it, and at 100 they'd come only 1-2
units closer to the mockup's (in n and m they're 4-8 lower at 100-180). d and q are b and p
mirrored. The mockup has no þ, so þ takes the mockup's b, its counter scaled across to
ours. Thin keeps Inter's joints and tops: at its 46-unit strokes its screenshot can't show
the joints, and its arches are no heavier at the top than its o.

5 has no mockup letter. Its bowl leaves its stem the way n's arch does, but it kept Inter's
joint, which thinned toward the stem (Regular's top stroke was 152 units thick 15 units from
the notch, 172 at 140). So its notch slides up the stem's edge and the foot's corner, where
the counter's top curve starts, slides down a parallel line, so the foot's line steepens;
each curve keeps its far end (the bowl's top, the counter's top) and its shape, scaled to its
new ends. `fit_five` sets how far: 5 gets n's weight FIVE_AT units from the stem, as a
fraction of each glyph's depth, and the notch and the foot add the same weight 15 units out.
Nearer the stem n is heavier still (Regular 262, 1.46 times its depth, at 15), because its
inner curve runs down a vertical stem, which 5 doesn't have. Black's 5 already has n's
weight against its depth, so the fit leaves it alone.

No points are added or removed, so the masters stay compatible. Each changed glyph keeps
its right sidebearing. Running it again changes nothing.

Usage: python tools/joints.py source/PlaceholderSans-*.ufo   # move the points to POINTS
       python tools/joints.py --fit [kind ...]                # print POINTS with these curves refitted
                                                              # (all; "top": the inner curves and counters;
                                                              # "five": 5's joint)
       python tools/joints.py --check [source]                # joint widths, ours against the mockups
                                                              # (5 against n, scaled to 5's depth)
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

N_LIKE = [("inner", 0, (0, 1, 2, 3), (3, 4, 5, 6), "stem"), ("notch", 0, (15, 14, 13, 12), 16)]
B_LIKE = [("counter", 1, (3, 4, 5, 6), (6, 7, 8, 9), "side"), ("counter", 1, (3, 2, 1, 0), (0, 11, 10, 9), "side"),
          ("notch", 0, (9, 8, 7, 6), 10), ("notch", 0, (16, 17, 18, 0), 15)]
P_LIKE = [("counter", 1, (3, 4, 5, 6), (6, 7, 8, 9), "side"), ("counter", 1, (3, 2, 1, 0), (0, 11, 10, 9), "side"),
          ("notch", 0, (15, 14, 13, 12), 16), ("notch", 0, (3, 4, 5, 6), 2)]

# Each glyph's mockup letter and its stems: the stem's edge on the joint's side, in our
# outline a point that nothing here moves (contour, point) and in the mockup's a scanline
# (y, run, edge: 0 left, 1 right); +1 if the joint is right of the stem (-1 left); and the
# joint's curves: (kind, contour, the curve's points from its stem end, and for notches the
# other end of the notch's line; for inner curves and counters the curve that goes on from
# the counter's top or bottom to the far side, fitted with it, and how that curve's far end
# moves: "stem" along the far stem's edge, "side" across to the mockup's counter, or not at
# all). Point numbers are the same in every master.
STEMS = {
    "n": ("n", [((0, 20), (300, 0, 1), +1, N_LIKE)]),
    "h": ("h", [((0, 20), (300, 0, 1), +1, N_LIKE)]),
    "m": ("m", [((0, 1), (300, 0, 1), +1, [("inner", 0, (2, 3, 4, 5), (5, 6, 7, 8), "stem"),
                                           ("notch", 0, (33, 32, 31, 30), 34)]),
                ((0, 10), (300, 1, 1), +1, [("inner", 0, (11, 12, 13, 14), (14, 15, 16, 17), "stem"),
                                            ("valley", 0, (26, 25, 24, 23))])]),
    "u": ("u", [((0, 8), (750, -1, 0), -1, [("inner", 0, (9, 10, 11, 12), (12, 13, 14, 15), "stem"),
                                            ("notch", 0, (3, 2, 1, 0), 4)])]),
    "a": ("a", [((1, 9), (680, -1, 0), -1, [("inner", 1, (10, 11, 12, 0)), ("notch", 0, (3, 2, 1, 0), 4)])]),
    "r": ("r", [((0, 1), (300, 0, 1), +1, [("arm", 0, (2, 3, 4, 5, 6, 7, 8)), ("notch", 0, (15, 14, 13, 12), 16),
                                           ("level", 0, (9, 10, 11, 12, 13))])]),
    "b": ("b", [((1, 3), (538, 0, 1), +1, B_LIKE)]),
    "p": ("p", [((1, 3), (538, 0, 1), +1, P_LIKE)]),
    "thorn": ("b", [((1, 3), (538, 0, 1), +1, B_LIKE)]),
    # 5 has no mockup letter (fit_five): its stem's edge is the line from the bar down to the
    # notch, and the counter's top curve leaves the stem's foot, which ends at point 16.
    "five": (None, [((0, 11), None, +1, [("inner", 0, (16, 17, 18, 19)), ("notch", 0, (9, 8, 7, 6), 10)])]),
}
MASTERS = ("Regular", "Black")
NEAR, FAR = {"Regular": 100, "Black": 60}, {"Regular": 180, "Black": 130}

# Fitted by `--fit`: {master: {glyph: [(stem, contour, point, x from that stem's edge, y)]}}
POINTS = {
    "Regular": {
        "n": [(0, 0, 0, 0, 538), (0, 0, 1, 0, 794), (0, 0, 2, 100.6, 922),
            (0, 0, 3, 300, 922), (0, 0, 4, 434.6, 922), (0, 0, 5, 513, 826),
            (0, 0, 6, 513, 661), (0, 0, 13, 259.2, 1101), (0, 0, 14, 112.5, 1083),
            (0, 0, 15, 12.4, 948), (0, 0, 16, -7, 948)],
        "h": [(0, 0, 0, 0, 538), (0, 0, 1, 0, 794), (0, 0, 2, 100.3, 922),
            (0, 0, 3, 300.4, 922), (0, 0, 4, 432.3, 922), (0, 0, 5, 512, 827),
            (0, 0, 6, 512, 668), (0, 0, 13, 256.3, 1101), (0, 0, 14, 112.1, 1082),
            (0, 0, 15, 12.4, 948), (0, 0, 16, 0, 948)],
        "m": [(0, 0, 2, 0, 573), (0, 0, 3, 0, 810), (0, 0, 4, 93.8, 926),
            (0, 0, 5, 286.7, 926), (0, 0, 6, 402.6, 926), (0, 0, 7, 475, 824),
            (0, 0, 8, 475, 659), (1, 0, 11, 0, 576), (1, 0, 12, 0, 805),
            (1, 0, 13, 95.5, 927), (1, 0, 14, 275.3, 927), (1, 0, 15, 402.9, 927),
            (1, 0, 16, 475, 834), (1, 0, 17, 475, 668), (1, 0, 24, 145.8, 1106),
            (1, 0, 25, -21.7, 1019), (0, 0, 31, 278, 1106), (0, 0, 32, 112.2, 1097),
            (0, 0, 33, 12.4, 954), (0, 0, 34, -5, 954)],
        "u": [(0, 0, 1, -271.6, -14), (0, 0, 2, -101.9, -2), (0, 0, 3, -12.4, 128),
            (0, 0, 4, 8, 128), (0, 0, 9, 0, 547), (0, 0, 10, 0, 281),
            (0, 0, 11, -90.4, 164), (0, 0, 12, -298, 164), (0, 0, 13, -432.3, 164),
            (0, 0, 14, -512, 258), (0, 0, 15, -512, 415)],
        "a": [(0, 0, 1, -271.8, -24), (0, 0, 2, -122.5, -23), (0, 0, 3, -4.1, 151),
            (0, 0, 4, 13, 151), (0, 1, 10, 0, 520), (0, 1, 11, 0, 483),
            (0, 1, 12, -27.6, 147)],
        "r": [(0, 0, 2, 0, 510), (0, 0, 3, 0, 739), (0, 0, 4, 118, 903),
            (0, 0, 5, 281.6, 903), (0, 0, 6, 325.7, 903), (0, 0, 7, 369.9, 903),
            (0, 0, 8, 414, 903), (0, 0, 9, 414, 1101), (0, 0, 10, 392, 1101),
            (0, 0, 11, 345, 1101), (0, 0, 12, 317, 1101), (0, 0, 13, 252, 1101),
            (0, 0, 14, 121.7, 1094), (0, 0, 15, 12.4, 902), (0, 0, 16, -7, 902)],
        "b": [(0, 0, 7, 244.8, 1101), (0, 0, 8, 127.9, 1073), (0, 0, 9, 18.6, 935),
            (0, 0, 10, 2, 935), (0, 0, 15, -4, 141), (0, 0, 16, 18.6, 141),
            (0, 0, 17, 121.8, 2), (0, 0, 18, 250.7, -22), (0, 1, 0, 308.1, 156),
            (0, 1, 1, 119.2, 156), (0, 1, 2, 0, 303), (0, 1, 4, 0, 775),
            (0, 1, 5, 119.5, 924), (0, 1, 6, 307.5, 924), (0, 1, 7, 519.6, 924),
            (0, 1, 8, 640.2, 785), (0, 1, 9, 640.2, 537), (0, 1, 10, 640.2, 291),
            (0, 1, 11, 521.7, 156)],
        "p": [(0, 0, 2, 2, 141), (0, 0, 3, 18.6, 141), (0, 0, 4, 119, 14),
            (0, 0, 5, 228.2, -22), (0, 0, 13, 273.8, 1101), (0, 0, 14, 132.1, 1087),
            (0, 0, 15, 18.6, 935), (0, 0, 16, -4, 935), (0, 1, 0, 304.6, 155),
            (0, 1, 1, 117.7, 155), (0, 1, 2, 0, 302), (0, 1, 4, 0, 774),
            (0, 1, 5, 120.9, 923), (0, 1, 6, 311, 923), (0, 1, 7, 521.5, 923),
            (0, 1, 8, 640.2, 786), (0, 1, 9, 640.2, 537), (0, 1, 10, 640.2, 291),
            (0, 1, 11, 519.8, 155)],
        "thorn": [(0, 0, 7, 237.6, 1101), (0, 0, 8, 130.3, 1074), (0, 0, 9, 18.6, 935),
            (0, 0, 10, 3, 935), (0, 0, 15, 3, 141), (0, 0, 16, 18.6, 141),
            (0, 0, 17, 126.1, -1), (0, 0, 18, 249.3, -22), (0, 1, 0, 304.5, 155),
            (0, 1, 1, 117.6, 155), (0, 1, 2, 0, 303), (0, 1, 4, 0, 775),
            (0, 1, 5, 117.6, 924), (0, 1, 6, 302.7, 924), (0, 1, 7, 501.9, 924),
            (0, 1, 8, 622, 779), (0, 1, 10, 622, 297), (0, 1, 11, 504, 155)],
        "five": [(0, 0, 7, 123.3, 978), (0, 0, 8, 21.6, 948), (0, 0, 9, -39.7, 908),
            (0, 0, 10, -48.7, 908), (0, 0, 16, -76.6, 666), (0, 0, 17, -15.3, 741),
            (0, 0, 18, 93.0, 795)],
    },
    "Black": {
        "n": [(0, 0, 0, 0, 581), (0, 0, 1, 0, 718), (0, 0, 2, 56.8, 785),
            (0, 0, 3, 172.8, 785), (0, 0, 4, 235.1, 785), (0, 0, 5, 284, 736),
            (0, 0, 6, 284, 675), (0, 0, 13, 195.3, 1101), (0, 0, 14, 61.4, 1049),
            (0, 0, 15, 2.1, 923), (0, 0, 16, -15, 923)],
        "h": [(0, 0, 0, 0, 578), (0, 0, 1, 0, 719), (0, 0, 2, 55.3, 785),
            (0, 0, 3, 174, 785), (0, 0, 4, 232.6, 785), (0, 0, 5, 283, 738),
            (0, 0, 6, 283, 683), (0, 0, 13, 185.3, 1101), (0, 0, 14, 61.6, 1041),
            (0, 0, 15, 14.5, 940), (0, 0, 16, -9, 940)],
        "m": [(0, 0, 2, 0, 585), (0, 0, 3, 0, 714), (0, 0, 4, 57.9, 781),
            (0, 0, 5, 167.6, 781), (0, 0, 6, 250.3, 781), (0, 0, 7, 293, 724),
            (0, 0, 8, 293, 611), (1, 0, 11, 0, 598), (1, 0, 12, 0, 714),
            (1, 0, 13, 60.8, 779), (1, 0, 14, 168, 779), (1, 0, 15, 251.4, 779),
            (1, 0, 16, 293, 723), (1, 0, 17, 293, 611), (1, 0, 24, 214.5, 1100),
            (1, 0, 25, -66.2, 1053), (0, 0, 31, 240.9, 1100), (0, 0, 32, 69.7, 1079),
            (0, 0, 33, 2.1, 921), (0, 0, 34, -8, 921)],
        "u": [(0, 0, 1, -212.5, -14), (0, 0, 2, -58.6, 25), (0, 0, 3, -2.1, 153),
            (0, 0, 4, 15, 153), (0, 0, 9, 0, 502), (0, 0, 10, 0, 360), (0, 0, 11, -47, 299),
            (0, 0, 12, -158.5, 299), (0, 0, 13, -231.6, 299), (0, 0, 14, -284, 344),
            (0, 0, 15, -284, 407)],
        "a": [(0, 0, 1, -146, -17), (0, 0, 2, -59, 19), (0, 0, 3, 8.3, 139),
            (0, 0, 4, 33, 139), (0, 1, 10, 0, 440), (0, 1, 11, 0, 258),
            (0, 1, 12, -92.3, 236)],
        "r": [(0, 0, 2, 0, 443), (0, 0, 3, 0, 622), (0, 0, 4, 95.8, 728),
            (0, 0, 5, 258.4, 728), (0, 0, 6, 313.2, 728), (0, 0, 7, 368.1, 728),
            (0, 0, 8, 423, 728), (0, 0, 9, 423, 1101), (0, 0, 10, 392, 1101),
            (0, 0, 11, 348, 1101), (0, 0, 12, 312, 1101), (0, 0, 13, 112, 1101),
            (0, 0, 14, 32.7, 949), (0, 0, 15, 2.1, 819), (0, 0, 16, -10, 819)],
        "b": [(0, 0, 7, 127.1, 1101), (0, 0, 8, 59.5, 978), (0, 0, 9, 22.8, 923),
            (0, 0, 10, 8, 923), (0, 0, 15, 4, 155), (0, 0, 16, 18.6, 155),
            (0, 0, 17, 60.2, 93), (0, 0, 18, 120.7, -13), (0, 1, 0, 179.6, 295),
            (0, 1, 1, 66.7, 295), (0, 1, 2, 0, 385), (0, 1, 4, 0, 693),
            (0, 1, 5, 72.8, 790), (0, 1, 6, 188.3, 790), (0, 1, 7, 314.7, 790),
            (0, 1, 8, 393.6, 694), (0, 1, 9, 393.6, 537), (0, 1, 10, 393.6, 391),
            (0, 1, 11, 308, 295)],
        "p": [(0, 0, 2, 8, 153), (0, 0, 3, 22.8, 153), (0, 0, 4, 61.5, 96),
            (0, 0, 5, 116.8, -13), (0, 0, 13, 130.5, 1101), (0, 0, 14, 58.3, 981),
            (0, 0, 15, 18.6, 921), (0, 0, 16, 4, 921), (0, 1, 0, 177.4, 294),
            (0, 1, 1, 67.4, 294), (0, 1, 2, 0, 386), (0, 1, 4, 0, 694),
            (0, 1, 5, 72.4, 790), (0, 1, 6, 190.2, 790), (0, 1, 7, 315.4, 790),
            (0, 1, 8, 393.6, 694), (0, 1, 9, 393.6, 537), (0, 1, 10, 393.6, 390),
            (0, 1, 11, 307.1, 294)],
        "thorn": [(0, 0, 7, 127.2, 1101), (0, 0, 8, 57.6, 975), (0, 0, 9, 22.8, 923),
            (0, 0, 10, 8, 923), (0, 0, 15, 8, 155), (0, 0, 16, 18.6, 155),
            (0, 0, 17, 58, 96), (0, 0, 18, 119.4, -13), (0, 1, 0, 187.1, 292),
            (0, 1, 1, 69.4, 292), (0, 1, 2, 0, 383), (0, 1, 4, 0, 695),
            (0, 1, 5, 76.3, 794), (0, 1, 6, 198, 794), (0, 1, 7, 331.2, 794),
            (0, 1, 8, 422, 690), (0, 1, 10, 422, 394), (0, 1, 11, 324.2, 292)],
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
        lo, hi = stop[1] + 5, F[1] + 100                # F, the flat's start, and the flat's height
        return ([S[1], abs(H3[1] - S[1]) / abs(F[1] - S[1]), abs(F[0] - H4[0]) / abs(F[0] - S[0]), F[1], F[0]],
                ([lo, 0.1, 0.1, lo, S[0] + 60], [F[1] - 20, 1, 1, hi, E[0] - 20]),
                lambda x: [(S[0], x[0]), (S[0], x[0] + x[1] * (x[3] - x[0])), (x[4] - x[2] * (x[4] - S[0]), x[3]),
                           (x[4], x[3]), (x[4] + (E[0] - x[4]) / 3, x[3]), (x[4] + 2 * (E[0] - x[4]) / 3, x[3]),
                           (E[0], x[3])])
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


def free_top(kind, P, R, stop, far_stop=None):
    """Like `free`, for an inner curve or counter P and the curve R that goes on from P's far
    end, the counter's top (or bottom), to the far side: 7 points, fitted together.

    The top moves, its handles staying level. R's handle at its far end slides along its own
    direction, and with `far_stop`, the other end of the far stem's line into it, the far end
    slides along that line too. Each handle stays inside its curve's box, so the top stays
    the top."""
    S, HS, HT, T = (np.array(p, float) for p in P)
    _, HR, HE, E = (np.array(p, float) for p in R)
    v = (HE - E) / np.hypot(*(HE - E))
    sv = np.sign(T[1] - S[1])

    def room(t, e):                                     # the longest handle at E inside the box
        return min(abs(t[k] - e[k]) / abs(v[k]) for k in (0, 1) if abs(v[k]) > 1e-6)

    x0 = [T[0], T[1], abs(HS[1] - S[1]) / abs(T[1] - S[1]), abs(T[0] - HT[0]) / abs(T[0] - S[0]),
          abs(HR[0] - T[0]) / abs(E[0] - T[0]), np.hypot(*(HE - E)) / room(T, E)]
    lo = [min(S[0], E[0]) + 20, T[1] - 80, 0.1, 0.1, 0.1, 0.1]
    hi = [max(S[0], E[0]) - 20, T[1] + 80, 1, 1, 1, 1]
    if kind == "inner":                                 # S slides between the line's end and the top
        a, b = sorted((stop[1] + sv * 5, T[1] - sv * 20))
        x0, lo, hi = x0 + [S[1]], lo + [a], hi + [b]
    if far_stop is not None:                            # and E between its line's end and the top
        se = np.sign(T[1] - far_stop[1])
        a, b = sorted((far_stop[1] + se * 5, T[1] - se * 20))
        x0, lo, hi = x0 + [E[1]], lo + [a], hi + [b]

    def build(x):
        s = (S[0], x[6]) if kind == "inner" else S
        e = np.array((E[0], x[-1])) if far_stop is not None else E
        t = np.array(x[:2])
        return [s, (s[0], s[1] + x[2] * (t[1] - s[1])), (t[0] - x[3] * (t[0] - s[0]), t[1]), t,
                (t[0] + x[4] * (e[0] - t[0]), t[1]), e + x[5] * room(t, e) * v, e]
    return x0, (lo, hi), build


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


# How strongly each curve's two handles are kept to the same fraction of their box, in units
# of distance per unit of difference. Many pairs of handles fit a mockup's edge within a unit
# or two, and the closest is often one long and one short, which turns too sharply at the
# short one (the mockups' and Inter's counters have about the same fraction at both ends).
BALANCE = 8


def solve(x0, bounds, build, targets, extra=lambda Q: [], balance=()):
    """Least squares; `balance`, pairs of indices into x of handle fractions kept alike."""
    from scipy.optimize import least_squares

    def resid(x):
        Q = build(x)
        t = np.linspace(0, 1, 300)
        curves = [bezier(Q[k:k + 4], t) for k in range(0, len(Q) - 1, 3)]
        fit = distances(targets, np.vstack([*extra(Q), *curves]))
        return np.concatenate([fit, [BALANCE * np.sqrt(len(fit)) * (x[a] - x[b]) for a, b in balance]])

    x0 = np.clip(x0, np.array(bounds[0]) + 1e-6, np.array(bounds[1]) - 1e-6)
    res = least_squares(resid, x0, bounds=bounds)
    return build(res.x), res.fun[:len(res.fun) - len(balance)]


def depth_kept(replay, aligned, ink, top):
    """`ink`, points on the mockup's edge, moved up or down by how far our outer edge is from
    the mockup's at the same x, on the top (or bottom) stroke: so the counter's edge keeps the
    mockup's depth under our outer edge (our u and bowls overshoot less than the mockups' at
    the baseline). Where a vertical cut runs into a stem, the points stay."""
    def outer(rep, x):
        runs = [r for r in vertical_runs(rep, x) if r[1] - r[0] < 450]
        return (max(r[1] for r in runs) if top else min(r[0] for r in runs)) if runs else None
    xs = np.arange(ink[:, 0].min(), ink[:, 0].max() + 4, 4)
    shift = np.zeros(len(xs))
    for j, x in enumerate(xs):
        o, m = outer(replay, x), outer(aligned, x)
        if o is not None and m is not None and abs(o - m) < 40:
            shift[j] = o - m
    return ink + np.c_[np.zeros(len(ink)), np.interp(ink[:, 0], xs, shift)]


def fit_master(master, src, kinds=None):
    """POINTS[master] with the curves of `kinds` (all if None; "top": the curves fitted with
    the one beyond them) refitted from `src`."""
    font = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
    table = {}
    for name, (char, groups) in STEMS.items():
        if char is None:                                # 5: n's weight, not a mockup's
            kept = {r[:3]: r for r in POINTS.get(master, {}).get(name, [])}
            kept.update({r[:3]: r for r in (fit_five(font) if not kinds or name in kinds else [])})
            if kept:
                table[name] = sorted(kept.values(), key=lambda r: (r[1], r[2]))
            continue
        glyph, rows = font[name], []
        for group, ((ec, ei), scan, side, curves) in enumerate(groups):
            edge = glyph.contours[ec].points[ei].x
            for kind, ci, idx, *more in curves:         # first, so the fits see the flat top
                if kind == "level" and (not kinds or kind in kinds):
                    top = max(y for _, y in ink_edge(mockup(master, char), step=10))
                    for i in idx:
                        p = glyph.contours[ci].points[i]
                        p.y = round(top)
                        rows.append((group, ci, i, round(p.x - edge, 1), p.y))
        lab, replay = labelled(glyph), ours(font, name)
        for group, ((ec, ei), scan, side, curves) in enumerate(groups):
            edge = glyph.contours[ec].points[ei].x
            mock = mockup(master, char)
            off = edge - stem_edge(mock, scan)
            aligned = lambda pen, mock=mock, off=off: mock(TransformPen(pen, (1, 0, 0, 1, off, 0)))
            ink = ink_edge(aligned)
            rec = RecordingPen()
            aligned(rec)
            for kind, ci, idx, *more in curves:
                if kind == "level":
                    continue
                line_end = more[0] if kind == "notch" else None
                beyond = more[0] if more and kind in ("inner", "counter") else None
                slide = more[1] if beyond and len(more) > 1 else None
                if kinds and kind not in kinds and not (beyond and "top" in kinds):
                    continue
                pts, n = glyph.contours[ci].points, len(glyph.contours[ci].points)
                P = [(pts[i].x, pts[i].y) for i in idx]
                counter_ink, counter_rep = ink, aligned
                if beyond and char != name:             # þ: the mockup's b, scaled across to our counter
                    E = pts[beyond[3]]
                    far_edge = strokes.cut(aligned, E.y + strokes.EPS)[1 if side > 0 else -2][0 if side > 0 else 1]
                    k = (E.x - edge) / (far_edge - edge)
                    counter_rep = lambda pen, a=aligned, k=k: a(TransformPen(pen, (k, 0, 0, 1, edge * (1 - k), 0)))
                    counter_ink = ink_edge(counter_rep)
                if beyond or kind == "arm":
                    counter_ink = depth_kept(replay, counter_rep, counter_ink, pts[idx[3]].y > pts[idx[0]].y)
                if beyond:
                    R = [(pts[i].x, pts[i].y) for i in beyond]
                if slide == "side" and char == name:    # the counter's far extremum: the mockup's
                    E = R[3]                            # stroke there, from our outer edge
                    m_run, o_run = (strokes.cut(f, E[1] + strokes.EPS)[-1 if side > 0 else 0]
                                    for f in (counter_rep, replay))
                    x = m_run[0] + o_run[1] - m_run[1] if side > 0 else m_run[1] + o_run[0] - m_run[0]
                    R = [*R[:2], (R[2][0] + x - E[0], R[2][1]), (x, E[1])]
                if kind == "notch":                     # the mockup's notch, from our stem's edge
                    P[0] = mockup_notch(rec, P[0], edge, side)
                forward = (idx[1] - idx[0]) % n == 1
                labels = {(ci, idx[3] if forward else idx[0])}
                if kind == "arm":
                    labels |= {(ci, idx[6])}
                if beyond:
                    labels |= {(ci, beyond[3] if forward else beyond[0])}
                far_line = None
                if slide == "stem":                     # and the far stem's line out of it
                    far_line = (ci, (beyond[3] + 1) % n if forward else beyond[3])
                    labels.add(far_line)
                if kind in ("inner", "arm"):            # and the stem's line into it
                    labels.add((ci, idx[0] if forward else (idx[0] + 1) % n))
                # the mockup's edge where our nearest outline is this curve, near the stem
                edge_pts = counter_ink if beyond or kind == "arm" else ink
                dd = ((edge_pts[:, None] - lab[None, :, :2]) ** 2).sum(2)
                near = lab[dd.argmin(1)]
                d = (edge_pts[:, 0] - edge) * side
                reach = min(NEAR[master], 0.7 * abs(P[3][0] - edge))
                if kind == "arm":                       # all the way to the terminal
                    reach = abs(P[-1][0] - edge) - 5
                if beyond:                              # all the way to the far side
                    reach = np.inf
                ok = np.array([(int(a), int(b)) in labels for a, b in near[:, 2:]]) & (np.sqrt(dd.min(1)) < 90)
                if kind in ("inner", "arm"):            # the stem's line only where it's straight
                    ok &= (np.abs(edge_pts[:, 0] - P[0][0]) < 8) | (d > 4)
                if far_line:                            # the far stem's, near the curve
                    on_line = np.array([(int(a), int(b)) == far_line for a, b in near[:, 2:]])
                    ok &= ~on_line | (np.abs(edge_pts[:, 1] - R[3][1]) < 150)
                ok &= d <= reach
                if kind == "notch":                     # past the mockup's notch
                    ok &= d >= (P[0][0] - edge) * side + 2
                if kind == "valley":
                    ok &= d >= 14
                mine = bezier(P[:4], np.linspace(0, 1, 400))
                far = mine[(mine[:, 0] - edge) * side >= max(FAR[master], reach + 50)][::4]
                targets = np.vstack([edge_pts[ok], far])
                stop, extra = None, lambda Q: []
                if kind in ("inner", "arm"):            # the stem's line is part of the outline fitted
                    k = pts[(idx[0] - 1) % n if forward else (idx[0] + 1) % n]
                    stop = (k.x, k.y)
                    extra = lambda Q, stop=stop: [np.array([stop, Q[0]])]
                if beyond:
                    far_stop = None
                    if slide == "stem":                 # the far stem's line is part of it too
                        k = pts[(beyond[3] + 1) % n if forward else (beyond[3] - 1) % n]
                        far_stop = (k.x, k.y)
                        extra = lambda Q, stop=stop, far_stop=far_stop: (
                            [np.array([stop, Q[0]])] if stop else []) + [np.array([Q[-1], far_stop])]
                    balance = ((2, 3), (4, 5)) if slide else ((2, 3),)   # r's far end is the terminal's corner
                    Q, err = solve(*free_top(kind, P, R, stop, far_stop), targets, extra, balance)
                    idx, moved = (*idx, *beyond[1:]), (*idx, *beyond[1:3], *([beyond[3]] if slide else []))
                else:
                    Q, err = solve(*free(kind, P, stop), targets, extra, ((1, 2),) if kind == "arm" else ())
                    moved = idx if kind == "arm" else idx[:3]
                print(f"  {master} {name} {kind} {idx}: {ok.sum()} + {len(far)} targets, "
                      f"rms {np.sqrt(np.mean(err ** 2)):.1f}", file=sys.stderr)
                for i, q in zip(idx, Q):
                    if i in moved and (round(float(q[0])), round(float(q[1]))) != (pts[i].x, pts[i].y):
                        rows.append((group, ci, i, round(float(q[0]) - edge, 1), round(float(q[1]))))
                if line_end is not None:
                    rows.append((group, ci, line_end, round(pts[line_end].x - edge, 1), round(float(Q[0][1]))))
        kept = {r[:3]: r for r in POINTS.get(master, {}).get(name, [])}   # points not refitted stay
        kept.update({r[:3]: r for r in rows})
        table[name] = sorted(kept.values(), key=lambda r: (r[1], r[2]))
    return table


# --- 5, after n --------------------------------------------------------------------------

# 5's joint is fitted to n's weight FIVE_AT units from the stem, as a fraction of each glyph's
# depth, and FIVE_SPLIT of the extra weight 15 units from the stem comes from the notch (the
# rest from the foot's corner).
FIVE_AT, FIVE_SPLIT = 80, 0.5


def five_curves():
    (edge, _, _, ((_, ci, inner), (_, _, outer, line_end))), = STEMS["five"][1]
    return edge, ci, inner, outer, line_end


def five_runs(font, distances):
    """5's top stroke on vertical lines `distances` units right of its notch: [(bottom, top)]."""
    (_, bar), ci, _, _, line_end = five_curves()            # the stem's top corner, under the bar
    pts = font["five"].contours[ci].points
    replay = ours(font, "five")
    return [[r for r in vertical_runs(replay, pts[line_end].x + d) if r[1] < pts[bar].y][-1] for d in distances]


def n_like(font, distances):
    """n's top stroke at `distances` from its stem, over its depth, times 5's depth."""
    _, ci, inner, outer, _ = five_curves()
    pts, replay = font["five"].contours[ci].points, ours(font, "n")
    n = np.array(widths(replay, CHECK["n"], distances)[0]) / depth(replay, CHECK["n"], -1)[1]
    return n * (pts[outer[3]].y - pts[inner[3]].y)


def fit_five(font, at=FIVE_AT, split=FIVE_SPLIT):
    """POINTS rows for 5: the notch's line end slides up the stem's edge, taking the outer curve's
    end with it, and the foot's corner, where the counter's top curve starts, slides down a
    line parallel to that edge, so the foot's line steepens. Each curve keeps its far end (the
    bowl's top, the counter's top) and its shape, scaled to its new ends. How far each slides
    is fitted so 5 has n's weight `at` units from the stem, `split` of the extra 15 units out
    coming from the notch."""
    from scipy.optimize import least_squares

    (_, edge), ci, inner, outer, line_end = five_curves()
    pts = font["five"].contours[ci].points
    P = {i: np.array((pts[i].x, pts[i].y), float) for i in (edge, line_end, *inner, *outer)}
    stem = (P[line_end] - P[edge]) / (P[line_end][1] - P[edge][1])     # per unit of height

    def moved(rise, drop):
        out = {line_end: P[line_end] + stem * rise}
        for idx, shift in ((outer, rise), (inner, -drop)):
            S, F = P[idx[0]], P[idx[3]]
            scale = (F - S - stem * shift) / (F - S)
            out.update({i: F - (F - P[i]) * scale for i in idx[:3]})
        return out

    def runs(v):
        for i, q in moved(*v).items():
            pts[i].x, pts[i].y = q
        out = five_runs(font, (15, at))
        for i, q in moved(0, 0).items():
            pts[i].x, pts[i].y = q
        return out

    (bottom, top), _ = runs((0, 0))
    target = n_like(font, (at,))[0]

    def resid(v):
        (b, t), (b_at, t_at) = runs(v)
        return [(1 - split) * (t - top) - split * (bottom - b), t_at - b_at - target]

    v = least_squares(resid, [10, 10], bounds=([0, 0], [200, 200])).x
    return [(0, ci, i, round(float(q[0] - P[edge][0]), 1), round(float(q[1])))
            for i, q in sorted(moved(*v).items()) if (round(q[0]), round(q[1])) != (pts[i].x, pts[i].y)]


# How the joints are measured (tools/joints.py --check): the stem is found on a horizontal
# scanline at y (its run, and +1 if the joint is right of it), and the joint is the top (-1)
# or bottom (0) run on vertical scanlines DISTANCES from the stem's edge. The depth is from
# the outer edge's top (bottom) to the counter's, across to the far side.
CHECK = {"n": (500, 0, +1, (-1,)), "h": (500, 0, +1, (-1,)), "r": (500, 0, +1, (-1,)),
         "m": (500, 0, +1, (-1,)), "m.2": (500, 1, +1, (-1,)), "u": (500, -1, -1, (0,)),
         "a": (380, -1, -1, (0,)), "b": (500, 0, +1, (-1, 0)), "d": (500, -1, -1, (-1, 0)),
         "p": (500, 0, +1, (-1, 0)), "q": (500, -1, -1, (-1, 0)), "thorn": (500, 0, +1, (-1, 0))}
DISTANCES = (15, 40, 80, 140, 200, 260)


def widths(replay, spec, distances=DISTANCES):
    y, run, side, which = spec
    edge = strokes.cut(replay, y + strokes.EPS)[run][1 if side > 0 else 0]
    out = []
    for w in which:
        runs = [vertical_runs(replay, edge + side * d) for d in distances]
        out.append([r[w][1] - r[w][0] if r else float("nan") for r in runs])
    return out


def depth(replay, spec, w):
    """(The counter's top, or bottom if w is 0; the depth of the arch or bowl there)."""
    y, run, side, _ = spec
    edge = strokes.cut(replay, y + strokes.EPS)[run][1 if side > 0 else 0]
    inner, outer = [], []
    for d in range(5, 1200, 5):
        runs = [r for r in vertical_runs(replay, edge + side * d) if -300 < r[0] and r[1] < 1300]
        if runs and not inner or runs and runs[w][1] - runs[w][0] < 500:
            outer.append(runs[w][1] if w else runs[w][0])
        if runs and runs[w][1] - runs[w][0] < 500:
            inner.append(runs[w][0] if w else runs[w][1])
        elif inner:                                     # past the counter: the far stem's or side's edge
            if runs:
                outer.append(runs[w][1] if w else runs[w][0])
            break
    return (max(inner), max(outer) - max(inner)) if w else (min(inner), min(inner) - min(outer))


def check(src="source"):
    for master in MASTERS:
        font = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
        for key, spec in CHECK.items():
            name = key.split(".")[0]
            far = (220, 280, 350) if name == "r" else ()
            o = widths(ours(font, name), spec, DISTANCES + far)
            m = widths(mockup(master, "b" if name == "thorn" else name), spec, DISTANCES + far)
            for w, ow, mw in zip(spec[3], o, m):
                cells = "  ".join(f"{a:4.0f}/{b:<4.0f}" for a, b in zip(ow, mw))
                (oc, od), (mc, md) = (depth(f, spec, w) for f in (ours(font, name), mockup(master, "b" if name == "thorn" else name)))
                print(f"{master:7s} {key:5s} {'top' if w else 'bottom':6s}  depth {od:3.0f}/{md:<3.0f} at {oc:4.0f}/{mc:<4.0f}"
                      f"  ours/mockup at {DISTANCES + far}:  {cells}")
            if key == "n":                              # 5 against n, scaled to 5's depth
                _, ci, inner, outer, _ = five_curves()
                pts = font["five"].contours[ci].points
                cells = "  ".join(f"{t - b:4.0f}/{n:<4.0f}" for (b, t), n in
                                  zip(five_runs(font, DISTANCES), n_like(font, DISTANCES)))
                print(f"{master:7s} {'5':5s} {'top':6s}  depth {pts[outer[3]].y - pts[inner[3]].y:3.0f}     at "
                      f"{pts[inner[3]].y:4.0f}       ours/n's  at {DISTANCES}:  {cells}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fit"]:
        print({m: fit_master(m, os.path.join(strokes.ROOT, "source"), sys.argv[2:]) for m in MASTERS})
    elif sys.argv[1:2] == ["--check"]:
        check(*sys.argv[2:])
    else:
        main(sys.argv[1:])
