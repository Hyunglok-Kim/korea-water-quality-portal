#!/usr/bin/env python3
"""home_new_preview.py [--port 8814] [--pages DIR] [--save DIR] [--local-media] — the lab's home page with this folder's blocks in it, locally.

    python embed/tools/home_new_preview.py                    # http://127.0.0.1:8814/
    python embed/tools/home_new_preview.py --save pages/      # also keep the three pages it fetched
    python embed/tools/home_new_preview.py --pages pages/     # use kept pages instead of fetching

The three blocks (embed/home/hero.html, latest.html, about.html) have been on hydroai.net since 2026-11-20, each
in a Webflow Code Embed. This fetches https://hydroai.net/ as it is now, with its Events and Publications pages,
and puts this folder's three files in the place of the three embeds, so that a change to a block can be looked
at and checked (check_home_new.py) before it is pasted into the Webflow Designer. With the files as published,
the page it serves is the live page, byte for byte, plus the <base> below.

Nothing is sent anywhere. The page's own styles, fonts and scripts come from Webflow's CDN as on the live page,
and a <base> makes its links lead to hydroai.net. The block files are read again on every request, so an edit
shows on reload. /events and /publication are served from here too, because the news block reads them from the
page's own address.

    /            the live page with this folder's blocks in it
    /?live       the live page as it is
    /?popup      with the announcement dialog on it (embed/home-announcement.html: made, and not used); add &fresh to see it again
    /?lang=ko    with the bilingual section in Korean (or lang=en); otherwise the browser's language decides

How a block is found on the live page: its embed begins with the file's first comment ("hydroai.net home page,
block N of 3") and ends with the file's one script, which is the last thing in each file. Keep both when
editing a block; this stops and says so otherwise.

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
ap.add_argument("--port", type=int, default=8814)
ap.add_argument("--pages", help="a folder with home.html, events.html and publication.html kept by --save, instead of fetching")
ap.add_argument("--save", help="keep the three fetched pages in this folder")
ap.add_argument("--local-media", action="store_true", help="serve this repository's loops from embed/media/ instead of the public site (for a loop that is not pushed yet)")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
SITE = "https://hydroai.net/"
PUBLIC_MEDIA = "https://hyunglok-kim.github.io/korea-water-quality-portal/embed/media/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PAGES = {"home": "", "events": "events", "publication": "publication"}
BLOCKS = ("hero.html", "latest.html", "about.html")        # block 1, 2 and 3 of 3, in the page's order
END = "</script>\n"                                         # how every block file ends


def get(name):
    if a.pages:
        return (Path(a.pages) / f"{name}.html").read_text(encoding="utf-8")
    req = urllib.request.Request(SITE + PAGES[name], headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


LIVE = {name: get(name) for name in PAGES}
if a.save:
    Path(a.save).mkdir(parents=True, exist_ok=True)
    for name, text in LIVE.items():
        (Path(a.save) / f"{name}.html").write_text(text, encoding="utf-8")


def embed(text):
    """A Code Embed as Webflow writes it into the page."""
    return '<div class="w-embed w-script">' + text + "</div>"


def block(name):
    text = (EMBED / "home" / name).read_text(encoding="utf-8")
    assert text.count("</script>") == 1 and text.endswith(END), f"{name}: a block is styles, markup and then one script that ends the file"
    if a.local_media:
        text = text.replace(PUBLIC_MEDIA, f"http://127.0.0.1:{a.port}/media/")
    return text


def new_home():
    """The live page with this folder's three files in the place of its three Code Embeds."""
    html = LIVE["home"]
    for n, name in enumerate(BLOCKS, 1):
        found = list(re.finditer(r'<div class="w-embed[^"]*"><!--\s+hydroai\.net home page, block %d of 3\b' % n, html))
        assert len(found) == 1, f"block {n} of 3: expected one such Code Embed on the live page, found {len(found)} (has the home page been changed or restored?)"
        start = found[0].start()
        end = html.index(END + "</div>", start) + len(END + "</div>")
        html = html[:start] + embed(block(name)) + html[end:]
    return html


def with_base(html):
    return re.sub(r"(<head[^>]*>)", r'\1<base href="' + SITE + '">', html, count=1)


FRESH = "<script>if (/[?&]fresh\\b/.test(location.search)) try { localStorage.removeItem('hydroai-announcement'); } catch (e) {}</script>\n"


def index(request):
    q = request.query_params
    if "live" in q:
        return HTMLResponse(with_base(LIVE["home"]), headers={"Cache-Control": "no-store"})
    html = new_home()
    if q.get("lang") in ("en", "ko"):
        html = html.replace("<body>", "<body><script>try { localStorage.setItem('hydroai-home-lang', '%s'); } catch (e) {}</script>" % q["lang"], 1)
    if "popup" in q:
        snippet = (EMBED / "home-announcement.html").read_text(encoding="utf-8")
        if a.local_media:
            snippet = snippet.replace(PUBLIC_MEDIA, f"http://127.0.0.1:{a.port}/media/")
        html = html.replace("</body>", FRESH + embed(snippet) + "\n</body>")
    return HTMLResponse(with_base(html), headers={"Cache-Control": "no-store"})


def page(name):
    def serve(request):
        return HTMLResponse(LIVE[name], headers={"Cache-Control": "no-store"})
    return serve


app = Starlette(routes=[
    Route("/", index),
    Route("/events", page("events")),
    Route("/publication", page("publication")),
    Mount("/media", app=StaticFiles(directory=str(EMBED / "media")), name="media"),
])

if __name__ == "__main__":
    new_home()      # fail now, not on the first request, if the live page or a block file is not as expected
    print(f"http://127.0.0.1:{a.port}/        (?live the page as it is on the site, ?lang=ko or en)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
