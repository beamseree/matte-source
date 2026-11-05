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
THRESHOLD keeps Inter's value. Greek and Cyrillic pairs are refitted the same way (Inter's
values for ТЛ, ГЛ and ТД had stayed unscaled). y's kerning group is split from v's (SPLIT):
its left side is fuller, so it takes v's pairs, each refitted on y itself. Letters before the
period and comma (BASELINE) take the shape change too, less their group's median change
(which is the comma's own redesign, shared by every pair), and ADD adds pairs Inter doesn't
kern but our reshaped letters need (S before v w x y t f), both without CLIP: the audit's
pair terms agree with them pair by pair.

Then every letter text uses (accented, Vietnamese, Greek and Cyrillic too) is set against
every other of its script, and against the figures and punctuation (and the punctuation's
capital forms against capitals and figures), with the kerning, at every WEIGHTS: a pair
whose ink comes nearer than CLEAR, or two letters of a script whose own shapes (marks left
out) come nearer than LETTERS in any direction, gets the least kerning over the axis that
holds it there (`least`). Dashes join, so they aren't held apart from each other. Raising
both masters by each weight's whole shortfall had left the Regular master up to 97 units
looser than needed (fî), and the redrawn diagonals and long bars 4-33 units apart (XX, fy).
`--check` scans every 100 from 100 to 900 on the built font. tools/kern.py's t and f pairs
are left to it; run on its own, this runs it after, and to_ufo.py runs this after
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
from scipy.spatial import cKDTree
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
CLEAR = 10         # units between the nearest points of two glyphs side by side, at every weight
LETTERS = 50       # and between two letters of a script, their marks left out, in any direction;
                   # the user chose 50 over 10, 40 and 60 (build/clear-compare/)
Y0, Y1, STEP = -800, 2600, 10
YS = np.arange(Y0 + STEP / 2, Y1, STEP)
WEIGHTS = range(100, 901, 50)   # where the clearance is checked, in user weights
DEFAULT = 430                    # the Regular master's weight

# Kerning groups split from Inter's, {new group: (Inter's group, key glyph)}: the new group
# takes the old one's members built on the key glyph, and a copy of the old group's pairs,
# refitted on its own key like any other pair (Inter kerns y in v's group, so Inter's value
# for x|y is x|v's). y's left side (its arm and tail) is 21-42 units fuller than v's, so
# kerning y as v left Ay, Fy, ky and Py tight. Refitting each pair instead as v's value plus
# whatever kept x|y's gap equal to x|v's undid y's own sidebearing: when spacing.py opened
# y's left 31 units (ASIDE's "zy"), ny went from -34 to -65 and stayed 30 units tight.
SPLIT = {"public.kern2.y": ("public.kern2.v", "y")}

# Punctuation groups whose pairs with letters take the shape change too, measured against the
# group's own median change: the pairs share whatever the punctuation's own redesign did to
# the measure (quotes.py shortened the comma, so every Black comma pair moved about +12), and
# what is left is the letter's. P's shorter bowl (reshape.py) and F's mockup arms made P. P,
# F. F, 55-59 units loose in Regular (87-99 in Thin) under Inter's -69, T, and V, 25-30.
BASELINE = ("public.kern2.comma",)          # . , and the ellipsis

# Pairs Inter doesn't kern that our reshaped letters need, {left group: right groups}: each
# starts from Inter's 0 and takes the shape change, like any letter pair. reshape.py gave S
# the mockups' curves in Regular and Black, and Sv Sw Sx Sy St Sf came out 34-61 units loose.
ADD = {"public.kern1.S": ("public.kern2.v", "public.kern2.w", "public.kern2.x", "public.kern2.y",
                          "public.kern2.t", "public.kern2.f")}

# The apostrophe sits midway between the letters either side, as in SF Pro, rather than near
# the following letter as Inter kerns it ("don't": 327 units from the n, 243 from the t, once
# quotes.py shortened it): every Latin letter's pairs with it, on both sides, are set so the
# nearest distance between the letter and the apostrophe is APOSTROPHE_GAP, the mean over
# common contractions before the quotes were shortened (the user chose this, "centred,
# tighter", over Inter's placement restored and centred at today's 372 / 308 / 293, from an
# apostrophe comparison page). {(left group, right group): key glyph}: ’ shares its kerning
# with ”, and ' with ", so those follow; each is measured on the apostrophe itself.
APOSTROPHE_GAP = {"Thin": 356, "Regular": 286, "Black": 273}
APOSTROPHES = {("public.kern1.quotedblright", "public.kern2.quotedblright"): "quoteright",
               ("public.kern1.quotedbl", "public.kern2.quotedbl"): "quotesingle"}

# Glyphs drawn to join their neighbours, which the clearance leaves touching each other.
DASHES = ("hyphen", "endash", "emdash", "hyphen.case", "endash.case", "emdash.case")

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


class Skipping(DecomposingRecordingPen):
    """Decomposes components, leaving out those in `skip` (at any depth)."""

    def __init__(self, glyph_set, skip=()):
        super().__init__(glyph_set)
        self.skip = skip

    def addComponent(self, name, transformation):
        if name not in self.skip:
            super().addComponent(name, transformation)


def profile(glyph_set, name, skip=()):
    """(left, right) ink edges on every row of the grid (NaN where there's no ink), leaving
    out the components named in `skip`."""
    rec = Skipping(glyph_set, skip)
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
    def __init__(self, glyph_set, widths=None, skip=()):
        self.glyphs, self.cache = glyph_set, {}
        self.widths, self.skip = widths, skip

    def width(self, name):
        return self.widths[name] if self.widths else self.glyphs[name].width

    def __getitem__(self, name):
        if name not in self.cache:
            self.cache[name] = profile(self.glyphs, name, self.skip)
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

def root(ufo, name):
    """The glyph a composite is built on: its first component's, all the way down."""
    while ufo[name].components and not ufo[name].contours:
        name = ufo[name].components[0].baseGlyph
    return name


def split(ufo):
    """Split SPLIT's groups off Inter's in `ufo`; returns whether the groups changed."""
    changed = False
    for new, (old, key) in SPLIT.items():
        moving = [m for m in ufo.groups.get(old, []) if root(ufo, m) == key]
        if moving:
            ufo.groups[old] = [m for m in ufo.groups[old] if m not in moving]
            ufo.groups[new] = list(ufo.groups.get(new, [])) + moving
            changed = True
    return changed


def refit(ufo, master, ours):
    """{pair: value} for Inter's pairs, refitted where they're ours to refit. A group SPLIT
    off Inter's takes its old group's pairs, each refitted on its own key glyph: Inter's value
    (the old group's, which Inter gives its key too), measured with that key in both fonts."""
    theirs, pairs = inter(master)
    depth, lam = CAL[master]
    k = scales(ufo, master)

    def parts(left, right, value):
        """(Inter's value scaled to our spacing, LAMBDA times the change in how the shapes meet
        or None, whether both are letters sharing OVERLAP of their height), measured on the
        key glyphs; None where either is missing here or in Inter."""
        if not all(n in ufo or n in ufo.groups for n in (left, right)):
            return None
        a, b = key_glyph(ufo, left), key_glyph(ufo, right)
        ca, cb = char(ufo, a), char(ufo, b)
        if a not in theirs.glyphs or b not in theirs.glyphs:
            return None
        o, t = measures(ours, a, b, depth), measures(theirs, a, b, depth)
        cases = [k[c] for c in (case(ca), case(cb)) if c]
        s = sum(cases) / len(cases) if cases else k["lower"]
        change = lam * (s * (t[1] - t[0]) - (o[1] - o[0])) if o and t else None
        letters = (change is not None and all(case(c) in ("upper", "lower") for c in (ca, cb))
                   and shared(ours, a, b) >= OVERLAP)
        return s * value, change, letters

    def one(left, right, value):
        p = parts(left, right, value)
        if p is None:
            return value
        new, change, letters = p
        if letters:
            new += max(-CLIP, min(CLIP, change))
        return new

    out = {}
    for (left, right), value in pairs.items():
        if (left, right) in kern.PAIRS:
            continue
        out[(left, right)] = value
        new = round(one(left, right, value))
        if abs(new - value) >= THRESHOLD:
            out[(left, right)] = new
    for split_group, (old, key) in SPLIT.items():
        if split_group not in ufo.groups:
            continue
        side = 0 if split_group.startswith("public.kern1.") else 1
        for (left, right), value in pairs.items():
            if (left, right)[side] != old:
                continue
            pair = (split_group, right) if side == 0 else (left, split_group)
            out[pair] = round(one(key, right, value) if side == 0 else one(left, key, value))
    # Letters before BASELINE's groups: the shape change less the group's median change, added
    # to the pair's value where it comes to THRESHOLD, with no CLIP (the audit's own pair terms
    # agree with it pair by pair). Pairs with nothing of their own keep their value exactly.
    # Inter's exceptions against one glyph of the group (P and F against the period) are
    # measured on that glyph, less its own median over the same letters.
    def letter(name):
        return case(char(ufo, key_glyph(ufo, name))) in ("upper", "lower")

    for group in BASELINE:
        members = set(ufo.groups.get(group, ()))
        lefts = {}
        for (left, right), value in pairs.items():
            if right == group and (left, right) not in kern.PAIRS and letter(left):
                p = parts(left, right, value)
                if p and p[1] is not None:
                    lefts[left] = p[1]
        if not lefts:
            continue
        found = {(left, group): change for left, change in lefts.items()}
        middle = {group: float(np.median(list(lefts.values())))}
        for (left, right), value in pairs.items():
            if right in members and (left, right) not in kern.PAIRS and letter(left):
                p = parts(left, right, value)
                if p and p[1] is not None:
                    if right not in middle:
                        own = [q[1] for q in (parts(l, right, 0) for l in lefts) if q and q[1] is not None]
                        middle[right] = float(np.median(own))
                    found[(left, right)] = p[1]
        for (left, right), change in found.items():
            if abs(change - middle[right]) >= THRESHOLD:
                out[(left, right)] = round(out[(left, right)] + change - middle[right])
    # ADD's pairs, from Inter's 0, with no CLIP for the same reason.
    for left, rights in ADD.items():
        for right in rights:
            p = parts(left, right, 0)
            if p and p[2]:
                new = round(p[1])
                out[(left, right)] = new if abs(new) >= THRESHOLD else 0
    out.update(apostrophes(ufo, master, pairs))
    return out


class Ink:
    """Points along a glyph's outline, every few units, for nearest distances in any direction."""

    def __init__(self, ufo):
        self.ufo, self.cache = ufo, {}

    def __getitem__(self, name):
        if name not in self.cache:
            rec = DecomposingRecordingPen(self.ufo)
            self.ufo[name].draw(rec)
            pen = Flat(self.ufo)
            rec.replay(pen)
            parts = []
            for x0, y0, x1, y1 in pen.segs:
                t = np.linspace(0, 1, max(1, int(np.hypot(x1 - x0, y1 - y0) // 4)) + 1)
                parts.append(np.stack([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t], axis=1))
            self.cache[name] = np.concatenate(parts)
        return self.cache[name]


def gap_at(ufo, ink, a, b, k):
    """The nearest distance between a and b, in any direction, with kerning k."""
    return cKDTree(ink[a]).query(ink[b] + (ufo[a].width + k, 0))[0].min()


def kerning_for_gap(ufo, ink, a, b, gap):
    """The kerning that leaves `gap` between a and b at their nearest, in any direction."""
    lo, hi = -1600.0, 800.0
    for _ in range(18):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if gap_at(ufo, ink, a, b, mid) < gap else (lo, mid)
    return (lo + hi) / 2


def apostrophes(ufo, master, pairs):
    """{pair: value} putting APOSTROPHES APOSTROPHE_GAP from every Latin letter on each side:
    each letter's kerning group against the apostrophe's (measured on the group's key glyph),
    and Inter's exceptions against it on their own glyphs."""
    gap, ink, out = APOSTROPHE_GAP[master], Ink(ufo), {}
    first, second = {}, {}
    for g, members in ufo.groups.items():
        for m in members:
            (first if g.startswith("public.kern1.") else second if g.startswith("public.kern2.") else {})[m] = g
    cmap = {g.unicode: g.name for g in ufo if g.unicode is not None}
    latin = [cmap[ord(c)] for c in string.ascii_letters]
    def letter(name):
        if name not in ufo and name not in ufo.groups:
            return False
        c = char(ufo, key_glyph(ufo, name))
        return bool(case(c)) and case(c) != "figure" and script(c) == "latin"

    for (g1, g2), q in APOSTROPHES.items():
        if g1 not in ufo.groups or g2 not in ufo.groups or q not in ufo:
            continue
        before = {(first.get(n, n), g2) for n in latin}     # the letter, then the apostrophe
        after = {(g1, second.get(n, n)) for n in latin}     # the apostrophe, then the letter
        for left, right in pairs:                           # Inter's exceptions with a letter
            if (right == g2 or right in ufo.groups[g2]) and letter(left):
                before.add((left, right))
            if (left == g1 or left in ufo.groups[g1]) and letter(right):
                after.add((left, right))
        for left, right in before:
            mark = q if right == g2 else right
            out[(left, right)] = round(kerning_for_gap(ufo, ink, key_glyph(ufo, left), mark, gap))
        for left, right in after:
            mark = q if left == g1 else left
            out[(left, right)] = round(kerning_for_gap(ufo, ink, mark, key_glyph(ufo, right), gap))
        # A letter shaped unlike its group's key glyph (c's terminal reaching up beside o's
        # round side: c’ 229 where o’ is 286) gets its own value, and so do the glyphs built
        # on it (ç, é ...), where its group's leaves it THRESHOLD or more off the gap.
        for n in latin:
            for group, pair, a, b in ((first.get(n), lambda g: (g, g2), n, q),
                                      (second.get(n), lambda g: (g1, g), q, n)):
                if not group or out.get(pair(group)) is None:
                    continue
                if abs(gap_at(ufo, ink, a, b, out[pair(group)]) - gap) < THRESHOLD:
                    continue
                own = round(kerning_for_gap(ufo, ink, a, b, gap))
                for member in ufo.groups[group]:
                    if root(ufo, member) == root(ufo, n) and pair(member) not in out:
                        out[pair(member)] = own
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
    """(glyph names, a mask of which pairs of them text sets side by side, a mask of which of
    those are two letters of a script). The punctuation's capital forms (parenleft.case ...)
    are set beside capitals and figures; dashes are drawn to join, so not against each other."""
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
    for c in MARKS:
        if ord(c) in cmap and f"{cmap[ord(c)]}.case" in ufo:
            names.append(f"{cmap[ord(c)]}.case")
            kinds.append("case")
    k = np.array(kinds)
    tall = np.array([case(char(ufo, n)) in ("upper", "figure") for n in names])
    marks, cased = k == "marks", k == "case"
    letters = (k[:, None] == k[None, :]) & np.isin(k, list(SCRIPTS))[:, None]
    mask = letters | (marks[:, None] & ~cased[None, :]) | (~cased[:, None] & marks[None, :])
    mask |= (cased[:, None] & tall[None, :]) | (tall[:, None] & cased[None, :])
    dash = np.isin(names, DASHES)
    mask &= ~(dash[:, None] & dash[None, :])
    return names, mask, letters


def mark_names(ufo):
    """The combining marks, which the clearance between letters leaves out."""
    categories = ufo.lib.get("public.openTypeCategories", {})
    return {n for n in ufo.keys() if categories.get(n) == "mark" or "comb" in n.split(".")[0]}


def with_marks(ufo, names, marks):
    """The glyphs among `names` built with a mark somewhere in them."""
    memo = {}
    def has(name):
        if name not in memo:
            memo[name] = any(c.baseGlyph in marks or has(c.baseGlyph) for c in ufo[name].components)
        return memo[name]
    return {n for n in names if has(n)}


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


def grown(edges, reach):
    """Right edges grown by a disc of radius `reach`, less `reach`: each row's edge as far
    out as the disc around any ink within `reach` above or below it gets, beyond `reach`."""
    out = edges.copy()
    for k in range(1, int(reach // STEP) + 1):
        g = np.sqrt(reach ** 2 - (k * STEP) ** 2) - reach
        for shifted in (np.roll(edges, k, axis=1), np.roll(edges, -k, axis=1)):
            out = np.fmax(out, shifted + g)
    return out


def nearest(names, P, K, reach=None):
    """Matrix of each pair's nearest distance with kerning K (inf where no shared rows), with
    each glyph's edges spread SPREAD rows up and down, so a near miss in height counts. With
    `reach`, the distance in any direction where it is under `reach`: the left glyph's ink
    grown by a disc that size (`grown`)."""
    if reach:
        L = np.stack([P[n][0] for n in names])
        R = grown(np.stack([P[n][1] for n in names]), reach)
    else:
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

    def __init__(self, a, b, t, skip=()):
        self.a, self.b, self.t, self.skip = a, b, t, skip

    def __getitem__(self, name):
        recs = []
        for font in (self.a, self.b):
            rec = Skipping(font, self.skip)
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


def weights():
    """[(user weight, master below, master above, how far between)] at each of WEIGHTS."""
    out = []
    for w in WEIGHTS:
        if w <= DEFAULT:
            out.append((w, "Thin", "Regular", (w - WEIGHTS[0]) / (DEFAULT - WEIGHTS[0])))
        else:
            out.append((w, "Regular", "Black", (w - DEFAULT) / (WEIGHTS[-1] - DEFAULT)))
    return out


def least(short):
    """{master: added kerning} making up each weight's shortfall ({weight: units}) with the
    least kerning added over the whole axis: the integral of its square, the kerning going in
    a straight line between the masters. Raising a master by the whole shortfall of a weight
    near the next one had left the Regular master up to 97 units looser than it needed."""
    lo, hi = WEIGHTS[0], WEIGHTS[-1]
    # Each weight's shortfall with the share of it the far master has (Thin below the
    # default, Black above it; Regular has the rest), and r: candidates for Regular's.
    below = [(1 - (w - lo) / (DEFAULT - lo), v) for w, v in short.items() if w < DEFAULT]
    above = [((w - DEFAULT) / (hi - DEFAULT), v) for w, v in short.items() if w > DEFAULT]
    r0 = max([0.0] + [v for w, v in short.items() if w == DEFAULT])
    r = np.linspace(r0, max(r0, 2 * max(short.values())), 401)
    def far(found):
        """The far master's least value for each candidate r."""
        x = np.zeros_like(r)
        for share, v in found:
            x = np.maximum(x, (v - (1 - share) * r) / share)
        return x
    thin, black = far(below), far(above)
    cost = (DEFAULT - lo) * (thin**2 + thin * r + r**2) + (hi - DEFAULT) * (r**2 + r * black + black**2)
    i = int(np.argmin(cost))
    return {"Thin": thin[i], "Regular": r[i], "Black": black[i]}


class Bodies:
    """Profiles of the glyphs with their marks left out (the rest are the glyphs' own)."""

    def __init__(self, full, bodies, marked):
        self.full, self.bodies, self.marked = full, bodies, marked

    def width(self, name):
        return self.full.width(name)

    def __getitem__(self, name):
        return (self.bodies if name in self.marked else self.full)[name]


def clear(ufos, pairs, rounds=6):
    """Kerning that holds every pair text sets side by side at least CLEAR apart, and two
    letters of a script at least LETTERS apart in any direction with their marks left out,
    at each of WEIGHTS: a glyph against the right glyph's kerning group where every letter
    of the group falls short with it (î against l's), or against each glyph that does, so
    the rest keep their kerning. Each pair gets the least kerning over the axis that makes
    up its shortfalls (`least`); a group entry is never tighter than what it replaces.
    Returns the entries added or raised."""
    regular = ufos["Regular"]
    names, mask, letters = text(regular)
    skip = mark_names(regular)
    marked = with_marks(regular, names, skip)
    profiles, bodies = {}, {}
    for w, lo, hi, t in weights():
        if t in (0, 1):
            glyphs = body = ufos[lo] if t == 0 else ufos[hi]
            widths = None
        else:
            glyphs, body = Blend(ufos[lo], ufos[hi], t), Blend(ufos[lo], ufos[hi], t, skip)
            widths = {n: glyphs[n].width for n in names}
        profiles[w] = Profiles(glyphs, widths)
        bodies[w] = Bodies(profiles[w], Profiles(body, widths, skip), marked)
    first, second = {}, {}
    for g, members in regular.groups.items():
        if g.startswith("public.kern1."):
            first.update({m: g for m in members})
        elif g.startswith("public.kern2."):
            second.update({m: g for m in members})
    in_text = set(names)
    touched = set()
    for _ in range(rounds):
        K = {m: Kerning(u.groups, pairs[m], names).K for m, u in ufos.items()}
        short = {}         # (i, j) -> {weight: units}
        for w, lo, hi, t in weights():
            k = K[lo] + (K[hi] - K[lo]) * t
            gap = np.where(mask, CLEAR - nearest(names, profiles[w], k), -np.inf)
            gap = np.fmax(gap, np.where(letters, LETTERS - nearest(names, bodies[w], k, LETTERS),
                                        -np.inf))
            for i, j in zip(*np.where(gap > 0)):
                short.setdefault((i, j), {})[w] = gap[i, j]
        if not short:
            break
        need = {}          # (a, b) -> {master: value}
        for (i, j), found in short.items():
            add = least(found)
            need[(names[i], names[j])] = {m: K[m][i, j] + add[m] for m in ufos}
        # One entry against a whole group when all of the group's text glyphs fall short with
        # the same glyph (î against l's), and then for a whole group on the left when all of
        # its text glyphs need an entry against the same glyph or group (À Á Â ... beside X);
        # otherwise one for each glyph that does, so the others keep their kerning.
        def merge(found, side, groups):
            out = {}
            for key, by_master in found.items():
                g = groups.get(key[side], key[side])
                out.setdefault((g, key[1]) if side == 0 else (key[0], g), {})[key[side]] = by_master
            entries = {}
            for key, members_found in out.items():
                g = key[side]
                members = [m for m in regular.groups.get(g, [g]) if m in in_text]
                if g in regular.groups and set(members_found) == set(members) and len(members) > 1:
                    merged = {}
                    for by_master in members_found.values():
                        for master, v in by_master.items():
                            merged[master] = max(merged.get(master, -np.inf), v)
                    entries[key] = merged
                else:
                    entries.update({(m, key[1]) if side == 0 else (key[0], m): by_master
                                    for m, by_master in members_found.items()})
            return entries
        entries = merge(merge(need, 1, second), 0, first)
        for key, by_master in entries.items():
            lefts, rights = (regular.groups.get(n, [n]) for n in key)
            for master, ufo in ufos.items():
                now = max(value(first, second, pairs[master], a, b)
                          for a in lefts if a in ufo for b in rights if b in ufo)
                pairs[master][key] = int(np.ceil(max(now, by_master.get(master, now)) - 1e-6))
            touched.add(key)
    return touched


def value(first, second, pairs, a, b):
    """The kerning between glyphs a and b, by the UFO's precedence ({glyph: its kerning
    group} on the left and on the right)."""
    ga, gb = first.get(a), second.get(b)
    for key in ((a, b), (a, gb), (ga, b), (ga, gb)):
        if key in pairs:
            return pairs[key]
    return 0


def apply_all(ufos):
    """Refit and clear the kerning of {master: ufo}; returns {master: changed pairs}."""
    pairs = {}
    for master, ufo in ufos.items():
        split(ufo)
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
        groups = f"{path}/groups.plist"
        with open(groups, "rb") as f:
            data = plistlib.load(f)
        if any(data.get(g) != ufos[master].groups.get(g) for n, (o, _) in SPLIT.items() for g in (n, o)):
            for new, (old, _) in SPLIT.items():
                data[old], data[new] = ufos[master].groups[old], ufos[master].groups[new]
            with open(groups, "wb") as f:
                plistlib.dump(data, f)
        print(f"{path}: {len(changed[master])} pairs changed, {len(ufos[master].kerning)} in all ({master})")
    kern.main(paths)   # t's and f's bars, last


def check(ttf=os.path.join(ROOT, "build/PlaceholderSans-VF.ttf"), src=os.path.join(ROOT, "source")):
    """Overlapping pairs of text glyphs, with the kerning, at every 100 from 100 to 900, and
    the pairs of letters without marks nearer than LETTERS (a unit's rounding allowed)."""
    from fontTools.ttLib import TTFont
    font = TTFont(ttf)
    ufos = {m: ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{m}.ufo")) for m in MASTERS}
    names, mask, letters = text(ufos["Regular"])
    plain = np.array([n not in with_marks(ufos["Regular"], names, mark_names(ufos["Regular"]))
                      for n in names])
    letters &= plain[:, None] & plain[None, :]
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
        close = nearest(names, P, np.round(k), LETTERS)
        tight = sorted((close[i, j], names[i], names[j])
                       for i, j in zip(*np.where((close < LETTERS - 1) & letters)))
        total += len(bad)
        print(f"wght {w}: {len(bad)} overlapping pairs" + (": " + ", ".join(
            f"{a} {b} {d:.0f}" for d, a, b in bad[:12]) if bad else "") +
            f"; {len(tight)} letter pairs nearer than {LETTERS}" + (": " + ", ".join(
                f"{a} {b} {d:.0f}" for d, a, b in tight[:8]) if tight else ""))
    return total


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        sys.exit(1 if check(*sys.argv[2:]) else 0)
    main(sys.argv[1:])
