"""Give the tabular and fixed-width glyphs their widths, with their ink placed as in Inter.

Inter builds its tabular glyphs (zero.tf to nine.tf and their alternates, period.tf,
colon.tf, hyphen.tf, the brackets, the maths signs) mostly from the proportional ones as
components, and tools/derive.py's composite branch gave each its proportional glyph's width
change, so they stopped sharing a width: the figures came out 1292-1338 units wide, where
Inter's are one width per master, and figurespace 1174-1624. Every glyph whose name has a
"tf" suffix part takes its width from Inter's source (the text-size masters), or from
WIDTHS where ours differs, so glyphs that shared a width in Inter share one again, and
figurespace takes the figures' width. Each is moved whole (contours, component offsets and
anchors by the same dx) so that its ink centre sits as far from the advance's centre as
Inter's did, which keeps Inter's off-centre 1. No points move relative to each other.

Glyphs whose width is the same in all of Inter's masters are fixed-width there (the arrows,
the squares, stars and hearts, the circled and squared forms, the em space and its
fractions, .notdef), but derive.py gave them sidebearing changes, so they narrowed toward
Regular and widened toward Black (the em space 1884 / 1810 / 2519, the arrows 1909 / 1889 /
2000): they take Inter's width the same way. The quads are the en and em spaces (U+2000 and
U+2001 are U+2002 and U+2003 by Unicode; Inter's change with weight), the medium
mathematical space is 4/18 em, the punctuation space is the period's width, and the thin,
narrow no-break and hair spaces are the word space's fraction Inter has in each master.
Running it again changes nothing.

Usage: python tools/tabular.py source/PlaceholderSans-*.ufo
"""

import os
import re
import sys

import glyphsLib
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ufoLib.glifLib import GlyphSet

INTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                     "vendor/inter/src/Inter-Roman.glyphspackage")

# Tabular widths where ours differ from Inter's, per master, as {Inter's width: ours}.
# Black's figures are wider than Inter's: at Inter's 1320 the 4 had 17 units a side and 44
# a 34-unit gap (proportional 169). The user chose 1400 over 1320 and 1455 (the 4 with its
# own sidebearings), in real text.
WIDTHS = {"Black": {1320: 1400}}
QUADS = {"enquad": "enspace", "emquad": "emspace"}
MATH_SPACE = ("mediumspace-math", 4 / 18)
WORD_FRACTIONS = ("thinspace", "narrownbspace", "hairspace")

_inter = {}


def tabular(name):
    return "tf" in name.split(".")[1:]


def inter(master):
    """({name: (width, ink centre minus half the width, or None)} for Inter's tabular glyphs
    and the glyphs with one width in all its masters, {space: its fraction of the word
    space}) for a master."""
    if not _inter:
        font = glyphsLib.GSFont(INTER)
        masters = [m for m in font.masters if m.axes[0] == 14]
        constant = {g.name for g in font.glyphs
                    if len({g.layers[m.id].width for m in masters}) == 1 and g.layers[masters[0].id].width}
        for m in masters:
            layers = {g.name: g.layers[m.id] for g in font.glyphs}
            out = {}
            for name, layer in layers.items():
                if tabular(name) or name in constant:
                    rec = DecomposingRecordingPen(layers)
                    layer.draw(rec)
                    bp = BoundsPen(None)
                    rec.replay(bp)
                    b = bp.bounds
                    out[name] = (layer.width, b and (b[0] + b[2]) / 2 - layer.width / 2)
            fractions = {n: layers[n].width / layers["space"].width for n in WORD_FRACTIONS}
            _inter[m.name] = out, fractions
    return _inter[master]


def shift(glyph, dx):
    for contour in glyph.contours:
        for p in contour.points:
            p.x += dx
    for c in glyph.components:
        t = c.transformation
        c.transformation = Transform(t[0], t[1], t[2], t[3], t[4] + dx, t[5])
    for a in glyph.anchors:
        a.x += dx


def bases_first(ufo, names):
    out = []
    def visit(name):
        if name not in out:
            for c in ufo[name].components:
                if c.baseGlyph in names:
                    visit(c.baseGlyph)
            out.append(name)
    for name in sorted(names):
        visit(name)
    return out


def apply(ufo, master):
    """Set the tabular and fixed-width glyphs' widths and places in `ufo`; returns the glyphs
    that changed."""
    ref, fractions = inter(master)
    widths = WIDTHS.get(master, {})
    changed = []
    # A component's shift moves the glyphs built on it, so place it before measuring them.
    # Glyphs we zeroed (combining marks) stay zero.
    for name in bases_first(ufo, [n for n in ref if n in ufo and ufo[n].width]):
        glyph = ufo[name]
        width, offset = ref[name]
        if tabular(name):
            width = widths.get(width, width)
        b = glyph.getBounds(ufo)
        dx = round(width / 2 + offset - (b.xMin + b.xMax) / 2) if b and offset is not None else 0
        if dx or glyph.width != width:
            shift(glyph, dx)
            glyph.width = width
            changed.append(name)
    fixed = {"figurespace": ufo["zero.tf"].width, "punctuationspace": ufo["period"].width,
             MATH_SPACE[0]: round(ufo.info.unitsPerEm * MATH_SPACE[1])}
    fixed.update({quad: ufo[space].width for quad, space in QUADS.items()})
    fixed.update({n: round(ufo["space"].width * fractions[n]) for n in WORD_FRACTIONS})
    for name, width in fixed.items():
        if ufo[name].width != width:
            ufo[name].width = width
            changed.append(name)
    return changed


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        widths = sorted({ufo[n].width for n in changed if tabular(n)})
        print(f"{path}: {len(changed)} tabular and fixed-width glyphs set ({master}; tabular widths {widths})")


if __name__ == "__main__":
    main(sys.argv[1:])
