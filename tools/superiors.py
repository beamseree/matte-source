"""Build the superscripts, and so the subscripts, from our own figures, lowercase and signs.

Inter draws its superscripts (.sups: the figures, the letters, + - = ( ) [ ]) with RMX
Scaler from its own glyphs at 66% of their width but 54.5% of their height, so they were
stretched 21% sideways: a superscript 0 was 1.26 times as wide for its height as our 0 in
every master but Black (1.18), and in Regular its horizontals were thin against its
verticals (top over side 0.82 of the 0's own). Against 30 sans serifs (Roboto, Work Sans,
IBM Plex Sans, Source Sans 3, Geist, Figtree, Noto Sans, Open Sans, Public Sans, Manrope,
Montserrat, Archivo, Lexend ...), the superscript figures are a median 1.05 times as wide
for their height as the figures at 100, 400 and 900 (1.00-1.17; Roboto's the widest), and
their top over side is a median 1.00 / 0.99 / 0.95 times the figures' (Thin / Regular /
Black weights). And they were Inter's shapes, not ours: the superscript letters kept the
round-topped f, the curved t foot, the hooked y, the curved joints of k v w x, the drooping
r and the flat cuts of s c e that we redrew in the lowercase, and the superscript 5 Inter's
thin joint; so did ª and º (RMX Scaler at 80% by 75%).

So each superscript is built from its default glyph (decomposed), as RMX Scaler does: its x
and y coordinates are mixed with the next heavier master's (the lighter one's, or past
Black away from Regular, when a factor is negative) by fx and fy, then scaled by sx and sy
and set on the superscript's baseline, keeping the glyph's left edge and right
sidebearing; anchors keep their place across the ink. One (fx, sx, fy, sy) per master and
group, solved on our glyphs:
- figures (and the figure alternates, and the signs, at SIGN_MIDDLE): sy makes
  the 7 as tall as FIGURE_Y; fy gives the 0's top and bottom FIGURE_STROKE (Inter's
  superscript horizontals); fx and sx give the 0's side CONTRAST times the 0's own side for
  that stroke, and make the superscript figures RATIO (1.10) times as wide for their
  height as the figures, on average;
- letters (ª and º's a and o apart): sy makes x as tall as LETTER_Y; the strokes are the
  superscript figures', times n's stem and o's top and bottom over the 0's side and top
  and bottom, so letters and figures are as heavy as in our text; the width is RATIO, on
  average over the letters whose width isn't mostly stem (not i, j, l);
- ª and º: ORDINAL_Y is º's box (o's goes in it, and a's with it), with ORDINAL_STROKE
  (Inter's) at o's contrast and ORDINAL_RATIO (Inter's) for width.
The user chose RATIO 1.10 over 1.15 and 1.05 (and Inter's), in text at every weight and
against twelve other sans serifs; in Black the figures mix 57% past the master to stay as
heavy as Inter's superscripts. The .subs are the .sups moved down and follow, as do
℀ ℁ ℅ ℆ ⅍ (through tools/accents.py). Inter's fractions (.dnom, .numr) are scaled evenly
(55% by 54.5%) and are left alone.

The defaults' points are mixed across masters, so the superscripts get the defaults'
points, the same in every master. Run it after every tool that changes a default
(straighten.py ... xheight.py) and before tools/spacing.py, whose SIDES give the .sups
their sides; run on its own, it runs spacing.py after (which runs accents.py, stacked.py,
tabular.py, kerning.py and kern.py). Rerun it after redrawing a lowercase letter, figure or
sign. Running it again changes nothing.

Usage: python tools/superiors.py source/PlaceholderSans-*.ufo
       python tools/superiors.py --check [source]   # the superscripts against their targets
"""

import os
import re
import sys

import ufoLib2
from fontTools.misc.roundTools import otRound
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.pointPen import PointToSegmentPen
from fontTools.pens.recordingPen import DecomposingRecordingPointPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTERS = ("Thin", "Regular", "Black")

FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
# Superscripts of the figure alternates and of the signs, from their defaults.
ALTERNATES = {"zero.sups.slash": "zero.slash", "one.sups.ss01": "one.ss01",
              "three.sups.ss01": "three.1", "four.sups.ss01": "four.ss01",
              "six.sups.ss01": "six.ss01", "nine.sups.ss01": "nine.ss01"}
SIGNS = ("plus", "minus", "equal", "parenleft", "parenright", "bracketleft", "bracketright")
LETTERS = tuple("abcdefghijklmnopqrstuvwxyz") + ("a.1", "a.2")
NARROW = ("i", "j", "l")   # mostly stem: left out of the letters' mean width
ORDINALS = {"ordfeminine": "a", "ordmasculine": "o"}

# How wide the superscript figures and letters are for their height, as a multiple of
# their defaults' (Inter's were 1.26 / 1.26 / 1.18). The user chose 1.10 over 1.15 and
# 1.05, in text at every weight and against twelve other sans serifs.
RATIO = 1.10
# The superscript 0's top over its side, as a multiple of the 0's (other faces' median).
CONTRAST = {"Thin": 1.00, "Regular": 1.00, "Black": 0.95}
# Where the superscripts sit, per master: (baseline, top) of the figures (the 7's) and of
# the letters (x's), and º's ink box (Inter's places).
FIGURE_Y = {"Thin": (916, 1683), "Regular": (896, 1713), "Black": (886, 1728)}
# The signs' middles (Inter's places: higher than our signs scaled with the figures, + - =
# by 45-64 units; + had sat 5-12 above - and = in Regular and Black, and now sits with them).
SIGN_MIDDLE = {"Thin": {"math": 1280, "brackets": 1253},
               "Regular": {"math": 1269, "brackets": 1260},
               "Black": {"math": 1287, "brackets": 1274}}
SIGN_KIND = {"plus": "math", "minus": "math", "equal": "math", "parenleft": "brackets",
             "parenright": "brackets", "bracketleft": "brackets", "bracketright": "brackets"}
LETTER_Y = {"Thin": (916, 1499), "Regular": (896, 1520), "Black": (886, 1540)}
ORDINAL_Y = {"Thin": (614, 1506), "Regular": (625, 1516), "Black": (634, 1523)}
# The superscript 0's top and bottom strokes, and º's (Inter's), and how wide ª and º are
# for their height against our a and o (Inter's: they weren't stretched).
FIGURE_STROKE = {"Thin": 44.5, "Regular": 154.5, "Black": 229}
ORDINAL_STROKE = {"Thin": 46, "Regular": 160.5, "Black": 228.5}
# (ª's over a's and º's over o's, on average)
ORDINAL_RATIO = {"Thin": 0.99, "Regular": 1.03, "Black": 1.03}


# --- Outlines ------------------------------------------------------------------------------

def points(font, name):
    """The glyph's decomposed contours, as [[(x, y, segment type, smooth), ...], ...]."""
    rec = DecomposingRecordingPointPen(font)
    font[name].drawPoints(rec)
    out = []
    for method, args, kwargs in rec.value:
        if method == "beginPath":
            out.append([])
        elif method == "addPoint":
            (x, y), seg = args[0], args[1] if len(args) > 1 else kwargs.get("segmentType")
            smooth = args[2] if len(args) > 2 else kwargs.get("smooth", False)
            out[-1].append((x, y, seg, smooth))
    return out


def outline(contours):
    rec = RecordingPen()
    pen = PointToSegmentPen(rec)
    for contour in contours:
        pen.beginPath()
        for x, y, seg, smooth in contour:
            pen.addPoint((x, y), seg, smooth)
        pen.endPath()
    return rec


def bounds(rec):
    pen = BoundsPen(None)
    rec.replay(pen)
    return pen.bounds


def across(rec):
    """The first ink run across the middle of the ink (a left side or stem)."""
    b = bounds(rec)
    a, z = strokes.cut(rec.replay, (b[1] + b[3]) / 2 + strokes.EPS)[0]
    return z - a


def up(rec):
    """The mean of the first and last ink runs up the middle (a bottom and top stroke)."""
    b = bounds(rec)
    turned = lambda pen: rec.replay(TransformPen(pen, (0, 1, 1, 0, 0, 0)))
    runs = strokes.cut(turned, (b[0] + b[2]) / 2 + strokes.EPS)
    return (runs[0][1] - runs[0][0] + runs[-1][1] - runs[-1][0]) / 2


def ratio(b, d):
    """How wide the box b is for its height, against the box d."""
    return ((b[2] - b[0]) / (b[3] - b[1])) / ((d[2] - d[0]) / (d[3] - d[1]))


class Source:
    """A default glyph's points in one master, mixed in x and y with the masters beside."""

    def __init__(self, fonts, master, name):
        i = MASTERS.index(master)
        self.own = points(fonts[master], name)
        # Heavier: the next master, or past this one away from the lighter one; lighter the
        # same way round. Each as (master, sign).
        self.heavier = (MASTERS[i + 1], 1) if i + 1 < len(MASTERS) else (MASTERS[i - 1], -1)
        self.lighter = (MASTERS[i - 1], 1) if i > 0 else (MASTERS[i + 1], -1)
        self.other = {m: points(fonts[m], name) for m in {self.heavier[0], self.lighter[0]}}
        for m, contours in self.other.items():
            assert [len(c) for c in contours] == [len(c) for c in self.own], (name, master, m)

    def mixed(self, fx, fy):
        def toward(f):
            m, sign = self.heavier if f >= 0 else self.lighter
            return self.other[m], abs(f) * sign
        (ox, kx), (oy, ky) = toward(fx), toward(fy)
        return [[(p[0] + kx * (q[0] - p[0]), p[1] + ky * (r[1] - p[1]), p[2], p[3])
                 for p, q, r in zip(c, cx, cy)] for c, cx, cy in zip(self.own, ox, oy)]

    def ink(self, fx, fy):
        rec = outline(self.mixed(fx, fy))
        return rec, bounds(rec)


def solve(fn, target, lo=-1.0, hi=1.5):
    """The factor where the increasing fn reaches target."""
    for _ in range(50):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fn(mid) < target else (lo, mid)
    assert -0.99 < lo < 1.49, "no mix reaches the target"
    return (lo + hi) / 2


class Group:
    """Superscripts built alike in one master: sy from a default's height and the
    superscript's (base, top); fy from a horizontal stroke; fx and sx from a vertical stroke
    and the mean width ratio of `wide`."""

    def __init__(self, fonts, master, names, tall, place, href, h, vref, v, ratio_, wide):
        self.font = fonts[master]
        self.src = {n: Source(fonts, master, n) for n in names}
        d = self.font[tall].getBounds(self.font)
        self.sy = (place[1] - place[0]) / (d.yMax - d.yMin)
        self.base = place[0] - self.sy * d.yMin      # where the default's y = 0 goes
        self.fy = solve(lambda fy: self.sy * up(self.src[href].ink(0, fy)[0]), h)
        across_at = lambda fx: across(self.src[vref].ink(fx, self.fy)[0])
        def width(fx):
            sx = v / across_at(fx)
            return sum(ratio(self.src[n].ink(fx, self.fy)[1], self.font[n].getBounds(self.font))
                       * sx / self.sy for n in wide) / len(wide)
        self.fx = solve(lambda fx: -width(fx), -ratio_)
        self.sx = v / across_at(self.fx)

    def build(self, default, name, middle=None):
        """Draw `name` as `default`, built, keeping its left edge and right sidebearing, with
        its ink's middle at `middle` if given; anchors keep their place across the ink. True
        if anything changed."""
        glyph = self.font[name]
        old = glyph.getBounds(self.font)
        left, right = otRound(old.xMin), glyph.width - old.xMax
        contours = self.src[default].mixed(self.fx, self.fy)
        b = bounds(outline(contours))
        base = self.base if middle is None else middle - self.sy * (b[1] + b[3]) / 2
        new = [[(otRound(left + self.sx * (x - b[0])), otRound(base + self.sy * y), seg, smooth)
                for x, y, seg, smooth in c] for c in contours]
        before = [[(p.x, p.y, p.segmentType, p.smooth) for p in c] for c in glyph.contours]
        if before == new and not glyph.components:
            return False
        anchors = [(a, (a.x - old.xMin) / (old.xMax - old.xMin)) for a in glyph.anchors]
        glyph.clearContours()
        glyph.clearComponents()
        pen = glyph.getPointPen()
        for contour in new:
            pen.beginPath()
            for x, y, seg, smooth in contour:
                pen.addPoint((x, y), seg, smooth)
            pen.endPath()
        nb = glyph.getBounds(self.font)
        for a, at in anchors:
            a.x = otRound(nb.xMin + at * (nb.xMax - nb.xMin))
        glyph.width = otRound(nb.xMax + right)
        return True


def plan(fonts, master):
    """{group: Group} for one master."""
    font = fonts[master]
    def rec(name):
        return outline(points(font, name))
    zero_side, zero_tb = across(rec("zero")), up(rec("zero"))
    fig_v = FIGURE_STROKE[master] * zero_side / zero_tb / CONTRAST[master]
    figures = Group(fonts, master, FIGURES + tuple(ALTERNATES.values()) + SIGNS, "seven",
                    FIGURE_Y[master], "zero", FIGURE_STROKE[master], "zero", fig_v, RATIO, FIGURES)
    letters = Group(fonts, master, LETTERS, "x", LETTER_Y[master],
                    "o", FIGURE_STROKE[master] * up(rec("o")) / zero_tb,
                    "n", fig_v * across(rec("n")) / zero_side, RATIO,
                    tuple(n for n in LETTERS if n not in NARROW))
    o = rec("o")
    ordinals = Group(fonts, master, tuple(ORDINALS.values()), "o", ORDINAL_Y[master],
                     "o", ORDINAL_STROKE[master], "o", ORDINAL_STROKE[master] * across(o) / up(o),
                     ORDINAL_RATIO[master], tuple(ORDINALS.values()))
    # º's box is ORDINAL_Y; a takes its place from o's.
    return {"figures": figures, "letters": letters, "ordinals": ordinals}


def jobs():
    """(group, default, superscript[, sign kind]) for every superscript built."""
    out = [("figures", f, f + ".sups") for f in FIGURES]
    out += [("figures", d, s) for s, d in ALTERNATES.items()]
    out += [("figures", s, s + ".sups", SIGN_KIND[s]) for s in SIGNS]
    out += [("letters", n, n + ".sups") for n in LETTERS]
    out += [("ordinals", d, s) for s, d in ORDINALS.items()]
    return out


def apply_all(fonts):
    """Build the superscripts in every master of {master: ufo}, reading all of them before
    changing any; returns {master: changed glyphs}."""
    plans = {m: plan(fonts, m) for m in MASTERS if m in fonts}
    def build(m, group, default, name, kind=None):
        middle = SIGN_MIDDLE[m][kind] if kind else None
        return plans[m][group].build(default, name, middle)
    return {m: [job[2] for job in jobs() if build(m, *job)] for m in plans}


def check(src):
    fonts = {m: ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{m}.ufo")) for m in MASTERS}
    for m in MASTERS:
        font = fonts[m]
        def rec(name):
            return outline(points(font, name))
        def box(name):
            b = font[name].getBounds(font)
            return (b.xMin, b.yMin, b.xMax, b.yMax)
        wide = lambda names, sup: sum(ratio(box(sup(n)), box(n)) for n in names) / len(names)
        z, zs = rec("zero"), rec("zero.sups")
        n, ns, o, os_ = rec("n"), rec("n.sups"), rec("o"), rec("o.sups")
        print(f"{m}: figures {wide(FIGURES, lambda n: n + '.sups'):.2f} times as wide as theirs "
              f"(RATIO {RATIO:.2f}), 0's side {across(zs):.0f} and top/bottom {up(zs):.0f} "
              f"(the 0's {across(z):.0f} / {up(z):.0f}; contrast "
              f"{(up(zs) / across(zs)) / (up(z) / across(z)):.2f}, CONTRAST {CONTRAST[m]:.2f}); "
              f"letters {wide([l for l in LETTERS if l not in NARROW], lambda n: n + '.sups'):.2f}, "
              f"n's stem {across(ns):.0f} (n {across(n):.0f}), o's top/bottom {up(os_):.0f} "
              f"(o {up(o):.0f}); º {ratio(box('ordmasculine'), box('o')):.2f} "
              f"(ORDINAL_RATIO {ORDINAL_RATIO[m]:.2f})")


def main(paths):
    import spacing
    masters = {re.search(r"-(\w+)\.ufo", p).group(1): p for p in paths}
    fonts = {m: ufoLib2.Font.open(p) for m, p in masters.items()}
    changed = apply_all(fonts)
    for m, path in masters.items():
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed.get(m, []):
            glyph_set.writeGlyph(name, fonts[m][name], fonts[m][name].drawPoints)
        print(f"{path}: {len(changed.get(m, []))} superscripts built ({m})")
    # What follows in tools/to_ufo.py: the sides, then the composites and kerning.
    spacing.main(paths)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        check(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source"))
    else:
        main(sys.argv[1:])
