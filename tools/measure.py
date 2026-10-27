"""Measure per-letter boxes in a two-line comparison image (Inter on top, new below)."""
import sys, numpy as np
from PIL import Image
from scipy import ndimage

im = np.asarray(Image.open(sys.argv[1]).convert("L")).astype(float)
mask = im > 110
TEXT = "quickbrownfoxjumpsoverthelazydog"

def letters(y0, y1, x0=170):
    lab, n = ndimage.label(mask[y0:y1, x0:])
    boxes = []
    for sl in ndimage.find_objects(lab):
        ys, xs = sl
        boxes.append([xs.start + x0, xs.stop + x0, ys.start + y0, ys.stop + y0])
    boxes.sort()
    # merge dots (i, j) into the stem below them
    out = []
    for b in boxes:
        if out and b[0] < out[-1][1] - 2 and (b[3] - b[2]) < 15 or (out and (b[3]-b[2]) < 15 and b[0] >= out[-1][0] and b[1] <= out[-1][1] + 3):
            o = out[-1]; o[0]=min(o[0],b[0]); o[1]=max(o[1],b[1]); o[2]=min(o[2],b[2]); o[3]=max(o[3],b[3])
        else:
            out.append(b)
    return out

for name, (y0, y1) in zip(["inter", "new"], [(10, 118), (145, 250)]):
    L = letters(y0, y1)
    print(name, len(L), "line x:", L[0][0], "->", L[-1][1])
    globals()[name] = L

if len(inter) == len(new) == len(TEXT):
    base_i = max(b[3] for b in inter if TEXT[inter.index(b)] in "oxwnmuvrsze") 
    print("ch  inter(w,h,top,bot)   new(w,h,top,bot)   w-ratio")
    for c, a, b in zip(TEXT, inter, new):
        print(f"{c}  {a[1]-a[0]:4d} {a[3]-a[2]:4d} {a[2]:4d} {a[3]:4d}   {b[1]-b[0]:4d} {b[3]-b[2]:4d} {b[2]:4d} {b[3]:4d}   {(b[1]-b[0])/(a[1]-a[0]):.3f}")

for name in ["inter", "new"]:
    print(name, [(b[0], b[1], b[2], b[3]) for b in globals()[name]])
