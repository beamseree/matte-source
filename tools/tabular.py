"""Give the tabular glyphs one width per master again, with their ink placed as in Inter.

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

_inter = {}


def tabular(name):
    return "tf" in name.split(".")[1:]


def inter(master):
    """{name: (width, ink centre minus half the width, or None)} for Inter's tabular glyphs."""
    if not _inter:
        font = glyphsLib.GSFont(INTER)
        for m in font.masters:
            if m.axes[0] != 14:
                continue
            layers = {g.name: g.layers[m.id] for g in font.glyphs}
            out = _inter[m.name] = {}
            for name, layer in layers.items():
                if tabular(name):
                    rec = DecomposingRecordingPen(layers)
                    layer.draw(rec)
                    bp = BoundsPen(None)
                    rec.replay(bp)
                    b = bp.bounds
                    out[name] = (layer.width, b and (b[0] + b[2]) / 2 - layer.width / 2)
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
    """Set the tabular glyphs' widths and places in `ufo`; returns the glyphs that changed."""
    ref = inter(master)
    widths = WIDTHS.get(master, {})
    changed = []
    # A component's shift moves the glyphs built on it, so place it before measuring them.
    for name in bases_first(ufo, [n for n in ref if n in ufo]):
        glyph = ufo[name]
        width, offset = ref[name]
        width = widths.get(width, width)
        b = glyph.getBounds(ufo)
        dx = round(width / 2 + offset - (b.xMin + b.xMax) / 2) if b and offset is not None else 0
        if dx or glyph.width != width:
            shift(glyph, dx)
            glyph.width = width
            changed.append(name)
    if ufo["figurespace"].width != ufo["zero.tf"].width:
        ufo["figurespace"].width = ufo["zero.tf"].width
        changed.append("figurespace")
    return changed


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        widths = sorted({ufo[n].width for n in changed})
        print(f"{path}: {len(changed)} tabular glyphs set ({master}; widths {widths})")


if __name__ == "__main__":
    main(sys.argv[1:])
