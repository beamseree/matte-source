"""Give the period and the dots of !, ?, ¡ and ¿ the i dot's size and proportions, and keep
the glyphs built on them in place.

tools/redraw.py gave the i and j dots the mockups' size (its DOTS). The period and the
other punctuation dots were still Inter's, scaled by tools/derive.py with a heavier
vertical weight, so Regular's period was 280 x 290 against the i dot's 240 x 236. So:

- Each dot is scaled, separately in x and y, to DOTS's width and height times FACTOR,
  about its own centre line, so it stays centred on its stem. The period's and the ! and ?
  dots' feet stay on the overshoot, and the ¡ dots keep their tops (¿ is ? turned round,
  so its dot keeps its top too). Points only move, so the masters stay compatible.
- period, exclam, exclamdown and exclamdown.case keep their sidebearings (Inter ties them
  to the period's), so each narrows by as much as its ink does.
- The glyphs built on these follow as FOLLOW says. In the colon the upper dot keeps its
  top, so the colon stays centred on the middle of the x-height, and both dots are centred
  in the advance (derive.py had moved only the upper one, 17-44 units off the lower).

Run it before tools/tabular.py, which centres the tabular forms (period.tf, colon.tf,
semicolon.tf) on the result; run on its own, it runs tabular.py after. Running it again
changes nothing.

Usage: python tools/dots.py [--factor 1.08] source/PlaceholderSans-*.ufo
"""

import argparse
import os
import re
import sys

import ufoLib2
from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Transform
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tabular  # noqa: E402
from redraw import DOTS  # noqa: E402

# The punctuation dots' size against the i dot's.
FACTOR = 1.0

# Glyphs with a dot of their own: the dot's contour index, and the edge that stays.
DOTTED = {"period": (0, "foot"), "exclam": (1, "foot"), "question": (1, "foot"),
          "exclamdown": (1, "top"), "exclamdown.case": (1, "top")}

# The glyphs built on these, and how each follows. Components keep their offsets, so a
# dot keeps its left edge and foot, unless the glyph's moves say otherwise:
#   {index: (x, y)}  that component keeps its ink's centre ("middle") or top ("top") in
#                    place, or is centred in the advance ("advance")
#   ("row",)         components side by side, which close up as each narrows; ("row",
#                    "middle") then keeps the ink's centre, for marks
#   ("mirror",)      one component turned round, at its base's width
# The width keeps the right sidebearing ("ink"), changes as another glyph's does (its
# name), or stays (None).
FOLLOW = {
    "colon": ({0: ("advance", None), 1: ("advance", "top")}, "period"),
    "colon.case": ({}, "colon"),
    "raisedcolonmod": ({}, "colon"),
    "ratio": ({}, "colon.case"),
    "semicolon": ({1: ("middle", "top")}, "ink"),
    "semicolon.ss03": ({1: ("middle", "top")}, "ink"),
    "questiongreek": ({}, "semicolon"),
    "reversedsemicolon": (("mirror",), "semicolon"),
    "reversedsemicolon.ss03": (("mirror",), "semicolon.ss03"),
    "periodcentered": ({0: (None, "middle")}, "period"),
    "hyphendot": ({}, "periodcentered"),
    "ldot": ({}, "ink"),
    "ldot.ss02": ({}, "ink"),
    "anoteleia": ({0: (None, "top")}, "period"),
    "onedotleader": ({}, "period"),
    "twodotleader": (("row",), "ink"),
    "ellipsis": (("row",), "ink"),
    "threedotsabovecomb": (("row", "middle"), None),
    "fourdotsabovecomb": (("row", "middle"), None),
    "tripleunderdotcomb": ({0: ("middle", "top")}, None),
    "period.numr": ({}, "ink"),
    "period.dnom": ({}, "ink"),
    "bullseye": ({1: ("middle", "middle")}, None),
    "uni03FE": ({1: ("middle", "middle")}, None),
    "uni03FF": ({1: ("middle", "middle")}, None),
    "interrobang": ({0: ("middle", None)}, None),
    "exclam1": ({}, "exclam"),
    "exclamdbl": (("row",), "ink"),
    "uni2048": (("row",), "ink"),
    "uni2049": (("row",), "ink"),
    "exclam.circled": ({1: ("middle", None)}, None),
    "exclam.squared": ({1: ("middle", None)}, None),
}

# Built on these, but unmoved: ? and ‽ keep their widths and ink (the hook sets both), and
# tools/tabular.py places the tabular forms.
UNMOVED = {"questiondown", "question.circled", "question.squared", "uni2047",
           "invertedinterrobang"}


def users(ufo, names):
    """Every glyph built on `names`, through components."""
    built = {}
    for glyph in ufo:
        for c in glyph.components:
            built.setdefault(c.baseGlyph, set()).add(glyph.name)
    out, todo = set(), list(names)
    while todo:
        for user in built.get(todo.pop(), ()):
            if user not in out:
                out.add(user)
                todo.append(user)
    return out


def shift(glyph, dx):
    for contour in glyph.contours:
        for p in contour.points:
            p.x += dx
    for c in glyph.components:
        move(c, dx, 0)
    for a in glyph.anchors:
        a.x += dx


def move(component, dx, dy):
    t = component.transformation
    component.transformation = Transform(t[0], t[1], t[2], t[3], otRound(t[4] + dx), otRound(t[5] + dy))


def resize(ufo, glyph, index, keep, w, h):
    """Scale one dot about its centre line to w x h, keeping its foot or top; the glyph keeps
    its sidebearings."""
    contour = glyph.contours[index]
    if len(contour) != 12:
        raise ValueError(f"{glyph.name}: expected a 12-point dot, contour {index}")
    b = contour.getBounds()
    if (b.xMax - b.xMin, b.yMax - b.yMin) == (w, h):
        return False
    box = glyph.getBounds(ufo)
    cx, y0 = (b.xMin + b.xMax) / 2, b.yMin if keep == "foot" else b.yMax
    sx, sy = w / (b.xMax - b.xMin), h / (b.yMax - b.yMin)
    for p in contour.points:
        p.x = otRound(cx + (p.x - cx) * sx)
        p.y = otRound(y0 + (p.y - y0) * sy)
    new = glyph.getBounds(ufo)
    shift(glyph, box.xMin - new.xMin)
    glyph.width += (new.xMax - new.xMin) - (box.xMax - box.xMin)
    return True


def follow(ufo, glyph, moves, width, before):
    box = before[glyph.name][0]
    ops = moves if isinstance(moves, tuple) else ()
    if width in before:
        glyph.width += ufo[width].width - before[width][1]
    if "row" in ops:
        dx = 0
        for c in glyph.components:
            move(c, dx, 0)
            dx += ufo[c.baseGlyph].width - before[c.baseGlyph][1]
    if "mirror" in ops:
        c = glyph.components[0]
        move(c, ufo[c.baseGlyph].width - before[c.baseGlyph][1], 0)
    if isinstance(moves, dict):
        for index, (kx, ky) in moves.items():
            c = glyph.components[index]
            b0, b1 = before[c.baseGlyph][0], ufo[c.baseGlyph].getBounds(ufo)
            xx, _, _, yy, x, _ = c.transformation
            dx = dy = 0
            if kx == "middle":
                dx = xx * (b0.xMin + b0.xMax - b1.xMin - b1.xMax) / 2
            elif kx == "advance":
                dx = glyph.width / 2 - xx * (b1.xMin + b1.xMax) / 2 - x
            if ky == "middle":
                dy = yy * (b0.yMin + b0.yMax - b1.yMin - b1.yMax) / 2
            elif ky == "top":
                dy = yy * (b0.yMax - b1.yMax)
            move(c, dx, dy)
    if ops[-1:] == ("middle",):
        new = glyph.getBounds(ufo)
        dx = otRound((box.xMin + box.xMax - new.xMin - new.xMax) / 2)
        for c in glyph.components:
            move(c, dx, 0)
    if width == "ink":
        glyph.width += otRound(glyph.getBounds(ufo).xMax - box.xMax)


def state(glyph):
    return glyph.width, [tuple(c.transformation) for c in glyph.components]


def apply(ufo, master, factor=FACTOR):
    """Resize the dots in `ufo` and move the glyphs built on them; returns the glyphs that changed."""
    w, h, _ = DOTS[master]
    w, h = otRound(w * factor), otRound(h * factor)
    built = users(ufo, DOTTED)
    unknown = {n for n in built - set(FOLLOW) - UNMOVED if not tabular.tabular(n)}
    if unknown:
        raise ValueError(f"no FOLLOW rule for {sorted(unknown)}")
    before = {n: (ufo[n].getBounds(ufo), ufo[n].width) for n in set(DOTTED) | built}
    changed = [n for n, (index, keep) in DOTTED.items() if resize(ufo, ufo[n], index, keep, w, h)]
    for name in tabular.bases_first(ufo, [n for n in FOLLOW if n in ufo]):
        was = state(ufo[name])
        follow(ufo, ufo[name], *FOLLOW[name], before)
        if state(ufo[name]) != was:
            changed.append(name)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--factor", type=float, default=FACTOR)
    args = ap.parse_args()
    for path in args.paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master, args.factor)
        changed += [n for n in tabular.apply(ufo, master) if n not in changed]
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        dot = ufo["period"].getBounds(ufo)
        print(f"{path}: period {dot.xMax - dot.xMin:g} x {dot.yMax - dot.yMin:g}, "
              f"{len(changed)} glyphs changed ({master})")


if __name__ == "__main__":
    main()
