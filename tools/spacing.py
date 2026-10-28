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
default glyph. LOOSEN (looser text spacing) and ASIDE (pangram pairs left out) are the
user's to choose, and empty until then.

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
# of its counter at 430; Inter's text cut 0.296). The user chooses from
# build/loose-compare/; none until then.
LOOSEN = {}
# Pangram pairs the fit leaves out. Each of these alone sets a side against Inter's
# proportions (F's right 41 units in Regular, 13 in Black, from "FO"; X's and x's sides
# from "OX" and "ox", Y's from "ZY"), and the sets and symmetry carry that to every pair
# with the letter. Left out, those sides take Inter's proportions, and the four pairs come
# out 30-55 units looser than the mockups' (93 in Black's ZY). The user chooses, from
# build/structure-compare/; none until then.
ASIDE = ()
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
        "A": (59, 59), "B": (185, 115), "C": (100, 92), "D": (185, 100), "E": (185, 101),
        "F": (185, 112), "G": (100, 114), "H": (185, 185), "I": (185, 185), "J": (128, 155),
        "K": (185, 32), "L": (185, 134), "M": (185, 185), "N": (185, 185), "O": (100, 100),
        "P": (185, 104), "Q": (None, 118), "R": (185, 130), "S": (123, 134), "T": (67, 87),
        "U": (155, 155), "V": (70, 70), "W": (35, 35), "X": (20, 20), "Y": (31, 31),
        "Z": (97, 122), "a": (117, 155), "b": (177, 119), "c": (119, 100), "e": (119, 130),
        "f": (8, 20), "g": (119, 179), "h": (177, 177), "k": (177, 48), "l": (189, 189),
        "m": (177, 177), "n": (177, 177), "o": (119, 119), "p": (177, 119), "r": (177, 56),
        "s": (123, 113), "t": (19, 65), "u": (162, 177), "v": (75, 75), "w": (77, 77),
        "x": (45, 45), "y": (54, 70), "z": (106, 104), "AE": (25, 91), "Ezh": (74, 105),
        "G.1": (101, 138), "I.1": (68, 68), "OE": (98, 90), "Schwa": (112, 102),
        "Thorn": (168, 108), "a.1": (111, 179), "a.1.sups": (90, 133), "a.2": (91, 13),
        "a.2.sups": (75, 20), "a.sups": (89, 122), "ae": (91, 101), "ampersand": (108, 24),
        "asciicircum": (76, 76), "asciitilde": (168, 167), "asterisk": (111, 111),
        "at": (125, 124), "b.sups": (133, 95), "backslash": (47, 47), "bar": (231, 231),
        "braceleft": (142, 129), "braceright": (129, 142), "bracketleft": (231, 129),
        "bracketleft.sups": (171, 103), "bracketright": (129, 231),
        "bracketright.sups": (103, 171), "brokenbar": (148, 148), "bullet": (348, 348),
        "c.sups": (95, 84), "d.sups": (95, 133), "dagger": (109, 109),
        "daggerdbl": (109, 109), "degree": (141, 141), "divide": (194, 194),
        "e.sups": (95, 100), "eight": (112, 112), "eight.dnom": (81, 82),
        "eight.sups": (96, 97), "emdash": (0, 0), "endash": (0, 0), "equal": (265, 265),
        "equal.dnom": (149, 149), "equal.sups": (148, 148), "eth": (110, 113),
        "euro": (50, 146), "f.1": (179, 11), "f.i": (36, -6), "f.i.1": (205, -6),
        "f.sups": (18, 26), "five": (110, 111), "five.dnom": (102, 81),
        "five.sups": (117, 96), "florin": (-41, -41), "four": (109, 106),
        "four.dnom": (82, 79), "four.ss01": (109, 106), "four.sups": (96, 73),
        "g.sups": (95, 134), "germandbls": (210, 135), "greater": (254, 181),
        "guilsinglleft": (79, 78), "guilsinglright": (78, 79), "h.sups": (133, 133),
        "hyphen": (155, 154), "i.numr": (100, 128), "i.sups": (116, 116),
        "idotless": (177, 177), "j.sups": (-7, 119), "jdotless": (-41, 182),
        "k.sups": (133, 47), "kgreenlandic": (179, 50), "l.ss02": (189, 21),
        "l.sups": (139, 139), "less": (181, 254), "m.sups": (133, 133), "minus": (208, 208),
        "minus.dnom": (111, 111), "minus.sups": (118, 117), "multiply": (192, 192),
        "n.numr": (113, 161), "n.sups": (133, 133), "nine": (113, 116), "nine.dnom": (82, 84),
        "nine.sups": (97, 99), "numbersign": (28, 30), "o.sups": (95, 95), "one": (104, 198),
        "one.dnom": (71, 121), "one.ss01": (96, 198), "one.sups": (87, 147),
        "p.sups": (133, 95), "paragraph": (122, 210), "parenleft": (209, 117),
        "parenleft.dnom": (132, 75), "parenleft.sups": (159, 93), "parenright": (117, 209),
        "parenright.dnom": (75, 132), "parenright.sups": (93, 159), "plus": (194, 194),
        "plus.dnom": (116, 116), "plus.sups": (118, 118), "plusminus": (195, 195),
        "q.sups": (95, 133), "quoteleft": (157, 77), "quoteright": (158, 76),
        "quotesingle": (231, 231), "r.sups": (133, 53), "registered": (83, 83),
        "s.sups": (97, 90), "section": (124, 124), "seven": (87, 89), "seven.dnom": (66, 67),
        "seven.sups": (79, 80), "six": (116, 113), "six.dnom": (84, 82),
        "six.ss01": (110, 110), "six.sups": (99, 97), "slash": (47, 47),
        "sterling": (104, 119), "t.1": (176, 19), "t.sups": (24, 50), "thorn": (179, 111),
        "three": (119, 113), "three.1": (117, 111), "three.dnom": (91, 82),
        "three.sups": (105, 97), "trademark": (61, 85), "two": (143, 136),
        "two.dnom": (101, 95), "two.sups": (120, 114), "u.1": (162, 177),
        "u.sups": (125, 133), "v.sups": (65, 65), "w.sups": (71, 71), "x.sups": (46, 46),
        "y.sups": (54, 63), "yen": (27, 27), "z.sups": (93, 92), "zero": (116, 116),
        "zero.dnom": (83, 83), "zero.sups": (98, 98),
    },
    "Regular": {
        "A": (28, 28), "B": (153, 93), "C": (91, 80), "D": (153, 91), "E": (153, 80),
        "F": (153, 41), "G": (91, 94), "H": (153, 153), "I": (153, 153), "J": (86, 141),
        "K": (153, 20), "L": (153, 86), "M": (153, 153), "N": (153, 153), "O": (91, 91),
        "P": (153, 84), "Q": (None, 96), "R": (153, 80), "S": (90, 92), "T": (61, 58),
        "U": (141, 141), "V": (30, 30), "W": (6, 6), "X": (-4, -4), "Y": (14, 14),
        "Z": (74, 64), "a": (92, 112), "b": (141, 95), "c": (95, 73), "e": (95, 101),
        "f": (5, 14), "g": (95, 141), "h": (141, 141), "k": (141, 17), "l": (148, 148),
        "m": (141, 141), "n": (141, 141), "o": (95, 95), "p": (141, 95), "r": (141, 33),
        "s": (55, 70), "t": (14, 44), "u": (133, 141), "v": (31, 31), "w": (32, 32),
        "x": (5, 5), "y": (5, 25), "z": (79, 74), "AE": (26, 104), "Ezh": (66, 87),
        "G.1": (91, 120), "I.1": (66, 66), "OE": (90, 100), "Schwa": (97, 92),
        "Thorn": (143, 125), "a.1": (86, 141), "a.1.sups": (73, 107), "a.2": (71, 11),
        "a.2.sups": (60, 23), "a.sups": (71, 92), "ae": (71, 82), "ampersand": (82, 16),
        "asciicircum": (62, 62), "asciitilde": (143, 143), "asterisk": (93, 93),
        "at": (100, 99), "b.sups": (108, 79), "backslash": (29, 29), "bar": (233, 233),
        "braceleft": (117, 101), "braceright": (101, 117), "bracketleft": (201, 101),
        "bracketleft.sups": (144, 88), "bracketright": (101, 201),
        "bracketright.sups": (88, 144), "brokenbar": (169, 169), "bullet": (222, 222),
        "c.sups": (79, 66), "d.sups": (79, 108), "dagger": (91, 91), "daggerdbl": (94, 94),
        "degree": (109, 109), "divide": (177, 175), "e.sups": (79, 81), "eight": (95, 94),
        "eight.dnom": (63, 63), "eight.sups": (78, 78), "emdash": (0, 0), "endash": (0, 0),
        "equal": (198, 197), "equal.dnom": (116, 116), "equal.sups": (131, 131),
        "eth": (85, 87), "euro": (34, 98), "f.1": (141, 28), "f.i": (22, -248),
        "f.i.1": (141, -248), "f.sups": (23, 20), "five": (101, 96), "five.dnom": (101, 64),
        "five.sups": (108, 79), "florin": (10, 9), "four": (92, 89), "four.dnom": (76, 71),
        "four.ss01": (92, 89), "four.sups": (86, 78), "g.sups": (79, 108),
        "germandbls": (160, 95), "greater": (207, 147), "guilsinglleft": (77, 59),
        "guilsinglright": (59, 77), "h.sups": (108, 108), "hyphen": (128, 128),
        "i.numr": (84, 134), "i.sups": (104, 106), "idotless": (141, 141),
        "j.sups": (-14, 105), "jdotless": (-38, 139), "k.sups": (108, 31),
        "kgreenlandic": (141, 14), "l.ss02": (148, 15), "l.sups": (112, 112),
        "less": (147, 207), "m.sups": (108, 108), "minus": (187, 185), "minus.dnom": (98, 99),
        "minus.sups": (120, 120), "multiply": (177, 173), "n.numr": (84, 144),
        "n.sups": (108, 108), "nine": (96, 97), "nine.dnom": (64, 64), "nine.sups": (79, 79),
        "numbersign": (19, 21), "o.sups": (79, 79), "one": (71, 157), "one.dnom": (61, 88),
        "one.ss01": (97, 157), "one.sups": (85, 111), "p.sups": (108, 79),
        "paragraph": (88, 160), "parenleft": (187, 74), "parenleft.dnom": (116, 48),
        "parenleft.sups": (130, 66), "parenright": (74, 187), "parenright.dnom": (48, 116),
        "parenright.sups": (66, 130), "plus": (164, 164), "plus.dnom": (104, 104),
        "plus.sups": (119, 119), "plusminus": (179, 178), "q.sups": (79, 108),
        "quoteleft": (133, 66), "quoteright": (138, 61), "quotesingle": (185, 185),
        "r.sups": (107, 42), "registered": (81, 81), "s.sups": (53, 62), "section": (99, 98),
        "seven": (72, 73), "seven.dnom": (57, 57), "seven.sups": (68, 68), "six": (97, 96),
        "six.dnom": (64, 64), "six.ss01": (95, 95), "six.sups": (79, 79), "slash": (29, 29),
        "sterling": (91, 91), "t.1": (140, 29), "t.sups": (29, 44), "thorn": (141, 87),
        "three": (95, 95), "three.1": (95, 96), "three.dnom": (84, 63),
        "three.sups": (87, 78), "trademark": (64, 84), "two": (124, 117),
        "two.dnom": (83, 81), "two.sups": (96, 92), "u.1": (133, 141), "u.sups": (103, 108),
        "v.sups": (40, 40), "w.sups": (29, 29), "x.sups": (21, 21), "y.sups": (26, 37),
        "yen": (15, 13), "z.sups": (83, 80), "zero": (97, 97), "zero.dnom": (64, 64),
        "zero.sups": (79, 79),
    },
    "Black": {
        "A": (27, 27), "B": (116, 73), "C": (93, 74), "D": (116, 93), "E": (116, 77),
        "F": (116, 13), "G": (93, 84), "H": (116, 116), "I": (116, 116), "J": (47, 103),
        "K": (116, 38), "L": (116, 59), "M": (116, 116), "N": (116, 116), "O": (93, 93),
        "P": (116, 59), "Q": (None, 73), "R": (116, 30), "S": (62, 60), "T": (72, 57),
        "U": (112, 112), "V": (22, 22), "W": (36, 36), "X": (37, 37), "Y": (22, 22),
        "Z": (56, 42), "a": (72, 66), "b": (113, 73), "c": (73, 50), "e": (73, 65),
        "f": (27, 37), "g": (73, 111), "h": (113, 113), "k": (113, 6), "l": (119, 119),
        "m": (113, 113), "n": (113, 113), "o": (73, 73), "p": (113, 73), "r": (113, 96),
        "s": (35, 55), "t": (0, 41), "u": (110, 113), "v": (13, 13), "w": (12, 12),
        "x": (-7, -7), "y": (-26, 16), "z": (83, 80), "AE": (55, 97), "Ezh": (66, 56),
        "G.1": (80, 103), "I.1": (67, 67), "OE": (80, 91), "Schwa": (86, 80),
        "Thorn": (107, 173), "a.1": (72, 111), "a.1.sups": (89, 113), "a.2": (59, 14),
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
        "euro": (78, 122), "f.1": (111, 16), "f.i": (11, -311), "f.i.1": (101, -311),
        "f.sups": (57, 48), "five": (75, 81), "five.dnom": (102, 65), "five.sups": (140, 101),
        "florin": (126, 114), "four": (96, 81), "four.dnom": (70, 53), "four.ss01": (96, 81),
        "four.sups": (107, 86), "g.sups": (90, 115), "germandbls": (105, 58),
        "greater": (198, 181), "guilsinglleft": (95, 85), "guilsinglright": (85, 95),
        "h.sups": (116, 116), "hyphen": (150, 150), "i.numr": (44, 152), "i.sups": (100, 100),
        "idotless": (113, 113), "j.sups": (5, 100), "jdotless": (-58, 114),
        "k.sups": (116, 45), "kgreenlandic": (111, 0), "l.ss02": (119, 22),
        "l.sups": (120, 120), "less": (181, 198), "m.sups": (116, 116), "minus": (188, 188),
        "minus.dnom": (111, 111), "minus.sups": (168, 169), "multiply": (159, 159),
        "n.numr": (72, 195), "n.sups": (116, 116), "nine": (80, 80), "nine.dnom": (65, 65),
        "nine.sups": (101, 101), "numbersign": (21, 21), "o.sups": (90, 90),
        "one": (103, 105), "one.dnom": (92, 69), "one.ss01": (107, 105),
        "one.sups": (129, 109), "p.sups": (116, 90), "paragraph": (63, 105),
        "parenleft": (145, 54), "parenleft.dnom": (96, 39), "parenleft.sups": (142, 75),
        "parenright": (53, 145), "parenright.dnom": (39, 96), "parenright.sups": (74, 142),
        "plus": (194, 194), "plus.dnom": (120, 120), "plus.sups": (171, 171),
        "plusminus": (188, 190), "q.sups": (90, 116), "quoteleft": (193, 97),
        "quoteright": (190, 100), "quotesingle": (217, 217), "r.sups": (117, 103),
        "registered": (108, 108), "s.sups": (87, 83), "section": (81, 81), "seven": (66, 65),
        "seven.dnom": (51, 50), "seven.sups": (86, 85), "six": (80, 80), "six.dnom": (65, 65),
        "six.ss01": (81, 81), "six.sups": (101, 101), "slash": (21, 21), "sterling": (93, 79),
        "t.1": (109, 42), "t.sups": (41, 62), "thorn": (111, 73), "three": (88, 81),
        "three.1": (88, 81), "three.dnom": (60, 65), "three.sups": (97, 101),
        "trademark": (96, 103), "two": (82, 93), "two.dnom": (54, 61), "two.sups": (91, 100),
        "u.1": (110, 113), "u.sups": (115, 116), "v.sups": (51, 51), "w.sups": (43, 43),
        "x.sups": (47, 47), "y.sups": (29, 54), "yen": (38, 39), "z.sups": (103, 101),
        "zero": (80, 80), "zero.dnom": (65, 65), "zero.sups": (101, 101),
    },
}
SPACE = {"Thin": 525, "Regular": 516, "Black": 453}


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
