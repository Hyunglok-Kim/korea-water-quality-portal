#!/usr/bin/env python3
"""project_preview.py --site DIR [--port 8816] — the lab's project pages with the new block on them, locally.

    python embed/tools/project_preview.py --site ~/somewhere/site        # http://127.0.0.1:8816/

Shows https://hydroai.net/project/<slug> the way it will look with embed/project/project.html as one Code
Embed on the Projects template page, right after the navigation bar. Two kinds of page:

    a project that is on the site       the live page, with the block put on it. Nothing else is changed.
    a project that is not on the site   a page built the way Webflow would build it from an item of the
    yet (a folder in --site)            Projects collection: the live template with this project's title,
                                        date, text and pictures in the places of the item's fields.

--site is a folder outside this repository (the texts and figures of projects that are not public yet do not
belong in a public repository):

    DIR/projects.json            [{"slug": ..., "title": ..., "date": ..., "person": "Ms. Subin Kim",
                                   "summary": ..., "thumb": "file.webp"}, ...]   in the order of the list
                                 ("people": [names] when the project is the main project of several;
                                  "replaces": the slug of a page on the site that this one takes the place of)
    DIR/<slug>/body.html         the item's text as Webflow's rich text would hold it: p, h2, h3, ul, ol,
                                 blockquote, figure > div > img + figcaption, a, strong, em. Picture
                                 addresses are file names in the same folder.
    DIR/<slug>/*.webp ...        the pictures

    /                         a list of the projects in --site
    /project/<slug>           a project page with the block (?old: without it)
    /people                   the live People page with each person's "Main Project Link" pointing at the
                              project that projects.json names for them, so that the two pages can be
                              walked both ways before anything is changed in Webflow
    /media/<slug>/<file>      a picture from --site

Nothing is sent anywhere. The page's styles, fonts and scripts come from Webflow's CDN as on the live page;
any other address is passed on to hydroai.net. The block file and the site folder are read again on every
request, so an edit shows on reload.

Needs starlette and uvicorn (as dev_server.py does).
"""
import argparse
import html
import json
import mimetypes
import re
import urllib.request
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.routing import Route

ap = argparse.ArgumentParser()
ap.add_argument("--site", required=True, help="the folder with projects.json and one folder per project")
ap.add_argument("--port", type=int, default=8816)
ap.add_argument("--shell", default="enhancing-earth-science-predictions-through-advanced-data-assimilation-techniques",
                help="the live project page whose template the new pages are built on")
a = ap.parse_args()

EMBED = Path(__file__).resolve().parents[1]
SITE = Path(a.site).expanduser().resolve()
LIVE = "https://hydroai.net/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
OPEN = '<div class="w-embed w-script">'      # a Code Embed as Webflow writes it into the page
CACHE = {}


def get(path):
    if path not in CACHE:
        req = urllib.request.Request(LIVE + path, headers={"User-Agent": UA})
        CACHE[path] = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    return CACHE[path]


def projects():
    return json.loads((SITE / "projects.json").read_text(encoding="utf-8"))


def element_end(text, start):
    """The index just past the element whose opening tag begins at `start`."""
    tag = re.match(r"<([a-zA-Z0-9]+)", text[start:]).group(1)
    depth = 0
    for m in re.finditer(rf"<(/?){tag}\b[^>]*>", text[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return start + m.end()
    raise AssertionError(f"no end for the <{tag}> at {start}")


def one(pattern, text, what):
    found = list(re.finditer(pattern, text))
    assert len(found) == 1, f"{what}: expected one, found {len(found)} (has the live page changed?)"
    return found[0]


def with_block(page):
    """The page with the block as a Code Embed right after the navigation bar (before the project's sections)."""
    if 'id="hj-project"' in page:      # the block is on the site: this folder's file in its place
        i = page.index('id="hj-project"')
        s = page.rindex(OPEN, 0, i) + len(OPEN)
        e = re.compile(r"</script>\s*</div>").search(page, i).end() - len("</div>")
        return page[:s] + block() + page[e:]
    m = one(r'(<div>\s*)?<div[^>]*class="section project-detail"', page, "the project's first section")
    return page[:m.start()] + OPEN + block() + "</div>" + page[m.start():]


def block():
    return (EMBED / "project" / "project.html").read_text(encoding="utf-8")


def item(p):
    """A project as the template's list of other projects holds it."""
    e = html.escape
    return ('<div role="listitem" class="w-dyn-item"><div class="project-image-wrap"><img src="/media/%s/%s" loading="lazy" alt=""/>'
            '<div class="space-80"></div></div><div class="block"><div class="text-block-h3-style">%s</div><div class="space-16"></div>'
            '<p>%s</p><div class="space-16"></div><a href="/project/%s" class="cta secondary w-button">Read this project</a></div></div>'
            % (p["slug"], e(p.get("thumb", "")), e(p["title"]), e(p.get("summary", "")), p["slug"]))


def built(p, plist):
    """The template with this project's fields, as Webflow would publish the item."""
    page = get("project/" + a.shell)
    body = (SITE / p["slug"] / "body.html").read_text(encoding="utf-8")
    body = re.sub(r'(<img\b[^>]*?\bsrc=")(?!https?:|/)([^"]+)"', lambda m: m.group(1) + "/media/" + p["slug"] + "/" + m.group(2) + '"', body)
    # the title, the date, the picture behind the old header
    h = one(r'<h1 class="mega-h1">.*?</h1>', page, "the title")
    page = page[:h.start()] + '<h1 class="mega-h1">' + html.escape(p["title"]) + "</h1>" + page[h.end():]
    d = one(r'<p class="text-medium">.*?</p>', page, "the date")
    page = page[:d.start()] + '<p class="text-medium">' + html.escape(p.get("date", "")) + "</p>" + page[d.end():]
    bg = one(r'<div style="background-image:url\(&quot;[^&]*&quot;\)" class="section project-detail">', page, "the header")
    page = page[:bg.start()] + '<div style="background-image:url(&quot;/media/%s/%s&quot;)" class="section project-detail">' % (p["slug"], html.escape(p.get("thumb", ""))) + page[bg.end():]
    # the text
    r = one(r'<div class="rich-text-block w-richtext">', page, "the text")
    page = page[:r.start()] + '<div class="rich-text-block w-richtext">' + body + "</div>" + page[element_end(page, r.start()):]
    # the list of other projects: this folder's projects first, as the collection would list them. An item of the live
    # list that a project of the folder stands for (the same slug, or the slug named in "replaces") is taken out first,
    # so that an edited project shows once, in its new form.
    for old in {q.get("replaces") or q["slug"] for q in plist} | {q["slug"] for q in plist}:
        i = page.find('href="/project/%s"' % old)
        if i >= 0:
            s = page.rindex('<div role="listitem"', 0, i); page = page[:s] + page[element_end(page, s):]
    lst = one(r'<div role="list" class="grid-project w-dyn-items">', page, "the list of other projects")
    page = page[:lst.end()] + "".join(item(q) for q in plist) + page[lst.end():]
    return re.sub(r"<title>[^<]*</title>", "<title>HydroAI</title>", page, count=1)


def project(request):
    slug = request.path_params["slug"]
    plist = projects()
    mine = [p for p in plist if p["slug"] == slug]
    page = built(mine[0], plist) if mine else get("project/" + slug)
    if "old" not in request.query_params:
        page = with_block(page)
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


def people(request):
    """The live People page, each person's main project link pointing at the project named for them."""
    page = get("people")
    for p, who in [(p, w) for p in projects() for w in (p.get("people") or [p.get("person")]) if w]:
        m = re.search(r'<h2 class="education-title">\s*' + re.escape(who) + r"\s*</h2>", page)
        assert m, "nobody named %r on the People page" % who
        s = page.index('<div class="rich-text-block-5 w-richtext">', m.end())
        e = element_end(page, s)
        rich = page[s:e]
        link = re.search(r'<a href="[^"]*"(>(?:<strong>)?\[?Main Pro\w+ Link)', rich)
        if link:
            rich = rich[:link.start()] + '<a href="/project/' + p["slug"] + '"' + link.group(1) + rich[link.end():]
        else:
            first = re.search(r"</p>", rich)
            rich = rich[:first.end()] + '<h5>[<a href="/project/' + p["slug"] + '">Main Project Link</a>]</h5>' + rich[first.end():]
        page = page[:s] + rich + page[e:]
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


def media(request):
    """A picture of the site folder. No header lets a page of another origin read it: these pictures are not public."""
    f = (SITE / request.path_params["slug"] / request.path_params["file"]).resolve()
    if SITE not in f.parents or not f.is_file():
        return Response("not found", status_code=404)
    return Response(f.read_bytes(), media_type=mimetypes.guess_type(f.name)[0] or "application/octet-stream", headers={"Cache-Control": "no-store"})


def index(request):
    rows = "".join('<li><a href="/project/%s">%s</a><span>%s</span></li>' % (p["slug"], html.escape(p["title"]), html.escape(p.get("person", "")))
                   for p in projects())
    page = ('<!doctype html><meta charset="utf-8"><title>Project pages, preview</title><style>body{font:16px/1.5 system-ui,sans-serif;max-width:860px;'
            'margin:48px auto;padding:0 20px;color:#1c3533}li{margin:0 0 12px}span{display:block;color:#5d6f6d;font-size:14px}a{color:#14622f}</style>'
            '<h1>Project pages, preview</h1><p>Not on hydroai.net. <a href="/people">The People page with these links</a></p><ol>' + rows + "</ol>")
    return HTMLResponse(page, headers={"Cache-Control": "no-store"})


def elsewhere(request):
    return RedirectResponse(LIVE + request.path_params["rest"], status_code=307)


app = Starlette(routes=[Route("/", index), Route("/project/{slug}", project), Route("/people", people),
                        Route("/media/{slug}/{file}", media),
                        Route("/{rest:path}", elsewhere)])

if __name__ == "__main__":
    for q in projects():      # fail now, not on the first request, if a project's folder or the live template is not as expected
        with_block(built(q, projects()))
    print(f"http://127.0.0.1:{a.port}/        ({len(projects())} projects in {SITE})", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
