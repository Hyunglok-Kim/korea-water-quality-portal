#!/usr/bin/env python3
"""home_new_preview.py [--port 8814] [--pages DIR] [--save DIR] [--local-media] — the lab's home page with the new blocks in it, locally.

    python embed/tools/home_new_preview.py                    # http://127.0.0.1:8814/
    python embed/tools/home_new_preview.py --save pages/      # also keep the three pages it fetched
    python embed/tools/home_new_preview.py --pages pages/     # use kept pages instead of fetching (after the site has changed)

Fetches https://hydroai.net/ as it is now, with its Events and Publications pages, and makes on it the same
changes that publishing would make in the Webflow Designer:

    1. the hero's dark block and the two photographs under it  ->  embed/home/hero.html      (one Code Embed)
    2. at the end of the first section                          ->  embed/home/latest.html, embed/home/about.html
    3. the long paragraph above the four green tiles            ->  removed (its words are in about.html)
    4. the stray "Heading" at the foot of the page              ->  removed
    5. two misspellings in the sections below                   ->  corrected ("Rede more", "improvments")

Nothing is sent anywhere. The page's own styles, fonts and scripts come from Webflow's CDN as on the live page,
and a <base> makes its links lead to hydroai.net. The block files are read again on every request, so an edit
shows on reload. /events and /publication are served from here too, because the news block reads them from the
page's own address.

    /            the new page
    /?old        the page as it is on the site now, for comparison
    /?popup      the new page with the announcement dialog (embed/home-announcement.html) on it; add &fresh to see it again
    /?lang=ko    the new page with the bilingual section in Korean (or lang=en); otherwise the browser's language decides

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
ap.add_argument("--local-media", action="store_true", help="serve this repository's loops from embed/media/ instead of the public site")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
SITE = "https://hydroai.net/"
PUBLIC_MEDIA = "https://hyunglok-kim.github.io/korea-water-quality-portal/embed/media/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PAGES = {"home": "", "events": "events", "publication": "publication"}


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
assert "hh-hero" not in LIVE["home"], "the home page already carries the new blocks: use pages kept from before (--pages)"


def element_end(html, start):
    """The index just past the element whose opening tag begins at `start`."""
    tag = re.match(r"<([a-zA-Z0-9]+)", html[start:]).group(1)
    depth = 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", html[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    raise AssertionError(f"no end for the <{tag}> at {start}")


def one(pattern, html, what):
    found = list(re.finditer(pattern, html))
    assert len(found) == 1, f"{what}: expected one, found {len(found)} (has the live page changed?)"
    return found[0]


def embed(text):
    """A Code Embed as Webflow writes it into the page."""
    return '<div class="w-embed w-script">' + text + "</div>"


def block(name):
    text = (EMBED / "home" / name).read_text(encoding="utf-8")
    if a.local_media:
        text = text.replace(PUBLIC_MEDIA, f"http://127.0.0.1:{a.port}/media/")
    return text


def new_home():
    html = LIVE["home"]
    # 1. the hero block and the photographs under it -> the hero embed
    m = one(r'<div[^>]*class="hero-block"[^>]*>', html, "the hero block")
    end = element_end(html, m.start())
    p = one(r'<div class="w-layout-blockcontainer container-6 w-container">', html, "the photographs under the hero")
    assert p.start() == end, "the photographs no longer follow the hero block"
    html = html[:m.start()] + embed(block("hero.html")) + html[element_end(html, p.start()):]
    # 2. the news block and the about block, last in the first section
    s = one(r'<div class="section one-step-away-section">', html, "the second section")
    assert html[s.start() - 6:s.start()] == "</div>", "the first section does not end where expected"
    at = s.start() - 6
    html = html[:at] + embed(block("latest.html")) + embed(block("about.html")) + html[at:]
    # 3. the long paragraph above the tiles
    m = one(r'<p class="paragraph">', html, "the long paragraph")
    end = html.index("</p>", m.start()) + 4
    assert "InnoCore" in html[m.start():end] and html[end:end + 23] == '<div class="usps-wrap">', "the long paragraph is not what it was"
    html = html[:m.start()] + html[end:]
    # 4. the stray heading
    assert html.count("<h1>Heading</h1>") == 1
    html = html.replace("<h1>Heading</h1>", "")
    # 5. the misspellings
    for wrong, right in [(">Rede more<", ">Read more<"), ("resolution improvments", "resolution improvements")]:
        assert html.count(wrong) == 1, wrong
        html = html.replace(wrong, right)
    return html


def with_base(html):
    return re.sub(r"(<head[^>]*>)", r'\1<base href="' + SITE + '">', html, count=1)


FRESH = "<script>if (/[?&]fresh\\b/.test(location.search)) try { localStorage.removeItem('hydroai-announcement'); } catch (e) {}</script>\n"


def index(request):
    q = request.query_params
    if "old" in q:
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
    new_home()      # fail now, not on the first request, if the live page no longer has the shape these changes expect
    print(f"http://127.0.0.1:{a.port}/        (?old the live page, ?popup with the announcement, ?lang=ko or en)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
