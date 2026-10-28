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
tools/accents.py, tools/kern.py, tools/stacked.py and tools/tabular.py after.

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
        "A": (73, 42), "B": (199, 109), "C": (103, 93), "D": (188, 103), "E": (190, 97),
        "F": (184, 90), "G": (103, 131), "H": (193, 178), "I": (190, 192), "J": (129, 156),
        "K": (186, 34), "L": (180, 125), "M": (191, 188), "N": (196, 184), "O": (103, 103),
        "P": (188, 105), "Q": (None, 119), "R": (195, 108), "S": (125, 130), "T": (89, 83),
        "U": (157, 150), "V": (78, 49), "W": (18, 34), "X": (-4, 41), "Y": (43, 26),
        "Z": (114, 115), "a": (110, 155), "b": (196, 115), "c": (112, 98), "e": (115, 117),
        "f": (6, 26), "g": (102, 182), "h": (202, 183), "k": (181, 42), "l": (191, 198),
        "m": (172, 174), "n": (173, 189), "o": (112, 119), "p": (168, 119), "r": (196, 54),
        "s": (123, 121), "t": (24, 44), "u": (169, 175), "v": (72, 81), "w": (94, 65),
        "x": (46, 48), "y": (53, 76), "z": (107, 104), "AE": (38, 109), "Ezh": (91, 122),
        "G.1": (116, 154), "I.1": (84, 84), "OE": (113, 108), "Schwa": (129, 117),
        "Thorn": (181, 125), "a.1": (113, 182), "a.2": (93, 16), "ae": (94, 104),
        "ampersand": (111, 26), "asciicircum": (79, 79), "asciitilde": (171, 171),
        "asterisk": (115, 115), "at": (128, 128), "backslash": (50, 50), "bar": (235, 235),
        "braceleft": (146, 133), "braceright": (133, 146), "bracketleft": (235, 133),
        "bracketright": (133, 235), "brokenbar": (151, 151), "bullet": (354, 354),
        "dagger": (113, 113), "daggerdbl": (113, 113), "degree": (144, 144),
        "divide": (199, 199), "eight": (121, 121), "emdash": (0, 0), "endash": (0, 0),
        "equal": (271, 271), "eth": (112, 115), "euro": (52, 150), "f.1": (182, 14),
        "f.i": (34, 0), "f.i.1": (203, 0), "five": (120, 121), "florin": (-38, -38),
        "four": (120, 118), "four.ss01": (120, 118), "germandbls": (213, 138),
        "greater": (260, 185), "guilsinglleft": (81, 81), "guilsinglright": (81, 81),
        "hyphen": (158, 156), "idotless": (184, 184), "jdotless": (-38, 177),
        "kgreenlandic": (182, 53), "l.ss02": (181, 16), "less": (185, 260),
        "minus": (211, 211), "multiply": (197, 197), "nine": (122, 124),
        "numbersign": (30, 32), "one": (115, 207), "one.ss01": (107, 207),
        "paragraph": (126, 213), "parenleft": (213, 120), "parenright": (120, 213),
        "plus": (199, 199), "plusminus": (200, 200), "quoteleft": (161, 78),
        "quoteright": (161, 78), "quotesingle": (235, 235), "registered": (85, 85),
        "section": (127, 127), "seven": (98, 99), "six": (124, 122), "six.ss01": (120, 120),
        "slash": (50, 50), "sterling": (108, 123), "t.1": (179, 22), "thorn": (182, 114),
        "three": (129, 122), "three.1": (128, 120), "trademark": (64, 86), "two": (155, 148),
        "u.1": (180, 180), "yen": (29, 29), "zero": (124, 124),
    },
    "Regular": {
        "A": (36, 20), "B": (150, 97), "C": (88, 82), "D": (150, 88), "E": (149, 83),
        "F": (155, 37), "G": (88, 94), "H": (148, 157), "I": (150, 156), "J": (71, 141),
        "K": (151, 23), "L": (153, 78), "M": (150, 154), "N": (146, 155), "O": (88, 88),
        "P": (154, 84), "Q": (None, 96), "R": (149, 77), "S": (90, 91), "T": (64, 63),
        "U": (141, 144), "V": (54, 17), "W": (6, 21), "X": (-7, 28), "Y": (8, 23),
        "Z": (82, 70), "a": (86, 112), "b": (152, 86), "c": (91, 77), "e": (86, 90),
        "f": (7, 45), "g": (101, 139), "h": (145, 136), "k": (136, 12), "l": (148, 155),
        "m": (143, 135), "n": (122, 137), "o": (86, 84), "p": (138, 74), "r": (152, 41),
        "s": (75, 75), "t": (11, 40), "u": (135, 147), "v": (40, 40), "w": (58, 35),
        "x": (15, 34), "y": (6, 29), "z": (79, 74), "AE": (26, 104), "Ezh": (67, 87),
        "G.1": (92, 120), "I.1": (67, 67), "OE": (90, 100), "Schwa": (97, 92),
        "Thorn": (143, 125), "a.1": (84, 139), "a.2": (69, 10), "ae": (69, 80),
        "ampersand": (80, 14), "asciicircum": (60, 60), "asciitilde": (141, 141),
        "asterisk": (91, 91), "at": (98, 97), "backslash": (27, 27), "bar": (231, 231),
        "braceleft": (114, 98), "braceright": (98, 114), "bracketleft": (199, 98),
        "bracketright": (98, 199), "brokenbar": (166, 166), "bullet": (218, 218),
        "dagger": (88, 88), "daggerdbl": (91, 91), "degree": (107, 107), "divide": (173, 172),
        "eight": (94, 93), "emdash": (0, 0), "endash": (0, 0), "equal": (195, 194),
        "eth": (83, 86), "euro": (32, 96), "f.1": (139, 26), "f.i": (24, -217),
        "f.i.1": (143, -217), "five": (100, 95), "florin": (8, 6), "four": (91, 88),
        "four.ss01": (91, 88), "germandbls": (158, 93), "greater": (204, 143),
        "guilsinglleft": (75, 57), "guilsinglright": (57, 75), "hyphen": (127, 127),
        "idotless": (143, 148), "jdotless": (-52, 137), "kgreenlandic": (139, 12),
        "l.ss02": (137, 11), "less": (143, 204), "minus": (185, 183), "multiply": (174, 170),
        "nine": (95, 96), "numbersign": (18, 20), "one": (70, 156), "one.ss01": (95, 156),
        "paragraph": (86, 158), "parenleft": (184, 71), "parenright": (71, 184),
        "plus": (161, 161), "plusminus": (175, 174), "quoteleft": (131, 65),
        "quoteright": (136, 59), "quotesingle": (183, 183), "registered": (79, 79),
        "section": (97, 96), "seven": (71, 72), "six": (96, 95), "six.ss01": (94, 93),
        "slash": (27, 27), "sterling": (88, 88), "t.1": (138, 28), "thorn": (139, 85),
        "three": (94, 94), "three.1": (94, 95), "trademark": (62, 83), "two": (123, 116),
        "u.1": (136, 136), "yen": (14, 11), "zero": (96, 96),
    },
    "Black": {
        "A": (38, 16), "B": (96, 78), "C": (86, 79), "D": (96, 86), "E": (107, 82),
        "F": (119, 31), "G": (86, 80), "H": (106, 137), "I": (110, 112), "J": (40, 116),
        "K": (110, 46), "L": (112, 48), "M": (110, 122), "N": (88, 119), "O": (86, 86),
        "P": (122, 59), "Q": (None, 86), "R": (111, 48), "S": (62, 67), "T": (61, 67),
        "U": (99, 119), "V": (38, 21), "W": (77, 39), "X": (42, 47), "Y": (6, 47),
        "Z": (67, 58), "a": (70, 67), "b": (104, 75), "c": (74, 61), "e": (68, 65),
        "f": (26, 27), "g": (79, 107), "h": (107, 110), "k": (103, 8), "l": (115, 120),
        "m": (113, 113), "n": (110, 111), "o": (83, 67), "p": (111, 60), "r": (113, 87),
        "s": (48, 48), "t": (2, 47), "u": (112, 118), "v": (20, 17), "w": (26, 7),
        "x": (-13, 18), "y": (-24, 13), "z": (82, 78), "AE": (52, 93), "Ezh": (63, 53),
        "G.1": (77, 99), "I.1": (64, 64), "OE": (77, 87), "Schwa": (82, 77),
        "Thorn": (104, 167), "a.1": (67, 107), "a.2": (54, 10), "ae": (55, 63),
        "ampersand": (69, -8), "asciicircum": (65, 65), "asciitilde": (156, 156),
        "asterisk": (214, 216), "at": (77, 78), "backslash": (17, 17), "bar": (229, 231),
        "braceleft": (148, 91), "braceright": (91, 148), "bracketleft": (151, 91),
        "bracketright": (91, 151), "brokenbar": (242, 242), "bullet": (95, 95),
        "dagger": (213, 215), "daggerdbl": (213, 215), "degree": (110, 110),
        "divide": (184, 184), "eight": (76, 76), "emdash": (0, 0), "endash": (0, 0),
        "equal": (181, 181), "eth": (68, 69), "euro": (71, 114), "f.1": (107, 10),
        "f.i": (10, -321), "f.i.1": (100, -321), "five": (70, 76), "florin": (116, 105),
        "four": (91, 76), "four.ss01": (91, 76), "germandbls": (101, 54),
        "greater": (188, 171), "guilsinglleft": (88, 78), "guilsinglright": (78, 88),
        "hyphen": (144, 144), "idotless": (112, 113), "jdotless": (-73, 112),
        "kgreenlandic": (107, -3), "l.ss02": (108, 11), "less": (171, 188),
        "minus": (180, 180), "multiply": (149, 149), "nine": (76, 76), "numbersign": (17, 17),
        "one": (97, 101), "one.ss01": (102, 101), "paragraph": (58, 101),
        "parenleft": (137, 48), "parenright": (48, 137), "plus": (184, 184),
        "plusminus": (178, 181), "quoteleft": (183, 91), "quoteright": (180, 93),
        "quotesingle": (207, 207), "registered": (101, 102), "section": (75, 75),
        "seven": (62, 61), "six": (76, 76), "six.ss01": (76, 76), "slash": (17, 17),
        "sterling": (87, 72), "t.1": (104, 38), "thorn": (107, 68), "three": (83, 76),
        "three.1": (83, 77), "trademark": (90, 99), "two": (78, 88), "u.1": (108, 108),
        "yen": (33, 34), "zero": (76, 76),
    },
}
SPACE = {"Thin": 519, "Regular": 513, "Black": 506}


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


def proportions(ours, theirs, names, band, depth):
    """{(name, side): change to Inter's proportions at the median letter's}, and that median."""
    sides = {n: (ours.optical(n, BANDS[band], depth), theirs.optical(n, INTER_BANDS[band], depth))
             for n in names}
    k = float(np.median([o[s] / t[s] for o, t in sides.values() for s in (0, 1) if t[s] > 5]))
    return {(n, s): k * t[s] - o[s] for n, (o, t) in sides.items() for s in (0, 1)}, k


def fit_master(ufo, master):
    """{glyph: (left, right)} and the space's width for one master."""
    ours, theirs = Outlines(ufo), inter(master)
    w_pair, w_word, w_prior = WEIGHTS[master]
    lower = [GLYPH.get(c, c) for c in string.ascii_lowercase if c not in MIRRORED]
    upper = [c for c in string.ascii_uppercase if c not in LEFT_OF]
    prior, k_lower = proportions(ours, theirs, lower, "lower", DEPTH[master][0])
    upper_prior, k_upper = proportions(ours, theirs, upper, "upper", DEPTH[master][1])
    prior.update(upper_prior)
    o, t = (f.optical("Q", band, DEPTH[master][1])
            for f, band in ((ours, BANDS["upper"]), (theirs, INTER_BANDS["upper"])))
    prior[("Q", 1)] = k_upper * t[1] - o[1]   # Q's tail, at the capitals' median

    names, rows = [], []
    def col(key):
        if key not in names:
            names.append(key)
        return names.index(key)
    for a, b, word, err in pairs(ufo, master):
        row = {}
        for key in (unknown(a, 1), unknown(b, 0)):
            row[col(key)] = row.get(col(key), 0) + 1
        if word:
            row[col(("space", 0))] = 1
        rows.append((row, -err, w_word if word else w_pair))
    for key, change in prior.items():
        rows.append(({col(key): 1}, change, w_prior))
    A, rhs = np.zeros((len(rows), len(names))), np.zeros(len(rows))
    for r, (row, value, w) in enumerate(rows):
        for c, v in row.items():
            A[r, c] = v * w
        rhs[r] = value * w
    delta = dict(zip(names, np.linalg.lstsq(A, rhs, rcond=None)[0]))

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
    if ROUND == "inter":
        h = ours.plain("H", BANDS["upper"]), theirs.plain("H", INTER_BANDS["upper"])
        ratio = (sum(h[0]) + delta[("H", 0)] + delta[("H", 1)]) / sum(h[1])
        for name, which in ROUND_SIDES.items():
            o, t = ours.plain(name, BANDS["upper"]), theirs.plain(name, INTER_BANDS["upper"])
            new = list(sides[name])
            for side in which:
                new[side] = current(name)[side] + ratio * t[side] - o[side]
            sides[name] = tuple(new)
    elif ROUND == "white":
        d, band, theirs_band = DEPTH[master][1], BANDS["upper"], INTER_BANDS["upper"]
        k = float(np.median([(ours.optical(n, band, d)[s] + delta[(n, s)])
                             / theirs.optical(n, theirs_band, d)[s]
                             for n, which in STEMS.items() for s in which]))
        wanted = [current(n)[s] + k * theirs.optical(n, theirs_band, d)[s] - ours.optical(n, band, d)[s]
                  for n, which in ROUND_SIDES.items() for s in which]
        even = sum(wanted) / len(wanted)
        for name, which in ROUND_SIDES.items():
            sides[name] = tuple(even if s in which else sides[name][s] for s in (0, 1))

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
    kern.main(paths)
    stacked.main(paths)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--fit"]:
        print(show(*fit(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source"))))
    else:
        main(sys.argv[1:])
