#!/usr/bin/env python3
"""The link-preview picture (assets/preview.jpg, 1200 x 630): the map of the record-mean chlorophyll-a with the
title over it, taken from a running copy of the portal.

    python tests/make_preview.py http://127.0.0.1:8797/index.html assets/preview.jpg

Needs playwright (chromium) and Pillow. Re-make it when the map's look or the title changes; the page's
og:image tag points at the published copy."""
import sys, io
from PIL import Image
from playwright.sync_api import sync_playwright
base, out = sys.argv[1], sys.argv[2]
GL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"]
with sync_playwright() as pw:
    br = pw.chromium.launch(args=GL)
    page = br.new_context(viewport={"width": 1240, "height": 1000}, device_scale_factor=2).new_page()
    page.goto(base + "?intro=0&embed=1&hidefooter=1", wait_until="domcontentloaded")
    page.wait_for_function("window.__portal && window.__portal.ready && window.__portal.ready()", timeout=60000)
    page.wait_for_function("window.__portal.current() && window.__portal.current().vals", timeout=60000)
    page.evaluate("""() => {
        document.documentElement.style.setProperty('--map-h', '630px');
        const w = document.querySelector('.mapwrap'); w.style.width = '1200px'; w.style.borderRadius = '0'; w.style.border = '0';
        for (const q of ['.side', '#cardRecord', '.map-tr', '.map-br', '.maplibregl-ctrl-top-right', '.maplibregl-ctrl-bottom-left', '#lgHist', '.lg-note', '#scaleSeg']) document.querySelectorAll(q).forEach((e) => e.style.display = 'none');
        const t = document.createElement('div');
        t.style.cssText = 'position:absolute;z-index:4;left:44px;top:40px;max-width:520px;color:#FAF9F5;text-shadow:0 1px 10px rgba(0,0,0,.75)';
        t.innerHTML = '<div style="font:500 17px Archivo,sans-serif;letter-spacing:.08em;text-transform:uppercase;opacity:.85">HydroAI Lab · GIST</div>'
          + '<div style="font:600 50px/1.08 \\'Source Serif 4\\',Georgia,serif;margin-top:10px">Inland Water Quality of South Korea</div>'
          + '<div style="font:400 22px/1.4 Archivo,sans-serif;margin-top:16px;opacity:.95">1 km grids of six parameters on 1,012 dates, 2016–2024, each with its uncertainty</div>';
        w.appendChild(t);
        window.__portal.map.resize();
        window.__portal.map.fitBounds([[125.2, 34.2], [129.7, 38.2]], {padding: {top: 26, bottom: 26, left: 560, right: 30}, duration: 0});
    }""")
    page.wait_for_timeout(2500)
    page.wait_for_function("window.__portal.map.areTilesLoaded()", timeout=60000)
    page.wait_for_timeout(800)
    im = Image.open(io.BytesIO(page.locator(".mapwrap").screenshot())).convert("RGB")
    im = im.resize((1200, 630), Image.LANCZOS)
    im.save(out, quality=88, optimize=True, progressive=True)
    print(im.size)
    br.close()
