#!/usr/bin/env python3
"""home_preview.py [--port 8813] [--local-media] [--page FILE] — the lab's home page with the announcement on it, locally.

    python embed/tools/home_preview.py                 # http://127.0.0.1:8813/  (loops from the public site)
    python embed/tools/home_preview.py --local-media   # loops from embed/media/ here (before they are pushed)

Fetches https://hydroai.net/ as it is now (or reads --page), puts `embed/home-announcement.html` before </body>
as the Webflow embed would, and serves the result. Nothing is sent anywhere: this is how to look at a change to
the announcement before it goes on the site. The page's own styles, fonts and scripts come from Webflow's CDN as
on the live page; a <base> makes its links lead to hydroai.net. The announcement file is read again on every
request, so an edit shows on reload.

`/?fresh` first forgets what this browser has seen, so the dialog opens again.
Needs starlette and uvicorn (as dev_server.py does); they answer Range requests, which Safari needs for video.
"""
import argparse
import re
import urllib.request
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8813)
ap.add_argument("--local-media", action="store_true", help="serve the loops from embed/media/ instead of the public site")
ap.add_argument("--page", help="a saved copy of the home page's HTML, instead of fetching it")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
PUBLIC_MEDIA = "https://hyunglok-kim.github.io/korea-water-quality-portal/embed/media/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
FRESH = "<script>if (/[?&]fresh\\b/.test(location.search)) try { localStorage.removeItem('hydroai-announcement'); } catch (e) {}</script>\n"

if a.page:
    HOME = Path(a.page).read_text(encoding="utf-8")
else:
    HOME = urllib.request.urlopen(urllib.request.Request("https://hydroai.net/", headers={"User-Agent": UA}), timeout=30).read().decode("utf-8")
assert HOME.count("</body>") == 1, "the home page has no single </body>"
# the block's own element, not the name alone: the home page's first block mentions it in its script (it waits behind the dialog)
assert 'id="ha-ann"' not in HOME, "the home page already carries the announcement: preview a saved copy from before (--page)"
HOME = re.sub(r"(<head[^>]*>)", r'\1<base href="https://hydroai.net/">', HOME, count=1)


def index(request):
    snippet = (EMBED / "home-announcement.html").read_text(encoding="utf-8")
    if a.local_media:
        assert PUBLIC_MEDIA in snippet
        snippet = snippet.replace(PUBLIC_MEDIA, f"http://127.0.0.1:{a.port}/media/")
    return HTMLResponse(HOME.replace("</body>", FRESH + snippet + "\n</body>"), headers={"Cache-Control": "no-store"})


app = Starlette(routes=[
    Route("/", index),
    Mount("/media", app=StaticFiles(directory=str(EMBED / "media")), name="media"),
])

if __name__ == "__main__":
    print(f"http://127.0.0.1:{a.port}/        (add ?fresh to see the dialog again)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
