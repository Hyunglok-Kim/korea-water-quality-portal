#!/usr/bin/env python3
"""reel_room.py [URL] [--browser chromium] [--step 2] — does every dataset's name and line fit the first screen, at every width?

    python embed/tools/reel_room.py                          # the local preview (home_new_preview.py, port 8814)
    python embed/tools/reel_room.py --browser webkit
    python embed/tools/reel_room.py https://hydroai.net/     # the live page

The home page's first screen keeps one height whichever dataset is on show, because the room under the pictures
(.hh-reel-info) is reserved per window width in hero.html. A name or line that is too long for that room makes the
first screen jump when its dataset comes. check_home_new.py looks at thirteen window sizes; a longer line can
overflow only between them (on 2026-11-21 one candidate did, from 480 to 488 px). This goes through every width
from 320 to 2048 px, shows each dataset in turn and lists the ranges of widths where one needs more room than is
reserved.

Run it after changing a dataset's title or line (REEL.slides and the markup in hero.html) or the reserved heights.
The exit status is the number of widths with too little room. Needs playwright.
"""
import argparse
import sys

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8814/")
ap.add_argument("--browser", default="chromium", choices=["chromium", "webkit", "firefox"])
ap.add_argument("--step", type=int, default=2, help="pixels between the widths tried")
a = ap.parse_args()

# each dataset on show in turn: the height its name and line take, and the first screen's height with it
JS = """async () => { const tabs = [...document.querySelectorAll('.hh-reel-tab')], info = document.querySelector('.hh-reel-info'), hero = document.querySelector('.hh-hero'), out = [];
  for (const t of tabs) { t.click(); await new Promise(r => setTimeout(r, 12)); out.push([Math.round(info.getBoundingClientRect().height * 10) / 10, Math.round(hero.getBoundingClientRect().height)]); }
  tabs[0].click();
  return { room: parseFloat(getComputedStyle(info).minHeight), out }; }"""

with sync_playwright() as pw:
    br = getattr(pw, a.browser).launch()
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")      # still pictures: nothing to wait for
    page = ctx.new_page()
    page.goto(a.url if a.url.endswith("/") else a.url + "/", wait_until="load", timeout=60000)
    page.wait_for_selector(".hh-reel-tab", state="attached", timeout=20000)
    page.wait_for_timeout(1500)
    rows = []
    for w in range(320, 2049, a.step):
        page.set_viewport_size({"width": w, "height": 900})
        page.wait_for_timeout(40)
        r = page.evaluate(JS)
        rows.append((w, r["room"], [round(h - r["room"], 1) for h, _ in r["out"]], len({hh for _, hh in r["out"]}) > 1))
    br.close()

bad = [i for i, (_, _, over, uneven) in enumerate(rows) if max(over) > 0.5 or uneven]
start = None
for i in range(len(rows) + 1):
    hit = i in bad
    if hit and start is None:
        start = i
    if not hit and start is not None:
        seg = rows[start:i]
        who = sorted({k + 1 for _, _, over, _ in seg for k, v in enumerate(over) if v > 0.5})
        print(f"  {seg[0][0]}-{seg[-1][0]} px: {seg[0][1]:.0f} px reserved, up to {max(max(o) for _, _, o, _ in seg):.0f} px more needed by dataset(s) {who}"
              + ("; the first screen changes height" if any(u for *_, u in seg) else ""))
        start = None
print(f"{a.browser}: {len(rows)} widths from 320 to 2048 px; too little room at {len(bad)}")
sys.exit(min(len(bad), 100))
