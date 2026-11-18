#!/usr/bin/env python3
"""cap_wq.py BASE OUTDIR [test] [size=WxH] [scale=S] [pad=T,R,B,L] [strip=none] — frames of the loop for the Korea water quality portal.

    # the Data page card (16:9; the month strip drawn into the frames)
    python embed/tools/cap_wq.py "http://127.0.0.1:8797/index.html?intro=0&data=/data/" frames/wq
    embed/tools/encode.sh frames/wq/final wq-v1 embed/media 30 44 768 24

    # the home page announcement (upright, beside the text; the months are shown by the page, not drawn in)
    python embed/tools/cap_wq.py "http://127.0.0.1:8797/index.html?intro=0&data=/data/" frames/wq_tall size=540x556 scale=1.5 pad=40,30,40,30 strip=none
    embed/tools/encode.sh frames/wq_tall/final wq-tall-v1 embed/media 30 44 810 24

The loop (about ten seconds, drawn in software, one settled frame at a time, from a running copy of the portal
and nothing else):
  B  the six parameters in turn on the whole country: water temperature, suspended solids, dissolved oxygen,
     total nitrogen, total phosphorus, chlorophyll-a (record means; one picture each, cross-faded)
  C  into Daecheong Lake, where the dots become the 1 km cells they are
  D  chlorophyll-a there through the year: the twelve calendar-month means, a strip of months marking which
  E  a short dissolve back to the first frame
The first frame is also the card's still picture (shown before the loop plays, and to visitors who asked for
reduced motion), so the loop opens on the whole country with data on it, not on a flight in from the globe: a
first version did, and its still was a globe with nothing on it.

Writes OUTDIR/raw/*.png (captures), OUTDIR/final/f_%04d.png (the loop's frames) and OUTDIR/timeline.json, which
gives the second at which each stage begins: the card's data-caps times are read from it. `test` captures a handful
of frames only. Needs playwright (chromium), numpy and Pillow.

`size` is the picture in CSS pixels as the page will show it and `scale` the device pixel ratio it is drawn at
(frames are size x scale pixels); `pad` is the room left around the country in the opening view. The stages and
their lengths do not depend on any of these, so every version has the same timeline and the same captions fit.
With `strip=none` the strip of months is left out of the frames: a page that crops the picture to its own shape
(the announcement does) shows the months itself, from the same timeline, where no crop can cut them.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

base, out = sys.argv[1], Path(sys.argv[2])
test = "test" in sys.argv[3:]
opt = dict(kv.split("=", 1) for kv in sys.argv[3:] if "=" in kv)
raw, final = out / "raw", out / "final"
raw.mkdir(parents=True, exist_ok=True); final.mkdir(parents=True, exist_ok=True)
W, H = (int(v) for v in opt.get("size", "960x540").split("x"))
SCALE = float(opt.get("scale", "1"))
PAD = [int(v) for v in opt.get("pad", "34,34,34,34").split(",")]          # top, right, bottom, left
STRIP = opt.get("strip", "burn") != "none"
FPS = 24
NC = 40                              # frames of the zoom into the lake
HOLD_B, FADE_B, FIRST_B = 12, 5, 20  # each parameter: frames held, frames of cross-fade into the next; the first is held longer
HOLD_D, FADE_D = 5, 3                # each month
NE = 10                              # dissolve back to the first frame
ORDER_B = ["wt", "ss", "do", "tn", "tp", "chla"]
LAKE = (127.53, 36.41, 10.15)        # Daecheong Lake
MON = "JFMAMJJASOND"
CSS = """html, body { background: #0F1318 !important; overflow: hidden !important; }
.mapwrap { position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 99999 !important; border: 0 !important; border-radius: 0 !important; }
.map-ui, .nomap-msg, #boot, .maplibregl-control-container, .logos-footer, .maplibregl-marker { display: none !important; }"""
SETTLE = """async ([lng, lat, z]) => { const m = window.__portal.map; m.jumpTo({center: [lng, lat], zoom: z});
  await new Promise((res) => { let done = false; const fin = () => { if (!done) { done = true; res(); } }; m.once('idle', fin); setTimeout(fin, 9000); });
  return m.areTilesLoaded(); }"""
LAYER = """async ([v, mode, month]) => { const p = window.__portal;
  if (p.state.var !== v) document.querySelector(`#varSeg button[data-var=${v}]`).click();
  if (p.state.mode !== mode) document.querySelector(`#modeSeg button[data-mode=${mode}]`).click();
  if (mode === 'clim' && p.state.climMonth !== month) document.querySelectorAll('#when .mon button')[month - 1].click();
  const key = `${v}|mu|${mode}|` + (mode === 'clim' ? String(month).padStart(2, '0') : '');
  for (let i = 0; i < 400; i++) { const c = p.current(); if (c && c.spec.key === key && c.vals) return key; await new Promise((r) => setTimeout(r, 50)); }
  throw new Error('layer did not arrive: ' + key); }"""
smooth = lambda t: t * t * (3 - 2 * t)


def capture():
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"])
        page = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=SCALE).new_page()
        page.goto(base, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_function("window.__portal && window.__portal.ready && window.__portal.ready()", timeout=90000)
        page.wait_for_function("(() => { const c = window.__portal.current(); return !!c && !!c.vals; })()", timeout=90000)
        page.add_style_tag(content=CSS)
        page.evaluate("() => { const m = window.__portal.map; m.setMinZoom(0); m.resize(); }")
        home = page.evaluate("([t, r, b, l]) => { const c = window.__portal.map.cameraForBounds([[125.95, 34.2], [129.65, 38.2]], {padding: {top: t, right: r, bottom: b, left: l}}); return [c.center.lng, c.center.lat, c.zoom]; }", PAD)

        def shot(view, name):
            ok = page.evaluate(SETTLE, list(view))
            page.wait_for_timeout(60)
            page.screenshot(path=str(raw / name))
            return ok

        bad = 0
        # B — the six parameters on the whole country
        for v in ORDER_B:
            page.evaluate(LAYER, [v, "all", 0])
            bad += 0 if shot(home, f"B_{v}.png") else 1
        # C — into the lake (chlorophyll-a is on the map)
        for i in (range(NC) if not test else [0, NC // 2, NC - 1]):
            t = smooth((i + 1) / NC)
            view = [home[k] + (LAKE[k] - home[k]) * t for k in range(3)]
            bad += 0 if shot(view, f"C_{i:03d}.png") else 1
        # D — the twelve calendar months there
        for m in range(1, 13):
            page.evaluate(LAYER, ["chla", "clim", m])
            bad += 0 if shot(LAKE, f"D_{m:02d}.png") else 1
        br.close()
        print("captured; frames whose tiles had not all arrived:", bad, flush=True)
        return home


def month_strip(im, month, alpha=1.0):
    """The strip of months at the top left, the current one lit. Drawn at twice the size and scaled, for clean edges."""
    if not STRIP:
        return im
    u = SCALE                                                 # one CSS pixel, in frame pixels
    s = 2 * u
    r = lambda v: int(round(v))
    pad, cell, hgt = r(12 * s), r(21 * s), r(30 * s)
    w = pad * 2 + cell * 12
    strip = Image.new("RGBA", (w, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.rounded_rectangle([0, 0, w - 1, hgt - 1], radius=hgt // 2, fill=(15, 19, 24, 190))
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", r(15 * s))
        bold = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", r(15 * s), index=1)
    except OSError:
        font = bold = ImageFont.load_default()
    for k, ch in enumerate(MON):
        on = k == month - 1
        cx = pad + cell * k + cell // 2
        if on:
            d.rounded_rectangle([cx - cell // 2 + 2, r(4 * s), cx + cell // 2 - 2, hgt - r(4 * s)], radius=r(10 * s), fill=(253, 231, 37, 235))
        tw = d.textlength(ch, font=bold if on else font)
        d.text((cx - tw / 2, r(6 * s)), ch, font=bold if on else font, fill=(15, 19, 24, 255) if on else (240, 238, 230, 200))
    strip = strip.resize((w // 2, hgt // 2), Image.LANCZOS)
    if alpha < 1:
        strip.putalpha(strip.getchannel("A").point(lambda a: int(a * alpha)))
    base = im.convert("RGBA")
    base.alpha_composite(strip, (r(16 * u), r(16 * u)))
    return base.convert("RGB")


def compose():
    load = lambda name: Image.open(raw / name).convert("RGB")
    frames, marks = [], {}
    mark = lambda key: marks.__setitem__(key, round(len(frames) / FPS, 2))
    pics = [load(f"B_{v}.png") for v in ORDER_B]
    for k, v in enumerate(ORDER_B):
        mark("B_" + v)
        frames += [pics[k]] * (FIRST_B if k == 0 else HOLD_B)
        if k < len(ORDER_B) - 1:
            frames += [Image.blend(pics[k], pics[k + 1], smooth((j + 1) / (FADE_B + 1))) for j in range(FADE_B)]
    mark("C")
    frames += [load(f"C_{i:03d}.png") for i in range(NC)]
    months = [load(f"D_{m:02d}.png") for m in range(1, 13)]
    last_c = frames[-1]
    mark("D")
    for j in range(FADE_D):                                   # the record mean gives way to January, the strip coming in
        t = smooth((j + 1) / (FADE_D + 1))
        frames.append(month_strip(Image.blend(last_c, months[0], t), 1, alpha=t))
    for m in range(1, 13):
        frames += [month_strip(months[m - 1], m)] * HOLD_D
        if m < 12:
            frames += [month_strip(Image.blend(months[m - 1], months[m], smooth((j + 1) / (FADE_D + 1))), m if j < FADE_D // 2 else m + 1) for j in range(FADE_D)]
    mark("E")
    end, first = frames[-1], frames[0]
    frames += [Image.blend(end, first, smooth((j + 1) / (NE + 1))) for j in range(NE)]
    for i, f in enumerate(frames):
        f.save(final / f"f_{i:04d}.png")
    marks["duration"] = round(len(frames) / FPS, 2)
    (out / "timeline.json").write_text(json.dumps({"fps": FPS, "frames": len(frames), "seconds": marks, "order": ORDER_B,
                                                   "size": [W, H], "scale": SCALE, "pad": PAD, "months_drawn_in": STRIP,
                                                   "months": {"first_frame": int(round(marks["D"] * FPS)), "fade_in": FADE_D, "hold": HOLD_D, "fade": FADE_D}}, indent=1))
    print(len(frames), "frames,", marks, flush=True)


if __name__ == "__main__":
    capture()
    if not test:
        compose()
