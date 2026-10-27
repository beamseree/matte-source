"""Turn the mockup SVG into per-letter targets in font units.

The SVG has two lines of outlined text: lowercase on top, capitals below.
Scale comes from the "l" and the capitals both being 1490 units tall (Inter's
ascender and cap height).

Usage: python tools/svgtarget.py reference/mockup.svg > reference/targets.json
"""

import json
import re
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.svgLib.path import parse_path

LINES = [
    ("lower", "quickbrownfoxjumpsoverthelazydog", 50),
    ("upper", "QUICKBROWNFOXJUMPSOVERTHELAZYDOG", 200),
]
NAMES = {c: c for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"}


def main(path):
    svg = open(path).read()
    paths = re.findall(r'<path d="([^"]+)"', svg)
    glyphs = []
    for d in paths:
        rec = RecordingPen()
        parse_path(d, rec)
        bp = BoundsPen(None)
        rec.replay(bp)
        glyphs.append((bp.bounds, rec))
    out = {}
    for key, text, ymax in LINES:
        line = sorted((g for g in glyphs if g[0][1] < ymax and (key == "upper" or g[0][3] < 50)
                       and not (key == "upper" and g[0][1] < 50)), key=lambda g: g[0][0])
        assert len(line) == len(text), (key, len(line))
        baseline = line[[i for i, c in enumerate(text) if c in "lL"][0]][0][3]
        top = line[[i for i, c in enumerate(text) if c in "lL"][0]][0][1]
        scale = 1490 / (baseline - top)
        letters = []
        for c, ((x0, y0, x1, y1), rec) in zip(text, line):
            letters.append({
                "char": c,
                "xMin": round(x0 * scale, 1), "xMax": round(x1 * scale, 1),
                "yMin": round((baseline - y1) * scale, 1), "yMax": round((baseline - y0) * scale, 1),
            })
        out[key] = {"scale": scale, "text": text, "letters": letters}
    json.dump(out, sys.stdout, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
