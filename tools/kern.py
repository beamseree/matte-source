"""Kern t and f so their crossbars don't touch in tt, tf, ft and ff.

Inter's kerning pulls these pairs together, and our crossbars are longer than Inter's
(tools/redraw.py), so they met or overlapped (Regular: tt 0, tf -4, ft -72, ff -36 units
apart). Each pair gets a glyph-to-glyph value that leaves BAR_GAP between the bars in every
master, measured inside both bars. Glyph pairs rather than groups, because Inter's t and f
kerning groups also hold letters without these crossbars; accented t's and f's keep the
group kerning. Only kerning.plist is written. Running it again changes nothing.

Usage: python tools/kern.py source/PlaceholderSans-*.ufo
"""

import os
import re
import sys

import ufoLib2
from fontTools.misc import plistlib
from fontTools.pens.recordingPen import DecomposingRecordingPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

BAR_GAP = 60  # units between the bars; the user chose it over 30 and 100
PAIRS = (("t", "t"), ("t", "f"), ("f", "t"), ("f", "f"))


def group(font, name, side):
    return next((g for g, members in font.groups.items()
                 if g.startswith(f"public.kern{side}.") and name in members), None)


def kerning(font, a, b):
    """The kerning between glyphs a and b, by the UFO's order of precedence."""
    ga, gb = group(font, a, 1), group(font, b, 2)
    for key in ((a, b), (a, gb), (ga, b), (ga, gb)):
        if key in font.kerning:
            return font.kerning[key]
    return 0


def bar(font, name, y):
    """Left and right ends of a glyph's ink at height y: its crossbar, at BAR_ROWS."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    runs = strokes.cut(rec.replay, y + strokes.EPS)
    return runs[0][0], runs[-1][1]


def apply(ufo, master):
    """Kern PAIRS in `ufo`; returns the pairs whose value changed."""
    y = strokes.BAR_ROWS[master]
    changed = {}
    for a, b in PAIRS:
        k = kerning(ufo, a, b)
        gap = ufo[a].width + k + bar(ufo, b, y)[0] - bar(ufo, a, y)[1]
        value = round(k + BAR_GAP - gap)
        if ufo.kerning.get((a, b)) != value:
            ufo.kerning[(a, b)] = value
            changed[(a, b)] = value
    return changed


def main(paths):
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        changed = apply(ufoLib2.Font.open(path), master)
        plist = f"{path}/kerning.plist"
        with open(plist, "rb") as f:
            data = plistlib.load(f)
        for (a, b), value in changed.items():
            data.setdefault(a, {})[b] = value
        with open(plist, "wb") as f:
            plistlib.dump(data, f)
        print(f"{path}: {', '.join(f'{a}{b} {v}' for (a, b), v in changed.items()) or 'nothing'} kerned ({master})")


if __name__ == "__main__":
    main(sys.argv[1:])
