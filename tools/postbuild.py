"""Finish a built variable font the way Inter's and Google Fonts' release pipelines do.

fontmake leaves out what those pipelines add after it, so tools/build.sh runs this on every
font it builds:

- gasp and prep: the font is unhinted, so gasp asks for smoothing in both directions at
  every size, and prep turns on smart dropout control, which keeps Thin's 46-unit stems
  from breaking up in black-and-white and low-resolution rendering (as gftools
  fix-nonhinting does).
- usWinAscent and usWinDescent cover every glyph at every weight, so Windows GDI clips
  nothing (Inter's 1984/494 cut the Vietnamese stacked capitals' top marks). hhea and
  typo, which set the line height, don't change.
- The OS/2 Unicode and code page ranges are recalculated from the cmap (Inter's claimed
  Hebrew and missed Enclosed Alphanumerics, among others).
- The strikeout's centre is checked against the hyphen's at each master. The positions
  are in each master's fontinfo (openTypeOS2StrikeoutPosition), so varLib varies them in
  MVAR; if the hyphen moves, this says so and gives the values to put there.

Usage: python tools/postbuild.py build/PlaceholderSans-VF.ttf
"""

import sys

from fontTools.pens.boundsPen import BoundsPen, ControlBoundsPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import ttProgram
from fontTools.varLib.models import normalizeValue
from fontTools.varLib.varStore import VarStoreInstancer

GASP = {0xFFFF: 0x000F}  # gridfit, grayscale, symmetric gridfit, symmetric smoothing
PREP = ["PUSHW[]", "511", "SCANCTRL[]", "PUSHB[]", "4", "SCANTYPE[]"]  # smart dropout
STRIKE_TOLERANCE = 1  # units the strikeout's centre may sit from the hyphen's


def locations(font):
    """The axis ends and default, and every 100 between: interpolation is linear between
    masters, so each glyph's extremes fall on one of these as long as the masters do."""
    axis = font["fvar"].axes[0]
    ws = {axis.minValue, axis.defaultValue, axis.maxValue}
    ws |= set(range(100 * -(-int(axis.minValue) // 100), int(axis.maxValue) + 1, 100))
    return [{axis.axisTag: w} for w in sorted(ws)]


def unhinted(font):
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = dict(GASP)
    font["gasp"] = gasp
    prep = newTable("prep")
    prep.program = ttProgram.Program()
    prep.program.fromAssembly(PREP)
    font["prep"] = prep
    font["maxp"].maxStackElements = max(font["maxp"].maxStackElements, 1)


def win_metrics(font):
    """usWinAscent/Descent from every glyph's control box at every location (the box
    head's bounds use, so they're never smaller than head.yMax/yMin)."""
    top, bottom = 0, 0
    for loc in locations(font):
        glyphs = font.getGlyphSet(location=loc)
        for name in font.getGlyphOrder():
            pen = ControlBoundsPen(glyphs)
            glyphs[name].draw(pen)
            if pen.bounds:
                top, bottom = max(top, pen.bounds[3]), min(bottom, pen.bounds[1])
    os2 = font["OS/2"]
    os2.usWinAscent = max(round(top), os2.sTypoAscender)
    os2.usWinDescent = max(round(-bottom), -os2.sTypoDescender)
    return os2.usWinAscent, os2.usWinDescent


def ranges(font):
    os2 = font["OS/2"]
    os2.recalcUnicodeRanges(font)
    os2.recalcCodePageRanges(font)


def strikeout(font):
    """Where the strikeout's centre sits against the hyphen's, at the axis ends and default.
    Returns the masters where it is off, with the position each should have."""
    os2, axis = font["OS/2"], font["fvar"].axes[0]
    triple = (axis.minValue, axis.defaultValue, axis.maxValue)
    records = {}
    if "MVAR" in font:
        records = {r.ValueTag: r.VarIdx for r in font["MVAR"].table.ValueRecord}
    off = []
    for w in triple:
        loc = {axis.axisTag: w}
        deltas = VarStoreInstancer(font["MVAR"].table.VarStore if records else None,
                                   font["fvar"].axes, {axis.axisTag: normalizeValue(w, triple)})
        pos = os2.yStrikeoutPosition + (round(deltas[records["stro"]]) if "stro" in records else 0)
        size = os2.yStrikeoutSize + (round(deltas[records["strs"]]) if "strs" in records else 0)
        glyphs = font.getGlyphSet(location=loc)
        pen = BoundsPen(glyphs)
        glyphs["hyphen"].draw(pen)
        hyphen = (pen.bounds[1] + pen.bounds[3]) / 2
        if abs(pos - size / 2 - hyphen) > STRIKE_TOLERANCE:
            off.append((w, pos, round(hyphen + size / 2)))
    return off


def main(path):
    font = TTFont(path)
    unhinted(font)
    ascent, descent = win_metrics(font)
    ranges(font)
    off = strikeout(font)
    font.save(path)
    print(f"postbuild {path}: gasp + prep, usWinAscent {ascent} usWinDescent {descent}, "
          "Unicode and code page ranges recalculated")
    for w, pos, want in off:
        print(f"  warning: at wght {w:g} the strikeout (top {pos}) isn't centred on the hyphen; "
              f"set that master's openTypeOS2StrikeoutPosition to {want}", file=sys.stderr)


if __name__ == "__main__":
    for path in sys.argv[1:]:
        main(path)
