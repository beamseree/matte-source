"""Convert the derived Glyphs source to designspace + UFO (the format Fontra edits),
and put the mockup SVG letters into the Regular master's background layer as
tracing guides. Inter's own backup and background layers are dropped: they no
longer match the derived outlines and would only clutter the editor.

Each SVG letter is scaled to font units (the "l" and capitals are 1490 units
tall), sat on the baseline, and centred on the glyph's own outline.

Usage: python tools/to_ufo.py <in.glyphspackage> <out.designspace> [mockup.svg]
"""

import logging
import os
import re
import shutil
import sys

import glyphsLib
import ufoLib2
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

BACKGROUND = "public.background"
LINES = [("quickbrownfoxjumpsoverthelazydog", lambda b: b[3] < 50),
         ("QUICKBROWNFOXJUMPSOVERTHELAZYDOG", lambda b: b[1] >= 50)]


def svg_letters(path):
    """{char: (RecordingPen, bounds, baseline, scale)} for the first occurrence of each letter."""
    paths = []
    for d in re.findall(r'<path d="([^"]+)"', open(path).read()):
        rec = RecordingPen()
        parse_path(d, rec)
        bp = BoundsPen(None)
        rec.replay(bp)
        paths.append((bp.bounds, rec))
    out = {}
    for text, in_line in LINES:
        line = sorted((p for p in paths if in_line(p[0])), key=lambda p: p[0][0])
        assert len(line) == len(text), (text, len(line))
        l_box = line[text.lower().index("l")][0]
        baseline, scale = l_box[3], 1490 / (l_box[3] - l_box[1])
        for c, (bounds, rec) in zip(text, line):
            out.setdefault(c, (rec, bounds, baseline, scale))
    return out


def add_guides(ufo, letters):
    layer = ufo.layers.get(BACKGROUND) or ufo.layers.newLayer(BACKGROUND)
    for name, (rec, (x0, _, x1, _), baseline, s) in letters.items():
        if name not in ufo:
            continue
        glyph = ufo[name]
        bx0, _, bx1, _ = glyph.getBounds(ufo)
        dx = (bx0 + bx1) / 2 - s * (x0 + x1) / 2
        bg = layer[name] if name in layer else layer.newGlyph(name)
        bg.clearContours()
        bg.clearComponents()
        bg.width = glyph.width
        # SVG y points down: flip, which also reverses contour direction; undo that.
        rec.replay(TransformPen(ReverseContourPen(bg.getPen()), (s, 0, 0, -s, dx, s * baseline)))


def main(src, dst, svg=None):
    logging.getLogger("glyphsLib").setLevel(logging.ERROR)
    font = glyphsLib.GSFont(src)
    ds = glyphsLib.to_designspace(
        font, ufo_module=ufoLib2, expand_includes=True, write_skipexportglyphs=True
    )
    out_dir = os.path.dirname(os.path.abspath(dst))
    for source in ds.sources:
        for name in list(source.font.layers.keys()):
            if name != source.font.layers.defaultLayer.name:
                del source.font.layers[name]
    regular = next(s for s in ds.sources if s.location.get("Weight") == 400)
    if svg:
        add_guides(regular.font, svg_letters(svg))
    for source in ds.sources:
        path = os.path.join(out_dir, source.filename)
        if os.path.exists(path):
            shutil.rmtree(path)
        source.font.save(path)
    ds.write(dst)
    print(f"saved {dst} ({len(ds.sources)} masters)")


if __name__ == "__main__":
    main(*sys.argv[1:4])
