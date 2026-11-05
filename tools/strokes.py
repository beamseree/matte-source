"""Measure horizontal stroke widths on scanlines: our glyphs against the mockups.

On a scanline at height y (font units) a letter is a list of ink runs (left, right),
in font units from the letter's left ink edge. Our glyphs are read from source/*.ufo
(components decomposed) and cut exactly; so is the mockup SVG. The screenshots give
each run from anti-aliasing coverage: its width is the coverage summed across the run
and its position the coverage-weighted centre, which holds for slanted edges too.
An image row averages one pixel of height (about 24 units).

Usage: python tools/strokes.py <Thin|Regular|Black> <char> <y> [<y> ...]
       python tools/strokes.py --check     # the letters tools/redraw.py fixes
"""

import os
import sys
from functools import lru_cache
from math import comb

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import imgtarget  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MOCKUPS = {"Regular": "reference/mockup.svg", "Thin": "reference/mockup-thin.webp",
           "Black": "reference/mockup-black.svg"}
EPS = 0.01  # keeps scanlines off vertices and flat segments


class CrossingsPen(BasePen):
    """Collects (x, direction) where the outline crosses the line y = Y."""

    def __init__(self, y):
        super().__init__(None)
        self.y, self.hits = y, []

    def _cut(self, pts):
        # Bezier of any degree in power form, solved for y(t) = Y
        n = len(pts) - 1
        def poly(i):
            c = np.zeros(n + 1)
            for k, p in enumerate(pts):
                for j in range(n - k + 1):
                    c[k + j] += comb(n, k) * comb(n - k, j) * (-1) ** j * p[i]
            return c[::-1]  # highest power first
        py, px = poly(1), poly(0)
        py[-1] -= self.y
        for t in np.roots(py) if np.any(py[:-1]) else []:
            if abs(t.imag) > 1e-9 or not 0 <= t.real < 1:
                continue
            t = t.real
            dy = np.polyval(np.polyder(py), t)
            if dy:
                self.hits.append((float(np.polyval(px, t)), 1 if dy > 0 else -1))

    def _moveTo(self, pt):
        self.start = pt

    def _lineTo(self, pt):
        self._cut([self._getCurrentPoint(), pt])

    def _curveToOne(self, p1, p2, p3):
        self._cut([self._getCurrentPoint(), p1, p2, p3])

    def _qCurveToOne(self, p1, p2):
        self._cut([self._getCurrentPoint(), p1, p2])

    def _closePath(self):
        if self._getCurrentPoint() != self.start:
            self._cut([self._getCurrentPoint(), self.start])


def cut(replay, y):
    """Ink runs (nonzero winding) of an outline on the line y."""
    pen = CrossingsPen(y)
    replay(pen)
    runs, wind, start = [], 0, None
    for x, d in sorted(pen.hits):
        if wind == 0:
            start = x
        wind += d
        if wind == 0:
            runs.append((start, x))
    return runs


@lru_cache(None)
def ufo(master):
    import ufoLib2
    return ufoLib2.Font.open(os.path.join(ROOT, f"source/PlaceholderSans-{master}.ufo"))


def ours(master, char, y, font=None):
    """Runs of our glyph at y, from its left ink edge."""
    font = font or ufo(master)
    rec = DecomposingRecordingPen(font)
    font[char].draw(rec)
    x0 = font[char].getBounds(font).xMin
    return [(a - x0, b - x0) for a, b in cut(rec.replay, y + EPS)]


@lru_cache(None)
def svg_letters(path):
    import to_ufo
    return to_ufo.svg_letters(path)


@lru_cache(None)
def img_letters(path):
    from PIL import Image
    im = np.asarray(Image.open(path).convert("L")).astype(float)
    bg = np.median(im)
    cov = np.clip((im - bg) / (im.max() - bg), 0, 1)
    b = imgtarget.bands(cov)
    out = {}
    for (y0, y1), text in zip([b[0], b[-1]], imgtarget.LINES):
        ls = imgtarget.letters(cov, y0, y1, text)
        l = ls[text.lower().index("l")]
        baseline, scale = l["bottom"], 1490 / (l["bottom"] - l["top"])
        for d in ls:
            out.setdefault(d["char"], (d, baseline, scale))
    return out


def row_runs(row):
    """Runs in one row of coverage, as (left, right) in pixels, split at dips below 0.5."""
    core = row > 0.5
    idx = np.nonzero(row > 0.02)[0]
    if not len(idx):
        return []
    cores, start = [], None
    for i in range(idx[0], idx[-1] + 2):
        on = i < len(row) and core[i]
        if on and start is None:
            start = i
        if not on and start is not None:
            cores.append([start, i])
            start = None
    if not cores:
        return []
    # give each partial column to the nearer core; gaps split at their lowest column
    bounds = [idx[0]]
    for (_, e), (s, _) in zip(cores, cores[1:]):
        bounds.append(e + int(np.argmin(row[e:s])))
    bounds.append(idx[-1] + 1)
    out = []
    for a, b in zip(bounds, bounds[1:]):
        c = row[a:b]
        w = c.sum()
        mid = (c * (np.arange(a, b) + 0.5)).sum() / w
        out.append((mid - w / 2, mid + w / 2))
    return out


def mockup(master, char, y):
    """Runs of the mockup's letter at y, from its left ink edge."""
    path = os.path.join(ROOT, MOCKUPS[master])
    if path.endswith(".svg"):
        rec, (x0, _, _, _), baseline, s = svg_letters(path)[char]
        return [((a - x0) * s, (b - x0) * s) for a, b in cut(rec.replay, baseline - (y + EPS) / s)]
    d, baseline, s = img_letters(path)[char]
    r = int(np.floor(baseline - y / s)) - d["off"]
    if not 0 <= r < len(d["part"]):
        return []
    return [((a - d["x0"]) * s, (b - d["x0"]) * s) for a, b in row_runs(d["part"][r])]


def widths(runs):
    return [round(b - a) for a, b in runs]


def show(runs):
    return " ".join(f"[{a:.0f} {b:.0f}]" for a, b in runs)


def t_bar(runs_stem, runs_bar):
    """How far the t crossbar reaches past the stem's left and right edges."""
    (s0, s1), (b0, b1) = runs_stem[0], runs_bar[0]
    return [round(s0 - b0), round(b1 - s1)]


def top_contour(rec, y_down=False):
    """Bounds of the highest contour in a recorded outline (an i/j dot)."""
    boxes, cur = [], None
    for op, args in rec.value:
        if op == "moveTo":
            cur = RecordingPen()
        getattr(cur, op)(*args)
        if op in ("closePath", "endPath"):
            bp = BoundsPen(None)
            cur.replay(bp)
            boxes.append(bp.bounds)
    return min(boxes, key=lambda b: b[1]) if y_down else max(boxes, key=lambda b: b[1])


def dot(master, char, source):
    """(width, height, top, centre minus stem centre) of an i/j dot."""
    if source == "ours":
        font = ufo(master)
        rec = DecomposingRecordingPen(font)
        font[char].draw(rec)
        x0, y0, x1, y1 = top_contour(rec)
        left = font[char].getBounds(font).xMin
        s = ours(master, char, 600)[-1]
        return [round(x1 - x0), round(y1 - y0), round(y1), round((x0 + x1 - 2 * left - s[0] - s[1]) / 2)]
    path = os.path.join(ROOT, MOCKUPS[master])
    s = mockup(master, char, 600)[-1]
    if path.endswith(".svg"):
        rec, (lx0, _, _, _), baseline, sc = svg_letters(path)[char]
        x0, y0, x1, y1 = top_contour(rec, y_down=True)
        x0, x1 = (x0 - lx0) * sc, (x1 - lx0) * sc
        return [round(x1 - x0), round((y1 - y0) * sc), round((baseline - y0) * sc),
                round((x0 + x1 - s[0] - s[1]) / 2)]
    d, baseline, sc = img_letters(path)[char]
    p = d["part"][: int(baseline - 1076 / sc) - d["off"] - 2]   # rows above the x-height
    rows = np.arange(len(p)) + 0.5
    col = p[:, int(np.argmax(p.sum(0)))]                      # the dot's tallest column
    mid, h = (col * rows).sum() / col.sum(), col.sum()
    cx = (p.sum(0) * (np.arange(p.shape[1]) + 0.5)).sum() / p.sum()
    return [round(p.sum(1).max() * sc), round(h * sc), round((baseline - d["off"] - mid + h / 2) * sc),
            round((cx - d["x0"]) * sc - (s[0] + s[1]) / 2)]


# What tools/straighten.py and tools/redraw.py fixed: horizontal widths on these rows
# (masters whose strokes match their mockup), the t crossbar's reach past the stem
# (every master), the i/j dots, and the Z/z top bars' insets (every master).
# x/X rows sit below, through and above the crossing; z/Z rows also cut both bars. Q's
# tail is left out: its thickness and angle are the mockups' (redraw.py's POLYGONS), but it
# starts nearer the bowl and reaches further below the baseline on purpose (Q_TAIL_START,
# Q_TAIL_DEPTH), so no row outside the bowl cuts it where it cuts the mockups'.
ROWS = [("x", 150), ("x", 300), ("x", 560), ("x", 850), ("x", 900),
        ("X", 300), ("X", 450), ("X", 770), ("X", 1100), ("X", 1200),
        ("z", 80), ("z", 550), ("z", 1000), ("Z", 80), ("Z", 745), ("Z", 1420),
        ("N", 745), ("K", 1200), ("K", 300), ("k", 900), ("k", 150),
        ("w", 300), ("w", 575), ("w", 800),
        ("A", 150), ("A", 450), ("A", 1100), ("V", 300), ("V", 1200), ("v", 250), ("v", 900),
        ("W", 300), ("W", 1200), ("M", 300), ("M", 1300), ("Y", 300), ("Y", 1200),
        ("E", 750), ("E", 1300), ("F", 750), ("F", 1300)]
BAR_ROWS = {"Thin": 1050, "Regular": 990, "Black": 940}  # inside both crossbars
# Rows inside z's and Z's bottom and top bars: the mockups' (full rows of the screenshot,
# whose strokes are about 105 units) and ours (20 units in from each edge, inside Thin's).
ZED_ROWS = {"Z": ((25, 48), (1406, 1430, 1454)), "z": ((41, 65), (997, 1021, 1045))}
ZED_OURS = {"Z": ((20,), (1470,)), "z": ((20,), (1056,))}


def bar_insets(runs_bottom, runs_top):
    """How far the top bar's ends sit in from the bottom bar's (left, right), averaged over rows."""
    b = np.mean([r[0] for r in runs_bottom], axis=0)
    t = np.mean([r[0] for r in runs_top], axis=0)
    return [round(t[0] - b[0]), round(b[1] - t[1])]


def check():
    def pct(o, m):
        return " ".join(f"{100 * (a - b) / b:+.1f}%" for a, b in zip(o, m)) if len(o) == len(m) else "-"
    for master in ("Regular", "Black"):
        for char, y in ROWS:
            m, o = widths(mockup(master, char, y)), widths(ours(master, char, y))
            print(f"{master:7s} {char} y={y:<4d}  ours {str(o):22s} mockup {str(m):22s} {pct(o, m)}")
    for master in ("Thin", "Regular", "Black"):
        y = BAR_ROWS[master]
        m = t_bar(mockup(master, "t", 600), mockup(master, "t", y))
        o = t_bar(ours(master, "t", 600), ours(master, "t", y))
        print(f"{master:7s} t bar past stem L/R  ours {str(o):12s} mockup {str(m):12s} {pct(o, m)}")
    for master in ("Thin", "Regular", "Black"):
        for char, (yb, yt) in ZED_ROWS.items():
            m = bar_insets([mockup(master, char, y) for y in yb], [mockup(master, char, y) for y in yt])
            ob, ot = ZED_OURS[char]
            o = bar_insets([ours(master, char, y) for y in ob], [ours(master, char, y) for y in ot])
            print(f"{master:7s} {char} top bar inset L/R  ours {str(o):12s} mockup {str(m):12s} "
                  f"diff {o[0] - m[0]:+d} {o[1] - m[1]:+d}")
    for master in ("Thin", "Regular", "Black"):
        for char in "ij":
            print(f"{master:7s} {char} dot w/h/top/off-centre  ours {dot(master, char, 'ours')}"
                  f"  mockup {dot(master, char, 'mockup')}")


def main(master, char, *ys):
    for y in map(float, ys):
        m, o = mockup(master, char, y), ours(master, char, y)
        print(f"y={y:5.0f}  mockup {widths(m)} {show(m)}")
        print(f"         ours   {widths(o)} {show(o)}")


if __name__ == "__main__":
    check() if sys.argv[1:] == ["--check"] else main(*sys.argv[1:])
