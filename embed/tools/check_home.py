#!/usr/bin/env python3
"""check_home.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] — the home page announcement in real browsers.

    python embed/tools/check_home.py                          # the local preview (home_preview.py), http://127.0.0.1:8813/
    python embed/tools/check_home.py https://hydroai.net/     # the live page, once the embed is on it

What it checks, each time in a browser that has never seen the page unless said otherwise:
  first visit   the page is seen first, then the dialog opens once; it is a labelled modal dialog with the focus in it;
                the loop plays and every caption and all twelve months are shown; the page behind does not scroll;
                Tab stays inside; Escape closes it and the pill comes in
  later visits  no dialog, the pill only; hiding the pill is remembered
  ways out      "Maybe later", a click beside the card, and the link (which is remembered: no pill afterwards)
  narrow        the picture on top with the Data page card's loop; nothing wider than the window
  sizes         the card inside the window from 2048 px wide down to 360 px, and in short wide windows (a phone held
                sideways), where the picture stays beside the text; the loop always the one made for the layout; the
                button in view without scrolling, and where the text scrolls its last line comes clear of the button
  kindness      reduced motion (a still picture, no video fetched); storage blocked (no dialog, the pill only);
                past its last day (nothing at all); a tab opened in the background (waits until it is looked at)
Exit status is the number of failed checks. Needs playwright with its browsers.
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8813/")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures of the dialog at each size (chromium)")
a = ap.parse_args()

ID, KEY = "wq-korea-2026-11", "hydroai-announcement"
TITLE = "Inland Water Quality of South Korea"
CAPS = ["Water temperature, 2016–2024 mean", "Suspended solids", "Dissolved oxygen", "Total nitrogen", "Total phosphorus",
        "Chlorophyll-a", "Into Daecheong Lake: 1 km cells", "Chlorophyll-a through the year"]
SIZES = [(2048, 1100), (1440, 900), (1280, 720), (1280, 560), (1024, 768), (900, 700), (932, 430), (844, 390), (667, 375), (568, 320),
         (768, 1024), (390, 844), (360, 640)]
STACKED = lambda w, h: (w <= 880 and h >= 600) or w <= 599          # the picture on top; otherwise beside the text
STATE = """() => { const root = document.getElementById('ha-ann'), pill = document.getElementById('ha-pill'); if (!root || !pill) return null;
  const v = root.querySelector('video'), on = (e) => !e.hidden && getComputedStyle(e).display !== 'none';
  let st = null; try { st = JSON.parse(localStorage.getItem('hydroai-announcement')); } catch (e) {}
  const r = (e) => { const b = e.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom].map(Math.round); };
  const card = root.querySelector('.ha-card'), body = root.querySelector('.ha-body'), a = document.activeElement, m = root.querySelector('.ha-months');
  const cr = r(card), mid = document.elementFromPoint((cr[0] + cr[2]) / 2, (cr[1] + cr[3]) / 2), x = root.querySelector('.ha-x'), xr = r(x);
  return {open: on(root) && root.classList.contains('is-open'), shown: on(root), pill: on(pill) && pill.classList.contains('is-in'), inBody: root.parentElement === document.body && pill.parentElement === document.body,
    loop: v.getAttribute('data-loop'), t: v.currentTime, sources: [...v.querySelectorAll('source')].map((s) => s.src.split('/').pop()), err: v.error ? v.error.code : 0,
    cap: root.querySelector('.ha-cap').textContent, month: m.classList.contains('is-on') ? [...m.children].findIndex((i) => i.classList.contains('is-on')) + 1 : 0,
    focus: a ? String(a.className || a.tagName) : '', state: st, card: cr, media: r(root.querySelector('.ha-media')), body: [body.scrollHeight, body.clientHeight], body_top: r(body)[1],
    cta: r(root.querySelector('.ha-cta')), top: !!mid && card.contains(mid), xTop: document.elementFromPoint((xr[0] + xr[2]) / 2, (xr[1] + xr[3]) / 2) === x || x.contains(document.elementFromPoint((xr[0] + xr[2]) / 2, (xr[1] + xr[3]) / 2)),
    role: card.getAttribute('role'), modal: card.getAttribute('aria-modal'), label: (document.getElementById(card.getAttribute('aria-labelledby')) || {}).textContent,
    href: root.querySelector('.ha-cta').href, pillHref: pill.querySelector('a').href, y: Math.round(window.scrollY), docW: document.documentElement.scrollWidth, win: [innerWidth, innerHeight]}; }"""

failed = 0


def check(name, ok, detail=""):
    global failed
    failed += 0 if ok else 1
    print(("ok   " if ok else "FAIL ") + name + (f" ({detail})" if detail != "" else ""), flush=True)


def run(pw, kind):
    br = getattr(pw, kind).launch()
    errors = []

    def fresh(w=1440, h=900, init=None, **kw):
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, **kw)
        if init:
            ctx.add_init_script(init)
        page = ctx.new_page()
        page.on("pageerror", lambda e: errors.append(str(e)))
        return page

    def opened(page, wait="load"):
        page.goto(a.url, wait_until=wait)
        page.wait_for_selector(".ha-ann.is-open", timeout=20000)
        page.wait_for_timeout(900)                                  # the card has finished coming in
        return page.evaluate(STATE)

    T = f"{kind}: "
    # ---- first visit
    page = fresh()
    page.goto(a.url, wait_until="domcontentloaded")
    s = page.evaluate(STATE)
    check(T + "the embed is on the page and the page is seen first", bool(s) and not s["shown"] and not s["pill"], "no announcement found" if not s else "")
    if not s:
        br.close(); return
    page.wait_for_selector(".ha-ann.is-open", timeout=20000); page.wait_for_timeout(900)
    s = page.evaluate(STATE)
    check(T + "the dialog opens on a first visit, on top of the page, inside the window", s["open"] and s["inBody"] and s["top"] and s["xTop"] and s["card"][0] >= 12 and s["card"][1] >= 12 and s["card"][2] <= s["win"][0] - 12 and s["card"][3] <= s["win"][1] - 12, f"card {s['card']} in {s['win']}")
    check(T + "it is a labelled modal dialog and the focus is in it", s["role"] == "dialog" and s["modal"] == "true" and s["label"] == TITLE and "ha-card" in s["focus"], f"{s['role']}, {s['label']!r}, focus on {s['focus']!r}")
    check(T + "its link leads to the dataset on the Data page", s["href"].endswith("/data#wq") and s["pillHref"].endswith("/data#wq"), s["href"])
    check(T + "it is remembered as seen at once", s["state"] == {"id": ID, "seen": True}, s["state"])
    check(T + "beside the text it plays the upright loop", s["loop"] == "wq-tall-v1" and s["sources"] == ["wq-tall-v1.webm", "wq-tall-v1.mp4"], f"{s['loop']} {s['sources']}")
    caps, months, wrong, times = [], set(), [], []
    for _ in range(115):                                            # a little more than one turn of the loop
        q = page.evaluate("""() => { const r = document.getElementById('ha-ann'), m = r.querySelector('.ha-months'), v = r.querySelector('video');
            return [v.currentTime, r.querySelector('.ha-cap').textContent, m.classList.contains('is-on') ? [...m.children].findIndex((i) => i.classList.contains('is-on')) + 1 : 0]; }""")
        times.append(q[0])
        if q[1] not in caps:
            caps.append(q[1])
        if q[2]:
            months.add(q[2])
            if q[1] != "Chlorophyll-a through the year":
                wrong.append(q)
        page.wait_for_timeout(100)
    plays = max(times) - min(times) > 3
    if not plays and page.evaluate(STATE)["err"]:
        print(f"note {T}this browser build cannot decode the loop here; the still picture is shown (captions and months not checked)", flush=True)
    else:
        check(T + "the loop plays", plays, f"{min(times):.2f} to {max(times):.2f} s")
        check(T + "every caption is shown in its turn", sorted(caps) == sorted(CAPS), f"{len(caps)} of {len(CAPS)}")
        check(T + "all twelve months are lit, only while the year plays", months == set(range(1, 13)) and not wrong, f"{sorted(months)}; out of place: {wrong[:2]}")
    box = s["media"]
    page.mouse.move((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    page.mouse.wheel(0, 700); page.wait_for_timeout(350)
    page.keyboard.press("PageDown"); page.keyboard.press("End"); page.wait_for_timeout(350)
    check(T + "the page behind stays where it is (wheel, PageDown, End)", page.evaluate("window.scrollY") == 0, page.evaluate("window.scrollY"))
    order = []
    for _ in range(4):
        page.keyboard.press("Tab")
        order.append(page.evaluate("document.activeElement.className.split(' ')[0]"))
    page.keyboard.press("Shift+Tab")
    order.append(page.evaluate("document.activeElement.className.split(' ')[0]"))
    check(T + "Tab goes round inside the dialog", order == ["ha-x", "ha-cta", "ha-later", "ha-x", "ha-later"], order)
    page.keyboard.press("Escape"); page.wait_for_timeout(900)
    s = page.evaluate(STATE)
    check(T + "Escape closes it and the pill comes in", not s["shown"] and s["pill"], f"dialog shown {s['shown']}, pill {s['pill']}")
    page.mouse.wheel(0, 700); page.wait_for_timeout(500)
    check(T + "the page scrolls again afterwards", page.evaluate("window.scrollY") > 0)
    # ---- later visits
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(2600)
    s = page.evaluate(STATE)
    check(T + "on a later visit there is no dialog, only the pill", not s["shown"] and s["pill"])
    page.click(".ha-pill-x"); page.wait_for_timeout(800)
    s = page.evaluate(STATE)
    check(T + "the pill can be hidden, and that is remembered", not s["pill"] and s["state"] == {"id": ID, "seen": True, "pillHidden": True}, s["state"])
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(2600)
    s = page.evaluate(STATE)
    check(T + "after that neither shows", not s["shown"] and not s["pill"])
    page.context.close()
    # ---- ways out
    page = fresh(); opened(page)
    page.click(".ha-later"); page.wait_for_timeout(900)
    s = page.evaluate(STATE)
    check(T + "'Maybe later' closes it", not s["shown"] and s["pill"])
    page.context.close()
    page = fresh(); opened(page)
    page.mouse.click(8, 450); page.wait_for_timeout(900)
    s = page.evaluate(STATE)
    check(T + "a click beside the card closes it", not s["shown"] and s["pill"])
    page.context.close()
    page = fresh(); opened(page)
    page.mouse.click(700, 450); page.wait_for_timeout(600)
    check(T + "a click on the card does not", page.evaluate(STATE)["open"])
    page.route("**/data", lambda r: r.fulfill(status=200, content_type="text/html", body="<title>data</title>"))   # the click is what is checked, not the Data page
    page.click(".ha-cta"); page.wait_for_url("**/data#wq", timeout=20000)
    page.unroute("**/data")
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(2600)
    s = page.evaluate(STATE)
    check(T + "the link leads to /data#wq, and whoever follows it is not shown the pill again", not s["shown"] and not s["pill"] and bool(s["state"]) and s["state"].get("pillHidden") is True, s["state"])
    page.context.close()
    # ---- narrow
    page = fresh(390, 844)
    s = opened(page)
    mw, mh = s["media"][2] - s["media"][0], s["media"][3] - s["media"][1]
    check(T + "narrow: the picture is on top, 16:9, with the Data page card's loop", s["loop"] == "wq-v1" and s["media"][3] <= s["cta"][1] and abs(mw / mh - 16 / 9) < 0.03, f"{s['loop']}, picture {mw} x {mh}")
    check(T + "narrow: nothing is wider than the window and the whole card is in it", s["docW"] <= s["win"][0] and s["card"][0] >= 0 and s["card"][2] <= s["win"][0] and s["card"][3] <= s["win"][1] and s["body"][0] <= s["body"][1] + 1, f"card {s['card']} in {s['win']}, text {s['body']}")
    page.wait_for_timeout(7000)
    check(T + "narrow: the months are in the picture, not drawn twice", page.evaluate(STATE)["month"] == 0)
    page.context.close()
    # ---- sizes
    for w, h in SIZES:
        page = fresh(w, h)
        s = opened(page)
        inside = s["card"][0] >= 12 and s["card"][1] >= 12 and s["card"][2] <= w - 12 and s["card"][3] <= h - 12 and s["docW"] <= w and s["xTop"]
        scrolls = s["body"][0] > s["body"][1] + 1
        reach = s["cta"][3] <= s["card"][3] and s["cta"][1] >= s["media"][3 if STACKED(w, h) else 1]      # in view without scrolling
        if scrolls:                                                 # then the last line of text must come clear of the buttons
            page.evaluate("document.querySelector('.ha-body').scrollTop = 1e6"); page.wait_for_timeout(150)
            reach = reach and page.evaluate("document.querySelector('.ha-status').getBoundingClientRect().bottom <= document.querySelector('.ha-cta').getBoundingClientRect().top")
        on_top = s["media"][3] <= s["body_top"] + 1 and s["media"][2] - s["media"][0] > (s["card"][2] - s["card"][0]) * 0.9
        fits = on_top == STACKED(w, h) and s["loop"] == ("wq-v1" if on_top else "wq-tall-v1")
        check(T + f"{w} x {h}: the card is inside the window, the button is in view, the loop fits the layout", inside and reach and fits,
              f"card {s['card']}, picture {'on top' if on_top else 'beside'} {s['media'][2] - s['media'][0]} x {s['media'][3] - s['media'][1]}, {'text scrolls' if scrolls else 'all in view'}, {s['loop']}")
        if a.shots and kind == "chromium":
            Path(a.shots).mkdir(parents=True, exist_ok=True)
            page.evaluate("document.querySelector('.ha-body').scrollTop = 0")
            page.wait_for_timeout(2500)
            page.screenshot(path=f"{a.shots}/dialog_{w}x{h}.png")
        page.context.close()
    # ---- turning the window while it is open
    page = fresh(1200, 900); opened(page)
    page.set_viewport_size({"width": 700, "height": 900}); page.wait_for_timeout(700)
    n = page.evaluate(STATE)["loop"]
    page.set_viewport_size({"width": 1200, "height": 900}); page.wait_for_timeout(700)
    check(T + "when the window is made narrow and wide again the loop follows the layout", (n, page.evaluate(STATE)["loop"]) == ("wq-v1", "wq-tall-v1"), n)
    page.context.close()
    # ---- kindness
    page = fresh(reduced_motion="reduce")
    asked = []
    page.on("request", lambda r: asked.append(r.url.split("/")[-1]) if "/media/" in r.url else None)
    s = opened(page); page.wait_for_timeout(1500)
    s = page.evaluate(STATE)
    check(T + "reduced motion: a still picture with its caption, no video fetched", s["open"] and not s["sources"] and s["t"] == 0 and s["cap"] == CAPS[0] and not [u for u in asked if not u.endswith(".jpg")] and "wq-tall-v1.jpg" in asked, asked)
    page.context.close()
    page = fresh(init="Object.defineProperty(window, 'localStorage', { get() { throw new Error('storage is blocked'); } });")
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(3000)
    s = page.evaluate(STATE)
    check(T + "storage blocked: no dialog that would return on every visit, the pill only", not s["shown"] and s["pill"])
    page.context.close()
    page = fresh(init="Date.now = () => new Date('2027-03-01T00:00:01+09:00').getTime();")
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(3000)
    s = page.evaluate(STATE)
    check(T + "past its last day (28 February 2027) nothing shows", not s["shown"] and not s["pill"])
    page.context.close()
    page = fresh(init="Date.now = () => new Date('2027-02-28T23:00:00+09:00').getTime();")
    page.goto(a.url, wait_until="load"); page.wait_for_selector(".ha-ann.is-open", timeout=20000)
    check(T + "on its last day it still does", True)
    page.context.close()
    page = fresh(init="window.__vis = 'hidden'; Object.defineProperty(Document.prototype, 'visibilityState', { get() { return window.__vis; }, configurable: true });")
    page.goto(a.url, wait_until="load"); page.wait_for_timeout(3000)
    before = page.evaluate(STATE)["shown"]
    page.evaluate("window.__vis = 'visible'; document.dispatchEvent(new Event('visibilitychange'));")
    page.wait_for_selector(".ha-ann.is-open", timeout=20000)
    check(T + "in a tab opened in the background it waits until the tab is looked at", not before)
    page.context.close()
    check(T + "no script error", not errors, errors[:3])
    br.close()


with sync_playwright() as pw:
    for kind in a.browsers.split(","):
        run(pw, kind.strip())
print(f"{failed} failed", flush=True)
sys.exit(failed)
