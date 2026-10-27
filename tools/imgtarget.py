"""Turn a screenshot of the two mockup pangrams into per-letter targets in font units.

Like tools/svgtarget.py, but for a raster image (light text on a dark background).
Edges are found to sub-pixel precision from anti-aliasing coverage, so 2-3 px
strokes still measure to a fraction of a pixel.

With --stem N, the targets are re-expressed for strokes N units thick: every letter
keeps its skeleton (stroke centre lines) and loses (measured stem - N) / 2 of ink on
each side, which widens the gaps by the same amount. Use it when the image is a
shape reference but the master keeps its own stroke weight.

Usage: python tools/imgtarget.py <image> [--stem N] > reference/targets-<master>.json
"""

import argparse
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

LINES = ["quickbrownfoxjumpsoverthelazydog", "QUICKBROWNFOXJUMPSOVERTHELAZYDOG"]


def bands(cov):
    rows = (cov > 0.5).any(1)
    out, start = [], None
    for y, v in enumerate(rows):
        if v and start is None:
            start = y
        if not v and start is not None:
            out.append((start, y))
            start = None
    if start is not None:
        out.append((start, len(rows)))
    return out


def edges(profile):
    """Sub-pixel [lo, hi) extent of a coverage profile (max coverage per column/row)."""
    idx = np.nonzero(profile > 0.02)[0]
    i, j = idx[0], idx[-1]
    return i + 1 - profile[i], j + profile[j]


def letters(cov, y0, y1, text):
    band = cov[max(0, y0 - 6):y1 + 6]
    off = max(0, y0 - 6)
    lab, _ = ndimage.label(band > 0.25)
    objs = [(sl, k + 1) for k, sl in enumerate(ndimage.find_objects(lab))]
    small = lambda sl: sl[0].stop - sl[0].start < (y1 - y0) * 0.2
    merged = [{"labels": [k], "sl": sl} for sl, k in objs if not small(sl)]
    merged.sort(key=lambda m: m["sl"][1].start)
    # i/j dots join the letter they overlap most horizontally
    for sl, k in objs:
        if small(sl):
            overlap = lambda m: min(sl[1].stop, m["sl"][1].stop) - max(sl[1].start, m["sl"][1].start)
            max(merged, key=overlap)["labels"].append(k)
    assert len(merged) == len(text), (text, len(merged))
    out = []
    for m, c in zip(merged, text):
        mask = np.isin(lab, m["labels"])
        mask = ndimage.binary_dilation(mask, iterations=2)
        part = np.where(mask, band, 0)
        x0, x1 = edges(part.max(0))
        t0, t1 = edges(part.max(1))
        out.append({"char": c, "x0": x0, "x1": x1, "top": t0 + off, "bottom": t1 + off,
                    "ink": float(part.sum()), "part": part, "off": off})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--stem", type=float)
    args = ap.parse_args()
    im = np.asarray(Image.open(args.image).convert("L")).astype(float)
    bg = np.median(im)
    cov = np.clip((im - bg) / (im.max() - bg), 0, 1)
    b = bands(cov)
    result = {}
    stems = {}
    for key, (y0, y1), text in zip(["lower", "upper"], [b[0], b[-1]], LINES):
        ls = letters(cov, y0, y1, text)
        l = ls[text.lower().index("l")]
        baseline = l["bottom"]
        scale = 1490 / (l["bottom"] - l["top"])
        if key == "upper":
            # horizontal stem: ink of the H between its stems, per column
            h = ls[text.index("H")]
            prof = h["part"].sum(0)
            cols = np.nonzero(prof > 0.02)[0]
            mid = cols[(prof[cols] < prof[cols].max() * 0.5)]
            inner = mid[(mid > cols[0] + 3) & (mid < cols[-1] - 3)]
            stems["h_upper"] = float(prof[inner].mean()) * scale
        stem_letter = ls[text.index("l" if key == "lower" else "I")]
        measured = (stem_letter["x1"] - stem_letter["x0"]) * scale
        shrink = (measured - args.stem) / 2 if args.stem else 0.0
        stems["measured_" + key] = measured
        result[key] = {
            "scale": scale,
            "text": text,
            "shrink_each_side": round(shrink, 1),
            "letters": [
                {"char": d["char"],
                 "xMin": round(d["x0"] * scale + shrink, 1), "xMax": round(d["x1"] * scale - shrink, 1),
                 "yMin": round((baseline - d["bottom"]) * scale, 1),
                 "yMax": round((baseline - d["top"]) * scale, 1)}
                for d in ls
            ],
        }
    result["stems"] = {k: round(v, 1) for k, v in stems.items()}
    json.dump(result, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
