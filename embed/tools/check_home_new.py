#!/usr/bin/env python3
"""check_home_new.py [URL] [--browsers chromium,webkit,firefox] [--shots DIR] [--quick] — the home page's three new blocks, checked.

    python embed/tools/check_home_new.py                         # the local preview (home_new_preview.py, port 8814)
    python embed/tools/check_home_new.py https://hydroai.net/    # the live page (the blocks are on it since 2026-11-20)

What it looks at, in each browser:
  the page      one <h1>; the three blocks are there and what they replace is gone; no script error; nothing wider than the window;
                without scripts the words and still pictures remain and what needs scripts is left out
  the reel      the first loop plays with its captions; each dataset follows the one before (all five, at speed);
                the larger loop on a dense desktop screen, the card's own on a phone or when the larger cannot be fetched;
                a click on a bar (also right after a change, on a loop slow to arrive, and back to the dataset just left),
                pause and play, a hidden tab, scrolling away; loops that cannot be fetched do not hold it;
                with reduced motion no video is fetched until play is pressed; the block keeps its height as datasets change
  the lists     three news entries and three papers, the same as the first entries of /events and /publication;
                either page unreadable -> that list is left out; both -> the block is
  the section   one language at a time, chosen by the browser's language, switched and remembered;
                every sentence of the recruiting list that the block replaced is still on the page, in the folded call
  the sizes     thirteen window sizes from 2048 px down to a 320 px phone
The exit status is the number of failures. Needs playwright with the three browsers installed.
"""
import argparse
import re
import sys
import time
from pathlib import Path

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

SLIDES = [("wq", "Inland Water Quality of South Korea", "/data#wq"), ("et", "Global 30m-ET", "/data#et"), ("hdca", "Hybrid Dual-Channel Algorithm (HDCA)", "/data#hdca"),
          ("tca", "SMAP Time-Variant Error", "/data#tca"), ("cvs", "NASA-GIST Core Validation Site", "/data#cvs")]
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


def without_scripts(br):
    print("  without scripts")
    ctx = br.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(URL, wait_until="load", timeout=60000)
    seen = lambda sel: page.locator(sel).first.is_visible()
    ok("the title, the first dataset's still picture and words, and both languages of the section are there", seen(".hh-hero-title") and seen(".hh-reel-stage") and seen(".hh-reel-title") and seen('.hh-about-h2[data-l="en"]') and seen('.hh-about-h2[data-l="ko"]'))
    ok("what needs scripts is left out (the bars, the two lists, the language buttons)", not seen(".hh-reel-tabs") and not seen("#hh-latest") and not seen(".hh-lang"))
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
    ok("the first loop starts by itself", wait_reel(page, "s.front && s.front.id === 'wq' && !s.front.paused && s.front.t > 0.3", 12000))
    s = page.evaluate(REEL)
    ok("five datasets, the first one on show, marked new", s["n"] == 5 and s["cur"] == 0 and s["isNew"] and s["title"] == SLIDES[0][1], s)
    ok("its link and its still picture", s["href"] == "/data#wq" and s["stageHref"] == "/data#wq" and "wq-v1.jpg" in s["poster"], s)
    ok("only the loop on show has been fetched", len({u.split("/")[-1].split(".")[0] for u in media}) == 1, media)
    seen = set()
    for _ in range(60):                                   # the captions over the first loop
        st = page.evaluate(REEL)
        if st["cur"] != 0:
            break
        seen.add(st["cap"])
        page.wait_for_timeout(190)
    want = {"Water temperature, 2016–2024 mean", "Suspended solids", "Dissolved oxygen", "Total nitrogen", "Total phosphorus", "Chlorophyll-a", "Into Daecheong Lake: 1 km cells", "Chlorophyll-a through the year"}
    ok("every caption of the first loop is shown", want <= seen, sorted(want - seen))
    ok("when it ends the second dataset comes, its loop playing", wait_reel(page, "s.cur === 1 && s.front && s.front.id === 'et' && !s.front.paused && s.front.t > 0.2", 16000))
    s = page.evaluate(REEL)
    ok("its words, link and bars", s["title"] == SLIDES[1][1] and s["href"] == "/data#et" and not s["isNew"] and s["bars"][0] == 1 and 0 < s["bars"][1] < 1 and s["bars"][2] == 0, s)
    ok("only one video is visible", sum(v["on"] for v in s["vids"]) == 1, s["vids"])

    page.click(".hh-reel-tab:nth-child(4)")                # a bar
    ok("a click on the fourth bar shows the fourth dataset", wait_reel(page, "s.cur === 3 && s.front && s.front.id === 'tca' && !s.front.paused && s.front.t > 0.2", 12000))
    s = page.evaluate(REEL)
    ok("with its words", s["title"] == SLIDES[3][1] and s["href"] == "/data#tca" and s["bars"][:3] == [1, 1, 1], s)

    page.click(".hh-reel-pause")                           # pause, play
    page.wait_for_timeout(400)
    s1 = page.evaluate(REEL)
    page.wait_for_timeout(1200)
    s2 = page.evaluate(REEL)
    ok("pause stops the loop where it is", all(v["paused"] for v in s2["vids"]) and abs(s2["front"]["t"] - s1["front"]["t"]) < 0.05 and s2["button"] == "Play the pictures", (s1["front"], s2["front"], s2["button"]))
    page.click(".hh-reel-pause")
    ok("play goes on from there, the same loop", wait_reel(page, f"s.cur === 3 && s.front && s.front.id === 'tca' && !s.front.paused && s.front.t > {s2['front']['t'] + 0.3}", 6000))
    ok("the button says pause again", page.evaluate(REEL)["button"] == "Pause the pictures")
    page.click(".hh-reel-tab:nth-child(2)")                # a long pause is not taken for a loop that has stalled
    wait_reel(page, "s.cur === 1 && s.front && s.front.id === 'et' && !s.front.paused && s.front.t > 0.5", 12000)
    page.click(".hh-reel-pause")
    t0 = page.evaluate(REEL)["front"]["t"]
    page.wait_for_timeout(9500)
    page.click(".hh-reel-pause")
    page.wait_for_timeout(1200)
    s3 = page.evaluate(REEL)
    ok("after a pause of ten seconds play goes on with the same dataset", s3["cur"] == 1 and s3["front"] and s3["front"]["id"] == "et" and not s3["front"]["paused"] and t0 < s3["front"]["t"] < t0 + 2.5, (t0, s3["cur"], s3["front"]))

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
    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"/tca-[^/]*\.(webm|mp4)"), late))
    wait_reel(page, "s.front && s.front.id === 'wq' && !s.front.paused && s.front.t > 0.3", 12000)
    quick = """([after, then]) => { let done = false; document.querySelectorAll('.hh-reel-stage video').forEach(v => v.addEventListener('playing', () => {
        if (!done && v.getAttribute('data-id') === after) { done = true; setTimeout(() => document.querySelectorAll('.hh-reel-tab')[then].click(), 200); } })); }"""
    page.evaluate(quick, ["et", 3])                        # the second dataset, and 0.2 s after it shows, the fourth
    page.click(".hh-reel-tab:nth-child(2)")
    ok("a bar clicked 0.2 s after a change gets its loop, though the loop is slow to arrive", wait_reel(page, "s.cur === 3 && s.front && s.front.id === 'tca' && !s.front.paused && s.front.t > 0.2", 10000), page.evaluate(REEL))
    page.evaluate(quick, ["hdca", 3])                      # the third, and 0.2 s after it shows, back to the fourth, whose video is still fading out
    page.click(".hh-reel-tab:nth-child(3)")
    ok("and so does the bar of the dataset just left", wait_reel(page, "s.cur === 3 && s.front && s.front.id === 'tca' && !s.front.paused && s.front.t > 0.2 && s.vids.filter(v => v.on).length === 1", 10000), page.evaluate(REEL))
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
    ok("all five loops play in turn and the first comes round again", order == ["wq", "et", "hdca", "tca", "cvs", "wq"], order)
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


def two_sizes(br):
    print("  the loops in two sizes")
    ctx, page = open_page(br, 1440, 900, device_scale_factor=2)
    ok("a dense desktop screen: the loop starts", wait_reel(page, "s.front && !s.front.paused && s.front.t > 0.2 && s.front.px > 0", 15000))
    s = page.evaluate(REEL)
    ok("and it is the larger one (1536 px), with the larger still picture", s["front"] and s["front"]["src"].startswith("wq-wide-v1.") and s["front"]["px"] == 1536 and "wq-wide-v1.jpg" in s["poster"], (s["front"], s["poster"]))
    ctx.close()
    ctx, page = open_page(br, 1440, 900, device_scale_factor=2, route=lambda p: p.route(re.compile(r"-wide-v\d+\.(webm|mp4)"), lambda r: r.abort()))
    ok("the larger loop cannot be fetched: the card's own plays instead", wait_reel(page, "s.front && s.front.id === 'wq' && !s.front.paused && s.front.t > 0.2 && s.front.px === 768", 15000), page.evaluate(REEL)["vids"])
    ctx.close()
    ctx, page = open_page(br, 390, 844, device_scale_factor=3)
    ok("a phone: the loop starts", wait_reel(page, "s.front && !s.front.paused && s.front.t > 0.2 && s.front.px > 0", 15000))
    s = page.evaluate(REEL)
    ok("and it is the card's own (768 px)", s["front"] and s["front"]["src"].startswith("wq-v1.") and s["front"]["px"] == 768, s["front"])
    ctx.close()


def reel_without_loops(br):
    print("  the reel when the loops cannot be fetched")
    ctx, page = open_page(br, route=lambda p: p.route(re.compile(r"\.(webm|mp4)(\?|$)"), lambda r: r.abort()))
    page.wait_for_timeout(3000)
    s = page.evaluate(REEL)
    ok("the first still picture stays", s["cur"] == 0 and "wq-v1.jpg" in s["poster"] and not s["front"], s)
    ok("then the next dataset comes anyway", wait_reel(page, "s.cur === 1", 16000))
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def reduced_motion(br):
    print("  reduced motion")
    media = []
    ctx, page = open_page(br, reduced_motion="reduce", route=lambda p: p.on("request", lambda q: media.append(q.url) if re.search(r"\.(webm|mp4)(\?|$)", q.url) else None))
    page.wait_for_timeout(2500)
    s = page.evaluate(REEL)
    ok("no video is fetched; the still picture and its words are there", media == [] and "wq-v1.jpg" in s["poster"] and s["title"] == SLIDES[0][1] and s["cap"] != "", (media, s))
    ok("the button offers to play", s["button"] == "Play the pictures")
    page.click(".hh-reel-tab:nth-child(3)")
    page.wait_for_timeout(600)
    s = page.evaluate(REEL)
    ok("a bar still changes the dataset, as a still picture", s["cur"] == 2 and s["title"] == SLIDES[2][1] and "hdca-v3.jpg" in s["poster"] and media == [], (s, media))
    page.click(".hh-reel-pause")
    ok("pressing play starts that dataset's loop", wait_reel(page, "s.front && s.front.id === 'hdca' && !s.front.paused && s.front.t > 0.2", 12000))
    r = page.evaluate("() => ({ anim: getComputedStyle(document.querySelector('.hh-hero-copy > *')).animationName, rise: !!document.querySelector('.hh-anim') })")
    ok("nothing slides or rises in", r["anim"] == "none" and not r["rise"], r)
    ok("no script error", page.errors == [], page.errors[:3])
    ctx.close()


def first_entries(br, path, js):
    ctx = br.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(URL + path, wait_until="domcontentloaded", timeout=60000)
    out = page.evaluate(js)
    ctx.close()
    return out


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
    ok("the Korean button switches it", r["lang"] == "ko" and r["en"] == 0 and r["h2"] == ["지구 시스템을 관측하고 이해하고 예측하기 위한 AI"], r)
    page.reload(wait_until="load")
    r = page.evaluate(SEEN)
    ok("and the browser remembers it", r["lang"] == "ko" and r["pressed"] == "false,true", r)
    page.click('.hh-lang button[data-set="en"]')

    # nothing of the recruiting list was lost: each of its sentences is in the folded call
    old = (HOME / "replaced-paragraph.html").read_text(encoding="utf-8").replace("‍", "").replace("가족기숙자", "가족기숙사")
    bullets = [norm(re.sub(r"<[^>]+>", "", x).replace("&#x27;", "'").replace("&quot;", '"')) for x in old.split("<br/>") if "•" in x]
    ok("the replaced paragraph has its twelve recruiting sentences", len(bullets) == 12, len(bullets))
    r = page.evaluate("""() => { const d = document.querySelector('.hh-call'); const before = d.open; const call = d.textContent;
      document.querySelector('.hh-call summary').click();
      return { before, after: d.open, call, shown: [...d.querySelectorAll('ul')].filter(u => u.getClientRects().length).map(u => u.getAttribute('data-l')).join(),
        links: [...document.querySelectorAll('#hh-about a')].map(x => x.getAttribute('href')),
        pics: [...document.querySelectorAll('.hh-pics img')].map(i => [i.naturalWidth, i.naturalHeight, +i.getAttribute('width'), +i.getAttribute('height')]) }; }""")
    call = norm(r["call"])
    missing = [b[:40] for b in bullets if b not in call]
    ok("each of them is in the folded call, word for word", missing == [], missing)
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
          const wide = [...document.querySelectorAll('#hh-hero, #hh-hero *, #hh-latest, #hh-latest *, #hh-about, #hh-about *')].filter(e => { const b = e.getBoundingClientRect(); return b.width > 0 && (b.right > innerWidth + 0.5 || b.left < -0.5) && !e.classList.contains('hh-thumb-bg') && (!e.checkVisibility || e.checkVisibility()); }).map(e => e.className).slice(0, 4);
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
