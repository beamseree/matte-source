#!/bin/sh
# Build the variable font from source/PlaceholderSans.designspace (the UFOs you
# edit in Fontra), then finish it with tools/postbuild.py (gasp and prep, Windows
# metrics, OS/2 ranges).
#
# The default build, in build/, keeps the source's glyph names (Che-cy, a.1 ...),
# which tools/kerning.py --check and other tools look glyphs up by. With --release,
# it builds build/release/ instead, with production glyph names (uni0427 ...) as
# Inter's releases have, and OFL.txt beside the fonts: ship those files.
#
# With --derive [params.json], first regenerate that source from Inter: derive a
# Glyphs file in build/derived, then convert it to designspace + UFO with the
# mockup letters as background guides. This OVERWRITES hand edits in source/.
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
DS=source/PlaceholderSans.designspace
OUT=build
NAMES=--no-production-names

if [ "$1" = "--derive" ]; then
  mkdir -p build/derived
  rm -rf build/derived/features
  cp -R vendor/inter/src/features build/derived/features
  $PY -I tools/derive.py vendor/inter/src/Inter-Roman.glyphspackage build/derived/PlaceholderSans.glyphspackage $2
  $PY -I tools/to_ufo.py build/derived/PlaceholderSans.glyphspackage $DS \
    --guides Regular=reference/mockup.svg --guides Thin=reference/mockup-thin.webp \
    --guides Black=reference/mockup-black.svg
elif [ "$1" = "--release" ]; then
  OUT=build/release
  NAMES=
fi

# DecomposeTransformedComponentsFilter decomposes mirrored, scaled and rotated
# components (d is b mirrored), reversing mirrored contours so every outer contour
# runs clockwise. Without it, flattening left đ, ₫ and Ҋ with a mirrored stem whose
# reversed contour cancelled the crossbar or tail where they overlap: holes. '...'
# keeps the masters' own filters (eraseOpenCorners).
mkdir -p $OUT
$PY -m fontmake -m $DS -o variable --output-dir $OUT --flatten-components $NAMES \
  --filter '...' --filter DecomposeTransformedComponentsFilter >/dev/null 2>$OUT/fontmake.log
$PY -I tools/postbuild.py $OUT/PlaceholderSans-VF.ttf
$PY -I -c "import sys; from fontTools.ttLib import TTFont; f=TTFont(sys.argv[1]); f.flavor='woff2'; f.save(sys.argv[2])" \
  $OUT/PlaceholderSans-VF.ttf $OUT/PlaceholderSans-VF.woff2
if [ "$OUT" = build/release ]; then
  cp OFL.txt $OUT/
fi
echo "built $OUT/PlaceholderSans-VF.ttf and .woff2"
