# aumo-font: notes for Claude

A weight-only variable font (wght 100–900) derived from Inter (SIL OFL 1.1) and fitted
to the user's own mockup, `reference/mockup.svg`. Working family name "Placeholder Sans";
the real name is still to be chosen. The folder name "aumo-font" is not the font name.
See README.md for the file layout, setup and commands.

## Status (2026-10-27)

- The automatic fit is done. Letter widths, stem weights, x-height and spacing match the
  mockup closely (fit report: ink error mean 2.7 units, gap error mean 5.8 units).
- **Hand-drawing has not started.** The user draws in Fontra. Letters that still differ
  from the mockup in shape (not size), in priority order: g (longer hook), y (straight
  tail, no curve), t (longer crossbar; fit held at 1.12), f (shorter top hook, top at
  1515; fit held at 0.95), R (check against the guide), c and e (flatter terminals), k (arm
  and leg junction), Q (shorter tail), i and j (dots a little lower, top 1515).
- Next, with Claude: choose a real name, review figures and punctuation in real text
  (the mockup only covers letters), do a kerning pass, then use the font in
  `~/Documents/Projects/port-coming-soon` instead of `src/app/fonts/MuotoTrialVAR.ttf`.

## Decisions and why

- **Source of truth is `source/*.ufo`** (designspace + 3 masters: Thin 100, Regular 400,
  Black 900). The user chose Fontra over Glyphs 3. Fontra only partly writes .glyphs
  files, so the source is UFO.
- **The Regular master is heavier than Inter's and has less contrast.** Stems are 194
  vertical and 190 horizontal, against Inter's 180 and 168, because the mockup measures
  that way. Thin and Black are Inter's. The user decided to keep Black's contrast as is.
  If 400 later feels too heavy, change the wght axis mapping (avar) rather than the
  drawings.
- x-height is 1076 (Inter 1118), the lowercase overshoot is 25, and ascender, cap height
  and descenders are Inter's. The optical-size axis was dropped.
- The Regular master's `public.background` layer holds the 52 mockup letters as tracing
  guides. Inter's own backup and background layers were removed.
- Licensing: keep Inter's copyright line and the OFL. Don't use "Inter" in the font name.
  The Muoto trial in port-coming-soon is a commercial trial font: never extract, trace or
  match its outlines. All targets come from the user's mockup.

## Rules

- After hand-drawing has started, **never run `tools/build.sh --derive` or
  `tools/fit.py`**. Both regenerate `source/` from Inter and overwrite the user's edits.
  Use plain `tools/build.sh`.
- Masters must stay compatible: change Thin, Regular and Black the same way, and move
  points rather than adding or deleting them.
- Checking work: `tools/build.sh`, then
  `.venv/bin/python -I -c "import sys,json; sys.path.insert(0,'tools'); import fit; fit.report(json.load(open('reference/params.json')), update=False)"`
  for numbers against the mockup, and `specimen/check.html?x=<svg units>&s=<zoom>` for a
  visual overlay. `.claude/launch.json` has preview configs: "specimen" serves the project
  root on 8791, "fontra" runs Fontra on `source/` on 8793.

## Gotchas

- The PyPI package named `fontra` is an unrelated font-listing tool. The editor is
  installed from `vendor/fontra` (`pip install -e`) into `vendor/fontra-venv`.
- Virtual environments break when the folder moves, so recreate them (README "Setup").
  `tools/build.sh` calls `python -m fontmake` so it doesn't depend on script shebangs.
- The name table copyright (ID 0) is still Inter's line. Setting `font.copyright` in
  glyphsLib didn't change it. That is acceptable under the OFL.
