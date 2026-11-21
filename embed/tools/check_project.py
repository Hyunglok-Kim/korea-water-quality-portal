#!/usr/bin/env python3
"""check_project.py [URL ...] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the project pages' block, checked.

    python embed/tools/check_project.py                                   # every page of the local preview (project_preview.py, port 8816)
    python embed/tools/check_project.py https://hydroai.net/project/SLUG  # live pages, once the block is on the site

Without addresses it takes every project the preview lists, and two projects that are on the site already
(so that the block is also tried on text that was not written with it in mind).

What it looks at on each page, in each browser:
  the page      one <h1>, the page's title; the block is on and the page's own sections are not shown; no script
                error; nothing wider than the window
  the words     every word of the page's own text (title, text, captions, list items) is in the block, and the block
                adds nothing to it; the headings "At a glance" and "Links" give tiles and buttons and are not shown
                themselves, "Status" gives the mark by the name, and "Contact the lab" stands for the page's button
  the figures   every picture of the text is shown once, in order, and arrives; the first is large under the title
  enlarged      a click enlarges a figure; arrows and keys step; Escape and Close close; the page behind stays put
  whose it is   everyone whose card on the People page links here is named, with a link to their card
  other         the cards of other projects: none is this page, each leads to a project
and once per browser, on the first page:
  falling back  without scripts, without <dialog>, and with the text taken away: the page as it was
  the sizes     thirteen window sizes from 2048 px down to a 320 px phone: nothing wider than the window, the
                title whole, a figure and an enlarged figure inside the window
  motion        with reduced motion everything is simply there
The exit status is the number of failures. Needs playwright with the three browsers installed.
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("urls", nargs="*")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures")
ap.add_argument("--quick", action="store_true", help="three sizes instead of thirteen, and no falling back")
a = ap.parse_args()
PREVIEW = "http://127.0.0.1:8816"
OLD = ["building-koreas-first-nasa-core-validation-site-for-advanced-earth-observation-satellites",
       "enhancing-earth-science-predictions-through-advanced-data-assimilation-techniques"]
SIZES = [(2048, 970), (1680, 1050), (1440, 900), (1280, 720), (1200, 800), (1100, 700), (1024, 768), (960, 600), (834, 1194), (768, 1024), (600, 900), (390, 844), (320, 568)]
FAILS = 0
ZW = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF))

if a.urls:
    URLS = a.urls
else:
    index = urllib.request.urlopen(PREVIEW + "/", timeout=20).read().decode("utf-8")
    URLS = [PREVIEW + h for h in re.findall(r'href="(/project/[^"]+)"', index)] + [PREVIEW + "/project/" + s for s in OLD]

# the page's own content, read without the block's help
OWN = r"""([ZW]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const words = e => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  const old = document.querySelector('.section.project-detail'), post = document.querySelector('.section.project-post-content');
  if (!old || !post) return null;
  const rich = post.querySelector('.w-richtext'), special = /^(at a glance|key facts|facts|in brief|links|read more|related links|resources)$/i;
  /* by design the headings of the tiles and of the buttons are not shown, and "Status" gives its value to the mark by the name */
  const copy = rich.cloneNode(true);
  [...copy.children].forEach(n => { if (/^H[1-6]$/.test(n.tagName) && special.test(clean(n.textContent))) n.remove(); });
  copy.querySelectorAll('li > strong:first-child, li > b:first-child').forEach(s => { if (/^status:?$/i.test(clean(s.textContent))) s.remove(); });
  const parts = [...copy.children].map(words).filter(Boolean);
  return { title: clean(old.querySelector('h1').textContent), date: clean((old.querySelector('.text-medium') || {}).textContent), text: parts.join(' '),
    pics: [...rich.querySelectorAll('img')].map(i => i.getAttribute('src')), hidden: [old, post].every(e => getComputedStyle(e).display === 'none'),
    list: post.nextElementSibling && post.nextElementSibling.querySelector('.w-dyn-item') ? getComputedStyle(post.nextElementSibling).display : 'none',
    back: (/url\((['"]?)(.*?)\1\)/.exec(old.style.backgroundImage || '') || [])[2] || '' };
}"""
NEW = r"""([ZW]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const r = document.getElementById('hj-project'), q = s => r.querySelector('[data-hj="' + s + '"]');
  const words = e => { if (!e) return ''; const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  return { state: r.getAttribute('data-state'), people: r.getAttribute('data-people'), h1: [...document.querySelectorAll('h1')].filter(h => h.offsetParent).map(h => clean(h.textContent)),
    title: clean(q('title').textContent), date: clean((r.querySelector('.hj-date') || {}).textContent),
    text: [q('lede'), r.querySelector('.hj-chip'), q('hero'), q('facts'), q('body')].map(words).concat([...q('links').querySelectorAll('.hj-pill')].filter(p => clean(p.textContent) !== 'Contact the lab').map(words)).join(' '),
    pics: [...r.querySelectorAll('.hj-shot img')].map(i => i.getAttribute('src')), hero: (q('hero').querySelector('img') || {}).src ? q('hero').querySelector('img').getAttribute('src') : '',
    loaded: [...r.querySelectorAll('.hj-shot img, .hj-thumb img, .hj-face img')].map(i => i.complete && i.naturalWidth > 0),
    persons: [...r.querySelectorAll('.hj-person')].map(p => [clean(p.querySelector('.hj-who').textContent), p.getAttribute('href')]), kind: q('kind').hidden ? '' : clean(q('kind').textContent),
    cards: [...r.querySelectorAll('.hj-card')].map(c => c.getAttribute('href')), contact: [...r.querySelectorAll('.hj-pill')].map(p => p.getAttribute('href')),
    wide: document.documentElement.scrollWidth - innerWidth };
}"""
PEOPLE = r"""async (self) => {
  const t = await (await fetch('/people')).text(), d = new DOMParser().parseFromString(t, 'text/html'), out = [];
  d.querySelectorAll('.people-card').forEach(c => {
    const a = [...c.querySelectorAll('.w-richtext a[href]')].find(x => /main\s+pro\w*\s+link/i.test(x.textContent));
    if (a && new URL(a.getAttribute('href'), location.href).pathname.replace(/\/+$/, '') === self) out.push((c.querySelector('.name h2') || c.querySelector('h2')).textContent.replace(/\s+/g, ' ').trim());
  });
  return out;
}"""


def check(ok, what, detail=""):
    global FAILS
    if not ok:
        FAILS += 1
    print(f"    {'ok  ' if ok else 'FAIL'}  {what}" + (f"   [{detail}]" if detail and not ok else ""), flush=True)
    return ok


def bag(s):
    return sorted(re.findall(r"[^\W_]+", s.lower()))


def settle(pg):
    pg.wait_for_function("document.getElementById('hj-project') && ['on', 'off'].includes(document.getElementById('hj-project').getAttribute('data-state'))", timeout=30000)
    pg.wait_for_function("document.getElementById('hj-project').hasAttribute('data-people') || document.getElementById('hj-project').getAttribute('data-state') === 'off'", timeout=30000)
    pg.evaluate("""async () => { const H = () => document.documentElement.scrollHeight; for (let y = 0; y < H(); y += Math.round(innerHeight * 0.7)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 110)); } scrollTo(0, 0); await new Promise(r => setTimeout(r, 900)); }""")
    try:
        pg.wait_for_function("[...document.querySelectorAll('#hj-project .hj-shot img, #hj-project .hj-thumb img')].every(i => i.complete)", timeout=20000)
    except Exception:
        pass


def one_page(ctx, url, name):
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url, wait_until="load", timeout=90000)
    settle(pg)
    own, new = pg.evaluate(OWN, [ZW]), pg.evaluate(NEW, [ZW])
    print(f"  {name}", flush=True)
    check(new["state"] == "on" and own and own["hidden"] and own["list"] == "none", "the block is on and the page's own sections are not shown", f"{new['state']} {own and own['hidden']}")
    check(new["h1"] == [own["title"]] and new["title"] == own["title"] and new["date"] == own["date"], "one <h1>, the page's title, and its date", f"{new['h1']} | {new['date']!r} vs {own['date']!r}")
    check(own["title"].lower() in pg.title().lower(), "the browser's tab carries the title", pg.title())
    # the words: everything the page says is in the block, and the block adds nothing
    o, n = bag(own["text"]), bag(new["text"])
    missing, extra = list(o), []
    for w in n:
        if w in missing:
            missing.remove(w)
        else:
            extra.append(w)
    check(not missing, "every word of the page's text is in the block", " ".join(missing[:14]))
    check(not extra, "the block adds no word to the text", " ".join(extra[:14]))
    pics = own["pics"] or ([own["back"]] if own["back"] else [])
    check(new["pics"] == pics, f"every picture of the text once and in order ({len(pics)})", f"{len(new['pics'])} of {len(pics)}")
    check(not pics or new["hero"] == pics[0], "the first picture large under the title")
    check(all(new["loaded"]), "every picture arrives", f"{new['loaded'].count(False)} did not")
    check(new["wide"] <= 0 and not errs, "nothing wider than the window, no script error", f"{new['wide']} {errs[:2]}")
    # whose project it is
    path = re.sub(r"^https?://[^/]+", "", url).split("?")[0].rstrip("/")
    who = pg.evaluate(PEOPLE, path)
    check([p[0] for p in new["persons"]] == who and all(p[1].startswith("/people#") for p in new["persons"]) and (new["kind"] == "Main project") == bool(who),
          f"whoever's card links here is named ({', '.join(who) or 'nobody'})", f"{new['persons']} vs {who} | {new['kind']!r}")
    check(path not in new["cards"] and all(c.startswith("/project/") for c in new["cards"]) and len(set(new["cards"])) == len(new["cards"]) and 0 < len(new["cards"]) <= 6,
          f"other projects: {len(new['cards'])} cards, none of them this page", str(new["cards"][:3]))
    # a figure, enlarged
    if pics:
        y0 = pg.evaluate("() => { const b = document.querySelectorAll('#hj-project .hj-shot'); const e = b[b.length - 1]; e.scrollIntoView({ block: 'center' }); return scrollY; }")
        pg.wait_for_timeout(200)
        y0 = pg.evaluate("scrollY")
        pg.evaluate("() => { const b = document.querySelectorAll('#hj-project .hj-shot'); b[b.length - 1].click(); }")
        pg.wait_for_function("document.querySelector('.hj-lb').open && document.querySelector('.hj-lb img').complete && document.querySelector('.hj-lb img').naturalWidth > 0", timeout=20000)
        st = pg.evaluate("() => { const d = document.querySelector('.hj-lb'), i = d.querySelector('img').getBoundingClientRect(); return { n: document.querySelector('[data-hj=lb-n]').textContent, src: d.querySelector('img').getAttribute('src'), inside: i.top >= 0 && i.left >= 0 && i.right <= innerWidth + 1 && i.bottom <= innerHeight + 1, lock: document.documentElement.classList.contains('hj-lock'), full: document.querySelector('[data-hj=lb-full]').getAttribute('href') }; }")
        check(st["src"] == pics[-1] and st["inside"] and st["lock"] and st["full"] == pics[-1], "a click enlarges the figure, inside the window", str(st))
        if len(pics) > 1:
            check(st["n"] == f"{len(pics)} / {len(pics)}", "it says which figure of how many", st["n"])
            pg.keyboard.press("ArrowRight")
            pg.wait_for_timeout(250)
            first = pg.evaluate("document.querySelector('.hj-lb img').getAttribute('src')")
            pg.evaluate("document.querySelector('.hj-lb [data-step=\"-1\"]').click()")
            pg.wait_for_timeout(250)
            check(first == pics[0] and pg.evaluate("document.querySelector('.hj-lb img').getAttribute('src')") == pics[-1], "the arrow key and the arrow step through the figures, round the end")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(250)
        closed = pg.evaluate("() => [document.querySelector('.hj-lb').open, document.documentElement.classList.contains('hj-lock'), scrollY]")
        check(closed[0] is False and closed[1] is False and abs(closed[2] - y0) < 3, "Escape closes it, and the page is where it was", str(closed))
    pg.close()


def falling_back(b, url):
    print("  falling back", flush=True)
    for what, kw, init, route in (("without scripts", {"java_script_enabled": False}, None, None),
                                  ("without <dialog>", {}, "delete window.HTMLDialogElement;", None),
                                  ("with the text taken away", {}, None, True)):
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, **kw)
        if init:
            ctx.add_init_script(init)
        pg = ctx.new_page()
        if route:
            def handle(r):
                resp = r.fetch()
                body = resp.text()
                i = body.index('<div class="rich-text-block w-richtext">')
                r.fulfill(response=resp, body=body[:i] + '<div class="rich-text-block">' + body[i + len('<div class="rich-text-block w-richtext">'):])
            pg.route(url, handle)
        pg.goto(url, wait_until="load", timeout=90000)
        pg.wait_for_timeout(900)
        st = pg.evaluate("() => { const r = document.getElementById('hj-project'), o = document.querySelector('.section.project-detail'), p = document.querySelector('.section.project-post-content'); return [getComputedStyle(r).display, getComputedStyle(o).display, getComputedStyle(p).display, document.documentElement.classList.contains('hj-js')]; }")
        check(st[0] == "none" and st[1] != "none" and st[2] != "none" and not st[3], f"{what}: the page as it was", str(st))
        ctx.close()


def sizes(b, url, name, shots):
    print("  the sizes", flush=True)
    for w, h in (SIZES if not a.quick else [(2048, 970), (1440, 900), (390, 844)]):
        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url, wait_until="load", timeout=90000)
        settle(pg)
        st = pg.evaluate("""() => { const r = document.getElementById('hj-project'), t = r.querySelector('.hj-title'), wrap = r.querySelector('.hj-wrap').getBoundingClientRect();
          const cut = [...r.querySelectorAll('.hj-title, .hj-lede, .hj-h, .hj-p, .hj-cap, .hj-fact dd, .hj-cn, .hj-who')].filter(e => e.scrollWidth > e.clientWidth + 1).length;
          const figs = [...r.querySelectorAll('.hj-shot')].filter(f => { const b = f.getBoundingClientRect(); return b.left < -1 || b.right > innerWidth + 1; }).length;
          return { wide: document.documentElement.scrollWidth - innerWidth, cut, figs, centred: Math.abs((wrap.left + wrap.right) / 2 - innerWidth / 2) < 1.5, title: t.getBoundingClientRect().width > 100 }; }""")
        pg.evaluate("document.querySelector('#hj-project .hj-shot').click()")
        pg.wait_for_function("document.querySelector('.hj-lb').open && document.querySelector('.hj-lb img').complete", timeout=20000)
        pg.wait_for_timeout(450)
        lb = pg.evaluate("() => { const d = document.querySelector('.hj-lb'), i = d.querySelector('img').getBoundingClientRect(), c = d.querySelector('[data-close]').getBoundingClientRect(); return i.top >= -1 && i.left >= -1 && i.right <= innerWidth + 1 && c.bottom <= innerHeight + 1 && i.height > 40; }")
        if shots:
            pg.screenshot(path=str(Path(shots) / f"{name}-{w}-enlarged.png"))
        pg.keyboard.press("Escape")
        if shots:
            pg.screenshot(path=str(Path(shots) / f"{name}-{w}.png"))
        check(st["wide"] <= 0 and st["cut"] == 0 and st["figs"] == 0 and st["centred"] and st["title"] and lb and not errs,
              f"{w} x {h}: nothing wider than the window or cut, the page centred, an enlarged figure inside the window", f"{st} lb {lb} {errs[:1]}")
        ctx.close()


with sync_playwright() as p:
    if a.shots:
        Path(a.shots).mkdir(parents=True, exist_ok=True)
    for name in a.browsers.split(","):
        print(name, flush=True)
        b = getattr(p, name).launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        for u in URLS:
            one_page(ctx, u, u.rstrip("/").split("/")[-1][:70])
        ctx.close()
        if not a.quick:
            falling_back(b, URLS[0])
        sizes(b, URLS[0], name, a.shots)
        print("  motion", flush=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.goto(URLS[0], wait_until="load", timeout=90000)
        pg.wait_for_timeout(1200)
        check(pg.evaluate("() => [...document.querySelectorAll('#hj-project .hj-sec, #hj-project .hj-card')].every(e => getComputedStyle(e).opacity === '1') && !document.getElementById('hj-project').classList.contains('hj-anim')"),
              "with reduced motion everything is simply there")
        ctx.close()
        b.close()
print(f"\n{FAILS} failed", flush=True)
sys.exit(min(FAILS, 100))
