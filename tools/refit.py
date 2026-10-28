"""Fit R, B, G, c and e to the mockups: R's bowl and leg, B's middle bar, G's bar, and c's
and e's bowls, e's bar and their terminal cuts.

These letters were still Inter's construction where the mockups' differs:

- R: the bowl's lower bar sits higher (like P's, which tools/reshape.py moves), the bowl
  is wider, and the leg leans more.
- B: the middle bar is thicker, and in Regular higher.
- G: the bar starts further left, and its underside meets the bowl's inner curve where
  that runs straight up into the bar (in Black, 27 units lower than Inter's).
- c and e: the bowls take the mockups' curves, e's bar the mockups' height and weight
  (Regular's 9 units higher, Black's 28 lighter), and the terminal cuts the mockups'
  angles (Black e's lower one 20 degrees, Inter's 9). The mockups' terminals also reach
  further round, closing the opening; the user chose Inter's wider opening, so each cut is
  turned about the middle of Inter's (APERTURE) and the fitted curves cut back to it.

In Regular and Black each letter takes the mockup's outline (mockup.svg,
mockup-black.svg): every moved on-curve point goes to the mockup's corner or extreme of
the same kind nearest it, and each curve between them gets handles fitted by least
squares to the mockup's outline between its ends, along the mockup's tangents. Black's
mockup splits each of our curves into two or three, so there ours approximates it. Where
Inter's construction hides a point inside another stroke (R's lower bar end and leg top,
G's spur, e's bar ends and the counter's ends inside the bar), it stays hidden, and the
curve leaving it is fitted only to the part of the mockup's outline that shows. The tops
and bottoms of the round letters keep their heights (the mockups overshoot by 25, our
capitals by 20 and c and e by 23), and the stems keep their edges.

Thin's screenshot (mockup-thin.webp) is too blurred to take points from, and its strokes
are about 105 units thick against Thin's 46. So Thin makes the same construction moves,
measured on its guide (the screenshot traced into `public.background`): R's and B's bars
and G's and e's crossbars are centred on the guide's, R's bowl takes the guide's width
(from the stem) and its leg the guide's slope (its foot stays). The curves either side of
a moved bar are scaled to meet it, as P's are. Thin's c and e keep Inter's terminals.

`--fit` makes POINTS from the mockups and guides; applying moves the points to POINTS.
No points are added or removed, every master gets the same ones, and each changed glyph
keeps its right sidebearing (so do the glyphs built on them). An anchor on a moved point
(e's ogonek, c's topr) moves with it, and ę's ogonek (ogonek.e), which ends just inside
e's lower cut, keeps its place against the turned cut. Running it again changes nothing.

Usage: python tools/refit.py source/PlaceholderSans-*.ufo
       python tools/refit.py --fit [source]    # print POINTS fitted to the mockups and guides
"""

import copy
import os
import re
import sys

import numpy as np
import ufoLib2
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import joints  # noqa: E402
import reshape  # noqa: E402
import strokes  # noqa: E402

GLYPHS = ("R", "B", "G", "c", "e")
THIN_STEM = 46

# The middle of each of Inter's c and e terminal cuts (x from the left ink edge, y). The
# mockups' terminals reach further round, closing the opening; the user kept Inter's wider
# opening, so the fitted terminals are cut through these, at the mockups' angles.
APERTURE = {
    "Regular": {"c": [(928.0, 329.0), (923.5, 747.0)], "e": [(902.5, 282.5)]},
    "Black": {"c": [(930.5, 432.5), (929.5, 644.0)], "e": [(905.5, 324.5)]},
}

# Fitted by `--fit`: {master: {glyph: [(contour, point, x from the left ink edge, y)]}}
POINTS = {
    "Thin": {
        "R": [(0, 2, 46, 1444), (0, 3, 476, 1444), (0, 4, 747, 1444), (0, 5, 941, 1305),
            (0, 6, 941, 1094), (0, 7, 941, 885), (0, 8, 747, 747), (0, 9, 476, 747),
            (0, 10, 24, 747), (0, 11, 24, 701), (0, 12, 476, 701), (0, 13, 772, 701),
            (0, 14, 987, 858), (0, 15, 987, 1094), (0, 16, 987, 1332), (0, 17, 772, 1490),
            (0, 18, 476, 1490), (0, 19, 0, 1490), (1, 2, 554, 724), (1, 3, 502, 724)],
        "B": [(0, 1, 565, 0), (0, 2, 843, 0), (0, 3, 1008, 155), (0, 4, 1008, 392),
            (0, 5, 1008, 603), (0, 6, 860, 759), (0, 7, 696, 773), (0, 8, 696, 779),
            (0, 9, 855, 814), (0, 10, 945, 951), (0, 11, 945, 1122), (0, 12, 945, 1350),
            (0, 13, 782, 1490), (0, 14, 509, 1490), (1, 0, 46, 46), (1, 1, 46, 753),
            (1, 2, 564, 753), (1, 3, 796, 753), (1, 4, 962, 603), (1, 5, 962, 391),
            (1, 6, 962, 184), (1, 7, 804, 46), (1, 8, 565, 46), (2, 0, 46, 799),
            (2, 1, 46, 1444), (2, 2, 509, 1444), (2, 3, 748, 1444), (2, 4, 898, 1326),
            (2, 5, 898, 1122), (2, 6, 898, 949), (2, 7, 790, 799), (2, 8, 566, 799)],
        "G": [(0, 1, 999, -20), (0, 2, 1233, 253), (0, 3, 1233, 671), (0, 4, 1233, 715),
            (0, 5, 655, 715), (0, 6, 655, 669), (0, 7, 1207, 669), (0, 8, 1187, 679),
            (0, 9, 1187, 279), (0, 10, 976, 26)],
        "e": [(0, 8, 203, 23), (0, 9, 46, 268), (0, 10, 46, 563), (0, 11, 46, 570),
            (0, 12, 46, 841), (0, 13, 232, 1045), (0, 15, 693, 1045), (0, 16, 865, 841),
            (0, 17, 865, 585), (0, 18, 885, 605), (0, 19, 24, 605), (0, 20, 24, 559),
            (0, 21, 910, 559), (0, 22, 910, 585), (0, 23, 910, 875), (0, 24, 717, 1103)],
    },
    "Regular": {
        "R": [(0, 2, 204.0, 1304), (0, 3, 643.6, 1304), (0, 4, 811.2, 1304),
            (0, 5, 914.7, 1225), (0, 6, 914.7, 1055), (0, 7, 914.7, 892), (0, 8, 809.2, 807),
            (0, 9, 635.3, 807), (0, 10, 114.0, 807), (0, 11, 114.0, 621), (0, 12, 637.1, 621),
            (0, 13, 952.6, 621), (0, 14, 1129.9, 804), (0, 15, 1129.9, 1055),
            (0, 16, 1129.9, 1322), (0, 17, 939.5, 1490), (0, 18, 651.9, 1490),
            (1, 0, 904.3, 0), (1, 1, 1158.9, 0), (1, 2, 691.5, 714), (1, 3, 454.6, 714)],
        "B": [(0, 1, 664.3, 0), (0, 2, 972.6, 0), (0, 3, 1146.4, 172), (0, 4, 1146.4, 420),
            (0, 5, 1146.4, 644), (0, 6, 1014.0, 755), (0, 7, 850.6, 791), (0, 8, 850.6, 803),
            (0, 9, 978.7, 853), (0, 10, 1076.1, 941), (0, 11, 1076.1, 1103),
            (0, 12, 1076.1, 1337), (0, 13, 900.2, 1490), (0, 14, 629.1, 1490),
            (1, 0, 204.0, 190), (1, 1, 204.0, 683), (1, 2, 662.2, 683), (1, 3, 827.8, 683),
            (1, 4, 933.3, 598), (1, 5, 933.3, 437), (1, 6, 933.3, 281), (1, 7, 831.9, 190),
            (1, 8, 662.2, 190), (2, 0, 204.0, 873), (2, 1, 204.0, 1300), (2, 2, 620.8, 1300),
            (2, 3, 767.8, 1300), (2, 4, 867.1, 1227), (2, 5, 867.1, 1089), (2, 6, 867.1, 950),
            (2, 7, 765.7, 873), (2, 8, 620.8, 873)],
        "G": [(0, 0, 716.3, -20), (0, 1, 1110.3, -20), (0, 2, 1374.1, 231),
            (0, 3, 1374.1, 615), (0, 4, 1374.1, 784), (0, 5, 699.7, 784), (0, 6, 699.7, 594),
            (0, 7, 1203.0, 594), (0, 8, 1163.0, 610), (0, 9, 1163.0, 318),
            (0, 10, 989.9, 166), (0, 11, 720.0, 166), (0, 12, 384.9, 166),
            (0, 13, 215.3, 387), (0, 14, 215.3, 745), (0, 15, 215.3, 1103),
            (0, 16, 387.2, 1324), (0, 17, 720.0, 1324), (0, 18, 945.9, 1324),
            (0, 19, 1090.6, 1223), (0, 20, 1140.4, 1035), (0, 21, 1349.2, 1080),
            (0, 22, 1298.5, 1289), (0, 23, 1117.8, 1510), (0, 24, 720.0, 1510),
            (0, 25, 285.6, 1510), (0, 26, 0.0, 1198), (0, 27, 0.0, 745), (0, 28, 0.0, 293),
            (0, 29, 281.2, -20)],
        "c": [(0, 0, 534.0, -23), (0, 1, 781.0, -23), (0, 2, 956.0, 115), (0, 3, 1008.0, 310),
            (0, 4, 814.0, 356), (0, 5, 774.0, 235), (0, 6, 687.0, 153), (0, 7, 534.0, 153),
            (0, 8, 322.8, 153), (0, 9, 202.8, 300), (0, 10, 202.8, 538), (0, 11, 202.8, 776),
            (0, 12, 324.9, 923), (0, 13, 534.0, 923), (0, 14, 684.0, 923),
            (0, 15, 773.0, 845), (0, 16, 814.0, 729), (0, 17, 1008.0, 761),
            (0, 18, 952.0, 969), (0, 19, 772.0, 1101), (0, 20, 534.0, 1101),
            (0, 21, 229.9, 1101), (0, 22, 0.0, 880), (0, 23, 0.0, 538), (0, 24, 0.0, 202),
            (0, 25, 222.5, -23)],
        "e": [(0, 0, 519.0, -23), (0, 1, 793.0, -23), (0, 2, 920.0, 114), (0, 3, 978.0, 257),
            (0, 4, 796.0, 319), (0, 5, 740.0, 209), (0, 6, 657.0, 153), (0, 7, 519.0, 153),
            (0, 8, 301.9, 153), (0, 9, 201.8, 326), (0, 10, 201.8, 497), (0, 11, 201.8, 627),
            (0, 12, 201.8, 670), (0, 13, 259.7, 923), (0, 14, 521.5, 923),
            (0, 15, 799.3, 923), (0, 16, 809.3, 640), (0, 17, 812.9, 597),
            (0, 18, 902.9, 642), (0, 19, 125.0, 642), (0, 20, 125.0, 482),
            (0, 21, 1014.0, 482), (0, 22, 1014.0, 540), (0, 23, 1014.0, 900),
            (0, 24, 811.0, 1101), (0, 25, 521.5, 1101), (0, 26, 223.7, 1101),
            (0, 27, 0.0, 873), (0, 28, 0.0, 538), (0, 29, 0.0, 202), (0, 30, 209.8, -23)],
        "ogonek.e": [(0, 12, 340.7, 38), (0, 13, 413.7, 266)],
    },
    "Black": {
        "R": [(0, 2, 377.0, 1163), (0, 3, 664.3, 1163), (0, 4, 774.5, 1163),
            (0, 5, 844.3, 1101), (0, 6, 844.3, 997), (0, 7, 844.3, 902), (0, 8, 786.9, 836),
            (0, 9, 664.3, 836), (0, 10, 226.0, 836), (0, 11, 226.0, 530), (0, 12, 697.4, 530),
            (0, 13, 1083.5, 530), (0, 14, 1225.1, 752), (0, 15, 1225.1, 997),
            (0, 16, 1225.1, 1271), (0, 17, 1038.5, 1490), (0, 18, 697.4, 1490),
            (1, 0, 829.9, 0), (1, 1, 1266.5, 0), (1, 2, 819.5, 706), (1, 3, 432.5, 706)],
        "B": [(0, 1, 726.4, 0), (0, 2, 1167.5, 0), (0, 3, 1245.8, 249), (0, 4, 1245.8, 395),
            (0, 5, 1245.8, 643), (0, 6, 1089.1, 746), (0, 7, 962.3, 778), (0, 8, 962.3, 791),
            (0, 9, 1147.1, 864), (0, 10, 1177.5, 980), (0, 11, 1177.5, 1089),
            (0, 12, 1177.5, 1318), (0, 13, 1004.5, 1490), (0, 14, 672.6, 1490),
            (1, 0, 377.0, 327), (1, 1, 377.0, 610), (1, 2, 701.5, 610), (1, 3, 796.7, 610),
            (1, 4, 863.0, 558), (1, 5, 863.0, 470), (1, 6, 863.0, 384), (1, 7, 802.2, 327),
            (1, 8, 701.5, 327), (2, 0, 377.0, 913), (2, 1, 377.0, 1163), (2, 2, 649.8, 1163),
            (2, 3, 724.2, 1163), (2, 4, 792.6, 1126), (2, 5, 792.6, 1037), (2, 6, 792.6, 924),
            (2, 7, 691.7, 913), (2, 8, 649.8, 913)],
        "G": [(0, 0, 768.0, -20), (0, 1, 1236.9, -20), (0, 2, 1471.4, 247),
            (0, 3, 1471.4, 625), (0, 4, 1471.4, 824), (0, 5, 724.2, 824), (0, 6, 724.2, 517),
            (0, 7, 1177.7, 517), (0, 8, 1094.8, 586), (0, 9, 1094.8, 427),
            (0, 10, 1009.4, 300), (0, 11, 768.0, 300), (0, 12, 509.4, 300),
            (0, 13, 393.2, 480), (0, 14, 393.2, 745), (0, 15, 393.2, 998),
            (0, 16, 495.8, 1180), (0, 17, 757.3, 1180), (0, 18, 957.5, 1180),
            (0, 19, 1035.7, 1062), (0, 20, 1061.6, 969), (0, 21, 1442.3, 1051),
            (0, 22, 1415.7, 1168), (0, 23, 1295.8, 1510), (0, 24, 763.8, 1510),
            (0, 25, 322.8, 1510), (0, 26, 0.0, 1209), (0, 27, 0.0, 743), (0, 28, 0.0, 275),
            (0, 29, 275.9, -20)],
        "c": [(0, 0, 565.0, -20), (0, 1, 802.0, -20), (0, 2, 1030.0, 48), (0, 3, 1097.0, 402),
            (0, 4, 746.0, 466), (0, 5, 718.0, 322), (0, 6, 643.0, 294), (0, 7, 565.0, 294),
            (0, 8, 446.6, 294), (0, 9, 368.4, 375), (0, 10, 368.4, 538), (0, 11, 368.4, 673),
            (0, 12, 425.9, 782), (0, 13, 565.0, 782), (0, 14, 702.0, 782),
            (0, 15, 736.0, 679), (0, 16, 745.0, 610), (0, 17, 1096.0, 674),
            (0, 18, 1066.0, 884), (0, 19, 921.0, 1101), (0, 20, 565.0, 1101),
            (0, 21, 259.0, 1101), (0, 22, 0.0, 904), (0, 23, 0.0, 538), (0, 24, 0.0, 172),
            (0, 25, 257.7, -20)],
        "e": [(0, 0, 557.0, -20), (0, 1, 646.0, -20), (0, 2, 939.0, -21), (0, 3, 1051.0, 272),
            (0, 4, 740.0, 384), (0, 5, 678.0, 263), (0, 6, 595.0, 259), (0, 7, 557.0, 259),
            (0, 8, 375.1, 259), (0, 9, 358.3, 434), (0, 10, 358.3, 468), (0, 11, 358.3, 627),
            (0, 12, 358.3, 654), (0, 13, 375.6, 822), (0, 14, 548.4, 822),
            (0, 15, 717.1, 822), (0, 16, 720.7, 628), (0, 17, 724.7, 597),
            (0, 18, 814.7, 642), (0, 19, 122.0, 642), (0, 20, 122.0, 453),
            (0, 21, 1078.2, 453), (0, 22, 1078.2, 511), (0, 23, 1078.2, 853),
            (0, 24, 899.8, 1101), (0, 25, 548.4, 1101), (0, 26, 229.8, 1101),
            (0, 27, 0.0, 858), (0, 28, 0.0, 538), (0, 29, 0.0, 231), (0, 30, 179.6, -20)],
        "ogonek.e": [(0, 12, 451.6, 86), (0, 13, 503.6, 281)],
    },
}


# --- applying POINTS --------------------------------------------------------------------

def apply(ufo, master):
    """Move the points in `ufo` to POINTS; returns the names of the glyphs that changed."""
    table = POINTS.get(master, {})
    touched = reshape.users(ufo, table)
    before = {name: reshape.outline(ufo, name) for name in touched}
    right = {name: ufo[name].getBounds(ufo).xMax for name in touched if ufo[name].getBounds(ufo)}
    for name, rows in table.items():
        glyph = ufo[name]
        left = glyph.getBounds(ufo).xMin
        for ci, i, dx, y in rows:
            p = glyph.contours[ci].points[i]
            x = round(left + dx)
            for a in glyph.anchors:
                if p.type and (a.x, a.y) == (p.x, p.y):
                    a.x, a.y = x, y
            p.x, p.y = x, y
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
        print(f"{path}: {', '.join(changed) or 'nothing'} refitted ({master})")


# --- outlines ---------------------------------------------------------------------------

def unit(v):
    v = np.asarray(v, float)
    return v / np.hypot(*v)


def kind(into, out):
    """'h' or 'v' for a smooth point with a level or upright tangent, 's' for another smooth
    point, 'c' for a corner (tangents more than 3 degrees apart)."""
    if np.dot(into, out) < np.cos(np.radians(3)):
        return "c"
    t = unit(into + out)
    if abs(t[1]) < np.sin(np.radians(2)):
        return "h"
    if abs(t[0]) < np.sin(np.radians(2)):
        return "v"
    return "s"


class Outline:
    """A recorded outline's contours, each a list of segments (arrays of points); its nodes
    are the segments' starts."""

    def __init__(self, replay):
        rec = RecordingPen()
        replay(rec)
        self.contours, cur, start = [], None, None
        for op, args in rec.value:
            if op == "moveTo":
                cur = start = np.array(args[0], float)
                self.contours.append([])
            elif op == "closePath":
                if np.hypot(*(cur - start)) > 0.01:
                    self.contours[-1].append(np.array([cur, start]))
            else:
                seg = np.array([cur, *args], float)
                if len(seg) > 2 or np.hypot(*(seg[1] - seg[0])) > 0.01:
                    self.contours[-1].append(seg)
                cur = seg[-1]

    def nodes(self):
        return [(k, j) for k, segs in enumerate(self.contours) for j in range(len(segs))]

    def at(self, node):
        k, j = node
        return self.contours[k][j][0]

    def tangents(self, node):
        """Unit tangents into and out of a node, along the contour."""
        k, j = node
        segs = self.contours[k]
        out = next(p for p in segs[j][1:] if np.hypot(*(p - segs[j][0])) > 0.01) - segs[j][0]
        prev = segs[j - 1]
        into = prev[-1] - next(p for p in prev[-2::-1] if np.hypot(*(p - prev[-1])) > 0.01)
        return unit(into), unit(out)

    def find(self, near, want, within=120, taken=()):
        """The node of a kind in `want` nearest `near`, other than those `taken`."""
        dist, node = min(((np.hypot(*(self.at(n) - near)), n) for n in self.nodes()
                          if kind(*self.tangents(n)) in want and n not in taken), default=(np.inf, None))
        if dist > within:
            raise ValueError(f"no {want} node within {within} of {tuple(np.round(near))}")
        return node

    def walk(self, node, step):
        """Dense points along the contour from a node, forward (step 1) or back (-1), once round."""
        k, j = node
        segs, out = self.contours[k], []
        for n in range(len(segs)):
            seg = segs[(j + n) % len(segs)] if step == 1 else segs[(j - 1 - n) % len(segs)][::-1]
            out.append(joints.bezier(seg, np.linspace(0, 1, 120)) if len(seg) == 4
                       else np.linspace(seg[0], seg[1], 60))
        return np.vstack(out)

    def path(self, a, start_dir, stop):
        """Points from node a, setting off along start_dir, up to `stop`: a node, or a test
        on each point that is true once the path has gone far enough. Also the tangents
        leaving a and arriving at the end (pointing back along the path)."""
        into, out = self.tangents(a)
        step = 1 if np.dot(out, start_dir) > np.dot(-into, start_dir) else -1
        pts = self.walk(a, step)
        test = stop if callable(stop) else (lambda p: np.hypot(*(p - self.at(stop))) < 0.01)
        end = next(i for i in range(5, len(pts)) if test(pts[i]))
        if callable(stop):
            back = unit(pts[end - 1] - pts[end])
        else:
            b_into, b_out = self.tangents(stop)
            back = -b_into if step == 1 else b_out
        return pts[:end + 1], (out if step == 1 else -into), back


def our_tangents(contour, i):
    pts, n = contour.points, len(contour.points)
    p = (pts[i].x, pts[i].y)
    prev = next((q.x, q.y) for q in (pts[(i - k) % n] for k in range(1, n)) if (q.x, q.y) != p)
    nxt = next((q.x, q.y) for q in (pts[(i + k) % n] for k in range(1, n)) if (q.x, q.y) != p)
    return unit(np.subtract(p, prev)), unit(np.subtract(nxt, p))


# --- Regular and Black: fitting to the mockups ------------------------------------------

def fit_handles(P0, t0, P3, t3, target, oneway=False):
    """Handles leaving P0 along t0 and P3 along t3, fitted to the points `target`: both
    ways (the target's points to the curve and the curve's to the target), or only the
    target's points to the curve if the curve runs on past them (`oneway`). The handles
    stay inside the box of P0 and P3, so extremes stay extremes."""
    from scipy.optimize import least_squares

    P0, P3, t0, t3 = (np.asarray(v, float) for v in (P0, P3, t0, t3))
    span = np.hypot(*(P3 - P0))
    lo, hi = np.minimum(P0, P3) - 0.5, np.maximum(P0, P3) + 0.5

    def reach(P, t):                    # how far along t from P stays in the box, over span
        out = 1.5
        for k in range(2):
            if abs(t[k]) > 1e-9:
                out = min(out, ((hi[k] if t[k] > 0 else lo[k]) - P[k]) / t[k] / span)
        return max(out, 0.15)

    top = [reach(P0, t0), reach(P3, t3)]
    build = lambda x: np.array([P0, P0 + x[0] * span * t0, P3 + x[1] * span * t3, P3])
    t = np.linspace(0, 1, 300)

    def resid(x):
        curve = joints.bezier(build(x), t)
        r = joints.distances(target, curve)
        return r if oneway else np.concatenate([r, joints.distances(curve[::3], target)])

    res = min((least_squares(resid, np.minimum(x0, np.array(top) - 1e-3), bounds=([0.1, 0.1], top))
               for x0 in ([0.3, 0.3], [0.55, 0.55], [0.8, 0.4], [0.4, 0.8])), key=lambda r: r.cost)
    Q = build(res.x)
    return Q[1], Q[2], np.abs(res.fun[:len(target)]).max()


class Fit:
    """One glyph's new points in one master: on-curve points first, then the curves."""

    def __init__(self, font, master, name):
        self.glyph, self.master, self.name = font[name], master, name
        self.left = self.glyph.getBounds(font).xMin
        mock = joints.mockup(master, name)        # its left ink edge on ours
        self.mock = Outline(lambda pen: mock(TransformPen(pen, (1, 0, 0, 1, self.left, 0))))
        self.new, self.nodes, self.worst = {}, {}, 0.0

    def pt(self, ci, i):
        if (ci, i) in self.new:
            return self.new[ci, i]
        p = self.glyph.contours[ci].points[i]
        return np.array((p.x, p.y), float)

    def node(self, ci, i, keep_x=False, keep_y=False, near=(0, 0)):
        """Point i goes to the mockup's nearest node of its own kind (to it offset by `near`)
        that no other point has taken."""
        n = self.mock.find(self.pt(ci, i) + near, kind(*our_tangents(self.glyph.contours[ci], i)),
                           taken=set(self.nodes.values()))
        self.nodes[ci, i] = n
        x, y = self.mock.at(n)
        self.set(ci, i, None if keep_x else x, None if keep_y else y)
        return n

    def set(self, ci, i, x=None, y=None):
        p = self.pt(ci, i)
        self.new[ci, i] = np.array((p[0] if x is None else x, p[1] if y is None else y), float)

    def curve(self, ci, i, step=1, stop=None, end_dir=None):
        """Fit the curve from on-curve point i (on a mockup node) to the next on-curve point
        along the contour (step 1) or back (-1). The mockup's outline runs from i's node to
        `stop` (the far end's node if not given). If the far end is hidden, and so not on
        the mockup's outline, `end_dir` is its tangent, pointing back along the curve."""
        n = len(self.glyph.contours[ci].points)
        idx = [(i + k * step) % n for k in range(4)]
        P0, h0, h3, P3 = (self.pt(ci, k) for k in idx)
        target, t0, t3 = self.mock.path(self.nodes[ci, i], unit(h0 - P0), stop or self.nodes[ci, idx[3]])
        # where an end keeps a coordinate of its own (an overshoot, a stem's edge), the
        # mockup's outline is moved onto it, less and less toward the other end
        along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(target, axis=0).T))])
        along /= along[-1]
        target = target + np.outer(1 - along, P0 - target[0])
        if end_dir is None:
            target = target + np.outer(along, P3 - target[-1])
        H0, H3, worst = fit_handles(P0, t0, P3, t3 if end_dir is None else unit(end_dir),
                                    target, oneway=end_dir is not None)
        self.new[ci, idx[1]], self.new[ci, idx[2]] = H0, H3
        self.worst = max(self.worst, worst)
        return target

    def rows(self):
        return sorted((ci, i, round(float(q[0]) - self.left, 1), round(float(q[1])))
                      for (ci, i), q in self.new.items())


def fit_R(font, master):
    """The bowl (outer and inner curves, the bar) and the leg. In mockup.svg the bowl's
    outer curve runs into the leg's edge; ours runs on into the leg, a separate contour,
    down to the bar's underside."""
    f = Fit(font, master, "R")
    for i in (3, 6, 9, 15, 18):
        f.node(0, i)
    f.set(0, 2, y=f.pt(0, 3)[1])                    # the counter's top, on the stem's edge
    f.set(0, 10, y=f.pt(0, 9)[1])                   # the bar's ends inside the stem
    for i in (3, 6, 15):
        f.curve(0, i)
    if master == "Regular":
        corner = f.mock.find(f.pt(0, 11) + (400, 50), "c")   # where the leg leaves the bar
        junction = f.mock.find(f.pt(0, 12) + (200, 60), "c")  # where the bowl meets the leg
        (cx, under), (jx, jy) = f.mock.at(corner), f.mock.at(junction)
        f.set(0, 11, y=under)
        f.set(0, 12, x=jx - 110, y=under)
        f.curve(0, 15, -1, stop=junction, end_dir=(1, 0))
        top = (f.pt(0, 9)[1] + under) / 2           # the leg's top: the bar's middle
        for foot, top_i, edge in ((0, 3, (cx, under)), (1, 2, (jx, jy))):
            a = f.mock.at(f.mock.find(f.pt(1, foot), "c"))
            f.set(1, foot, *a)
            f.set(1, top_i, x=a[0] + (edge[0] - a[0]) * (top - a[1]) / (edge[1] - a[1]), y=top)
    else:
        f.node(0, 12)
        f.set(0, 11, y=f.pt(0, 12)[1])
        f.curve(0, 15, -1)
        for i in range(4):
            f.node(1, i)
    return f


def fit_B(font, master):
    """Both bowls, the waist and the counters; the stem's edges stay."""
    f = Fit(font, master, "B")
    for i in (1, 4, 7, 8, 11, 14):
        f.node(0, i)
    for i in (1, 4, 8, 11):
        f.curve(0, i)
    for ci in (1, 2):
        for i in (2, 5, 8):
            f.node(ci, i)
        f.set(ci, 1, y=f.pt(ci, 2)[1])
        f.set(ci, 0, y=f.pt(ci, 8)[1])
        f.curve(ci, 2)
        f.curve(ci, 5)
    return f


def fit_G(font, master):
    """The bowl, the terminal and the bar. Ours keeps Inter's hidden spur: the bar's
    underside runs on past the inner curve into the bowl (point 7) and back up to the
    curve's end (8). In mockup-black.svg the inner curve ends inside the bar too, with the
    same spur; in mockup.svg it ends at the underside, so ours ends 16 units above it."""
    f = Fit(font, master, "G")
    for i in (3, 4, 5, 6, 11, 14, 17, 20, 21, 27):
        f.node(0, i)
    for i in (0, 24):
        f.node(0, i, keep_y=True)
    under = f.pt(0, 6)[1]
    inner = f.mock.find(f.pt(0, 8), "vc", within=150)   # the inner curve's end
    ix, iy = f.mock.at(inner)
    f.nodes[0, 8] = inner
    if iy - under < 10:
        f.set(0, 8, x=ix, y=under + 16)
        f.set(0, 7, x=ix + 40, y=under)
        f.curve(0, 11, -1, stop=inner, end_dir=(0, -1))
    else:
        f.set(0, 8, ix, iy)
        f.set(0, 7, *f.mock.at(f.mock.find((ix + 80, under), "c")))
        f.curve(0, 11, -1)
    for i in (0, 11, 14, 17, 21, 24, 27):
        f.curve(0, i)
    return f


def fit_c(font, master):
    """Both terminals and the bowl."""
    f = Fit(font, master, "c")
    for i in (3, 4, 7, 10, 13, 16, 17, 23):
        f.node(0, i)
    for i in (0, 20):
        f.node(0, i, keep_y=True)
    for i in (0, 4, 7, 10, 13, 17, 20, 23):
        f.curve(0, i)
    open_terminals(f)
    return f


def fit_e(font, master):
    """The lower terminal, the bowl, the bar and the counter. Inter's e runs the inner curve
    up into the bar and on up its left side (points 10-11), the counter's right side down
    into the bar (17) and back up to the bar's top (18); those stay inside the bar, and the
    curves either side are fitted to the mockup's outline below and above it."""
    f = Fit(font, master, "e")
    for i in (3, 4, 7, 14, 21, 22, 28):
        f.node(0, i)
    for i in (0, 25):
        f.node(0, i, keep_y=True)
    under = f.pt(0, 21)[1]
    top = f.mock.at(f.mock.find(f.pt(0, 19) + (80, 0), "c", within=200))[1]   # the bar's top-left
    f.set(0, 19, y=top)
    f.set(0, 20, y=under)
    lower = f.mock.path(f.nodes[0, 7], unit(f.pt(0, 8) - f.pt(0, 7)), lambda p: p[1] >= under - 0.5)[0]
    left = f.mock.path(f.nodes[0, 14], unit(f.pt(0, 13) - f.pt(0, 14)), lambda p: p[1] <= top + 0.5)[0]
    x = (lower[-1][0] + left[-1][0]) / 2            # the counter's left side, inside the bar
    f.set(0, 10, x=x, y=under + 15)
    f.set(0, 11, x=x, y=top - 15)
    f.curve(0, 7, stop=lambda p: p[1] >= under - 0.5, end_dir=(0, -1))
    f.curve(0, 14, -1, stop=lambda p: p[1] <= top + 0.5, end_dir=(0, 1))
    # the counter's right side runs on down into the bar along its tangent there
    right = f.mock.path(f.nodes[0, 14], (1, 0), lambda p: p[1] <= top + 0.5)
    (ex, ey), back = right[0][-1], right[2]
    f.set(0, 17, x=ex - back[0] / back[1] * 45, y=top - 45)
    f.set(0, 18, x=f.pt(0, 17)[0] + 90, y=top)
    f.curve(0, 14, stop=lambda p: p[1] <= top + 0.5, end_dir=back)
    for i in (0, 4, 22, 25, 28):
        f.curve(0, i)
    open_terminals(f)
    return f


def open_terminals(f):
    """Cut the fitted terminals back along their own curves to lines through APERTURE, at
    the mockup's angles."""
    contour = copy.deepcopy(f.glyph).contours[0]
    for (ci, i), q in f.new.items():
        contour.points[i].x, contour.points[i].y = float(q[0]), float(q[1])
    for (x, y), i in zip(APERTURE[f.master][f.name], reshape.terminals(contour)):
        u = unit(f.pt(0, i + 1) - f.pt(0, i))
        a = (f.left + x, y)
        reshape.cut(contour, i, a, (a[0] + 100 * u[0], a[1] + 100 * u[1]))
    for ci, i in f.new:
        f.new[ci, i] = np.array((contour.points[i].x, contour.points[i].y), float)


FITS = {"R": fit_R, "B": fit_B, "G": fit_G, "c": fit_c, "e": fit_e}


def fit_ogonek(font, e):
    """ę's ogonek (ogonek.e) ends in a corner (13) just inside e's lower terminal cut. It
    keeps its place across and along the cut as the cut turns; its handle (12) moves with it."""
    off = next(c for c in font["eogonek"].components if c.baseGlyph == "ogonek.e").transformation[4]
    pts = font["e"].contours[0].points
    old, new = [np.array((pts[i].x, pts[i].y), float) for i in (3, 4)], [e.new[0, 3], e.new[0, 4]]
    (u0, u1) = (unit(b - a) for a, b in (old, new))
    n0, n1 = np.array((-u0[1], u0[0])), np.array((-u1[1], u1[0]))
    ogonek = font["ogonek.e"]
    left = ogonek.getBounds(font).xMin
    corner, handle = (np.array((p.x + off, p.y), float) for p in ogonek.contours[0].points[13:11:-1])
    d = corner - old[0]
    moved = new[0] + np.dot(d, u0) * u1 + np.dot(d, n0) * n1
    return [(0, i, round(float(q[0]) - off - left, 1), round(float(q[1])))
            for i, q in ((12, handle + moved - corner), (13, moved))]


# --- Thin: construction moves measured on its guide -------------------------------------

def replay(layer, name):
    rec = DecomposingRecordingPen(layer)
    layer[name].draw(rec)
    return rec.replay


def bar_centre(guide, xs, near):
    """The middle of the guide's bar: the run nearest `near` on vertical lines at xs."""
    centres = []
    for x in xs:
        runs = joints.vertical_runs(guide, x)
        a, b = min(runs, key=lambda r: abs((r[0] + r[1]) / 2 - near))
        centres.append((a + b) / 2)
    return float(np.median(centres))


def scale_y(points, idx, fixed, old, new):
    """Scale the points' y about `fixed`, taking `old` to `new`."""
    for i in idx:
        points[i].y = round(fixed + (points[i].y - fixed) * (new - fixed) / (old - fixed))


def move_bar(points, bar, curves, delta):
    """Move the bar's points up by delta; each curve (end on the bar, handles, fixed end)
    is scaled to meet it."""
    for end, handles, fixed in curves:
        old = points[end].y
        scale_y(points, handles, points[fixed].y, old, old + delta)
    for i in bar:
        points[i].y = round(points[i].y + delta)


def thin_R(font, guide):
    """The bar centred on the guide's, the bowl the guide's width from the stem, the leg at
    the guide's slope from its foot to the bar's middle."""
    pts = font["R"].contours[0].points
    bar = bar_centre(guide, np.linspace(pts[1].x + 80, pts[9].x - 40, 5), (pts[9].y + pts[11].y) / 2)
    # as reshape.set_bowl moves P's: the inner and outer curves scaled from their tops
    scale_y(pts, range(2, 11), pts[2].y, pts[9].y, round(bar + THIN_STEM / 2))
    scale_y(pts, range(11, 20), pts[19].y, pts[11].y, round(bar - THIN_STEM / 2))
    stem, bowl = strokes.cut(guide, pts[15].y + strokes.EPS)[0], strokes.cut(guide, pts[15].y + strokes.EPS)[-1]
    want = (pts[0].x + pts[1].x) / 2 + (sum(bowl) - sum(stem)) / 2
    delta = want - (pts[6].x + pts[15].x) / 2
    for idx, extreme, x0 in (((4, 5, 6, 7, 8), 6, pts[3].x), ((13, 14, 15, 16, 17), 15, pts[18].x)):
        k = (pts[extreme].x + delta - x0) / (pts[extreme].x - x0)
        for i in idx:
            pts[i].x = round(x0 + (pts[i].x - x0) * k)
    ys = np.arange(40, 470, 30)
    legs = [strokes.cut(guide, y + strokes.EPS)[-1] for y in ys]
    slope = np.polyfit(ys, [(a + b) / 2 for a, b in legs], 1)[0]
    leg = font["R"].contours[1].points
    foot, half = (leg[0].x + leg[1].x) / 2, (leg[2].x - leg[3].x) / 2
    top = round(bar)
    leg[2].x, leg[3].x = round(foot + slope * top + half), round(foot + slope * top - half)
    leg[2].y = leg[3].y = top


def thin_B(font, guide):
    """The waist centred on the guide's."""
    outer, lower, upper = (c.points for c in font["B"].contours)
    delta = bar_centre(guide, np.linspace(lower[0].x + 80, lower[2].x - 40, 5),
                       (lower[1].y + upper[0].y) / 2) - (lower[1].y + upper[0].y) / 2
    scale_y(lower, range(9), lower[0].y, lower[1].y, lower[1].y + delta)
    scale_y(upper, range(9), upper[1].y, upper[0].y, upper[0].y + delta)
    scale_y(outer, range(1, 8), outer[0].y, outer[7].y, outer[7].y + delta)
    scale_y(outer, range(8, 15), outer[15].y, outer[8].y, outer[8].y + delta)


def thin_G(font, guide):
    """The bar centred on the guide's: with it the outer curve's end (3) and the inner
    curve's (8), whose curves are scaled to meet them."""
    pts = font["G"].contours[0].points
    mid = (pts[5].y + pts[6].y) / 2
    delta = bar_centre(guide, np.linspace(pts[5].x + 60, pts[8].x - 60, 5), mid) - mid
    move_bar(pts, (3, 4, 5, 6, 7, 8), ((3, (1, 2), 0), (8, (9, 10), 11)), delta)


def thin_e(font, guide):
    """The bar centred on the guide's, with the hidden points inside it."""
    pts = font["e"].contours[0].points
    mid = (pts[19].y + pts[20].y) / 2
    delta = bar_centre(guide, np.linspace(pts[10].x + 200, pts[17].x - 150, 5), mid) - mid
    move_bar(pts, (10, 11, 17, 18, 19, 20, 21, 22),
             ((22, (23, 24), 25), (17, (15, 16), 14), (11, (12, 13), 14), (10, (8, 9), 7)), delta)


# The points Thin's moves set: {glyph: {contour: points}}
THIN_MOVED = {"R": {0: range(2, 20), 1: (2, 3)}, "B": {0: range(1, 15), 1: range(9), 2: range(9)},
              "G": {0: range(1, 11)}, "e": {0: (*range(8, 14), *range(15, 25))}}


def fit_thin(font):
    """Thin's rows: the points the construction moves set, made on copies of the glyphs."""
    bg = font.layers["public.background"]
    work = {name: copy.deepcopy(font[name]) for name in THIN_MOVED}
    thin_R(work, replay(bg, "R"))
    thin_B(work, replay(bg, "B"))
    thin_G(work, replay(bg, "G"))
    thin_e(work, replay(bg, "e"))
    table = {}
    for name, moved in THIN_MOVED.items():
        left = font[name].getBounds(font).xMin
        table[name] = [(ci, i, round(q.x - left, 1), q.y) for ci, idx in moved.items()
                       for i, q in ((i, work[name].contours[ci].points[i]) for i in idx)]
    return table


def fit(src):
    fonts = {m: ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{m}.ufo")) for m in ("Thin", "Regular", "Black")}
    fits = {m: {name: FITS[name](fonts[m], m) for name in GLYPHS} for m in ("Regular", "Black")}
    for m, by_name in fits.items():
        for name, f in by_name.items():
            print(f"  {m} {name}: worst handle fit {f.worst:.1f}", file=sys.stderr)
    table = {"Thin": fit_thin(fonts["Thin"])}
    for m in ("Regular", "Black"):
        table[m] = {name: f.rows() for name, f in fits[m].items()}
        table[m]["ogonek.e"] = fit_ogonek(fonts[m], fits[m]["e"])
    return table


def show(table):
    """POINTS as Python, wrapped like the other tables."""
    lines = ["POINTS = {"]
    for m, by_name in table.items():
        lines.append(f'    "{m}": {{')
        for name, rows in by_name.items():
            cells, line = [f"({ci}, {i}, {x}, {y})" for ci, i, x, y in rows], f'        "{name}": ['
            for k, cell in enumerate(cells):
                piece = cell + (", " if k < len(cells) - 1 else "],")
                if len(line) + len(piece) > 95:
                    lines.append(line.rstrip())
                    line = "            "
                line += piece
            lines.append(line if cells else line + "],")
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fit"]:
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        print(show(fit(sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "source"))))
    else:
        main(sys.argv[1:])
