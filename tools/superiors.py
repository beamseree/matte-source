"""Narrow the superscripts, and so the subscripts, to the figures' proportions.

Inter draws its superscripts (.sups: the figures, the letters, + - = ( ) [ ]) with RMX
Scaler at 66% of the default glyph's width but 54.5% of its height (each one's lib keeps
the recipe), so they are stretched 21% sideways: a superscript 0 was 1.26 times as wide
for its height as our 0 in every master but Black (1.18), and in Regular its horizontals
were thin against its verticals (top over side 0.82 of the 0's own; Thin 0.94, Black
0.94). Against 30 sans serifs (Roboto, Work Sans, IBM Plex Sans, Source Sans 3, Geist,
Figtree, Noto Sans, Open Sans, Public Sans, Manrope, Montserrat, Archivo, Lexend ...), the
superscript figures are a median 1.05 times as wide for their height as the figures at
100, 400 and 900 (1.00-1.17; Roboto's the widest), and their top over side is a median
1.00 / 0.99 / 0.95 times the figures' (Thin / Regular / Black weights). Inter's fractions
(.dnom, .numr) are scaled evenly (55% by 54.5%) and are left alone.

So each master's drawn superscripts move in x only (heights, and so the horizontal strokes,
stay), the way tools/derive.py compensates stems: their x coordinates are mixed with the
next heavier master's (or the lighter one's, or extrapolated past Black away from Regular)
by a factor f, then scaled by s about the left ink edge, with both sidebearings kept. One
(f, s) per master, solved on the figures: s makes the superscript 0's side CONTRAST times
the top it has, against the 0's own top over side, and f makes the superscript figures
RATIO times as wide for their height as the figures (the mean of 0-9). The letters and
signs take the same (f, s). The .subs are the .sups moved down and follow, as do ℀ ℅ ℁
(through tools/accents.py). Points only move, so the masters stay compatible.

The sidebearings stay, so tools/spacing.py's SIDES for the small glyphs don't change; run on
its own, this runs spacing.py after (which runs accents.py, stacked.py, tabular.py,
kerning.py and kern.py). Run it before tools/spacing.py. Running it again changes nothing.

Usage: python tools/superiors.py source/PlaceholderSans-*.ufo
       python tools/superiors.py --check [source]   # the superscripts against the figures
"""

import os
import re
import sys

import ufoLib2
from fontTools.misc.roundTools import otRound
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTERS = ("Thin", "Regular", "Black")
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
# How wide the superscript figures are for their height, as a multiple of the figures'
# (Inter's: 1.26 / 1.26 / 1.18).
RATIO = {"Thin": 1.10, "Regular": 1.10, "Black": 1.10}
# The superscript 0's top over its side, as a multiple of the 0's.
CONTRAST = {"Thin": 1.00, "Regular": 1.00, "Black": 0.95}
# Below these the masters are taken as done (a unit of rounding moves a ratio about 0.002).
TOLERANCE = 0.005


def drawn(ufo):
    """The superscripts drawn as contours (four.sups.ss01 and zero.sups.slash too)."""
    return sorted(n for n in ufo.keys() if "sups" in n.split(".")[1:] and ufo[n].contours)


def points(glyph):
    return [(p.x, p.y) for c in glyph.contours for p in c.points]


def outline(glyph, xs):
    """A RecordingPen of the glyph's contours with its points' x replaced by xs."""
    rec = RecordingPen()
    pen = PointToSegmentPen(rec)
    i = 0
    for contour in glyph.contours:
        pen.beginPath()
        for p in contour.points:
            pen.addPoint((xs[i], p.y), p.type, p.smooth)
            i += 1
        pen.endPath()
    return rec


def bounds(rec):
    pen = BoundsPen(None)
    rec.replay(pen)
    return pen.bounds


def side(rec):
    """The first ink run across the glyph's middle (the 0's left side)."""
    b = bounds(rec)
    a, z = strokes.cut(rec.replay, (b[1] + b[3]) / 2 + strokes.EPS)[0]
    return z - a


def top(rec):
    """The last ink run up the glyph's middle (the 0's top)."""
    b = bounds(rec)
    turned = lambda pen: rec.replay(TransformPen(pen, (0, 1, 1, 0, 0, 0)))
    a, z = strokes.cut(turned, (b[0] + b[2]) / 2 + strokes.EPS)[-1]
    return z - a


class Master:
    """One master's superscripts, with the x coordinates of the masters either side."""

    def __init__(self, fonts, master):
        i = MASTERS.index(master)
        self.ufo = fonts[master]
        self.names = drawn(self.ufo)
        self.x = {n: [x for x, _ in points(self.ufo[n])] for n in self.names}
        ax = lambda m, n: [a.x for a in sorted(fonts[m][n].anchors, key=lambda a: a.name)]
        self.ax = {n: ax(master, n) for n in self.names}
        # Heavier: the next master, or past this one away from the lighter one; lighter the
        # same way round. Each as (master to mix toward, sign).
        self.heavier = (MASTERS[i + 1], 1) if i + 1 < len(MASTERS) else (MASTERS[i - 1], -1)
        self.lighter = (MASTERS[i - 1], 1) if i > 0 else (MASTERS[i + 1], -1)
        self.other = {}
        for m in {self.heavier[0], self.lighter[0]}:
            for n in self.names:
                assert len(points(fonts[m][n])) == len(self.x[n]), (m, n)
            self.other[m] = {n: ([x for x, _ in points(fonts[m][n])], ax(m, n)) for n in self.names}

    def mixed(self, name, f, anchors=False):
        m, sign = self.heavier if f >= 0 else self.lighter
        k = abs(f) * sign
        own = self.ax[name] if anchors else self.x[name]
        theirs = self.other[m][name][1 if anchors else 0]
        return [a + k * (b - a) for a, b in zip(own, theirs)]

    def ink(self, name, f):
        rec = outline(self.ufo[name], self.mixed(name, f))
        return rec, bounds(rec)

    def shape(self, f, s):
        """The superscript figures' width for their height over the figures', on average."""
        out = []
        for fig in FIGURES:
            _, b = self.ink(f"{fig}.sups", f)
            fb = self.ufo[fig].getBounds(self.ufo)
            out.append((s * (b[2] - b[0]) / (b[3] - b[1])) / ((fb.xMax - fb.xMin) / (fb.yMax - fb.yMin)))
        return sum(out) / len(out)

    def solve(self, ratio, contrast):
        """(f, s) for the RATIO and CONTRAST given."""
        zero = DecomposingRecordingPen(self.ufo)
        self.ufo["zero"].draw(zero)
        own = top(zero) / side(zero)
        sup_top = top(outline(self.ufo["zero.sups"], self.x["zero.sups"]))
        target = sup_top / (contrast * own)
        scale = lambda f: target / side(self.ink("zero.sups", f)[0])
        lo, hi = -0.6, 0.6
        for _ in range(40):
            f = (lo + hi) / 2
            # Mixing in the heavier master's points and scaling down to the side narrows.
            if self.shape(f, scale(f)) > ratio:
                lo = f
            else:
                hi = f
        f = (lo + hi) / 2
        return f, scale(f)

    def apply(self, f, s):
        changed = []
        for name in self.names:
            glyph = self.ufo[name]
            b = glyph.getBounds(self.ufo)
            right = glyph.width - b.xMax
            _, mb = self.ink(name, f)
            fx = lambda x: b.xMin + s * (x - mb[0])
            xs = iter(self.mixed(name, f))
            for contour in glyph.contours:
                for p in contour.points:
                    p.x = otRound(fx(next(xs)))
            for a, x in zip(sorted(glyph.anchors, key=lambda a: a.name), self.mixed(name, f, True)):
                a.x = otRound(fx(x))
            glyph.width = otRound(glyph.getBounds(self.ufo).xMax + right)
            changed.append(name)
        return changed



def apply_all(fonts, ratio=RATIO, contrast=CONTRAST):
    """Narrow the superscripts in every master of {master: ufo}, reading all of them before
    changing any; returns {master: changed glyphs}."""
    found = {m: Master(fonts, m) for m in MASTERS if m in fonts}
    plans = {}
    for m, master in found.items():
        now = master.shape(0, 1)
        zero = DecomposingRecordingPen(master.ufo)
        master.ufo["zero"].draw(zero)
        sup = outline(master.ufo["zero.sups"], master.x["zero.sups"])
        con = (top(sup) / side(sup)) / (top(zero) / side(zero))
        if abs(now - ratio[m]) < TOLERANCE and abs(con - contrast[m]) < TOLERANCE:
            continue
        plans[m] = master.solve(ratio[m], contrast[m])
    return {m: found[m].apply(*plans[m]) for m in plans}


def check(src):
    fonts = {m: ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{m}.ufo")) for m in MASTERS}
    for m in MASTERS:
        ufo = fonts[m]
        master = Master(fonts, m)
        zero = DecomposingRecordingPen(ufo)
        ufo["zero"].draw(zero)
        sup = outline(ufo["zero.sups"], master.x["zero.sups"])
        print(f"{m}: superscript figures {master.shape(0, 1):.2f} times as wide for their height "
              f"as the figures (RATIO {RATIO[m]:.2f}); 0's top over side "
              f"{(top(sup) / side(sup)) / (top(zero) / side(zero)):.2f} of the 0's "
              f"(CONTRAST {CONTRAST[m]:.2f}); side {side(sup):.0f} against the 0's {side(zero):.0f}, "
              f"top {top(sup):.0f} against {top(zero):.0f}")


def main(paths):
    import spacing
    masters = {re.search(r"-(\w+)\.ufo", p).group(1): p for p in paths}
    fonts = {m: ufoLib2.Font.open(p) for m, p in masters.items()}
    changed = apply_all(fonts)
    for m, path in masters.items():
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed.get(m, []):
            glyph_set.writeGlyph(name, fonts[m][name], fonts[m][name].drawPoints)
        print(f"{path}: {len(changed.get(m, []))} superscripts narrowed ({m})")
    # What follows in tools/to_ufo.py: the sides, then the composites and kerning.
    spacing.main(paths)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        check(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source"))
    else:
        main(sys.argv[1:])
