"""Give accented letters (and every glyph built from others) Inter's widths and marks.

tools/derive.py told marks from letters by their width, zero in Inter's Regular, but Inter's
combining marks have widths in its source (acutecomb 573 / 661 / 822 in Thin / Regular /
Black), so it handled every mark as a letter set beside its base: each composite took the
marks' own width changes (their sidebearings were tightened in Thin and Regular and
loosened in Black, so A 1453, Á 1417, Ä 1385 in Regular; Black's 15-32 wider), and each mark
moved right by its base's width change instead of following its anchor (Ÿ's dieresis 59-99
units left of centre, ñ's tilde 36-58). Marks over the lowercase also kept Inter's height
while the x-height came down 42 units, so they sat 42 units higher above it than Inter's.

So, with Inter's source (its text-size masters) as the rule, for each glyph built only of
components:
- A component is attached if it has a "_" anchor that meets an anchor propagated through
  the components before it, in Inter (a mark); the others are set beside them (n and j in
  nj). The first component is set beside.
- Each component set beside keeps Inter's offset plus the width changes of the components
  set beside before it (and its own, if it is mirrored), as derive.py meant.
- Each attached component sits on the anchor it sits on in Inter, at Inter's offset from it
  (none, unless Inter placed it by hand), with anchors propagated by ufo2ft's algorithm.
  Except ť's caron in Thin, which Inter puts left of the stem: CARON_GAP places it.
- The width is Inter's plus the width changes of the components set beside, so a composite
  with its base's width in Inter has our base's width. Our combining marks have no width
  (glyphsLib zeroes them), so glyphs built beside one (´, ¨, the compound marks) keep their
  widths and the offsets of the components set beside, and marks stay at no width.
- The glyph's anchors are propagated again from its components, keeping those Inter sets
  by hand.
Left alone: glyphs with contours of their own (t, f, Q, the stroked and barred letters;
their widths were set on purpose and none of them carries a mark), the glyphs other tools
place on purpose (tools/dots.py's FOLLOW and UNMOVED, tools/stacked.py's, the tabular
glyphs), and the i and j dots, which tools/redraw.py centres over the stem at its DOTS size
(redone here, so they follow a stem that moves). Components only move, so the masters stay
compatible.

Run it after every tool that changes a base glyph's outline or width (tools/spacing.py is
the last) and before tools/kern.py, tools/dots.py, tools/stacked.py and tools/tabular.py.
Running it again changes nothing.

Usage: python tools/accents.py [--check] source/PlaceholderSans-*.ufo
"""

import argparse
import os
import re
import sys

import glyphsLib
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ufoLib.glifLib import GlyphSet
from ufo2ft.filters.propagateAnchors import (AnchorData, _depth_sorted_glyphs,
                                             anchors_traversing_components)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dots  # noqa: E402
import redraw  # noqa: E402
import stacked  # noqa: E402
import strokes  # noqa: E402
import tabular  # noqa: E402

CATEGORIES = "public.openTypeCategories"
DOTTED = ("i", "j")   # tools/redraw.py's set_dot places these dots

# Inter's Thin master puts ť's caron left of t's stem, so from wght 150 to 300 it ran through
# the stem. In the masters named, the caron's left edge goes this far right of the stem's
# right edge instead (Regular's is 101 at 430); the others keep Inter's offset.
CARON_GAP = {"Thin": {"tcaron": 100, "tcaron.1": 100}}

_inter = {}


class _Component:
    def __init__(self, name, transform):
        self.baseGlyph, self.transformation = name, tuple(transform)


class _Glyph:
    def __init__(self, components):
        self.components = components


def left_alone(name):
    return (name in dots.FOLLOW or name in dots.UNMOVED or tabular.tabular(name)
            or stacked.targets([name]))


def propagate(glyphs, categories, explicit, component_names=None):
    """{name: [AnchorData]} for every glyph, through its components, by ufo2ft's algorithm.
    `glyphs` is {name: [_Component]}, `explicit` {name: [AnchorData]} (a glyph's own)."""
    done, counts = {}, {}
    names = component_names or {}
    order = _depth_sorted_glyphs({n: _Glyph(c) for n, c in glyphs.items()})
    for name in order:
        done[name] = anchors_traversing_components(
            name, explicit.get(name, []), glyphs[name], categories.get(name) == "mark",
            categories.get(name) == "ligature", done, counts, names.get(name, {}))
    return done, counts, order


def table(name, components, categories, done, counts, component_names):
    """The anchors propagated through `components`, the glyph's components so far."""
    found = anchors_traversing_components(
        name, [], components, False, categories.get(name) == "ligature", done, dict(counts),
        component_names)
    return {a.name: (a.x, a.y) for a in found}


def attachment(mark_anchors, base_table, transform):
    """(base anchor, mark anchor, offset) for a mark: the pair it sits on exactly, else the
    pair with the same name, else None."""
    t = Transform(*transform)
    best = None
    for a in mark_anchors:
        if not a.name.startswith("_"):
            continue
        x = a.name[1:]
        for y, (bx, by) in base_table.items():
            if y != x and not y.startswith(x + "_"):
                continue
            mx, my = t.transformPoint((a.x, a.y))
            offset = (round(bx - mx), round(by - my))
            if offset == (0, 0):
                return y, a.name, offset
            if best is None or (y == x and best[0] != x):
                best = (y, a.name, offset)
    return best


def inter(master, categories):
    """{name: {"width", "components": [(name, transform)], "explicit": {anchor names},
    "names": {index: anchor}, "attach": {index: attachment}}} from Inter's text-size master.
    A component is attached (a mark) if it has a "_" anchor that meets one of the anchors
    propagated through the components before it; the others are set beside them (n and j in
    nj, though j has a "_right" anchor)."""
    if master not in _inter:
        font = glyphsLib.GSFont(tabular.INTER)
        for m in font.masters:
            if m.axes[0] != 14:
                continue
            layers = {g.name: g.layers[m.id] for g in font.glyphs}
            glyphs = {n: [_Component(c.name, c.transform) for c in l.components]
                      for n, l in layers.items()}
            explicit = {n: [AnchorData(a.name, a.position.x, a.position.y) for a in l.anchors]
                        for n, l in layers.items()}
            names = {n: {i: c.anchor for i, c in enumerate(l.components) if c.anchor}
                     for n, l in layers.items()}
            done, counts, _ = propagate(glyphs, categories, explicit, names)
            out = _inter[m.name] = {}
            for name, layer in layers.items():
                comps = glyphs[name]
                attach = {}
                for i, c in enumerate(comps[1:], 1):
                    base = table(name, comps[:i], categories, done, counts, names[name])
                    found = attachment(done[c.baseGlyph], base, c.transformation)
                    if found:
                        attach[i] = found
                out[name] = {"width": layer.width,
                             "components": [(c.baseGlyph, c.transformation) for c in comps],
                             "explicit": {a.name for a in explicit[name]},
                             "names": names[name], "attach": attach}
    return _inter[master]


def stem_right(ufo, component):
    """The right edge of a placed t's stem, 80 units below its top, where nothing else is."""
    rec = DecomposingRecordingPen(ufo)
    ufo[component.baseGlyph].draw(rec)
    top = ufo[component.baseGlyph].getBounds(ufo).yMax
    return strokes.cut(rec.replay, top - 80 + strokes.EPS)[-1][1] + component.transformation[4]


def moved(component, dx, dy=0):
    t = component.transformation
    component.transformation = Transform(t[0], t[1], t[2], t[3], t[4] + dx, t[5] + dy)


def apply(ufo, master):
    """Re-place components, widths and anchors in `ufo`; returns the glyphs that changed."""
    categories = ufo.lib.get(CATEGORIES, {})
    ref = inter(master, categories)
    own = {g.name: [AnchorData(a.name, a.x, a.y) for a in g.anchors] for g in ufo}
    glyphs = {g.name: [_Component(c.baseGlyph, c.transformation) for c in g.components]
              for g in ufo}
    done, counts = {}, {}
    order = _depth_sorted_glyphs({n: _Glyph(c) for n, c in glyphs.items()})
    changed = []
    for name in order:
        glyph = ufo[name]
        r = ref.get(name)
        comps = list(glyph.components)
        ours = [c.baseGlyph for c in comps]
        fixed = (not comps or glyph.contours or r is None or left_alone(name)
                 or ours != [n for n, _ in r["components"]])
        if fixed:
            done[name] = anchors_traversing_components(
                name, own[name], glyphs[name], categories.get(name) == "mark",
                categories.get(name) == "ligature", done, counts,
                {} if r is None else r["names"])
            continue
        was = (glyph.width, [tuple(c.transformation) for c in comps],
               sorted((a.name, a.x, a.y) for a in glyph.anchors))
        attached = r["attach"]
        # Our combining marks have no width (glyphsLib zeroes them), so a glyph built beside
        # one (´, ¨, the compound marks) keeps its width and offsets.
        beside = [b for i, b in enumerate(ours) if i not in attached]
        spacing = all(ufo[b].width or not ref[b]["width"] for b in beside)
        # Components set beside: Inter's offsets plus the width changes before them.
        shift = 0
        for i, (c, (base, t)) in enumerate(zip(comps, r["components"])):
            if i in attached or not spacing:
                continue
            delta = ufo[base].width - ref[base]["width"]
            dx = t[4] + shift + (delta if c.transformation[0] < 0 else 0) - c.transformation[4]
            moved(c, round(dx))
            shift += delta
        # Marks: on the anchor Inter puts them on, at Inter's offset from it.
        for i, c in enumerate(comps):
            if i not in attached or name in DOTTED:
                continue
            base_anchor, mark_anchor, (ox, oy) = attached[i]
            so_far = [_Component(k.baseGlyph, k.transformation) for k in comps[:i]]
            anchors = table(name, so_far, categories, done, counts, r["names"])
            if base_anchor not in anchors:
                continue
            m = next(a for a in done[c.baseGlyph] if a.name == mark_anchor)
            mx, my = Transform(*c.transformation).transformPoint((m.x, m.y))
            bx, by = anchors[base_anchor]
            moved(c, round(bx - mx - ox), round(by - my - oy))
        gap = CARON_GAP.get(master, {}).get(name)
        if gap is not None:
            base, caron = comps[0], comps[-1]
            b = ufo[caron.baseGlyph].getBounds(ufo)
            moved(caron, round(stem_right(ufo, base) + gap - (b.xMin + caron.transformation[4])))
        if name in DOTTED:
            redraw.set_dot(ufo, glyph, redraw.DOTS.get(master))
        if spacing and glyph.width and r["width"]:   # marks keep no width
            glyph.width = round(r["width"] + sum(ufo[b].width - ref[b]["width"] for b in beside))
        explicit = [a for a in own[name] if a.name in r["explicit"]]
        new = anchors_traversing_components(
            name, explicit, [_Component(c.baseGlyph, c.transformation) for c in comps],
            categories.get(name) == "mark", categories.get(name) == "ligature", done, counts,
            r["names"])
        done[name] = new
        order = [a.name for a in glyph.anchors]
        glyph.clearAnchors()
        for a in sorted(new, key=lambda a: order.index(a.name) if a.name in order else len(order)):
            glyph.appendAnchor({"name": a.name, "x": round(a.x), "y": round(a.y)})
        now = (glyph.width, [tuple(c.transformation) for c in comps],
               sorted((a.name, a.x, a.y) for a in glyph.anchors))
        if now != was:
            changed.append(name)
    return changed


def run(path, check=False):
    master = re.search(r"-(\w+)\.ufo", path).group(1)
    ufo = ufoLib2.Font.open(path)
    before = {g.name: g.width for g in ufo}
    changed = apply(ufo, master)
    wider = sum(ufo[n].width != before[n] for n in changed)
    print(f"{path}: {len(changed)} glyphs changed, {wider} of them in width ({master})")
    if not check:
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--check", action="store_true", help="report, don't write")
    args = ap.parse_args()
    for path in args.paths:
        run(path, args.check)


if __name__ == "__main__":
    main()
