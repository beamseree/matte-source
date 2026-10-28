# aumo-font: notes for Claude

A weight-only variable font (wght 100–900) derived from Inter (SIL OFL 1.1) and fitted
to the user's own mockup, `reference/mockup.svg`. Working family name "Placeholder Sans";
the real name is still to be chosen. The folder name "aumo-font" is not the font name.
See README.md for the file layout, setup and commands.

## Status (2026-10-28)

- **Regular** is fitted to `reference/mockup.svg` (fit report: ink error mean 0.8 units,
  gap error mean 7.0 units, since the redraws below, the new f, t, P, C/G/S/s terminals
  and i/j dots).
- **Thin** is fitted to `reference/mockup-thin.webp` (a screenshot, so about ±12 units of
  precision; ink error mean 2.9, gap error mean 10.0). At the user's request Thin keeps
  Inter's stems (46). The image is a shape and proportion reference only: its strokes
  are about 105 units thick, so the targets keep each letter's skeleton and thin the
  strokes evenly (`imgtarget.py --stem 46`). Thin has its own guides, traced from the
  image, so they are heavier than the glyphs and centred on them.
- **Black** is fitted to the user's exact design, `reference/mockup-black.svg` (same
  layout and scale as mockup.svg), **including its stroke weights**: l stem 353, I stem
  377, H bar 327, against the SVG's 352, 377 and 327 and Inter's 402, 404 and 326. Black
  is low-contrast like Regular, and its lowercase stems are lighter than its capital
  stems (`weight_v_lower`). Ink error mean 1.3 (the largest is j, 15), gap error
  mean 4.9; the largest gap
  errors are word spaces ("BROWN FOX" −55, "quick brown" −49), uneven in the mockup
  itself. It was first fitted to the screenshot `mockup-black.webp` (against the SVG:
  ink 9.7, gap 14.6). Black's guides are the SVG's outlines, except f, g, y and
  `_part.f_base`, whose backgrounds the user was editing; those, the hand-drawn g and y
  and the empty "test" layer were carried over unchanged through the refit, so g and y
  keep the webp fit's spacing (g's advance 1277 where the refit gave 1280, y's 1198
  where it gave 1210).
- Stems across the range: 100 → 46/46/46, 400 → 194/204/190, 900 → 353/377/327 (l/I/H).
  The 300→400 step is larger than the others because Regular is heavier; the avar
  mapping can even that out later.
- **Straight letters are redrawn by script** to match the mockups: x, X, z, Z
  (`tools/straighten.py`), and N, K, k, w, A, V, v, W, M, Y, E's and F's bars, Q's tail,
  the t crossbar and the i/j dots (`tools/redraw.py`); see Decisions. Every measured
  stroke is within about 1% of the mockups (`tools/strokes.py --check`), and their
  outlines differ from the SVGs' by 0.0–0.4% of the ink area. Earlier, the redraw of
  N, K, k, w, t and i/j lowered ink errors but raised gap errors, for two spacing
  problems the redraw exposed: the i/j dots now sit centred over their stems, which
  shows the fits had placed those stems about 20–30 units right of the mockups' to make
  up for off-centre dots; and t's longer bar reaches further into its left sidebearing
  (the mockups only show t after a word space, so the fits never set t's left side).
  Leave these for the spacing and kerning pass. The longer bars also met or overlapped
  in tt, tf, ft and ff; `tools/kern.py` now kerns those pairs so the bars sit 60 units
  apart at every weight (the user chose 60 over 30 and 100, side by side in real text).
- **The i/j dots are lower than the mockups'** at the user's request: the mockups' size
  (Thin's 94 units), moved down by 15% of the space above the x-height. Regular's is
  240 × 236 with its top at 1485 (the mockup's 1515), Black's 410 × 389 at 1539 (1552),
  Thin's top at 1434. The period and the dots of !, ?, ¡ and ¿ are the same size
  (`tools/dots.py`, see Decisions); the user chose the i dot's size over 8% bigger
  (about Inter's ratio), from `build/dots-compare/`. They had been Inter's, scaled by
  derive.py: Regular's period was 280 × 290. The accent dots (ż ė ċ ġ İ, 260 × 257 in
  Regular; ä ö ü, 245 × 252) are still Inter's.
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
- **Hand-drawing has started**: the user lengthened the g hook in Regular and is drawing
  g and y (straight tail) in every master; keep those edits. f's top is now flat like
  the mockups' (`_part.f_base`, 12 points: flat top at 1515, the terminal cut upright at
  the crossbar's end, a flat underside). The user drew Regular's; Thin's and Black's
  were made by script to match (Black's from mockup-black.svg, Thin's from the
  screenshot's outer curve, about 235 × 213, with Thin's 46-unit strokes), and their
  crossbars now end at the terminal. Check them by eye.
  Letters that still differ from the mockups in shape, largest first (Black's numbers
  are ours against mockup-black.svg; Regular's percentages are the outline mismatch):
  t (stem top 14 too tall), G (Black's bar is 27 thinner at the bottom and the
  mockup's spur runs straight down into the bowl; its bar starts about 45 further left),
  a (the mockup's top terminal is taller: 710–932 in Black, ours 749–918; spur at the
  foot), J (the hook's end is 66 units lower than the mockup's), c and e (their terminals
  are already angled, within about 5° of the mockups' except Black e's lower one, 9°
  against 20°; c's and e's lower ends about 23 too high), R (Black's bowl bar 350 thick at
  the leg, the mockup's 428; leg join; Regular 15%), B (Black's middle bar 250 thick,
  the mockup's 303), Regular's o, e and c tops (10–14 units too deep, like the arches
  were: their counters top out at 909–913, the mockups' at 923), the bottoms of u and
  the bowls (they overshoot 14 and 22 in Regular, 13–14 in Black, the mockups 25), η and ƕ (drawn apart from n, they keep Inter's joints and tops), j (Regular's hook,
  14%), S and s (the spine: the mockups' bowls run into it higher on the right and lower
  on the left, up to 45 units in Regular S, whose spine is straight at 7° from level
  where ours is 13°; Black S's counters are 15–17 units shallower, tops 1177 and 315
  against 1192 and 298; Regular S 9.8%, s 6.0%), and Regular's O and Q bowl (6%). `fit.py` still holds t's ink factor at 1.12, but
  redraw.py and reshape.py now set t's crossbar and foot, so the factor has no effect.
- Next, with Claude: choose a real name, review figures and punctuation in real text
  (the mockup only covers letters), do a kerning pass, then use the font in
  `~/Documents/Projects/port-coming-soon` instead of `src/app/fonts/MuotoTrialVAR.ttf`.

## Decisions and why

- **Source of truth is `source/*.ufo`** (designspace + 3 masters: Thin 100, Regular 400,
  Black 900). The user chose Fontra over Glyphs 3. Fontra only partly writes .glyphs
  files, so the source is UFO.
- **The Regular master is heavier than Inter's and has less contrast.** Stems are 194
  vertical and 190 horizontal, against Inter's 180 and 168, because the mockup measures
  that way. Thin keeps Inter's stems; Black matches its mockup (see Status). If 400 later
  feels too heavy, change the wght axis mapping (avar) rather than the drawings.
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
- t's and f's crossbars stay apart through kerning, not shorter bars (the bars' reach
  is the mockups'): `tools/kern.py` sets glyph-to-glyph pairs tt, tf, ft and ff to leave
  `BAR_GAP` (60) between the bars in every master, on top of Inter's group kerning.
  Glyph pairs, because Inter's t and f kerning groups also hold letters without these
  bars (public.kern1.t has 56 members, 33 of them t's); accented t's and f's still kern
  as before. It writes only kerning.plist, and `to_ufo.py` runs it after reshape.py.
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
  in real text, from `build/tabular-compare/`. `to_ufo.py` runs it last.
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
- The name table copyright (ID 0) is still Inter's line. Setting `font.copyright` in
  glyphsLib didn't change it. That is acceptable under the OFL.
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
- `derive.py` places some marks off their base's anchor: the i/j dots were 26–34 units
  left of the stem before the redraw, and ż (Regular) and ė (Thin, Black) dots are still
  20–25 units off. Its composites moved some components by their glyph's width change:
  the colon's upper dot (fixed by dots.py), and the semicolon's dot and the circled forms
  (fixed by stacked.py).
