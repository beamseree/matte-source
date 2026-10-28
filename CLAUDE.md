# aumo-font: notes for Claude

A weight-only variable font (wght 100–900) derived from Inter (SIL OFL 1.1) and fitted
to the user's own mockup, `reference/mockup.svg`. Working family name "Placeholder Sans";
the real name is still to be chosen. The folder name "aumo-font" is not the font name.
See README.md for the file layout, setup and commands.

## Status (2026-10-28)

- **Regular** is fitted to `reference/mockup.svg` (fit report: ink error mean 1.0 units,
  gap error mean 7.0 units, since the redraws below, the new f, t, P, C/G/S/s terminals
  and i/j dots, and c's wider opening, which makes c 12 units narrower than the mockup's).
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
  Thin's top at 1434.
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
  Now every joint is within 3 units of the mockup's at 15, 40 and 80 units from the stem
  in Regular, and at 15 and 40 in Black, and Black r's arm is the mockup's weight all
  along (it was 20–30 thinner). Further out our arches stay heavier, because their tops
  are (see below): at 140 units Regular is 1–9 heavier (n, h, m, r 5–7, where they had
  matched), and Black's n, h, m and u are 6–9 heavier at 80 and 14–21 at 140 (8–16
  before). `tools/joints.py --check` prints these. þ has b's joints and takes the
  mockup's b. æ needed nothing: its a-bowl runs into the e's bowl, not a stem, so the
  joint is already the mockup a's weight in Regular (241/210/188/173 at 15/40/80/140,
  the mockup's 234/209/187/171) and heavier in Black (285/264/251/246, the mockup's
  229/215/216/231). The user chose this from `build/joints-compare/`.
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
  mockup's), c and e (only their openings, wider on purpose; see above), r (the arm's
  end hangs about 100 lower in the mockups), the arch
  tops (too heavy: n's arch is 198 units deep at the top in Regular, the mockup's 178,
  and 339 in Black, the mockup's 310, so our counters reach lower; that keeps the arches
  heavier than the mockups' from about 80 units past the stem), j (Regular's hook,
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
  from. Black r's arm moves its whole lower edge. Every curve keeps its far end. The moved
  points are in `POINTS`, as x from the stem's edge (a point nothing moves) and y;
  `--fit` remakes the table by least squares: the mockup's ink edge, aligned on the
  stem's edge, up to `NEAR` units out (Regular 100, Black 60) and the curve's own
  outline from `FAR` on (180, 130), so it keeps its shape further out. Black's are
  shorter because its counters reach 28 units less high than the mockup's, so its inner
  curves can only follow the mockup's that far. It refits from the current outlines, so
  refit only after changing a joint's far end. Each changed glyph keeps its right
  sidebearing, and `to_ufo.py` runs it after reshape.py.
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
- t's and f's crossbars stay apart through kerning, not shorter bars (the bars' reach
  is the mockups'): `tools/kern.py` sets glyph-to-glyph pairs tt, tf, ft and ff to leave
  `BAR_GAP` (60) between the bars in every master, on top of Inter's group kerning.
  Glyph pairs, because Inter's t and f kerning groups also hold letters without these
  bars (public.kern1.t has 56 members, 33 of them t's); accented t's and f's still kern
  as before. It writes only kerning.plist, and `to_ufo.py` runs it after reshape.py.
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
  20–25 units off.
