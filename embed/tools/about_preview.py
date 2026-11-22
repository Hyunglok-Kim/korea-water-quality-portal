#!/usr/bin/env python3
"""about_preview.py [--port 8819] [--pages DIR] [--save DIR] [--public-media] — the lab's About page with the new block in it, locally.

    python embed/tools/about_preview.py                    # http://127.0.0.1:8819/about
    python embed/tools/about_preview.py --save pages/      # also keep the pages it fetched
    python embed/tools/about_preview.py --pages pages/     # use kept pages instead of fetching (after the site has changed)

Fetches https://hydroai.net/about as it is now and shows it with this folder's block:

    while the block is not on the site    the change that putting it there makes in the Webflow Designer:
                                          embed/about/about.html as one Code Embed right after the navigation
                                          bar, and the page's four old sections taken off the page
    once the block is on the site         embed/about/about.html in the place of the page's Code Embed, so that
                                          a change is seen on the page as it is before it goes into the
                                          Designer; with the file as published this is the live page byte for
                                          byte

Unlike the People, Projects and Publications blocks this one holds the page's words itself: the About page
has no collection behind it. What it reads from the site is what would otherwise go stale: the datasets (the
Data page's cards, from /data at the page's own address). This server passes that request, and a few other
pages of the site, on to hydroai.net.

Nothing is sent anywhere; `?old` shows the site untouched. The page's styles, fonts and scripts come from
Webflow's CDN as on the live page. The block file is read again on every request, so an edit shows on reload.
The block's pictures are served from embed/media/ here (they are on the public site only after a push); with
--public-media the block is left to fetch them from the public address, as on the site.

    /about                the new page (the site's own address for it, so the navigation bar marks "About")
    /about?old            the page as it is on the site now, for comparison
    /about?keep           the block with the page's old sections left under it (what the page would be if
                          they were not taken off)
    /about?nofetch        nothing can be fetched (every fetch fails): the page must still be whole, with the
                          datasets written in the block and the picture in the globe's place

Needs starlette and uvicorn (as dev_server.py does).
"""
import argparse
import re
import urllib.error
import urllib.request
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8819)
ap.add_argument("--pages", help="a folder with the pages kept by --save, instead of fetching")
ap.add_argument("--save", help="keep the fetched pages in this folder")
ap.add_argument("--public-media", action="store_true", help="leave the block's pictures on their public address instead of serving embed/media/")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
BLOCK = EMBED / "about" / "about.html"
SITE = "https://hydroai.net/"
PUBLIC_MEDIA = "https://hyunglok-kim.github.io/korea-water-quality-portal/embed/media/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
READ = ("publication", "projects", "data", "people", "events", "teaching")     # pages the block may ask for
KEPT = {}


def name(path, query):
    return path + ("." + query if query else "") + ".html"


def get(path, query=""):
    """A live page, fetched once."""
    key = (path, query)
    if key not in KEPT:
        if a.pages:
            KEPT[key] = (Path(a.pages) / name(path, query)).read_text(encoding="utf-8")
        else:
            req = urllib.request.Request(SITE + path + ("?" + query if query else ""), headers={"User-Agent": UA})
            KEPT[key] = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
            if a.save:
                Path(a.save).mkdir(parents=True, exist_ok=True)
                (Path(a.save) / name(path, query)).write_text(KEPT[key], encoding="utf-8")
    return KEPT[key]


def element_end(html, start):
    """The index just past the element whose opening tag begins at `start`."""
    tag = re.match(r"<([a-zA-Z0-9]+)", html[start:]).group(1)
    depth = 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", html[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    raise AssertionError(f"no end for the <{tag}> at {start}")


OPEN = '<div class="w-embed w-script">'      # a Code Embed as Webflow writes it into the page
OLD = ("section hero-about-us", "section course-process", "section process-tiles", "section")   # the page's four old sections, in order


def carried(html):
    """Where the page carries the block's text (start, end), or None while the block is not on the page."""
    i = html.find('id="hb-about"')
    if i < 0:
        return None
    return html.rindex(OPEN, 0, i) + len(OPEN), re.compile(r"</script>\s*</div>").search(html, i).end() - len("</div>")


def block_text():
    text = BLOCK.read_text(encoding="utf-8")
    if not a.public_media:
        text = text.replace(PUBLIC_MEDIA, f"http://127.0.0.1:{a.port}/media/")
    return text


def new_page(html, keep=False):
    text = block_text()
    at = carried(html)
    if at:      # the block is on the site: this folder's file in its place
        return html[:at[0]] + text + html[at[1]:]
    nav = html.index('<div data-animation="default"', html.index("<body"))
    assert 'class="navbar w-nav"' in html[nav:nav + 300], "the navigation bar is no longer the first element of the page"
    start = element_end(html, nav)
    end = start
    for cls in OLD:
        assert html[end:end + 200].lstrip().startswith(f'<div class="{cls}">'), f'expected the old section "{cls}" here (has the live page changed?)'
        end = element_end(html, html.index("<div", end))
    assert html[end:].lstrip().startswith("<script"), "something follows the page's four old sections"
    return html[:start] + OPEN + text + "</div>" + (html[start:] if keep else html[end:])


def about(request):
    q = request.query_params
    html = get("about")
    if "old" not in q:
        html = new_page(html, "keep" in q)
        if "nofetch" in q:
            html = html.replace("<head>", "<head><script>window.fetch = function () { return Promise.reject(new Error('nofetch')); };</script>", 1)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def passed_on(request):
    """Another page of the site, as it is: the block reads a few of them from the page's own address."""
    rest = request.path_params["rest"]
    if rest.split("/")[0] not in READ:
        return RedirectResponse(SITE + rest + ("?" + request.url.query if request.url.query else ""), status_code=307)
    try:
        return HTMLResponse(get(rest, request.url.query), headers={"Cache-Control": "no-store"})
    except urllib.error.HTTPError as e:
        return Response(status_code=e.code)


def home(request):
    q = request.url.query
    return RedirectResponse("/about" + ("?" + q if q else ""), status_code=307)


app = Starlette(routes=[
    Route("/", home),
    Route("/about", about),
    Mount("/media", app=StaticFiles(directory=str(EMBED / "media")), name="media"),
    Route("/{rest:path}", passed_on),
])

if __name__ == "__main__":
    LIVE = get("about")
    new_page(LIVE)      # fail now, not on the first request, if the live page no longer has the shape this change expects
    at = carried(LIVE)
    if at:
        same = LIVE[at[0]:at[1]].strip() == BLOCK.read_text(encoding="utf-8").strip()
        print("the block is on the site, " + ("the same as this folder's file" if same else "and DIFFERS from this folder's file (the preview shows the file)"), flush=True)
    else:
        print("the block is not on the site", flush=True)
    print(f"http://127.0.0.1:{a.port}/about        (?old the live page, ?keep, ?nofetch)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
