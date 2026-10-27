# aumo-font

A weight-only variable font (100–900) derived from [Inter](https://github.com/rsms/inter)
(SIL Open Font License 1.1) and fitted to the mockup in `reference/mockup.svg`.
Working family name: "Placeholder Sans".

## Layout

| Path | What it is |
|---|---|
| `source/PlaceholderSans.designspace` + `*.ufo` | **The font source.** Edit this in Fontra. The Regular master's `public.background` layer holds the mockup letters as tracing guides. |
| `build/PlaceholderSans-VF.ttf`, `.woff2` | Built font |
| `reference/mockup.svg` | The target design (lowercase + capitals pangrams) |
| `reference/mockup-black.svg` | The Black design, same layout (`mockup-thin.webp` and `mockup-black.webp` are screenshots) |
| `reference/targets.json`, `params.json` | Measurements from the mockup and the fitted parameters |
| `tools/derive.py` | Inter → widened, lower x-height, heavier Regular, tighter spacing |
| `tools/to_ufo.py` | Glyphs → designspace + UFO, adds the background guides, runs straighten and redraw |
| `tools/straighten.py` | Redraws x, X, z, Z with straight strokes from the mockups' measurements (x/X narrowing toward the crossing, Z/z's shorter top bar; also usable on `source/` directly) |
| `tools/redraw.py` | Redraws N, K, k, w, A, V, v, W, M, Y as the mockups' straight polygons, sets E/F's bars and Q's tail, the t crossbar and i/j dots (also usable on `source/` directly) |
| `tools/reshape.py` | Rebuilds t's foot (flat, with an upright cut), cuts C, G and S's terminals at the mockups' angles, moves P's bowl bar to the mockups' height and sets Black's f and t stems to 352, keeping right sidebearings (also usable on `source/` directly) |
| `tools/kern.py` | Kerns tt, tf, ft and ff so t's and f's crossbars stay 60 units apart in every master (writes only kerning.plist) |
| `tools/strokes.py` | Compares stroke widths on scanlines, ours (from `source/`) against the mockups; `--check` covers the redrawn letters |
| `tools/fit.py` | Fits one master's `params.json` values to its mockup, building in `build/fit/`; `--apply` writes that master into `source/` |
| `tools/svgtarget.py`, `imgtarget.py` | Mockup (SVG or screenshot) → per-letter targets and stems (l, I, H bar) in font units |
| `tools/build.sh` | Builds the font |
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
tools/build.sh --derive reference/params.json   # regenerate source/ from Inter: OVERWRITES edits
.venv/bin/python -I tools/fit.py --master Thin --targets reference/targets-thin.json \
    --guides reference/mockup-thin.webp --apply  # refit one master: OVERWRITES that master
.venv/bin/python -I tools/fit.py --master Black --targets reference/targets-black.json \
    --guides reference/mockup-black.svg --fit-stems --apply  # Black (targets from svgtarget.py)
python3 -m http.server 8791                     # then open http://localhost:8791/specimen/
```

## Editing rules

- Change every master (Thin, Regular, Black) the same way, and move points rather than
  adding or deleting them, so the masters stay compatible.
- Keep Inter's copyright line and the OFL license; don't use "Inter" in the font name.
