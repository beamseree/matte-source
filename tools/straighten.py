"""Rebuild x, X, z and Z with straight strokes, at the mockups' diagonal weights.

Inter draws x and X as one overlapping contour whose inner edges curve into the
crossing, and Z with curved joints where the diagonal meets the bars; it also keeps
the diagonals of x, z and Z lighter than the stems. The mockups use straight lines and
diagonals about as heavy as the stems. So:

- x and X become two straight crossing strokes (12 points), keeping the four outer
  foot edges; each stroke's horizontal width is set from DIAGONALS.
- z and Z become two bars joined by a straight diagonal (10 points), keeping the bars;
  the diagonal's horizontal width is set from DIAGONALS.

Strokes thicken inward, so outer edges, advance widths and spacing don't change. The
point structure is the same in every master, so they stay compatible. Masters missing
from DIAGONALS (Thin) keep their current stroke widths. Running it again changes nothing.

Usage: python tools/straighten.py source/PlaceholderSans-*.ufo   # rewrites x, X, z, Z
"""

import re
import sys

import ufoLib2
from fontTools.ufoLib.glifLib import GlyphSet

GLYPHS = ("x", "X", "z", "Z")

# Horizontal widths of the diagonal strokes measured on the mockups (font units):
# x/X as ("/" stroke, "\" stroke), z/Z as the single diagonal.
DIAGONALS = {
    "Regular": {"x": (229, 243.5), "X": (244, 255), "z": 255, "Z": 261},   # mockup.svg
    "Black": {"x": (411, 428), "X": (441, 452), "z": 471, "Z": 478},       # mockup-black.webp
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


def shifted(line, dx):
    return [(x + dx, y) for x, y in line]


def on_curve(glyph):
    return [(p.x, p.y) for c in glyph.contours for p in c.points if p.segmentType]


def redraw(glyph, poly):
    glyph.clearContours()
    pen = glyph.getPointPen()
    pen.beginPath()
    for x, y in poly:
        pen.addPoint((round(x), round(y)), "line")
    pen.endPath()


def cross(glyph, widths=None):
    """x / X: two straight crossing strokes between the four feet."""
    pts = on_curve(glyph)
    top = max(y for _, y in pts)
    bottom = sorted(x for x, y in pts if y == 0)
    upper = sorted(x for x, y in pts if y == top)
    if len(bottom) != 4 or len(upper) != 4:
        raise ValueError(f"{glyph.name}: expected four feet")
    bl0, bl1, br0, br1 = bottom
    tl0, tl1, tr0, tr1 = upper
    if widths:  # thicken inward from the outer edges
        slash, back = widths
        bl1, tr0 = bl0 + slash, tr1 - slash
        tl1, br0 = tl0 + back, br1 - back
    bl0, bl1, br0, br1 = [(x, 0) for x in (bl0, bl1, br0, br1)]
    tl0, tl1, tr0, tr1 = [(x, top) for x in (tl0, tl1, tr0, tr1)]
    # "/" runs bottom-left to top-right, "\" top-left to bottom-right
    redraw(glyph, [
        bl0, bl1, intersect(bl1, tr1, tl0, br0),   # bottom notch
        br0, br1, intersect(bl1, tr1, tl1, br1),   # right notch
        tr1, tr0, intersect(bl0, tr0, tl1, br1),   # top notch
        tl1, tl0, intersect(bl0, tr0, tl0, br0),   # left notch
    ])


def zed(glyph, width=None):
    """z / Z: bottom bar, straight diagonal, top bar."""
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
    if width:
        grow = (width - (x_at(right, mid) - x_at(left, mid))) / 2
        left, right = shifted(left, -grow), shifted(right, grow)
    redraw(glyph, [
        (bl, 0), (br, 0), (br, bb),
        (x_at(right, bb), bb), (tr, x_at([(y, x) for x, y in right], tr)),
        (tr, top), (tl, top), (tl, tb),
        (x_at(left, tb), tb), (bl, x_at([(y, x) for x, y in left], bl)),
    ])


def apply(ufo, master):
    widths = DIAGONALS.get(master, {})
    cross(ufo["x"], widths.get("x"))
    cross(ufo["X"], widths.get("X"))
    zed(ufo["z"], widths.get("z"))
    zed(ufo["Z"], widths.get("Z"))


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
