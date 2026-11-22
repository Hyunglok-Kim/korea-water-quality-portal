#!/usr/bin/env python3
"""check_about.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the About page's block, checked.

    python embed/tools/check_about.py                               # the local preview (about_preview.py, port 8819)
    python embed/tools/check_about.py https://hydroai.net/about     # the live page, once the block is on it

What it looks at, in each browser:
  the page       one <h1>; the block is on and nothing of the old page is left beside it (its four sections, the
                 "Contact me" block); the order the lab head set: the panel with the globe first, holding the
                 page's title, then the lab in a statement, then its two lines of research; no photograph of
                 the lab and no counts (he had them taken off); no script error; (local) the block fits a Code
                 Embed and ends with its script
  the datasets   the Data page's cards, in its order: name, kind, picture and address, each address one that
                 opens its dataset on the Data page; a note (not a failure) when the rows written in the markup
                 are no longer the Data page's
  the field site what the block says of the ground network and the drone flights is what the Data page says
  the globe      drawn in its place, with as many satellites as the block names; a family can be put off and on;
                 it stands still while it is off screen
  the links      every address in the block answers; every picture has arrived
  falling back   without scripts; when the Data page cannot be read; when the globe's files do not arrive or its
                 orbits cannot be had: the page whole, with the markup's rows and the picture in the globe's place
  changed pages  a sixth dataset on the Data page, one fewer, a card without a picture
  the sizes      thirteen window sizes from 2048 px down to a 320 px phone: nothing wider than the window, no word
                 cut, the page centred, the columns as meant, everything there; where the globe stands above the
                 text, the text does not jump when the globe arrives (it is held back once to see)
The exit status is the number of failures. Needs playwright with the three browsers installed.
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8819/about")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures of every size")
ap.add_argument("--quick", action="store_true", help="leave out the changed pages and all sizes but three")
a = ap.parse_args()
URL = a.url
LOCAL = "127.0.0.1" in URL or "localhost" in URL
BLOCK = Path(__file__).resolve().parents[1] / "about" / "about.html"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
FAILS = 0
SIZES = [(2048, 970), (1680, 1050), (1440, 900), (1280, 720), (1200, 800), (1100, 700), (1024, 768), (960, 600), (834, 1194), (768, 1024), (600, 900), (390, 844), (320, 568)]
OLD = (".hero-about-us", ".course-process", ".process-tiles", ".cta-block", ".section")        # what the page held before the block
SITE = ("47 stations", "82", "5 minutes", "June 2025", "1 m", "one to two weeks")               # the field site's figures, in the block and on the Data page

# the Data page as it is here: its cards, and what it says of the field site
DATA = r"""async () => {
  const d = new DOMParser().parseFromString(await (await fetch('/data', { cache: 'no-store' })).text(), 'text/html');
  const sets = [...d.querySelectorAll('a.hd-card[href^="#"]')].map(c => ({ href: '/data' + c.getAttribute('href'), name: c.querySelector('h3').textContent.replace(/\s+/g, ' ').trim(),
    kind: [...c.querySelectorAll('.hd-tag')].pop().textContent.trim(), pic: (c.querySelector('video[poster]') || { getAttribute: () => '' }).getAttribute('poster'),
    there: !!d.getElementById('hd-panel-' + c.getAttribute('href').slice(1)) }));
  const cvs = d.querySelector('a.hd-card[href="#cvs"]'), place = d.getElementById('hd-panel-cvs');
  return { sets, cvs: ((cvs ? cvs.textContent : '') + ' ' + (place ? place.textContent : '')).replace(/\s+/g, ' ') };
}"""

# what the block shows
SHOWN = r"""() => {
  const r = document.getElementById('hb-about'), t = e => e ? e.textContent.replace(/\s+/g, ' ').trim() : '', seen = e => !!e && e.getClientRects().length > 0;
  const stage = r.querySelector('#ha-stage'), top = y => Math.round(y.getBoundingClientRect().top + scrollY);
  return { h1: document.querySelectorAll('h1').length, ready: r.getAttribute('data-ready'), live: r.getAttribute('data-live') || '',
    old: %s.filter(s => [...document.querySelectorAll(s)].some(e => !r.contains(e) && !e.closest('.w-nav'))),
    after: r.closest('.w-embed') && r.closest('.w-embed').nextElementSibling ? r.closest('.w-embed').nextElementSibling.tagName : '',
    order: [...r.querySelector('.ha-wrap').children].slice(0, 3).map(e => e.id || e.className), title: !!r.querySelector('#ha-orbit h1'), first: top(r.querySelector('#ha-orbit')),
    photos: [...r.querySelectorAll('figure, .ha-photo, img')].filter(e => e.tagName !== 'IMG' || /website-files/.test(e.getAttribute('src') || '')).length,
    counts: r.querySelectorAll('[data-n], .ha-nums, .ha-num').length,
    sets: [...r.querySelectorAll('.ha-set')].map(e => ({ href: e.getAttribute('href'), name: t(e.querySelector('b')), kind: t(e.querySelector('small')), pic: (e.querySelector('img') || { getAttribute: () => '' }).getAttribute('src') })),
    views: [...r.querySelectorAll('.ha-view')].map(t).join(' | '), sats: parseInt(t(r.querySelector('#ha-sats')), 10), now: seen(r.querySelector('#ha-now')),
    orbit: stage.getAttribute('data-orbit') || '', pic: seen(stage.querySelector('.ha-stage-pic')),
    canvases: [...stage.querySelectorAll('canvas')].filter(seen).length,
    anim: r.classList.contains('ha-anim'), faint: [...r.querySelectorAll('.ha-rise')].filter(e => getComputedStyle(e).opacity !== '1').length,
    links: [...new Set([...r.querySelectorAll('a[href]')].map(e => e.getAttribute('href')))],
    broken: [...r.querySelectorAll('img')].filter(e => seen(e) && !(e.complete && e.naturalWidth > 0)).map(e => e.getAttribute('src')),
    words: t(r).length };
}""" % repr(list(OLD))

# the globe: what it says of itself, and whether anything is drawn
GLOBE = r"""() => {
  const s = document.querySelector('#ha-stage'), st = window.HydroOrbit && HydroOrbit._state ? HydroOrbit._state() : null;
  const cv = [...s.querySelectorAll('canvas')].map(c => { let ink = 0; try { const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; for (let i = 3; i < d.length; i += 4 * 97) if (d[i]) ink++; } catch (e) { ink = -1; } return { w: c.width, cw: c.clientWidth, ink }; });
  return { on: s.getAttribute('data-orbit'), cv, total: st && st.total, shown: st && st.shown, drawn: st && st.drawn, running: st && st.running, frames: st && st.frames,
    chips: [...s.querySelectorAll('.ho-chip')].map(b => b.textContent.trim()) };
}"""

# measures at one window size
FIT = r"""() => {
  const W = document.documentElement.clientWidth, r = document.getElementById('hb-about');
  const box = e => e.getBoundingClientRect(), seen = e => e.getClientRects().length > 0, name = e => (e.className || e.tagName) + ':' + e.textContent.trim().slice(0, 24);
  const wrap = box(r.querySelector('.ha-wrap')), cols = sel => new Set([...r.querySelectorAll(sel)].filter(seen).map(c => Math.round(box(c).left))).size;
  return { W, scrollW: document.documentElement.scrollWidth,
    over: [...r.querySelectorAll('*')].filter(e => { const b = box(e); return b.width > 0 && (b.right > W + 0.5 || b.left < -0.5); }).map(name).slice(0, 4),
    cut: [...r.querySelectorAll('.ha-kicker, .ha-big, .ha-h2, .ha-axis b, .ha-axis small, .ha-view small, .ha-view b, .ha-step b, .ha-set small, .ha-set b, .ha-tags li, .ha-btn, .ha-link, .ha-card h3, .ha-kit dt, .ha-find address, .ho-chip, .ho-seg, .ho-clock, .ho-note')].filter(e => seen(e) && e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1).map(name).slice(0, 4),
    faint: [...r.querySelectorAll('.ha-rise')].filter(e => seen(e) && getComputedStyle(e).opacity !== '1').length,
    left: Math.round(wrap.left * 10) / 10, right: Math.round((W - wrap.right) * 10) / 10, wrap: Math.round(wrap.width),
    mission: cols('.ha-mission > *'), axes: cols('.ha-axis'), steps: cols('.ha-step'), cards: cols('.ha-two > .ha-card'), end: cols('.ha-end > *'),
    stage: Math.round(box(r.querySelector('#ha-stage')).width), orbit: r.querySelector('#ha-stage').getAttribute('data-orbit'),
    narrow: Math.round(Math.min(...[...r.querySelectorAll('.ha-prose p, .ha-axis span, .ha-step p, .ha-card p, .ha-view div')].filter(seen).map(e => box(e).width))) };
}"""

KICKER = "() => Math.round(document.querySelector('#ha-orbit .ha-kicker').getBoundingClientRect().top + scrollY)"
WALK = "async () => { const H = () => document.documentElement.scrollHeight; for (let y = 0; y < H(); y += Math.round(innerHeight * 0.7)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, H()); await new Promise(r => setTimeout(r, 250)); }"
READ = "() => { const r = document.getElementById('hb-about'); return !!r && r.getAttribute('data-live') === 'sets'; }"
ORBIT = "() => { const s = document.querySelector('#ha-stage'); return !!s && !!s.getAttribute('data-orbit'); }"


def ok(name, cond, detail=""):
    global FAILS
    if not cond:
        FAILS += 1
    print(("    ok    " if cond else "    FAIL  ") + name + (f"   [{detail}]" if detail != "" and not cond else ""), flush=True)
    return cond


def note(text):
    print("    note  " + text, flush=True)


def path_is(*names):
    return lambda u: urlsplit(u).path.strip("/") in names


def open_page(br, url=None, w=1440, h=900, edit=None, stop=(), **kw):
    """A page at `url`, walked from top to bottom so that everything that waits to be near has started. `edit` changes
    the Data page's HTML on its way to the block; `stop` names requests that fail (a path of the site, or a part of
    an address)."""
    ctx = br.new_context(viewport={"width": w, "height": h}, **kw)
    page = ctx.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    if edit:
        def handle(route):
            r = route.fetch()
            try:
                body = edit(r.text())
            except Exception as e:
                ok("the Data page could be changed for this check", False, repr(e))
                body = r.text()
            route.fulfill(response=r, body=body)
        page.route(path_is("data"), handle)
    for s in stop:
        page.route((path_is(s) if "." not in s else (lambda u, s=s: s in u)), lambda route: route.abort())
    page.goto(url or URL, wait_until="load", timeout=60000)
    if kw.get("java_script_enabled", True):
        page.evaluate(WALK)
        for waited, wanted in ((ORBIT, True), (READ, "data" not in stop)):
            if wanted:
                try:
                    page.wait_for_function(waited, timeout=15000)
                except Exception:
                    pass
        page.evaluate(WALK)
    page.wait_for_timeout(400)
    return ctx, page


ANSWERED = {}


def answers(address):
    """Whether an address of the site answers (asked once)."""
    if address not in ANSWERED:
        try:
            req = urllib.request.Request(address, headers={"User-Agent": UA})
            ANSWERED[address] = urllib.request.urlopen(req, timeout=30).status == 200
        except Exception:
            ANSWERED[address] = False
    return ANSWERED[address]


def markup():
    """What is written in the block's markup: what a visitor without scripts gets."""
    html = BLOCK.read_text(encoding="utf-8") if LOCAL else urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8")
    return {"sats": int(re.search(r'id="ha-sats">(\d+)<', html).group(1)),
            "rows": [tuple(r) for r in re.findall(r'<a class="ha-set" href="([^"]+)">.*?<small>(.*?)</small><b>(.*?)</b>', html)]}


def check(br, bname):
    print(f"\n{bname}  {URL}", flush=True)
    wrote = markup()

    # ---- the page as a visitor gets it ----
    ctx, page = open_page(br)
    site = page.evaluate(DATA)
    s = page.evaluate(SHOWN)
    print("  the page")
    ok("one <h1>, the block is on", s["h1"] == 1 and s["ready"] == "1", str((s["h1"], s["ready"])))
    ok("nothing of the old page is left beside the block", not s["old"] and s["after"] in ("", "SCRIPT"), str((s["old"], s["after"])))
    ok("the panel with the globe comes first and holds the page's title, then the lab, then its research", s["order"] == ["ha-orbit", "ha-mission", "ha-research"] and s["title"] and 70 <= s["first"] <= 110, str((s["order"], s["title"], s["first"])))
    ok("no photograph of the lab, no counts", s["photos"] == 0 and s["counts"] == 0, str((s["photos"], s["counts"])))
    ok("no script error", not page.errors, str(page.errors[:2]))
    if LOCAL:
        text = BLOCK.read_text(encoding="utf-8")
        ok(f"the block fits a Code Embed ({len(text)} of 50000 characters), ends with its script, and is plain ASCII",
           len(text) <= 50000 and text.rstrip().endswith("</script>") and text.count("<script") == 1 and 'id="hb-about"' in text and text.isascii(), str(len(text)))

    print("  the datasets")
    want = [{k: c[k] for k in ("href", "name", "kind", "pic")} for c in site["sets"]]
    ok(f"the Data page's cards in its order: name, kind, picture, address ({len(want)})", s["live"] == "sets" and s["sets"] == want and len(want) > 0, str((s["live"], [x for x in zip(s["sets"], want) if x[0] != x[1]][:1])))
    ok("each address opens its dataset on the Data page", all(c["there"] for c in site["sets"]), str([c["href"] for c in site["sets"] if not c["there"]]))
    if wrote["rows"] != [(c["href"], c["kind"], c["name"]) for c in site["sets"]]:
        note("the rows written in the markup are no longer the Data page's (they are what a visitor without scripts sees)")

    print("  the field site")
    ok("the ground network and the flights as the Data page tells them", all(t in s["views"] and t in site["cvs"] for t in SITE),
       str([t for t in SITE if t not in s["views"] or t not in site["cvs"]]))

    print("  the globe")
    page.evaluate("document.querySelector('#ha-stage').scrollIntoView({ block: 'center' })")
    page.wait_for_timeout(1200)
    g = page.evaluate(GLOBE)
    ok("drawn in its place, the picture put away", g["on"] == "on" and any(c["ink"] > 50 and c["cw"] > 200 for c in g["cv"]) and not s["pic"] and s["now"], str((g["on"], g["cv"], s["pic"], s["now"])))
    ok(f"as many satellites as the block names ({s['sats']}), and the markup says the same ({wrote['sats']})", g["total"] == g["shown"] == s["sats"] == wrote["sats"] and (g["drawn"] or 0) > 0, str((g["total"], g["shown"], g["drawn"], s["sats"], wrote["sats"])))
    page.click("#ha-stage .ho-chip >> nth=1")
    page.wait_for_timeout(300)
    off = page.evaluate(GLOBE)
    page.click("#ha-stage .ho-chip >> nth=1")
    page.wait_for_timeout(300)
    on = page.evaluate(GLOBE)
    ok(f"a family can be put off and on ({g['shown']}, {off['shown']}, {on['shown']})", len(g["chips"]) == 4 and 0 < off["shown"] < g["shown"] and on["shown"] == g["shown"], str((g["chips"], off["shown"], on["shown"])))
    page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(900)
    away = page.evaluate(GLOBE)
    page.wait_for_timeout(900)
    later = page.evaluate(GLOBE)
    ok("it stands still while it is off screen", away["running"] is False and later["frames"] == away["frames"], str((away["running"], away["frames"], later["frames"])))

    print("  the links")
    bad = [href for href in s["links"] if not href.startswith("mailto:") and not answers(href if href.startswith("http") else "https://hydroai.net" + href.split("#")[0])]
    ok(f"every address in the block answers ({len(s['links'])})", not bad, str(bad))
    ok("every picture has arrived", not s["broken"], str(s["broken"][:2]))
    ctx.close()

    # ---- falling back ----
    print("  falling back")
    ctx, page = open_page(br, java_script_enabled=False)
    f = page.evaluate(SHOWN)
    ok("without scripts: the page whole, with the markup's rows and the picture in the globe's place",
       [(x["href"], x["kind"], x["name"]) for x in f["sets"]] == wrote["rows"] and f["faint"] == 0 and f["pic"] and not f["now"] and f["sats"] == wrote["sats"] and f["words"] > 3000,
       str({k: f[k] for k in ("faint", "pic", "now", "sats", "words")}))
    ctx.close()
    ctx, page = open_page(br, stop=("data",))
    page.wait_for_timeout(1200)
    f = page.evaluate(SHOWN)
    ok("when the Data page cannot be read: the markup's rows, and no error", f["live"] == "" and [(x["href"], x["kind"], x["name"]) for x in f["sets"]] == wrote["rows"] and f["faint"] == 0 and not page.errors, str((f["live"], f["faint"], page.errors[:2])))
    ctx.close()
    for what, stop in (("the globe's file does not arrive", ("orbit-v1.js",)), ("its library does not arrive", ("orbit-lib-v1.js",)), ("the land does not arrive", ("orbit-land-v1.json",)), ("its orbits cannot be had", ("orbit-tle.json", "celestrak.org"))):
        ctx, page = open_page(br, stop=stop)
        page.wait_for_timeout(1200)
        f = page.evaluate(SHOWN)
        ok(f"when {what}: the picture in its place, nothing of the globe left, no error", f["orbit"] == "off" and f["pic"] and not f["now"] and f["canvases"] == 0 and not page.errors and f["sats"] == wrote["sats"], str((f["orbit"], f["pic"], f["now"], f["canvases"], page.errors[:2])))
        ctx.close()
    ctx, page = open_page(br, reduced_motion="reduce")
    f = page.evaluate(SHOWN)
    ok("with reduced motion everything is simply there", not f["anim"] and f["faint"] == 0 and f["orbit"] == "on", str((f["anim"], f["faint"], f["orbit"])))
    ctx.close()

    # ---- the Data page changed ----
    if not a.quick:
        print("  changed pages")
        card = re.compile(r'<a class="hd-card" href="#wq">.*?</a>', re.S)

        def sixth(html):
            m = card.search(html)
            new = m.group(0).replace('href="#wq"', 'href="#new-one"').replace("Inland Water Quality of South Korea", "A dataset of tomorrow").replace("Water quality", "Snow")
            return html[:m.end()] + new + html[m.end():]

        ctx, page = open_page(br, edit=sixth)
        f = page.evaluate(SHOWN)
        ok("a sixth dataset on the Data page: a sixth row", len(f["sets"]) == len(site["sets"]) + 1 and f["sets"][-1]["name"] == "A dataset of tomorrow" and f["sets"][-1]["kind"] == "Snow" and f["sets"][-1]["href"] == "/data#new-one", str(f["sets"][-1:]))
        ctx.close()
        ctx, page = open_page(br, edit=lambda html: card.sub("", html, count=1))
        f = page.evaluate(SHOWN)
        ok("one fewer: its row is gone", len(f["sets"]) == len(site["sets"]) - 1 and all(x["href"] != "/data#wq" for x in f["sets"]), str(len(f["sets"])))
        ctx.close()
        ctx, page = open_page(br, edit=lambda html: re.sub(r'(<a class="hd-card" href="#et">.*?)<video[^>]*></video>', r"\1", html, count=1, flags=re.S))
        f = page.evaluate(SHOWN)
        ok("a card without a picture: its row without one, the others as they were", [x["pic"] for x in f["sets"]] == [("" if c["href"] == "/data#et" else c["pic"]) for c in site["sets"]] and not f["broken"], str([x["pic"][-14:] for x in f["sets"]]))
        ctx.close()

    # ---- the sizes ----
    print("  the sizes")
    for w, h in (SIZES if not a.quick else [(2048, 970), (1440, 900), (390, 844)]):
        ctx, page = open_page(br, w=w, h=h)
        page.mouse.move(1, 1)
        f = page.evaluate(FIT)
        two, steps = (2 if w >= 900 else 1), (4 if w >= 1100 else 2 if w >= 560 else 1)
        good = (f["scrollW"] <= f["W"] and not f["over"] and not f["cut"] and f["faint"] == 0 and abs(f["left"] - f["right"]) <= 1 and f["wrap"] <= 1348 and f["orbit"] == "on"
                and f["mission"] == (2 if w >= 1100 else 1) and f["axes"] == two and f["steps"] == steps and f["cards"] == two and f["end"] == (2 if w >= 1100 else 1) and f["narrow"] >= 200 and 240 <= f["stage"] <= 640)
        ok(f"{w} x {h}: fits, centred, {two} axes and {steps} steps abreast, the globe drawn, everything there", good, str(f))
        ok(f"{w} x {h}: no script error", not page.errors, str(page.errors[:2]))
        if w < 1100:
            after = page.evaluate(KICKER)
            hold = br.new_context(viewport={"width": w, "height": h})
            held = hold.new_page()
            waiting = []
            held.route(lambda u: "orbit-v1.js" in u, lambda route: waiting.append(route))   # not answered yet: the globe stays on its way
            held.goto(URL, wait_until="domcontentloaded", timeout=60000)      # not "load": the held script keeps it from coming
            held.wait_for_function("() => document.querySelector('#ha-stage').getAttribute('data-orbit') === 'wait'", timeout=15000)
            held.wait_for_timeout(1500)                                         # the site's fonts and styles in place
            before = held.evaluate(KICKER)
            ok(f"{w} x {h}: the text under the globe stays where it is when the globe arrives ({before} px, then {after} px)", abs(after - before) <= 45, str((before, after)))
            for route in waiting:                                               # answered now, so that nothing is left hanging
                route.abort()
            hold.close()
        if a.shots:
            Path(a.shots).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}.png"), full_page=True)
        ctx.close()


with sync_playwright() as p:
    for bname in a.browsers.split(","):
        br = getattr(p, bname).launch()
        try:
            check(br, bname)
        finally:
            br.close()
print(f"\n{FAILS} failed")
sys.exit(min(FAILS, 100))
