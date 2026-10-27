"""Fit tools/derive.py parameters to the mockup (reference/targets.json).

Each round: derive + build, shape both mockup lines with HarfBuzz at the default
weight (Regular), then nudge per-letter ink factors, stem weights, sidebearing
factors and the word space toward the mockup. Writes reference/params.json.

Usage: python tools/fit.py [rounds]
"""

import json
import subprocess
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

TTF = "build/PlaceholderSans-VF.ttf"
PARAMS = "reference/params.json"
TARGETS = json.load(open("reference/targets.json"))
SENTENCES = {"lower": "quick brown fox jumps over the lazy dog",
             "upper": "QUICK BROWN FOX JUMPS OVER THE LAZY DOG"}
SINGLE_STEM = {"i", "l", "I", "j"}  # width is the stem; set by weight_v, not ink
COMPOSITES = {"d": "b", "q": "p"}   # mirrored b / p in Inter's source
HELD = {"t": 1.12, "f": 0.95}       # shape differs from Inter: draw by hand
RIDGE = 0.5


def shape(text):
    blob = hb.Blob.from_file_path(TTF)
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True})
    x, letters = 0, []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ext = font.get_glyph_extents(info.codepoint)
        if ext.width:
            x0 = x + pos.x_offset + ext.x_bearing
            letters.append((x0, x0 + ext.width))
        x += pos.x_advance
    return letters


def stems():
    f = TTFont(TTF)
    glyf = f["glyf"]
    def coords(name, axis):
        g = glyf[name]
        return sorted(set(c[axis] for c in g.getCoordinates(glyf)[0]))
    l = coords("l", 0)
    E = coords("E", 1)
    return l[-1] - l[0], E[1] - E[0]


def build(params):
    json.dump(params, open(PARAMS, "w"), indent=1, sort_keys=True)
    subprocess.run(["tools/build.sh", "--derive", PARAMS], check=True, stdout=subprocess.DEVNULL)


def report(params, update):
    ink_err, gap_err = [], []
    for key, text in SENTENCES.items():
        target = TARGETS[key]["letters"]
        mine = shape(text)
        assert len(mine) == len(target), (key, len(mine), len(target))
        words = [len(w) for w in text.split()]
        word_end = set()
        n = 0
        for w in words:
            n += w
            word_end.add(n - 1)
        # ink widths
        ratios = {}
        for t, (x0, x1) in zip(target, mine):
            tw, mw = t["xMax"] - t["xMin"], x1 - x0
            ink_err.append(abs(mw - tw))
            ratios.setdefault(t["char"], []).append(tw / mw)
        # gaps
        in_t = in_m = sp_t = sp_m = 0.0
        for i in range(len(target) - 1):
            gt = target[i + 1]["xMin"] - target[i]["xMax"]
            gm = mine[i + 1][0] - mine[i][1]
            gap_err.append(abs(gm - gt))
            if i in word_end:
                sp_t += gt; sp_m += gm
            else:
                in_t += gt; in_m += gm
        if update:
            for c, rs in ratios.items():
                if c in SINGLE_STEM or c in COMPOSITES:
                    continue
                if c in HELD:
                    params["ink"][c] = HELD[c]
                    continue
                r = sum(rs) / len(rs)
                params["ink"][c] = round(params["ink"].get(c, 1.0) * r, 4)
            k = "spacing_upper" if key == "upper" else "spacing"
            params[k] = round(params[k] * in_t / in_m, 4)
            if key == "lower":
                space = 576 * params["space"]
                params["space"] = round((space + (sp_t - sp_m) / len(word_end - {len(target) - 1})) / 576, 4)
    lw, ew = stems()
    if update:
        params["weight_v"]["Regular"] = round(params["weight_v"]["Regular"] * 194.5 / lw, 4)
        params["weight_h"]["Regular"] = round(params["weight_h"]["Regular"] * 190.4 / ew, 4)
    print(f"  ink error mean {sum(ink_err)/len(ink_err):5.1f} max {max(ink_err):5.0f} | "
          f"gap error mean {sum(gap_err)/len(gap_err):5.1f} max {max(gap_err):5.0f} | "
          f"l stem {lw} (194.5)  E arm {ew} (190.4)")


def fit_sidebearings(params):
    """Least-squares per-letter sidebearing nudges so in-word gaps match the mockup."""
    import numpy as np
    rows, rhs, names = [], [], []
    def var(c, side):
        # d and q are mirrored b and p: their left is the base's right, and vice versa
        if c in COMPOSITES:
            c, side = COMPOSITES[c], 1 - side
        key = (c, side)
        if key not in names:
            names.append(key)
        return names.index(key)
    pairs = []
    for key, text in SENTENCES.items():
        target, mine = TARGETS[key]["letters"], shape(text)
        s = text.replace(" ", "")
        ends, n = set(), 0
        for w in text.split():
            n += len(w); ends.add(n - 1)
        for i in range(len(s) - 1):
            if i in ends:
                continue
            err = (mine[i + 1][0] - mine[i][1]) - (target[i + 1]["xMin"] - target[i]["xMax"])
            pairs.append((var(s[i], 1), var(s[i + 1], 0), -err))
    A = np.zeros((len(pairs) + len(names), len(names)))
    b = np.zeros(len(pairs) + len(names))
    for r, (i, j, e) in enumerate(pairs):
        A[r, i] += 1; A[r, j] += 1; b[r] = e
    A[len(pairs):] = np.eye(len(names)) * RIDGE
    x = np.linalg.lstsq(A, b, rcond=None)[0]
    for (c, side), v in zip(names, x):
        cur = params["sb"].setdefault(c, [0, 0])
        cur[side] = round(cur[side] + float(v))


def main(rounds=4):
    try:
        params = json.load(open(PARAMS))
    except FileNotFoundError:
        params = {"xheight": round(1076 / 1118, 4), "weight_v": {"Regular": 1.07},
                  "weight_h": {"Regular": 1.13}, "ink": {}, "spacing": 0.82,
                  "spacing_upper": 0.82, "space": 0.85}
    params.setdefault("sb", {})
    for r in range(int(rounds)):
        build(params)
        print(f"round {r + 1}")
        report(params, update=True)
    for r in range(2):
        build(params)
        print(f"spacing round {r + 1}")
        fit_sidebearings(params)
    build(params)
    print("final")
    report(params, update=False)


if __name__ == "__main__":
    main(*sys.argv[1:])
