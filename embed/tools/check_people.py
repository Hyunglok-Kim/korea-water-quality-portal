#!/usr/bin/env python3
"""check_people.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the People page's block, checked.

    python embed/tools/check_people.py                              # the local preview (people_preview.py, port 8815)
    python embed/tools/check_people.py https://hydroai.net/people   # the live page, once the block is on it

What it looks at, in each browser:
  the page      one <h1>; the block is on and the page's own section is not shown; the "Contact me" block is gone;
                no script error; nothing wider than the window
  the people    everyone in the page's tabs is shown once, in the page's groups and order, with role, name and photograph;
                every word of a person's text is on their card (the first group) or in their profile, and nothing is
                added; links that are no addresses yet ("TBD", "#") are left out and real ones kept; project links kept;
                every photograph arrives; a group named Alumni is shown briefly: each name (without Mr. or Ms.) and
                the role line, nothing else and nothing to open
  the groups    a chip for each group, without numbers; a chip shows one group and the address follows it; "All" shows
                everyone; an address with a group opens it
  a profile     opens from the name, the photograph and "View profile"; closes by the cross, Escape, a click beside it
                and Back; its address opens it; the page behind stays where it was
  the photos    the page's group photographs, all of them; a click enlarges one; arrows and keys step through them
  falling back  without scripts, in a browser without <dialog>, and when nobody can be read: the page as it was
  other places  the block as the first or the last element instead of after the navigation bar (local preview only)
  changed pages a person without photograph, a photograph that cannot be fetched, a link filled in, a second person in
                the first group, an emptied group, a fifth group photograph and no motto, a long text without interests
  the sizes     thirteen window sizes from 2048 px down to a 320 px phone: nothing wider than the window, no word cut,
                the page centred, every card arrived, a profile and an enlarged photograph inside the window
The exit status is the number of failures. Needs playwright with the three browsers installed.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8815/people")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures of every size")
ap.add_argument("--quick", action="store_true", help="leave out the changed pages and all sizes but three")
a = ap.parse_args()
URL = a.url
LOCAL = "127.0.0.1" in URL or "localhost" in URL
FAILS = 0
SIZES = [(2048, 970), (1680, 1050), (1440, 900), (1280, 720), (1200, 800), (1100, 700), (1024, 768), (960, 600), (834, 1194), (768, 1024), (600, 900), (390, 844), (320, 568)]
ZW = "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0xFEFF))
DASH = "-" + chr(0x2013) + chr(0x2014)

# the page's own content, read without the block's help: who is in which tab, and what each card says
OLD = r"""([ZW, DASH]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const pieces = e => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  const tabs = [...document.querySelectorAll('.w-tabs')].find(t => t.querySelector('.people-card'));
  if (!tabs) return null;
  const sec = tabs.closest('.section'), panes = [...tabs.querySelectorAll('.w-tab-pane')];
  const block = x => x.closest('p,h1,h2,h3,h4,h5,h6,li');
  const groups = [...tabs.querySelectorAll('.w-tab-link')].map(a => ({
    label: clean(a.textContent),
    people: [...panes.find(p => p.getAttribute('data-w-tab') === a.getAttribute('data-w-tab')).querySelectorAll('.people-card')].map(card => {
      const img = card.querySelector('.people-image-wrap img');
      const rich = [...card.querySelectorAll('.w-richtext')].filter(r => !/w-dyn-bind-empty|w-condition-invisible/.test(r.className));
      const titles = rich.map(r => { const h = /wrap-people-services/.test(r.parentNode.className) ? r.parentNode.querySelector('h2') : null; return h && !/w-condition-invisible/.test(h.className) ? clean(h.textContent) : ''; });
      const skip = [], links = [], project = [];
      rich.forEach(r => {
        // what need not be shown as words: the line that is the project link, and a heading over nothing but a dash
        [...r.querySelectorAll('a[href]')].forEach(x => { const t = clean(block(x).textContent); if (/^\W*main\s+pro\w*(\s+link)?\W*$/i.test(t)) { skip.push(t); project.push(x.href); } else links.push(x.href); });
        const blocks = [...r.children].filter(b => clean(b.textContent));
        blocks.forEach((b, i) => { if (i && clean(b.textContent).length === 1 && DASH.includes(clean(b.textContent))) skip.push(clean(blocks[i - 1].textContent)); });
      });
      return { name: clean(card.querySelector('.name h2').textContent), role: clean(card.querySelector('.subtext').textContent), photo: (img && img.getAttribute('src')) || '',
        social: [...card.querySelectorAll('a.social-link')].filter(x => !/w-condition-invisible/.test(x.className + ' ' + (x.querySelector('img') || { className: '' }).className)).map(x => ({ raw: (x.getAttribute('href') || '').trim(), abs: x.href })),
        text: rich.map(pieces), titles, skip, links, project };
    }),
  }));
  const head = [...sec.children].filter(c => c !== tabs && !c.querySelector('#hp-people'));
  return { groups, pics: head.flatMap(c => [...c.querySelectorAll('img')].map(i => i.getAttribute('src'))), motto: clean(head.map(c => c.textContent).join(' ')),
    shown: getComputedStyle(sec).display !== 'none', tabsSeen: +getComputedStyle(tabs).opacity, cta: document.querySelectorAll('.cta-block').length };
}"""

# what the block shows
NEW = r"""([ZW]) => {
  const clean = s => [...(s || '')].filter(c => !ZW.includes(c)).join('').replace(/\s+/g, ' ').trim();
  const pieces = e => { const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT), out = []; while (w.nextNode()) out.push(w.currentNode.nodeValue); return clean(out.join(' ')); };
  const r = document.getElementById('hp-people');
  if (!r) return null;
  const seen = e => !!(e && e.getClientRects().length);
  return { state: r.getAttribute('data-state'), seen: seen(r), js: document.documentElement.classList.contains('hp-js'), lock: document.documentElement.classList.contains('hp-lock'),
    h1: [...document.querySelectorAll('h1')].filter(seen).map(h => clean(h.textContent)), hash: location.hash, y: Math.round(scrollY),
    motto: clean(r.querySelector('.hp-motto').textContent), pics: [...r.querySelectorAll('.hp-pic img')].map(i => i.getAttribute('src')),
    chips: [...r.querySelectorAll('.hp-chip')].map(c => ({ g: c.getAttribute('data-g'), text: clean(c.textContent), cur: c.getAttribute('aria-current') === 'true' })),
    groups: [...r.querySelectorAll('.hp-group')].map(g => ({ key: g.getAttribute('data-g'), label: clean(g.querySelector('h2').firstChild.textContent), hidden: g.hidden, solo: g.classList.contains('is-solo'),
      people: [...g.querySelectorAll('.hp-card, .hp-pi, .hp-brief')].map(c => ({ id: c.id, wide: c.classList.contains('hp-pi'), brief: c.classList.contains('hp-brief'), more: c.classList.contains('has-more'),
        name: clean(c.querySelector('.hp-name').textContent), role: clean((c.querySelector('.hp-role, .hp-now') || { textContent: '' }).textContent),
        photo: c.querySelector('.hp-ph img') ? c.querySelector('.hp-ph img').getAttribute('src') : '', empty: !!c.querySelector('.hp-ph.is-empty'), initials: c.querySelector('.hp-ph') ? c.querySelector('.hp-ph').getAttribute('data-i') : '',
        social: [...c.querySelectorAll('.hp-ic')].map(x => ({ href: x.href, label: x.title, tab: x.target })),
        project: c.querySelector('.hp-acts a:not([data-open])') ? c.querySelector('.hp-acts a:not([data-open])').href : '',
        links: [...c.querySelectorAll('.hp-p a, .hp-bd a, .hp-int a, .hp-tags a')].map(x => x.href),
        text: pieces(c), items: [...c.querySelectorAll('.hp-int li')].map(li => clean(li.textContent)), cut: !!c.querySelector('.hp-note.is-cut') })) })),
    dlg: (d => ({ open: d.open, name: d.open ? clean(d.querySelector('#hp-dlg-name').textContent) : '', text: pieces(d.querySelector('[data-hp=profile-body]')),
      pills: [...d.querySelectorAll('.hp-pill')].map(x => ({ href: x.href, text: clean(x.textContent) })), links: [...d.querySelectorAll('.hp-sec a[href]')].map(x => x.href),
      photo: d.querySelector('.hp-ph img') ? d.querySelector('.hp-ph img').getAttribute('src') : '' }))(r.querySelector('[data-hp=profile]')),
    lb: (d => ({ open: d.open, n: clean(d.querySelector('[data-hp=photo-n]').textContent), src: d.querySelector('img').getAttribute('src') || '' }))(r.querySelector('[data-hp=photo]')),
    focus: document.activeElement ? document.activeElement.className : '' };
}"""

# measures at one window size
FIT = r"""() => {
  const W = document.documentElement.clientWidth, H = innerHeight, r = document.getElementById('hp-people');
  const box = e => e.getBoundingClientRect(), name = e => (e.className && e.className.baseVal === undefined ? e.className : e.tagName) + ':' + e.textContent.trim().slice(0, 24);
  const wrap = box(r.querySelector('.hp-wrap')), cards = [...r.querySelectorAll('.hp-card')].filter(c => c.getClientRects().length);
  const dlg = [...r.querySelectorAll('dialog')].find(d => d.open), inner = dlg && dlg.querySelector('.hp-sheet, .hp-fig');
  return { W, scrollW: document.documentElement.scrollWidth,
    over: [...r.querySelectorAll('*')].filter(e => { const b = box(e); return b.width > 0 && !e.closest('dialog') && (b.right > W + 0.5 || b.left < -0.5); }).map(name).slice(0, 4),
    cut: [...r.querySelectorAll('.hp-title, .hp-kicker, .hp-chip, .hp-gh, .hp-name, .hp-role, .hp-mk, .hp-st, .hp-go, .hp-pill, .hp-tags li, .hp-pt')].filter(e => e.getClientRects().length && e.scrollWidth > e.clientWidth + 1).map(name).slice(0, 4),
    faint: [...r.querySelectorAll('.hp-card, .hp-pi, .hp-brief')].filter(e => e.getClientRects().length && getComputedStyle(e).opacity !== '1').length,
    left: Math.round(wrap.left * 10) / 10, right: Math.round((W - wrap.right) * 10) / 10, wrap: Math.round(wrap.width),
    cols: new Set(cards.map(c => Math.round(box(c).left))).size, small: Math.round(Math.min(...[...r.querySelectorAll('.hp-card .hp-int li, .hp-card .hp-p')].filter(e => e.getClientRects().length).map(e => box(e).width))),
    ratio: [...new Set([...r.querySelectorAll('.hp-card .hp-ph')].filter(e => e.getClientRects().length).map(e => (e.offsetWidth / e.offsetHeight).toFixed(2)))],
    inner: inner ? (b => ({ left: Math.round(b.left), top: Math.round(b.top), right: Math.round(W - b.right), bottom: Math.round(H - b.bottom), wide: inner.scrollWidth - inner.clientWidth }))(box(inner)) : null,
    close: dlg ? (b => b.width > 20 && b.top >= 0 && b.bottom <= H && b.left >= 0 && b.right <= W)(box(dlg.querySelector('[data-close]'))) : null };
}"""

WALK = "async () => { const H = () => document.documentElement.scrollHeight; for (let y = 0; y < H(); y += Math.round(innerHeight * 0.7)) { scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, H()); await new Promise(r => setTimeout(r, 250)); scrollTo(0, 0); await new Promise(r => setTimeout(r, 1400)); }"


def ok(name, cond, detail=""):
    global FAILS
    if not cond:
        FAILS += 1
    print(("    ok    " if cond else "    FAIL  ") + name + (f"   [{detail}]" if detail != "" and not cond else ""), flush=True)
    return cond


def words(s):
    return re.findall(r"\w+", s.lower())


def address(href):
    """Is this an address yet? ("TBD", "#" and "https://tbd" are not.)"""
    m = re.match(r"^https?://([^/?#]+\.[a-z]{2,})(?:[/?#]|$)", href, re.I)
    return bool(m) and not re.match(r"^(www\.)?tbd\.", m.group(1), re.I)


def open_page(br, url=None, w=1440, h=900, edit=None, init=None, wait=700, **kw):
    """A page at `url`; `edit` changes the page's HTML on its way to the browser (to try the block on changed content)."""
    ctx = br.new_context(viewport={"width": w, "height": h}, **kw)
    if init:
        ctx.add_init_script(init)
    page = ctx.new_page()
    page.errors, page.warnings = [], []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    page.on("console", lambda m: page.warnings.append(m.text) if m.type == "warning" else None)
    if edit:
        def handle(route):
            r = route.fetch()
            try:
                body = edit(r.text())
            except Exception as e:
                ok("the page could be changed for this check", False, repr(e))
                body = r.text()
            route.fulfill(response=r, body=body)
        page.route(lambda u: u.split("#")[0].split("?")[0] == URL.split("#")[0].split("?")[0], handle)
    page.goto(url or URL, wait_until="load", timeout=60000)
    page.wait_for_timeout(wait)
    return ctx, page


def fresh(page, url):
    """Open `url` anew (from the same page, an address that differs only after the # would not load the page again)."""
    page.goto("about:blank")
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(700)


def after_name(h, name):
    """Where the page's HTML has this person's name."""
    return re.search(">\\s*" + "\\s+".join(re.escape(w) for w in name.split()) + "\\s*<", h).start()


def old(page):
    return page.evaluate(OLD, [ZW, DASH])


def new(page):
    return page.evaluate(NEW, [ZW])


def with_query(q):
    return URL + ("&" if "?" in URL else "?") + q


def the_people(page, o, n, label=""):
    """Everyone the page lists is shown, with everything their card says."""
    og = [g for g in o["groups"] if g["people"]]
    short = [gi > 0 and "alumni" in g["label"].lower() for gi, g in enumerate(og)]      # a group named Alumni is shown briefly
    plainly = lambda name: re.sub(r"^((mr|ms|mrs|miss|mx)\.?\s+)+", "", name, flags=re.I)
    ok(label + "the groups are the page's tabs that have someone, in the page's order", [g["label"] for g in n["groups"]] == [g["label"] for g in og], f'{[g["label"] for g in n["groups"]]} / {[g["label"] for g in og]}')
    ok(label + "everyone is shown once, in the page's order", [[p["name"] for p in g["people"]] for g in n["groups"]] == [[plainly(p["name"]) if short[gi] else p["name"] for p in g["people"]] for gi, g in enumerate(og)])
    total = sum(len(g["people"]) for g in og)
    chips = n["chips"]
    ok(label + "a chip for all and one for each group, without numbers", [c["text"] for c in chips] == ["All"] + [g["label"] for g in og], str([c["text"] for c in chips]))
    ok(label + "no head counts in the headings either", page.evaluate("() => [...document.querySelectorAll('#hp-people .hp-gh')].every(h => !/\\d/.test(h.textContent))"))
    ok(label + "the first group is drawn wide, a group named Alumni briefly, the others as cards", all(p["wide"] == (gi == 0) and p["brief"] == short[gi] for gi, g in enumerate(n["groups"]) for p in g["people"]))
    brief = [(p, og[gi]["people"][pi]) for gi, g in enumerate(n["groups"]) for pi, p in enumerate(g["people"]) if short[gi] and pi < len(og[gi]["people"])]
    if brief:
        ok(label + "Alumni: the name without Mr. or Ms. and the role line (where they are now), nothing else, nothing to open",
           all(words(p["text"]) == words(plainly(op["name"]) + " " + op["role"]) and not p["more"] and not p["photo"] and not p["social"] for p, op in brief), str([p["text"] for p, op in brief][:3]))
    ids = [p["id"] for g in n["groups"] for p in g["people"]]
    ok(label + "every card has its own address", len(set(ids)) == len(ids) and all(i.startswith("hp-") and len(i) > 3 for i in ids), str(ids))
    bad = {"role": [], "photo": [], "social": [], "project": [], "missing": [], "added": [], "links": [], "card": [], "opens": []}
    for gi, g in enumerate(og):
        for pi, op in enumerate(g["people"]):
            if gi >= len(n["groups"]) or pi >= len(n["groups"][gi]["people"]):
                continue
            np_ = n["groups"][gi]["people"][pi]
            who = op["name"]
            if short[gi]:
                continue        # checked above: an alumnus is a name and a line
            if words(np_["role"]) != words(op["role"]):
                bad["role"].append(who)
            if (np_["photo"] or "") != op["photo"] and not np_["empty"]:
                bad["photo"].append(who)
            want = [s["abs"] for s in op["social"] if address(s["raw"])]
            if [s["href"] for s in np_["social"]] != want or any(s["tab"] != "_blank" or not s["label"] for s in np_["social"]):
                bad["social"].append(f'{who}: {[s["href"] for s in np_["social"]]} / {want}')
            if np_["project"] != (op["project"][0] if op["project"] else ""):
                bad["project"].append(who)
            expect = Counter(words(" ".join(op["text"] + op["titles"])))
            for s in op["skip"]:
                expect -= Counter(words(s))
            ui = Counter(words(" ".join([op["name"], op["role"], "main project view profile research interests", " ".join(s["label"] for s in np_["social"])])))
            if np_["more"]:
                # the profile carries the whole text; the card a part of it
                page.click(f'#{np_["id"]} .hp-name a')
                page.wait_for_timeout(250)
                d = new(page)["dlg"]
                if not d["open"] or d["name"] != who:
                    bad["opens"].append(who)
                    continue
                shown, links = Counter(words(d["text"])), d["links"]
                if [x["href"] for x in d["pills"] if "project" not in x["text"].lower()] != want:
                    bad["social"].append(who + " (profile)")
                if not np_["empty"] and d["photo"] != np_["photo"]:
                    bad["photo"].append(who + " (profile)")
                if Counter(words(np_["text"])) - expect - ui:
                    bad["card"].append(f'{who}: {sorted((Counter(words(np_["text"])) - expect - ui).elements())[:6]}')
                page.keyboard.press("Escape")
                page.wait_for_timeout(150)
            else:
                shown, links = Counter(words(np_["text"])), np_["links"]
                if not np_["wide"] and np_["cut"]:
                    bad["card"].append(who + ": text cut on a card that opens nothing")
            missing = expect - shown
            if not np_["wide"] and not np_["more"]:
                # a card that is all there is lists the interests without their heading and without the numbers of the list
                missing = Counter({k: v for k, v in (missing - Counter(["research", "interests", "interest"])).items() if not (k.isdigit() and len(k) < 3)})
            if missing:
                bad["missing"].append(f'{who}: {sorted(missing.elements())[:8]}')
            extra = shown - expect - ui
            extra = Counter({k: v for k, v in extra.items() if not (k.isdigit() and (np_["wide"] or len(k) < 3))})       # a numbered list's numbers; how many lines a folded section holds
            if extra:
                bad["added"].append(f'{who}: {sorted(extra.elements())[:8]}')
            if sorted(links) != sorted(op["links"]):
                bad["links"].append(f'{who}: {links} / {op["links"]}')
    ok(label + "roles as the page has them", not bad["role"], str(bad["role"]))
    ok(label + "photographs are the page's own", not bad["photo"], str(bad["photo"]))
    ok(label + 'links that are addresses are kept, in a new tab; "TBD" and "#" are left out', not bad["social"], str(bad["social"][:3]))
    ok(label + "project links kept", not bad["project"], str(bad["project"]))
    ok(label + "whoever has more to show opens as a profile under their name", not bad["opens"], str(bad["opens"]))
    ok(label + "every word of everyone's text is shown", not bad["missing"], str(bad["missing"][:3]))
    ok(label + "no word is added to anyone's text", not bad["added"], str(bad["added"][:3]))
    ok(label + "a card says nothing its profile does not", not bad["card"], str(bad["card"][:3]))
    ok(label + "links inside the texts are kept", not bad["links"], str(bad["links"][:2]))
    return total


def check(br, bname):
    print(f"\n{bname}")
    # ---- the page ----
    print("  the page")
    ctx, page = open_page(br)
    o, n = old(page), new(page)
    if not ok("the People tabs and the block are on the page", bool(o) and bool(n), "is this the People page with the block on it?"):
        ctx.close()
        return
    ok("the block is on", n["state"] == "on" and n["seen"] and n["js"], str(n["state"]))
    ok("the page's own section is not shown", not o["shown"])
    ok('the "Contact me" block is gone', o["cta"] == 0, str(o["cta"]))
    ok("one <h1>, the block's", n["h1"] == ["People"], str(n["h1"]))
    ok("the motto is the page's", n["motto"] == o["motto"] and len(n["motto"]) > 5, f'{n["motto"]!r} / {o["motto"]!r}')
    ok("the group photographs are the page's, all of them", n["pics"] == o["pics"] and len(n["pics"]) > 0, f'{len(n["pics"])} / {len(o["pics"])}')

    # ---- the people ----
    print("  the people")
    total = the_people(page, o, n)
    page.evaluate(WALK)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    pics = page.evaluate("() => [...document.querySelectorAll('#hp-people .hp-ph img, #hp-people .hp-pic img')].filter(i => !i.closest('dialog')).map(i => ({ src: i.currentSrc.split('/').pop(), ok: i.complete && i.naturalWidth > 0 }))")
    ok("every photograph arrives", len(pics) >= total and all(p["ok"] for p in pics), str([p["src"] for p in pics if not p["ok"]][:4]))
    ok("no script error", not page.errors, str(page.errors[:2]))

    # ---- the groups ----
    print("  the groups")
    keys = [g["key"] for g in n["groups"]]
    seen = []
    for k in keys:
        page.click(f'.hp-chip[data-g="{k}"]')
        page.wait_for_timeout(120)
        s = new(page)
        seen.append(([g["key"] for g in s["groups"] if not g["hidden"]], [c["g"] for c in s["chips"] if c["cur"]], s["hash"]))
    ok("a chip shows its group alone, is marked, and the address follows", seen == [([k], [k], "#" + k) for k in keys], str(seen[:2]))
    page.click('.hp-chip[data-g=""]')
    page.wait_for_timeout(120)
    s = new(page)
    ok('"All" shows everyone again and clears the address', all(not g["hidden"] for g in s["groups"]) and s["hash"] == "" and [c["g"] for c in s["chips"] if c["cur"]] == [""])
    fresh(page, URL + "#" + keys[-1])
    s = new(page)
    ok("an address with a group opens on that group", [g["key"] for g in s["groups"] if not g["hidden"]] == [keys[-1]], str(s["hash"]))
    page.goto(URL + "#" + keys[1], wait_until="load")
    page.wait_for_timeout(300)
    s = new(page)
    ok("the address changed by hand to another group shows that one", [g["key"] for g in s["groups"] if not g["hidden"]] == [keys[1]], str(s["hash"]))
    fresh(page, URL + "#no-such-thing")
    ok("an address with something unknown shows everyone", all(not g["hidden"] for g in new(page)["groups"]))
    ctx.close()

    # ---- a profile ----
    print("  a profile")
    ctx, page = open_page(br)
    n = new(page)
    cards = [p for g in n["groups"] for p in g["people"] if p["more"]]
    plain = [p for g in n["groups"][1:] for p in g["people"] if not p["more"]]
    if ok("somebody has a profile to open", bool(cards)):
        c = cards[0]
        sid = c["id"][3:]
        page.click(f'.hp-chip[data-g="{n["groups"][1]["key"]}"]')
        ways = {}
        for way, sel in (("name", f'#{c["id"]} .hp-name a'), ("photograph", f'#{c["id"]} .hp-phl'), ("View profile", f'#{c["id"]} .hp-go[data-open]')):
            page.click(sel)
            page.wait_for_timeout(350)
            s = new(page)
            ways[way] = s["dlg"]["open"] and s["dlg"]["name"] == c["name"] and s["hash"] == "#" + sid and s["lock"]
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)
        ok("it opens from the name, the photograph and \"View profile\", and the address names the person", all(ways.values()), str(ways))
        s = new(page)
        ok("Escape closes it and the address goes back to the group", not s["dlg"]["open"] and s["hash"] == "#" + n["groups"][1]["key"] and not s["lock"], s["hash"])
        far = [p for p in n["groups"][1]["people"] if p["more"]][-1]       # someone far enough down that the page has been scrolled to reach them
        page.click(f'#{far["id"]} .hp-name a')
        page.wait_for_timeout(350)
        ok("the close button has the focus when it opens", "hp-x" in new(page)["focus"], new(page)["focus"])
        y0 = new(page)["y"]
        page.mouse.move(20, 400)
        page.mouse.wheel(0, 700)
        page.wait_for_timeout(300)
        ok("the page behind stays where it was when the wheel turns", new(page)["y"] == y0 and y0 > 0, f'{new(page)["y"]} / {y0}')
        page.click(".hp-dlg[open] [data-close]")
        page.wait_for_timeout(300)
        closed = [not new(page)["dlg"]["open"]]
        page.click(f'#{c["id"]} .hp-name a')
        page.wait_for_timeout(300)
        page.mouse.click(12, 300)
        page.wait_for_timeout(300)
        closed.append(not new(page)["dlg"]["open"])
        page.click(f'#{c["id"]} .hp-name a')
        page.wait_for_timeout(300)
        page.go_back()
        page.wait_for_timeout(400)
        closed.append(not new(page)["dlg"]["open"] and new(page)["hash"] == "#" + n["groups"][1]["key"])
        ok("the cross, a click beside it and Back close it", all(closed), str(closed))
        page.go_forward()
        page.wait_for_timeout(400)
        ok("Forward opens it again", new(page)["dlg"]["open"] and new(page)["dlg"]["name"] == c["name"])
        page.keyboard.press("Escape")
        fresh(page, URL + "#" + sid)
        s = new(page)
        ok("a person's address opens their profile, over everyone", s["dlg"]["open"] and s["dlg"]["name"] == c["name"] and all(not g["hidden"] for g in s["groups"]))
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        s = new(page)
        box = page.evaluate(f"() => {{ const b = document.getElementById('{c['id']}').getBoundingClientRect(); return b.top >= 0 && b.bottom <= innerHeight + 2; }}")
        ok("closed, the address is clean and their card is in view", not s["dlg"]["open"] and s["hash"] == "" and box, f'{s["hash"]} {box}')
    if plain:
        c = plain[0]
        fresh(page, URL + "#" + c["id"][3:])
        box = page.evaluate(f"() => {{ const e = document.getElementById('{c['id']}'), b = e.getBoundingClientRect(); return b.top >= 0 && b.bottom <= innerHeight + 2 && e.classList.contains('is-here'); }}")
        ok("the address of a person with nothing to open brings their card into view, marked", box and not new(page)["dlg"]["open"])
    wide = n["groups"][0]["people"][0]
    fresh(page, URL + "#" + wide["id"][3:])
    top = page.evaluate(f"() => Math.round(document.getElementById('{wide['id']}').getBoundingClientRect().top)")
    ok("the address of the first group's person brings the top of their card under the navigation bar", 70 <= top <= 140, str(top))
    fold = page.evaluate("() => { const d = document.querySelector('#hp-people .hp-fold'); if (!d) return null; const was = d.open; d.querySelector('summary').click(); return [was, d.open, d.querySelector('.hp-parts').getClientRects().length > 0]; }")
    ok("a long section of the wide card is folded, and opens", fold is None or fold == [False, True, True], str(fold))
    ok("no script error", not page.errors, str(page.errors[:2]))
    ctx.close()

    # ---- the photographs ----
    print("  the photographs")
    ctx, page = open_page(br)
    n = new(page)
    k = len(n["pics"])
    page.click(".hp-pic >> nth=0")
    page.wait_for_timeout(350)
    s = new(page)
    ok("a click enlarges a photograph", s["lb"]["open"] and s["lb"]["src"] == n["pics"][0] and s["lb"]["n"] == f"1 / {k}" and s["lock"], str(s["lb"]))
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(150)
    step = [new(page)["lb"]["src"] == n["pics"][1 % k]]
    page.click('.hp-lb [data-step="1"]')
    page.wait_for_timeout(150)
    step.append(new(page)["lb"]["src"] == n["pics"][2 % k])
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(150)
    step.append(new(page)["lb"]["src"] == n["pics"][-1] and new(page)["lb"]["n"] == f"{k} / {k}")
    ok("the keys and the arrows step through them, round the end", all(step), str(step))
    big = page.evaluate("() => { const i = document.querySelector('#hp-people .hp-lb img'); return new Promise(r => { const done = () => r({ w: i.naturalWidth, box: i.getBoundingClientRect().width }); i.complete && i.naturalWidth ? done() : (i.onload = done, setTimeout(done, 8000)); }); }")
    ok("the enlarged photograph arrives, larger than its tile", big["w"] > 0 and big["box"] > 400, str(big))
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    s = new(page)
    ok("Escape closes it and the page scrolls again", not s["lb"]["open"] and not s["lock"])
    ctx.close()

    # ---- falling back ----
    print("  falling back")
    asked = "() => { const r = document.getElementById('hp-people'), sec = document.querySelector('.section.teachers'), tabs = sec.querySelector('.w-tabs'); return { state: r.getAttribute('data-state'), block: r.getClientRects().length, old: getComputedStyle(sec).display !== 'none' && sec.getClientRects().length > 0, tabs: +getComputedStyle(tabs).opacity, js: document.documentElement.classList.contains('hp-js') }; }"
    ctx, page = open_page(br, java_script_enabled=False)
    s = page.evaluate(asked)
    ok("without scripts: the page's own section, and nothing of the block", s["state"] is None and s["block"] == 0 and s["old"] and not s["js"], str(s))
    ctx.close()
    for what, kw in (("in a browser without <dialog>", dict(init="delete window.HTMLDialogElement; Object.defineProperty(window, 'HTMLDialogElement', { value: undefined });")),
                     ("when nobody can be read from the page", dict(edit=lambda h: h.replace('class="people-card"', 'class="people-kard"')))):
        ctx, page = open_page(br, wait=1500, **kw)
        s = page.evaluate(asked)
        ok(f"{what}: the page as it was, tabs and all", s["state"] == "off" and s["block"] == 0 and s["old"] and s["tabs"] == 1 and not s["js"], str(s))
        if "edit" in kw:
            ok("  and the reason is in the console", any("people block" in w for w in page.warnings), str(page.warnings[:2]))
        ok(f"{what}: no script error", not page.errors, str(page.errors[:2]))
        ctx.close()

    # ---- other places ----
    if LOCAL:
        print("  other places")
        for place in ("first", "last"):
            ctx, page = open_page(br, with_query("place=" + place))
            o2, n2 = old(page), new(page)
            ok(f"as the {place} element: on, everyone there, the page's own section not shown", n2["state"] == "on" and sum(len(g["people"]) for g in n2["groups"]) == total and not o2["shown"] and n2["motto"] == o["motto"] and n2["pics"] == o["pics"] and not page.errors, str(page.errors[:1]))
            ctx.close()
        ctx, page = open_page(br, with_query("cta"))
        ok('with the "Contact me" block still on the page: on all the same', new(page)["state"] == "on" and old(page)["cta"] == 1)
        ctx.close()

    # ---- changed pages ----
    if not a.quick:
        print("  changed pages")
        o0 = o
        groups = {g["label"]: g for g in o0["groups"]}
        second = [g for g in o0["groups"] if len(g["people"]) > 2][0]
        nophoto, broken, linked = second["people"][0], second["people"][1], second["people"][2]

        def changed(h):
            # a person without a photograph; one whose photograph cannot be fetched; one whose first link is filled in
            for person, new_src in ((nophoto, ""), (broken, "https://cdn.prod.website-files.com/640cbd423ecaf879303aa519/no-such-picture.jpg")):
                i = h.index(person["photo"])
                j = h.index(">", i)
                tag = h[i:j]
                tag = re.sub(r'\ssrcset="[^"]*"', "", tag).replace(person["photo"], new_src, 1)
                h = h[:i] + tag + h[j:]
            i = after_name(h, linked["name"])
            j = h.index('href="', i)
            k = h.index('"', j + 6)
            h = h[:j] + 'href="https://orcid.org/0000-0002-1825-0097"' + h[k + 1:]
            # a second person in the first group: the first one's item, twice
            pane = h.index('class="w-tab-pane', h.index('class="w-tab-content"'))
            i = h.index('<div role="listitem"', pane)
            depth, j = 0, i
            for m in re.finditer(r"<(/?)div\b[^>]*>", h[i:]):
                depth += -1 if m.group(1) else 1
                if depth == 0:
                    j = i + m.end()
                    break
            h = h[:j] + h[i:j] + h[j:]
            # a fifth group photograph, and no motto
            first = o0["pics"][0]
            i = h.index("<img", h.rindex("<", 0, h.index(first)))
            j = h.index(">", i) + 1
            h = h[:j] + h[i:j] + h[j:]
            h = h.replace(">" + o0["motto"], ">", 1)
            return h

        ctx, page = open_page(br, edit=changed, wait=900)
        o2, n2 = old(page), new(page)
        ok("the changed page is read: on", n2 and n2["state"] == "on", str(n2 and n2["state"]))
        if n2 and n2["state"] == "on":
            page.evaluate(WALK)
            page.wait_for_timeout(1500)
            n2 = new(page)
            byname = {}
            for g in n2["groups"]:
                for p in g["people"]:
                    byname.setdefault(p["name"], []).append(p)
            want = "".join(w[0] for w in re.sub(r"^((prof|dr|mr|ms|mrs|miss|mx)\.?\s+)+", "", nophoto["name"], flags=re.I).split())[:2].upper()
            p = byname[nophoto["name"]][0]
            ok("a person without a photograph gets their initials", p["empty"] and p["initials"] == want and not p["photo"], f'{p["initials"]} / {want}')
            p = byname[broken["name"]][0]
            ok("a photograph that cannot be fetched gives way to the initials", p["empty"], str(p["photo"]))
            p = byname[linked["name"]][0]
            ok("a link that is filled in appears, named after its site", [(s["href"], s["label"]) for s in p["social"]] == [("https://orcid.org/0000-0002-1825-0097", "orcid.org")], str(p["social"]))
            firsts = n2["groups"][0]["people"]
            ok("a second person in the first group gets a wide card and an address of their own", len(firsts) == 2 and all(p["wide"] for p in firsts) and firsts[1]["id"] == firsts[0]["id"] + "-2", str([p["id"] for p in firsts]))
            ok("a fifth group photograph is shown with the others", len(n2["pics"]) == len(o0["pics"]) + 1)
            ok("without a motto its place is empty", n2["motto"] == "" and page.evaluate("() => document.querySelector('#hp-people .hp-motto').getClientRects().length") == 0, repr(n2["motto"]))
            the_people(page, o2, n2, "changed: ")
            ok("no script error", not page.errors, str(page.errors[:2]))
        ctx.close()

        # a group that has nobody (Webflow then writes "No items found"), and a long text without interests
        solo = [g for g in o0["groups"][1:] if len(g["people"]) == 1]
        if len(solo) >= 2:
            gone, kept = solo[0], solo[-1]
            long_text = " ".join(["This sentence stands in for a long description of somebody who lists no research interests."] * 6)

            def emptied(h):
                i = after_name(h, gone["people"][0]["name"])
                s = h.rindex('<div role="list" ', 0, i)
                e = s
                depth = 0
                for m in re.finditer(r"<(/?)div\b[^>]*>", h[s:]):
                    depth += -1 if m.group(1) else 1
                    if depth == 0:
                        e = s + m.end()
                        break
                h = h[:s] + '<div class="w-dyn-empty"><div>No items found.</div></div>' + h[e:]
                i = after_name(h, kept["people"][0]["name"])
                mark = 'class="rich-text-block-5 w-richtext">'
                j = h.index(mark, i) + len(mark)
                return h[:j] + "<p>" + long_text + "</p>" + h[j:]

            ctx, page = open_page(br, edit=emptied, wait=900)
            n2 = new(page)
            ok("a group with nobody in it has no chip and no heading", n2["state"] == "on" and gone["label"] not in [g["label"] for g in n2["groups"]] and not any(gone["label"] in c["text"] for c in n2["chips"]), str([g["label"] for g in n2["groups"]]))
            p = [p for g in n2["groups"] for p in g["people"] if p["name"] == kept["people"][0]["name"]]
            ok("a long text without interests is cut on the card and opens whole as a profile", bool(p) and p[0]["more"] and p[0]["cut"], str(p[:1])[:200])
            if p and p[0]["more"]:
                page.click(f'#{p[0]["id"]} .hp-name a')
                page.wait_for_timeout(300)
                ok("  the profile has all of it", new(page)["dlg"]["text"].count("This sentence stands in") == 6)
            ok("no script error", not page.errors, str(page.errors[:2]))
            ctx.close()

    # ---- the sizes ----
    print("  the sizes")
    sizes = [s for s in SIZES if s[0] in (2048, 1440, 390)] if a.quick else SIZES
    wordy = max((p for g in o["groups"][1:] for p in g["people"]), key=lambda p: len(" ".join(p["text"])))["name"]      # whoever has the most to say: the longest profile
    for w, h in sizes:
        ctx, page = open_page(br, w=w, h=h)
        page.evaluate(WALK)
        f = page.evaluate(FIT)
        n = new(page)
        cols = 2 if w >= 700 else 1
        good = (f["scrollW"] <= f["W"] and not f["over"] and not f["cut"] and f["faint"] == 0 and abs(f["left"] - f["right"]) <= 1 and f["wrap"] <= 1348
                and f["cols"] == cols and f["small"] >= 200 and f["ratio"] == ["0.80"])
        ok(f"{w} x {h}: fits, centred, {cols} column{'s' if cols > 1 else ''}, every card there", good, str(f))
        if a.shots:
            Path(a.shots).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}.png"), full_page=True)
        long_one = next((p for g in n["groups"] for p in g["people"] if p["more"] and p["name"] == wordy), None)
        if long_one:
            page.goto(URL + "#" + long_one["id"][3:], wait_until="load")
            page.wait_for_timeout(600)
            f = page.evaluate(FIT)
            i = f["inner"] or {}
            deep = page.evaluate("() => { const s = document.querySelector('#hp-people .hp-sheet'); s.scrollTop = 1e6; return s.scrollTop; }")
            ok(f"{w} x {h}: the longest profile inside the window, scrolling in itself, its cross in reach", bool(f["inner"]) and min(i["left"], i["top"], i["right"], i["bottom"]) >= 0 and i["wide"] <= 0 and f["close"] and deep > 0, f'{f["inner"]} {deep}')
            if a.shots:
                page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}-profile.png"))
            page.keyboard.press("Escape")
        page.goto(URL, wait_until="load")
        page.wait_for_timeout(400)
        page.click(".hp-pic >> nth=-1")
        page.wait_for_function("() => { const i = document.querySelector('#hp-people .hp-lb img'); return i.complete && i.naturalWidth > 0; }", timeout=20000)
        page.wait_for_timeout(350)
        f = page.evaluate(FIT)
        i = f["inner"] or {}
        ok(f"{w} x {h}: an enlarged photograph inside the window", bool(f["inner"]) and min(i["left"], i["top"], i["right"], i["bottom"]) >= 0 and f["close"], str(f["inner"]))
        if a.shots:
            page.screenshot(path=str(Path(a.shots) / f"{bname}-{w}-photo.png"))
        ok(f"{w} x {h}: no script error", not page.errors, str(page.errors[:2]))
        ctx.close()

    # ---- a visitor who asked for less motion ----
    ctx, page = open_page(br, reduced_motion="reduce")
    f = page.evaluate("() => ({ anim: document.getElementById('hp-people').classList.contains('hp-anim'), faint: [...document.querySelectorAll('#hp-people .hp-card, #hp-people .hp-pi')].filter(e => getComputedStyle(e).opacity !== '1').length })")
    ok("with reduced motion everything is simply there", not f["anim"] and f["faint"] == 0, str(f))
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
