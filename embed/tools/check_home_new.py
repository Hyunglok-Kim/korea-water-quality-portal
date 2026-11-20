#!/usr/bin/env python3
"""check_home_new.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the home page's three new blocks, checked.

    python embed/tools/check_home_new.py                         # the local preview (home_new_preview.py, port 8814)
    python embed/tools/check_home_new.py https://hydroai.net/    # the live page (the blocks are on it since 2026-11-20)

What it looks at, in each browser:
  the page      one <h1>; the three blocks are there and what they replace is gone; no script error; nothing wider than the window;
                without scripts the words and still pictures remain and what needs scripts is left out
  the picture   the satellites behind the first screen: there, loaded, behind everything, not in the way of a click; the page
                is whole without it; and at every size the words on it can be read (contrast against the brightest of what
                lies behind each line, measured on a picture of the page with the letters taken out)
  the reel      the datasets in the order the lab head asked for (soil moisture, ET, SMAP error, validation site, water quality),
                the new one marked when it is on show; the first loop plays with its captions; each follows the one before;
                the larger loop on a dense desktop screen, the card's own on a phone or when the larger cannot be fetched;
                a click on a bar (also right after a change, on a loop slow to arrive, and back to the dataset just left),
                pause and play, a hidden tab, scrolling away; loops that cannot be fetched do not hold it;
                with reduced motion no video is fetched until play is pressed; the block keeps its height as datasets change
  the lists     three news entries and three papers, the same as the first entries of /events and /publication;
                every picture whole and in its own proportions, its frame the picture's own, nothing behind it
                (at three widths), and a quiet box where a picture cannot be fetched;
                either page unreadable -> that list is left out; both -> the block is
  the section   one language at a time, chosen by the browser's language, switched and remembered;
                every sentence of the recruiting list that the block replaced is still on the page, in the folded call
  the sizes     thirteen window sizes from 2048 px down to a 320 px phone
The exit status is the number of failures. Needs playwright with the three browsers installed, and Pillow.
"""
import argparse
import io
import re
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("url", nargs="?", default="http://127.0.0.1:8814/")
ap.add_argument("--browsers", default="chromium,webkit,firefox")
ap.add_argument("--shots", help="a folder for pictures of every size")
ap.add_argument("--quick", action="store_true", help="leave out the slow tests (loops that cannot be fetched)")
a = ap.parse_args()
URL = a.url if a.url.endswith("/") else a.url + "/"
HOME = Path(__file__).resolve().parents[1] / "home"
FAILS = 0

# the reel's datasets in the page's order: id, title, link, the card loop's file, the larger loop's file, marked new
SLIDES = [("hdca", "Hybrid Dual-Channel Algorithm (HDCA)", "/data#hdca", "hdca-v3", "hdca-wide-v1", False),
          ("et", "Global 30m-ET", "/data#et", "et-v2", "et-wide-v1", False),
          ("tca", "SMAP Time-Variant Error", "/data#tca", "tca-v2", "tca-wide-v1", False),
          ("cvs", "NASA-GIST Core Validation Site", "/data#cvs", "cvs", "cvs-wide-v1", False),
          ("wq", "Inland Water Quality of South Korea", "/data#wq", "wq-v1", "wq-wide-v1", True)]
IDS = [x[0] for x in SLIDES]
FIRST_CAPS = {"Soil moisture, 2015-2025 mean", "Into the Amazon basin", "Amazon basin: wet and dry seasons, 2015-2025"}     # the first dataset's
SIZES = [(2048, 970), (1680, 1050), (1440, 900), (1280, 720), (1200, 800), (1100, 700), (1024, 768), (960, 600), (834, 1194), (768, 1024), (600, 900), (390, 844), (320, 568)]

REEL = """() => {
  const vids = [...document.querySelectorAll('.hh-reel-stage video')].map(v => ({ id: v.dataset.id || '', on: v.classList.contains('is-on'), paused: v.paused, t: v.currentTime, dur: v.duration || 0, rate: v.playbackRate, src: v.currentSrc.split('/').pop(), px: v.videoWidth }));
  const tabs = [...document.querySelectorAll('.hh-reel-tab')];
  const front = vids.find(v => v.on) || null;
  return { vids, front, n: tabs.length, cur: tabs.findIndex(t => t.getAttribute('aria-current') === 'true'),
    bars: tabs.map(t => +(t.firstChild.style.transform.replace(/[^0-9.]/g, '') || 0)),
    title: document.querySelector('.hh-reel-title').textContent, cap: document.querySelector('.hh-reel-cap').textContent,
    href: document.querySelector('.hh-reel-go').getAttribute('href'), stageHref: document.querySelector('.hh-reel-stage').getAttribute('href'),
    isNew: !document.querySelector('.hh-reel-new').hidden, poster: document.querySelector('.hh-reel-stage').style.backgroundImage,
    button: document.querySelector('.hh-reel-pause').getAttribute('aria-label'), heroH: Math.round(document.querySelector('.hh-hero').getBoundingClientRect().height) };
}"""
FAST = "(() => { const play = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { try { this.playbackRate = 5; } catch (e) {} return play.apply(this, arguments); }; })()"


def ok(name, cond, detail=""):
    global FAILS
    if not cond:
        FAILS += 1
    print(("    ok    " if cond else "    FAIL  ") + name + (f"   [{detail}]" if detail != "" and not cond else ""), flush=True)
    return cond


def norm(s):
    return re.sub(r"[\W_]+", "", s, flags=re.UNICODE).lower()


def open_page(br, w=1440, h=900, locale="en-US", init=None, route=None, **kw):
    ctx = br.new_context(viewport={"width": w, "height": h}, locale=locale, **kw)
    if init:
        ctx.add_init_script(init)
    page = ctx.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    if route:
        route(page)
    page.goto(URL, wait_until="load", timeout=60000)
    return ctx, page


def wait_reel(page, cond, timeout=15000):
    try:
        page.wait_for_function("(c) => { const s = (" + REEL + ")(); return eval(c); }", arg=cond, timeout=timeout)
        return True
    except Exception:
        return False


def luminance(rgb):
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])


LINES = """() => { const out = [], hb = document.querySelector('#hh-hero').getBoundingClientRect();
  for (const s of ['.hh-eyebrow', '.hh-hero-title', '.hh-hero-lead', '.hh-btn-ghost', '.hh-reel-tab span', '.hh-reel-title', '.hh-reel-desc', '.hh-reel-go'])
    for (const e of document.querySelectorAll(s)) {
      const cs = getComputedStyle(e); if (cs.display === 'none' || !e.getClientRects().length) continue;
      const m = cs.color.match(/[\\d.]+/g).map(Number), range = document.createRange(); range.selectNodeContents(e);
      for (const r of range.getClientRects()) if (r.width > 3 && r.height > 3) out.push({ s, x: r.left - hb.left, y: r.top - hb.top, w: r.width, h: r.height, color: m, size: parseFloat(cs.fontSize), weight: +cs.fontWeight || 400 });
    }
  return { lines: out, width: hb.width }; }"""
# for the measurement: the letters taken out (their shadows stay), the mark beside "new" and the site's fixed bar out of the way
NO_LETTERS = "#hh-hero, #hh-hero * { -webkit-text-fill-color: transparent !important; } #hh-hero .hh-reel-tab b, .navbar { visibility: hidden !important; }"


def unreadable(page):
    """The lines of the first screen's words whose contrast against what lies behind them is under WCAG's 4.5 : 1 (3 : 1 for
    large text): the block is pictured with the letters taken out, and each line's colour is compared with the brightest
    of what its box holds (the 97th percentile, so that a single star does not decide it)."""
    page.evaluate("window.scrollTo(0, 0)")
    tag = page.add_style_tag(content=NO_LETTERS)
    page.wait_for_timeout(120)
    got = page.evaluate(LINES)
    for attempt in range(3):                               # a large picture of a page sometimes fails once under software drawing
        try:
            im = Image.open(io.BytesIO(page.locator("#hh-hero").screenshot())).convert("RGB")
            break
        except Exception:
            if attempt == 2:
                raise
            page.wait_for_timeout(500)
    tag.evaluate("e => e.remove()")
    k = im.width / got["width"]
    low = []
    for ln in got["lines"]:
        x0, y0 = max(0, int(ln["x"] * k)), max(0, int(ln["y"] * k))
        box = im.crop((x0, y0, min(im.width, max(x0 + 1, int((ln["x"] + ln["w"]) * k))), min(im.height, max(y0 + 1, int((ln["y"] + ln["h"]) * k)))))
        data = sorted(box.get_flattened_data() if hasattr(box, "get_flattened_data") else box.getdata(), key=luminance)     # Pillow 12.1 renamed it
        if not data:
            continue
        back, mid = luminance(data[min(len(data) - 1, int(len(data) * 0.97))]), data[len(data) // 2]
        al = ln["color"][3] if len(ln["color"]) > 3 else 1
        text = luminance([ln["color"][i] * al + mid[i] * (1 - al) for i in range(3)])
        ratio = (max(text, back) + 0.05) / (min(text, back) + 0.05)
        need = 3.0 if ln["size"] >= 24 or (ln["size"] >= 18.66 and ln["weight"] >= 700) else 4.5
        if ratio < need:
            low.append((ln["s"], round(ratio, 2), need, int(ln["x"]), int(ln["y"])))
    return low


def without_scripts(br):
    print("  without scripts")
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(URL, wait_until="load", timeout=60000)
    seen = lambda sel: page.locator(sel).first.is_visible()
    ok("the title, the first dataset's still picture and words, and both languages of the section are there", seen(".hh-hero-title") and seen(".hh-reel-stage") and seen(".hh-reel-title") and seen('.hh-about-h2[data-l="en"]') and seen('.hh-about-h2[data-l="ko"]'))
    ok("what needs scripts is left out (the bars, the two lists, the language buttons)", not seen(".hh-reel-tabs") and not seen("#hh-latest") and not seen(".hh-lang"))
    r = page.evaluate("""() => ({ title: document.querySelector('.hh-reel-title').textContent, href: document.querySelector('.hh-reel-go').getAttribute('href'),
      stage: document.querySelector('.hh-reel-stage').getAttribute('href'), still: document.querySelector('.hh-reel-stage').getAttribute('style'),
      isNew: !document.querySelector('.hh-reel-new').hidden, sky: (i => i.complete && i.naturalWidth > 0 && getComputedStyle(i).opacity === '1')(document.querySelector('.hh-hero-sky img')),
      desc: document.querySelector('.hh-reel-desc').textContent.trim(), script: document.querySelector('#hh-hero').parentNode.querySelector('script').textContent })""")
    ok("the words and still picture in the page itself are the first dataset's (soil moisture)", r["title"] == SLIDES[0][1] and r["href"] == SLIDES[0][2] and r["stage"] == SLIDES[0][2] and SLIDES[0][3] + ".jpg" in r["still"] and r["isNew"] == SLIDES[0][5],
       {k: v for k, v in r.items() if k != "script"})
    listed = re.search(r"id: 'hdca'.*?desc: '([^']*)'", r["script"], re.S)
    ok("its line says the data are over dense vegetation, the same words in the page itself and in the reel's list", "over dense vegetation" in r["desc"] and listed is not None and listed.group(1) == r["desc"],
       (r["desc"], listed.group(1) if listed else None))
    ok("the picture of the satellites is there without scripts too", r["sky"], r)
    ctx.close()


def the_page(br):
    print("  the page")
    ctx, page = open_page(br)
    page.wait_for_timeout(1500)
    r = page.evaluate("""() => ({
      h1: [...document.querySelectorAll('h1')].map(h => h.textContent.replace(/\\s+/g, ' ').trim()),
      blocks: ['#hh-hero', '#hh-latest', '#hh-about'].map(s => !!document.querySelector(s)),
      inEmbeds: ['#hh-hero', '#hh-latest', '#hh-about'].map(s => !!document.querySelector('.w-embed ' + s)),
      old: ['.hero-block', '.home-subittle', '.usps-block > p.paragraph', '.image-28', '.image-32'].filter(s => document.querySelector(s)),
      heroParent: document.querySelector('#hh-hero').closest('.teaching-detail-wrap.hero') !== null,
      firstSection: ['#hh-latest', '#hh-about'].map(s => document.querySelector(s).closest('.section.hero-home') !== null),
      tiles: document.querySelectorAll('.usps-block .step-tile').length,
      words: ['Rede more', 'improvments', 'technics'].filter(w => document.body.innerText.includes(w)),
      links: [...document.querySelectorAll('.hh-hero-actions a')].map(x => x.getAttribute('href')),
      over: document.documentElement.scrollWidth - window.innerWidth })""")
    ok("one <h1>, the lab's title", r["h1"] == ["Hydrology with AI and Remote Sensing"], r["h1"])
    ok("the three blocks are on the page, each in a Code Embed", all(r["blocks"]) and all(r["inEmbeds"]), r)
    ok("the hero block is in the hero's container; the other two close the first section", r["heroParent"] and all(r["firstSection"]), r)
    ok("what they replace is gone (old hero text, photographs, long paragraph)", r["old"] == [], r["old"])
    ok("the four tiles are still there", r["tiles"] == 4, r["tiles"])
    ok("the misspellings are gone from the page's words", r["words"] == [], r["words"])
    ok("the two buttons lead to Data and Opportunities", r["links"] == ["/data", "/opportunities"], r["links"])
    ok("nothing is wider than the window", r["over"] <= 0, r["over"])
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def the_reel(br):
    print("  the reel")
    media = []
    ctx, page = open_page(br, route=lambda p: p.on("request", lambda q: media.append(q.url) if re.search(r"\.(webm|mp4)(\?|$)", q.url) else None))
    ok("the first loop starts by itself", wait_reel(page, f"s.front && s.front.id === '{IDS[0]}' && !s.front.paused && s.front.t > 0.3", 12000))
    s = page.evaluate(REEL)
    ok("five datasets, soil moisture first, on show", s["n"] == 5 and s["cur"] == 0 and s["isNew"] == SLIDES[0][5] and s["title"] == SLIDES[0][1], s)
    ok("its link and its still picture", s["href"] == SLIDES[0][2] and s["stageHref"] == SLIDES[0][2] and SLIDES[0][3] + ".jpg" in s["poster"], s)
    names = page.evaluate("() => [...document.querySelectorAll('.hh-reel-tab')].map(t => [t.getAttribute('aria-label'), !!t.querySelector('b')])")
    ok("the bars are in the order asked for, the new dataset's bar marked", names == [["Show " + x[1], x[5]] for x in SLIDES], names)
    ok("only the loop on show has been fetched", len({u.split("/")[-1].split(".")[0] for u in media}) == 1, media)
    seen = set()
    for _ in range(60):                                   # the captions over the first loop
        st = page.evaluate(REEL)
        if st["cur"] != 0:
            break
        seen.add(st["cap"])
        page.wait_for_timeout(190)
    ok("every caption of the first loop is shown", FIRST_CAPS <= seen, sorted(FIRST_CAPS - seen))
    ok("when it ends the second dataset comes, its loop playing", wait_reel(page, f"s.cur === 1 && s.front && s.front.id === '{IDS[1]}' && !s.front.paused && s.front.t > 0.2", 16000))
    s = page.evaluate(REEL)
    ok("its words, link and bars", s["title"] == SLIDES[1][1] and s["href"] == SLIDES[1][2] and s["isNew"] == SLIDES[1][5] and s["bars"][0] == 1 and 0 < s["bars"][1] < 1 and s["bars"][2] == 0, s)
    ok("only one video is visible", sum(v["on"] for v in s["vids"]) == 1, s["vids"])

    page.click(".hh-reel-tab:nth-child(4)")                # a bar
    ok("a click on the fourth bar shows the fourth dataset", wait_reel(page, f"s.cur === 3 && s.front && s.front.id === '{IDS[3]}' && !s.front.paused && s.front.t > 0.2", 12000))
    s = page.evaluate(REEL)
    ok("with its words", s["title"] == SLIDES[3][1] and s["href"] == SLIDES[3][2] and s["bars"][:3] == [1, 1, 1], s)

    page.click(".hh-reel-pause")                           # pause, play
    page.wait_for_timeout(400)
    s1 = page.evaluate(REEL)
    page.wait_for_timeout(1200)
    s2 = page.evaluate(REEL)
    ok("pause stops the loop where it is", all(v["paused"] for v in s2["vids"]) and abs(s2["front"]["t"] - s1["front"]["t"]) < 0.05 and s2["button"] == "Play the pictures", (s1["front"], s2["front"], s2["button"]))
    page.click(".hh-reel-pause")
    ok("play goes on from there, the same loop", wait_reel(page, f"s.cur === 3 && s.front && s.front.id === '{IDS[3]}' && !s.front.paused && s.front.t > {s2['front']['t'] + 0.3}", 6000))
    ok("the button says pause again", page.evaluate(REEL)["button"] == "Pause the pictures")
    new = [i for i, x in enumerate(SLIDES) if x[5]][0]     # the new dataset is marked when it is on show, and only then
    page.click(f".hh-reel-tab:nth-child({new + 1})")
    ok("the new dataset, last in the row, is marked new when it is on show", wait_reel(page, f"s.cur === {new} && s.isNew && s.front && s.front.id === '{IDS[new]}' && !s.front.paused", 12000), page.evaluate(REEL))
    page.click(".hh-reel-tab:nth-child(2)")                # a long pause is not taken for a loop that has stalled
    wait_reel(page, f"s.cur === 1 && s.front && s.front.id === '{IDS[1]}' && !s.front.paused && s.front.t > 0.5", 12000)
    ok("and the mark goes when another is", not page.evaluate(REEL)["isNew"])
    page.click(".hh-reel-pause")
    t0 = page.evaluate(REEL)["front"]["t"]
    page.wait_for_timeout(9500)
    page.click(".hh-reel-pause")
    page.wait_for_timeout(1200)
    s3 = page.evaluate(REEL)
    ok("after a pause of ten seconds play goes on with the same dataset", s3["cur"] == 1 and s3["front"] and s3["front"]["id"] == IDS[1] and not s3["front"]["paused"] and t0 < s3["front"]["t"] < t0 + 2.5, (t0, s3["cur"], s3["front"]))

    page.evaluate("Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' }); document.dispatchEvent(new Event('visibilitychange'));")
    page.wait_for_timeout(500)
    ok("a hidden tab stops it", all(v["paused"] for v in page.evaluate(REEL)["vids"]))
    page.evaluate("Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' }); document.dispatchEvent(new Event('visibilitychange'));")
    ok("coming back starts it", wait_reel(page, "s.front && !s.front.paused", 6000))

    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    ok("scrolled away, it stops", wait_reel(page, "s.vids.every(v => v.paused)", 6000))
    page.evaluate("window.scrollTo(0, 0)")
    ok("scrolled back, it plays", wait_reel(page, "s.front && !s.front.paused", 6000))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()

    # a bar clicked while the change before it is still dissolving (the picture before takes 0.65 s to go) must get its
    # loop all the same. On the live page on 2026-11-20 such a click, on a loop that took longer than that to arrive,
    # left the loop before it playing under the new words; so the fourth dataset's loop is held back a second here.
    def late(route):
        time.sleep(1.0)
        route.continue_()
    ctx, page = open_page(br, route=lambda p: p.route(re.compile("/" + IDS[3] + r"[^/]*\.(webm|mp4)"), late))
    wait_reel(page, f"s.front && s.front.id === '{IDS[0]}' && !s.front.paused && s.front.t > 0.3", 12000)
    quick = """([after, then]) => { let done = false; document.querySelectorAll('.hh-reel-stage video').forEach(v => v.addEventListener('playing', () => {
        if (!done && v.getAttribute('data-id') === after) { done = true; setTimeout(() => document.querySelectorAll('.hh-reel-tab')[then].click(), 200); } })); }"""
    page.evaluate(quick, [IDS[1], 3])                      # the second dataset, and 0.2 s after it shows, the fourth
    page.click(".hh-reel-tab:nth-child(2)")
    ok("a bar clicked 0.2 s after a change gets its loop, though the loop is slow to arrive", wait_reel(page, f"s.cur === 3 && s.front && s.front.id === '{IDS[3]}' && !s.front.paused && s.front.t > 0.2", 10000), page.evaluate(REEL))
    page.evaluate(quick, [IDS[2], 3])                      # the third, and 0.2 s after it shows, back to the fourth, whose video is still fading out
    page.click(".hh-reel-tab:nth-child(3)")
    ok("and so does the bar of the dataset just left", wait_reel(page, f"s.cur === 3 && s.front && s.front.id === '{IDS[3]}' && !s.front.paused && s.front.t > 0.2 && s.vids.filter(v => v.on).length === 1", 10000), page.evaluate(REEL))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()

    # all five in turn and round to the first again, at five times the speed
    ctx, page = open_page(br, init=FAST)
    order, last, t0 = [], None, 0
    for _ in range(140):
        s = page.evaluate(REEL)
        if s["front"] and not s["front"]["paused"] and s["front"]["t"] > 0.2 and s["front"]["id"] != last:
            last = s["front"]["id"]
            order.append(last)
            if len(order) == 6:
                break
        page.wait_for_timeout(150)
    ok("all five loops play in turn, in the order asked for, and the first comes round again", order == IDS + IDS[:1], order)
    s = page.evaluate(REEL)
    ok("the bars start again with it", s["cur"] == 0 and s["bars"][1:] == [0, 0, 0, 0], s["bars"])
    heights = set()
    for i in range(5):
        page.click(f".hh-reel-tab:nth-child({i + 1})")
        page.wait_for_timeout(80)
        heights.add(page.evaluate(REEL)["heroH"])
    ok("the block keeps its height from one dataset to the next", len(heights) == 1, heights)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


SKY = """() => { const h = document.querySelector('#hh-hero'), box = document.querySelector('.hh-hero-sky'), i = box.querySelector('img');
  const hb = h.getBoundingClientRect(), ib = i.getBoundingClientRect(), cs = getComputedStyle(box);
  // a click in the middle of each of these must reach it, not the picture (each is brought into the window first)
  const hit = (sel) => { const e = document.querySelector(sel); window.scrollTo(0, e.getBoundingClientRect().top + scrollY - innerHeight / 2); const b = e.getBoundingClientRect();
    const t = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); return !!t && t.closest(sel) !== null; };
  const out = { loaded: i.complete && i.naturalWidth > 0, px: [i.naturalWidth, i.naturalHeight], src: i.currentSrc.split('/').pop(), alt: i.getAttribute('alt'), hidden: box.getAttribute('aria-hidden'),
    opacity: getComputedStyle(i).opacity, z: cs.zIndex, events: cs.pointerEvents, covers: ib.left <= hb.left + 0.5 && ib.top <= hb.top + 0.5 && ib.right >= hb.right - 0.5,
    reaches: (ib.bottom - hb.top) / hb.height, over: document.documentElement.scrollWidth - innerWidth,
    bg: getComputedStyle(h).backgroundImage.includes('gradient'), clip: getComputedStyle(h).overflow,
    hit: ['.hh-btn-primary', '.hh-btn-ghost', '.hh-reel-stage', '.hh-reel-tab', '.hh-reel-pause', '.hh-reel-go'].map(hit) };
  // the pools behind the words reach past the panel's foot: asking for a link to be brought to the middle must not move the panel's own content
  document.querySelector('.hh-reel-go').scrollIntoView({ block: 'center', behavior: 'instant' }); out.shifted = h.scrollTop + h.scrollLeft;
  h.scrollTop = 0; h.scrollLeft = 0; window.scrollTo(0, 0); return out; }"""


def the_sky(br):
    print("  the picture behind the first screen")
    asked = []
    ctx, page = open_page(br, route=lambda p: p.on("request", lambda q: asked.append(q.url) if "home-sky" in q.url else None))
    page.wait_for_function("(i => i.complete && i.naturalWidth > 0)(document.querySelector('.hh-hero-sky img'))", timeout=20000)
    page.wait_for_timeout(1500)                            # it fades in
    r = page.evaluate(SKY)
    ok("the picture of the satellites is behind the first screen, loaded once, 1500 px wide", r["loaded"] and r["px"] == [1500, 1125] and len(asked) == 1 and r["opacity"] == "1", (r["px"], asked, r["opacity"]))
    ok("it is decoration: no words for a screen reader, behind everything, not in the way of a click", r["alt"] == "" and r["hidden"] == "true" and r["z"] == "-1" and r["events"] == "none" and all(r["hit"]), r)
    ok("the panel cannot be scrolled inside itself (it clips what reaches past it)", r["shifted"] == 0, r["shifted"])
    ok("across the whole panel on a wide window, and it widens nothing", r["covers"] and r["reaches"] > 0.99 and r["over"] <= 0 and r["clip"] in ("clip", "hidden"), r)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(300)
    r = page.evaluate(SKY)
    ok("on a phone: across the top, behind the words, gone before the pictures", r["covers"] and 0.4 < r["reaches"] < 0.75 and r["over"] <= 0 and all(r["hit"]) and r["shifted"] == 0, r)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()
    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"home-sky"), lambda q: q.abort()))
    page.wait_for_timeout(1500)
    r = page.evaluate(SKY)
    ok("the picture cannot be fetched: the panel is as it was, dark, and the reel goes on", (not r["loaded"]) and r["bg"] and wait_reel(page, "s.front && !s.front.paused && s.front.t > 0.2", 12000), r)
    low = unreadable(page)
    ok("and its words are still readable", low == [], low)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def two_sizes(br):
    print("  the loops in two sizes")
    ctx, page = open_page(br, 1440, 900, device_scale_factor=2)
    ok("a dense desktop screen: the loop starts", wait_reel(page, "s.front && !s.front.paused && s.front.t > 0.2 && s.front.px > 0", 15000))
    s = page.evaluate(REEL)
    ok("and it is the larger one (1536 px), with the larger still picture", s["front"] and s["front"]["src"].startswith(SLIDES[0][4] + ".") and s["front"]["px"] == 1536 and SLIDES[0][4] + ".jpg" in s["poster"], (s["front"], s["poster"]))
    ctx.close()
    ctx, page = open_page(br, 1440, 900, device_scale_factor=2, route=lambda p: p.route(re.compile(r"-wide-v\d+\.(webm|mp4)"), lambda r: r.abort()))
    ok("the larger loop cannot be fetched: the card's own plays instead", wait_reel(page, f"s.front && s.front.id === '{IDS[0]}' && !s.front.paused && s.front.t > 0.2 && s.front.px === 768", 15000), page.evaluate(REEL)["vids"])
    ctx.close()
    ctx, page = open_page(br, 390, 844, device_scale_factor=3)
    ok("a phone: the loop starts", wait_reel(page, "s.front && !s.front.paused && s.front.t > 0.2 && s.front.px > 0", 15000))
    s = page.evaluate(REEL)
    ok("and it is the card's own (768 px)", s["front"] and s["front"]["src"].startswith(SLIDES[0][3] + ".") and s["front"]["px"] == 768, s["front"])
    ctx.close()


def reel_without_loops(br):
    print("  the reel when the loops cannot be fetched")
    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"\.(webm|mp4)(\?|$)"), lambda r: r.abort()))
    page.wait_for_timeout(3000)
    s = page.evaluate(REEL)
    ok("the first still picture stays", s["cur"] == 0 and SLIDES[0][3] + ".jpg" in s["poster"] and not s["front"], s)
    ok("then the next dataset comes anyway", wait_reel(page, "s.cur === 1", 16000))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def reduced_motion(br):
    print("  reduced motion")
    media = []
    ctx, page = open_page(br, reduced_motion="reduce", route=lambda p: p.on("request", lambda q: media.append(q.url) if re.search(r"\.(webm|mp4)(\?|$)", q.url) else None))
    page.wait_for_timeout(2500)
    s = page.evaluate(REEL)
    ok("no video is fetched; the still picture and its words are there", media == [] and SLIDES[0][3] + ".jpg" in s["poster"] and s["title"] == SLIDES[0][1] and s["cap"] != "", (media, s))
    ok("the button offers to play", s["button"] == "Play the pictures")
    page.click(".hh-reel-tab:nth-child(3)")
    page.wait_for_timeout(600)
    s = page.evaluate(REEL)
    ok("a bar still changes the dataset, as a still picture", s["cur"] == 2 and s["title"] == SLIDES[2][1] and SLIDES[2][3] + ".jpg" in s["poster"] and media == [], (s, media))
    page.click(".hh-reel-pause")
    ok("pressing play starts that dataset's loop", wait_reel(page, f"s.front && s.front.id === '{IDS[2]}' && !s.front.paused && s.front.t > 0.2", 12000))
    r = page.evaluate("""() => ({ anim: getComputedStyle(document.querySelector('.hh-hero-copy > *')).animationName, rise: !!document.querySelector('.hh-anim'),
      words: getComputedStyle(document.querySelector('.hh-reel-info > *')).animationName, sky: parseFloat(getComputedStyle(document.querySelector('.hh-hero-sky img')).transitionDuration) })""")
    ok("nothing slides, rises or fades in", r["anim"] == "none" and not r["rise"] and r["words"] == "none" and r["sky"] == 0, r)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def first_entries(br, path, js):
    ctx = br.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(URL + path, wait_until="domcontentloaded", timeout=60000)
    out = page.evaluate(js)
    ctx.close()
    return out


# the lists' pictures: the room a picture has (a square of the column's width), and each frame with what it holds
THUMBS = """() => { const col = parseFloat(getComputedStyle(document.querySelector('#hh-latest')).getPropertyValue('--hh-t'));
  return { col, behind: document.querySelectorAll('#hh-latest .hh-thumb-bg').length,
    pics: [...document.querySelectorAll('#hh-latest .hh-item:not(.hh-wait) .hh-thumb')].map(t => { const i = t.querySelector('img'), b = t.getBoundingClientRect(), ib = i ? i.getBoundingClientRect() : null, row = t.closest('.hh-row');
      return { nat: i ? [i.naturalWidth, i.naturalHeight] : [0, 0], box: [b.width, b.height], img: ib ? [ib.width, ib.height] : [0, 0], left: b.left - row.getBoundingClientRect().left - parseFloat(getComputedStyle(row).paddingLeft),
        kids: t.children.length, back: getComputedStyle(t).backgroundImage, none: t.classList.contains('is-none') }; }) }; }"""


def whole(t):
    """Is every picture of the two lists shown whole: its frame the picture's own proportions and size, the longer side
    the column's width, flush with the list's left edge, nothing else in the frame or behind it?"""
    def one(p):
        (nw, nh), (bw, bh), (iw, ih) = p["nat"], p["box"], p["img"]
        if not (nw > 0 and nh > 0 and bh > 0):
            return False
        return (abs(bw - iw) <= 0.6 and abs(bh - ih) <= 0.6 and abs(bw / bh - nw / nh) <= 0.02 * nw / nh and abs(max(bw, bh) - t["col"]) <= 0.6
                and min(bw, bh) <= t["col"] + 0.6 and abs(p["left"]) <= 0.6 and p["kids"] == 1 and p["back"] == "none" and not p["none"])
    return t["behind"] == 0 and len(t["pics"]) == 6 and all(one(p) for p in t["pics"])


def the_lists(br):
    print("  news and publications")
    news = first_entries(br, "events", """() => [...(document.querySelector('.w-tab-pane') || document).querySelectorAll('.w-dyn-item')].slice(0, 3).map(it => ({
        title: [...it.querySelectorAll('.text-block-h3-style')].filter(b => !b.classList.contains('date'))[0].textContent.replace(/\\s+/g, ' ').trim(),
        href: it.querySelector('a[href*="/events/"]').getAttribute('href') }))""")
    pubs = first_entries(br, "publication", """() => [...(document.querySelector('.w-tab-pane') || document).querySelectorAll('.w-dyn-item')].slice(0, 3).map(it => ({
        title: it.querySelector('h3').textContent.replace(/\\s+/g, ' ').trim(), href: (it.querySelector('a[href]') || { getAttribute: () => '' }).getAttribute('href') }))""")
    asked = []
    ctx, page = open_page(br, route=lambda p: p.on("request", lambda q: asked.append(q.url) if re.search(r"/(events|publication)$", q.url) else None))
    page.wait_for_function("document.querySelector('#hh-latest').dataset.news !== undefined && document.querySelector('#hh-latest').dataset.pubs !== undefined", timeout=15000)
    page.evaluate("document.querySelector('#hh-latest').scrollIntoView()")
    page.wait_for_timeout(1500)
    r = page.evaluate("""() => { const rows = k => [...document.querySelectorAll('[data-hh="' + k + '"] .hh-item:not(.hh-wait) .hh-row')].map(a => ({
        title: a.querySelector('.hh-title').textContent, href: a.getAttribute('href'), target: a.getAttribute('target') || '', meta: (a.querySelector('.hh-meta') || {}).textContent || '',
        img: a.querySelector('img') ? a.querySelector('img').naturalWidth : 0, seen: getComputedStyle(a.closest('.hh-item')).opacity }));
      return { news: rows('news'), pubs: rows('pubs'), waiting: document.querySelectorAll('#hh-latest .hh-wait').length, hidden: document.querySelector('#hh-latest').hidden }; }""")
    ok("three news entries, the first three of the Events page, in its order", [x["title"] for x in r["news"]] == [x["title"] for x in news], ([x["title"][:30] for x in r["news"]], [x["title"][:30] for x in news]))
    ok("each leads to its own page", [x["href"] for x in r["news"]] == [x["href"] for x in news], [x["href"] for x in r["news"]])
    ok("three papers, the first three of the Publications page", [x["title"] for x in r["pubs"]] == [x["title"] for x in pubs], ([x["title"][:30] for x in r["pubs"]], [x["title"][:30] for x in pubs]))
    good = all((x["href"] == p["href"] and x["target"] == "_blank") if re.match(r"https?://", p["href"] or "") else (x["href"] == "/publication" and x["target"] == "") for x, p in zip(r["pubs"], pubs))
    ok("a paper with an address opens it in a new tab; one without leads to the Publications page", good, [(x["href"], x["target"]) for x in r["pubs"]])
    ok("every entry has its date and its picture", all(x["meta"] and x["img"] > 0 for x in r["news"] + r["pubs"]), [(x["meta"], x["img"]) for x in r["news"] + r["pubs"]])
    ok("the waiting rows are gone and the entries are visible", r["waiting"] == 0 and not r["hidden"] and all(x["seen"] == "1" for x in r["news"] + r["pubs"]), r["waiting"])
    pictures = page.evaluate("[...document.querySelectorAll('#hh-latest .hh-thumb img')].map(i => i.currentSrc || i.src)")
    for w, h in ((1440, 900), (1024, 768), (390, 844)):
        page.set_viewport_size({"width": w, "height": h})
        page.evaluate("document.querySelector('#hh-latest').scrollIntoView()")
        try:
            page.wait_for_function("(t => t.length === 6 && t.every(e => e.classList.contains('is-wide') || e.classList.contains('is-tall')))([...document.querySelectorAll('#hh-latest .hh-item:not(.hh-wait) .hh-thumb')])", timeout=15000)
        except Exception:
            pass
        page.wait_for_timeout(300)
        t = page.evaluate(THUMBS)
        ok(f"{w} px wide: every picture is whole and in its own proportions, its frame the picture's, nothing behind it", whole(t),
           (t["col"], t["behind"], [([round(v, 1) for v in p["box"]], p["nat"], round(p["left"], 1), p["kids"], p["back"][:20]) for p in t["pics"]]))
    page.set_viewport_size({"width": 1440, "height": 900})
    ok("each of the two pages was read once", len(asked) == 2, asked)
    page.reload(wait_until="load")
    page.wait_for_function("document.querySelector('#hh-latest').dataset.news === '3'", timeout=15000)
    ok("a second visit in the same tab re-uses what was read", len(asked) == 2, asked)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()

    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"/events$"), lambda q: q.abort()))
    page.wait_for_function("document.querySelector('#hh-latest').dataset.news !== undefined && document.querySelector('#hh-latest').dataset.pubs !== undefined", timeout=15000)
    r = page.evaluate("() => ({ news: document.querySelector('[data-hh=news]').hidden, pubs: document.querySelectorAll('[data-hh=pubs] .hh-item:not(.hh-wait)').length, single: document.querySelector('.hh-latest-wrap').classList.contains('is-single'), block: document.querySelector('#hh-latest').hidden })")
    ok("the Events page unreadable: the news list is left out, the papers stay", r["news"] and r["pubs"] == 3 and r["single"] and not r["block"], r)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()

    names = {u.split("?")[0].rsplit("/", 1)[-1] for u in pictures if u}
    ctx, page = open_page(br, route=lambda p: p.route(lambda u: u.split("?")[0].rsplit("/", 1)[-1] in names, lambda q: q.abort()))
    page.wait_for_function("document.querySelector('#hh-latest').dataset.news !== undefined && document.querySelector('#hh-latest').dataset.pubs !== undefined", timeout=15000)
    page.evaluate("document.querySelector('#hh-latest').scrollIntoView()")
    try:
        page.wait_for_function("document.querySelectorAll('#hh-latest .hh-thumb.is-none').length === 6", timeout=15000)
    except Exception:
        pass
    t = page.evaluate(THUMBS)
    r = page.evaluate("() => [...document.querySelectorAll('#hh-latest .hh-item:not(.hh-wait) .hh-title')].map(e => e.getBoundingClientRect().width > 50).length")
    quiet = len(names) == 6 and len(t["pics"]) == 6 and all(p["none"] and abs(p["box"][0] - t["col"]) <= 0.6 and abs(p["box"][1] - 0.75 * t["col"]) <= 0.6 and p["back"] == "none" for p in t["pics"])
    ok("the pictures cannot be fetched: a quiet box in each one's place, the six entries stay", quiet and r == 6, (sorted(names)[:2], [([round(v, 1) for v in p["box"]], p["none"]) for p in t["pics"]], r))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()
    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"/(events|publication)$"), lambda q: q.fulfill(status=200, content_type="text/html", body="<html><body><p>rebuilt</p></body></html>")))
    page.wait_for_function("document.querySelector('#hh-latest').dataset.news !== undefined && document.querySelector('#hh-latest').dataset.pubs !== undefined", timeout=15000)
    r = page.evaluate("() => ({ block: document.querySelector('#hh-latest').hidden, h: document.querySelector('#hh-latest').getBoundingClientRect().height })")
    ok("both pages rebuilt beyond reading: the block is left out, with no gap", r["block"] and r["h"] == 0, r)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def the_section(br):
    print("  the lab and recruiting, in two languages")
    SEEN = """() => { const vis = l => [...document.querySelectorAll('#hh-about [data-l="' + l + '"]')].filter(e => e.getClientRects().length).length;
      return { lang: document.querySelector('#hh-about').dataset.lang, en: vis('en'), ko: vis('ko'), pressed: [...document.querySelectorAll('.hh-lang button')].map(b => b.getAttribute('aria-pressed')).join(),
        h2: [...document.querySelectorAll('#hh-about .hh-about-h2')].filter(e => e.getClientRects().length).map(e => e.textContent) }; }"""
    ctx, page = open_page(br, locale="ko-KR")
    r = page.evaluate(SEEN)
    ok("a Korean browser gets Korean, and only Korean", r["lang"] == "ko" and r["en"] == 0 and r["ko"] > 8 and r["pressed"] == "false,true", r)
    ctx.close()
    ctx, page = open_page(br, locale="en-US")
    r = page.evaluate(SEEN)
    ok("any other browser gets English, and only English", r["lang"] == "en" and r["ko"] == 0 and r["en"] > 8 and r["pressed"] == "true,false", r)
    page.click('.hh-lang button[data-set="ko"]')
    r = page.evaluate(SEEN)
    ok("the Korean button switches it", r["lang"] == "ko" and r["en"] == 0 and r["h2"] == ["지구 시스템을 관측하고 이해하고 예측하는 AI"], r)
    page.reload(wait_until="load")
    r = page.evaluate(SEEN)
    ok("and the browser remembers it", r["lang"] == "ko" and r["pressed"] == "false,true", r)
    page.click('.hh-lang button[data-set="en"]')

    # nothing of the recruiting list was lost: each of its sentences is in the folded call. One Korean sentence reads
    # differently since 2026-11-20, when the lab head had the Korean wording revised.
    old = (HOME / "replaced-paragraph.html").read_text(encoding="utf-8").replace("‍", "").replace("가족기숙자", "가족기숙사")
    bullets = [norm(re.sub(r"<[^>]+>", "", x).replace("&#x27;", "'").replace("&quot;", '"')) for x in old.split("<br/>") if "•" in x]
    ok("the replaced paragraph has its twelve recruiting sentences", len(bullets) == 12, len(bullets))
    was = norm("위성 원격 탐사, 수치모델, 기후변화, 환경/원격탐사 분야 Domain Scientist로 AI/기계학습 방법론 적용 연구에 대한 열정을 가지고 있는 학부생 및 대학원 진학 예정 학생을 환영합니다.")
    now = norm("위성 원격탐사, 수치모델, 기후변화, 환경/원격탐사 분야의 Domain Scientist로 AI/기계학습 방법론을 적용해 연구하고 싶은 학부생 및 대학원 진학 예정 학생을 환영합니다.")
    ok("the one reworded sentence is among them as it was", sum(b == was for b in bullets) == 1, [b[:30] for b in bullets])
    bullets = [now if b == was else b for b in bullets]
    r = page.evaluate("""() => { const d = document.querySelector('.hh-call'); const before = d.open; const call = d.textContent;
      document.querySelector('.hh-call summary').click();
      return { before, after: d.open, call, shown: [...d.querySelectorAll('ul')].filter(u => u.getClientRects().length).map(u => u.getAttribute('data-l')).join(),
        links: [...document.querySelectorAll('#hh-about a')].map(x => x.getAttribute('href')),
        pics: [...document.querySelectorAll('.hh-pics img')].map(i => [i.naturalWidth, i.naturalHeight, +i.getAttribute('width'), +i.getAttribute('height')]) }; }""")
    call = norm(r["call"])
    missing = [b[:40] for b in bullets if b not in call]
    ok("each of them is in the folded call, word for word (the one as reworded)", missing == [], missing)
    ok("the call is folded until asked for, then shows the chosen language", (not r["before"]) and r["after"] and r["shown"] == "en", r["shown"])
    ok("links to Projects, Opportunities and Contact", {"/projects", "/opportunities", "/contact"} <= set(r["links"]), sorted(set(r["links"])))
    page.evaluate("document.querySelector('.hh-pics').scrollIntoView()")
    page.wait_for_function("[...document.querySelectorAll('.hh-pics img')].every(i => i.complete && i.naturalWidth > 0)", timeout=15000)
    r2 = page.evaluate("() => [...document.querySelectorAll('.hh-pics img')].map(i => [i.naturalWidth / i.naturalHeight, i.getAttribute('width') / i.getAttribute('height'), i.clientWidth / i.clientHeight])")
    ok("the two photographs load and keep their proportions", all(abs(x[0] - x[1]) < 0.02 and abs(x[0] - x[2]) < 0.02 for x in r2), r2)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def the_sizes(br, name):
    print("  thirteen window sizes")
    ctx, page = open_page(br, 1440, 900, reduced_motion="reduce")      # still pictures, and nothing waiting to rise into place: what is measured is where things end up
    page.wait_for_function("document.querySelector('#hh-latest').dataset.pubs !== undefined", timeout=15000)
    page.wait_for_function("(i => i.complete && i.naturalWidth > 0)(document.querySelector('.hh-hero-sky img'))", timeout=20000)
    for w, h in SIZES:
        page.set_viewport_size({"width": w, "height": h})
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(150)
        r = page.evaluate("""async () => {
          const box = s => { const e = document.querySelector(s); const b = e.getBoundingClientRect(); return [b.left, b.top + scrollY, b.right, b.bottom + scrollY]; };
          const tabs = [...document.querySelectorAll('.hh-reel-tab')], hero = document.querySelector('.hh-hero'), heights = [];
          const cut = [];
          for (const t of tabs) { t.click(); await new Promise(r => setTimeout(r, 25)); heights.push(Math.round(hero.getBoundingClientRect().height));
            const s = t.querySelector('span'); if (getComputedStyle(s).display !== 'none' && t.scrollWidth > t.clientWidth + 1) cut.push(s.textContent); }
          tabs[0].click();
          const wide = [...document.querySelectorAll('#hh-hero, #hh-hero *, #hh-latest, #hh-latest *, #hh-about, #hh-about *')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && (b.right > innerWidth + 0.5 || b.left < -0.5) && (!e.checkVisibility || e.checkVisibility()); }).map(e => e.className).slice(0, 4);
          const title = document.querySelector('.hh-hero-title'), cta = document.querySelector('.hh-hero-actions'), stage = document.querySelector('.hh-reel-stage'), first = cta.querySelector('a');
          const sr = stage.getBoundingClientRect();
          return { over: document.documentElement.scrollWidth - innerWidth, heights, cut, wide, hero: box('.hh-hero'), stage: [sr.width, sr.height],
            lines: Math.round(title.getBoundingClientRect().height / parseFloat(getComputedStyle(title).lineHeight)), ctaBottom: cta.getBoundingClientRect().bottom, firstBottom: first.getBoundingClientRect().bottom, stageTop: sr.top,
            order: [box('.hh-hero')[3], box('.hh-latest')[1], box('.hh-latest')[3], box('.hh-about')[1], box('.hh-about')[3], box('.usps-wrap')[1]],
            join: box('.hh-join'), tile: box('.step-tile') }; }""")
        good = (r["over"] <= 0 and r["wide"] == [] and len(set(r["heights"])) == 1 and r["cut"] == [] and r["lines"] <= 3
                and abs(r["stage"][0] / r["stage"][1] - 16 / 9) < 0.02 and (r["ctaBottom"] <= h or (h < 600 and r["firstBottom"] <= h)) and (r["stageTop"] < h or h < 700)
                and all(x <= y + 1 for x, y in zip(r["order"], r["order"][1:])) and r["join"][3] + 16 <= r["tile"][1])
        ok(f"{w} x {h}: fits the window, the buttons on the first screen (on the smallest phone, the first of them) and the top of the pictures (on any but a small phone), the blocks in order, nothing cut", good,
           {k: r[k] for k in ("over", "wide", "heights", "cut", "lines", "stage", "ctaBottom", "firstBottom", "stageTop", "order", "join", "tile")})
        low = unreadable(page)
        ok(f"{w} x {h}: every line of words on the first screen can be read against the picture behind it", low == [], low)
        if a.shots:
            Path(a.shots).mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(Path(a.shots) / f"{name}_{w}x{h}.png"))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


with sync_playwright() as pw:
    for name in a.browsers.split(","):
        print(f"\n== {name}: {URL}")
        br = getattr(pw, name).launch()
        the_page(br)
        without_scripts(br)
        the_sky(br)
        the_reel(br)
        two_sizes(br)
        if not a.quick:
            reel_without_loops(br)
        reduced_motion(br)
        the_lists(br)
        the_section(br)
        the_sizes(br, name)
        br.close()
print(f"\n{FAILS} failed")
sys.exit(min(FAILS, 100))
