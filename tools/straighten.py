"""Rebuild x, X, z and Z with straight strokes, at the mockups' diagonal weights.

Inter draws x and X as one overlapping contour whose inner edges curve into the
crossing, and Z with curved joints where the diagonal meets the bars; it also keeps
the diagonals of x, z and Z lighter than the stems. The mockups use straight lines and
diagonals about as heavy as the stems. So:

- x and X become two crossing strokes (12 points: 8 at the feet, 4 where the strokes
  cross). In the mockups the strokes narrow toward the crossing and the top is a little
  narrower than the bottom, so x and X take the mockup's points from CROSSES, placed in
  proportion across our bottom feet (which set the letter's width), with each foot at
  the mockup's width. Thin keeps its own four outer foot edges and straight strokes.
- z and Z become two bars joined by a straight diagonal (10 points). The bottom bar
  spans the letter, and the top bar is inset from its ends by TOP_BARS, as in the
  mockups. The bars' thickness and the diagonal's edges come from ZEDS, in proportion
  across the bottom bar (the mockups' small steps where the diagonal meets a bar are
  left out).

The letters' widths don't change, so advance widths and spacing don't either. The point
structure is the same in every master, so they stay compatible. Masters missing from
CROSSES and ZEDS (Thin) keep their own strokes, with x and X straight. Running it again
changes nothing.

Usage: python tools/straighten.py source/PlaceholderSans-*.ufo   # rewrites x, X, z, Z
"""

import re
import sys

import ufoLib2
from fontTools.ufoLib.glifLib import GlyphSet

GLYPHS = ("x", "X", "z", "Z")

# x and X in mockup.svg (Regular) and mockup-black.svg (Black), in font units from the
# letter's left edge: the feet's x at the baseline (bl0, bl1, br0, br1) and at the top
# (tl0, tl1, tr0, tr1), the crossing points (bottom, right, top, left), and the height.
CROSSES = {
    "Regular": {"x": ((0.0, 235.9, 850.5, 1094.7), (26.9, 271.1, 829.8, 1061.6),
                      ((536.0, 424.3), (668.4, 562.9), (552.5, 699.5), (418.0, 560.8)), 1076.1),
                "X": ((0.0, 248.4, 1181.7, 1436.2), (41.4, 295.9, 1150.6, 1394.8),
                      ((705.7, 622.9), (850.6, 765.7), (730.5, 920.9), (585.6, 780.2)), 1490.0)},
    "Black": {"x": ((0.0, 436.7, 831.9, 1274.8), (45.5, 494.6, 794.7, 1223.1),
                    ((618.7, 324.9), (867.1, 560.8), (658.1, 827.8), (407.7, 581.5)), 1076.1),
              "X": ((0.0, 480.1, 1119.6, 1574.9), (43.4, 504.9, 1078.2, 1535.5),
                    ((771.9, 482.2), (1026.4, 761.6), (811.2, 1061.6), (552.5, 784.3)), 1490.0)},
}

# z and Z in mockup.svg (Regular) and mockup-black.svg (Black): the letter's width (the
# bottom bar) and height, the bars' thickness, and the diagonal's left and right edges as
# (x at the baseline, x at the top), in font units from the letter's left edge.
ZEDS = {
    "Regular": {"z": dict(width=962.3, height=1076.1, bar=169.7, left=(-182.8, 861.6), right=(68.6, 1119.2)),
                "Z": dict(width=1278.9, height=1490.0, bar=186.3, left=(-167.3, 1156.2), right=(93.9, 1415.6))},
    "Black": {"z": dict(width=1036.8, height=1076.1, bar=269.1, left=(-285.1, 855.3), right=(198.2, 1314.7)),
              "Z": dict(width=1287.2, height=1490.0, bar=327.0, left=(-311.9, 1082.8), right=(178.0, 1563.3))},
}

# How far the top bar's ends sit in from the bottom bar's (left, right). Thin's are
# measured on mockup-thin.webp with tools/strokes.py (about +-5 units): thinning strokes
# evenly moves both bars' ends by the same amount, so the insets hold at Thin's weight.
TOP_BARS = {
    "Thin": {"z": (57.1, 25.5), "Z": (58.3, 40.0)},
    "Regular": {"z": (41.4, 29.0), "Z": (55.9, 41.4)},   # mockup.svg
    "Black": {"z": (22.7, 26.9), "Z": (55.9, 41.3)},     # mockup-black.svg
}


def intersect(p1, p2, p3, p4):
    """Intersection of line p1-p2 with line p3-p4."""
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p1, p2, p3, p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    a, b = x1 * y2 - y1 * x2, x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / d, (a * (y3 - y4) - (y1 - y2) * b) / d)


def x_at(line, y):
    (x1, y1), (x2, y2) = line
    return x1 + (y - y1) * (x2 - x1) / (y2 - y1)


def on_curve(glyph):
    return [(p.x, p.y) for c in glyph.contours for p in c.points if p.segmentType]


def redraw(glyph, poly):
    glyph.clearContours()
    pen = glyph.getPointPen()
    pen.beginPath()
    for x, y in poly:
        pen.addPoint((round(x), round(y)), "line")
    pen.endPath()


def cross(glyph, shape=None):
    """x / X: two crossing strokes between the four feet, straight or from a mockup."""
    pts = on_curve(glyph)
    top = max(y for _, y in pts)
    bottom = sorted(x for x, y in pts if y == 0)
    upper = sorted(x for x, y in pts if y == top)
    if len(bottom) != 4 or len(upper) != 4:
        raise ValueError(f"{glyph.name}: expected four feet")
    bl0, bl1, br0, br1 = bottom
    tl0, tl1, tr0, tr1 = upper
    if shape:  # the mockup, in proportion across our bottom feet (the letter's width)
        mb, mt, crossing, height = shape
        place = lambda x, y: (bl0 + (x - mb[0]) * (br1 - bl0) / (mb[3] - mb[0]), y * top / height)
        tl0, tr1 = place(mt[0], 0)[0], place(mt[3], 0)[0]
        bl1, br0 = bl0 + mb[1] - mb[0], br1 - (mb[3] - mb[2])   # foot widths as measured
        tl1, tr0 = tl0 + mt[1] - mt[0], tr1 - (mt[3] - mt[2])
        bottom_n, right_n, top_n, left_n = (place(*p) for p in crossing)
    bl0, bl1, br0, br1 = [(x, 0) for x in (bl0, bl1, br0, br1)]
    tl0, tl1, tr0, tr1 = [(x, top) for x in (tl0, tl1, tr0, tr1)]
    if not shape:
        # "/" runs bottom-left to top-right, "\" top-left to bottom-right
        bottom_n, right_n = intersect(bl1, tr1, tl0, br0), intersect(bl1, tr1, tl1, br1)
        top_n, left_n = intersect(bl0, tr0, tl1, br1), intersect(bl0, tr0, tl0, br0)
    redraw(glyph, [bl0, bl1, bottom_n, br0, br1, right_n, tr1, tr0, top_n, tl1, tl0, left_n])


def zed(glyph, shape=None, insets=None):
    """z / Z: bottom bar, straight diagonal, top bar; bars and diagonal from a mockup."""
    pts = on_curve(glyph)
    top = max(y for _, y in pts)
    bl = min(x for x, y in pts if y == 0)
    br = max(x for x, y in pts if y == 0)
    tl = min(x for x, y in pts if y == top)
    tr = max(x for x, y in pts if y == top)
    bb = min(y for x, y in pts if x == br and y > 0)      # top of the bottom bar
    tb = max(y for x, y in pts if x == tl and y < top)    # underside of the top bar
    # the diagonal's two edges: the two longest segments that are neither flat nor upright
    segs = []
    for c in glyph.contours:
        on = [(p.x, p.y) for p in c.points if p.segmentType]
        for a, b in zip(on, on[1:] + on[:1]):
            if abs(a[0] - b[0]) > 100 and abs(a[1] - b[1]) > 100:
                segs.append(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2, [a, b]))
    segs.sort(reverse=True)
    if len(segs) < 2:
        raise ValueError(f"{glyph.name}: diagonal not found")
    mid = (bb + tb) / 2
    left, right = sorted((segs[0][1], segs[1][1]), key=lambda line: x_at(line, mid))
    bl, br = min(bl, tl), max(br, tr)   # the bottom bar spans the letter
    if shape:  # the mockup's bars and diagonal, in proportion across the bottom bar
        s, v = (br - bl) / shape["width"], top / shape["height"]
        bb, tb = round(shape["bar"] * v), round(top - shape["bar"] * v)
        left, right = ([(bl + s * x0, 0), (bl + s * x1, top)] for x0, x1 in (shape["left"], shape["right"]))
    if insets:  # the top bar sits in from the bottom bar's ends
        tl, tr = round(bl + insets[0]), round(br - insets[1])
    redraw(glyph, [
        (bl, 0), (br, 0), (br, bb),
        (x_at(right, bb), bb), (tr, x_at([(y, x) for x, y in right], tr)),
        (tr, top), (tl, top), (tl, tb),
        (x_at(left, tb), tb), (bl, x_at([(y, x) for x, y in left], bl)),
    ])


def apply(ufo, master):
    crosses, zeds, bars = CROSSES.get(master, {}), ZEDS.get(master, {}), TOP_BARS.get(master, {})
    cross(ufo["x"], crosses.get("x"))
    cross(ufo["X"], crosses.get("X"))
    zed(ufo["z"], zeds.get("z"), bars.get("z"))
    zed(ufo["Z"], zeds.get("Z"), bars.get("Z"))


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in GLYPHS:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {', '.join(GLYPHS)} rebuilt ({master})")


if __name__ == "__main__":
    main(sys.argv[1:])
