#!/bin/sh
# Build the variable font from source/PlaceholderSans.designspace (the UFOs you
# edit in Fontra).
#
# With --derive [params.json], first regenerate that source from Inter: derive a
# Glyphs file in build/derived, then convert it to designspace + UFO with the
# mockup letters as background guides. This OVERWRITES hand edits in source/.
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
DS=source/PlaceholderSans.designspace

if [ "$1" = "--derive" ]; then
  mkdir -p build/derived
  rm -rf build/derived/features
  cp -R vendor/inter/src/features build/derived/features
  $PY -I tools/derive.py vendor/inter/src/Inter-Roman.glyphspackage build/derived/PlaceholderSans.glyphspackage $2
  $PY -I tools/to_ufo.py build/derived/PlaceholderSans.glyphspackage $DS \
    --guides Regular=reference/mockup.svg --guides Thin=reference/mockup-thin.webp \
    --guides Black=reference/mockup-black.svg
fi

$PY -m fontmake -m $DS -o variable --output-dir build \
  --flatten-components --no-production-names >/dev/null 2>build/fontmake.log
$PY -I -c "from fontTools.ttLib import TTFont; f=TTFont('build/PlaceholderSans-VF.ttf'); f.flavor='woff2'; f.save('build/PlaceholderSans-VF.woff2')"
echo "built build/PlaceholderSans-VF.ttf and .woff2"
