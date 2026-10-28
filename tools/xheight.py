"""Bring the glyphs tools/derive.py missed down to the x-height, at the lowercase weight.

derive.py lowered the x-height from Inter's 1118 to 1076 (and, in Black, made the lowercase
stems lighter than the capitals') only in glyphs whose character is lowercase and that
have no .sc suffix. So the small capitals (h.sc, t.sc, m.sc ...), pecyrillicturn and the
hook parts kept Inter's 1118 and, in Black, the capitals' stems (h.sc 374 against l's 353),
and so did the glyphs built on them: Cyrillic н т м я ц џ ң ҥ ӈ ӊ ӎ ҭ ҵ, п (pecyrillicturn
turned over, which put its foot 42 units below the baseline) and the IPA small capitals
ɪ ɴ ɶ ʀ ʁ ʏ ʜ ʟ ᴀ ᴍ ᴛ ɢ ʛ. Some anchors were missed too: the turned letters' top anchors
(ɐ ǝ ɯ ɹ ʌ ʍ ɥ ʞ ʇ, and so ə and ӛ) sat at 1118 or 1160, which put ӛ's dieresis 84 units above
ӧ's, and the hook part's attaching anchor at 1118, which dropped the hook 42 units onto the
lowered anchor of k, n, p, a, g and q in ƙ ɦ ɧ ƥ ɗ ɠ ʠ. And ʒ and ӡ are the capital Ʒ moved down
so that its top met Inter's x-height. So:

- LOWER's points and anchors take derive.py's vertical map (the baseline and ascender stay,
  1118 goes to our x-height and Inter's 14-unit overshoot to our 25), in every master.
- In Black, each glyph in STEMS is mixed in x between the Regular and Black masters, as
  derive.py compensates stems, until its stem (the first ink run on the line STEMS gives) is
  Regular's times l's Black-to-Regular ratio. BORROW's glyphs mix their own contours as the
  glyph named does. The left edge (of the first component's ink, in a glyph with
  components) and both sidebearings stay.
- ANCHORS go to the x-height, and ʒ's capital Ʒ moves down so its top meets it.

The glyphs built on these follow through tools/accents.py, so run this before tools/spacing.py
and tools/accents.py. Running it again changes nothing.

Usage: python tools/xheight.py source/PlaceholderSans-*.ufo
"""

import os
import re
import sys

import ufoLib2
from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

INTER_XHEIGHT = 1118
INTER_OVERSHOOT = 14
OVERSHOOT = 25      # derive.py's xh_overshoot
ASCENDER = 1490

LOWER = ("a.sc", "g.sc", "h.sc", "i.sc", "l.sc", "m.sc", "n.sc", "oe.sc", "r.sc", "rinv.sc",
         "t.sc", "y.sc", "pecyrillicturn", "enghecyrillic", "tetsecyrillic",
         "_part.top_r_hook_g_sc")

# The line each glyph's stem is measured on (its first ink run there is a stem or, in
# a.sc and g.sc, a diagonal or the round side), and the line l's is.
STEMS = {"a.sc": 450, "g.sc": 450, "h.sc": 150, "i.sc": 450, "l.sc": 450, "m.sc": 560,
         "n.sc": 560, "oe.sc": 450, "r.sc": 150, "rinv.sc": 450, "t.sc": 450, "y.sc": 150,
         "pecyrillicturn": 450, "_part.top_r_hook": 1100}
L_LINE = 450

# Contours drawn on one of STEMS's glyphs (ҥ's bar on н's stem, ҵ's on ц's, ʛ's hook on ɢ's
# side), mixed as that glyph is.
BORROW = {"enghecyrillic": "h.sc", "tetsecyrillic": "pecyrillicturn",
          "_part.top_r_hook_g_sc": "g.sc"}

ANCHORS = {"aturn": "top", "aturn.1": "top", "aturn.2": "top", "eturn": "top", "mturn": "top",
           "mturndescend": "top", "rturn": "top", "rturnrthook": "top", "vturn": "top",
           "wturn": "top", "hturn": "top", "kturn": "top", "tturn": "top",
           "_part.top_r_hook": "_topr"}

EZH = ("dzeabkhasiancyrillic", "Dzeabkhasiancyrillic")


def ymap(y, xheight):
    """derive.py's lowercase vertical map."""
    zones = [(0, 0), (INTER_XHEIGHT, xheight), (INTER_XHEIGHT + INTER_OVERSHOOT, xheight + OVERSHOOT),
             (ASCENDER, ASCENDER)]
    if y <= 0 or y >= ASCENDER:
        return y
    for (a, fa), (b, fb) in zip(zones, zones[1:]):
        if y <= b:
            return fa + (y - a) * (fb - fa) / (b - a)
    return y


def lowered(ufo):
    """Whether LOWER already takes the x-height: h.sc's top is our x-height, not Inter's."""
    return max(p.y for c in ufo["h.sc"].contours for p in c) != INTER_XHEIGHT


def stem(ufo, name):
    rec = DecomposingRecordingPen(ufo)
    ufo[name].draw(rec)
    left, right = strokes.cut(rec.replay, STEMS.get(name, L_LINE) + strokes.EPS)[0]
    return right - left


def left_edge(ufo, glyph):
    """The x that stays put: the first component's left ink edge, else the glyph's."""
    if glyph.components:
        c = glyph.components[0]
        b = ufo[c.baseGlyph].getBounds(ufo)
        return Transform(*c.transformation).transformPoint((b.xMin, b.yMin))[0]
    return glyph.getBounds(ufo).xMin


def mix_factors(black, regular):
    """{name: f}: Black's x = Regular's + f * (Black's - Regular's), for each glyph to mix."""
    ratio = stem(black, "l") / stem(regular, "l")
    f = {}
    for name in STEMS:
        r, b = stem(regular, name), stem(black, name)
        if abs(b - r * ratio) >= 1:
            f[name] = (r * ratio - r) / (b - r)
    for name, base in BORROW.items():
        if base in f:
            f[name] = f[base]
    return f


def mix(black, regular, name, f):
    """Mix one Black glyph's contours and anchors toward Regular's, keeping its left edge and
    sidebearings."""
    gb, gr = black[name], regular[name]
    before = gb.getBounds(black)
    ab, ar = left_edge(black, gb), left_edge(regular, gr)
    for cb, cr in zip(gb.contours, gr.contours):
        for pb, pr in zip(cb, cr):
            pb.x = otRound(ab + (pr.x - ar) + f * ((pb.x - ab) - (pr.x - ar)))
    anchors_r = {a.name: a for a in gr.anchors}
    for a in gb.anchors:
        if a.name in anchors_r:
            r = anchors_r[a.name]
            a.x = otRound(ab + (r.x - ar) + f * ((a.x - ab) - (r.x - ar)))
    return before


def apply(ufo, master, regular=None):
    """Fix the glyphs in `ufo` (Black also needs the Regular master); returns those changed."""
    xheight = ufo.info.xHeight
    changed = set()
    if not lowered(ufo):
        for name in LOWER:
            glyph = ufo[name]
            for c in glyph.contours:
                for p in c:
                    p.y = otRound(ymap(p.y, xheight))
            for a in glyph.anchors:
                a.y = otRound(ymap(a.y, xheight))
            changed.add(name)
    # Black's points have Black's heights, so a slanted or curved stem doesn't come out at
    # its target in one mix; a second (or third) gets within a unit.
    for _ in range(4 if master == "Black" else 0):
        f = mix_factors(ufo, regular)
        if not f:
            break
        order = [n for n in f if n not in BORROW] + [n for n in f if n in BORROW]
        before = {name: mix(ufo, regular, name, f[name]) for name in order}
        for name in order:   # keep the right sidebearing, once every outline has moved
            ufo[name].width += otRound(ufo[name].getBounds(ufo).xMax - before[name].xMax)
        changed |= set(order)
    for name, anchor in ANCHORS.items():
        for a in ufo[name].anchors:
            if a.name == anchor and a.y != xheight:
                a.y = xheight
                changed.add(name)
    glyph, base = EZH
    c = ufo[glyph].components[0]
    dy = xheight - ufo[base].getBounds(ufo).yMax - c.transformation[5]
    if dy:
        t = c.transformation
        c.transformation = Transform(t[0], t[1], t[2], t[3], t[4], t[5] + dy)
        changed.add(glyph)
    return sorted(changed)


def main():
    # Black is mixed against Regular as LOWER has left it, so Regular goes first.
    order = ("Thin", "Regular", "Black")
    paths = sorted(sys.argv[1:], key=lambda p: order.index(re.search(r"-(\w+)\.ufo", p).group(1)))
    fonts = {re.search(r"-(\w+)\.ufo", p).group(1): ufoLib2.Font.open(p) for p in paths}
    regular = fonts.get("Regular") or ufoLib2.Font.open(
        re.sub(r"-\w+\.ufo", "-Regular.ufo", paths[0]))
    if "Regular" not in fonts:
        apply(regular, "Regular")
    for path, (master, ufo) in zip(paths, fonts.items()):
        changed = apply(ufo, master, regular)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {len(changed)} glyphs changed ({master})")


if __name__ == "__main__":
    main()
