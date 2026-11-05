"""Shorten the quote wedges, and so the comma, to other text faces' median length.

The quotes were Inter's long wedges (Inter's lengths, a little heavier). Against 20 sans
serifs (Inter, Nimbus Sans as Helvetica, Plus Jakarta Sans, Geist, Roboto, IBM Plex Sans,
DM Sans ...) scaled to one cap height, at 400 our ’ was longer than in 15 of them (569
units at our cap height, the median 506) and ended 155 below the x-height (the median
65), and the comma, ’ moved down, reached 88% of the way to p's descender (the median
70%; only Source Sans 3's hangs lower), and at 900 it ended 9 units below p (-427, p
-418). Their heads were no thicker than the others' (1.08 times the stem at 400, the
median 1.17), so only the length changes. The user chose "-15%" (Regular and Black 15%
shorter, Thin 8%, since our Thin was nearer the others' Thin) over -10% and -20%: at 400 it
puts both lengths at the median, and at 100 and 900 near it.

quoteleft, quoteright and quotesingle are each one 4-point wedge from the cap height down.
The two points of its bottom edge move up to BOTTOM, keeping the edge's width, and their
middle slides along the line from the top edge's middle, so the wedge keeps its head, its
tail and its lean. The comma, quotesinglbase, quotedblbase, the double quotes, quotedbl,
quotereversed, the semicolon's comma and comma.tf, .numr and .dnom are built on these, so
they follow; the comma's head stays at its height. Points only move, so the masters stay
compatible.

Moving the foot up along the lean moves its outer corner about 19 units right in Regular,
so the quotes' sides change: tools/spacing.py's SIDES hold the sides refitted for these
shapes (spacing.py --fit), and run on its own this runs spacing.py after (which runs
accents.py, stacked.py, tabular.py, kerning.py and kern.py). Run it before tools/spacing.py.
Running it again changes nothing.

Usage: python tools/quotes.py source/PlaceholderSans-*.ufo
"""

import os
import re
import sys

import ufoLib2
from fontTools.misc.roundTools import otRound
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GLYPHS = ("quoteleft", "quoteright", "quotesingle")

# Where each wedge ends, per master (it was 1040 / 909 / 823; the x-height is 1076).
BOTTOM = {"Thin": 1076, "Regular": 996, "Black": 923}


def shorten(glyph, bottom):
    """Move the wedge's bottom edge to `bottom` along its lean; True if anything moved."""
    (contour,) = glyph.contours
    points = contour.points
    top, low = max(p.y for p in points), min(p.y for p in points)
    upper = [p for p in points if p.y == top]
    lower = [p for p in points if p.y == low]
    assert len(points) == 4 and len(upper) == 2 and len(lower) == 2, glyph.name
    if low == bottom:
        return False
    mid_top = sum(p.x for p in upper) / 2
    mid_low = sum(p.x for p in lower) / 2
    mid = mid_top + (mid_low - mid_top) * (top - bottom) / (top - low)
    for p in lower:
        p.x, p.y = otRound(mid + p.x - mid_low), bottom
    return True


def apply(ufo, master):
    """Shorten the quote wedges in `ufo`; returns the glyphs that changed."""
    if master not in BOTTOM:
        return []
    return [name for name in GLYPHS if name in ufo and shorten(ufo[name], BOTTOM[master])]


def main(paths):
    import spacing
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {', '.join(changed) or 'nothing'} shortened ({master})")
    # What follows in tools/to_ufo.py: the quotes' sides, then the composites and kerning.
    spacing.main(paths)


if __name__ == "__main__":
    main(sys.argv[1:])
