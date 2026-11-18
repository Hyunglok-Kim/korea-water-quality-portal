#!/usr/bin/env python3
"""Browser smoke test for the Korea inland water quality portal (headless, Playwright).

    python tests/smoke.py --base http://127.0.0.1:8797/ --shots /tmp/shots --ref tests/field_ref.json
    python tests/smoke.py --browser webkit ...        # Safari's engine; also firefox

Checks that the page boots without console errors; that what the browser reads from the two stores is what the
GeoTIFFs hold (--ref: values written by pipeline/build_store.py straight from the rasters, before any encoding);
that the means and counts the site computes agree with each other; that every skill number in the text, the tables
and the two bar charts is the one in data/skill.json (computed by pipeline/skill.py from the record's validation
file), in the page as shown and in its source; that hover, click, the cell charts, the tables
and the CSV, the four period views, the uncertainty band, the count of dates, the calendar, the place list, the
monitoring points, the tabs and the narrow layout work; and that the page says so when the map cannot be drawn.
Saves screenshots to look at. Exit code 1 on any failure.

Against the lab dashboard the portal needs a session cookie: put "hydroai_rd=<token>" in the SMOKE_COOKIE
environment variable and use the /rd/wq-korea/ address as --base.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="http://127.0.0.1:8797/")
ap.add_argument("--shots", required=True)
ap.add_argument("--ref", default="")
ap.add_argument("--query", default="intro=0")
ap.add_argument("--browser", default="chromium", choices=["chromium", "webkit", "firefox"])
ap.add_argument("--cookie", default="", help="name=value to send with every request (internal copy); or set SMOKE_COOKIE")
ap.add_argument("--figures", action="store_true", help="also check the page with the manuscript's figures (?paper=figures); only where assets/figures/ is served")
a = ap.parse_args()
a.cookie = a.cookie or os.environ.get("SMOKE_COOKIE", "")
shots = Path(a.shots)
shots.mkdir(parents=True, exist_ok=True)
fails, notes = [], []
LAYERS = [f"{p}_{b}" for p in ("wt", "ss", "chla", "do", "tn", "tp") for b in ("mu", "sigma")]
LIN = {0, 1, 6, 7}                         # wt and do are stored linearly (0.001), the rest logarithmically (0.028 % steps)


def check(ok, msg):
    (notes if ok else fails).append(("ok   " if ok else "FAIL ") + msg)


def close(got, exp, k, n=1):
    """Is `got` the stored form of `exp` (a value, or a sum of n values) for layer k?"""
    if got is None:
        return False
    return abs(got - exp) <= (6e-4 * n if k in LIN else 2e-4 * abs(exp))


def skill_text(spec, sk):
    """What a <span data-skill="..."> must read, from skill.json: the same rule as skillText in app.js."""
    part = spec.split("|")
    if part[0] in ("site_min", "site_max"):
        v = [x["r2_" + part[1]] for x in sk["sites"]]
        return f"{(min(v) if part[0] == 'site_min' else max(v)):.2f}"
    key, agg, plist, dec = part
    vals = [sk["params"][q][key] for q in (["wt", "ss", "chla", "do", "tn", "tp"] if plist == "all" else plist.split(","))]
    v = min(vals) if agg == "min" else max(vals) if agg == "max" else vals[0]
    if dec == "int":
        return f"{v:,}"
    return f"{v * 100:.{int(dec[3:])}f}" if dec.startswith("pct") else f"{v:.{int(dec)}f}"


def settle(page, ms=700, key_prefix=None):
    """Wait for the layer switch to land (the numbers may come over the internet), then for the map."""
    if key_prefix:
        # current() is null until the first layer's numbers have arrived, which over the internet is after the map's load event
        page.wait_for_function("p => { const c = window.__portal.current(); return !!c && c.spec.key.startsWith(p) && !!c.vals; }", arg=key_prefix, timeout=60000)
    page.wait_for_timeout(ms)
    page.wait_for_function("window.__portal.map.areTilesLoaded()", timeout=60000)


# What the app would draw for a layer, without touching what is on screen.
DISPLAY = """async ([v, band, mode, when]) => { const p = window.__portal, s = p.state, keep = {...s};
    s.var = v; s.band = band; s.mode = mode;
    if (mode === 'date') s.date = when; if (mode === 'month') s.ym = when; if (mode === 'clim') s.climMonth = +when;
    const spec = p.layerSpec(); Object.assign(s, keep);
    return p.getDisplay(spec); }"""

with sync_playwright() as pw:
    gl = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"]
    br = getattr(pw, a.browser).launch(args=gl if a.browser == "chromium" else [])

    def new_context(w=1440, h=900):
        c = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, accept_downloads=True)
        if a.cookie:
            from urllib.parse import urlparse
            name, _, value = a.cookie.partition("=")
            c.add_cookies([{"name": name, "value": value, "domain": urlparse(a.base).hostname, "path": "/"}])
        return c

    ctx = new_context()
    page = ctx.new_page()
    console, bad = [], []
    page.on("console", lambda m: console.append((m.type, m.text)))
    page.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    aborted = ("ERR_ABORTED", "cancelled", "NS_BINDING_ABORTED")
    page.on("requestfailed", lambda r: bad.append((r.url, r.failure)) if not any(x in str(r.failure) for x in aborted) else None)
    page.on("response", lambda r: bad.append((r.url, r.status)) if r.status >= 400 else None)

    sep = "&" if "?" in a.base else "?"
    url = a.base + (sep + a.query if a.query else "")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_function("window.__portal && window.__portal.ready && window.__portal.ready()", timeout=60000)
    page.wait_for_function("document.querySelector('#boot') === null", timeout=15000)
    settle(page, 2000, "chla|mu|all|")
    page.screenshot(path=str(shots / "01_record_mean.png"))

    info = page.evaluate("""() => { const p = window.__portal, c = p.current(), cat = p.CAT();
        return {zoom: p.map.getZoom(), key: c.spec.key, n: c.stats.n, median: c.stats.median, cells: cat.cells.n, dates: cat.dates.d.length,
                first: cat.record.first, last: cat.record.last, title: document.querySelector('#lyTitle').textContent,
                card: document.querySelector('#lyMean').textContent, cover: document.querySelector('#lyCover').textContent}; }""")
    notes.append(f"info {info}")
    check(info["cells"] == 8558 and info["dates"] == 1012 and info["first"] == "2016-01-06" and info["last"] == "2024-12-29",
          f"catalog: {info['cells']} cells, {info['dates']} dates, {info['first']} to {info['last']}")
    check(info["n"] == info["cells"] and info["cover"] == "8,558", f"the record mean has a value at every one of the product's cells ({info['n']})")
    check("Chlorophyll-a, mean of 2016–2024" == info["title"], "opens on: " + info["title"] + " · median " + info["card"])

    # the skill numbers: data/skill.json against the text as shown, the text in the page source, the tables and the charts
    page.wait_for_function("document.querySelectorAll('#abSkill tbody tr').length === 6", timeout=30000)
    sk = page.evaluate("""async () => { const d = new URLSearchParams(location.search).get('data') || './data/';
        return (await fetch(new URL(d, location.href).href + 'skill.json')).json(); }""")
    check(sk["matchups"] == 46933 and sk["points"] == 1194 and len(sk["sites"]) == 6, f"skill.json: {sk['matchups']} matchups at {sk['points']} points, {len(sk['sites'])} sites — {sk['source']}")
    shown = page.evaluate("[...document.querySelectorAll('[data-skill]')].map((n) => [n.dataset.skill, n.textContent])")
    wrong = [(k, t, skill_text(k, sk)) for k, t in shown if t != skill_text(k, sk)]
    check(len(shown) >= 30 and not wrong, f"{len(shown)} numbers in the text are those of skill.json" + (f" — wrong: {wrong[:4]}" if wrong else ""))
    import re
    src = page.evaluate("async () => (await fetch(location.pathname, {cache: 'no-store'})).text()")
    static = re.findall(r'data-skill="([^"]+)">([^<]*)<', src)
    stale = [(k, t, skill_text(k, sk)) for k, t in static if t != skill_text(k, sk)]
    check(len(static) >= 30 and not stale, f"the {len(static)} numbers written in the page source (the fallback) agree too" + (f" — stale: {stale[:4]}" if stale else ""))
    P = sk["params"]
    rows = page.evaluate("[...document.querySelectorAll('#abSkill tbody tr')].map((r) => [...r.children].map((c) => c.textContent))")
    exp = [[f"{P[q]['r2']:.3f}", "—" if "r2_log" not in P[q] else f"{P[q]['r2_log']:.3f}", f"{P[q]['rmse']:.{4 if P[q]['rmse'] < 1 else 2}f}", f"{P[q]['within']:.3f}"] for q in ("wt", "do", "ss", "chla", "tp", "tn")]
    got = [[r[2], r[3], r[4].split(" ")[0], r[5]] for r in rows]
    check(got == exp, f"About tab skill table: {got[0]} … {got[-1]}")
    drift = max(max(abs(P[q]["r2_mu"] - P[q]["r2"]) for q in P), max(abs(P[q]["r2_log_mu"] - P[q]["r2_log"]) for q in P if "r2_log" in P[q]),
                max(abs(P[q]["within_mu"] - P[q]["within"]) for q in P if q != "tn"))
    check(drift <= 0.04, f"the released mean scores within 0.04 of the single prediction, total nitrogen's series skill apart (largest difference {drift:.3f})")
    mode = page.evaluate("document.documentElement.className.split(' ').find((c) => c.startsWith('paper-'))")
    if mode != "paper-off":
        bars = page.evaluate("['#barsSkill', '#barsCover'].map((q) => [document.querySelectorAll(q + ' svg path').length, document.querySelectorAll(q + ' svg text.val').length, [...document.querySelectorAll(q + ' svg text.val')].map((t) => t.textContent)])")
        check(bars[0][0] == 12 and bars[1][0] == 12 and bars[0][2] == [f"{P[q]['within']:.2f}" for q in ("wt", "do", "ss", "chla", "tp", "tn")]
              and bars[1][2] == [f"{round(P[q]['cover_cal'] * 100)} %" for q in ("wt", "do", "ss", "chla", "tp", "tn")],
              f"two bar charts of twelve bars each, labelled from skill.json: {bars[0][2]} | {bars[1][2]}")
        sites = page.evaluate("[...document.querySelectorAll('#siteTable tbody tr')].map((r) => [...r.children].map((c) => c.textContent))")
        check(len(sites) == 6 and [r[3] for r in sites] == [f"{x['r2_wt']:.2f}" for x in sk["sites"]] and [r[4].replace("−", "-") for r in sites] == [f"{x['r2_chla']:.2f}" for x in sk["sites"]],
              f"the paper's six points: {[r[0] for r in sites][:2]} …, chlorophyll-a R² {[r[4] for r in sites]}")
        imgs = page.evaluate("document.querySelectorAll('#paper img').length")
        check((mode == "paper-text" and imgs == 0) or (mode == "paper-figures" and imgs == 6), f"“From the paper” is shown as {mode}: {imgs} manuscript figures on the page")
        page.click("#barsSkillBtn")
        check(page.locator("#barsSkillTable table tbody tr").count() == 6 and page.locator("#barsSkillTable").is_visible(), "the skill chart has its table")
        page.click("#barsSkillBtn")

    if a.ref:
        ref = json.loads(Path(a.ref).read_text())
        # 1 — single dates: every layer of four dates against the rasters
        for d, exp in ref["dates"].items():
            iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            worst = []
            for k, layer in enumerate(LAYERS):
                par, band = layer.split("_")
                got = page.evaluate("async (a) => { const v = await (" + DISPLAY + """)(a.slice(0, 4)); let n = 0, sum = 0;
                    for (const x of v) if (!Number.isNaN(x)) { n++; sum += x; } return {n, sum, at: a[4].map((c) => v[c])}; }""",
                    [par, band, "date", iso, [p["cell"] for p in exp["at"]]])
                ok = got["n"] == exp["n"] and close(got["sum"], exp["sum"][k], k, exp["n"]) and all(close(g, p["v"][k], k) for g, p in zip(got["at"], exp["at"]))
                if not ok:
                    worst.append(f"{layer}: n {got['n']}/{exp['n']}, sum {got['sum']:.6g}/{exp['sum'][k]:.6g}")
            check(not worst, f"{iso}: all 12 layers ({exp['n']} cells) match the GeoTIFFs" + ("" if not worst else " — " + "; ".join(worst[:3])))
        # 2 — the series store: whole records of four cells against the rasters
        for c, exp in ref["cells"].items():
            got = page.evaluate("""async (c) => { const p = window.__portal, cat = p.CAT(), S = await p.getSeries(c);
                return {n: S.n, first: cat.dates.d[S.di[0]], last: cat.dates.d[S.di[S.n - 1]], sorted: S.di.every((x, i) => !i || x > S.di[i - 1]),
                        mean: S.vals.map((a) => a.reduce((s, x) => s + x, 0) / a.length)}; }""", int(c))
            ok = got["n"] == exp["n"] and got["first"] == exp["first"] and got["last"] == exp["last"] and got["sorted"] and all(close(g, e, k) for k, (g, e) in enumerate(zip(got["mean"], exp["mean"])))
            check(ok, f"cell {c} (row {exp['row']}, column {exp['col']}): its {exp['n']} overpass{'' if exp['n'] == 1 else 'es'}, {exp['first']} to {exp['last']}, match the GeoTIFFs in all 12 layers")
        # 3 — record means and counts: what the site computes from the files
        for c, exp in ref["clim"].items():
            got = page.evaluate("async ([c, pars]) => { const out = {all: [], cnt: []}; for (const [v, b] of pars) out.all.push((await (" + DISPLAY + """)([v, b, 'all', ''])) [c]);
                out.cnt.push((await (""" + DISPLAY + """)(['n', 'mu', 'all', ''])) [c]);
                for (let m = 1; m <= 12; m++) out.cnt.push((await (""" + DISPLAY + """)(['n', 'mu', 'clim', m])) [c]); return out; }""",
                [int(c), [layer.split("_") for layer in LAYERS]])
            cnt = [0 if x is None or x != x else int(x) for x in got["cnt"]]     # NaN: no date in that calendar month at this cell
            ok = all(close(g, e, k) for k, (g, e) in enumerate(zip(got["all"], exp["all"]))) and cnt == exp["count"]
            check(ok, f"cell {c}: record means of all 12 layers and the counts of dates (whole record, 12 calendar months) match")
        # 4 — one month computed two ways in the browser: from the by-date store and from the by-cell store
        c = max(ref["cells"], key=lambda k: ref["cells"][k]["n"])
        two = page.evaluate("async ([c]) => { const p = window.__portal, cat = p.CAT(), S = await p.getSeries(c); const v = await (" + DISPLAY + """)(['chla', 'mu', 'month', '2022-10']);
            let s = 0, n = 0; S.di.forEach((d, j) => { if (cat.dates.d[d].startsWith('202210')) { s += S.vals[4][j]; n++; } });
            const cn = await (""" + DISPLAY + """)(['n', 'mu', 'month', '2022-10']); return {field: v[c], series: n ? s / n : null, n, count: cn[c]}; }""", [int(c)])
        check(two["n"] > 0 and two["count"] == two["n"] and abs(two["field"] - two["series"]) <= 1e-5 * abs(two["series"]),
              f"October 2022 mean at cell {c}: {two['field']:.4f} from the by-date store, {two['series']:.4f} from the by-cell store, {two['n']} dates in both")

    # hover readout and click, at the cell with the longest record (the map is scrolled to the middle of the window
    # first: with the lead boxes above it, its centre otherwise sits under the fixed partner strip)
    page.evaluate("document.getElementById('map').scrollIntoView({block: 'center'})")
    page.wait_for_timeout(300)
    best = page.evaluate("""async () => { const p = window.__portal, cat = p.CAT(), v = await p.getDisplay({...p.layerSpec(), var: 'n', isN: true, L: -1, key: 'n|mu|all|'});
        let c = 0; for (let i = 1; i < v.length; i++) if (v[i] > v[c]) c = i;
        const g = cat.grid; return {c, n: v[c], lng: g.x0 + (cat.cells.col[c] + 0.5) * g.dx, lat: g.y0 - (cat.cells.row[c] + 0.5) * g.dy}; }""")
    page.evaluate("([x, y]) => window.__portal.map.jumpTo({center: [x, y], zoom: 10.6})", [best["lng"], best["lat"]])
    settle(page, 1200)
    box = page.locator("#map").bounding_box()
    pt = page.evaluate("([x, y]) => { const p = window.__portal.map.project([x, y]); return [p.x, p.y]; }", [best["lng"], best["lat"]])
    cx, cy = box["x"] + pt[0], box["y"] + pt[1]
    page.mouse.move(cx, cy)
    page.wait_for_timeout(400)
    ro = page.inner_text("#roVal")
    check("µg/L" in ro, f"hover readout over the cell with the longest record ({best['n']:.0f} dates): '{ro}'")
    page.screenshot(path=str(shots / "02_zoomed.png"))

    page.mouse.click(cx, cy)
    page.wait_for_function("document.querySelector('#recordBox') && !document.querySelector('#recordBox').hidden", timeout=60000)
    picked = page.evaluate("window.__portal.state.pick")
    check(picked and picked["i"] == best["c"], f"click picks that cell: row {picked and picked['row']}, column {picked and picked['col']} — {page.inner_text('#srTitle')}")
    check(page.locator("#chart svg circle").count() >= 5 and page.locator("#chartRecord svg circle").count() >= best["n"],
          "cell charts drawn: " + page.inner_text("#srSub")[:110])
    check(page.locator("#six button").count() == 6 and page.locator("#six svg").count() == 6, "six small multiples, one per parameter")
    with page.expect_download() as dl:
        page.click("#rcCsv")
    csv_text = Path(dl.value.path()).read_text()
    rows = [r for r in csv_text.splitlines() if r and not r.startswith("#")]
    check(rows[0] == "date," + ",".join(f"{p}_mu,{p}_sigma" for p in ("wt", "ss", "chla", "do", "tn", "tp")) and len(rows) == int(best["n"]) + 1
          and all(len(r.split(",")) == 13 and all(x for x in r.split(",")) for r in rows[1:]),
          f"record CSV: {len(rows) - 1} rows of 13 filled columns, first {rows[1][:60]!r}")
    with page.expect_download() as dl:
        page.click("#srCsv")
    ycsv = [r for r in Path(dl.value.path()).read_text().splitlines() if r and not r.startswith("#")]
    check(ycsv[0] == "date,mu,sigma,lo95,hi95" and len(ycsv) > 5 and all(float(r.split(",")[3]) <= float(r.split(",")[1]) <= float(r.split(",")[4]) for r in ycsv[1:]),
          f"year CSV: {len(ycsv) - 1} overpasses, each with its 95 % interval around the value")

    # tooltip on the chart, its table, the year stepper
    page.locator("#chart svg").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    sv = page.locator("#chart svg").bounding_box()
    page.mouse.move(sv["x"] + sv["width"] * 0.6, sv["y"] + sv["height"] * 0.5)
    page.wait_for_timeout(200)
    tip = page.inner_text("#tip").replace("\n", " / ") if page.locator("#tip").is_visible() else ""
    check("95 % interval" in tip and "µg/L" in tip, "chart tooltip: " + tip[:100])
    page.mouse.move(5, 5)
    page.click("#srTableBtn")
    n_rows = page.locator("#srTable table tbody tr").count()
    check(n_rows == len(ycsv) - 1, f"series table has {n_rows} rows, as many as the year's overpasses")
    page.click("#srTableBtn")
    y0 = page.inner_text("#srYear")
    page.click("#srYearPrev")
    page.wait_for_timeout(400)
    check(page.inner_text("#srYear") == str(int(y0) - 1), f"year stepper: {y0} → {page.inner_text('#srYear')}")
    page.screenshot(path=str(shots / "03_cell.png"), full_page=True)

    # a small multiple puts its parameter on the map
    page.click("#six button >> nth=0")
    settle(page, 800, "wt|mu|all|")
    check(page.inner_text("#lyTitle").startswith("Water temperature") and "Meteorologically" in page.inner_text("#lyRegime"),
          "small multiple → map: " + page.inner_text("#lyTitle") + " · " + page.inner_text("#lyRegime"))
    page.click("#srReset")
    page.wait_for_timeout(300)
    check(page.evaluate("window.__portal.state.pick") is None and page.inner_text("#srTitle") == "All cells", "“← All cells” clears the pick")
    page.evaluate("document.getElementById('map').scrollIntoView({block: 'center'})")

    # date view: the date of the paper's product figure, then stepping, then a date without a grid
    page.click("#btnHome")
    page.wait_for_timeout(1900)
    page.click("#modeSeg button[data-mode=date]")
    settle(page, 1000, "wt|mu|date|2023-12-03")
    n = page.evaluate("window.__portal.current().stats.n")
    check(n == 4565 and "3 Dec 2023" in page.inner_text("#lyTitle"), f"date view opens on 3 December 2023 with {n} cells (the paper's Fig. 3 says 4,565)")
    chips = page.locator("#when .chip").count()
    check(chips == 11, f"{chips} overpass dates offered for December 2023")
    page.screenshot(path=str(shots / "04_date.png"))
    page.click("#when button[aria-label='Next overpass']")
    settle(page, 800, "wt|mu|date|2023-12-05")
    check(page.evaluate("window.__portal.state.date") == "2023-12-05", "next overpass: " + page.inner_text("#lyTitle"))

    # uncertainty band, count of dates, seasonal cycle, month
    page.click("#varSeg button[data-var=chla]")
    page.click("#bandSeg button[data-band=sigma]")
    settle(page, 800, "chla|sigma|date|")
    check(page.inner_text("#lgTitle").startswith("σ Chl-a") and "calibrated uncertainty" in page.inner_text("#lyFlag"), "uncertainty layer: " + page.inner_text("#lyTitle"))
    page.click("#varSeg button[data-var=n]")
    settle(page, 800, "n|mu|month|")
    check(page.evaluate("document.querySelector('#modeSeg button[data-mode=date]').disabled && document.querySelector('#bandSeg button[data-band=sigma]').disabled"),
          "for the count of dates the single-date view and the uncertainty band are switched off: " + page.inner_text("#lyTitle"))
    page.click("#modeSeg button[data-mode=clim]")
    settle(page, 800, "n|mu|clim|")
    check("Dates with a value in" in page.inner_text("#lyTitle"), "count by calendar month: " + page.inner_text("#lyTitle"))
    page.click("#varSeg button[data-var=ss]")                        # the band chosen before the count comes back with the parameter
    settle(page, 600, "ss|sigma|clim|")
    page.click("#bandSeg button[data-band=mu]")
    settle(page, 800, "ss|mu|clim|")
    page.click("#when .mon button >> nth=6")
    settle(page, 800, "ss|mu|clim|07")
    check("July mean" in page.inner_text("#lyTitle") and "Optical" in page.inner_text("#lyRegime"), "seasonal cycle: " + page.inner_text("#lyTitle"))
    page.screenshot(path=str(shots / "05_ss_july.png"))

    # stretch scale + calendar click + place list + monitoring points
    page.click("#scaleSeg button[data-scale=auto]")
    settle(page, 600)
    rng = page.evaluate("(() => { const c = window.__portal.current(); return [c.lo, c.hi, c.stats.p02, c.stats.p98]; })()")
    check(rng[0] <= rng[2] and rng[1] >= rng[3], f"stretched scale {rng[0]}–{rng[1]} holds the layer's 2nd–98th percentile ({rng[2]:.2f}–{rng[3]:.2f}); ticks: " + page.inner_text("#lgTicks").replace("\n", " "))
    page.click("#scaleSeg button[data-scale=fixed]")
    page.click("#cal button.cal-c.built >> nth=40")
    settle(page, 800, "ss|mu|month|2019-05")
    check(page.evaluate("window.__portal.state.mode") == "month", "calendar click selects a month: " + page.inner_text("#lyTitle"))
    page.select_option("#jump", label="Daecheong Lake")
    page.wait_for_timeout(2300)
    c = page.evaluate("(() => { const m = window.__portal.map, c = m.getCenter(); return [c.lng, c.lat, m.getZoom()]; })()")
    check(abs(c[0] - 127.53) < 0.02 and abs(c[1] - 36.41) < 0.02 and page.input_value("#jump") == "", f"jump to Daecheong Lake: {c[0]:.2f}, {c[1]:.2f}, zoom {c[2]:.2f}")
    page.click("#btnPts")
    page.wait_for_function("window.__portal.points > 0 && window.__portal.map.getLayer('stations')", timeout=30000)
    settle(page, 900)
    pts = page.evaluate("[window.__portal.points, window.__portal.map.getLayoutProperty('stations', 'visibility'), window.__portal.map.queryRenderedFeatures({layers: ['stations']}).length]")
    check(pts[0] == 1194 and pts[1] == "visible" and pts[2] > 0 and page.locator("#lgPts").is_visible(), f"monitoring points: {pts[0]} loaded, {pts[2]} in view, key shown")
    page.screenshot(path=str(shots / "06_daecheong_points.png"))
    page.click("#btnPts")
    page.select_option("#jump", label="Daeho 2 (3201B20)")
    page.wait_for_timeout(2300)
    off = page.evaluate("""(() => { const m = document.getElementById('map').getBoundingClientRect(), d = document.querySelector('.pulse').getBoundingClientRect();
        return [d.left + d.width / 2 - m.left - m.width / 2, d.top + d.height / 2 - m.top - m.height / 2]; })()""")
    check(page.locator(".pulse-label").count() == 1 and page.inner_text(".pulse-label") == "Daeho 2" and abs(off[0]) < 3 and abs(off[1]) < 3,
          f"a monitoring point of the paper is marked at the centre of the map: {page.inner_text('.pulse-label')} (off by {off[0]:.1f}, {off[1]:.1f} px)")
    page.screenshot(path=str(shots / "07_paper_point.png"))

    for tab, shot in (("download", "08_download.png"), ("code", "09_code.png"), ("about", "10_about.png")):
        page.click(f".tab[data-tab={tab}]")
        page.wait_for_timeout(250)
        page.screenshot(path=str(shots / shot), full_page=True)
    page.click(".tab[data-tab=download]")
    links = page.evaluate("[...document.querySelectorAll('#dlProduct a, #dlOther a')].map((x) => x.href)")
    check(page.locator("#dlProduct tbody tr").count() == 6 and page.locator("#dlTable tbody tr").count() == 9 and len(links) == 18
          and all(u.startswith("https://zenodo.org/records/23750573/files/") for u in links), f"download tab: six grids, {len(links)} file links to the Zenodo record, nine years")

    # narrow screen
    page.set_viewport_size({"width": 430, "height": 860})
    page.click(".tab[data-tab=explore]")
    page.wait_for_timeout(1500)
    page.screenshot(path=str(shots / "11_phone.png"), full_page=True)
    over = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check(over <= 1, f"no horizontal overflow at 430 px (overflow {over}px)")
    ctx.close()

    # a link to a date without a grid, and one to a place
    ctx = new_context()
    p2 = ctx.new_page()
    p2.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    p2.goto(a.base + sep + "intro=0&date=2023-12-04&at=36.41,127.53" + ("&" + a.query if a.query and a.query != "intro=0" else ""), wait_until="domcontentloaded")
    p2.wait_for_function("window.__portal && window.__portal.ready && window.__portal.ready() && window.__portal.current() && !!window.__portal.current().vals", timeout=60000)
    p2.wait_for_function("document.querySelector('#recordBox') && !document.querySelector('#recordBox').hidden", timeout=60000)
    st = p2.evaluate("[window.__portal.state.date, window.__portal.state.pick && window.__portal.state.pick.row, window.__portal.state.pick && window.__portal.state.pick.col]")
    check(st[0] in ("2023-12-03", "2023-12-05") and st[1] == 222 and st[2] == 295, f"a link to 4 Dec 2023 (no grid) opens the nearest overpass ({st[0]}); ?at= picks the cell at Daecheong Lake (row {st[1]}, column {st[2]})")
    ctx.close()

    # the other two states of “From the paper”
    ctx = new_context()
    p3 = ctx.new_page()
    p3.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    p3.on("response", lambda r: bad.append((r.url, r.status)) if r.status >= 400 else None)
    extra = ("&" + a.query) if a.query and a.query != "intro=0" else ""
    p3.goto(a.base + sep + "intro=0&paper=off" + extra, wait_until="domcontentloaded")
    p3.wait_for_function("document.querySelectorAll('#abSkill tbody tr').length === 6", timeout=60000)
    off = p3.evaluate("[!!document.querySelector('#paper'), document.querySelectorAll('.novelty-more').length, document.querySelectorAll('#abSkill tbody tr').length]")
    check(off == [False, 0, 6], "?paper=off: no account of the paper and no links to it; the About tab keeps its skill table")
    if a.figures:
        p3.goto(a.base + sep + "intro=0&paper=figures" + extra, wait_until="domcontentloaded")
        p3.wait_for_function("document.querySelectorAll('#paper img').length === 6", timeout=60000)
        p3.evaluate("document.querySelectorAll('#paper img').forEach((im) => { im.loading = 'eager'; })")
        p3.wait_for_function("[...document.querySelectorAll('#paper img')].every((im) => im.complete && im.naturalWidth > 0)", timeout=60000)
        figs = p3.evaluate("[...document.querySelectorAll('#paper img')].map((im) => im.naturalWidth)")
        check(len(figs) == 6 and min(figs) >= 1200 and p3.locator(".fig-only").count() >= 2, f"?paper=figures: the manuscript's six figures load ({figs})")
        p3.screenshot(path=str(shots / "14_paper_figures.png"), full_page=True)
    ctx.close()

    # A browser that gives no WebGL context (graphics acceleration switched off, or lost for the session): the page
    # says so where the map would be instead of staying on its loading screen, and the rest of it works.
    VIS = "const vis = (q) => { const e = document.querySelector(q); return !!e && !e.hidden && getComputedStyle(e).display !== 'none' && e.getBoundingClientRect().height > 0; };"
    pc = new_context()
    pc.add_init_script("""(() => { const real = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function (type, ...rest) { return /webgl/i.test(String(type)) ? null : real.call(this, type, ...rest); }; })();""")
    ng = pc.new_page()
    ng.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    ng.goto(url, wait_until="domcontentloaded")
    try:
        ng.wait_for_function("document.documentElement.classList.contains('nomap') && document.querySelector('#boot') === null", timeout=30000)
        ng.wait_for_function("document.querySelector('#lyMean').textContent.trim() !== '—'", timeout=60000)      # the numbers came and the card is filled
    except Exception:
        pass
    st = ng.evaluate("() => { " + VIS + """ return {cls: document.documentElement.className.split(' ').filter((k) => k !== 'embed' && !k.startsWith('paper-')), boot: !!document.querySelector('#boot'), msg: vis('#noMap'),
        text: document.querySelector('#noMap').innerText, map: vis('#map'), legend: vis('#legend'), controls: vis('.map-tr'), hint: vis('#hint'), cards: vis('#cardLayer'),
        title: document.querySelector('#lyTitle').textContent, mean: document.querySelector('#lyMean').textContent}; }""")
    ng.click("#varSeg button[data-var=tn]")                           # the layer buttons drive the cards beside the map too
    try:
        ng.wait_for_function("document.querySelector('#lyTitle').textContent.includes('nitrogen')", timeout=30000)
    except Exception:
        pass
    t2 = ng.inner_text("#lyTitle")
    ng.click(".tab[data-tab=download]")
    ng.wait_for_timeout(400)
    dl_ok = ng.locator("#tab-download").is_visible()
    ng.click(".tab[data-tab=explore]")
    ng.wait_for_timeout(300)
    check(st["cls"] == ["nomap"] and not st["boot"] and st["msg"] and "WebGL" in st["text"] and "open it again" in st["text"]
          and not st["map"] and not st["legend"] and not st["controls"] and not st["hint"] and st["cards"] and st["mean"].strip() not in ("", "—"),
          "without WebGL the page says in the map's place why there is no map, and its loading screen goes: " + st["text"].splitlines()[0])
    check(t2 != st["title"] and dl_ok and ng.evaluate("() => { " + VIS + " return vis('#noMap'); }"),
          f"without WebGL the rest of the page works (layer card goes to '{t2}', the Download tab opens)")
    ng.screenshot(path=str(shots / "12_no_webgl.png"))
    pc.close()

    # A WebGL context lost while the page is open (the browser's graphics process failed): if it has not come back
    # after a few seconds the page says the map is gone; when it does come back, so does the map.
    pc = new_context()
    lc = pc.new_page()
    lc.on("pageerror", lambda e: console.append(("pageerror", str(e))))
    lc.goto(url, wait_until="domcontentloaded")
    lc.wait_for_function("window.__portal && window.__portal.ready && window.__portal.ready()", timeout=60000)
    lc.wait_for_function("document.querySelector('#boot') === null", timeout=15000)
    lc.wait_for_function("(() => { const c = window.__portal.current(); return !!c && !!c.vals; })()", timeout=60000)
    lc.wait_for_timeout(600)
    COLOURED = "(() => { const m = window.__portal.map; return ['cells', 'dots'].map((s) => [0, 4000, 8557].filter((id) => (m.getFeatureState({source: s, id}).t ?? -1) >= 0).length); })()"
    before = lc.evaluate(COLOURED)
    has = lc.evaluate("""() => { const c = window.__portal.map.getCanvas(), gl = c.getContext('webgl2') || c.getContext('webgl');
        const x = gl && gl.getExtension('WEBGL_lose_context'); if (!x) return false; window.__lose = x; x.loseContext(); return true; }""")
    if has:
        # while the context is lost the map has no style: the layer buttons, the opacity and a pick must still work, without an error
        lc.wait_for_timeout(400)
        lc.click("#varSeg button[data-var=wt]")
        lc.wait_for_function("document.querySelector('#lyTitle').textContent.startsWith('Water temperature')", timeout=60000)
        lc.evaluate("() => { const o = document.querySelector('#opacity'); o.value = 80; o.dispatchEvent(new Event('input')); window.__portal.pickCell(4000); }")
        lc.wait_for_function("document.querySelector('#recordBox') && !document.querySelector('#recordBox').hidden", timeout=60000)
        while_lost = lc.evaluate("[!!window.__portal.map.style, document.querySelector('#lyTitle').textContent, document.querySelector('#srTitle').textContent]")
        check(not while_lost[0] and while_lost[1].startswith("Water temperature") and "°N" in while_lost[2],
              f"while the WebGL context is lost (the map has no style) a layer change and a pick still fill the cards: {while_lost[1]} | {while_lost[2]}")
        lc.wait_for_timeout(2000)
        early = lc.evaluate("document.documentElement.classList.contains('nomap')")      # not at once: a context usually comes back
        try:
            lc.wait_for_function("document.documentElement.classList.contains('nomap')", timeout=12000)
        except Exception:
            pass
        gone = lc.evaluate("() => { " + VIS + " return {msg: vis('#noMap'), map: vis('#map'), noMap: window.__portal.noMap}; }")
        lc.evaluate("window.__lose.restoreContext()")
        try:
            lc.wait_for_function("!document.documentElement.classList.contains('nomap') && window.__portal.map.loaded()", timeout=30000)
        except Exception:
            pass
        lc.wait_for_timeout(800)
        back = lc.evaluate("() => { " + VIS + " return {msg: vis('#noMap'), map: vis('#map'), noMap: window.__portal.noMap, loaded: window.__portal.map.loaded(), zoom: window.__portal.map.getZoom()}; }")
        check(not early and gone["msg"] and not gone["map"] and gone["noMap"] is True,
              "a WebGL context lost while the page is open: after a few seconds without it the page says the map is gone")
        check(not back["msg"] and back["map"] and back["noMap"] is False and back["loaded"],
              f"when the context comes back the map returns (zoom {back['zoom']:.2f})")
        try:
            lc.wait_for_function(COLOURED + ".every((n) => n === 3)", timeout=20000)
        except Exception:
            pass
        after = lc.evaluate("[" + COLOURED + ", window.__portal.current().spec.key, window.__portal.map.getPaintProperty('cells-fill', 'fill-opacity')[6][2], (window.__portal.map.getSource('pick')._data || {}).type || '']")
        check(before == [3, 3] and after[0] == [3, 3] and after[1].startswith("wt|") and after[2] == 0.8,
              f"and its cells have their colours again, for the layer chosen meanwhile ({after[1]}), at the opacity set meanwhile ({after[2]})")
        lc.screenshot(path=str(shots / "13_context_restored.png"))
    else:
        notes.append("   (this browser has no WEBGL_lose_context: the lost-context check was skipped)")
    pc.close()

    errs = [c for c in console if c[0] in ("error", "pageerror")]
    check(not errs, f"no console errors ({len(errs)})")
    for c in errs[:12]:
        notes.append(f"   console {c}")
    warn = [c for c in console if c[0] == "warning" and "GL Driver Message" not in c[1] and "READ-usage buffer" not in c[1]]
    for c in warn[:8]:
        notes.append(f"   warning {c[1][:200]}")
    check(not bad, f"no failed or 4xx/5xx requests ({len(bad)})")
    for b in bad[:12]:
        notes.append(f"   request {b}")
    br.close()

print("\n".join(notes))
print("\n".join(fails))
print(f"\n{len(fails)} failed")
sys.exit(1 if fails else 0)
