# aumo-font: notes for Claude

A weight-only variable font (wght 100–900) derived from Inter (SIL OFL 1.1) and fitted
to the user's own mockup, `reference/mockup.svg`. Working family name "Placeholder Sans";
the real name is still to be chosen. The folder name "aumo-font" is not the font name.
See README.md for the file layout, setup and commands.

## Status (2026-10-27)

- **Regular** is fitted to `reference/mockup.svg` (fit report: ink error mean 1.2 units,
  gap error mean 7.2 units, since the redraws below and the new f).
- **Thin** is fitted to `reference/mockup-thin.webp` (a screenshot, so about ±12 units of
  precision; ink error mean 3.1, gap error mean 9.8). At the user's request Thin keeps
  Inter's stems (46). The image is a shape and proportion reference only: its strokes
  are about 105 units thick, so the targets keep each letter's skeleton and thin the
  strokes evenly (`imgtarget.py --stem 46`). Thin has its own guides, traced from the
  image, so they are heavier than the glyphs and centred on them.
- **Black** is fitted to the user's exact design, `reference/mockup-black.svg` (same
  layout and scale as mockup.svg), **including its stroke weights**: l stem 353, I stem
  377, H bar 327, against the SVG's 352, 377 and 327 and Inter's 402, 404 and 326. Black
  is low-contrast like Regular, and its lowercase stems are lighter than its capital
  stems (`weight_v_lower`). Ink error mean 1.3, gap error mean 4.9; the largest gap
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
  The longer bars also join in "tt" and "ft" at 400 and 900. Leave these for the
  spacing and kerning pass.
- **Hand-drawing has started**: the user lengthened the g hook in Regular and is drawing
  g and y (straight tail) in every master; keep those edits. f's top is now flat like
  the mockups' (`_part.f_base`, 12 points: flat top at 1515, the terminal cut upright at
  the crossbar's end, a flat underside). The user drew Regular's; Thin's and Black's
  were made by script to match (Black's from mockup-black.svg, Thin's from the
  screenshot's outer curve, about 235 × 213, with Thin's 46-unit strokes), and their
  crossbars now end at the terminal. Check them by eye.
  Letters that still differ from the mockups in shape, largest first (Black's numbers
  are ours against mockup-black.svg; Regular's percentages are the outline mismatch):
  S and s (terminals reach too far round: Black S's lower terminal reaches 126 units
  higher at 150 from the left, its upper one 102 lower near the right; Regular S 16%),
  P (the bowl's lower bar sits about 70 units low in Black; Regular 22%), t (stem top 14
  too tall, the hook's end 24 lower than the mockup's and the hook shorter: about 25
  units in Regular, 45 in Black, 80 in Thin, from the stem), G (Black's bar is 27 thinner
  at the bottom and the mockup's spur runs straight down into the bowl; top terminal),
  a (the mockup's top terminal is taller: 710–932 in Black, ours 749–918; spur at the
  foot), J (the hook's end is 66 units lower than the mockup's), C, c and e (flatter
  terminals: c's and e's lower ends about 23 too high), R (Black's bowl bar 350 thick at
  the leg, the mockup's 428; leg join; Regular 15%), B (Black's middle bar 250 thick,
  the mockup's 303), r (the arm's end hangs about 100 lower in the mockups), the n, m, h
  and u shoulders (slightly heavy where the arch meets the stem), j (Regular's hook,
  14%), i and j in Regular (dots 240 wide with their top at 1515, ours 260 and 1548),
  f in Black (crossbar 293 thick, the mockup's 269; stem 373, the mockup's 352), and
  Regular's O and Q bowl (6%). The t's crossbar no longer depends on its ink factor,
  which `fit.py` still holds at 1.12 and now only moves the hook.
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
  thickness, 269) and centres the i/j dots over their stems, with Black's at the
  mockup's size and height (410 × 389, top 1552). The dots change through the
  dotaccentcomb component's transform in i and j, so other dotted letters keep theirs,
  and ufo2ft decomposes i and j because that transform differs between masters.
  `to_ufo.py` runs it after straighten.py.
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
  points rather than adding or deleting them (straighten.py and redraw.py rebuild their
  letters with new points, but the same points in every master).
- Checking work: `tools/build.sh`, then
  `.venv/bin/python -I -c "import sys,json; sys.path.insert(0,'tools'); import fit; fit.TTF='build/PlaceholderSans-VF.ttf'; fit.report(fit.Master(json.load(open('reference/params.json')), 'Regular'), json.load(open('reference/targets.json')), update=False)"`
  for numbers against the mockup (swap in `'Thin'` / `'Black'` and their targets files),
  `.venv/bin/python -I tools/strokes.py --check` for the redrawn letters' stroke widths
  (`tools/strokes.py <Master> <char> <y>...` compares any letter on any scanline), and
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
  20–25 units off.
