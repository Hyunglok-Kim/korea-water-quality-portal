#!/usr/bin/env python3
"""people_preview.py [--port 8815] [--pages DIR] [--save DIR] — the lab's People page with the new block in it, locally.

    python embed/tools/people_preview.py                    # http://127.0.0.1:8815/people
    python embed/tools/people_preview.py --save pages/      # also keep the page it fetched
    python embed/tools/people_preview.py --pages pages/     # use a kept page instead of fetching (after the site has changed)

Fetches https://hydroai.net/people as it is now and shows it with this folder's block:

    while the block is not on the site    the two changes that putting it there makes in the Webflow Designer:
                                          the "Contact me" block at the foot of the page is removed (if it is
                                          still there), and embed/people/people.html is put right after the
                                          navigation bar, as one Code Embed
    once the block is on the site         embed/people/people.html in the place of the page's Code Embed, so that
                                          a change is seen on the page as it is before it goes into the Designer;
                                          with the file as published this is the live page byte for byte

Nothing else on the page changes: the block reads the people, the group photographs and the motto from the
page's own content (the CMS lists in the five tabs, the four pictures above them) and shows them its own way.

Nothing is sent anywhere; `?old` shows the site untouched. The page's styles, fonts and scripts come from Webflow's CDN as on the live page; any
other address (/about, /contact, ...) is passed on to hydroai.net. The block file is read again on every
request, so an edit shows on reload.

    /people               the new page (the site's own address for it, so that the navigation bar marks "People")
    /people?old           the page as it is on the site now, for comparison
  and, while the block is not on the site:
    /people?cta           the new page with the "Contact me" block still on it
    /people?place=first   the block as the first element of the page's section instead of right after the navigation bar
    /people?place=last    the block as the last element of the page (it works there too, see embed/people/README.md)
    /people?page=NAME     another page from the --pages folder (NAME.html), for trying the block on changed content

Needs starlette and uvicorn (as dev_server.py does).
"""
import argparse
import re
import urllib.request
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, default=8815)
ap.add_argument("--pages", help="a folder with people.html kept by --save, instead of fetching")
ap.add_argument("--save", help="keep the fetched page in this folder")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
SITE = "https://hydroai.net/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"


def get():
    if a.pages:
        return (Path(a.pages) / "people.html").read_text(encoding="utf-8")
    req = urllib.request.Request(SITE + "people", headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")


LIVE = get()
if a.save:
    Path(a.save).mkdir(parents=True, exist_ok=True)
    (Path(a.save) / "people.html").write_text(LIVE, encoding="utf-8")


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


def embed(text):
    return OPEN + text + "</div>"


def carried(html):
    """Where the page carries the block's text (start, end), or None while the block is not on the page."""
    i = html.find('id="hp-people"')
    if i < 0:
        return None
    return html.rindex(OPEN, 0, i) + len(OPEN), re.compile(r"</script>\s*</div>").search(html, i).end() - len("</div>")


def new_page(html, place="nav", cta=False):
    text = (EMBED / "people" / "people.html").read_text(encoding="utf-8")
    at = carried(html)
    if at:      # the block is on the site: this folder's file in its place
        return html[:at[0]] + text + html[at[1]:]
    # 1. the "Contact me" block: the last section of the page, a component that other pages carry too
    gone = 'class="cta-block"' not in html
    if not cta and not gone:
        m = one(r'<div class="section"><div class="teaching-detail-wrap w-container"><div[^>]*class="cta-block"', html, 'the "Contact me" block')
        html = html[:m.start()] + html[element_end(html, m.start()):]
    # 2. the block
    block = embed(text)
    sec = one(r'<div class="section teachers">', html, "the page's section")
    if place == "first":
        at = sec.end()
    elif place == "last":
        at = html.index("<script", element_end(html, sec.start()))
    else:
        assert html[:sec.start()].rstrip().endswith("</div>") and 'class="navbar w-nav"' in html[:sec.start()], "the navigation bar no longer comes right before the section"
        at = sec.start()
    return html[:at] + block + html[at:]


def index(request):
    q = request.query_params
    html = LIVE
    if q.get("page"):
        assert a.pages and re.fullmatch(r"[\w.-]+", q["page"]), "?page= needs --pages and a plain name"
        html = (Path(a.pages) / (q["page"] + ".html")).read_text(encoding="utf-8")
    if "old" not in q:
        html = new_page(html, q.get("place", "nav"), "cta" in q)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


def elsewhere(request):
    return RedirectResponse(SITE + request.path_params["rest"], status_code=307)


def home(request):
    q = request.url.query
    return RedirectResponse("/people" + ("?" + q if q else ""), status_code=307)


app = Starlette(routes=[Route("/", home), Route("/people", index), Route("/{rest:path}", elsewhere)])

if __name__ == "__main__":
    new_page(LIVE)      # fail now, not on the first request, if the live page no longer has the shape these changes expect
    at = carried(LIVE)
    if at:
        same = LIVE[at[0]:at[1]].strip() == (EMBED / "people" / "people.html").read_text(encoding="utf-8").strip()
        print("the block is on the site, " + ("the same as this folder's file" if same else "and DIFFERS from this folder's file (the preview shows the file)"), flush=True)
    else:
        print("the block is not on the site" + ("" if 'class="cta-block"' in LIVE else '; the "Contact me" block is gone from it'), flush=True)
    print(f"http://127.0.0.1:{a.port}/people        (?old the live page, ?cta with the Contact me block, ?place=first or last)", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
