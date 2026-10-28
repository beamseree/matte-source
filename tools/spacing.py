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
user chose this, "white", for consistency over the mockups' uneven round sides). The round
sides are held at the rule's values while the rest are solved, so their neighbours fit
against them (solving them as free sides first had left Black F's right side at -20).

The fit has structure, as Inter has: sides drawn the same way (SAME: the lowercase stems,
the bowls, the capital stems) share one unknown, so they come out one sidebearing in each
master, and SYMMETRIC letters get the same sidebearing on both sides. The pangrams' pairs had
made n's left 122 units and b's 156 on the same stem, and Y 43 units off centre in Black.
`--cost` prints what each of these costs in fit.py's gap error against the mockups. Black's
word space is WORD times n|n's gap rather than the mockup's (503 units, airy). Alternates
(FOLLOW) and the small figures and letters drawn on their own (SMALL) move with their
default glyph. LOOSEN makes Thin and Regular 8% looser than the mockups, for text, and
ASIDE leaves out four pangram pairs that alone set sides against Inter's proportions (the
user chose both). They act through `--fit`: refit after changing them.

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
       python tools/spacing.py --cost [source]   # gap error with each constraint on or off
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
          "kgreenlandic", "florin", "a.1", "a.2", "f.1", "t.1", "G.1", "I.1")
WITH = {"f.i": "f", "f.i.1": "f"}        # the dlig pieces before i move with their letter
# The round capitals' round sides: "mockup" fits them to the pangrams' pairs like the other
# letters; "inter" gives them the same fraction of Inter's sidebearings as H has; "white"
# makes them all one sidebearing, the one that leaves as much white beside them, against
# Inter's, as the straight capitals' stems have (our O is wider than Inter's, so its curve
# already leaves more white beside it than Inter's does).
ROUND = "white"
ROUND_SIDES = {"O": (0, 1), "C": (0,), "G": (0,), "D": (1,)}
# Sides drawn the same way share one sidebearing in each master, as in Inter: the fit solves
# one unknown for each set. d and q are b and p turned round, so b's and p's left sides are
# d's and q's right sides too: the lowercase stems' lefts and rights are one set, and so are
# the bowls'. The pangrams' pairs could otherwise give n's left 122 units and b's 156 on the
# same stem (Regular), and the capital stems a 34-unit spread in Black.
SAME = (
    (("n", 0), ("m", 0), ("h", 0), ("r", 0), ("b", 0), ("p", 0), ("k", 0), ("i", 0),
     ("n", 1), ("h", 1), ("m", 1), ("d", 1), ("q", 1), ("u", 1)),
    (("o", 0), ("c", 0), ("e", 0), ("d", 0), ("q", 0), ("g", 0), ("o", 1), ("b", 1), ("p", 1)),
    (("B", 0), ("D", 0), ("E", 0), ("F", 0), ("H", 0), ("I", 0), ("K", 0), ("L", 0), ("M", 0),
     ("N", 0), ("P", 0), ("R", 0), ("H", 1), ("I", 1), ("M", 1), ("N", 1)),
)
# Letters drawn the same on both sides get the same sidebearing on both (their Greek and
# Cyrillic twins are built on them and follow); Y had been 43 units off centre in Black.
SYMMETRIC = "AHIMNOUVWXYilovwx"
# The word space, where it isn't the mockups' (`--fit` solves it from their word gaps): as
# many times n|n's gap as the word gap n|space|n should be. The Black mockup's word gaps
# made it 503 units, 3.25 times the letter gap, where Inter's, SF Pro's and Graphik's Black
# have 2.9-3.0, and paragraphs looked airy.
WORD = {"Black": 3.0}
# Alternates move with their default letter, and the small figures, letters and signs
# drawn on their own (.sups, .dnom, .numr; the other .numr and the .subs are built on them)
# with theirs: each side is Inter's plus the default's change from Inter's, scaled by the
# glyph's height against the default's, so a side drawn like the default's keeps its
# sidebearing.
FOLLOW = {"u.1": "u", "l.ss02": "l"}
SMALL = (".sups", ".dnom", ".numr")
# Looser spacing than the mockups', per master: every side of the letters, figures and
# punctuation spacing.py sets gets the same white, (factor - 1) times its case's median
# optical sidebearing, so straight, round and diagonal sides loosen alike and the sets stay
# one value. The audit found 100-500 about as tight as a display face (n's sidebearing 0.251
# of its counter at 430; Inter's text cut 0.296). The user chose 8% over none and 12% from
# build/loose-compare/ (n 141 -> 152 at 430); Black stays the mockup's, so 500-800 loosen
# less.
LOOSEN = {"Thin": 1.08, "Regular": 1.08}
# Pangram pairs the fit leaves out. Each of these alone sets a side against Inter's
# proportions (F's right 41 units in Regular, 13 in Black, from "FO"; X's and x's sides
# from "OX" and "ox", Y's from "ZY"), and the sets and symmetry carry that to every pair
# with the letter. Left out, those sides take Inter's proportions, and the four pairs come
# out 30-55 units looser than the mockups' (93 in Black's ZY). The user chose to leave them
# out, from build/structure-compare/.
ASIDE = ("FO", "ZY", "OX", "ox")
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
        "A": (73, 73), "B": (199, 130), "C": (115, 107), "D": (199, 115), "E": (199, 115),
        "F": (199, 119), "G": (115, 129), "H": (199, 199), "I": (199, 199), "J": (137, 170),
        "K": (199, 46), "L": (199, 148), "M": (199, 199), "N": (199, 199), "O": (115, 115),
        "P": (199, 119), "Q": (None, 132), "R": (199, 144), "S": (138, 148), "T": (81, 102),
        "U": (170, 170), "V": (85, 85), "W": (50, 50), "X": (46, 46), "Y": (35, 35),
        "Z": (112, 107), "a": (132, 170), "b": (192, 134), "c": (134, 115), "e": (134, 145),
        "f": (23, 35), "g": (134, 194), "h": (192, 192), "k": (192, 62), "l": (204, 204),
        "m": (192, 192), "n": (192, 192), "o": (134, 134), "p": (192, 134), "r": (192, 72),
        "s": (138, 128), "t": (34, 80), "u": (177, 192), "v": (90, 90), "w": (92, 92),
        "x": (58, 58), "y": (69, 85), "z": (121, 119), "AE": (39, 105), "Ezh": (89, 120),
        "G.1": (116, 153), "I.1": (83, 83), "OE": (113, 105), "Schwa": (127, 117),
        "Thorn": (183, 123), "a.1": (126, 194), "a.1.sups": (98, 141), "a.2": (106, 28),
        "a.2.sups": (83, 28), "a.sups": (96, 129), "ae": (106, 116), "ampersand": (123, 39),
        "asciicircum": (91, 91), "asciitilde": (183, 182), "asterisk": (126, 126),
        "at": (140, 139), "b.sups": (141, 103), "backslash": (62, 62), "bar": (246, 246),
        "braceleft": (157, 144), "braceright": (144, 157), "bracketleft": (246, 144),
        "bracketleft.sups": (179, 111), "bracketright": (144, 246),
        "bracketright.sups": (111, 179), "brokenbar": (163, 163), "bullet": (363, 363),
        "c.sups": (103, 91), "d.sups": (103, 141), "dagger": (124, 124),
        "daggerdbl": (124, 124), "degree": (156, 156), "divide": (209, 209),
        "e.sups": (103, 108), "eight": (127, 127), "eight.dnom": (89, 89),
        "eight.sups": (104, 104), "emdash": (15, 15), "endash": (15, 15), "equal": (281, 281),
        "equal.dnom": (158, 158), "equal.sups": (157, 157), "eth": (125, 128),
        "euro": (65, 161), "f.1": (194, 26), "f.i": (51, 9), "f.i.1": (220, 9),
        "f.sups": (26, 34), "five": (125, 126), "five.dnom": (109, 89),
        "five.sups": (124, 104), "florin": (-26, -26), "four": (124, 121),
        "four.dnom": (90, 87), "four.ss01": (124, 121), "four.sups": (104, 81),
        "g.sups": (103, 142), "germandbls": (225, 150), "greater": (269, 196),
        "guilsinglleft": (94, 93), "guilsinglright": (93, 94), "h.sups": (141, 141),
        "hyphen": (171, 169), "i.numr": (111, 138), "i.sups": (123, 123),
        "idotless": (192, 192), "j.sups": (1, 126), "jdotless": (-25, 197),
        "k.sups": (141, 55), "kgreenlandic": (194, 65), "l.ss02": (204, 36),
        "l.sups": (147, 147), "less": (196, 269), "m.sups": (141, 141), "minus": (223, 223),
        "minus.dnom": (126, 126), "minus.sups": (133, 132), "multiply": (207, 207),
        "n.numr": (124, 172), "n.sups": (141, 141), "nine": (128, 131), "nine.dnom": (89, 91),
        "nine.sups": (104, 106), "numbersign": (43, 45), "o.sups": (103, 103),
        "one": (119, 212), "one.dnom": (79, 129), "one.ss01": (111, 212),
        "one.sups": (95, 155), "p.sups": (141, 103), "paragraph": (138, 225),
        "parenleft": (224, 132), "parenleft.dnom": (140, 83), "parenleft.sups": (167, 101),
        "parenright": (132, 224), "parenright.dnom": (83, 140), "parenright.sups": (101, 167),
        "plus": (209, 209), "plus.dnom": (125, 125), "plus.sups": (126, 126),
        "plusminus": (210, 210), "q.sups": (103, 141), "quoteleft": (173, 92),
        "quoteright": (173, 91), "quotesingle": (246, 246), "r.sups": (141, 61),
        "registered": (98, 98), "s.sups": (105, 98), "section": (139, 139),
        "seven": (102, 104), "seven.dnom": (74, 75), "seven.sups": (87, 88),
        "six": (131, 128), "six.dnom": (91, 89), "six.ss01": (125, 125),
        "six.sups": (106, 104), "slash": (62, 62), "sterling": (119, 134), "t.1": (191, 34),
        "t.sups": (31, 58), "thorn": (194, 126), "three": (134, 128), "three.1": (132, 126),
        "three.dnom": (98, 90), "three.sups": (112, 105), "trademark": (76, 100),
        "two": (158, 151), "two.dnom": (109, 103), "two.sups": (128, 122), "u.1": (177, 192),
        "u.sups": (133, 141), "v.sups": (73, 73), "w.sups": (79, 79), "x.sups": (53, 53),
        "y.sups": (62, 70), "yen": (42, 42), "z.sups": (101, 99), "zero": (131, 131),
        "zero.dnom": (91, 91), "zero.sups": (106, 106),
    },
    "Regular": {
        "A": (40, 40), "B": (165, 105), "C": (103, 92), "D": (165, 103), "E": (165, 92),
        "F": (165, 105), "G": (103, 106), "H": (165, 165), "I": (165, 165), "J": (84, 154),
        "K": (165, 35), "L": (165, 98), "M": (165, 165), "N": (165, 165), "O": (103, 103),
        "P": (165, 96), "Q": (None, 109), "R": (165, 93), "S": (102, 106), "T": (75, 70),
        "U": (153, 153), "V": (42, 42), "W": (18, 18), "X": (41, 41), "Y": (36, 36),
        "Z": (87, 99), "a": (102, 123), "b": (152, 106), "c": (106, 84), "e": (106, 112),
        "f": (18, 26), "g": (106, 152), "h": (152, 152), "k": (152, 30), "l": (161, 161),
        "m": (152, 152), "n": (152, 152), "o": (106, 106), "p": (152, 106), "r": (152, 44),
        "s": (66, 84), "t": (28, 56), "u": (144, 152), "v": (42, 42), "w": (43, 43),
        "x": (50, 50), "y": (17, 38), "z": (90, 85), "AE": (38, 116), "Ezh": (79, 99),
        "G.1": (104, 132), "I.1": (79, 79), "OE": (102, 112), "Schwa": (109, 104),
        "Thorn": (155, 137), "a.1": (97, 152), "a.1.sups": (79, 113), "a.2": (82, 22),
        "a.2.sups": (67, 30), "a.sups": (77, 98), "ae": (83, 93), "ampersand": (93, 27),
        "asciicircum": (73, 73), "asciitilde": (154, 155), "asterisk": (105, 105),
        "at": (111, 111), "b.sups": (114, 85), "backslash": (40, 40), "bar": (245, 245),
        "braceleft": (128, 112), "braceright": (112, 128), "bracketleft": (213, 112),
        "bracketleft.sups": (150, 94), "bracketright": (112, 213),
        "bracketright.sups": (94, 150), "brokenbar": (180, 180), "bullet": (233, 233),
        "c.sups": (85, 72), "d.sups": (85, 114), "dagger": (102, 102),
        "daggerdbl": (105, 105), "degree": (120, 120), "divide": (188, 186),
        "e.sups": (85, 87), "eight": (106, 106), "eight.dnom": (70, 69),
        "eight.sups": (85, 84), "emdash": (11, 11), "endash": (11, 11), "equal": (209, 208),
        "equal.dnom": (123, 123), "equal.sups": (139, 139), "eth": (96, 99),
        "euro": (45, 109), "f.1": (152, 39), "f.i": (35, -236), "f.i.1": (154, -236),
        "f.sups": (31, 27), "five": (113, 107), "five.dnom": (108, 70),
        "five.sups": (115, 85), "florin": (21, 20), "four": (104, 101), "four.dnom": (82, 78),
        "four.ss01": (104, 101), "four.sups": (92, 85), "g.sups": (85, 114),
        "germandbls": (172, 106), "greater": (219, 158), "guilsinglleft": (88, 70),
        "guilsinglright": (70, 88), "h.sups": (114, 114), "hyphen": (140, 140),
        "i.numr": (91, 142), "i.sups": (111, 113), "idotless": (152, 152),
        "j.sups": (-16, 111), "jdotless": (-42, 150), "k.sups": (114, 38),
        "kgreenlandic": (152, 25), "l.ss02": (161, 28), "l.sups": (119, 119),
        "less": (158, 219), "m.sups": (114, 114), "minus": (198, 197),
        "minus.dnom": (107, 107), "minus.sups": (129, 130), "multiply": (189, 184),
        "n.numr": (92, 152), "n.sups": (114, 114), "nine": (108, 109), "nine.dnom": (70, 71),
        "nine.sups": (85, 86), "numbersign": (31, 33), "o.sups": (85, 85), "one": (83, 168),
        "one.dnom": (68, 95), "one.ss01": (108, 168), "one.sups": (92, 118),
        "p.sups": (114, 85), "paragraph": (100, 172), "parenleft": (198, 85),
        "parenleft.dnom": (122, 54), "parenleft.sups": (136, 72), "parenright": (85, 198),
        "parenright.dnom": (54, 122), "parenright.sups": (72, 136), "plus": (176, 176),
        "plus.dnom": (110, 110), "plus.sups": (126, 126), "plusminus": (190, 189),
        "q.sups": (85, 114), "quoteleft": (144, 77), "quoteright": (149, 72),
        "quotesingle": (197, 197), "r.sups": (114, 48), "registered": (92, 92),
        "s.sups": (59, 70), "section": (110, 110), "seven": (84, 85), "seven.dnom": (63, 64),
        "seven.sups": (74, 75), "six": (109, 108), "six.dnom": (71, 70),
        "six.ss01": (106, 106), "six.sups": (86, 85), "slash": (40, 40),
        "sterling": (102, 102), "t.1": (151, 41), "t.sups": (37, 50), "thorn": (152, 98),
        "three": (107, 106), "three.1": (107, 107), "three.dnom": (90, 70),
        "three.sups": (93, 84), "trademark": (75, 95), "two": (136, 129),
        "two.dnom": (89, 88), "two.sups": (102, 99), "u.1": (144, 152), "u.sups": (109, 114),
        "v.sups": (46, 46), "w.sups": (35, 35), "x.sups": (46, 46), "y.sups": (32, 44),
        "yen": (27, 24), "z.sups": (89, 87), "zero": (109, 109), "zero.dnom": (71, 71),
        "zero.sups": (86, 86),
    },
    "Black": {
        "A": (27, 27), "B": (116, 73), "C": (93, 74), "D": (116, 93), "E": (116, 77),
        "F": (116, 62), "G": (93, 85), "H": (116, 116), "I": (116, 116), "J": (42, 103),
        "K": (116, 42), "L": (116, 60), "M": (116, 116), "N": (116, 116), "O": (93, 93),
        "P": (116, 59), "Q": (None, 73), "R": (116, 30), "S": (62, 63), "T": (75, 57),
        "U": (112, 112), "V": (22, 22), "W": (36, 36), "X": (53, 53), "Y": (47, 47),
        "Z": (57, 110), "a": (70, 66), "b": (113, 73), "c": (73, 50), "e": (73, 65),
        "f": (30, 37), "g": (73, 111), "h": (113, 113), "k": (113, 9), "l": (121, 121),
        "m": (113, 113), "n": (113, 113), "o": (73, 73), "p": (113, 73), "r": (113, 96),
        "s": (35, 58), "t": (3, 40), "u": (110, 113), "v": (13, 13), "w": (12, 12),
        "x": (25, 25), "y": (-26, 19), "z": (83, 80), "AE": (56, 98), "Ezh": (67, 57),
        "G.1": (81, 104), "I.1": (67, 67), "OE": (81, 92), "Schwa": (87, 81),
        "Thorn": (108, 174), "a.1": (72, 111), "a.1.sups": (89, 113), "a.2": (59, 14),
        "a.2.sups": (75, 39), "a.sups": (82, 89), "ae": (59, 68), "ampersand": (75, -4),
        "asciicircum": (71, 71), "asciitilde": (164, 164), "asterisk": (226, 228),
        "at": (83, 84), "b.sups": (116, 90), "backslash": (21, 21), "bar": (238, 240),
        "braceleft": (157, 98), "braceright": (98, 157), "bracketleft": (157, 98),
        "bracketleft.sups": (152, 110), "bracketright": (98, 157),
        "bracketright.sups": (110, 152), "brokenbar": (253, 253), "bullet": (101, 101),
        "c.sups": (90, 77), "d.sups": (90, 116), "dagger": (225, 227),
        "daggerdbl": (224, 226), "degree": (116, 116), "divide": (195, 195),
        "e.sups": (90, 86), "eight": (81, 81), "eight.dnom": (65, 65),
        "eight.sups": (101, 101), "emdash": (0, 0), "endash": (0, 0), "equal": (190, 190),
        "equal.dnom": (116, 116), "equal.sups": (166, 166), "eth": (73, 74),
        "euro": (78, 122), "f.1": (111, 16), "f.i": (14, -311), "f.i.1": (104, -311),
        "f.sups": (59, 48), "five": (75, 81), "five.dnom": (102, 65), "five.sups": (140, 101),
        "florin": (126, 114), "four": (96, 81), "four.dnom": (70, 53), "four.ss01": (96, 81),
        "four.sups": (107, 86), "g.sups": (90, 115), "germandbls": (105, 58),
        "greater": (198, 181), "guilsinglleft": (95, 85), "guilsinglright": (85, 95),
        "h.sups": (116, 116), "hyphen": (150, 150), "i.numr": (44, 153), "i.sups": (100, 100),
        "idotless": (113, 113), "j.sups": (-3, 100), "jdotless": (-71, 113),
        "k.sups": (116, 47), "kgreenlandic": (111, 0), "l.ss02": (121, 24),
        "l.sups": (121, 121), "less": (181, 198), "m.sups": (117, 117), "minus": (188, 188),
        "minus.dnom": (111, 111), "minus.sups": (168, 169), "multiply": (159, 159),
        "n.numr": (72, 195), "n.sups": (117, 117), "nine": (81, 81), "nine.dnom": (65, 65),
        "nine.sups": (101, 101), "numbersign": (21, 21), "o.sups": (90, 90),
        "one": (103, 105), "one.dnom": (92, 69), "one.ss01": (108, 105),
        "one.sups": (129, 109), "p.sups": (116, 90), "paragraph": (63, 105),
        "parenleft": (145, 54), "parenleft.dnom": (96, 39), "parenleft.sups": (142, 75),
        "parenright": (53, 145), "parenright.dnom": (39, 96), "parenright.sups": (74, 142),
        "plus": (194, 194), "plus.dnom": (120, 120), "plus.sups": (171, 171),
        "plusminus": (188, 190), "q.sups": (90, 116), "quoteleft": (193, 97),
        "quoteright": (190, 100), "quotesingle": (217, 217), "r.sups": (117, 103),
        "registered": (108, 108), "s.sups": (87, 85), "section": (81, 81), "seven": (66, 66),
        "seven.dnom": (51, 50), "seven.sups": (86, 85), "six": (81, 81), "six.dnom": (65, 65),
        "six.ss01": (81, 81), "six.sups": (101, 101), "slash": (21, 21), "sterling": (93, 79),
        "t.1": (109, 42), "t.sups": (43, 62), "thorn": (111, 73), "three": (88, 81),
        "three.1": (88, 81), "three.dnom": (60, 65), "three.sups": (97, 101),
        "trademark": (96, 103), "two": (82, 93), "two.dnom": (54, 61), "two.sups": (91, 100),
        "u.1": (110, 113), "u.sups": (115, 117), "v.sups": (51, 51), "w.sups": (43, 43),
        "x.sups": (65, 65), "y.sups": (29, 55), "yen": (38, 39), "z.sups": (103, 101),
        "zero": (81, 81), "zero.dnom": (65, 65), "zero.sups": (101, 101),
    },
}
SPACE = {"Thin": 525, "Regular": 511, "Black": 453}


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

    def bounds(self, name):
        rec = DecomposingRecordingPen(self.glyphs)
        self.glyphs[name].draw(rec)
        pen = BoundsPen(None)
        rec.replay(pen)
        return pen.bounds

    def extent(self, name):
        """The glyph's ink from bottom to top, as a band."""
        b = self.bounds(name)
        return (round(b[1]), round(b[3]))

    def sides(self, name):
        """(left, right) sidebearings of all the glyph's ink."""
        b = self.bounds(name)
        return b[0], self.width(name) - b[2]

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


def classes(keys, same, symmetric):
    """{side: number of its set}: the sides `same` and `symmetric` make equal share one."""
    parent = {k: k for k in keys}
    def find(k):
        while parent[k] != k:
            k = parent[k]
        return k
    links = [[unknown(c, s) for c, s in group] for group in same]
    links += [[unknown(c, 0), unknown(c, 1)] for c in symmetric]
    for group in links:
        group = [k for k in group if k in parent]
        for k in group[1:]:
            a, b = find(k), find(group[0])
            if a != b:
                parent[a] = b
    roots = list(dict.fromkeys(find(k) for k in keys))
    return {k: roots.index(find(k)) for k in keys}


def fit_master(ufo, master, same=SAME, symmetric=SYMMETRIC, word=WORD):
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
    for a, b, word_space, err in pairs(ufo, master):
        row = {}
        for key in (unknown(a, 1), unknown(b, 0)) + ((("space", 0),) if word_space else ()):
            row[col(key)] = row.get(col(key), 0) + 1
        rows.append((row, -err, 0 if a + b in ASIDE else w_word if word_space else w_pair))
    for key in optical:
        col(key)

    def current(name):
        b = ufo[name].getBounds(ufo)
        return b.xMin, ufo[name].width - b.xMax
    # Sides that come out equal share one unknown, their sidebearing: each side's change is
    # that minus its own sidebearing now.
    cur = np.array([0.0 if n == "space" else current(n)[s] for n, s in names])
    sets = classes(names, same, symmetric)
    M = np.zeros((len(names), max(sets.values()) + 1))
    for i, key in enumerate(names):
        M[i, sets[key]] = 1

    # Inter's proportions are taken at the median letter's fraction of Inter's, so solve
    # again with the solution's own medians until they stay put: refitting then changes
    # nothing. A ROUND rule's round sides are held at the rule's values in the solve, so
    # their neighbours fit against them, and the rule follows the solution the same way.
    k = {case: median(o / t for o, t, c in optical.values() if c == case and t > 5)
         for case in cases}
    fixed = {}
    for _ in range(200):
        A = np.zeros((len(rows) + len(optical), len(names)))
        rhs = np.zeros(len(rows) + len(optical))
        for r, (row, value, w) in enumerate(rows):
            for c, v in row.items():
                A[r, c] = v * w
            rhs[r] = value * w
        for r, (key, (o, t, case)) in enumerate(optical.items(), len(rows)):
            A[r, col(key)] = w_prior
            rhs[r] = (k[case] * t - o) * w_prior
        held, base = M.copy(), -cur
        for key, d in fixed.items():
            held[names.index(key)] = 0
            base[names.index(key)] = d
        v = np.linalg.lstsq(A @ held, rhs - A @ base, rcond=None)[0]
        delta = dict(zip(names, held @ v + base))
        new = {case: median((o + delta[key]) / t for key, (o, t, c) in optical.items()
                            if c == case and t > 5) for case in cases}
        rounds = rule(ours, theirs, master, delta, optical) if ROUND != "mockup" else {}
        settled = all(abs(new[c] - k[c]) < 1e-9 for c in cases) and \
            all(abs(d - fixed.get(key, np.inf)) < 1e-6 for key, d in rounds.items())
        k, fixed = new, rounds
        if settled:
            break
    k_lower, k_upper = k["lower"], k["upper"]

    sides = {}
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
    # Looser spacing: the same white added to every side of a case, (factor - 1) times the
    # case's median optical sidebearing after the fit, so the sets stay one value.
    factor = LOOSEN.get(master, 1)
    if factor != 1:
        white = {case: (factor - 1) * median(o + delta[key] for key, (o, t, c) in optical.items()
                                             if c == case) for case in cases}
        white["figure"] = (white["lower"] + white["upper"]) / 2
        def kind(name):
            if name in FIGURES:
                return "figure"
            upper = name in cases["upper"] or (name in OTHERS and name[0].isupper())
            return "upper" if upper else "lower"
        sides = {name: tuple(None if v is None else v + white[kind(name)] for v in sides[name])
                 for name in sides}
    # Alternates and the small glyphs, after their defaults.
    def moved(name):
        """A default's sides after the fit (d and q move with b and p, i and j with ı and ȷ)."""
        base = MIRRORED.get(name, GLYPH.get(name, name))
        if base not in sides:
            return current(name)
        change = [s - c for s, c in zip(sides[base], current(base))]
        if name in MIRRORED:
            change.reverse()
        return tuple(c + d for c, d in zip(current(name), change))
    small = [(n, n.rsplit(".", 1)[0]) for n in sorted(ufo.keys())
             if n.endswith(SMALL) and ufo[n].contours]
    for name, base in list(FOLLOW.items()) + small:
        if base not in ufo or base not in theirs.glyphs:
            continue
        height = lambda n: theirs.bounds(n)[3] - theirs.bounds(n)[1]
        scale = height(name) / height(base)
        t, t_base = theirs.sides(name), theirs.sides(base)
        sides[name] = tuple(t[s] + scale * (moved(base)[s] - t_base[s]) for s in (0, 1))
    space = ufo["space"].width + delta[("space", 0)]
    if master in word:
        space = (word[master] - 1) * sum(sides["n"])
    return ({n: (None if l is None else round(l), round(r)) for n, (l, r) in sides.items()},
            round(space))


def cost(src):
    """fit.py's gap error against the mockups (mean |ours - mockup| over the pangrams' gaps,
    all / inside words / across word spaces) with each constraint on or off, at the
    current kerning: the pairs' errors move by their sides' changes."""
    variants = (("no sets, mockup space", (), "", {}),
                ("SYMMETRIC", (), SYMMETRIC, {}),
                ("SAME", SAME, "", {}),
                ("SAME + SYMMETRIC", SAME, SYMMETRIC, {}),
                ("SAME + SYMMETRIC + WORD", SAME, SYMMETRIC, WORD))
    for master in MASTERS:
        ufo = ufoLib2.Font.open(os.path.join(src, f"PlaceholderSans-{master}.ufo"))
        found = pairs(ufo, master)
        for label, same, symmetric, word in variants:
            sides, space = fit_master(ufo, master, same, symmetric, word)
            def change(key):
                name, side = key
                if name == "space":
                    return space - ufo["space"].width
                b = ufo[name].getBounds(ufo)
                now = (b.xMin, ufo[name].width - b.xMax)[side]
                new = sides[name][side]
                return 0 if new is None else new - now
            errs = [(err + change(unknown(a, 1)) + change(unknown(b, 0))
                     + (change(("space", 0)) if w else 0), w) for a, b, w, err in found]
            mean = lambda v: sum(abs(e) for e in v) / len(v)
            print(f"{master:8s} {label:24s} all {mean([e for e, _ in errs]):5.2f}  "
                  f"in words {mean([e for e, w in errs if not w]):5.2f}  "
                  f"across spaces {mean([e for e, w in errs if w]):5.2f}  (space {space})")


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
    elif sys.argv[1:2] == ["--cost"]:
        cost(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "source"))
    else:
        main(sys.argv[1:])
