"""Fit one master's tools/derive.py parameters to a mockup.

Each round: derive from Inter and build into build/fit/ (source/ is not touched),
shape both mockup lines with HarfBuzz at the master's weight, then nudge per-letter
ink factors, sidebearing factors and the word space toward the targets. The Regular
master also fits its stem weights; other masters do with --fit-stems, using the stems
measured in their targets file (stem of l, stem of I, bar of H). Parameters go to reference/params.json: Regular's
at the top level, other masters' under "masters".

With --apply, the fitted master is then written into source/ (only that master's
UFO, with its guides), leaving the other masters and their hand edits alone.

Usage: python tools/fit.py [--master Thin] [--targets reference/targets-thin.json]
                           [--guides reference/mockup-thin.webp] [--rounds 4]
                           [--fit-stems] [--apply]
"""

import argparse
import json
import os
import shutil
import subprocess

import uharfbuzz as hb

PY = ".venv/bin/python"
PARAMS = "reference/params.json"
FIT_DIR = "build/fit"
TTF = f"{FIT_DIR}/PlaceholderSans-VF.ttf"
LOCATION = {"Thin": 100, "Regular": 400, "Black": 900}
SENTENCES = {"lower": "quick brown fox jumps over the lazy dog",
             "upper": "QUICK BROWN FOX JUMPS OVER THE LAZY DOG"}
SINGLE_STEM = {"i", "l", "I", "j"}  # width is the stem; set by weight_v, not ink
COMPOSITES = {"d": "b", "q": "p"}   # mirrored b / p in Inter's source
HELD = {"Regular": {"t": 1.12, "f": 0.95},   # shape differs from Inter: draw by hand
        "Thin": {"t": 1.12}}
RIDGE = 0.5


class Master:
    """Read/write access to one master's parameters inside params.json."""

    def __init__(self, params, name):
        self.params, self.name = params, name
        if name != "Regular":
            own = params.setdefault("masters", {}).setdefault(name, {})
            # start from Regular's fitted values
            own.setdefault("ink", dict(params.get("ink", {})))
            own.setdefault("sb", {k: list(v) for k, v in params.get("sb", {}).items()})
            for k in ("spacing", "spacing_upper", "space"):
                own.setdefault(k, params[k])
            self.store = own
        else:
            params.setdefault("sb", {})
            self.store = params

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value


def shape(text, wght):
    blob = hb.Blob.from_file_path(TTF)
    font = hb.Font(hb.Face(blob))
    font.set_variations({"wght": wght})
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


def stems(wght):
    """Vertical stem (width of "l") at a weight."""
    l = shape("l", wght)[0]
    return l[1] - l[0]


def all_stems(wght):
    """Stem of l, stem of I and bar of H, measured on the built font at a weight."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    font = instantiateVariableFont(TTFont(TTF), {"wght": wght})
    glyf = font["glyf"]
    H = sorted(set(c[1] for c in glyf["H"].getCoordinates(glyf)[0]))
    I = shape("I", wght)[0]
    return {"l": stems(wght), "I": I[1] - I[0], "H": H[2] - H[1]}


def build(params):
    json.dump(params, open(PARAMS, "w"), indent=1, sort_keys=True)
    os.makedirs(FIT_DIR, exist_ok=True)
    shutil.rmtree(f"{FIT_DIR}/features", ignore_errors=True)
    shutil.copytree("vendor/inter/src/features", f"{FIT_DIR}/features")
    run = lambda *a: subprocess.run(a, check=True, stdout=subprocess.DEVNULL)
    run(PY, "-I", "tools/derive.py", "vendor/inter/src/Inter-Roman.glyphspackage",
        f"{FIT_DIR}/derived.glyphspackage", PARAMS)
    run(PY, "-I", "tools/to_ufo.py", f"{FIT_DIR}/derived.glyphspackage",
        f"{FIT_DIR}/PlaceholderSans.designspace")
    with open(f"{FIT_DIR}/fontmake.log", "w") as log:
        subprocess.run([PY, "-m", "fontmake", "-m", f"{FIT_DIR}/PlaceholderSans.designspace",
                        "-o", "variable", "--output-dir", FIT_DIR, "--flatten-components",
                        "--no-production-names"], check=True, stdout=log, stderr=log)


def word_ends(text):
    ends, n = set(), 0
    for w in text.split():
        n += len(w)
        ends.add(n - 1)
    return ends


def report(m, targets, update, fit_stems=False):
    wght = LOCATION[m.name]
    ink_err, gap_err = [], []
    for key, text in SENTENCES.items():
        target, mine = targets[key]["letters"], shape(text, wght)
        assert len(mine) == len(target), (key, len(mine), len(target))
        ends = word_ends(text)
        ratios = {}
        for t, (x0, x1) in zip(target, mine):
            tw, mw = t["xMax"] - t["xMin"], x1 - x0
            ink_err.append(abs(mw - tw))
            ratios.setdefault(t["char"], []).append(tw / mw)
        in_t = in_m = sp_t = sp_m = 0.0
        for i in range(len(target) - 1):
            gt = target[i + 1]["xMin"] - target[i]["xMax"]
            gm = mine[i + 1][0] - mine[i][1]
            gap_err.append(abs(gm - gt))
            if i in ends:
                sp_t += gt; sp_m += gm
            else:
                in_t += gt; in_m += gm
        if update:
            held = HELD.get(m.name, {})
            for c, rs in ratios.items():
                if c in SINGLE_STEM or c in COMPOSITES:
                    continue
                if c in held:
                    m["ink"][c] = held[c]
                    continue
                r = sum(rs) / len(rs)
                m["ink"][c] = round(m["ink"].get(c, 1.0) * r, 4)
            k = "spacing_upper" if key == "upper" else "spacing"
            m[k] = round(m[k] * in_t / in_m, 4)
            if key == "lower":
                space = 576 * m["space"]
                m["space"] = round((space + (sp_t - sp_m) / len(ends - {len(target) - 1})) / 576, 4)
    lw = stems(wght)
    line = (f"  ink error mean {sum(ink_err)/len(ink_err):5.1f} max {max(ink_err):5.0f} | "
            f"gap error mean {sum(gap_err)/len(gap_err):5.1f} max {max(gap_err):5.0f} | l stem {lw}")
    if m.name == "Regular":
        # Regular's weight comes from the mockup SVG; other masters keep Inter's stems
        from fontTools.ttLib import TTFont
        f = TTFont(TTF)
        glyf = f["glyf"]
        E = sorted(set(c[1] for c in glyf["E"].getCoordinates(glyf)[0]))
        ew = E[1] - E[0]
        line += f" (194.5)  E arm {ew} (190.4)"
        if update:
            p = m.params
            p["weight_v"]["Regular"] = round(p["weight_v"]["Regular"] * 194.5 / lw, 4)
            p["weight_h"]["Regular"] = round(p["weight_h"]["Regular"] * 190.4 / ew, 4)
    elif fit_stems:
        st, want = all_stems(wght), targets["stems"]
        want = {"l": want["measured_lower"], "I": want["measured_upper"], "H": want["h_upper"]}
        line += "  " + "  ".join(f"{k} {st[k]} ({want[k]:.0f})" for k in st)
        if update:
            p = m.params
            for key, k in (("weight_v_lower", "l"), ("weight_v", "I"), ("weight_h", "H")):
                p.setdefault(key, {})
                p[key][m.name] = round(p[key].get(m.name, 1.0) * want[k] / st[k], 4)
    print(line)


def fit_sidebearings(m, targets):
    """Least-squares per-letter sidebearing nudges so in-word gaps match the mockup."""
    import numpy as np
    names = []
    def var(c, side):
        # d and q are mirrored b and p: their left is the base's right, and vice versa
        if c in COMPOSITES:
            c, side = COMPOSITES[c], 1 - side
        if (c, side) not in names:
            names.append((c, side))
        return names.index((c, side))
    pairs = []
    for key, text in SENTENCES.items():
        target, mine = targets[key]["letters"], shape(text, LOCATION[m.name])
        s = text.replace(" ", "")
        ends = word_ends(text)
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
        cur = m["sb"].setdefault(c, [0, 0])
        cur[side] = round(cur[side] + float(v))


def apply(name, guides):
    """Write the fitted master into source/, with its guides; other masters stay as they are."""
    args = [PY, "-I", "tools/to_ufo.py", f"{FIT_DIR}/derived.glyphspackage",
            "source/PlaceholderSans.designspace", "--only", name]
    if guides:
        args += ["--guides", f"{name}={guides}"]
    subprocess.run(args, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="Regular", choices=list(LOCATION))
    ap.add_argument("--targets", default="reference/targets.json")
    ap.add_argument("--guides")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--fit-stems", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    targets = json.load(open(args.targets))
    params = json.load(open(PARAMS))
    m = Master(params, args.master)
    for r in range(args.rounds):
        build(params)
        print(f"round {r + 1}")
        report(m, targets, update=True, fit_stems=args.fit_stems)
    for r in range(2):
        build(params)
        print(f"spacing round {r + 1}")
        fit_sidebearings(m, targets)
    build(params)
    print("final")
    report(m, targets, update=False, fit_stems=args.fit_stems)
    if args.apply:
        apply(args.master, args.guides)


if __name__ == "__main__":
    main()
