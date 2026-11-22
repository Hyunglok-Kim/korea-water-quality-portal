#!/usr/bin/env python3
"""publications_preview.py [--port 8817] [--pages DIR] [--save DIR] — the lab's Publications page with the new block in it, locally.

    python embed/tools/publications_preview.py                    # http://127.0.0.1:8817/publication
    python embed/tools/publications_preview.py --save pages/      # also keep the pages it fetched
    python embed/tools/publications_preview.py --pages pages/     # use kept pages instead of fetching (after the site has changed)

Fetches https://hydroai.net/publication as it is now and shows it with this folder's block:

    while the block is not on the site    the one change that putting it there makes in the Webflow Designer:
                                          embed/publications/publications.html as one Code Embed, the first
                                          element of the page (before the page's own section)
    once the block is on the site         embed/publications/publications.html in the place of the page's Code
                                          Embed, so that a change is seen on the page as it is before it goes
                                          into the Designer; with the file as published this is the live page
                                          byte for byte

Nothing else on the page changes: the block reads the papers, the quotation and the three lists from the page's
own content (the CMS lists in the three tabs) and shows them its own way. The page lists its journal papers a
few at a time ("Next"); the block asks for the following pages itself, and this server passes each of those
requests on to hydroai.net (/publication?<key>_page=2 ...) and puts the block on them as the site would.

Nothing is sent anywhere; `?old` shows the site untouched. The page's styles, fonts and scripts come from
Webflow's CDN as on the live page; any other address (/about, /contact, ...) is passed on to hydroai.net. The
block file is read again on every request, so an edit shows on reload.

    /publication               the new page (the site's own address for it, so the navigation bar marks "Publications")
    /publication?old           the page as it is on the site now, for comparison
    /publication?place=last    the block as the last element of the page instead of the first (it works there too)
    /publication?one           every journal paper on the first page and no "Next", as the page would be if its
                               list were set to 100 a page in the Designer (the block then asks for nothing)

Needs starlette and uvicorn (as dev_server.py does).
"""
import argparse
import re
import urllib.parse
import urllib.request
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8817)
ap.add_argument("--pages", help="a folder with the pages kept by --save, instead of fetching")
ap.add_argument("--save", help="keep the fetched pages in this folder")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
BLOCK = EMBED / "publications" / "publications.html"
SITE = "https://hydroai.net/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PAGED = re.compile(r"^[0-9a-f]{4,12}_page$")      # Webflow's name for a list's page number: 9f7fdb6f_page
KEPT = {}


def name(query):
    """The file a page is kept in: publication.html, publication.9f7fdb6f_page=2.html"""
    return "publication" + ("." + query if query else "") + ".html"


def get(query=""):
    """The live page for this query (only a list's page number is passed on), fetched once."""
    if query not in KEPT:
        if a.pages:
            KEPT[query] = (Path(a.pages) / name(query)).read_text(encoding="utf-8")
        else:
            req = urllib.request.Request(SITE + "publication" + ("?" + query if query else ""), headers={"User-Agent": UA})
            KEPT[query] = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
            if a.save:
                Path(a.save).mkdir(parents=True, exist_ok=True)
                (Path(a.save) / name(query)).write_text(KEPT[query], encoding="utf-8")
    return KEPT[query]


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


OPEN = '<div class="w-embed w-script">'      # a Code Embed as Webflow writes it into the page


def carried(html):
    """Where the page carries the block's text (start, end), or None while the block is not on the page."""
    i = html.find('id="hb-pubs"')
    if i < 0:
        return None
    return html.rindex(OPEN, 0, i) + len(OPEN), re.compile(r"</script>\s*</div>").search(html, i).end() - len("</div>")


def new_page(html, place="first"):
    text = BLOCK.read_text(encoding="utf-8")
    at = carried(html)
    if at:      # the block is on the site: this folder's file in its place
        return html[:at[0]] + text + html[at[1]:]
    sec = one(r'<div class="section teachers">', html, "the page's section")
    if place == "last":
        at = html.index("<script", element_end(html, sec.start()))
    else:
        assert html[:sec.start()].rstrip().endswith("<body>"), "the page's section is no longer the first element of the page"
        at = sec.start()
    return html[:at] + OPEN + text + "</div>" + html[at:]


ITEM = '<div role="listitem" class="w-dyn-item"><div class="publications-card">'


def journal_items(html):
    """(start, end) of the journal papers' items on a page: the first tab's list."""
    i = html.index('<div role="list"')
    j = element_end(html, i)
    k = html.index(ITEM, i)
    assert k < j, "the first list has no journal paper"
    return k, j - len("</div>")


def in_one(html):
    """The first page with every journal paper on it and no "Next": the list set to 100 a page."""
    k, j = journal_items(html)
    more, n, page = "", 2, html
    while True:
        nxt = re.search(r'<a href="\?([0-9a-f]+_page)=(\d+)"[^>]*class="w-pagination-next', page)
        if not nxt:
            break
        page = get(f"{nxt.group(1)}={n}")
        s, e = journal_items(page)
        more += page[s:e]
        n += 1
    html = html[:j] + more + html[j:]
    nav = html.index('<div role="navigation" aria-label="List" class="w-pagination-wrapper">')
    return html[:nav] + html[element_end(html, nav):]


def index(request):
    q = request.query_params
    paged = [(k, v) for k, v in q.items() if PAGED.match(k) and v.isdigit()]
    html = get(urllib.parse.urlencode(paged[:1]))
    if "one" in q:
        html = in_one(get())
    if "old" not in q:
        html = new_page(html, q.get("place", "first"))
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def elsewhere(request):
    return RedirectResponse(SITE + request.path_params["rest"], status_code=307)


def home(request):
    q = request.url.query
    return RedirectResponse("/publication" + ("?" + q if q else ""), status_code=307)


app = Starlette(routes=[Route("/", home), Route("/publication", index), Route("/{rest:path}", elsewhere)])

if __name__ == "__main__":
    LIVE = get()
    new_page(LIVE)      # fail now, not on the first request, if the live page no longer has the shape this change expects
    at = carried(LIVE)
    if at:
        same = LIVE[at[0]:at[1]].strip() == BLOCK.read_text(encoding="utf-8").strip()
        print("the block is on the site, " + ("the same as this folder's file" if same else "and DIFFERS from this folder's file (the preview shows the file)"), flush=True)
    else:
        print("the block is not on the site", flush=True)
    print(f"http://127.0.0.1:{a.port}/publication        (?old the live page, ?place=last, ?one the papers on one page)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
