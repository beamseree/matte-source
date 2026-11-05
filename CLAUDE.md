# aumo-font: notes for Claude

A weight-only variable font (wght 100–900) derived from Inter (SIL OFL 1.1) and fitted
to the user's own mockup, `reference/mockup.svg`. Working family name "Placeholder Sans";
the real name is still to be chosen. The folder name "aumo-font" is not the font name.
See README.md for the file layout, setup and commands.

## Status (2026-11-05)

- **Regular** is fitted to `reference/mockup.svg` (fit report: ink error mean 1.0 units,
  since the redraws below, the new f, t, P, C/G/S/s terminals and i/j dots, and c's wider
  opening, which makes c 12 units narrower than the mockup's; gap error mean 2.3 since the
  spacing and kerning pass, 7.0 before it).
- **Thin** is fitted to `reference/mockup-thin.webp` (a screenshot, so about ±12 units of
  precision; ink error mean 2.9, gap error mean 7.5 since the spacing and kerning pass, 10.0 before;
  most of what's left is the round capitals, see the spacing bullet). At the user's request Thin keeps
  Inter's stems (46). The image is a shape and proportion reference only: its strokes
  are about 105 units thick, so the targets keep each letter's skeleton and thin the
  strokes evenly (`imgtarget.py --stem 46`). Thin has its own guides, traced from the
  image, so they are heavier than the glyphs and centred on them.
- **Black** is fitted to the user's exact design, `reference/mockup-black.svg` (same
  layout and scale as mockup.svg), **including its stroke weights**: l stem 353, I stem
  377, H bar 327, against the SVG's 352, 377 and 327 and Inter's 402, 404 and 326. Black
  is low-contrast like Regular, and its lowercase stems are lighter than its capital
  stems (`weight_v_lower`). Ink error mean 1.3 (the largest is j, 15), gap error
  mean 3.5 since the spacing and kerning pass (4.9 before); the largest gap errors are the
  round capitals' pairs (DO +19, OG +18; the user chose even round sides over the
  mockup's) and word spaces ("over the" +22, "BROWN FOX" −16), uneven in the mockup itself. It was first fitted to the screenshot `mockup-black.webp` (against the SVG:
  ink 9.7, gap 14.6). Black's guides are the SVG's outlines, except f, g, y and
  `_part.f_base`, whose backgrounds the user was editing; those, the hand-drawn g and y
  and the empty "test" layer were carried over unchanged through the refit, so g and y
  keep the webp fit's spacing (g's advance 1277 where the refit gave 1280, y's 1198
  where it gave 1210).
- **The Regular master is at wght 430**, the axis default (the axis map, see Decisions),
  so the mockup's Regular is CSS weight 430, and the named Regular (400) has Inter
  Regular's stem. The masters' stems: 100 → 46/46/46, 430 → 194/204/190, 900 →
  353/377/327 (l/I/H). l stem at 100 … 900: 46, 91, 136, 181, 218, 252, 285, 319, 353
  (I/H at 400: 190/177). The steps are 45 up to 400 (Inter's own), then 34 at each step
  above 430. The site sets its body text at 415 (tuned for the Muoto trial); it needs 430
  for the mockup's Regular.
- **Straight letters are redrawn by script** to match the mockups: x, X, z, Z
  (`tools/straighten.py`), and N, K, k, w, A, V, v, W, M, Y, E's and F's bars, Q's tail,
  the t crossbar and the i/j dots (`tools/redraw.py`); see Decisions. Every measured
  stroke is within about 1% of the mockups (`tools/strokes.py --check`), and their
  outlines differ from the SVGs' by 0.0–0.4% of the ink area. Earlier, the redraw of
  N, K, k, w, t and i/j lowered ink errors but raised gap errors (ui, ic, ju, r_t, th),
  which looked like i/j stems placed 20–30 units right of the mockups' and t's longer bar
  reaching into its left sidebearing. The spacing pass found the cause (see its bullet):
  the fits could never move i, j, t or f, and made up for them on their neighbours (u's
  right side, not the i, was loose). The longer bars also met or overlapped
  in tt, tf, ft and ff; `tools/kern.py` now kerns those pairs so the bars sit 60 units
  apart at every weight (the user chose 60 over 30 and 100, side by side in real text).
- **The i/j dots are lower than the mockups'** at the user's request: the mockups' size
  (Thin's 94 units), moved down by 15% of the space above the x-height. Regular's is
  240 × 236 with its top at 1485 (the mockup's 1515), Black's 410 × 389 at 1539 (1552),
  Thin's top at 1434. The period and the dots of !, ?, ¡ and ¿ are the same size
  (`tools/dots.py`, see Decisions); the user chose the i dot's size over 8% bigger
  (about Inter's ratio), from `build/dots-compare/`. They had been Inter's, scaled by
  derive.py: Regular's period was 280 × 290. The accent dots (ż ė ċ ġ İ, 260 × 257 in
  Regular; ä ö ü, 245 × 252) are still Inter's size; since the spacing pass they sit on
  their anchors, so over the lowercase their feet are near the i dot's (Regular: both 1249).
- **t's foot, P's bowl and the C, G, S and s terminals are reshaped by script**
  (`tools/reshape.py`, see Decisions): t ends in a flat foot with an upright cut, like
  the mockups' and like f's top, reaching about 20 units past the crossbar (25 in Thin),
  so t and every glyph built on it widened by that much with their right sidebearings
  kept. P's bowl is shorter, its lower bar at the mockups' height (about 70–90 units
  higher than Inter's). C, G, S and s have the mockups' angled terminal cuts (8–22°)
  instead of Inter's flat ones (s's were shallower: 13° in Regular, 9° in Black); the
  user chose them after comparing both, as letters and in real text. In S and s the
  curves either side of each cut also take the mockups' shape in Regular and Black, with
  the cut's corners exactly the mockups': Inter's arms came down more steeply into the
  terminals, so they were up to 70 units deeper near the cut (Regular S's upper arm 170
  units deep 75 in from the right edge, the mockup's 100), s's lower terminal stopped
  23–38 units short in Regular (the user saw the s as tilted), and Black s's terminals
  wrapped 54–98 units further round. Outline mismatch went from 15.1% to 9.8% (Regular
  S), 10.9% to 6.0% (Regular s), 8.1% to 5.5% (Black S) and 13.0% to 6.9% (Black s).
  Black S's lower tip is now the mockup's, 23 units further left, so S is the mockup's
  width (1279) and its left side is no longer loose; Tonetwo (a mirrored S) widened 23 to
  keep its right sidebearing. Thin's S and s terminals end where its screenshot's do,
  thinned to 46-unit strokes, at Regular's angles: 60 units further round at S's lower
  terminal, 30 and 34 at s's. Thin S's lengthened curve bulges 1 unit past its corner,
  and its handle 15, so fit.py's ink (the control box) reads 5 more than the outline. The
  user chose this from `build/s-compare/`. The same
  script makes Black's f and t stems 352, like its other lowercase stems (350–357) and
  the mockup's: they came out of the fit at 373 and 374. Black t now matches the mockup
  exactly (stem, crossbar and foot) and is 22 units narrower. f's, f.1's and t.1's
  crossbars take t's height, as in both mockups (Black's f bar had reached 24 lower), and
  Thin's t foot is its f top turned upside down (it had turned a tighter corner).
- **The joints where arches and bowls leave their stems are thickened by script**
  (`tools/joints.py`, see Decisions) in a, n, h, m, u, r, b, p and þ, and so d and q, in
  Regular and Black; Thin is unchanged. The mockups' arches get heavier toward the stem,
  where Inter's stay even or thin out: at 15 units from the stem, Regular's n, h, m and u
  were 80–85 units thinner than the mockup's, a 100, r 70, the bowls 25; Black's 30–45.
  Now every joint is within 3 units of the mockup's at 15, 40 and 80 units from the stem.
  `tools/joints.py --check` prints these. þ has b's joints and takes the
  mockup's b. æ needed nothing: its a-bowl runs into the e's bowl, not a stem, so the
  joint is already the mockup a's weight in Regular (241/210/188/173 at 15/40/80/140,
  the mockup's 234/209/187/171) and heavier in Black (285/264/251/246, the mockup's
  229/215/216/231). The user chose this from `build/joints-compare/`.
- **The arch and bowl tops are the mockups' depth, and r's arm is flat** (`tools/joints.py`
  again, Regular and Black). Our counters stopped short of the mockups' tops (bottoms, in
  u and the bowls), so the arches were heavy all across: n's arch was 198 units deep at
  the top in Regular (the mockup's 178) and 339 in Black (310), the bowls of b, d, p, q
  and þ 193 (178), and Black's n, h, m and u were 14–21 heavier at 140 units from the
  stem. Each counter's edge now takes the mockup's shape all the way across, with our
  outer edges, x-height and overshoot kept, so every arch and bowl is within 3 units of
  the mockup's weight at 15–260 units from the stem (Black þ, which takes the mockup's b
  scaled to its wider counter, up to 8 lighter at 200–260). Depths now: Regular n and h
  179, m 180, u 178, the bowls 177–178 (mockups 178); Black n and h 316 (310), m 319–321
  (314–315), u 313 (310), the bowls 307–311 (315). Where a depth differs, our outer edge
  does and the counter keeps the mockup's weight under it: Black's shoulders are 5–6
  lower than the mockup's 100–180 units out, and u and the bowls overshoot 13–22 at the
  baseline where the mockups overshoot 25. The bowls' far sides are the mockup's weight
  (Regular b 197 → 203 at mid-height, Black 364 → 370), and the counters join their far
  stems where the mockups' do. r's arm is flat on top (1101) and underneath (903 in
  Regular, 728 in Black; the mockups' 902 and 726) out to a square-cut terminal, as in
  both mockups; it had drooped toward the end (Regular's underside 906 → 882, Black's
  top 1101 → 1073), and its weight is now the mockup's out to the terminal. Outline
  mismatch, Regular: n 2.4 → 0.9%, h 2.0 → 0.7, m 3.0 → 2.0, u 3.1 → 2.4, r 2.9 → 2.5,
  b, d, p and q 2.6–3.1 → 1.4–1.9; Black: n 1.8 → 1.1, h 2.2 → 1.6, m 2.8 → 2.2, u 2.4 →
  1.9, the bowls 1.6–1.7 → 1.4–1.5. Thin is unchanged: every top stroke there is 58 units
  and every bottom 47, o, e and c too, and its screenshot shows nothing particular to the
  arches. The user chose this from `build/arch-tops-compare/`, after a first fit that
  turned sharply at the bowls' far sides (fixed by balancing the handles, see Decisions).
- **5's bowl leaves its stem like n's arch** (`tools/joints.py` again, Regular). It had
  Inter's joint, which thins toward the stem: its top stroke was 152/157/164/172 units
  thick at 15/40/80/140 from the notch, where n's, scaled to 5's depth (183, n's 179), is
  268/220/191/177. Now 203/198/191/183: the notch moved up the stem's edge (881 → 908)
  and the foot's corner, where the counter's top curve starts, down (711 → 666, so the
  foot is cut steeper), each adding half the extra weight at 15. n's weight right by the
  stem comes from its inner curve running down a vertical stem, which 5 doesn't have;
  fits that matched it pulled the foot into a spike or the notch up to the bowl's top.
  Black's 5 already has n's weight against its depth (within 4 units at 40–140, 17
  lighter at 15), so it, like Thin, is unchanged; 6 and 9 already had b's and d's
  weight at their joints. The user chose this ("n at 80") over matching n 40 units out
  (231/220/205/189), from `build/five-compare/`.
- **R, B, G, c and e take the mockups' outlines** (`tools/refit.py`, see Decisions). R's
  bowl bar is at the mockups' height (Regular 621–807, was 566–755; Black 530–836, was
  491–806), Regular's bowl is 34 units wider, and the leg leans more and meets the bar
  where the mockups' does. B's middle bar is the mockups' (Regular 683–873, was 671–843;
  Black 610–913, was 638–888). G's bar starts about 60 units further left, at the
  mockups' height (Black's 27 heavier underneath), and meets the inner curve where that
  runs straight up into it. c and e take the mockups' bowls, e's bar (Regular 482–642,
  was 473–632; Black 453–642, was 446–663) and the mockups' cut angles (Black e's 20°,
  was 9°). The mockups' c and e terminals reach further round (c's 50–70 units in
  Regular), which closes the opening; the user preferred Inter's wider opening, so the
  cuts turn about the middle of Inter's, and Regular c is 12 units narrower at the
  terminals (fit.py's ink error for c is 12; its sidebearings are kept). Outline
  distance from the mockups, Regular/Black: R 14.9/6.0 → 0.5/0.1, B 6.5/4.7 → 0.5/0.2,
  G 9.5/10.3 → 1.0/1.3, c 7.5/8.0 → 4.3/4.1 (the opening), e 6.5/7.3 → 1.9/2.2. Thin
  makes the same construction moves from its screenshot: R's bar up 59, its bowl 49
  wider and its leg at the screenshot's slope; B's waist up 19, G's bar up 43, e's bar
  up 23; its c and e terminals are Inter's. ę's ogonek follows e's turned cut. The user
  chose these from `build/refit-compare/`.
- **Spacing and kerning pass, phase 1 (spacing)** (see Decisions):
  - Accented letters have Inter's widths and their marks sit on their anchors
    (`tools/accents.py`). About 1,420 composites per master had their marks' sidebearing
    changes added (Regular Á 36 narrower than A, Ä 68; Black's 15–32 wider), marks off
    their anchors by up to 99 units (Ÿ's dieresis 59–99, ñ's tilde 36–58), and lowercase
    marks 42 units high; Greek and Cyrillic too. i and j were among them: they gained
    25 units on the right in Regular.
  - Every letter's sides are refitted (`tools/spacing.py`): pairs inside words match the
    mockups within a unit, except the round capitals' below (lowercase gap error inside
    words: Thin 6.0 → 2.2, Regular 3.6 → 0.4, Black 1.5 → 0.5), sides the pangrams don't show take Inter's proportions (t's left +57 in Regular, +93
    in Thin; u's right −33 and m's left +32 in Regular, where the old fit had made up for
    the i), the word space is 519 / 513 / 506 (Thin / Regular / Black), figures came in
    9–17 units a side in Thin and Regular (none in Black), punctuation about 10 in
    Regular, and æ, ß, þ and the character variants follow Inter's proportions. Phase 2
    made the fit settle on its own result and refitted it once with the new kerning (the
    pangrams are laid out with it): Regular f's right 45 → 25 (fo), X's left −7 → 0,
    Thin's Æ, Œ, Þ, Ʒ, Ə and the character variants 5–9 tighter, Black's maths signs and
    brackets 5–8 looser and V, X and x 7–11 looser on the left; the space is 523 / 515 / 503.
  - The round capitals O, C, G and D have one round sidebearing per master, as in Inter,
    at the white our straight capitals have: 103 / 88 / 86. The user chose this ("C")
    over the mockups' uneven ones ("A": Regular O 94/83, C 94, G 111, D 102) and over
    Inter's ratio to H ("B": 118 / 103 / 89, too loose for our wider O), from
    `build/spacing-compare/`, setting the mockup aside for consistency. So RO, OW, DO and
    OG differ from the mockups (Thin's screenshot most: OG −53, DO −46).
  - ŀ's dot is still 24–40 units off l's anchor (dots.py's FOLLOW places it).
- **Phase 2 (kerning)** (`tools/kerning.py`, see Decisions): Inter's pairs keep Inter's
  values scaled to our spacing (our sidebearings are a median 0.82–0.93 of Inter's in Thin
  and Regular, 1.08–1.10 in Black) plus the change in how our shapes meet (held to ±40);
  528 / 689 / 485 of Inter's pairs changed (Thin / Regular / Black), 192 / 230 / 109 by 20
  or more (Regular F|a −50 → −3: our a's top terminal sits at F's middle arm; Inter's
  large quote and diagonal values about 15% smaller in Regular, 10% larger in Black). No
  two text glyphs (Latin with its accented and Vietnamese letters, monotonic Greek, modern
  Cyrillic, figures, punctuation) overlap at any weight from 100 to 900
  (`tools/kerning.py --check`): before, 233 pairs did at 100 and 2,329 at 900, mostly wide
  accents on i and j beside ascenders and T's bar. That takes 2,703 kerning exceptions
  (2,651 glyph pairs, 52 glyph against group), the same in every master; kerning went from
  about 1,400 pairs per master to 4,100, the WOFF2 from 243 to 258 KB. Rare letters
  outside that set (Ƈ, ɉ, ǂ beside each other, polytonic Greek) can still overlap, as many
  do in Inter. ǂ's crossbars had drifted apart (derive.py), so it joined stacked.py's list.
- **A full audit (2026-10-28)**, with the mockups set aside and against Inter, SF Pro, Plus
  Jakarta Sans, Helvetica Neue and Graphik, is in `build/audit/README.md` (gitignored; area
  reports beside it). The release layer (metadata, STAT, gasp, win metrics, the đ ₫ Ҋ holes
  from mirrored components) and the spacing and kerning tools were fixed in their own
  sessions and merged (see Decisions), and `source/` was refitted with the new spacing and
  kerning code and the user's `LOOSEN` (Thin and Regular 8% looser) and `ASIDE` (FO, ZY, OX,
  ox): fit, apply, fit again (identical on a third fit). Symmetric letters are now centred
  (Y was 43 units off at 900), n h m r b p k share one left side (152 at 430, was 122–156), n's
  sidebearing over its counter is Inter's 0.296 at 430 (was 0.251), fy is 53 apart (was 35;
  13 at 900), fî's kerning +12 (was +97), and no letter pairs come nearer than 50 at any
  weight. The cost against the mockups: gap error mean Regular 2.3 → 25.4, Thin 7.5 → 27.9,
  Black 3.6 → 17.3 (ink error unchanged). Also fixed: **what derive.py missed** (`tools/xheight.py`,
  see Decisions). The small capitals and pecyrillicturn were still at Inter's x-height, 1118,
  so Cyrillic н т м я ц џ ң ҥ ӈ ӊ ӎ ҭ ҵ and the IPA small capitals stood 42 units above о and
  x, and п (pecyrillicturn turned over) hung 42 below the baseline; in Black their stems were
  the capitals' 374 (now 353, l's). ӛ's dieresis sat 84 units above ӧ's (the turned letters'
  top anchors were at 1160), the hooks of ƙ ɦ ɧ ƥ ɗ ɠ ʠ 42 low (the hook part's anchor), ʒ and
  ӡ at 1118. **ť's caron** in Thin sat left of the stem (as in Inter's Thin), so from 150 to
  300 it ran through it; it is now 100 units right of the stem (`accents.py`'s `CARON_GAP`).
  **The dot accent and dot below** are the i dot's size at every weight, and the dieresis
  takes Inter's size against its i dot (Regular 226 × 235, was 244 × 252; Black 365 × 357, was
  337 × 338): `dots.py`'s `MARK_DOTS`. The bigger Black dieresis made ÏÏ, ïï and their
  likes collide at 800–900 until kerning.py was rerun. Still open from the audit: see its
  README (sups and small caps, separately drawn Cyrillic and Greek, hooked letters, a heavier
  Black, Thin's contrast ...).
- **a, R, s, z, y and e's sides (2026-11-05)**: the user saw capitals before a and e, and
  pa, as too far apart, and asked whether the kerning was off globally. It wasn't: every
  Latin letter pair's gap, measured as kerning.py does against Inter's at our spacing,
  splits into one number per side (a median polish of the 52 × 52 grid) plus a pair term
  that is about a unit (median absolute 1.2 in Regular), so the kerning follows Inter's and
  the looseness was a few sidebearings, each set by one mockup pair. In Regular a's left was
  18 loose and its right 26 tight (the a sat about 20 units right in its advance), R's
  right 37 loose (69 in Thin), e's right 23 loose, s's left 34 tight, z's 28/33, y's left
  27. `spacing.py`'s `ASIDE` now also leaves out "la", "az", "RO", "ps", "zy", "er" and the
  word gap "R T" (the user chose this, "B", from `build/spacing-compare/` and a live proof
  artifact, over "la", "az", "RO" alone, which left z lopsided). Regular: a 102/123 →
  83/150, R right 93 → 56, s left 66 → 99, z 90/85 → 117/116, y left 17 → 48, e right 112 →
  100, T left 75 → 80; all within 2 units of our typical side but e's right (+10). The round
  letters (o c e d q g left, o b p right, about 10 looser than Inter's proportions) were
  left alone as the mockups' look. Gap error against the mockups: Regular 25.4 → 26.6,
  Thin 27.9 → 30.6, Black 17.3 → 21.2 (az and zy 77–105 units looser than the mockups', RO
  13–55 tighter); ink error unchanged, no overlaps and no letter pairs under 50 at any
  weight. Still uneven by the same measure: Regular E's, W's and w's sides and f's right
  (19–24 tight; redrawn or hand-set, so left to the eye), Thin's L right, V, t and A (35–60
  loose), Black's diagonals (Z left −61, V, A, W −27 to −40) and r's right (+54).
- **Hand-drawing has started**: the user lengthened the g hook in Regular and is drawing
  g and y (straight tail) in every master; keep those edits. f's top is now flat like
  the mockups' (`_part.f_base`, 12 points: flat top at 1515, the terminal cut upright at
  the crossbar's end, a flat underside). The user drew Regular's; Thin's and Black's
  were made by script to match (Black's from mockup-black.svg, Thin's from the
  screenshot's outer curve, about 235 × 213, with Thin's 46-unit strokes), and their
  crossbars now end at the terminal. Check them by eye.
  Letters that still differ from the mockups in shape, largest first (Black's numbers
  are ours against mockup-black.svg; Regular's percentages are the outline mismatch):
  t (stem top 14 too tall), a (the mockup's top terminal is taller: 710–932 in Black,
  ours 749–918; spur at the foot), J (the hook's end is 66 units lower than the
  mockup's), c and e (only their openings, wider on purpose; see above), Regular o's top
  (14 units too deep, like the arches were: its counter tops out at 909, the mockup's at
  923; c's and e's now take the mockups'), the bottoms of u and the bowls (they
  overshoot 14 and 22 in Regular, 13–14 in Black, the mockups 25), η and ƕ (drawn apart
  from n, they keep Inter's joints and tops), j (Regular's hook,
  14%), S and s (the spine: the mockups' bowls run into it higher on the right and lower
  on the left, up to 45 units in Regular S, whose spine is straight at 7° from level
  where ours is 13°; Black S's counters are 15–17 units shallower, tops 1177 and 315
  against 1192 and 298; Regular S 9.8%, s 6.0%), and Regular's O and Q bowl (6%). `fit.py` still holds t's ink factor at 1.12, but
  redraw.py and reshape.py now set t's crossbar and foot, so the factor has no effect.
- Next, with Claude: choose a real name, then use the font in
  `~/Documents/Projects/port-coming-soon` instead of `src/app/fonts/MuotoTrialVAR.ttf`
  (the site only needs Latin, so subsetting would shrink it well below 258 KB).

## Decisions and why

- **Source of truth is `source/*.ufo`** (designspace + 3 masters: Thin 100, Regular 400,
  Black 900 in design units; Regular is at wght 430 for users, see the axis map below).
  The user chose Fontra over Glyphs 3. Fontra only partly writes .glyphs files, so the
  source is UFO.
- **The Regular master is heavier than Inter's and has less contrast.** Stems are 194
  vertical and 190 horizontal, against Inter's 180 and 168, because the mockup measures
  that way. Thin keeps Inter's stems; Black matches its mockup (see Status). How heavy
  each weight number is comes from the axis map, never the drawings.
- **The axis map puts the Regular master at wght 430** (`<map>` in
  `source/PlaceholderSans.designspace`: 100→100, 430→400, 900→900; the axis default is
  430). Inter's map kept the master at 400. Our Regular is heavier and our Black lighter
  than Inter's, so with that map the l stem grew 49 a step up to 400 and 29 above it,
  and 300→400 looked like a jump. With the master at 430, 100–400 take Inter's own stems
  (46, 91, 135, 180) and steps, and 400 is about as heavy as Inter's, SF Pro's and Work Sans's 400
  (l stem 12.1% of the H's height; ours at 430 is 13.0%). The user chose this from
  `build/avar-compare/` (index.html, and fonts.html beside Inter, SF Pro, Geist, Public
  Sans and Work Sans). The alternatives were keeping the master at 400 with steps
  shrinking from 56 to 27 (other families' steps stay even or grow toward Black), and even
  38-unit steps with the master at 485 (400 lighter than every font compared). The map
  is straight on each side of the default, so the font has no avar table, and the
  named instances are given as weights (`uservalue`), exactly 100 … 900. Changing the map
  later moves no outlines, but whatever sets a weight number (the site, check.html)
  changes with it. Only the designspace holds it: `--derive` would put Inter's map
  back, and fit.py's own builds in build/fit/ keep Inter's map (Regular at 400). So
  fit.py reads each master's weight from the font's fvar (`location()`: Thin at the
  minimum, Regular at the default, Black at the maximum), and `specimen/check.html`
  overlays Regular at 430.
- x, X, z and Z are the mockups' straight shapes. Inter curves the inside of x/X at the
  crossing and Z's joints, and keeps those diagonals lighter than the stems; the user saw
  x as too thin. `tools/straighten.py` redraws them with the same points in every
  master. x/X are 12 points (8 at the feet, 4 where the strokes cross): the mockups'
  strokes narrow toward the crossing (Black X's "/" is 480 at its foot, about 435 near
  the middle) and their tops are narrower than their bottoms, so x/X take the mockups'
  points (`CROSSES`) in proportion across our bottom feet, which set the letter's width,
  with each foot at the mockup's width. z/Z are a full-width bottom bar, a straight
  diagonal and a top bar inset from the bottom bar's ends (`TOP_BARS`, every master;
  Thin's measured on its screenshot, since thinning strokes evenly keeps the insets);
  the bars' thickness and the diagonal's edges come from `ZEDS`. Thin keeps its own
  strokes, with x/X straight. Widths and spacing don't move. `to_ufo.py` runs it on
  every conversion.
- N, K, k, w, A, V, v, W, M and Y are the mockups' straight polygons (12, 13, 13, 16, 8,
  8, 8, 16, 16 and 10 points, with the mockups' small flat notches where one stroke
  meets another), not Inter's curved, overlapping joints and tapering strokes.
  `tools/redraw.py` builds N, K, k and w from edge lines fitted to mockup.svg and
  mockup-black.svg; A, V, v, W, M and Y, E's and F's bars and arms, and Q's tail (a
  rotated rectangle, as in both mockups) take the mockups' points from its `POLYGONS`
  table, placed in proportion on our letter (Q's tail on its bowl, keeping Q's right
  sidebearing). Thin's lines are its own Inter strokes: each curved joint becomes a
  5-unit flat notch where its edges meet. Each letter keeps its outer edges, so spacing
  doesn't move. Every master
  is rebuilt with the same points, because a master left with Inter's open corners would
  be erased differently by eraseOpenCorners. The same script sets how far the t
  crossbar reaches past the stem (every master; Black also takes the mockup's bar
  thickness, 269) and centres the i/j dots over their stems at `DOTS`'s size and height
  (the mockups' size, a little lower; see Status). The dots change through the
  dotaccentcomb component's transform in i and j, so other dotted letters keep theirs,
  and ufo2ft decomposes i and j because that transform differs between masters.
  `to_ufo.py` runs it after straighten.py.
- The punctuation dots take the i dot's proportions: `tools/dots.py` scales the period's
  contour and the separate dots of !, ?, ¡ and ¿ (and ¡.case), separately in x and y, to
  redraw.py's `DOTS` width and height times `FACTOR` (1.0), about each dot's centre line,
  so each stays on its stem. The period's and the ! and ? dots' feet stay on the
  overshoot, and the ¡ dots keep their tops (¿ is ? turned round, so its top stays too).
  The period, !, ¡ and the colon keep their sidebearings, so they narrow with their dots.
  The 32 glyphs built on these follow by its `FOLLOW` table: the colon's upper dot and the
  semicolon's keep their tops, so the colon stays centred on the middle of the x-height;
  the middle dot keeps its height; the ellipsis and leaders close up; the dots in ʘ, Ͼ, Ͽ
  and the circled ! keep their centres. It also lines up the colon's dots, centred in its
  advance: derive.py had moved only the upper one, 44 / 36 / 17 units off. A glyph built
  on a dot with no rule stops the script. `to_ufo.py` runs it after kern.py and before
  tabular.py, which centres period.tf, colon.tf and semicolon.tf on the result; run on
  its own, dots.py runs tabular.py after.
- t's foot, P's bowl and the C, G, S and s terminals are construction differences from
  Inter, so `tools/reshape.py` rebuilds them in every master: `_part.t_base` (t and t.1)
  becomes 12 points, a flat foot whose curves and reach past the stem's right edge come
  from its `FOOT` table (Regular's from mockup.svg, Black's single cubics fitted to
  mockup-black.svg's two within 1.3 units; in both mockups t's foot is f's top upside
  down within a few units, so Thin's, which its screenshot can't show, is its own f top
  upside down; if Thin's f top is redrawn, update that entry); f's, f.1's and t.1's
  crossbars take t's height (`match_bars`); P moves its 20 points so the bowl's lower bar sits at
  `P_BAR`; C, G, S and s keep their points, and each terminal's two curves are trimmed or
  extended along their own path to the SVG's cut line (`TERMINALS`, x from the letter's
  left edge for C and G, right edge for S and s, which the cuts don't move). In S and s,
  `ARMS` (Regular and Black) then puts each cut's corners at the mockup's and fits the
  handles of the curves either side, out to the extremes (the top, the bottom and the
  counters' top and bottom), which stay; `reshape.py --fit` remakes ARMS by least squares
  against the mockups' outlines, each handle kept inside its curve's box so the extremes
  stay extremes. Thin's screenshot is too blurred to show the cuts, so Thin tilts its own
  C and G cuts about their middles to Regular's angles; its S and s cuts are at Regular's
  angles where the screenshot's strokes end, thinned evenly to 46 units (S's upper one
  stayed where it was). `STEM` sets f's and t's stems where a master's came out
  heavier than its other lowercase stems (Black: 352), by moving the stem's right edge:
  f's inner corner moves with it (`_part.f_base` points 1–5), t's foot is rebuilt from
  the new edge, and t's crossbar is re-placed with redraw.py's `set_t_bar`, so it's
  right whichever script runs first. Every glyph built on these keeps its right sidebearing.
  `to_ufo.py` runs it after redraw.py. Small curve differences are left alone at the
  user's request: the user wants changes that alter a letter's construction (like f's
  top, y's tail, t's foot, the terminal angles).
- The arch and bowl joints are the mockups' construction, so `tools/joints.py` moves the
  points of the curves either side of each joint, in Regular and Black only (Thin's
  screenshot can't show joints at 46-unit strokes): the inner curve's end slides along
  the stem; the outer curve ends at the mockup's flat notch (12–17 units), placed from
  the stem's edge, with the notch's line following it. Inter's n, h, m and u ran that
  curve on into the stem instead, and Thin still does; eraseOpenCorners leaves both
  shapes alone in every master (it doesn't see them as open corners), so they
  interpolate. m's second arch keeps its end, which the first arch's outer curve starts
  from. The outer curves keep their far ends, so the x-height and overshoot stay. The
  inner curves (and b's, p's and þ's counters) are fitted together with the curve beyond
  the counter's top or bottom, against the mockup's whole counter edge: the top moves
  with its handles level, and the far end slides along the far stem (n, h, m, u) or
  across to the mockup's counter extremum (b, p; þ's stays, since it takes the mockup's
  b scaled across to its own counter). Each target point is moved up or down by how far
  our outer edge is from the mockup's at that x, so the counter keeps the mockup's depth
  under our edge. `BALANCE` keeps each of these curves' two handles about the same
  fraction of its box (now 54–70%, like the mockups' and Inter's): many handle pairs fit
  the mockup's edge within a unit, and the closest was often one long and one short,
  which turned sharply at the short end (the user saw it at the bowls' far sides). r's
  lower edge is an "arm": a curve out of the stem, then a flat run to the terminal's
  foot, which slides along the cut; "level" puts r's top, from the arch to the terminal,
  at the mockup's 1101. The moved points are in `POINTS`, as x from the stem's edge (a
  point nothing moves) and y. `--fit [kind ...]` remakes the table by least squares,
  only the curves of the kinds named (`top` is the inner curves and counters fitted
  with the curve beyond), keeping the other rows. The outer curves and a's inner curve
  are fitted to the mockup's ink edge, aligned on the stem's edge, up to `NEAR` units out
  (Regular 100, Black 60) and to their own outline from `FAR` on (180, 130). Black's
  `NEAR` was set when its counters reached 28 units less high than the mockup's; now only
  those curves use it, and at 100 they came only 1–2 units closer, so it stays. Refits
  start from the current outlines, so refit only the curves you change (a full refit
  moves the outer curves' handles a little each time). Each changed glyph keeps its
  right sidebearing, and `to_ufo.py` runs it after reshape.py.
- 5 has no mockup letter, so `joints.py`'s `fit_five` (`--fit five`) fits its joint to n
  instead: the notch's line end slides up the stem's edge, taking the outer curve's end
  with it, and the foot's corner slides down a parallel line, so the foot's line
  steepens; each curve keeps its far end (the bowl's top, the counter's top) and its
  shape, scaled to its new ends, so nothing turns sharply. Two numbers come from the fit:
  the notch and the foot each add `FIVE_SPLIT` (half) of the extra weight 15 units out,
  and 5's top stroke has n's weight `FIVE_AT` (80) units from the stem, as a fraction of
  each glyph's depth. Free least-squares fits of the handles to n's whole profile
  bulged the curves. In Black the fit moves nothing, so `POINTS` has no Black 5.
  `--check` prints 5 after n, against n's weight scaled to 5's depth. Its composites
  (five.tf, five.circled, five.squared, Tonefive) follow; 5's ink box doesn't move.
- R, B, G, c and e were still Inter's construction where the mockups' differs (R's bowl
  bar and leg, B's middle bar, G's bar, c's and e's bowls, e's bar and their cut angles),
  so `tools/refit.py` moves their points to its `POINTS` table, which `--fit` makes. In
  Regular and Black each moved on-curve point goes to the mockup's nearest corner or
  extreme of the same kind, and each curve's handles are fitted by least squares to the
  mockup's outline between its ends, along the mockup's tangents and inside the curve's
  box, so extremes stay extremes. Points Inter's construction hides inside another stroke
  (R's bar end and leg top, G's spur, e's bar ends and counter ends) stay hidden, and the
  curves leaving them are fitted to the part of the mockup that shows. Tops, bottoms and
  stems keep ours (the mockups overshoot by 25, our capitals by 20). Thin's screenshot
  can't give points, so Thin centres R's and B's bars and G's and e's crossbars on its
  guide's (scaling the curves either side, as P's), and takes R's bowl width (from the
  stem) and leg slope (from its foot) from it. c's and e's terminals are cut through the
  middle of Inter's cuts (`APERTURE`) at the mockups' angles, because the user preferred
  Inter's wider opening to the mockups'; Thin keeps Inter's terminals. ę's ogonek
  (ogonek.e) ends just inside e's lower cut, so its corner keeps its place against the
  turned cut. Each changed glyph keeps its right sidebearing, an anchor on a moved point
  moves with it (e's ogonek, c's topr), and `to_ufo.py` runs it after reshape.py.
- derive.py lowered the x-height only in glyphs whose character is lowercase without a .sc
  suffix, so `tools/xheight.py` brings the rest down: `LOWER` (the .sc glyphs,
  pecyrillicturn, ҥ's and ҵ's own contours, ʛ's hook part) take derive.py's vertical map in
  every master; in Black, each glyph in `STEMS` is mixed in x between Regular and Black (as
  derive.py compensates stems) until its stem is Regular's times l's Black-to-Regular ratio,
  keeping its left edge and sidebearings (`BORROW` mixes parts drawn on another glyph as that
  glyph). A per-glyph factor, since the .sc stems weren't even (h.sc 374, y.sc already 347);
  Black's points have Black's heights, so it mixes up to four times to get within a unit.
  `ANCHORS` puts the turned letters' top anchors and the hook part's `_topr` at the
  x-height, and ʒ's capital Ʒ moves down to meet it. The glyphs built on these follow through
  accents.py. `to_ufo.py` runs it after joints.py, with Regular before Black. ʃ and ʄ are built
  on ∫ and keep its heavier Black stem; k.base (inside ƙ) and the descender ticks shared with
  the capitals (`_part.cyrtic` ...) were left as they are.
- t's and f's crossbars stay apart through kerning, not shorter bars (the bars' reach
  is the mockups'): `tools/kern.py` sets glyph-to-glyph pairs tt, tf, ft and ff to leave
  `BAR_GAP` (60) between the bars in every master, on top of Inter's group kerning.
  Glyph pairs, because Inter's t and f kerning groups also hold letters without these
  bars (public.kern1.t has 56 members, 33 of them t's); accented t's and f's still kern
  as before. It writes only kerning.plist, and `to_ufo.py` runs it after kerning.py (and
  kerning.py, run on its own, runs it after).
- The tabular glyphs (every name with a `tf` suffix part, and `figurespace`) have one width
  per master, as in Inter. Inter builds most of them from the proportional glyphs as
  components, and derive.py gave each its proportional glyph's width change, so the
  figures came out 1292–1338 wide. `tools/tabular.py` sets each one's width from Inter's
  source (its text-size masters), so glyphs that shared a width in Inter share one again,
  and moves the whole glyph so its ink sits as far from the advance's centre as Inter's
  (Inter's 1 is off-centre on purpose); no points move relative to each other. Figures,
  maths signs and hyphen are 1320 / 1328 / 1400 (Thin / Regular / Black), punctuation and
  spaces 550, brackets 800, and `figurespace` takes the figures' width. Black differs from
  Inter's 1320 (`WIDTHS`): its figures are wider than Inter's, so at 1320 the 4 had 17
  units a side; the user chose 1400 over 1320 and 1455 (the 4 with its own sidebearings)
  in real text, from `build/tabular-compare/`. The same script gives every glyph whose
  width is the same in all of Inter's masters (arrows, ■, ♥, the circled and squared
  forms, the em space and its fractions, .notdef) Inter's width, placed the same way:
  derive.py had given them sidebearing changes, so the em space was 1884 / 1810 / 2519
  and 122 such glyphs varied by 20 or more. The quads are the en and em spaces, the
  medium mathematical space 4/18 em, the punctuation space the period's width, and the
  thin, narrow no-break and hair spaces the word space's fraction Inter has per master.
  `to_ufo.py` runs it last.
- Parts drawn over each other sit where Inter has them. derive.py moved each component
  right by the width changes of the components before it and widened the glyph by all of
  them, which suits parts side by side (the ellipsis) but put the semicolon's dot 31 / 24
  units left and 7 right (Thin / Regular / Black) of Inter's place over the comma, set the
  circled and squared forms' letters, figures and signs off centre by up to 124 units,
  and changed those glyphs' widths by up to 262. `tools/stacked.py` moves each later
  part of the semicolons, colon.ss07, ⁑, ʘ, Ͼ, Ͽ and every .circled and .squared glyph
  so that its ink centre sits as far from the first part's as in Inter, and makes the
  width the first part's plus Inter's difference (the semicolon is the comma's plus 8 /
  28 / 10, so it got 44 / 47 units wider in Thin / Regular, 25 narrower in Black; each
  circled form is its circle's width). Glyphs built on one of these alone follow its
  width. The colon is dots.py's; accented letters follow their anchors and are left
  alone. `to_ufo.py` runs it after dots.py and before tabular.py; run on its own, it runs
  tabular.py after. The user approved it from `build/stacked-compare/`.
- Composites follow Inter's construction: `tools/accents.py` takes each glyph built only of
  components and, from Inter's source (text-size masters), sorts its components into
  attached ones (a "_" anchor meeting an anchor propagated through the components before
  it, by ufo2ft's own `anchors_traversing_components`) and ones set beside (the first,
  and n and j in nj). Those set beside keep Inter's offset plus the width changes of the
  ones before them (and their own, if mirrored); attached ones sit on their anchor at
  Inter's offset from it (none, except where Inter placed a mark by hand); the width is
  Inter's plus the width changes of the components set beside, so a composite with its
  base's width in Inter has ours; the anchors are propagated again, keeping those Inter
  sets by hand. It leaves alone glyphs with contours of their own (t, f, Q, Ħ ...), the
  glyphs dots.py, stacked.py and tabular.py place, and our zero-width combining marks
  and the glyphs built beside them (´ ¨ and the compound marks), since a zeroed mark has
  no width change to add; i's and j's dots are redraw.py's `set_dot`, redone so they
  follow a stem that moves. `to_ufo.py` runs it after spacing.py and before kern.py.
- Sidebearings come from `tools/spacing.py`'s `SIDES` (absolute, ink to the advance's
  edges, per master) and `SPACE`, made by `--fit`. derive.py applies fit.py's per-letter
  "sb" only to drawn glyphs, so the fit never moved i, j, t, f or Q and made up for them
  on their neighbours, and never set the sides the pangrams show only beside a word space.
  `--fit` solves every letter's two sides at once by least squares: the mockups' pairs
  inside words (weight 1), gaps across word spaces (with the space's width as a shared
  unknown) and Inter's proportions, both weighted 0.11 (0.45 in Thin, whose screenshot is
  ±12 units), because Inter's proportions predict the pinned pairs only to ±22–32 units
  and the mockups' word gaps scatter as much. Inter's proportions are optical
  sidebearings (sidebearing plus the profile's white, clipped at `DEPTH` deep, averaged
  over the x-height or cap height) at the median letter's fraction of Inter's; `DEPTH`
  (Thin 150, Regular 130, Black 100 lowercase / 60 capitals) is the depth that makes
  Inter's own letters most even. d and q mirror b and p, i and j are ı and ȷ, Q's left is
  O's. `OTHERS` (æ, ß, þ, the character variants ...) take Inter's proportions at their
  case's median, `FIGURES` at the mean of both cases', `PUNCTUATION` at the lowercase
  median over each glyph's own height; f.i and f.i.1 (dlig) move with f. The dot family
  (. , : ; ! ? ¡ ¿ · …) is left to dots.py and stacked.py. `ROUND = "white"` gives O, C,
  G and D's round sides one sidebearing: the mean of what leaves each as much white,
  against Inter's, as the straight capitals' stems (`STEMS`) have; "mockup" fits them like
  the other letters, "inter" uses H's plain fraction of Inter's (the user chose "white").
  The round sides are held at the rule's values while the rest are solved, so their
  neighbours fit against them (solved free first, they had left Black F's right side at
  −20 once O's sides were tied). The fit has structure, as Inter has: `SAME` sets share
  one unknown, so the lowercase stems (n m h r b p k ı, and n h m u d q's rights: d and q
  are b and p turned, so lefts and rights are one set), the bowls (o, c e g's lefts, b p's
  rights, d q's lefts) and the capital stems (B D E F H I K L M N P R's lefts, H I M N's
  rights) are one sidebearing per master, and `SYMMETRIC` letters (A H I M N O U V W X Y
  i l o v w x; their Greek and Cyrillic twins follow) have equal sides. Before, the
  pangrams' pairs gave n's left 122 and b's 156 on the same stem (Regular) and Y was 43
  off centre in Black. That costs gap error against the mockups (`--cost`, at the current
  kerning: free fit → `SYMMETRIC` → `SAME` → both): Thin 5.8 / 6.8 / 8.3 / 10.3, Regular
  1.9 / 2.1 / 2.8 / 4.4, Black 2.9 / 3.2 / 4.9 / 5.7. Black's word space is `WORD` (3) times n|n's gap, 453, instead of the mockup's
  503 (3.25 times; Inter, SF Pro and Graphik have 2.9–3.0); that adds about 44 to Black's
  gap error across word spaces. `FOLLOW` (u.1, l.ss02) and `SMALL` (the drawn .sups, .dnom
  and .numr glyphs; .subs and the other .numr are built on them) take Inter's sides plus
  their default's change from Inter's, scaled by their height. `LOOSEN` adds the same
  white to every side of a case, 8% of its median optical sidebearing, in Thin and Regular
  (n 141 → 152 at 430; Black unchanged): the audit found 100–500 as tight as a display
  face, and the user chose 8% over none and 12% from `build/loose-compare/`, for text.
  `ASIDE` leaves pangram pairs out of the fit where one pair alone sets a side against
  Inter's proportions, which the sets and symmetry then carry to every pair with the
  letter: FO, ZY, OX and ox (F's right, Y's, X's and x's sides much tighter; Regular F
  right 41, X −4; the user chose this from `build/structure-compare/`, so they sit 30–55
  units looser than the mockups'), and la, az, RO, ps, zy and er (a's sides, R's right,
  s's left, z's sides, y's left and e's right; see Status), with the word gap "R T" ("RT"),
  which alone set T's left once RO was out. An entry is the two letters either side of a
  pair or a word gap, as `pairs` lists them. Both act through `--fit`, and cost most of the
  gap error against the mockups in Thin and Regular.
  Applying moves each glyph's outline, components and anchors together; glyphs drawn over
  it (Q's tail, the bars of đ and ŧ) move with it, and so do the anchors of composites
  built on it. `to_ufo.py` runs it after joints.py; run on its own, it runs accents.py,
  stacked.py, tabular.py, kerning.py and kern.py after. Refit with `--fit` (prints the
  tables) after changing an outline's width, then apply; the pangrams are laid out with the
  kerning, so refit again after kerning.py changes a pair in them (one round settles it).
  The fit solves again with its own solution's medians and round sides until they stay
  put, so refitting the spaced source reproduces the tables, but for a unit of rounding on
  a few sides after the kerning changes (the clearance follows the widths).
- Kerning is `tools/kerning.py`'s, worked out from Inter's source and our outlines each time
  it runs (no table), so it follows shape and spacing changes. Each Inter pair is measured
  on its groups' key glyphs by its visible gap: both sides' optical sidebearings (over the
  two glyphs' height together, white capped at a depth) plus `LAMBDA` times how the shapes
  meet beyond that (the white between them row by row, capped that deep past their nearest
  point, minus the optical sidebearings). `CAL` (Thin 200 / 0.25, Regular 140 / 0.375,
  Black 140 / 0.375) are the depth and share that make Inter's own kerned letter pairs most
  even. Our value is Inter's scaled to our spacing (the spacing's median letter's fraction
  of Inter's, for the pair's cases) plus `LAMBDA` times the change in how the shapes meet,
  only for letter pairs sharing `OVERLAP` (half) of their height and held to `CLIP` (40),
  because one close point (our a's top terminal at F's middle arm) moves that measure a
  lot and for punctuation, quotes and small figures it has too little to go on. Measuring
  against Inter's own pairs as a whole would have made the kerning undo the sides the
  spacing set from the mockups. Under `THRESHOLD` (10) a pair keeps Inter's value. Greek
  and Cyrillic pairs are refitted the same way (ТЛ, ГЛ, ТД had kept Inter's unscaled
  −280). y is split from v's right-side group (`SPLIT`, written to groups.plist): its left
  is fuller, so it takes v's pairs plus the difference in how y and v meet the other glyph
  (A–y −121 where A–v is −139 in Regular). With each glyph's own spacing factored out, the
  model's kerning matches Inter's within about 15 units for F's, Y's and the diagonals'
  pairs, so the audit's tight F and Black-Y pairs are spacing (see `ASIDE`), not kerning.
  Then `clear` sets every text glyph (`SCRIPTS`, `MARKS`) against its own script's
  letters and the figures and punctuation, and the punctuation's capital forms (.case)
  against capitals and figures, at every 50 from 100 to 900 (between the masters,
  outlines interpolated as the built font does). A pair nearer than `CLEAR` (10, edges
  spread a row up and down), or two letters of a script nearer than `LETTERS` (50) in any
  direction with their marks left out (the left glyph's ink grown by a disc), gets the
  least kerning over the axis that makes up its shortfalls (`least`: the integral of the
  added kerning's square, the kerning going straight between the masters). Raising both
  neighbouring masters by each weight's whole shortfall had left the Regular master up to
  97 units looser than needed (fî, Tî) and the redrawn diagonals and long bars 4–33 units
  apart (XX, kX, fy, fW). Dashes join, so they aren't held apart from each other. Entries
  go against the right glyph's group when all its text glyphs fall short, then against
  the left glyph's group the same way, else per glyph, never tighter than what they
  replace. The user chose `LETTERS` 50 over 10, 40 and 60 from `build/clear-compare/`
  (60 would leave no letter pair under 51 units, at about 500 more entries per master).
  `OVERRIDES` takes pairs set by hand. `to_ufo.py` runs it once all three masters are done
  (after stacked.py), then kern.py and tabular.py; `--check` scans the built font for
  overlaps and for letter pairs nearer than `LETTERS`.
- ȸ and ȹ (uni0238/uni0239) are excluded from the eraseOpenCorners filter in every
  master's lib: once stem weights differ between masters, their overlapping contours
  erase differently and stop interpolating.
- x-height is 1076 (Inter 1118), the lowercase overshoot is 25, and ascender, cap height
  and descenders are Inter's. The optical-size axis was dropped.
- Each master's `public.background` layer holds the 52 mockup letters as tracing guides:
  Regular's and Black's are the SVGs' outlines, Thin's are traced from its screenshot
  (heavier than the glyphs). Each guide is centred on its glyph's outline. Inter's own
  backup and background layers were removed.
- f's stem and hook are the component `_part.f_base` (shared with f.1, ſ and
  slongstroke); only the crossbar is drawn in f. Its background holds a copy of f's
  guide in every master, shifted by the component's offset in f, so it can be edited
  against the mockup.
- The build layer does what Inter's and Google Fonts' release pipelines add after
  fontmake. `tools/build.sh` runs ufo2ft's DecomposeTransformedComponentsFilter (after
  the masters' own filters and flattening): d is b mirrored, so flattening left đ, ₫ and
  Ҋ with a reversed stem that cancelled the crossbar or tail where they overlap (holes
  at every weight), and 123 glyphs with counter-clockwise outer contours. Then
  `tools/postbuild.py` adds gasp {0xFFFF: 15} and a smart-dropout prep (unhinted),
  sets usWinAscent/Descent from every glyph at every weight (2306/706; hhea and typo
  stay 1984/−494, so line height doesn't change), and recalculates the OS/2 Unicode and
  code page ranges. The strikeout is in each master's fontinfo (top 662 / 700 / 708, so
  its centre is the hyphen's), and postbuild.py warns if the hyphen moves away from it.
  The STAT labels (Thin … Black, Regular 400 elidable and linked to 700) and the
  instances' PostScript names are in the designspace. The default build keeps the source's
  glyph names, which kerning.py --check and other tools look glyphs up by;
  `--release` writes production names to `build/release/` with `OFL.txt`.
- Metadata (every master's fontinfo): copyright "Copyright 2026 Beamseree
  (https://beamseree.com); Copyright 2016 The Inter Project Authors
  (https://github.com/rsms/inter)", designer and manufacturer Beamseree with that URL,
  vendor ID NONE, the description credits Inter and Rasmus Andersson, the license URL is
  https://openfontlicense.org, no trademark. Version 0.100: bump `versionMinor` in all
  three masters for every build that leaves this machine (README "Releasing").
- Licensing: keep Inter's copyright line and the OFL. Don't use "Inter" in the font name.
  The Muoto trial in port-coming-soon is a commercial trial font: never extract, trace or
  match its outlines. All targets come from the user's mockup.

## Rules

- **Never run `tools/build.sh --derive`**. It regenerates all of `source/` from Inter and
  overwrites the user's hand edits. Use plain `tools/build.sh`.
- `tools/fit.py` builds in `build/fit/` and only touches `source/` with `--apply`, which
  rewrites just that one master's UFO. Get the user's OK before applying to a master
  that has hand edits (Regular does). Per-master parameters live under `"masters"` in
  `reference/params.json`; Regular's stay at the top level.
- Fitting a master from a mockup:
  `tools/imgtarget.py <png> --stem <stem> > reference/targets-<m>.json` (or
  `svgtarget.py` for an SVG), then
  `tools/fit.py --master <M> --targets reference/targets-<m>.json --guides <mockup> --apply`
  (Black also takes `--fit-stems`; both target scripts write the "stems" it reads).
  `--apply` rewrites the whole master UFO, so first copy out its hand-edited files (in
  Black: glyphs/g.glif and y.glif, the f, g, y and `_part.f_base` backgrounds with the
  background contents.plist, glyphs.test/ and layercontents.plist), put them back after,
  and check with `git diff` that they're unchanged. To apply exactly the dry run you
  showed the user, call `fit.apply(<M>, <guides>)` rather than refitting with `--apply`.
- Stop Fontra before rewriting UFOs from outside it, and restart it after (see Gotchas).
- Masters must stay compatible: change Thin, Regular and Black the same way, and move
  points rather than adding or deleting them (straighten.py, redraw.py and reshape.py
  rebuild their letters with new points, but the same points in every master).
- Checking work: `tools/build.sh`, then
  `.venv/bin/python -I -c "import sys,json; sys.path.insert(0,'tools'); import fit; fit.TTF='build/PlaceholderSans-VF.ttf'; fit.report(fit.Master(json.load(open('reference/params.json')), 'Regular'), json.load(open('reference/targets.json')), update=False)"`
  for numbers against the mockup (swap in `'Thin'` / `'Black'` and their targets files),
  `.venv/bin/python -I tools/strokes.py --check` for the redrawn letters' stroke widths
  (`tools/strokes.py <Master> <char> <y>...` compares any letter on any scanline),
  `.venv/bin/python -I tools/joints.py --check` for the arch and bowl joints, and
  `specimen/check.html?m=regular|thin|black&x=<px>&s=<zoom>` for a visual overlay. `.claude/launch.json` has preview configs: "specimen" serves the project
  root on 8791, "fontra" runs Fontra on `source/` on 8793.

## Gotchas

- The PyPI package named `fontra` is an unrelated font-listing tool. The editor is
  installed from `vendor/fontra` (`pip install -e`) into `vendor/fontra-venv`.
- Virtual environments break when the folder moves, so recreate them (README "Setup").
  `tools/build.sh` calls `python -m fontmake` so it doesn't depend on script shebangs.
- glyphsLib ignores `font.copyright`; set the copyright (name ID 0) in the masters'
  fontinfo.plist.
- `acutedblcomb` and `breveinvcomb` were Inter's PUA-only marks (U+EEA7, U+EEAB) and
  "base" in `public.openTypeCategories`, so U+030B and U+0311 were missing. Now they also
  encode U+030B and U+0311 and are "mark" in every master, so they attach over letters
  with no precomposed form (a̋, n̑); ő ű ȃ ȓ … still compose through HarfBuzz and ccmp.
  Unlike the other combining marks they still have widths (Thin / Regular / Black:
  acutedblcomb 827 / 984 / 1241, breveinvcomb 704 / 819 / 1026). HarfBuzz zeroes a mark's
  advance, but fontbakery `gdef_spacing_marks` WARNs; zeroing them is the spacing pass's job.
  The enclosing marks U+0488, U+0489, U+20DD and U+20DE (category Me) have no category,
  so they are still outside GDEF's mark class (`gdef_mark_chars` WARN); U+0488 and U+0489
  also have zero width, which fails `base_has_width`.
- `imgtarget.py` finds letter edges at 2% coverage, which catches webp ringing, so some
  letter boxes in the screenshot targets are up to about 1 px (25 units) too wide on a
  side, and the fits matched them. That still affects Thin; Black's webp fit had N 1439
  units wide against 1411 in mockup-black.svg, and the SVG refit gives 1412.
  `tools/strokes.py` measures ink runs by summed coverage, which ringing doesn't affect.
- mockup-black.svg draws E, F, L and other stem-and-arm letters as one self-overlapping
  contour. Fill it with the nonzero rule (`strokes.cut` does); an even-odd fill shows
  false holes where the arms meet the stem.
- Fontra caches each UFO's glyph list and can write a stale one back on its next save, so
  rewriting a UFO while it runs can lose glyphs or layers.
- Other Claude sessions sometimes work on this repo at the same time. Check `git status`
  and file times before overwriting anything you didn't just write.
- `derive.py` tells marks from letters by a width of 0 in Inter's Regular, but Inter's
  combining marks have widths in its source (acutecomb 573 / 661 / 822), so its composite
  branch treated every mark as a part set beside its base: each accented glyph took its
  marks' width changes, each mark moved by its base's width change instead of following
  its anchor, and marks over the lowercase kept Inter's height while the x-height came
  down 42. It also moved stacked parts by the width changes before them: the colon's upper
  dot, the semicolon's dot and the circled forms. accents.py, dots.py and stacked.py
  undo all of this after it; fix derive.py itself before ever deriving again. It also
  treated the .sc glyphs and parts like pecyrillicturn as capitals (no x-height change,
  capital stems), and moved some anchors of turned glyphs up 42 instead of down: xheight.py
  undoes that.
- glyphsLib zeroes the combining marks' widths in the UFOs, and `public.openTypeCategories`
  calls some combining marks "base" (breveacutecomb.cn, acutesubcomb ..., all unencoded or
  PUA-only), as Inter's own glyphsLib build does.
- Re-running straighten.py, redraw.py, reshape.py, refit.py or joints.py on `source/`
  moves a few points by 1 unit since spacing.py shifted the outlines (Python rounds .5 to
  even, so an odd shift flips some roundings). Run spacing.py after them; the 1-unit
  jitter is harmless. In `to_ufo.py`'s chain they run before spacing.py, so it doesn't
  arise there.
