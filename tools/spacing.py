"""Set the letters', figures' and punctuation's sidebearings and the word space.

tools/fit.py's spacing fit moved each letter's sides by the "sb" nudges tools/derive.py
applies, but derive.py applies them only to glyphs drawn as contours, and i, j, t, f and Q
are built from components, so their sides never moved: the fit made up for them on their
neighbours. In Regular u's right side came out 180 units, 44 more than Inter's proportions
give it, beside an i whose sides it couldn't reach (ui 25 too wide), while m's left side
was 111; in Inter every straight stem side is the same (158). Sides the pangrams show only
next to a word space (t's left, j's left, k's right, b's left ...) were never fitted at all
(r_t 77 units too tight in Regular, 120 in Thin).

So `--fit` solves every letter's two sides together, by least squares, from:
- the mockups' pairs inside words (quick brown fox jumps over the lazy dog, in both cases),
  which our letters must match;
- the gaps across word spaces, which also set the space's width; the mockups' word gaps are
  uneven (their spread is about the same as the next term's), so they count as much as it;
- Inter's proportions: each side's optical sidebearing (its sidebearing plus the white of
  its profile, as deep as DEPTH, averaged over the x-height or cap height) as the same
  fraction of Inter's as the median letter of its case. DEPTH is the depth that makes
  Inter's own letters most even by this measure. This splits each pair between its two
  letters and sets the sides the pangrams don't show (q's and Q's left, figures).
WEIGHTS sets how much the word gaps and Inter's proportions count against the pairs inside
words; Thin's screenshot is about +-12 units, so they count for more there. d and q mirror
b and p, i and j take ı's and ȷ's sides, Q's left is O's. OTHERS (letters the pangrams
don't have, like æ, ß and þ, and the character variants) take Inter's proportions at their
case's median letter, the figures at the median of both cases', and the pieces of the f
ligatures (WITH) move with f, and PUNCTUATION takes Inter's proportions at the lowercase
median, over each glyph's own height. ROUND can set the round capitals' round sides some other
way than the pangrams' pairs: at H's fraction of Inter's sidebearings, or all one sidebearing
that leaves them as much white as the straight capitals' stems have, against Inter's (the
user chose this, "white", for consistency over the mockups' uneven round sides).

SIDES holds the result as each glyph's left and right sidebearings (ink to the advance's
edges), so applying it is the same whatever ran before. A glyph's outline, components and
anchors move together; glyphs drawn over it (Q's tail over O, the bars of đ and ŧ) move
with it, and the anchors of composites built on it (d, q) too. tools/accents.py, which runs
after, gives every composite its base's new width and puts its marks back on the anchors.
Running it again changes nothing.

Run it after tools/joints.py and before tools/accents.py; run on its own, it runs
tools/accents.py, tools/stacked.py, tools/tabular.py, tools/kerning.py and tools/kern.py
after. The pangrams are laid out with the kerning, so refit after tools/kerning.py changes
the kerning of a pair in them (one round settles it).

Usage: python tools/spacing.py source/PlaceholderSans-*.ufo
       python tools/spacing.py --fit [source]    # prints new SIDES and SPACE tables
"""

import json
import os
import re
import string
import sys

import numpy as np
import ufoLib2
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ufoLib.glifLib import GlyphSet

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kern  # noqa: E402
import strokes  # noqa: E402
import tabular  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MASTERS = ("Thin", "Regular", "Black")
TARGETS = {"Thin": "targets-thin.json", "Regular": "targets.json", "Black": "targets-black.json"}
SENTENCES = ("quick brown fox jumps over the lazy dog", "QUICK BROWN FOX JUMPS OVER THE LAZY DOG")

# Optical depth (lowercase, capitals): the most even optical sidebearings for Inter's letters.
DEPTH = {"Thin": (150, 150), "Regular": (130, 130), "Black": (100, 60)}
# Weights of a pair inside a word, a gap across a word space, and Inter's proportions.
WEIGHTS = {"Thin": (1.0, 0.45, 0.45), "Regular": (1.0, 0.11, 0.11), "Black": (1.0, 0.11, 0.11)}
BANDS = {"lower": (0, 1076), "upper": (0, 1490)}
INTER_BANDS = {"lower": (0, 1118), "upper": (0, 1490)}
STEP = 10

GLYPH = {"i": "idotless", "j": "jdotless"}
MIRRORED = {"d": "b", "q": "p"}          # d is b turned round: its left side is b's right
LEFT_OF = {"Q": "O"}                     # Q is O with a tail: its left side is O's
# Drawn letters the pangrams don't show, and the character variants: Inter's proportions
# at the median letter's of their case.
OTHERS = ("AE", "OE", "Thorn", "Schwa", "Ezh", "ae", "eth", "thorn", "germandbls",
          "kgreenlandic", "florin", "a.1", "a.2", "f.1", "t.1", "u.1", "l.ss02", "G.1", "I.1")
WITH = {"f.i": "f", "f.i.1": "f"}        # the dlig pieces before i move with their letter
# The round capitals' round sides: "mockup" fits them to the pangrams' pairs like the other
# letters; "inter" gives them the same fraction of Inter's sidebearings as H has; "white"
# makes them all one sidebearing, the one that leaves as much white beside them, against
# Inter's, as the straight capitals' stems have (our O is wider than Inter's, so its curve
# already leaves more white beside it than Inter's does).
ROUND = "white"
ROUND_SIDES = {"O": (0, 1), "C": (0,), "G": (0,), "D": (1,)}
STEMS = {"H": (0, 1), "I": (0, 1), "M": (0, 1), "N": (0, 1), "U": (0, 1), "B": (0,), "D": (0,),
         "E": (0,), "F": (0,), "K": (0,), "L": (0,), "P": (0,), "R": (0,)}
FIGURES = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
           "one.ss01", "three.1", "four.ss01", "six.ss01")   # nine.ss01 is six.ss01 turned
# Punctuation and symbols standing alone (their doubled forms are composites and follow):
# Inter's proportions at the lowercase median, measured over each glyph's own height. The
# dots and the glyphs built on them are tools/dots.py's and tools/stacked.py's, so not here.
PUNCTUATION = ("quotesingle", "quoteleft", "quoteright", "parenleft", "parenright",
               "bracketleft", "bracketright", "braceleft", "braceright", "hyphen", "endash",
               "emdash", "slash", "backslash", "ampersand", "at", "asterisk", "numbersign",
               "guilsinglleft", "guilsinglright", "bullet", "bar", "brokenbar", "plus", "minus",
               "equal", "multiply", "divide", "less", "greater", "plusminus", "asciitilde",
               "asciicircum", "euro", "sterling", "yen", "section", "paragraph", "registered",
               "trademark", "degree", "dagger", "daggerdbl")
SPACES = ("space", "nbspace")

SIDES = {
    "Thin": {
        "A": (73, 43), "B": (195, 106), "C": (102, 92), "D": (184, 102), "E": (191, 95),
        "F": (180, 86), "G": (102, 123), "H": (193, 175), "I": (187, 191), "J": (124, 153),
        "K": (186, 31), "L": (176, 123), "M": (188, 187), "N": (195, 180), "O": (102, 102),
        "P": (187, 105), "Q": (None, 116), "R": (197, 105), "S": (124, 122), "T": (85, 82),
        "U": (158, 152), "V": (73, 47), "W": (12, 34), "X": (-1, 39), "Y": (43, 23),
        "Z": (112, 113), "a": (110, 155), "b": (194, 114), "c": (112, 98), "e": (115, 117),
        "f": (5, 25), "g": (103, 184), "h": (203, 184), "k": (181, 43), "l": (191, 199),
        "m": (173, 174), "n": (173, 188), "o": (114, 118), "p": (168, 119), "r": (197, 61),
        "s": (124, 119), "t": (20, 44), "u": (169, 174), "v": (74, 82), "w": (95, 65),
        "x": (47, 47), "y": (53, 76), "z": (108, 105), "AE": (31, 100), "Ezh": (82, 113),
        "G.1": (108, 146), "I.1": (76, 76), "OE": (106, 99), "Schwa": (121, 109),
        "Thorn": (174, 116), "a.1": (116, 184), "a.2": (96, 18), "ae": (96, 107),
        "ampersand": (113, 28), "asciicircum": (81, 81), "asciitilde": (174, 174),
        "asterisk": (118, 118), "at": (131, 130), "backslash": (52, 52), "bar": (238, 238),
        "braceleft": (149, 137), "braceright": (137, 149), "bracketleft": (238, 137),
        "bracketright": (137, 238), "brokenbar": (153, 153), "bullet": (359, 359),
        "dagger": (116, 116), "daggerdbl": (116, 116), "degree": (146, 146),
        "divide": (204, 204), "eight": (118, 119), "emdash": (0, 0), "endash": (0, 0),
        "equal": (276, 276), "eth": (115, 117), "euro": (55, 154), "f.1": (184, 16),
        "f.i": (33, -1), "f.i.1": (202, -1), "five": (117, 118), "florin": (-35, -35),
        "four": (117, 115), "four.ss01": (117, 115), "germandbls": (215, 140),
        "greater": (264, 190), "guilsinglleft": (84, 84), "guilsinglright": (84, 84),
        "hyphen": (160, 158), "idotless": (185, 184), "jdotless": (-38, 177),
        "kgreenlandic": (184, 55), "l.ss02": (184, 18), "less": (190, 264),
        "minus": (214, 214), "multiply": (201, 201), "nine": (119, 122),
        "numbersign": (33, 34), "one": (112, 204), "one.ss01": (104, 204),
        "paragraph": (129, 215), "parenleft": (216, 123), "parenright": (123, 216),
        "plus": (203, 203), "plusminus": (204, 204), "quoteleft": (163, 80),
        "quoteright": (164, 80), "quotesingle": (238, 238), "registered": (87, 87),
        "section": (130, 130), "seven": (95, 97), "six": (122, 119), "six.ss01": (118, 117),
        "slash": (52, 52), "sterling": (111, 126), "t.1": (181, 24), "thorn": (184, 116),
        "three": (126, 119), "three.1": (125, 118), "trademark": (66, 87), "two": (152, 145),
        "u.1": (182, 182), "yen": (31, 31), "zero": (122, 122),
    },
    "Regular": {
        "A": (36, 21), "B": (148, 96), "C": (88, 81), "D": (148, 88), "E": (150, 82),
        "F": (153, 36), "G": (88, 91), "H": (148, 156), "I": (149, 156), "J": (69, 140),
        "K": (151, 22), "L": (151, 78), "M": (149, 154), "N": (145, 153), "O": (88, 88),
        "P": (154, 84), "Q": (None, 95), "R": (150, 76), "S": (90, 88), "T": (61, 62),
        "U": (142, 144), "V": (51, 17), "W": (3, 21), "X": (0, 27), "Y": (9, 22),
        "Z": (82, 69), "a": (86, 112), "b": (156, 86), "c": (91, 77), "e": (86, 89),
        "f": (6, 25), "g": (101, 138), "h": (145, 136), "k": (137, 8), "l": (147, 155),
        "m": (143, 135), "n": (122, 136), "o": (82, 85), "p": (138, 74), "r": (153, 45),
        "s": (75, 75), "t": (8, 40), "u": (135, 148), "v": (40, 40), "w": (57, 35),
        "x": (14, 33), "y": (6, 28), "z": (79, 74), "AE": (23, 100), "Ezh": (63, 84),
        "G.1": (88, 116), "I.1": (63, 63), "OE": (87, 96), "Schwa": (93, 89),
        "Thorn": (140, 121), "a.1": (83, 138), "a.2": (68, 9), "ae": (69, 79),
        "ampersand": (79, 13), "asciicircum": (59, 59), "asciitilde": (140, 140),
        "asterisk": (90, 90), "at": (97, 96), "backslash": (26, 26), "bar": (229, 229),
        "braceleft": (113, 97), "braceright": (97, 113), "bracketleft": (198, 97),
        "bracketright": (97, 198), "brokenbar": (165, 165), "bullet": (217, 217),
        "dagger": (87, 87), "daggerdbl": (90, 90), "degree": (106, 106), "divide": (172, 170),
        "eight": (92, 91), "emdash": (0, 0), "endash": (0, 0), "equal": (193, 192),
        "eth": (82, 85), "euro": (31, 94), "f.1": (138, 25), "f.i": (23, -237),
        "f.i.1": (142, -237), "five": (98, 92), "florin": (7, 5), "four": (89, 86),
        "four.ss01": (89, 86), "germandbls": (157, 92), "greater": (202, 142),
        "guilsinglleft": (74, 56), "guilsinglright": (56, 74), "hyphen": (126, 126),
        "idotless": (143, 148), "jdotless": (-53, 137), "kgreenlandic": (138, 12),
        "l.ss02": (137, 10), "less": (142, 202), "minus": (184, 182), "multiply": (172, 168),
        "nine": (93, 94), "numbersign": (17, 19), "one": (68, 154), "one.ss01": (93, 154),
        "paragraph": (85, 157), "parenleft": (182, 70), "parenright": (70, 182),
        "plus": (159, 159), "plusminus": (174, 173), "quoteleft": (129, 64),
        "quoteright": (135, 58), "quotesingle": (182, 182), "registered": (78, 78),
        "section": (96, 95), "seven": (69, 70), "six": (94, 93), "six.ss01": (91, 91),
        "slash": (26, 26), "sterling": (87, 87), "t.1": (137, 27), "thorn": (138, 84),
        "three": (92, 91), "three.1": (91, 92), "trademark": (61, 82), "two": (120, 114),
        "u.1": (135, 135), "yen": (13, 10), "zero": (94, 94),
    },
    "Black": {
        "A": (38, 16), "B": (98, 79), "C": (86, 80), "D": (98, 86), "E": (106, 83),
        "F": (121, 32), "G": (86, 83), "H": (106, 138), "I": (110, 112), "J": (42, 117),
        "K": (110, 48), "L": (114, 48), "M": (110, 122), "N": (88, 121), "O": (86, 86),
        "P": (122, 59), "Q": (None, 87), "R": (110, 49), "S": (62, 70), "T": (63, 67),
        "U": (98, 118), "V": (46, 22), "W": (75, 39), "X": (49, 49), "Y": (6, 49),
        "Z": (67, 59), "a": (70, 67), "b": (105, 76), "c": (74, 61), "e": (67, 66),
        "f": (28, 28), "g": (78, 110), "h": (107, 111), "k": (102, 11), "l": (118, 120),
        "m": (114, 114), "n": (110, 114), "o": (81, 68), "p": (111, 59), "r": (112, 88),
        "s": (48, 52), "t": (5, 46), "u": (112, 117), "v": (19, 18), "w": (25, 6),
        "x": (-2, 21), "y": (-25, 16), "z": (82, 79), "AE": (54, 96), "Ezh": (65, 55),
        "G.1": (79, 102), "I.1": (66, 66), "OE": (79, 90), "Schwa": (85, 79),
        "Thorn": (106, 171), "a.1": (71, 110), "a.2": (57, 13), "ae": (58, 66),
        "ampersand": (73, -5), "asciicircum": (69, 69), "asciitilde": (161, 161),
        "asterisk": (222, 224), "at": (81, 82), "backslash": (20, 20), "bar": (235, 237),
        "braceleft": (154, 96), "braceright": (96, 154), "bracketleft": (155, 96),
        "bracketright": (96, 155), "brokenbar": (249, 249), "bullet": (99, 99),
        "dagger": (221, 223), "daggerdbl": (220, 223), "degree": (114, 114),
        "divide": (191, 191), "eight": (79, 79), "emdash": (0, 0), "endash": (0, 0),
        "equal": (187, 187), "eth": (71, 73), "euro": (76, 119), "f.1": (110, 14),
        "f.i": (12, -320), "f.i.1": (102, -320), "five": (73, 79), "florin": (123, 111),
        "four": (94, 79), "four.ss01": (94, 79), "germandbls": (103, 57),
        "greater": (195, 178), "guilsinglleft": (93, 82), "guilsinglright": (82, 93),
        "hyphen": (148, 148), "idotless": (113, 113), "jdotless": (-71, 111),
        "kgreenlandic": (110, -1), "l.ss02": (111, 13), "less": (178, 195),
        "minus": (185, 185), "multiply": (155, 155), "nine": (79, 79), "numbersign": (20, 20),
        "one": (101, 104), "one.ss01": (105, 104), "paragraph": (62, 103),
        "parenleft": (142, 52), "parenright": (52, 142), "plus": (191, 191),
        "plusminus": (185, 187), "quoteleft": (190, 95), "quoteright": (187, 98),
        "quotesingle": (214, 214), "registered": (106, 106), "section": (79, 79),
        "seven": (65, 64), "six": (79, 79), "six.ss01": (79, 79), "slash": (20, 20),
        "sterling": (91, 77), "t.1": (107, 41), "thorn": (110, 71), "three": (86, 79),
        "three.1": (86, 79), "trademark": (94, 101), "two": (80, 91), "u.1": (112, 112),
        "yen": (36, 37), "zero": (79, 79),
    },
}
SPACE = {"Thin": 523, "Regular": 515, "Black": 503}


# --- Applying -----------------------------------------------------------------------------

def shift(glyph, dx):
    for contour in glyph.contours:
        for p in contour.points:
            p.x += dx
    for c in glyph.components:
        t = c.transformation
        c.transformation = Transform(t[0], t[1], t[2], t[3], t[4] + dx, t[5])
    for a in glyph.anchors:
        a.x += dx


def depth_order(ufo):
    out, seen = [], set()
    def visit(name):
        if name in seen:
            return
        seen.add(name)
        for c in ufo[name].components:
            if c.baseGlyph in ufo:
                visit(c.baseGlyph)
        out.append(name)
    for name in sorted(ufo.keys()):
        visit(name)
    return out


def apply(ufo, master):
    """Set SIDES and SPACE in `ufo`; returns the glyphs that changed."""
    sides, moved, changed = SIDES.get(master, {}), {}, []
    for name in depth_order(ufo):
        glyph = ufo[name]
        m = dw = 0
        first = glyph.components[0] if glyph.components else None
        if first is not None and first.baseGlyph in moved:
            # Built on a glyph that moved: its ink moves with that glyph's.
            m0, dw = moved[first.baseGlyph]
            m = m0 if first.transformation[0] > 0 else dw - m0
            if glyph.contours:
                for contour in glyph.contours:
                    for p in contour.points:
                        p.x += m
                if first.transformation[0] < 0:
                    shift_component(first, dw)
                glyph.width += dw
            for a in glyph.anchors:
                a.x += m
        if name in sides:
            left, right = sides[name]
            b = glyph.getBounds(ufo)
            dx = 0 if left is None else round(left - b.xMin)
            shift(glyph, dx)
            width = round(b.xMax + dx + right)
            m, dw = m + dx, dw + width - glyph.width
            glyph.width = width
        if m or dw:
            moved[name] = (m, dw)
            changed.append(name)
    for name in SPACES:
        if master in SPACE and ufo[name].width != SPACE[master]:
            ufo[name].width = SPACE[master]
            changed.append(name)
    return changed


def shift_component(component, dx):
    t = component.transformation
    component.transformation = Transform(t[0], t[1], t[2], t[3], t[4] + dx, t[5])


# --- Measuring ----------------------------------------------------------------------------

class Outlines:
    """Profiles of a font's glyphs (a UFO, or Inter's layers for one master)."""

    def __init__(self, glyphs):
        self.glyphs, self.cache = glyphs, {}

    def width(self, name):
        return self.glyphs[name].width

    def profile(self, name, band):
        key = (name, band)
        if key not in self.cache:
            rec = DecomposingRecordingPen(self.glyphs)
            self.glyphs[name].draw(rec)
            ys = np.arange(band[0] + STEP / 2, band[1], STEP)
            left, right = np.full(len(ys), np.nan), np.full(len(ys), np.nan)
            for i, y in enumerate(ys):
                runs = strokes.cut(rec.replay, y + strokes.EPS)
                if runs:
                    left[i], right[i] = runs[0][0], runs[-1][1]
            self.cache[key] = (left, right)
        return self.cache[key]

    def extent(self, name):
        """The glyph's ink from bottom to top, as a band."""
        rec = DecomposingRecordingPen(self.glyphs)
        self.glyphs[name].draw(rec)
        pen = BoundsPen(None)
        rec.replay(pen)
        return (round(pen.bounds[1]), round(pen.bounds[3]))

    def plain(self, name, band):
        """(left, right) sidebearings of the ink inside the band."""
        left, right = self.profile(name, band)
        return np.nanmin(left), self.width(name) - np.nanmax(right)

    def optical(self, name, band, depth):
        """(left, right): sidebearing plus the profile's white, at most `depth` deep, averaged
        over the band (rows without ink count `depth`)."""
        left, right = self.profile(name, band)
        x0, x1 = np.nanmin(left), np.nanmax(right)
        dl = np.where(np.isnan(left), depth, np.minimum(left - x0, depth))
        dr = np.where(np.isnan(right), depth, np.minimum(x1 - right, depth))
        return x0 + dl.mean(), self.width(name) - x1 + dr.mean()


_inter = {}


def inter(master):
    if not _inter:
        import glyphsLib
        font = glyphsLib.GSFont(tabular.INTER)
        for m in font.masters:
            if m.axes[0] == 14:
                _inter[m.name] = Outlines({g.name: g.layers[m.id] for g in font.glyphs})
    return _inter[master]


def layout(ufo, text):
    """[(char, ink left, ink right)] for the text's letters, with widths and kerning."""
    cmap = {g.unicode: g.name for g in ufo if g.unicode is not None}
    x, prev, out = 0, None, []
    for ch in text:
        name = cmap[ord(ch)]
        if prev is not None:
            x += kern.kerning(ufo, prev, name)
        b = ufo[name].getBounds(ufo)
        if b is not None:
            out.append((ch, x + b.xMin, x + b.xMax))
        x, prev = x + ufo[name].width, name
    return out


def pairs(ufo, master):
    """[(left char, right char, across a word space, ours minus the mockup's gap)]."""
    targets = json.load(open(os.path.join(ROOT, "reference", TARGETS[master])))
    out = []
    for key, text in zip(("lower", "upper"), SENTENCES):
        mock, ours = targets[key]["letters"], layout(ufo, text)
        ends, n = set(), 0
        for word in text.split():
            n += len(word)
            ends.add(n - 1)
        for i in range(len(ours) - 1):
            err = (ours[i + 1][1] - ours[i][2]) - (mock[i + 1]["xMin"] - mock[i]["xMax"])
            out.append((ours[i][0], ours[i + 1][0], i in ends, err))
    return out


# --- Fitting ------------------------------------------------------------------------------

def unknown(ch, side):
    """The glyph side a letter's side is: d's left is b's right, Q's left is O's."""
    if ch in MIRRORED:
        return MIRRORED[ch], 1 - side
    if ch in LEFT_OF and side == 0:
        return LEFT_OF[ch], 0
    return GLYPH.get(ch, ch), side


def median(values):
    return float(np.median([v for v in values]))


def rule(ours, theirs, master, delta, optical):
    """{(name, side): change} for the round capitals' round sides, by ROUND."""
    out, band, theirs_band = {}, BANDS["upper"], INTER_BANDS["upper"]
    if ROUND == "inter":
        h = ours.plain("H", band), theirs.plain("H", theirs_band)
        ratio = (sum(h[0]) + delta[("H", 0)] + delta[("H", 1)]) / sum(h[1])
        for name, which in ROUND_SIDES.items():
            o, t = ours.plain(name, band), theirs.plain(name, theirs_band)
            out.update({(name, s): ratio * t[s] - o[s] for s in which})
    elif ROUND == "white":
        k = median((optical[(n, s)][0] + delta[(n, s)]) / optical[(n, s)][1]
                   for n, which in STEMS.items() for s in which)
        d = DEPTH[master][1]
        current = {(n, s): ours.plain(n, band)[s] for n, which in ROUND_SIDES.items() for s in which}
        wanted = {key: current[key] + k * optical[key][1] - optical[key][0] for key in current}
        even = sum(wanted.values()) / len(wanted)
        out = {key: even - current[key] for key in current}
    return out


def fit_master(ufo, master):
    """{glyph: (left, right)} and the space's width for one master."""
    ours, theirs = Outlines(ufo), inter(master)
    w_pair, w_word, w_prior = WEIGHTS[master]
    cases = {"lower": [GLYPH.get(c, c) for c in string.ascii_lowercase if c not in MIRRORED],
             "upper": [c for c in string.ascii_uppercase if c not in LEFT_OF] + ["Q"]}
    optical = {}   # (name, side) -> (ours, Inter's, case)
    for case, names_ in cases.items():
        depth = DEPTH[master][case == "upper"]
        for name in names_:
            o = ours.optical(name, BANDS[case], depth)
            t = theirs.optical(name, INTER_BANDS[case], depth)
            for side in (0, 1):
                if (name, side) != ("Q", 0):            # Q's left is O's
                    optical[(name, side)] = (o[side], t[side], case)
    names, rows = [], []
    def col(key):
        if key not in names:
            names.append(key)
        return names.index(key)
    for a, b, word, err in pairs(ufo, master):
        row = {}
        for key in (unknown(a, 1), unknown(b, 0)) + ((("space", 0),) if word else ()):
            row[col(key)] = row.get(col(key), 0) + 1
        rows.append((row, -err, w_word if word else w_pair))
    for key in optical:
        col(key)

    # Inter's proportions are taken at the median letter's fraction of Inter's, so solve
    # again with the solution's own medians until they stay put: refitting then changes
    # nothing.
    k = {case: median(o / t for o, t, c in optical.values() if c == case and t > 5)
         for case in cases}
    for _ in range(100):
        A = np.zeros((len(rows) + len(optical), len(names)))
        rhs = np.zeros(len(rows) + len(optical))
        for r, (row, value, w) in enumerate(rows):
            for c, v in row.items():
                A[r, c] = v * w
            rhs[r] = value * w
        for r, (key, (o, t, case)) in enumerate(optical.items(), len(rows)):
            A[r, col(key)] = w_prior
            rhs[r] = (k[case] * t - o) * w_prior
        delta = dict(zip(names, np.linalg.lstsq(A, rhs, rcond=None)[0]))
        new = {case: median((o + delta[key]) / t for key, (o, t, c) in optical.items()
                            if c == case and t > 5) for case in cases}
        settled = all(abs(new[c] - k[c]) < 1e-9 for c in cases)
        k = new
        if settled:
            break
    k_lower, k_upper = k["lower"], k["upper"]
    # The round capitals' round sides, if a ROUND rule sets them, after the rest are fitted.
    if ROUND != "mockup":
        delta.update(rule(ours, theirs, master, delta, optical))

    sides = {}
    def current(name):
        b = ufo[name].getBounds(ufo)
        return b.xMin, ufo[name].width - b.xMax
    for (name, side), d in delta.items():
        if name == "space":
            continue
        left, right = sides.get(name, current(name))
        sides[name] = (left + d, right) if side == 0 else (left, right + d)
    q_left, q_right = current("Q")
    sides["Q"] = (None, q_right + delta[("Q", 1)])
    # The rest: Inter's proportions at the median letter's of their case; figures at the
    # median of both cases'; the dlig pieces as their letter.
    def scaled(name, band, k, depth):
        o = ours.optical(name, BANDS[band], depth)
        t = theirs.optical(name, INTER_BANDS[band], depth)
        left, right = current(name)
        return left + k * t[0] - o[0], right + k * t[1] - o[1]
    for name in OTHERS:
        upper = (ufo[name].unicode and chr(ufo[name].unicode).isupper()) or name[0].isupper()
        sides[name] = scaled(name, "upper" if upper else "lower", k_upper if upper else k_lower,
                             DEPTH[master][bool(upper)])
    for name in FIGURES:
        sides[name] = scaled(name, "upper", (k_lower + k_upper) / 2, DEPTH[master][1])
    for name in PUNCTUATION:
        o = ours.optical(name, ours.extent(name), DEPTH[master][0])
        t = theirs.optical(name, theirs.extent(name), DEPTH[master][0])
        left, right = current(name)
        sides[name] = (left + k_lower * t[0] - o[0], right + k_lower * t[1] - o[1])
    for name, base in WITH.items():
        left, right = current(name)
        sides[name] = (left + delta[(base, 0)], right + delta[(base, 1)])
    space = ufo["space"].width + delta[("space", 0)]
    return ({n: (None if l is None else round(l), round(r)) for n, (l, r) in sides.items()},
            round(space))


def fit(src):
    sides, space = {}, {}
    for master in MASTERS:
        ufo = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
        sides[master], space[master] = fit_master(ufo, master)
    return sides, space


def show(sides, space):
    lines = ["SIDES = {"]
    for master, table in sides.items():
        lines.append(f'    "{master}": {{')
        line = "        "
        for name, (left, right) in sorted(table.items(), key=lambda kv: (len(kv[0]) > 1, kv[0])):
            piece = f'"{name}": ({left}, {right}), '
            if len(line) + len(piece) > 95:
                lines.append(line.rstrip())
                line = "        "
            line += piece
        lines.append(line.rstrip())
        lines.append("    },")
    lines.append("}")
    lines.append("SPACE = {" + ", ".join(f'"{m}": {w}' for m, w in space.items()) + "}")
    return "\n".join(lines)


def main(paths):
    import accents
    import kerning
    import stacked
    for path in paths:
        master = re.search(r"-(\w+)\.ufo", path).group(1)
        ufo = ufoLib2.Font.open(path)
        changed = apply(ufo, master)
        glyph_set = GlyphSet(f"{path}/glyphs")
        for name in changed:
            glyph_set.writeGlyph(name, ufo[name], ufo[name].drawPoints)
        print(f"{path}: {len(changed)} glyphs moved or widened ({master})")
    # What follows spacing in tools/to_ufo.py, as each tool does on its own.
    for path in paths:
        accents.run(path)
    stacked.main(paths)
    kerning.main(paths)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fit"]:
        print(show(*fit(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source"))))
    else:
        main(sys.argv[1:])
