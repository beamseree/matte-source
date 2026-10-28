"""Convert the derived Glyphs source to designspace + UFO (the format Fontra edits),
and put mockup letters into masters' background layers as tracing guides
(an SVG of outlined text, or a screenshot traced at 50% coverage). Inter's own backup and background layers are dropped: they no
longer match the derived outlines and would only clutter the editor. Letters that
tools/straighten.py, tools/redraw.py, tools/reshape.py and tools/refit.py fix are redrawn in
every master, tools/joints.py thickens the joints of arches and bowls in Regular and Black, and
tools/kern.py keeps t's and f's crossbars apart.

Each SVG letter is scaled to font units (the "l" and capitals are 1490 units
tall), sat on the baseline, and centred on the glyph's own outline.

Usage: python tools/to_ufo.py <in.glyphspackage> <out.designspace>
           [--guides Regular=reference/mockup.svg] [--guides Thin=reference/mockup-thin.webp]
           [--only Thin]    # write just these masters' UFOs, leaving the others as they are
"""

import argparse
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
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgtarget  # noqa: E402
import joints  # noqa: E402
import kern  # noqa: E402
import redraw  # noqa: E402
import refit  # noqa: E402
import reshape  # noqa: E402
import straighten  # noqa: E402

BACKGROUND = "public.background"
MASTERS = {100: "Thin", 400: "Regular", 900: "Black"}
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


def img_letters(path):
    """Like svg_letters, for a screenshot: each letter's ink traced into polygons."""
    import numpy as np
    from PIL import Image
    from skimage.measure import approximate_polygon, find_contours

    im = np.asarray(Image.open(path).convert("L")).astype(float)
    bg = np.median(im)
    cov = np.clip((im - bg) / (im.max() - bg), 0, 1)
    out = {}
    for (y0, y1), text in zip([imgtarget.bands(cov)[0], imgtarget.bands(cov)[-1]], imgtarget.LINES):
        ls = imgtarget.letters(cov, y0, y1, text)
        l = ls[text.lower().index("l")]
        baseline, scale = l["bottom"], 1490 / (l["bottom"] - l["top"])
        for d in ls:
            if d["char"] in out:
                continue
            rec = RecordingPen()
            for c in find_contours(np.pad(d["part"], 1), 0.5, positive_orientation="high"):
                c = approximate_polygon(c, tolerance=0.15)
                # contours run through pixel centres: +0.5 to edge coordinates, -1 for the pad
                pts = [(float(x - 0.5), float(y - 0.5 + d["off"])) for y, x in c[:-1]]
                rec.moveTo(pts[0])
                for pt in pts[1:]:
                    rec.lineTo(pt)
                rec.closePath()
            out[d["char"]] = (rec, (d["x0"], d["top"], d["x1"], d["bottom"]), baseline, scale)
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
        # SVG/image y points down: flip, which also reverses contour direction; undo that.
        # Round to whole units: UFO files only take plain numbers.
        pen = RoundingPen(ReverseContourPen(bg.getPen()))
        rec.replay(TransformPen(pen, (s, 0, 0, -s, float(dx), float(s * baseline))))


# Overlapping-contour glyphs whose open corners erase differently once the masters'
# stem weights diverge, which breaks interpolation. Keeping their corners is harmless.
OPEN_CORNER_EXCLUDE = ["uni0238", "uni0239"]


def exclude_from_open_corner_erasing(lib):
    for f in lib.get("com.github.googlei18n.ufo2ft.filters", []):
        if f.get("name") == "eraseOpenCorners":
            f["exclude"] = sorted(set(f.get("exclude", [])) | set(OPEN_CORNER_EXCLUDE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--guides", action="append", default=[], metavar="MASTER=PATH")
    ap.add_argument("--only", action="append", default=[], metavar="MASTER")
    args = ap.parse_args()
    src, dst = args.src, args.dst
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
        exclude_from_open_corner_erasing(source.font.lib)
        straighten.apply(source.font, MASTERS[source.location["Weight"]])
        redraw.apply(source.font, MASTERS[source.location["Weight"]])
        reshape.apply(source.font, MASTERS[source.location["Weight"]])
        refit.apply(source.font, MASTERS[source.location["Weight"]])
        joints.apply(source.font, MASTERS[source.location["Weight"]])
        kern.apply(source.font, MASTERS[source.location["Weight"]])
    by_name = {MASTERS[s.location["Weight"]]: s for s in ds.sources}
    for spec in args.guides:
        name, path = spec.split("=", 1)
        letters = svg_letters(path) if path.endswith(".svg") else img_letters(path)
        add_guides(by_name[name].font, letters)
    written = []
    for name, source in by_name.items():
        if args.only and name not in args.only:
            continue
        path = os.path.join(out_dir, source.filename)
        if os.path.exists(path):
            shutil.rmtree(path)
        source.font.save(path)
        written.append(name)
    if not args.only or not os.path.exists(dst):
        ds.write(dst)
    print(f"saved {', '.join(written)} to {out_dir}")


if __name__ == "__main__":
    main()
