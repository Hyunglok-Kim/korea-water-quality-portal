#!/usr/bin/env python3
"""home_sky.py [--out embed/media/home-sky-v1.jpg] [--source FILE] [--sheet FILE] — the picture behind the home page's first screen.

The lab's first page has always had one picture behind its title: the Earth-observing satellites streaming from
the Moon's side towards the Earth (the site's own asset, satellites.jpg, 1500 x 1125). The first screen
(embed/home/hero.html) has it across its whole panel again, under a veil, with the page's words on top. For
that the copy made here differs from the site's in two ways:

  - the satellites' names are taken out. Nineteen white labels are part of the picture; behind the page's own
    words they read as broken text, and at some window size one of them is always cut by the edge of the reel.
    Each name is found inside a box placed by eye (BOXES), as near-white pixels that stand out from what is
    round them, and filled in from its surroundings (every masked pixel becomes the mean of its neighbours,
    repeated until it settles), with a little of the picture's own grain so that the filled places are not
    smoother than the sky beside them. Nothing else in the picture is touched.
  - it is saved again as a progressive JPEG of about 140 kB (the site's file is 887 kB).

    python embed/tools/home_sky.py                       # fetches the site's picture, writes embed/media/home-sky-v1.jpg
    python embed/tools/home_sky.py --sheet names.png     # also a sheet of every name's place, before and after, to look at

If the site's picture is ever replaced, the boxes will be wrong: look at the sheet. A re-made picture gets a new
file name (home-sky-v2.jpg) and hero.html with it. Needs numpy, scipy and Pillow.
"""
import argparse
import io
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SOURCE = "https://cdn.prod.website-files.com/640cbd413ecaf856623aa507/640cc636ba6752b93af5a583_satellites.jpg"
BOXES = {   # name: (x0, y0, x1, y1) in the 1500 x 1125 picture, placed by eye; PAD widens each
    "OSTM/Jason 2 (NOAA)": (1143, 215, 1282, 262), "Aquarius": (987, 293, 1072, 316), "QuikSCAT": (828, 355, 920, 378),
    "TRMM": (705, 400, 770, 423), "Terra": (608, 469, 657, 491), "ISS-RapidScat, CATS": (719, 470, 862, 518),
    "EO-1": (918, 535, 965, 556), "SMAP": (521, 656, 580, 679), "Aqua": (668, 685, 719, 706),
    "Landsat 7 (USGS)": (791, 646, 886, 693), "Suomi NPP (NOAA)": (416, 705, 525, 753), "SORCE, TCTE (NOAA)": (638, 754, 747, 805),
    "Landsat 8 (USGS)": (374, 780, 464, 826), "Aura": (731, 852, 777, 874), "GPM": (415, 888, 461, 910),
    "GRACE (2)": (850, 899, 948, 922), "CALIPSO": (1070, 931, 1154, 953), "CloudSat": (1190, 971, 1279, 994), "OCO-2": (477, 1009, 540, 1032),
}
PAD = 14

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "media" / "home-sky-v1.jpg"))
ap.add_argument("--source", help="the site's picture as a file, instead of fetching it")
ap.add_argument("--sheet", help="write a picture of every name's place, before (above) and after (below)")
a = ap.parse_args()

raw = Path(a.source).read_bytes() if a.source else urllib.request.urlopen(urllib.request.Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
im = Image.open(io.BytesIO(raw)).convert("RGB")
assert im.size == (1500, 1125), f"the picture is {im.size}, not 1500 x 1125: the boxes were placed on that one"
rgb = np.asarray(im).astype(np.float32)

# 1. the letters: near-white, unsaturated, standing out from what is round them, inside the boxes
lo, hi, lum = rgb.min(axis=2), rgb.max(axis=2), rgb.mean(axis=2)
found = (lo > 120) & (hi - lo < 70) & (lum - ndi.median_filter(lum, size=31) > 38)
mask = np.zeros(found.shape, bool)
kept = dropped = 0
for name, (x0, y0, x1, y1) in BOXES.items():
    x0, y0, x1, y1 = max(0, x0 - PAD), max(0, y0 - PAD), min(found.shape[1], x1 + PAD), min(found.shape[0], y1 + PAD)
    sub = found[y0:y1, x0:x1]
    lab, n = ndi.label(sub, structure=np.ones((3, 3)))      # the letters as found, not widened: a trail beside a name must not join it
    before = kept
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if ys.min() == 0 or xs.min() == 0 or ys.max() == sub.shape[0] - 1 or xs.max() == sub.shape[1] - 1:
            dropped += 1          # touches the edge of its box: part of a satellite, a trail or a cloud, not a name
            continue
        kept += 1
        mask[y0:y1, x0:x1] |= ndi.binary_dilation(lab == k, iterations=2)
    assert kept > before, f"no letters found for {name}: has the picture changed?"
mask = ndi.binary_dilation(mask, iterations=1)              # the letters' soft edges
print(f"{len(BOXES)} names: {kept} pieces of letters filled in, {dropped} bright pieces at the boxes' edges left alone; {int(mask.sum())} pixels")

# 2. filled in from their surroundings, place by place
out = rgb.copy()
lab, n = ndi.label(ndi.binary_dilation(mask, iterations=6))
rng = np.random.default_rng(7)
for sl in ndi.find_objects(lab):
    ys = slice(max(0, sl[0].start - 4), min(mask.shape[0], sl[0].stop + 4))
    xs = slice(max(0, sl[1].start - 4), min(mask.shape[1], sl[1].stop + 4))
    m, v = mask[ys, xs], out[ys, xs].copy()
    w = (~m).astype(np.float32)
    for ch in range(3):                                     # a blurred first guess, then the relaxation
        v[..., ch][m] = (ndi.gaussian_filter(v[..., ch] * w, 6) / (ndi.gaussian_filter(w, 6) + 1e-6))[m]
    for _ in range(600):
        v[m] = ((np.roll(v, 1, 0) + np.roll(v, -1, 0) + np.roll(v, 1, 1) + np.roll(v, -1, 1)) / 4)[m]
    grain = rgb[ys, xs] - ndi.gaussian_filter(rgb[ys, xs], (2, 2, 0))
    v[m] += rng.normal(0, min(float(np.std(grain[~m])), 3.0), size=v[m].shape)
    out[ys, xs] = v
res = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
res.save(a.out, "JPEG", quality=76, optimize=True, progressive=True, subsampling="4:2:0")
print(f"{a.out}: {res.size[0]} x {res.size[1]}, {Path(a.out).stat().st_size} bytes (the site's picture: {len(raw)} bytes)")

if a.sheet:
    tiles = []
    for x0, y0, x1, y1 in BOXES.values():
        b = (x0 - 40, y0 - 40, x1 + 40, y1 + 40)
        t = Image.new("RGB", (b[2] - b[0], (b[3] - b[1]) * 2))
        t.paste(im.crop(b), (0, 0)); t.paste(res.crop(b), (0, b[3] - b[1])); tiles.append(t)
    x = y = row = 0
    sheet = Image.new("RGB", (1500, 3000), (20, 20, 20))
    for t in tiles:
        if x + t.width > 1500:
            x, y, row = 0, y + row + 8, 0
        sheet.paste(t, (x, y)); x += t.width + 8; row = max(row, t.height)
    sheet.crop((0, 0, 1500, y + row)).save(a.sheet)
    print(a.sheet)
