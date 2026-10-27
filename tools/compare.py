"""Render the built font like the mockup's "new" line and compare letter boxes.

Usage: python tools/compare.py <mockup image> [font.ttf]
"""

import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

TEXT = "quick brown fox jumps over the lazy dog"
LETTERS = TEXT.replace(" ", "")
SIZE = 96.2  # px; Inter's 1490-unit "l" is 70px tall in the mockup


def boxes(mask, x0=0):
    lab, _ = ndimage.label(mask)
    out = []
    for ys, xs in ndimage.find_objects(lab):
        if ys.stop - ys.start > 15:  # skip i/j dots
            out.append((xs.start + x0, xs.stop + x0, ys.start, ys.stop))
    out.sort()
    return out


def render(font_path):
    font = ImageFont.truetype(font_path, SIZE, layout_engine=ImageFont.Layout.BASIC)
    img = Image.new("L", (2400, 140), 0)
    ImageDraw.Draw(img).text((10, 0), TEXT, font=font, fill=255)
    return np.asarray(img) > 110


def main(mockup, font_path="build/PlaceholderSans-VF.ttf"):
    im = np.asarray(Image.open(mockup).convert("L")) > 110
    target = boxes(im[145:250, 170:], 170)
    mine = boxes(render(font_path))
    if len(target) != len(mine):
        print("letter count mismatch", len(target), len(mine))
        return
    t0, m0 = target[0][0], mine[0][0]
    print("ch   mockup  mine   (ink width)   start offset")
    dw = []
    for c, t, m in zip(LETTERS, target, mine):
        tw, mw = t[1] - t[0], m[1] - m[0]
        dw.append(mw - tw)
        print(f"{c}    {tw:4d}  {mw:4d}   {mw - tw:+3d}         {(m[0] - m0) - (t[0] - t0):+4d}")
    def h(bs, chars):
        return np.mean([b[3] - b[2] for c, b in zip(LETTERS, bs) if c in chars])
    print(f"line length: mockup {target[-1][1] - t0}  mine {mine[-1][1] - m0}")
    print(f"x-height-ish (o,x,n,u,s,e): mockup {h(target, 'oxnuse'):.1f}  mine {h(mine, 'oxnuse'):.1f}")
    print(f"mean ink width diff {np.mean(dw):+.2f}px")


if __name__ == "__main__":
    main(*sys.argv[1:])
