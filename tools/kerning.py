"""Refit Inter's kerning to our letters and spacing, and keep every pair clear of the next.

Inter's kerning (about 1,400 pairs per master over 277 groups) was made for Inter's shapes
and spacing; tools/derive.py copied it unchanged. Each pair is now measured by its visible
gap: each side's optical sidebearing (its sidebearing plus the profile's white, at most
DEPTH deep, over the two glyphs' height together) plus LAMBDA times how the two shapes meet
beyond that (the white between them, row by row, at most DEPTH past their closest point,
minus the optical sidebearings). DEPTH and LAMBDA are the values that make Inter's own
kerned letter pairs look most even by this measure (CAL).

Our sides are Inter's proportions at our spacing's median fraction of Inter's, or what the
mockups' pairs made them (tools/spacing.py), and kerning mustn't undo that; so each pair
keeps Inter's value scaled to our spacing (the median letter's fraction of Inter's
sidebearings, for the cases of the pair), and adds LAMBDA times the change in how the two
shapes meet, where both are letters sharing at least OVERLAP of their height (elsewhere the
measure has too little to go on). That change is held to CLIP: one close point (our a's
top terminal at F's middle arm, where Inter's sits above it) moves it a lot. A change under
THRESHOLD keeps Inter's value. Greek and Cyrillic pairs keep Inter's values.

Then every letter text uses (accented, Vietnamese, Greek and Cyrillic too) is set against
every other of its script, and against the figures and punctuation, with the kerning, and
a pair whose ink comes nearer than CLEAR gets kerning that holds it at CLEAR in every master
(`--check` scans every 100 from 100 to 900 on the built font). The groups don't change. tools/kern.py's t and f pairs are
left to it; run on its own, this runs it after, and to_ufo.py runs this after
tools/stacked.py, then tools/kern.py and tools/tabular.py. Running it again changes nothing.

Usage: python tools/kerning.py source/PlaceholderSans-*.ufo
       python tools/kerning.py --check [build/PlaceholderSans-VF.ttf]
"""

import os
import re
import string
import sys
import unicodedata

import numpy as np
import ufoLib2
from fontTools.misc import plistlib
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kern  # noqa: E402
import spacing  # noqa: E402
import tabular  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTERS = ("Thin", "Regular", "Black")
CAL = {"Thin": (200, 0.25), "Regular": (140, 0.375), "Black": (140, 0.375)}   # DEPTH, LAMBDA
CLIP = 40
THRESHOLD = 10
OVERLAP = 0.5
CLEAR = 10         # units between the nearest points of two glyphs side by side, at every master
Y0, Y1, STEP = -800, 2600, 10
YS = np.arange(Y0 + STEP / 2, Y1, STEP)

# Pairs set by hand after looking at them in text: {master: {(left, right): value}}.
OVERRIDES = {}


# --- Profiles --------------------------------------------------------------------------

class Flat(BasePen):
    """Outline as line segments (curves sampled), for crossing every row at once."""

    def __init__(self, glyph_set, steps=16):
        super().__init__(glyph_set)
        self.segs, self.steps, self.start = [], steps, None

    def _moveTo(self, p):
        self.start = self.last = p

    def _lineTo(self, p):
        self.segs.append((*self.last, *p))
        self.last = p

    def _curveToOne(self, p1, p2, p3):
        p0 = self.last
        t = np.linspace(0, 1, self.steps + 1)[1:]
        mt = 1 - t
        xs = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        ys = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        for x, y in zip(xs, ys):
            self._lineTo((x, y))

    def _qCurveToOne(self, p1, p2):
        p0 = self.last
        t = np.linspace(0, 1, self.steps + 1)[1:]
        mt = 1 - t
        xs = mt**2 * p0[0] + 2 * mt * t * p1[0] + t**2 * p2[0]
        ys = mt**2 * p0[1] + 2 * mt * t * p1[1] + t**2 * p2[1]
        for x, y in zip(xs, ys):
            self._lineTo((x, y))

    def _closePath(self):
        if self.last != self.start:
            self._lineTo(self.start)

    _endPath = _closePath


def profile(glyph_set, name):
    """(left, right) ink edges on every row of the grid (NaN where there's no ink)."""
    rec = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(rec)
    pen = Flat(glyph_set)
    rec.replay(pen)
    left, right = np.full(len(YS), np.nan), np.full(len(YS), np.nan)
    if not pen.segs:
        return left, right
    s = np.array(pen.segs)
    x0, y0, x1, y1 = s[:, 0:1], s[:, 1:2], s[:, 2:3], s[:, 3:4]
    y = YS[None, :]
    hit = ((y0 <= y) & (y < y1)) | ((y1 <= y) & (y < y0))
    with np.errstate(divide="ignore", invalid="ignore"):
        x = np.where(hit, x0 + (y - y0) * (x1 - x0) / (y1 - y0), np.nan)
    rows = hit.any(axis=0)
    left[rows], right[rows] = np.nanmin(x[:, rows], axis=0), np.nanmax(x[:, rows], axis=0)
    return left, right


class Profiles:
    def __init__(self, glyph_set, widths=None):
        self.glyphs, self.cache = glyph_set, {}
        self.widths = widths

    def width(self, name):
        return self.widths[name] if self.widths else self.glyphs[name].width

    def __getitem__(self, name):
        if name not in self.cache:
            self.cache[name] = profile(self.glyphs, name)
        return self.cache[name]


def measures(P, a, b, depth):
    """(optical gap, the shapes' own gap, nearest distance) of a set against b, unkerned.
    None if a pair has no rows with ink in both."""
    la, ra = P[a]
    lb, rb = P[b]
    ink_a, ink_b = ~np.isnan(ra), ~np.isnan(lb)
    both = ink_a & ink_b
    if not both.any():
        return None
    rows = np.where(ink_a | ink_b)[0]
    band = slice(rows[0], rows[-1] + 1)
    edge_a, edge_b = np.nanmax(ra), np.nanmin(lb)
    white_a = np.where(ink_a[band], np.minimum(edge_a - ra[band], depth), depth)
    white_b = np.where(ink_b[band], np.minimum(lb[band] - edge_b, depth), depth)
    optical = P.width(a) - edge_a + edge_b + white_a.mean() + white_b.mean()
    d = P.width(a) + lb - ra
    near = np.min(d[both])
    shapes = np.where(both, np.minimum(d, near + depth), near + depth)[band].mean()
    return optical, shapes, near


# --- Glyph kinds -------------------------------------------------------------------------

def char(ufo, name):
    for n in (name, name.split(".")[0]):
        if n in ufo and ufo[n].unicode is not None:
            return chr(ufo[n].unicode)
    return None


def script(c):
    o = ord(c) if c else 0
    if 0x370 <= o <= 0x3FF or 0x1F00 <= o <= 0x1FFF:
        return "greek"
    if 0x400 <= o <= 0x52F:
        return "cyrillic"
    return "latin"


def case(c):
    cat = unicodedata.category(c) if c else ""
    return {"Lu": "upper", "Lt": "upper", "Ll": "lower", "Nd": "figure"}.get(cat)


def key_glyph(ufo, name):
    if not name.startswith("public.kern"):
        return name
    members = ufo.groups[name]
    key = name.split(".", 2)[2]
    return key if key in members else members[0]


# --- Inter ---------------------------------------------------------------------------------

_inter = {}


def inter(master):
    """(Inter's outlines as Profiles, Inter's kerning with UFO group names) for a master."""
    if not _inter:
        import glyphsLib
        font = glyphsLib.GSFont(tabular.INTER)
        for m in font.masters:
            if m.axes[0] != 14:
                continue
            name = lambda s: (f"public.kern1.{s[7:]}" if s.startswith("@MMK_L_") else
                              f"public.kern2.{s[7:]}" if s.startswith("@MMK_R_") else s)
            pairs = {(name(a), name(b)): v for a, row in font.kerningLTR.get(m.id, {}).items()
                     for b, v in row.items()}
            _inter[m.name] = (Profiles({g.name: g.layers[m.id] for g in font.glyphs}), pairs)
    return _inter[master]


def scales(ufo, master):
    """Our sidebearings' median fraction of Inter's, per case (tools/spacing.py's measure)."""
    ours, theirs = spacing.Outlines(ufo), spacing.inter(master)
    out = {}
    for c, names in (("lower", [spacing.GLYPH.get(x, x) for x in string.ascii_lowercase
                                if x not in spacing.MIRRORED]),
                     ("upper", [x for x in string.ascii_uppercase if x not in spacing.LEFT_OF])):
        d = spacing.DEPTH[master][c == "upper"]
        out[c] = float(np.median([o[s] / t[s] for n in names
                                  for o, t in [(ours.optical(n, spacing.BANDS[c], d),
                                                theirs.optical(n, spacing.INTER_BANDS[c], d))]
                                  for s in (0, 1) if t[s] > 5]))
    out["figure"] = (out["lower"] + out["upper"]) / 2
    return out


# --- Refitting -----------------------------------------------------------------------------

def refit(ufo, master, ours):
    """{pair: value} for Inter's pairs, refitted where they're ours to refit."""
    theirs, pairs = inter(master)
    depth, lam = CAL[master]
    k = scales(ufo, master)
    out = {}
    for (left, right), value in pairs.items():
        if (left, right) in kern.PAIRS:
            continue
        out[(left, right)] = value
        if not all(n in ufo or n in ufo.groups for n in (left, right)):
            continue
        a, b = key_glyph(ufo, left), key_glyph(ufo, right)
        ca, cb = char(ufo, a), char(ufo, b)
        if {script(ca), script(cb)} & {"greek", "cyrillic"} or a not in theirs.glyphs \
                or b not in theirs.glyphs:
            continue
        o, t = measures(ours, a, b, depth), measures(theirs, a, b, depth)
        cases = [k[c] for c in (case(ca), case(cb)) if c]
        s = sum(cases) / len(cases) if cases else k["lower"]
        new = s * value
        if o and t:
            if all(case(c) in ("upper", "lower") for c in (ca, cb)) and shared(ours, a, b) >= OVERLAP:
                change = lam * (s * (t[1] - t[0]) - (o[1] - o[0]))
                new += max(-CLIP, min(CLIP, change))
        new = round(new)
        if abs(new - value) >= THRESHOLD:
            out[(left, right)] = new
    return out


def shared(P, a, b):
    """How much of the shorter glyph's height the two share."""
    rows = [np.where(~np.isnan(P[n][0]))[0] for n in (a, b)]
    lo, hi = max(r[0] for r in rows), min(r[-1] for r in rows)
    return (hi - lo) / max(1, min(r[-1] - r[0] for r in rows))


# --- Clearance -----------------------------------------------------------------------------

# The characters languages' text uses: letters by script, and figures and punctuation.
# Latin is Basic Latin, Latin-1, Extended-A, the Extended-B letters in use (Ǆ–ǌ, pinyin's
# ǎ–ǜ, Ǧ–ǩ, Ơ ơ Ư ư, Ș ș Ț ț), Welsh's ẁ ẃ ẅ, ẞ and Vietnamese; Greek is monotonic, Cyrillic
# modern. Letters are set against their own script's, and everything against the figures
# and punctuation.
SCRIPTS = {"latin": [(0x41, 0x5A), (0x61, 0x7A), (0xC0, 0x17F), (0x1A0, 0x1A1), (0x1AF, 0x1B0),
                     (0x1C4, 0x1DC), (0x1E6, 0x1E9), (0x218, 0x21B), (0x1E80, 0x1E85),
                     (0x1E9E, 0x1E9E), (0x1EA0, 0x1EF9)],
           "greek": [(0x386, 0x3CE)], "cyrillic": [(0x400, 0x45F), (0x490, 0x491)]}
SPREAD = 1   # rows above and below that count as a row's, so near misses in height count
MARKS = "0123456789.,:;!?¡¿'\"‘’“”‚„«»‹›-–—…·•()[]{}/\\&@#%*§¶†‡‰′″"


def text(ufo):
    """(glyph names, a mask of which pairs of them text sets side by side)."""
    cmap = {g.unicode: g.name for g in ufo if g.unicode is not None}
    names, kinds = [], []
    for kind, ranges in SCRIPTS.items():
        for lo, hi in ranges:
            for c in range(lo, hi + 1):
                if c in cmap and unicodedata.category(chr(c)).startswith("L"):
                    names.append(cmap[c])
                    kinds.append(kind)
    for c in MARKS:
        if ord(c) in cmap:
            names.append(cmap[ord(c)])
            kinds.append("marks")
    k = np.array(kinds)
    return names, (k[:, None] == k[None, :]) | (k[:, None] == "marks") | (k[None, :] == "marks")


class Kerning:
    """The kerning between any two of `names`, as a matrix, by the UFO's precedence."""

    def __init__(self, groups, pairs, names):
        index = {n: i for i, n in enumerate(names)}
        members = {g: [index[m] for m in ms if m in index] for g, ms in groups.items()}
        self.K = np.zeros((len(names), len(names)))
        order = sorted(pairs.items(), key=lambda kv: (not kv[0][0].startswith("public."),
                                                       not kv[0][1].startswith("public.")))
        for (a, b), v in order:          # group-group first, glyph-glyph last
            rows = members.get(a, [index[a]] if a in index else [])
            cols = members.get(b, [index[b]] if b in index else [])
            if rows and cols:
                self.K[np.ix_(rows, cols)] = v


def spread(edges, pick, rows=SPREAD):
    """Each row's edge as the furthest out of it and the `rows` rows either side."""
    out = edges.copy()
    for k in range(1, rows + 1):
        for shifted in (np.roll(edges, k, axis=1), np.roll(edges, -k, axis=1)):
            out = np.where(np.isnan(out), shifted, np.where(np.isnan(shifted), out, pick(out, shifted)))
    return out


def nearest(names, P, K):
    """Matrix of each pair's nearest distance with kerning K (inf where no shared rows), with
    each glyph's edges spread SPREAD rows up and down, so a near miss in height counts."""
    L = spread(np.stack([P[n][0] for n in names]), np.fmin)
    R = spread(np.stack([P[n][1] for n in names]), np.fmax)
    W = np.array([P.width(n) for n in names], dtype=float)
    Lf = np.where(np.isnan(L), np.inf, L)
    out = np.full((len(names), len(names)), np.inf)
    for i in range(len(names)):
        r = R[i]
        rows = ~np.isnan(r)
        if not rows.any():
            continue
        d = W[i] + Lf[:, rows] - r[rows][None, :]
        out[i] = d.min(axis=1) + K[i]
    return out


class Blend:
    """The glyphs between two masters, as tools/build.sh's variable font draws them (points
    interpolated in a straight line), for checking the weights between the masters."""

    class Glyph:
        def __init__(self, width, ops):
            self.width, self.ops = width, ops

        def draw(self, pen):
            for op, args in self.ops:
                getattr(pen, op)(*args)

    def __init__(self, a, b, t):
        self.a, self.b, self.t = a, b, t

    def __getitem__(self, name):
        recs = []
        for font in (self.a, self.b):
            rec = DecomposingRecordingPen(font)
            font[name].draw(rec)
            recs.append(rec.value)
        t = self.t
        mix = lambda p, q: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
        if [op for op, _ in recs[0]] != [op for op, _ in recs[1]] or \
                any(len(x) != len(y) for (_, x), (_, y) in zip(*recs)):
            ops = recs[0] if t < 0.5 else recs[1]
        else:
            ops = [(op, tuple(mix(p, q) for p, q in zip(x, y))) for (op, x), (_, y) in zip(*recs)]
        width = self.a[name].width + (self.b[name].width - self.a[name].width) * t
        return Blend.Glyph(width, ops)


def weights(ufos):
    """[(user weight, master below, master above, how far between)] at every 100."""
    out = []
    for w in range(100, 1000, 100):
        if w <= 430:
            out.append((w, "Thin", "Regular", (w - 100) / 330))
        else:
            out.append((w, "Regular", "Black", (w - 430) / 470))
    return out


def clear(ufos, pairs, rounds=6):
    """Kerning that holds every pair text sets side by side at least CLEAR apart at every
    100 from 100 to 900: a glyph against the right glyph's kerning group where every letter of
    the group collides with it (î against l's), or against each glyph that does, so the
    rest keep their kerning. Between the masters, both masters' values rise by what's
    missing. A group entry is never tighter than what it replaces. Returns the entries
    added or raised."""
    names, mask = text(ufos["Regular"])
    steps = weights(ufos)
    profiles = {}
    for w, lo, hi, t in steps:
        glyphs = ufos[lo] if t == 0 else ufos[hi] if t == 1 else Blend(ufos[lo], ufos[hi], t)
        widths = None if t in (0, 1) else {n: glyphs[n].width for n in names}
        profiles[w] = Profiles(glyphs, widths)
    second = {}
    for g, members in ufos["Regular"].groups.items():
        if g.startswith("public.kern2."):
            second.update({m: g for m in members})
    in_text = set(names)
    touched = set()
    for _ in range(rounds):
        K = {m: Kerning(u.groups, pairs[m], names).K for m, u in ufos.items()}
        need = {}          # (a, b) -> {master: value}
        for w, lo, hi, t in steps:
            near = nearest(names, profiles[w], K[lo] + (K[hi] - K[lo]) * t)
            for i, j in zip(*np.where((near < CLEAR) & mask)):
                short = CLEAR - near[i, j]
                for master, share in ((lo, 1 - t), (hi, t)):
                    if share > 0:
                        got = need.setdefault((names[i], names[j]), {})
                        got[master] = max(got.get(master, -np.inf), K[master][i, j] + short)
        if not need:
            break
        # One entry for a glyph against a whole group when all of the group's letters collide
        # with it; otherwise one for each glyph that does, so the others keep their kerning.
        by_group = {}
        for (a, b), by_master in need.items():
            by_group.setdefault((a, second.get(b, b)), {})[b] = by_master
        entries = {}
        for (a, right), found in by_group.items():
            members = [m for m in ufos["Regular"].groups.get(right, [right]) if m in in_text]
            if right in ufos["Regular"].groups and set(found) == set(members) and len(members) > 1:
                merged = {}
                for by_master in found.values():
                    for master, v in by_master.items():
                        merged[master] = max(merged.get(master, -np.inf), v)
                entries[(a, right)] = merged
            else:
                entries.update({(a, b): by_master for b, by_master in found.items()})
        for key, by_master in entries.items():
            a, right = key
            members = ufos["Regular"].groups.get(right, [right])
            for master, ufo in ufos.items():
                now = max(value(ufo.groups, pairs[master], a, b) for b in members if b in ufo)
                pairs[master][key] = int(np.ceil(max(now, by_master.get(master, now))))
            touched.add(key)
    return touched


def value(groups, pairs, a, b):
    """The kerning between glyphs a and b, by the UFO's precedence."""
    ga = next((g for g, ms in groups.items() if g.startswith("public.kern1.") and a in ms), None)
    gb = next((g for g, ms in groups.items() if g.startswith("public.kern2.") and b in ms), None)
    for key in ((a, b), (a, gb), (ga, b), (ga, gb)):
        if key in pairs:
            return pairs[key]
    return 0


def apply_all(ufos):
    """Refit and clear the kerning of {master: ufo}; returns {master: changed pairs}."""
    pairs = {}
    for master, ufo in ufos.items():
        ours = Profiles(ufo)
        new = refit(ufo, master, ours)
        keep = {p: v for p, v in ufo.kerning.items() if p in kern.PAIRS}
        new.update(keep)
        new.update(OVERRIDES.get(master, {}))
        pairs[master] = new
    clear(ufos, pairs)
    changed = {}
    for master, ufo in ufos.items():
        old = dict(ufo.kerning)
        ufo.kerning.clear()
        ufo.kerning.update(pairs[master])
        changed[master] = {p: v for p, v in pairs[master].items() if old.get(p) != v}
        changed[master].update({p: None for p in old if p not in pairs[master]})
    return changed


def main(paths):
    ufos = {re.search(r"-(\w+)\.ufo", p).group(1): ufoLib2.Font.open(p) for p in paths}
    changed = apply_all(ufos)
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        plist = f"{path}/kerning.plist"
        with open(plist, "rb") as f:
            data = plistlib.load(f)
        for (a, b), v in changed[master].items():
            if v is None:
                del data[a][b]
            else:
                data.setdefault(a, {})[b] = v
        data = {a: row for a, row in data.items() if row}
        with open(plist, "wb") as f:
            plistlib.dump(data, f)
        print(f"{path}: {len(changed[master])} pairs changed, {len(ufos[master].kerning)} in all ({master})")
    kern.main(paths)   # t's and f's bars, last


def check(ttf=os.path.join(ROOT, "build/PlaceholderSans-VF.ttf"), src=os.path.join(ROOT, "source")):
    """Overlapping pairs of text glyphs, with the kerning, at every 100 from 100 to 900."""
    from fontTools.ttLib import TTFont
    font = TTFont(ttf)
    ufos = {m: ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{m}.ufo")) for m in MASTERS}
    names, mask = text(ufos["Regular"])
    K = {m: Kerning(u.groups, dict(u.kerning), names).K for m, u in ufos.items()}
    axis = font["fvar"].axes[0]
    total = 0
    for w in range(100, 1000, 100):
        glyphs = font.getGlyphSet(location={"wght": w})
        P = Profiles(glyphs, {n: glyphs[n].width for n in names})
        if w <= axis.defaultValue:
            t = (w - axis.minValue) / (axis.defaultValue - axis.minValue)
            k = K["Thin"] + t * (K["Regular"] - K["Thin"])
        else:
            t = (w - axis.defaultValue) / (axis.maxValue - axis.defaultValue)
            k = K["Regular"] + t * (K["Black"] - K["Regular"])
        near = nearest(names, P, np.round(k))
        bad = sorted((near[i, j], names[i], names[j]) for i, j in zip(*np.where((near < 0) & mask)))
        total += len(bad)
        print(f"wght {w}: {len(bad)} overlapping pairs" + (": " + ", ".join(
            f"{a} {b} {d:.0f}" for d, a, b in bad[:12]) if bad else ""))
    return total


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        sys.exit(1 if check(*sys.argv[2:]) else 0)
    main(sys.argv[1:])
