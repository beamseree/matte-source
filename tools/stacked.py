"""Put the parts of stacked composites back where Inter has them.

tools/derive.py's composite branch moved each component right by the width changes of
the components before it, and widened the glyph by all of them. That is right for
components side by side (the ellipsis), but not for components drawn over each other: the
semicolon's dot sat 31 and 24 units left and 7 right (Thin / Regular / Black) of where
Inter puts it over the comma, the circled and squared letters, figures and signs sat off
centre in their circles and squares, and those glyphs' widths had drifted from their
circle's or square's by up to 262 units.

For each glyph in STACKED (ǂ's crossbars had moved 52 and 83 units apart) and every
.circled and .squared glyph, the first component
stays, and each other part (a component, or the glyph's own contours together) moves so
that its ink centre sits as far from the first component's as in Inter's text-size
masters. The width becomes the first component's plus Inter's difference. Anchors that
came from a moved component move with it. Glyphs built on one of these from that glyph
alone follow its width, and a mirrored one moves with it. Parts only move, so the masters
stay compatible. tools/dots.py centres the colon's dots, and letters with accents follow
their anchors, so neither is here.

Run it after tools/dots.py and before tools/tabular.py, which centres semicolon.tf,
semicolon.tf.ss07 and colon.tf.ss07 on the result; run on its own, it runs tabular.py
after. Running it again changes nothing.

Usage: python tools/stacked.py source/PlaceholderSans-*.ufo
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tabular  # noqa: E402

STACKED = ["semicolon", "semicolon.ss03", "semicolon.ss07", "colon.ss07", "uni2051",
           "bullseye", "uni03FE", "uni03FF", "pipedblbar"]

_inter = {}


def targets(names):
    return [n for n in names if n in STACKED or n.endswith((".circled", ".squared"))]


def centre(glyph_set, draw):
    rec = DecomposingRecordingPen(glyph_set)
    draw(rec)
    bp = BoundsPen(None)
    rec.replay(bp)
    return (bp.bounds[0] + bp.bounds[2]) / 2


def parts(glyph_set, components, contours):
    """Ink centre of each component, then of the contours (all together), if any."""
    out = [centre(glyph_set, lambda pen, c=c: pen.addComponent(*c)) for c in components]
    if contours:
        out.append(centre(glyph_set, lambda pen: [c.draw(pen) for c in contours]))
    return out


def inter(master):
    """{name: (width minus the first component's, [later parts' centres minus the first's])}."""
    if not _inter:
        font = glyphsLib.GSFont(tabular.INTER)
        for m in font.masters:
            if m.axes[0] != 14:
                continue
            layers = {g.name: g.layers[m.id] for g in font.glyphs}
            out = _inter[m.name] = {}
            for name in targets(layers):
                layer = layers[name]
                comps = [(c.name, c.transform) for c in layer.components]
                xs = parts(layers, comps, layer.paths)
                out[name] = (layer.width - layers[comps[0][0]].width, [x - xs[0] for x in xs[1:]])
    return _inter[master]


def moved(component, dx):
    t = component.transformation
    component.transformation = Transform(t[0], t[1], t[2], t[3], t[4] + dx, t[5])


def restack(ufo, glyph, ref):
    """Move glyph's later parts to Inter's offsets; returns its old width if anything changed."""
    extra, offsets = ref
    comps = list(glyph.components)
    xs = parts(ufo, [(c.baseGlyph, c.transformation) for c in comps], glyph.contours)
    changed = False
    for i, offset in enumerate(offsets, 1):
        dx = round(xs[0] + offset - xs[i])
        if not dx:
            continue
        changed = True
        if i < len(comps):
            c = comps[i]
            base = ufo[c.baseGlyph]
            came = {(a.name, round(c.transformation.transformPoint((a.x, a.y))[0])) for a in base.anchors}
            for a in glyph.anchors:
                if (a.name, round(a.x)) in came:
                    a.x += dx
            moved(c, dx)
        else:
            for contour in glyph.contours:
                for p in contour.points:
                    p.x += dx
    width = ufo[comps[0].baseGlyph].width + extra
    old = glyph.width
    if width != old:
        glyph.width = width
        changed = True
    return old if changed else None


def follow(ufo, name, old):
    """Glyphs built on `name` alone take its new width; returns their names."""
    new = ufo[name].width
    out = []
    for g in ufo:
        if g.contours or len(g.components) != 1 or g.components[0].baseGlyph != name:
            continue
        if tabular.tabular(g.name) or g.width != old:
            continue
        c = g.components[0]
        if c.transformation[0] < 0:
            moved(c, new - old)
        g.width = new
        out.append(g.name)
    return out


def apply(ufo, master):
    """Restack the glyphs in `ufo`; returns the names of the glyphs that changed."""
    ref = inter(master)
    changed = []
    for name in targets(ufo.keys()):
        if name not in ref:
            continue
        old = restack(ufo, ufo[name], ref[name])
        if old is not None:
            changed.append(name)
            changed += follow(ufo, name, old)
    return changed


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        changed += [n for n in tabular.apply(ufo, master) if n not in changed]
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {len(changed)} glyphs changed ({master})")


if __name__ == "__main__":
    main(sys.argv[1:])
