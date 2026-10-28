# aumo-font

A weight-only variable font (100–900) derived from [Inter](https://github.com/rsms/inter)
(SIL Open Font License 1.1) and fitted to the mockup in `reference/mockup.svg`.
Working family name: "Placeholder Sans".

## Layout

| Path | What it is |
|---|---|
| `source/PlaceholderSans.designspace` + `*.ufo` | **The font source.** Edit this in Fontra. The Regular master's `public.background` layer holds the mockup letters as tracing guides. |
| `build/PlaceholderSans-VF.ttf`, `.woff2` | Built font, with the source's glyph names (the tools read it) |
| `build/release/` | Release build (`tools/build.sh --release`): production glyph names, plus `OFL.txt`. Ship these. |
| `OFL.txt` | The license, with our copyright line and Inter's |
| `reference/mockup.svg` | The target design (lowercase + capitals pangrams) |
| `reference/mockup-black.svg` | The Black design, same layout (`mockup-thin.webp` and `mockup-black.webp` are screenshots) |
| `reference/targets.json`, `params.json` | Measurements from the mockup and the fitted parameters |
| `tools/derive.py` | Inter → widened, lower x-height, heavier Regular, tighter spacing |
| `tools/to_ufo.py` | Glyphs → designspace + UFO, adds the background guides, runs straighten, redraw, reshape, refit, joints, spacing, accents, dots, stacked, kerning, kern and tabular |
| `tools/straighten.py` | Redraws x, X, z, Z with straight strokes from the mockups' measurements (x/X narrowing toward the crossing, Z/z's shorter top bar; also usable on `source/` directly) |
| `tools/redraw.py` | Redraws N, K, k, w, A, V, v, W, M, Y as the mockups' straight polygons, sets E/F's bars and Q's tail, the t crossbar and i/j dots (also usable on `source/` directly) |
| `tools/dots.py` | Gives the period and the dots of !, ?, ¡ and ¿ the i dot's size, and moves the glyphs built on them (colon, semicolon, ellipsis, ·, ŀ, …); runs tabular.py after when used on `source/` directly |
| `tools/reshape.py` | Rebuilds t's foot (flat, with an upright cut), cuts C, G, S and s's terminals at the mockups' angles and fits S's and s's arms either side of the cuts (`--fit` remakes that table), moves P's bowl bar to the mockups' height, sets Black's f and t stems to 352 and gives f's crossbar t's height, keeping right sidebearings (also usable on `source/` directly) |
| `tools/refit.py` | Fits R (bowl, bar, leg), B (middle bar, bowls), G (bar, bowl), c and e (bowls, e's bar, the cut angles, keeping Inter's wider opening) to the mockups' points in Regular and Black, and makes the same construction moves in Thin from its guide (`--fit` remakes the table), keeping right sidebearings (also usable on `source/` directly) |
| `tools/joints.py` | Thickens the joints where arches and bowls leave their stems (a, n, h, m, u, r, b, p, þ; d and q follow), gives their tops the mockups' depth and makes r's arm flat, in Regular and Black, from points fitted to the mockups, and gives 5's bowl n's weight at its joint; `--fit [kind ...]` refits them, `--check` compares the joints and depths with the mockups (also usable on `source/` directly) |
| `tools/spacing.py` | Sets the letters', figures' and punctuation's sidebearings and the word space from its `SIDES` / `SPACE` tables, fitted (`--fit`) to the mockups' pairs and Inter's proportions, with one sidebearing per construction set (lowercase stems, bowls, capital stems), symmetric letters centred, even round capitals, Black's word space at 3× n\|n, and alternates and small figures following their defaults; `--cost` prints what each constraint costs against the mockups; run on its own, it runs accents, stacked, tabular, kerning and kern after (also usable on `source/` directly) |
| `tools/accents.py` | Gives composites (accented letters, digraphs, Greek and Cyrillic) Inter's widths and puts their marks on their anchors at Inter's offsets (also usable on `source/` directly) |
| `tools/kerning.py` | Refits Inter's kerning to our shapes and spacing (y in its own group), and adds the least kerning that keeps every two text glyphs 10 units apart and two letters 50 apart at every weight; `--check` scans the built font at every 100 (also usable on `source/` directly) |
| `tools/kern.py` | Kerns tt, tf, ft and ff so t's and f's crossbars stay 60 units apart in every master (writes only kerning.plist) |
| `tools/stacked.py` | Puts parts drawn over each other where Inter has them: the semicolons' dots, ⁑, ʘ Ͼ Ͽ and the circled and squared forms, with Inter's widths (also usable on `source/` directly) |
| `tools/tabular.py` | Gives the tabular glyphs (`.tf` names and `figurespace`) one width per master again, from Inter's source (Black's figures 1400), and Inter's fixed-width glyphs (arrows, symbols, the em space and its fractions) their constant widths, with their ink placed as in Inter; sets the quads, punctuation, maths and thin spaces (also usable on `source/` directly) |
| `tools/strokes.py` | Compares stroke widths on scanlines, ours (from `source/`) against the mockups; `--check` covers the redrawn letters |
| `tools/fit.py` | Fits one master's `params.json` values to its mockup, building in `build/fit/`; `--apply` writes that master into `source/` |
| `tools/svgtarget.py`, `imgtarget.py` | Mockup (SVG or screenshot) → per-letter targets and stems (l, I, H bar) in font units |
| `tools/build.sh` | Builds the font (decomposing mirrored and scaled components), then runs postbuild.py |
| `tools/postbuild.py` | Adds what fontmake leaves out: gasp and a smart-dropout prep, Windows ascent/descent covering every glyph at every weight, recalculated OS/2 ranges; checks the strikeout is centred on the hyphen |
| `specimen/index.html`, `check.html` | Comparison pages (serve the project root, open `/specimen/`) |
| `vendor/inter` | Inter's sources (only `src/`) |

## Setup

`vendor/`, `.venv/` and `build/` are not in git. On a fresh clone, fetch the vendored
sources at the revisions this project was built with:

```sh
git clone --filter=blob:none --sparse https://github.com/rsms/inter.git vendor/inter
git -C vendor/inter sparse-checkout set src
git -C vendor/inter checkout 353b61b9f4430d5f420d56605a6e7993e0941470
git clone https://github.com/fontra/fontra.git vendor/fontra
git -C vendor/fontra checkout 4762f5b0edd1cfbbebe2ac3bd3c4bfb12c47bbb8
```

The Python environments aren't portable; recreate them after moving or cloning the folder:

```sh
python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
python3 -m venv vendor/fontra-venv && vendor/fontra-venv/bin/python -m pip install -e vendor/fontra
tools/build.sh
```

## Commands

```sh
tools/build.sh                                  # build from source/ (keeps your edits)
tools/build.sh --release                        # release files in build/release/
tools/build.sh --derive reference/params.json   # regenerate source/ from Inter: OVERWRITES edits
.venv/bin/python -I tools/fit.py --master Thin --targets reference/targets-thin.json \
    --guides reference/mockup-thin.webp --apply  # refit one master: OVERWRITES that master
.venv/bin/python -I tools/fit.py --master Black --targets reference/targets-black.json \
    --guides reference/mockup-black.svg --fit-stems --apply  # Black (targets from svgtarget.py)
python3 -m http.server 8791                     # then open http://localhost:8791/specimen/
```

## Releasing

1. Bump the version in all three masters' `fontinfo.plist`: `versionMinor` 100 → 101 →
   102 … (shown as "Version 0.101"), and `versionMajor` 1 with `versionMinor` 0 for the
   first stable release. Do it for every build that leaves this machine: macOS and
   Windows cache fonts by version, so a new build with an old version can keep showing
   the old outlines.
2. `tools/build.sh --release`, and ship `build/release/` (the fonts and `OFL.txt`).

## Editing rules

- Change every master (Thin, Regular, Black) the same way, and move points rather than
  adding or deleting them, so the masters stay compatible.
- Keep Inter's copyright line and the OFL license; don't use "Inter" in the font name.
