#!/usr/bin/env python3
"""check_publications.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the Publications page's block, checked.

    python embed/tools/check_publications.py                                   # the local preview (publications_preview.py, port 8817)
    python embed/tools/check_publications.py https://hydroai.net/publication   # the live page, once the block is on it

What it looks at, in each browser:
  the page       one <h1>; the block is on and the page's own section is not shown; the "Contact me" block stays;
                 no script error; nothing wider than the window; the page's quotation with who said it
  the entries    every entry of the page's three lists (the journal papers of every page of their list, read here
                 by following the page's own "Next") is shown once, in its list and in the page's order: title,
                 journal, month and year (the whole date on pointing at it), authors, state; every word of a
                 summary is in the opened row and nothing is added; a link that is an address is kept and opens a
                 new tab, one that is "TBD" is left out; every picture is the page's; a journal "-" is left out
  the lists      a chip for each tab with the tab's label, without numbers; a chip shows its list and the address
                 follows it; an address with a list opens it
  the years      the years of the list beside it, in order; a click leads to the year; the year being read is
                 marked; the first year leads back to the search field; a list without dates has no years
  a paper        a click on the row and the arrow open the summary and the address follows; a second click closes;
                 selecting words opens nothing; the link does not open the row; the figure opens full size, arrows
                 and keys step through the figures, Escape and a click beside it close it; an address with a paper
                 opens it, also a paper of a page that arrives later; an address with a year leads to it
  the search     the three lists are searched at once and the chips count what was found; the words are marked;
                 nothing found in this list: said so, with the lists that have something; Escape, the cross and "/"
  the pages      the following pages are asked for once each; while they are on their way the first page's rows
                 are shown; a page that cannot be fetched: said so, and "Try again" brings the rest; the page
                 opened on a later page of the list shows the whole list; (local) every paper on one page: nothing asked for
  falling back   without scripts, in a browser without <dialog>, and when nothing can be read: the page as it was
  other places   the block as the last element instead of the first (local preview only)
  changed pages  a paper without picture, a picture that cannot be fetched, a paper with neither summary nor
                 picture, a link filled in, a fourth tab, an emptied tab, no quotation, a mark explained under a list
  the sizes      thirteen window sizes from 2048 px down to a 320 px phone: nothing wider than the window, no word
                 cut, the page centred, the years beside the list or in a row above it and in view while reading,
                 an opened paper and an enlarged figure inside the window
The exit status is the number of failures. Needs playwright with the three browsers installed.
"""
import argparse
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8817/publication")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures of every size")
ap.add_argument("--quick", action="store_true", help="leave out the changed pages and all sizes but three")
a = ap.parse_args()
URL = a.url
LOCAL = "127.0.0.1" in URL or "localhost" in URL
FAILS = 0
SIZES = [(2048, 970), (1680, 1050), (1440, 900), (1280, 720), (1200, 800), (1100, 700), (1024, 768), (960, 600), (834, 1194), (768, 1024), (600, 900), (390, 844), (320, 568)]
ZW = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF))
MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
UI = {"paper": "Paper", "scholar": "Google Scholar", "soon": "Link soon"}

# the page's own content, read without the block's help: the tabs, their entries, and the following pages by the page's own "Next"
OLD = r"""async ([ZW]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const pieces = e => { const w = e.ownerDocument.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  const read = doc => {
    const tabs = [...doc.querySelectorAll('.w-tabs')].find(t => t.querySelector('.w-tab-pane'));
    if (!tabs) return null;
    const panes = [...tabs.querySelectorAll('.w-tab-pane')];
    return { tabs, lists: [...tabs.querySelectorAll('.w-tab-link')].map(a => {
      const pane = panes.find(p => p.getAttribute('data-w-tab') === a.getAttribute('data-w-tab'));
      const next = pane.querySelector('a.w-pagination-next'), prev = pane.querySelector('a.w-pagination-previous');
      return { label: clean(a.textContent), name: a.getAttribute('data-w-tab'), next: next ? next.getAttribute('href') : '', prev: prev ? prev.getAttribute('href') : '',
        note: clean((pane.querySelector('.text-block-7') || {}).textContent),
        items: [...pane.querySelectorAll('.w-dyn-item')].map(it => {
          const q = s => clean((it.querySelector(s) || {}).textContent), img = it.querySelector('img'), link = it.querySelector('a[href]'), rich = it.querySelector('.w-richtext'), h = it.querySelector('h3');
          if (it.querySelector('.publications-card')) return { paper: true, title: q('h3'), venue: q('h4'), tail: q('.publication_date'), href: link ? link.getAttribute('href').trim() : '',
            img: img ? img.getAttribute('src') : '', srcset: img ? img.getAttribute('srcset') || '' : '', text: rich ? pieces(rich) : '', links: rich ? [...rich.querySelectorAll('a[href]')].map(x => x.getAttribute('href')) : [] };
          const n = h && h.nextElementSibling;
          return { paper: false, title: q('h3'), who: n && !n.querySelector('.text-block-4, .text-block-5') ? clean(n.textContent) : '', venue: q('.text-block-4'), tail: q('.text-block-5') };
        }).filter(d => d.title) };
    }) };
  };
  const me = read(document);
  if (!me) return null;
  for (const l of me.lists) {
    let next = l.next, guard = 0;
    l.pages = 1;
    if (l.prev) { l.items = []; next = l.prev.replace(/\d+$/, '1'); l.pages = 0; }      // opened on a later page of this list
    while (next && guard++ < 80) {
      const doc = new DOMParser().parseFromString(await (await fetch(location.pathname + next)).text(), 'text/html');
      const got = read(doc), m = got && got.lists.find(x => x.name === l.name);
      if (!m || !m.items.length) break;
      l.items.push(...m.items); next = m.next; l.pages++;
    }
  }
  const sec = me.tabs.closest('.section'), head = [...sec.querySelectorAll('p')].find(p => !p.closest('.w-tabs') && clean(p.textContent));
  return { lists: me.lists.map(l => ({ label: l.label, name: l.name, note: l.note, items: l.items, pages: l.pages })), quote: head ? pieces(head) : '',
    shown: getComputedStyle(sec).display !== 'none', cta: document.querySelectorAll('.cta-block').length };
}"""

# what the block shows
NEW = r"""([ZW]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const pieces = e => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  const r = document.getElementById('hb-pubs');
  if (!r) return null;
  const seen = e => !!(e && e.getClientRects().length), txt = (e, s) => clean((e.querySelector(s) || {}).textContent);
  const row = li => ({ id: li.id, hidden: li.hidden, paper: li.classList.contains('hb-paper'), talk: li.classList.contains('hb-talk'), open: li.classList.contains('is-open'), plain: li.classList.contains('is-plain'),
    title: txt(li, '.hb-t'), venue: txt(li, '.hb-venue'), who: txt(li, '.hb-who'), tag: txt(li, '.hb-tag'), tone: (li.querySelector('.hb-tag') || { className: '' }).className.replace('hb-tag', '').trim(),
    when: txt(li, 'time'), whole: (li.querySelector('time') || { title: '' }).title, iso: li.querySelector('time') ? li.querySelector('time').getAttribute('datetime') || '' : '',
    out: (o => o ? { tag: o.tagName, text: clean(o.textContent), href: o.getAttribute('href') || '', target: o.target || '', rel: o.rel || '', none: o.classList.contains('is-none') } : null)(li.querySelector('.hb-out')),
    img: (i => i ? i.getAttribute('src') : '')(li.querySelector('.hb-fig:not([hidden]) img')),
    btn: (b => b ? { hidden: b.hidden, exp: b.getAttribute('aria-expanded'), ctl: b.getAttribute('aria-controls'), label: b.getAttribute('aria-label') } : null)(li.querySelector('.hb-chev')),
    more: (m => m ? { id: m.id, hidden: m.hidden, text: pieces(m), links: [...m.querySelectorAll('a[href]')].map(x => x.getAttribute('href')) } : null)(li.querySelector('.hb-more')),
    year: (y => y ? y.getAttribute('data-y') || '' : '')(li.closest('.hb-yr')), meet: (m => m && m.querySelector('.hb-mh') ? clean(m.querySelector('.hb-mh').textContent) : '')(li.closest('.hb-meet')),
    level: li.querySelector('.hb-t').tagName, marks: [...li.querySelectorAll('mark')].map(m => m.textContent) });
  return { state: r.getAttribute('data-state'), seen: seen(r), js: document.documentElement.classList.contains('hb-js'), lock: document.documentElement.classList.contains('hb-lock'),
    h1: [...document.querySelectorAll('h1')].filter(seen).map(h => clean(h.textContent)), hash: location.hash, y: Math.round(scrollY),
    quote: pieces(r.querySelector('.hb-motto')), say: txt(r, '.hb-say'), by: txt(r, '.hb-by'),
    chips: [...r.querySelectorAll('.hb-nav .hb-chip')].map(c => ({ g: c.getAttribute('data-g'), text: clean(c.firstChild.textContent), n: clean(c.querySelector('.hb-n').textContent), cur: c.getAttribute('aria-current') === 'true', href: c.getAttribute('href') })),
    navSeen: seen(r.querySelector('.hb-nav')),
    lists: [...r.querySelectorAll('.hb-list')].map(l => ({ key: l.getAttribute('data-g'), hidden: l.hidden, rows: [...l.querySelectorAll('.hb-row')].map(row),
      years: [...l.querySelectorAll('.hb-yr')].map(y => ({ id: y.id, y: y.getAttribute('data-y') || '', hidden: y.hidden, head: txt(y, '.hb-yh') })),
      wait: (w => ({ seen: seen(w), text: clean(w.textContent), lost: w.classList.contains('is-lost') }))(l.querySelector('.hb-wait')), note: txt(l, '.hb-note') })),
    years: [...r.querySelectorAll('.hb-years .hb-year')].map(y => ({ y: clean(y.textContent), href: y.getAttribute('href'), cur: y.getAttribute('aria-current') === 'true' })),
    flat: r.querySelector('.hb-body').classList.contains('is-flat'), rail: seen(r.querySelector('.hb-years')),
    status: clean(r.querySelector('.hb-status').firstChild ? r.querySelector('.hb-status').firstChild.textContent : ''), none: r.querySelector('.hb-status').classList.contains('is-none'),
    also: [...r.querySelectorAll('.hb-also .hb-chip')].map(c => ({ g: c.getAttribute('data-g'), text: clean(c.firstChild.textContent), n: clean(c.querySelector('.hb-n').textContent) })),
    q: r.querySelector('#hb-q').value, clear: !r.querySelector('.hb-clear').hidden, anim: r.classList.contains('hb-anim'),
    lb: (d => ({ open: d.open, n: clean(d.querySelector('[data-hb=n]').textContent), cap: clean(d.querySelector('[data-hb=cap]').textContent), src: d.querySelector('img').getAttribute('src') || '' }))(r.querySelector('[data-hb=figure]')),
    focus: document.activeElement ? (document.activeElement.id || document.activeElement.className || document.activeElement.tagName) : '' };
}"""

# measures at one window size
FIT = r"""() => {
  const W = document.documentElement.clientWidth, H = innerHeight, r = document.getElementById('hb-pubs');
  const box = e => e.getBoundingClientRect(), name = e => (e.className && e.className.baseVal === undefined ? e.className : e.tagName) + ':' + e.textContent.trim().slice(0, 24);
  const wrap = box(r.querySelector('.hb-wrap')), years = r.querySelector('.hb-years'), yb = box(years), list = [...r.querySelectorAll('.hb-list')].find(l => !l.hidden), lbx = box(list);
  const dlg = r.querySelector('dialog'), inner = dlg.open && dlg.querySelector('img'), open = r.querySelector('.hb-paper.is-open');
  return { W, scrollW: document.documentElement.scrollWidth,
    over: [...r.querySelectorAll('*')].filter(e => { const b = box(e); return b.width > 0 && !e.closest('dialog') && !e.closest('.hb-years') && (b.right > W + 0.5 || b.left < -0.5); }).map(name).slice(0, 4),
    cut: [...r.querySelectorAll('.hb-title, .hb-kicker, .hb-chip, .hb-yh, .hb-t, .hb-out, .hb-tag, .hb-year, .hb-mh')].filter(e => e.getClientRects().length && e.scrollWidth > e.clientWidth + 1).map(name).slice(0, 4),
    left: Math.round(wrap.left * 10) / 10, right: Math.round((W - wrap.right) * 10) / 10, wrap: Math.round(wrap.width),
    years: { seen: years.getClientRects().length > 0, top: Math.round(yb.top), left: Math.round(yb.left), right: Math.round(yb.right), w: Math.round(yb.width), h: Math.round(yb.height), row: getComputedStyle(years).flexDirection === 'row', sticky: getComputedStyle(years).position },
    list: { left: Math.round(lbx.left), right: Math.round(lbx.right), w: Math.round(lbx.width) },
    small: Math.round(Math.min(...[...list.querySelectorAll('.hb-t')].filter(e => e.getClientRects().length).map(e => box(e).width))),
    open: open ? (o => ({ fig: (f => f && f.getClientRects().length ? [Math.round(box(f).left), Math.round(box(f).width), Math.round(box(f).height), Math.round(W - box(f).right)] : null)(o.querySelector('.hb-fig')), more: Math.round(box(o.querySelector('.hb-more')).width), lines: Math.round(box(o.querySelector('.hb-more')).height) }))(open) : null,
    inner: inner ? (b => ({ left: Math.round(b.left), top: Math.round(b.top), right: Math.round(W - b.right), bottom: Math.round(H - b.bottom), w: Math.round(b.width), h: Math.round(b.height), natural: inner.naturalWidth }))(box(inner)) : null,
    close: dlg.open ? (b => b.width > 20 && b.top >= 0 && b.bottom <= H && b.left >= 0 && b.right <= W)(box(dlg.querySelector('[data-close]'))) : null };
}"""

DONE = "() => { const r = document.getElementById('hb-pubs'); return !!r && r.getAttribute('data-state') !== 'wait' && ![...r.querySelectorAll('.hb-wait')].some(w => !w.hidden && !w.classList.contains('is-lost')); }"


def ok(name, cond, detail=""):
    global FAILS
    if not cond:
        FAILS += 1
    print(("    ok    " if cond else "    FAIL  ") + name + (f"   [{detail}]" if detail != "" and not cond else ""), flush=True)
    return cond


def words(s):
    return re.findall(r"\w+", (s or "").lower())


def address(href):
    """Is this an address yet? ("TBD", "#" and "https://tbd" are not.)"""
    m = re.match(r"^https?://([^/?#]+\.[a-z]{2,})(?:[/?#]|$)", href or "", re.I)
    return bool(m) and not re.match(r"^(www\.)?tbd\b", m.group(1), re.I)


def shown_date(s):
    """How a date of the page is shown: "December 1, 2026" as "Dec 2026" under the year 2026."""
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.? (?:(\d{1,2}), )?(\d{4})$", s or "")
    if m and m.group(1).lower() in MONTHS:
        iso = f"{m.group(3)}-{MONTHS.index(m.group(1).lower()) + 1:02d}" + (f"-{int(m.group(2)):02d}" if m.group(2) else "")
        return {"y": m.group(3), "text": f"{m.group(1)} {m.group(3)}", "iso": iso}
    return {"y": s if re.fullmatch(r"\d{4}", s or "") else "", "text": s or "", "iso": ""}


def venue(d):
    return "" if d["venue"] in ("-", chr(0x2013), chr(0x2014)) else d["venue"]


def is_dated(items):
    return bool(items) and sum(1 for d in items if shown_date(d["tail"])["y"]) * 2 >= len(items)


def in_order(items):
    """The order the block shows a list in: as the page has it; a list with dates by year, its talks by meeting."""
    if not is_dated(items):
        return list(items)
    out, years = [], []
    for d in items:
        y = shown_date(d["tail"])["y"] or "Undated"
        if y not in years:
            years.append(y)
    for y in years:
        mine = [d for d in items if (shown_date(d["tail"])["y"] or "Undated") == y]
        meets = []
        for d in mine:
            k = "" if d["paper"] else (venue(d), d["tail"])
            if k not in meets:
                meets.append(k)
        for k in meets:
            out += [d for d in mine if ("" if d["paper"] else (venue(d), d["tail"])) == k]
    return out


def hay(d):
    return " ".join([d["title"], venue(d), d.get("who", ""), d["tail"], d.get("text", "")]).lower()


def found(items, query):
    return [d for d in items if all(t in hay(d) for t in query.lower().split())]


def base(u):
    return u.split("#")[0].split("?")[0]


def open_page(br, url=None, w=1440, h=900, edit=None, init=None, hold=None, settle=True, **kw):
    """A page at `url`. `edit` changes the HTML of the Publications page (any page of its list) on its way to the
    browser; `hold` says what happens to the requests for the list's following pages: {"keep": True} holds them
    until page.release() is called, {"fail": {3}} lets those page numbers fail."""
    ctx = br.new_context(viewport={"width": w, "height": h}, **kw)
    if init:
        ctx.add_init_script(init)
    page = ctx.new_page()
    page.errors, page.warnings, page.asked, page.held = [], [], [], []
    page.hold = dict(hold or {})
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    page.on("console", lambda m: page.warnings.append(m.text) if m.type == "warning" else None)

    def handle(route):
        u = route.request.url
        n = re.search(r"[?&][0-9a-f]+_page=(\d+)", u)
        first = route.request.resource_type == "document"
        if n and not first:
            page.asked.append(int(n.group(1)))
            if int(n.group(1)) in page.hold.get("fail", ()):
                return route.fulfill(status=503, body="held back by the check")
            if page.hold.get("keep"):
                return page.held.append(route)
        if not edit:
            return route.continue_()
        r = route.fetch()
        try:
            body = edit(r.text())
        except Exception as e:
            ok("the page could be changed for this check", False, repr(e))
            body = r.text()
        route.fulfill(response=r, body=body)

    def release():
        page.hold = {}
        for r in page.held:
            r.continue_()
        page.held = []

    page.release = release
    page.route(lambda u: base(u) == base(URL), handle)
    page.goto(url or URL, wait_until="load", timeout=60000)
    if settle:
        done(page)
    return ctx, page


def done(page, wait=450):
    """Until the block has everything it asked for."""
    try:
        page.wait_for_function(DONE, timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(wait)


def fresh(page, url):
    """Open `url` anew (from the same page, an address that differs only after the # would not load the page again)."""
    page.goto("about:blank")
    page.goto(url, wait_until="load", timeout=60000)
    done(page)


def old(page):
    return page.evaluate(OLD, [ZW])


def new(page):
    return page.evaluate(NEW, [ZW])


def with_query(q):
    return base(URL) + "?" + q


def top_of(page, sel):
    return page.evaluate("s => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top) : null; }", sel)


def the_entries(page, o, n, label=""):
    """Every entry the page lists is shown, with everything the page says of it."""
    ol = [l for l in o["lists"] if l["items"]]
    ok(label + "the lists are the page's tabs that have an entry, in the page's order", [c["text"] for c in n["chips"]] == [l["label"] for l in ol] and len(n["lists"]) == len(ol), f'{[c["text"] for c in n["chips"]]} / {[l["label"] for l in ol]}')
    ok(label + "the chips carry no numbers", all(c["n"] == "" for c in n["chips"]), str([c["n"] for c in n["chips"]]))
    ok(label + "the first list is on show, the others are not", [l["hidden"] for l in n["lists"]] == [i > 0 for i in range(len(n["lists"]))] and [c["cur"] for c in n["chips"]] == [i == 0 for i in range(len(n["chips"]))])
    ids = [r["id"] for l in n["lists"] for r in l["rows"]]
    ok(label + "every entry has its own address", len(set(ids)) == len(ids) and all(i.startswith("hb-") and len(i) > 3 for i in ids), str(len(ids) - len(set(ids))))
    for li, l in enumerate(ol):
        if li >= len(n["lists"]):
            break
        rows, want, dated = n["lists"][li]["rows"], in_order(l["items"]), is_dated(l["items"])
        name = f'{label}{l["label"]}: '
        if not ok(name + f'every entry once, in the page\'s order ({len(want)})', [r["title"] for r in rows] == [d["title"] for d in want], f'{len(rows)} shown, {len(want)} on the page'):
            continue
        bad = {k: [] for k in "venue date year who state link picture level meeting".split()}
        for r, d in zip(rows, want):
            t, sd = d["title"][:40], shown_date(d["tail"])
            if d["paper"]:
                if r["venue"] != venue(d) or not r["paper"]:
                    bad["venue"].append(t)
                if (r["when"], r["whole"], r["iso"]) != (sd["text"], d["tail"] if sd["iso"] else "", sd["iso"]):
                    bad["date"].append(f'{t}: {r["when"]} / {r["whole"]} / {r["iso"]}')
                out = r["out"] or {}
                if address(d["href"]):
                    scholar = "scholar.google." in d["href"].lower()
                    if (out.get("tag"), out.get("href"), out.get("target"), out.get("text")) != ("A", d["href"], "_blank", UI["scholar"] if scholar else UI["paper"]) or "noopener" not in out.get("rel", ""):
                        bad["link"].append(f'{t}: {out}')
                elif out.get("tag") == "A" or out.get("text") != (UI["soon"] if d["href"] else ""):
                    bad["link"].append(f'{t}: {out}')
                if r["img"] != d["img"]:
                    bad["picture"].append(t)
                if r["level"] != "H3":
                    bad["level"].append(t)
            else:
                if r["who"] != d["who"]:
                    bad["who"].append(t)
                if dated:
                    if r["meet"] != " ".join(x for x in (venue(d), sd["text"]) if x) or r["venue"] or r["tag"] or not r["talk"]:
                        bad["meeting"].append(f'{t}: {r["meet"]}')
                    if r["level"] != "H4":
                        bad["level"].append(t)
                else:
                    if r["venue"] != venue(d):
                        bad["venue"].append(t)
                    tone = "is-a" if re.search("revis", d["tail"], re.I) else "is-b" if re.search("review|consider", d["tail"], re.I) else "is-c"
                    if r["tag"] != d["tail"] or (d["tail"] and r["tone"] != tone):
                        bad["state"].append(f'{t}: {r["tag"]} {r["tone"]}')
                    if r["level"] != "H2":
                        bad["level"].append(t)
            if r["year"] != ((sd["y"] or "Undated") if dated else ""):
                bad["year"].append(f'{t}: {r["year"]}')
        for k, v in bad.items():
            if any(d["paper"] for d in want) or k not in ("link", "picture"):
                ok(name + {"venue": "the journal as the page has it, a \"-\" left out", "date": "the month and year, with the whole date behind it", "year": "under its year" if dated else "no years in a list without dates",
                           "who": "the authors", "state": "the state as a mark, as the page words it", "link": "a link that is an address is kept and opens a new tab, one that is not is left out",
                           "picture": "the page's picture", "level": "headings in order (year, meeting, title)", "meeting": "the talks under their meeting and its month"}[k], not v, str(v[:3]))
        if dated:
            ys = []
            for d in want:
                y = shown_date(d["tail"])["y"] or "Undated"
                if y not in ys:
                    ys.append(y)
            ok(name + "its years in the page's order, each with a heading", [y["y"] for y in n["lists"][li]["years"]] == ys and all(y["head"] == y["y"] for y in n["lists"][li]["years"]), str([y["y"] for y in n["lists"][li]["years"]]))
        mark = l["note"][:1] if l["note"] and not l["note"][:1].isalnum() else ""
        used = bool(mark) and any(mark in d["title"] + d.get("who", "") for d in l["items"][: max(1, len(l["items"]))])
        ok(name + ("the line that explains a mark is shown, since an entry carries the mark" if used else "no line explaining a mark that no entry carries"), n["lists"][li]["note"] == (l["note"] if used else ""), n["lists"][li]["note"])


def the_summaries(page, o, label=""):
    """Every word of every summary is in the opened row, and nothing is added."""
    page.evaluate("() => document.querySelectorAll('#hb-pubs .hb-list:not([hidden]) .hb-chev:not([hidden])').forEach(b => b.click())")
    page.wait_for_timeout(500)
    n = new(page)
    papers = in_order(o["lists"][0]["items"])
    rows = n["lists"][0]["rows"]
    missing, added, links, shut, wired = [], [], [], [], []
    for r, d in zip(rows, papers):
        if not d["paper"]:
            continue
        can = bool(d["text"] or d["img"])
        if r["open"] != can or (r["btn"] or {}).get("hidden") == can:
            shut.append(d["title"][:40])
            continue
        if not can:
            continue
        b, m = r["btn"], r["more"]
        if b["exp"] != "true" or b["ctl"] != m["id"] or m["hidden"] or d["title"] not in b["label"]:
            wired.append(d["title"][:40])
        if words(m["text"]) != words(d["text"]):
            (missing if len(words(m["text"])) < len(words(d["text"])) else added).append(d["title"][:40])
        if m["links"] != [x for x in d["links"] if address(x)]:
            links.append(d["title"][:40])
    ok(label + "every paper with a summary or a picture opens, the others have no arrow", not shut, str(shut[:3]))
    ok(label + "the arrow is a button that says what it opens and whether it is open", not wired, str(wired[:3]))
    ok(label + "every word of every summary is in its opened row", not missing, str(missing[:3]))
    ok(label + "and nothing is added to a summary", not added, str(added[:3]))
    ok(label + "links inside a summary are kept", not links, str(links[:3]))
    page.evaluate("() => document.querySelectorAll('#hb-pubs .hb-list:not([hidden]) .hb-paper.is-open .hb-chev').forEach(b => b.click())")
    page.wait_for_timeout(300)
    ok(label + "and they all close again", not any(r["open"] for r in new(page)["lists"][0]["rows"]))


def check(br, bname):
    print(f"\n== {bname}: {URL}", flush=True)
    start = FAILS

    # ---- the page ----
    ctx, page = open_page(br)
    asked = list(page.asked)
    n = new(page)
    if not ok("the block is on the page", bool(n), "no #hb-pubs: is the block on this page?"):
        ctx.close()
        return
    o = old(page)
    ok("the page's own lists can be read", bool(o) and len(o["lists"]) >= 1 and all(l["items"] for l in o["lists"]), str(o and [len(l["items"]) for l in o["lists"]]))
    ok("the block is on, and the page's own section is not shown", n["state"] == "on" and n["seen"] and n["js"] and not o["shown"], f'{n["state"]} {o["shown"]}')
    ok("one <h1>, the block's", n["h1"] == ["Publications"], str(n["h1"]))
    ok('the "Contact me" block stays where it is', o["cta"] == 1, str(o["cta"]))
    ok("the page's quotation, and under it who said it", words(n["quote"]) == words(o["quote"]) and bool(n["say"]) and (not n["by"] or words(n["say"] + " " + n["by"]) == words(o["quote"])), f'{n["quote"]} / {o["quote"]}')
    ok("nothing wider than the window", page.evaluate("() => document.documentElement.scrollWidth <= document.documentElement.clientWidth"))
    the_entries(page, o, n)
    pages = o["lists"][0]["pages"]
    ok(f"the journal papers of all {pages} pages of the list are here ({len(o['lists'][0]['items'])})", len(n["lists"][0]["rows"]) == len(o["lists"][0]["items"]) and not n["lists"][0]["wait"]["seen"])
    ok("the following pages were asked for once each, a few at a time", sorted(set(asked)) == sorted(asked) and set(range(2, pages + 1)) <= set(asked) and len(asked) <= max(0, pages - 1) + 4, str(asked))
    # on a page of their own: opening and closing every paper changes the address a hundred times, and WebKit
    # then refuses further changes for half a minute (the block goes on without them; the checks below would not)
    ctx2, page2 = open_page(br)
    the_summaries(page2, o)
    ok("no script error with every paper opened and closed", not page2.errors, str(page2.errors[:2]))
    ctx2.close()
    ok("no script error", not page.errors, str(page.errors[:2]))
    ok("the block has nothing to complain of", not [w for w in page.warnings if "hydroai" in w], str(page.warnings[:2]))
    papers, keys = in_order(o["lists"][0]["items"]), [l["key"] for l in n["lists"]]
    rows = n["lists"][0]["rows"]

    # ---- the years ----
    ys = [y["y"] for y in n["lists"][0]["years"]]
    ok("the years stand beside the list, the first one marked", [y["y"] for y in n["years"]] == ys and n["rail"] and not n["flat"] and [y["cur"] for y in n["years"]] == [i == 0 for i in range(len(ys))], str(n["years"][:3]))
    ids = page.evaluate("() => [...document.querySelectorAll('[id]')].map(e => e.id)")
    ok("no address the block uses is the id of an element (the site's own script would scroll to it, under the navigation bar)", not [h for h in [y["href"][1:] for y in n["years"]] + [c["href"][1:] for c in n["chips"]] + [r["id"][3:] for l in n["lists"] for r in l["rows"]] if h in ids])
    if len(ys) > 3:
        y = ys[3]
        page.click(f'#hb-pubs .hb-year >> text="{y}"')
        page.wait_for_timeout(1500)
        t = top_of(page, f'#{n["lists"][0]["years"][3]["id"]}')
        nn = new(page)
        ok(f"a click on {y} leads to that year, just under the navigation bar", t is not None and 84 <= t <= 124, str(t))
        ok(f"and {y} is the year marked", [x["y"] for x in nn["years"] if x["cur"]] == [y], str([x["y"] for x in nn["years"] if x["cur"]]))
        ok("the years stay in view while the list is read", 90 <= top_of(page, "#hb-pubs .hb-years") <= 120, str(top_of(page, "#hb-pubs .hb-years")))
        page.evaluate("id => { const s = document.getElementById(id); scrollTo(0, s.getBoundingClientRect().top + scrollY - 120); }", n["lists"][0]["years"][-1]["id"])
        page.wait_for_timeout(500)
        ok("scrolled to the last year, that one is marked", [x["y"] for x in new(page)["years"] if x["cur"]] == [ys[-1]], str([x["y"] for x in new(page)["years"] if x["cur"]]))
        page.click("#hb-pubs .hb-year >> nth=0")
        page.wait_for_timeout(1500)
        t = top_of(page, "#hb-q")
        ok("the first year leads back to the top of the list, the search field in view", t is not None and 74 < t < 400 and [x["y"] for x in new(page)["years"] if x["cur"]] == [ys[0]], str(t))

    # ---- a paper ----
    page.evaluate("() => scrollTo(0, 0)")
    first = next(r for r, d in zip(rows, papers) if d["text"])
    page.click(f'#{first["id"]} .hb-t')
    page.wait_for_timeout(500)
    nn = new(page)
    r = next(x for x in nn["lists"][0]["rows"] if x["id"] == first["id"])
    ok("a click on a row opens its summary, and the address follows", r["open"] and not r["more"]["hidden"] and r["btn"]["exp"] == "true" and nn["hash"] == "#" + first["id"][3:], nn["hash"])
    page.click(f'#{first["id"]} .hb-meta')
    page.wait_for_timeout(350)
    nn = new(page)
    r = next(x for x in nn["lists"][0]["rows"] if x["id"] == first["id"])
    ok("a second click closes it, and the address is the page's again", not r["open"] and r["more"]["hidden"] and r["btn"]["exp"] == "false" and nn["hash"] == "", nn["hash"])
    page.focus(f'#{first["id"]} .hb-chev')
    page.keyboard.press("Enter")
    page.wait_for_timeout(350)
    ok("the arrow opens it from the keyboard", next(x for x in new(page)["lists"][0]["rows"] if x["id"] == first["id"])["open"])
    page.keyboard.press("Enter")
    page.wait_for_timeout(350)
    b = page.evaluate("id => { const r = document.querySelector('#' + id + ' .hb-t').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; }", first["id"])
    page.mouse.move(b[0] + 4, b[1] + 8)
    page.mouse.down()
    page.mouse.move(b[0] + min(b[2] - 6, 260), b[1] + 8, steps=6)
    page.mouse.up()
    page.wait_for_timeout(350)
    sel = page.evaluate("() => String(getSelection())")
    ok("selecting words of a title selects them and opens nothing", len(sel) > 3 and not next(x for x in new(page)["lists"][0]["rows"] if x["id"] == first["id"])["open"], repr(sel))
    page.evaluate("() => getSelection().removeAllRanges()")
    linked = next((r for r, d in zip(rows, papers) if address(d["href"])), None)
    if linked:
        page.evaluate("id => { const x = document.querySelector('#' + id + ' a.hb-out'); x.addEventListener('click', e => e.preventDefault(), { once: true }); x.click(); }", linked["id"])
        page.wait_for_timeout(250)
        ok("the link to the paper does not open the row", not next(x for x in new(page)["lists"][0]["rows"] if x["id"] == linked["id"])["open"])

    # the figure, full size
    figs = [(r, d) for r, d in zip(rows, papers) if d["img"]]
    if len(figs) > 2:
        r, d = figs[1]
        page.click(f'#{r["id"]} .hb-fig')
        page.wait_for_timeout(900)
        nn = new(page)
        files = [d["img"]] + [x.strip().split(" ")[0] for x in d["srcset"].split(",") if x.strip()]
        ok("a click on a figure shows it full size, with the paper's title", nn["lb"]["open"] and nn["lock"] and nn["lb"]["src"] in files and nn["lb"]["cap"] == d["title"] and nn["lb"]["n"] == f"2 / {len(figs)}", str(nn["lb"]))
        ok("and does not open the row", not next(x for x in nn["lists"][0]["rows"] if x["id"] == r["id"])["open"])
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(500)
        ok("the right arrow key shows the next figure", new(page)["lb"]["cap"] == figs[2][1]["title"] and new(page)["lb"]["n"] == f"3 / {len(figs)}", str(new(page)["lb"]))
        page.click('#hb-pubs dialog [data-step="-1"]')
        page.click('#hb-pubs dialog [data-step="-1"]')
        page.wait_for_timeout(500)
        ok("the arrow button steps back", new(page)["lb"]["cap"] == figs[0][1]["title"] and new(page)["lb"]["n"] == f"1 / {len(figs)}", str(new(page)["lb"]))
        page.click('#hb-pubs dialog [data-step="-1"]')
        page.wait_for_timeout(500)
        ok("before the first comes the last", new(page)["lb"]["n"] == f"{len(figs)} / {len(figs)}", new(page)["lb"]["n"])
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        ok("Escape closes it, and the page can be scrolled again", not new(page)["lb"]["open"] and not new(page)["lock"])
        page.click(f'#{r["id"]} .hb-fig')
        page.wait_for_timeout(500)
        page.mouse.click(8, 300)
        page.wait_for_timeout(300)
        ok("a click beside the figure closes it", not new(page)["lb"]["open"])
        page.click(f'#{r["id"]} .hb-fig')
        page.wait_for_timeout(400)
        page.click("#hb-pubs dialog [data-close]")
        page.wait_for_timeout(300)
        ok("the cross closes it", not new(page)["lb"]["open"] and not new(page)["lock"])

    # ---- the lists ----
    for i, key in enumerate(keys[1:], 1):
        page.click(f'#hb-pubs .hb-nav .hb-chip >> nth={i}')
        page.wait_for_timeout(350)
        nn = new(page)
        dated = is_dated(o["lists"][i]["items"])
        ok(f'the chip "{o["lists"][i]["label"]}" shows its list alone, and the address follows', [l["hidden"] for l in nn["lists"]] == [j != i for j in range(len(keys))] and nn["hash"] == "#" + key and [c["cur"] for c in nn["chips"]] == [j == i for j in range(len(keys))], nn["hash"])
        ok("  with its years beside it" if dated else "  a list without dates has no years beside it", (nn["rail"] and [y["y"] for y in nn["years"]] == [y["y"] for y in nn["lists"][i]["years"]]) if dated else (nn["flat"] and not nn["rail"] and not nn["years"]), str(nn["years"][:3]))
    page.click("#hb-pubs .hb-nav .hb-chip >> nth=0")
    page.wait_for_timeout(300)
    ok("the first chip shows the first list, and the address is the page's again", not new(page)["lists"][0]["hidden"] and new(page)["hash"] == "")

    # ---- the address ----
    if len(keys) > 1:
        fresh(page, URL + "#" + keys[-1])
        nn = new(page)
        ok("an address with a list opens that list", not nn["lists"][-1]["hidden"] and nn["chips"][-1]["cur"], nn["hash"])
    late = rows[-2] if len(rows) > 8 else rows[-1]
    fresh(page, URL + "#" + late["id"][3:])
    page.wait_for_timeout(600)
    nn = new(page)
    r = next(x for x in nn["lists"][0]["rows"] if x["id"] == late["id"])
    t = top_of(page, "#" + late["id"])
    ok("an address with a paper of a later page opens it and brings it into view", r["open"] and not nn["lists"][0]["hidden"] and t is not None and 60 < t < 800, f'{r["open"]} {t}')
    if len(n["lists"][0]["years"]) > 2:
        yid = n["lists"][0]["years"][-2]["id"]
        fresh(page, URL + "#" + yid[3:])
        page.wait_for_timeout(600)
        t = top_of(page, "#" + yid)
        ok("an address with a year leads to that year", t is not None and 84 <= t <= 124, str(t))
    fresh(page, URL + "#no-such-thing")
    nn = new(page)
    ok("an address with anything else shows the first list", not nn["lists"][0]["hidden"] and nn["state"] == "on")

    # ---- the search ----
    fresh(page, URL)
    for query in ["cygnss", "smap error", "flash drought 2025"]:
        page.fill("#hb-q", query)
        page.wait_for_timeout(350)
        nn = new(page)
        want = [[d["title"] for d in in_order(found(l["items"], query))] for l in o["lists"]]
        ok(f'"{query}": each list shows what has every word, and nothing else ({" + ".join(str(len(w)) for w in want)})', [[r["title"] for r in l["rows"] if not r["hidden"]] for l in nn["lists"]] == want)
        ok("  the chips count what was found", [c["n"] for c in nn["chips"]] == [str(len(w)) for w in want], str([c["n"] for c in nn["chips"]]))
        marks = [m.lower() for l in nn["lists"] for r in l["rows"] for m in r["marks"]]
        ok("  the words are marked where they stand", bool(marks) and set(marks) <= set(query.lower().split()), str(sorted(set(marks))[:6]))
        if want[0]:
            ok("  the line above the list says how many", nn["status"].startswith(f"{len(want[0])} result") and query in nn["status"] and not nn["none"], nn["status"])
            ok("  only the years that have something stand beside the list", [y["y"] for y in nn["years"]] == [y["y"] for y in nn["lists"][0]["years"] if not y["hidden"]] and all(not y["hidden"] or y["y"] not in [x["y"] for x in nn["years"]] for y in nn["lists"][0]["years"]))
    only = next((q for q in ["under review", "revision", "submitted"] if not found(o["lists"][0]["items"], q) and len(o["lists"]) > 1 and found(o["lists"][1]["items"], q)), None)
    if only:
        page.fill("#hb-q", only)
        page.wait_for_timeout(350)
        nn = new(page)
        hits = [len(found(l["items"], only)) for l in o["lists"]]
        ok(f'"{only}", which no journal paper has: said so, with the lists that have it', nn["none"] and only in nn["status"] and [(x["g"], x["n"]) for x in nn["also"]] == [(k, str(h)) for k, h in zip(keys, hits) if h and k != keys[0]], f'{nn["status"]} {nn["also"]}')
        page.click("#hb-pubs .hb-also .hb-chip >> nth=0")
        page.wait_for_timeout(350)
        nn = new(page)
        ok("  a click on one of them shows it, searched", not nn["lists"][1]["hidden"] and nn["q"] == only and len([r for r in nn["lists"][1]["rows"] if not r["hidden"]]) == hits[1] and not nn["none"])
        page.click("#hb-pubs .hb-nav .hb-chip >> nth=0")
    page.fill("#hb-q", "zzqx")
    page.wait_for_timeout(300)
    nn = new(page)
    ok("a word that is nowhere: said so, and no list offered", nn["none"] and not nn["also"] and all(r["hidden"] for l in nn["lists"] for r in l["rows"]) and nn["clear"], nn["status"])
    page.focus("#hb-q")
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    nn = new(page)
    ok("Escape empties the field and everything is back, unmarked, the chips without numbers", nn["q"] == "" and not nn["clear"] and not any(r["hidden"] or r["marks"] for l in nn["lists"] for r in l["rows"]) and all(c["n"] == "" for c in nn["chips"]) and nn["status"] == "")
    page.fill("#hb-q", "soil")
    page.wait_for_timeout(250)
    page.click("#hb-pubs .hb-clear")
    page.wait_for_timeout(300)
    nn = new(page)
    ok("the cross does the same and leaves the cursor in the field", nn["q"] == "" and not any(r["hidden"] for l in nn["lists"] for r in l["rows"]) and nn["focus"] == "hb-q", nn["focus"])
    page.evaluate("() => { document.activeElement.blur(); scrollTo(0, 2400); }")
    page.wait_for_timeout(300)
    page.keyboard.press("/")
    page.wait_for_timeout(500)
    t = top_of(page, "#hb-q")
    ok('"/" puts the cursor in the search field and brings it into view', new(page)["focus"] == "hb-q" and new(page)["q"] == "" and t is not None and 74 <= t < 800, f'{new(page)["focus"]} {t}')
    page.keyboard.type("a/b")
    ok('and typed there, "/" is a character', new(page)["q"] == "a/b", new(page)["q"])
    ok("no script error after all this", not page.errors, str(page.errors[:2]))
    ctx.close()

    # ---- the following pages ----
    if pages > 1:
        ctx, page = open_page(br, hold={"keep": True}, settle=False)
        page.wait_for_timeout(1200)
        nn = new(page)
        one = len(nn["lists"][0]["rows"])
        ok(f"while the following pages are on their way, the first page's rows are shown ({one}) and the list says that it is loading", nn["state"] == "on" and 0 < one < len(papers) and nn["lists"][0]["wait"]["seen"] and not nn["lists"][0]["wait"]["lost"], f'{one} {nn["lists"][0]["wait"]}')
        page.fill("#hb-q", "zzqx")
        page.wait_for_timeout(250)
        ok("  and a search that finds nothing yet does not say so before everything is here", not new(page)["none"])
        page.fill("#hb-q", "")
        page.release()
        done(page)
        nn = new(page)
        ok("once they are here the list is whole, in order", [r["title"] for r in nn["lists"][0]["rows"]] == [d["title"] for d in papers] and not nn["lists"][0]["wait"]["seen"])
        ctx.close()

        ctx, page = open_page(br, hold={"fail": {3}})
        page.wait_for_timeout(600)
        nn = new(page)
        w = nn["lists"][0]["wait"]
        ok("a page that cannot be fetched: the list says so and offers to try again, and what is here stays", nn["state"] == "on" and w["seen"] and w["lost"] and "could not" in w["text"] and 0 < len(nn["lists"][0]["rows"]) < len(papers), str(w))
        ok("  the block says so in the console too, and the page is not given up", any("hydroai publications block" in x for x in page.warnings) and nn["js"])
        page.hold = {}
        page.click("#hb-pubs .hb-wait button")
        done(page)
        nn = new(page)
        ok('  "Try again" brings the rest, each paper once', [r["title"] for r in nn["lists"][0]["rows"]] == [d["title"] for d in papers] and not nn["lists"][0]["wait"]["seen"], str(len(nn["lists"][0]["rows"])))
        ctx.close()

        key = page_key(br)
        if key:
            ctx, page = open_page(br, with_query(f"{key}=3"))
            nn = new(page)
            ok("opened on the third page of the list (as an old link may), the whole list is shown from its first paper", [r["title"] for r in nn["lists"][0]["rows"]] == [d["title"] for d in papers], str(len(nn["lists"][0]["rows"])))
            ok("  and the other lists are whole too", [len(l["rows"]) for l in nn["lists"][1:]] == [len(l["items"]) for l in o["lists"][1:]])
            ctx.close()
    if LOCAL:
        ctx, page = open_page(br, with_query("one"))
        nn = new(page)
        ok("(local) every paper on the first page, no \"Next\": the same list, and nothing is asked for", [r["title"] for r in nn["lists"][0]["rows"]] == [d["title"] for d in papers] and not page.asked, str(page.asked))
        ctx.close()

    # ---- falling back ----
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(URL, wait_until="load", timeout=60000)
    cards = page.locator(".publications-card").count()
    shown = page.locator(".section.teachers").first.is_visible() and page.locator(".publications-card").first.is_visible()
    block = page.locator("#hb-pubs").is_visible()
    ok("without scripts the page is as it was: its own section, and nothing of the block", cards > 0 and shown and not block, f"{cards} {shown} {block}")
    ctx.close()
    ctx, page = open_page(br, init="delete window.HTMLDialogElement;", settle=False)
    page.wait_for_timeout(900)
    f = page.evaluate("() => ({ state: document.getElementById('hb-pubs').getAttribute('data-state'), block: document.getElementById('hb-pubs').getClientRects().length, sec: getComputedStyle(document.querySelector('.section.teachers')).display, js: document.documentElement.classList.contains('hb-js') })")
    ok("in a browser without <dialog> the page is as it was", f["state"] == "off" and not f["block"] and f["sec"] != "none" and not f["js"], str(f))
    ctx.close()
    ctx, page = open_page(br, edit=lambda h: h.replace('class="w-tab-pane', 'class="x-tab-pane'), settle=False)
    page.wait_for_timeout(900)
    f = page.evaluate("() => ({ state: document.getElementById('hb-pubs').getAttribute('data-state'), block: document.getElementById('hb-pubs').getClientRects().length, sec: getComputedStyle(document.querySelector('.section.teachers')).display, js: document.documentElement.classList.contains('hb-js') })")
    ok("when nothing can be read from the page it is shown as it was, and the console says so", f["state"] == "off" and not f["block"] and f["sec"] != "none" and not f["js"] and any("hydroai publications block" in x for x in page.warnings), str(f))
    ctx.close()

    # ---- other places ----
    if LOCAL:
        ctx, page = open_page(br, with_query("place=last"))
        nn = new(page)
        ok("(local) as the last element of the page instead of the first, the block shows the same", nn["state"] == "on" and [[r["title"] for r in l["rows"]] for l in nn["lists"]] == [[d["title"] for d in in_order(l["items"])] for l in o["lists"]] and not page.errors, str(page.errors[:1]))
        ctx.close()

    # ---- changed pages ----
    if not a.quick:
        changed(br, o)

    # ---- the sizes ----
    for w, h in (SIZES if not a.quick else [SIZES[0], SIZES[2], SIZES[-2]]):
        ctx, page = open_page(br, w=w, h=h)
        f = page.evaluate(FIT)
        ok(f"{w} x {h}: nothing wider than the window", f["scrollW"] <= f["W"] and not f["over"], f'{f["scrollW"]} {f["over"]}')
        ok(f"{w} x {h}: no word cut", not f["cut"], str(f["cut"]))
        ok(f"{w} x {h}: the page centred, at most 1,348 px wide", abs(f["left"] - f["right"]) <= 1 and f["wrap"] <= 1348, f'{f["left"]} {f["right"]} {f["wrap"]}')
        ok(f"{w} x {h}: room for a title", f["small"] >= 200, str(f["small"]))
        beside = w >= 1000
        ok(f"{w} x {h}: the years " + ("beside the list" if beside else "in a row above the list"), f["years"]["seen"] and f["years"]["row"] != beside and (f["years"]["right"] <= f["list"]["left"] if beside else f["years"]["w"] >= f["list"]["w"]), str(f["years"]))
        page.evaluate("() => scrollTo(0, 2600)")
        page.wait_for_timeout(400)
        g = page.evaluate(FIT)
        bar = 64 if w < 480 else 74
        ok(f"{w} x {h}: and they stay in view while the list is read", g["years"]["sticky"] == "sticky" and (90 <= g["years"]["top"] <= 120 if beside else abs(g["years"]["top"] - bar) <= 1), str(g["years"]))
        cur = page.evaluate("() => { const r = document.getElementById('hb-pubs'), c = r.querySelector('.hb-year[aria-current=true]'), y = r.querySelector('.hb-years'); const b = c.getBoundingClientRect(), yb = y.getBoundingClientRect(); return [c.textContent, b.left >= yb.left - 1 && b.right <= yb.right + 1]; }")
        ok(f"{w} x {h}: the year being read is marked and can be seen among the years", cur[1] and cur[0] != "", str(cur))
        nn = new(page)
        r = next((x for x in nn["lists"][0]["rows"] if x["img"] and x["btn"] and not x["btn"]["hidden"]), None)
        if r:
            page.evaluate("id => { document.getElementById(id).scrollIntoView({ block: 'start' }); document.querySelector('#' + id + ' .hb-chev').click(); }", r["id"])
            page.wait_for_timeout(700)
            g = page.evaluate(FIT)
            op = g["open"] or {}
            ok(f"{w} x {h}: an opened paper: the figure and the summary inside the window", bool(op.get("fig")) and op["fig"][0] >= 0 and op["fig"][3] >= 0 and op["fig"][1] >= 60 and op["more"] >= min(280, w - 60) and g["scrollW"] <= g["W"] and not g["over"], str(op))
            if a.shots:
                page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}-open.png"))
            page.click(f'#{r["id"]} .hb-fig')
            page.wait_for_function("() => { const i = document.querySelector('#hb-pubs dialog img'); return i.complete && i.naturalWidth > 0; }", timeout=20000)
            page.wait_for_timeout(700)
            g = page.evaluate(FIT)
            i = g["inner"] or {}
            ok(f"{w} x {h}: an enlarged figure inside the window, not drawn larger than it is", bool(g["inner"]) and min(i["left"], i["top"], i["right"], i["bottom"]) >= 0 and g["close"] and i["w"] > 100, str(g["inner"]))
            if a.shots:
                page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}-figure.png"))
            page.keyboard.press("Escape")
        if a.shots:
            page.evaluate("() => scrollTo(0, 0)")
            page.wait_for_timeout(300)
            page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}.png"))
        ok(f"{w} x {h}: no script error", not page.errors, str(page.errors[:2]))
        ctx.close()

    # ---- a visitor who asked for less motion ----
    ctx, page = open_page(br, reduced_motion="reduce")
    nn = new(page)
    ok("with reduced motion everything is simply there", not nn["anim"] and nn["state"] == "on" and len(nn["lists"][0]["rows"]) == len(papers))
    ctx.close()
    print(f"   {bname}: {FAILS - start} failed", flush=True)


def page_key(br):
    """The name Webflow gives the journal list's page number (9f7fdb6f_page), from the page's own "Next"."""
    ctx = br.new_context(java_script_enabled=False)
    page = ctx.new_page()
    page.goto(base(URL), wait_until="load", timeout=60000)
    href = page.locator("a.w-pagination-next").first.get_attribute("href") if page.locator("a.w-pagination-next").count() else ""
    ctx.close()
    m = re.match(r"^\?([0-9a-f]+_page)=\d+$", href or "")
    return m.group(1) if m else ""


def changed(br, o):
    """The block on a page whose content differs from today's."""
    papers = in_order(o["lists"][0]["items"])
    card = lambda h, i: [m.start() for m in re.finditer(r'<div class="publications-card">', h)][i]
    end = lambda h, i: h.index('</div></div></div><div role="listitem"', card(h, i)) if h.count('<div class="publications-card">') > i + 1 else len(h)

    def part(h, i, fn):
        s, e = card(h, i), end(h, i)
        return h[:s] + fn(h[s:e]) + h[e:]

    first_page = lambda h: 'aria-label="Previous Page"' not in h

    # a paper without a picture; one whose picture cannot be fetched; one with neither summary nor picture
    def edit(h):
        if not first_page(h):
            return h
        h = part(h, 0, lambda c: re.sub(r"<img[^>]*>", "", c, count=1))
        h = part(h, 1, lambda c: re.sub(r'<img[^>]*>', '<img loading="lazy" src="https://cdn.prod.website-files.com/640cbd423ecaf879303aa519/no-such-picture.png" alt="" class="image"/>', c, count=1))
        h = part(h, 2, lambda c: re.sub(r'(<div class="rich-text-block-2 w-richtext">).*?(</div><div class="div-block-8">)', r"\1<p>" + chr(0x200D) + r"</p>\2", re.sub(r"<img[^>]*>", "", c, count=1), count=1, flags=re.S))
        return h

    ctx, page = open_page(br, edit=edit)
    page.wait_for_timeout(1500)
    n = new(page)
    r = n["lists"][0]["rows"]
    ok("changed: a paper without a picture has none, and still opens", r[0]["title"] == papers[0]["title"] and r[0]["img"] == "" and not r[0]["plain"] and not r[0]["btn"]["hidden"])
    ok("changed: a picture that cannot be fetched is left out, and the paper still opens", r[1]["img"] == "" and not r[1]["plain"], r[1]["img"])
    ok("changed: a paper with neither summary nor picture has no arrow", r[2]["plain"] and r[2]["btn"]["hidden"], str(r[2]["btn"]))
    page.click(f'#{r[2]["id"]} .hb-t')
    page.wait_for_timeout(300)
    ok("changed:   and a click on it opens nothing", not new(page)["lists"][0]["rows"][2]["open"] and new(page)["hash"] == "")
    ok("changed: no script error", not page.errors, str(page.errors[:2]))
    ctx.close()

    # a link filled in; an emptied tab; no quotation; a mark that an entry carries; a fourth tab
    tbd = next((i for i, d in enumerate(o["lists"][0]["items"][:6]) if not address(d["href"])), None)
    star = o["lists"][1]["items"][0]["who"] if len(o["lists"]) > 1 and o["lists"][1]["items"] else ""

    def edit2(h):
        if first_page(h) and tbd is not None:
            h = part(h, tbd, lambda c: c.replace('href="TBD"', 'href="https://doi.org/10.1234/example"', 1))
        h = re.sub(r'<div class="limit-740"><p>.*?</p></div>', '<div class="limit-740"></div>', h, count=1, flags=re.S)
        if star:
            h = h.replace("<div>" + star + "</div>", "<div>" + star + "*</div>", 1)
        s = h.index('<div data-w-tab="Conferences" class="w-tab-pane">')
        e = h.index('<div class="section">', s)
        tab = '<a data-w-tab="Books" class="tab-link w-inline-block w-tab-link"><div>Books</div></a>'
        pane = ('<div data-w-tab="Books" class="w-tab-pane"><div class="w-dyn-list"><div role="list" class="w-dyn-items"><div role="listitem" class="w-dyn-item"><div class="ur-card"><h3>A book about soil moisture</h3>'
                '<div>Kim and Lee</div><div class="div-block-10"><div class="text-block-4">A Publisher</div><div class="text-block-5">2027</div></div></div></div><div role="listitem" class="w-dyn-item"><div class="ur-card">'
                '<h3>A chapter</h3><div>Lee</div><div class="div-block-10"><div class="text-block-4">Another Publisher</div><div class="text-block-5">March 2025</div></div></div></div></div></div></div>')
        empty = '<div data-w-tab="Conferences" class="w-tab-pane"><div class="conference_card"><div class="w-dyn-list"><div class="w-dyn-empty"><div>No items found.</div></div></div></div></div>'
        tail = h[e:]
        k = h.rindex("</div></div></div>", s, e)        # the end of the Conferences pane, of the tab content, of the tabs
        h = h[:s] + empty + pane + h[k:e] + tail
        h = h.replace('<div>Conferences</div></a>', '<div>Conferences</div></a>' + tab, 1)
        return h

    ctx, page = open_page(br, edit=edit2)
    n = new(page)
    if ok("changed: the page could be read", bool(n) and n["state"] == "on", str(n and n["state"]) + str(page.warnings[:1])):
        labels = [c["text"] for c in n["chips"]]
        if tbd is not None:
            out = n["lists"][0]["rows"][tbd]["out"]
            ok("changed: a link filled in appears, and opens a new tab", out["tag"] == "A" and out["href"] == "https://doi.org/10.1234/example" and out["target"] == "_blank" and out["text"] == UI["paper"], str(out))
        ok("changed: an emptied tab has no chip, a new tab has one", "Conferences" not in labels and labels[-1] == "Books" and len(labels) == len(o["lists"]), str(labels))
        ok("changed: without a quotation there is none, and no empty frame", n["quote"] == "" and page.evaluate("() => document.querySelector('#hb-pubs .hb-motto').getClientRects().length") == 0, n["quote"])
        if star:
            ok("changed: an entry carries the mark, so the line that explains it is shown", n["lists"][1]["note"] == o["lists"][1]["note"] and bool(o["lists"][1]["note"]), n["lists"][1]["note"])
        b = n["lists"][-1]
        ok("changed: the new tab's entries by year, a date without a day read too", [(r["title"], r["year"], r["meet"]) for r in b["rows"]] == [("A book about soil moisture", "2027", "A Publisher 2027"), ("A chapter", "2025", "Another Publisher Mar 2025")], str([(r["title"], r["year"], r["meet"]) for r in b["rows"]]))
    ok("changed: no script error", not page.errors, str(page.errors[:2]))
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
