# Korea inland water quality data portal

Web portal for the lab's 1 km gridded inland water quality dataset for mainland South Korea: water
temperature (WT), suspended solids (SS), chlorophyll-a (Chl-a), dissolved oxygen (DO), total nitrogen (TN)
and total phosphorus (TP) on each of the 1,012 dates of 2016–2024 that a cloud-free HLS S30 overpass
allowed, every value with a calibrated uncertainty (Lee, Lee, Lee and Kim, Data Descriptor under review at
*Scientific Data*; data: doi:10.5281/zenodo.23750573, CC BY 4.0). It shows every water cell of the product
on a map, as one date, a month, a calendar month or the whole record, and any cell's full record for all
six parameters.

**Status (2026-11-18): public on GitHub Pages** at https://hyunglok-kim.github.io/korea-water-quality-portal/
and listed on the lab dashboard under 🌏 연구자료 (`/wq-korea.html`, which embeds the public page). A line at the
top of every tab says the paper is under review at *Scientific Data* (the lab head, 2026-11-18: “지금 본 논문
Scientific Data에 심사중이야. 그렇게 넣자”). **The manuscript's figures are not published** (the lab head the
same day: “그림 공개는 아직하지 말자”): the public page shows the plain-words account with this site's own
charts; see “The paper's figures” below. **On hydroai.net/data since 2026-11-18** as the fifth card, `#wq`
(the lab head: “올려”, “데이터는 올려야 해”); see “The hydroai.net card” below. **On the lab's home page since
2026-11-20**: three blocks made here that remake its top (the lab head: “올리고 팝업은 쓰지 말자”). The
announcement dialog made the day before is **not used**, by that same decision. **A second round of the
blocks is live since 2026-11-21** (the satellites' picture behind the first screen, the datasets' order,
the Korean reworded; the lab head: “우선올려”). See the two sections on the home page below.

This portal follows the HDCA portal (`~/orca/projects/hdca/portal/`) in structure, look and dashboard
wiring; read that folder's `CLAUDE.md` for the shared background (the dashboard's 연구자료 mechanism, the
Webflow Data page). What differs is the data model: the product is sparse, so the browser gets the numbers
and draws the cells itself instead of projecting a field or reading map tiles (below).

## Where things are

| What | Where |
|---|---|
| Portal app (this folder) | `~/orca/projects/wq_korea/portal/` — static site, no build step; **git repository** pushed to github.com/Hyunglok-Kim/korea-water-quality-portal (GitHub Pages, branch `main`, root) |
| Public browse data | `data/` in this repository (catalog.json, two `.pmtiles` stores, stations.json, skill.json — 71 MB) |
| The manuscript's six figures (web copies) | `assets/figures/Fig2,4,5,6,7,8.webp` on the dashboard Mac only: the folder is in `.gitignore` until the lab head decides to publish them |
| The product (public) | Zenodo doi:10.5281/zenodo.23750573 (version 4; concept DOI 10.5281/zenodo.18502401): six ZIP archives by parameter, code, models, validation files |
| The product (lab storage, CPU server) | `/home/data_4/finished_projects/project_water_quality/datasets/predictions_1km/<year>/kr_wq_<param>_1km_<yyyymmdd>.tif` (6,072 files, 517 MB; the same files as on Zenodo, in folders by year) |
| Build workspace (CPU server) | `/data/personal_data/project_wq_portal/` (`scripts/`, `venv/`, `work/`, `out/`, `logs/`) |
| Browse data served to the lab | `~/.hydroai/datasets/wq-korea/` on the dashboard Mac (outside the Drive-synced tree) |
| Dashboard pages | `hydroai-dashboard/gateway/static/research-data.html` (hub), `wq-korea.html` (shell); registry `gateway/research_datasets.json` (entry `wq-korea`) |
| Manuscript and code (private) | github.com/Hyunglok-Kim/Gridded_South_Korea_Water_Quality_Dataset (Overleaf-synced) and `…_code`; clones under `~/.hydroai/repos/2026-gridded-south-korea-water-quality-dataset/`; review record `2026-gridded-south-korea-water-quality-dataset` on the lab dashboard |

```
portal/
  index.html          one page: Explore / Download / Use in code / About the data
  css/portal.css      the HDCA portal's stylesheet with this portal's additions at the end
  js/config.js        deployment settings (data location, DOIs, contact, what “From the paper” shows)
  js/app.js           the app (MapLibre GL + feature state + SVG charts), one IIFE
  assets/             logos, preview.jpg (link preview); figures/ (the manuscript's, not in the repository)
  data/               what the page reads (public copy)
  pipeline/           scan → store → stations → skill; runs on the CPU server, under a minute
  tests/smoke.py      headless-browser test (Playwright); field_ref.json holds reference values from the rasters;
                      make_preview.py re-makes assets/preview.jpg
  dev_server.py       local preview with HTTP Range support
```

## How the data reaches the map

```
6,072 GeoTIFFs (470 x 510, Float32, two bands)                         CPU server
  └─ pipeline/scan.py          reads every file once, checks grid / bands / the shared mask,
                               keeps only the cells with a value                      -> work/cube.npz, scan.json
  └─ pipeline/build_store.py   two stores + catalog + reference values                 -> out/, work/field_ref.json
       kr_wq_1km_fields.pmtiles   by date   (z 10)
           x = 12, y = year-2016        the cells with a value on each date of that year, in date order
           x = L,  y = year-2016        layer L for those same cell-days
           x = L,  y = 20               [13][cells]: mean over the whole record (0) and each calendar month (1..12)
           x = 13, y = 20               [13][cells]: number of dates with a value, same slots
       kr_wq_1km_series.pmtiles   by cell   (z 10, x = column, y = row)
           n, date index [n], then [12 layers][n]
       catalog.json               grid, the 8,558 cells, the 1,012 dates and their cell counts, encodings,
                                  statistics by month and year, the Zenodo file list
  └─ pipeline/stations.py      the 1,194 monitoring points (published list + WEIS names and coordinates) -> out/stations.json
  └─ pipeline/skill.py         the skill numbers, from the record's validation file (oof_predictions.csv)  -> out/skill.json
rsync to the dashboard Mac (~/.hydroai/datasets/wq-korea/) → copy into data/ here → push       (public copy)
```

Layer index L: 0 wt_mu, 1 wt_sigma, 2 ss_mu, 3 ss_sigma, 4 chla_mu, 5 chla_sigma, 6 do_mu, 7 do_sigma,
8 tn_mu, 9 tn_sigma, 10 tp_mu, 11 tp_sigma.

**Why numbers and not tiles or pictures.** Of the grid's 239,700 cells, 8,558 ever carry a value, and the
whole record is 1,529,676 cell-values per layer: 37 MB for both bands of all six parameters as 16-bit
numbers. So the page loads the cells' positions once (catalog.json), then one small entry per year and
layer for the map, and one entry of a few kilobytes for a clicked cell. The cells are GeoJSON squares
(and a second source of their centres, drawn as dots below zoom 8.6 so that 1 km cells stay visible from
afar); a cell's position on the colour ramp is its **feature state** `t` (0..1, −1 = no value), and a
layer switch only updates the cells whose `t` changed. Nothing is resampled, the cursor reads the stored
value, and "Play" needs no further requests within a year.

**Number contract.** Unsigned 16-bit, little-endian, 65535 = no value. `lin`: value = DN × 0.001 + offset
(WT value: offset −5 °C, so a negative temperature would fit; WT σ, DO value and σ: offset 0). `log`:
value = 0.001 × exp(DN × k), k = ln(10⁸) / 65534 (SS, Chl-a, TN, TP, value and σ): a constant step of
0.028 %. `build_store.py` asserts that nothing is clipped and prints the largest error (0.0005 absolute,
0.014 % relative). The record means, calendar-month means and counts in the stores are computed by the
pipeline from the rasters; month means are computed in the browser from the year entries (the smoke test
checks the two routes against each other).

**Why PMTiles as the container.** The lab dashboard's gateway serves only `.json` and `.pmtiles` from a
portal's data folder, and counts `.pmtiles` bytes for the hub card. A PMTiles archive is a range-readable
key-value store addressed by z/x/y; the addressing above is in each archive's metadata and in
`catalog.json` (`store`). Every entry is gzip-compressed (`tile_compression`); `pmtiles.js` inflates on
read. All entries of an archive sit at one zoom (10), because the reader refuses zooms outside the
header's range.

**One repository.** The stores are 36 MB and 38 MB, so everything fits one GitHub Pages site (files under
100 MB, site under 1 GB); no second repository as for HDCA.

## Rebuilding

Runs on the CPU server as `discover` (address, port, user and key are on the lab dashboard's server page and
in the lab head's notes); the whole run takes under a minute and little memory.

```bash
cd /data/personal_data/project_wq_portal
# copy pipeline/*.py and run.sh into scripts/ if they changed
scripts/run.sh all              # scan → store → stations → skill, a few seconds each
scripts/run.sh store            # only the stores and the catalog (after a change to build_store.py)
```

- `venv/` is `python3 -m venv --system-site-packages` plus `pip install pmtiles`; NumPy and GDAL come from
  the system (Python 3.10). No rasterio there: `scan.py` reads with `osgeo.gdal`.
- `run.sh store` asks Zenodo for the record's file list (names, sizes, checksums → the Download tab),
  `stations` for `station_fold_map.csv` and `skill` for `oof_predictions.csv` (20 MB, kept in `work/`).
  Zenodo refuses curl's default User-Agent from the lab network; the script sends its own.
- `ZENODO=<record number>` picks another version of the record. A new version with new grids means: put
  the new GeoTIFFs under `SRC`, run `all`, copy `work/field_ref.json` to `tests/`, update the DOI in
  `js/config.js`, in `index.html` (use strip, Download and About tabs, the paper credit) and in the
  dashboard registry, and the version string in `build_store.py`.
- Copy to the dashboard Mac and into this repository, then run the smoke test before pushing:

```bash
rsync -a --exclude '*.part' -e "ssh <lab CPU server options>" \
  <cpu-server>:/data/personal_data/project_wq_portal/out/ ~/.hydroai/datasets/wq-korea/
rsync -a ~/.hydroai/datasets/wq-korea/ data/
```

Each push of changed stores adds 74 MB to the repository's history, so publish per data version, not per
experiment.

## Running it

**Local preview**:

```bash
~/.venvs/hydroai/bin/python dev_server.py --port 8797        # http://127.0.0.1:8797/   (serves ~/.hydroai/datasets/wq-korea at /data/)
~/miniconda3/bin/python tests/smoke.py --base http://127.0.0.1:8797/index.html --query "intro=0&data=/data/" --shots /tmp/shots --ref tests/field_ref.json
~/miniconda3/bin/python tests/smoke.py --browser webkit  --base http://127.0.0.1:8797/index.html --query "intro=0&data=/data/" --shots /tmp/shots-safari --ref tests/field_ref.json
```

`python -m http.server` will not do: PMTiles needs HTTP Range requests. `--data data` serves this
repository's own copy instead of the dashboard Mac's.

What the test proves, beyond the page working: every layer of four dates and the whole record of four cells
read through the page equal the GeoTIFF values that `build_store.py` wrote to `field_ref.json` **before**
encoding (so it tests the encoding, the stores, the reader and the decoding together); 3 December 2023 has
4,565 cells, the number the paper gives for its product figure; a month mean computed from the by-date
store equals the one computed from the by-cell store; and every skill number on the page (37 in the text,
the About tab's table, the six-point table, the labels of the two bar charts) is the one in `skill.json`,
both as shown and as written in the page source. `--figures` adds the page with the manuscript's figures
(only where `assets/figures/` is served: the local preview and the dashboard copy). It ends with the two checks on the map failing (no
WebGL context; a context lost on a running page), as in the HDCA portal. Chromium runs with software
drawing (SwiftShader), so the test does not depend on the machine's graphics card; headless WebKit uses the
real one.

The Python examples of the “Use in code” tab were run against the real Zenodo archive (chlorophyll-a,
checksum verified): 4,565 cells on 3 December 2023, 177 overpasses at the Daecheong Lake cell — the same
177 the portal shows there. If you change an example, run it again (unzip an archive, run the snippet in
that folder). The R example has not been run (no R on the dashboard Mac).

**Public site**: test it with
`tests/smoke.py --base https://hyunglok-kim.github.io/korea-water-quality-portal/index.html --shots /tmp/shots-public --ref tests/field_ref.json`.
Pages rebuilds a minute or two after a push. Bump the `?v=` on the script and style tags in `index.html`
when you change them.

**In the lab dashboard**: `/wq-korea.html` (sidebar 🌏 연구자료) embeds the public site (`?embed=1`), the
way `hdca.html` does. The gateway also serves this folder at `/rd/wq-korea/` and the data at
`/rd/wq-korea/data/` for signed-in lab members (a fallback when github.io is unreachable):
`/rd/wq-korea/index.html?embed=1&data=/rd/wq-korea/data/&nas=/home/data_4/finished_projects/project_water_quality/datasets/predictions_1km`.
To run the smoke test against that copy, mint a session cookie as described at the top of
`gateway/research_data.py` and pass it as `SMOKE_COOKIE="hydroai_rd=<token>"`.

URL parameters the app understands: `embed=1` (fixed map height, the record card under the map, reports
its height to the parent frame), `hidefooter=1`, `data=/path/` (same-origin data location), `nas=/path`
(lab storage path shown in Download), `intro=0` (skip the opening flight), `tab=download|code|about`,
`var=wt|ss|chla|do|tn|tp|n`, `band=sigma`, `mode=all|clim|month|date`, `month=1..12` (calendar month),
`ym=YYYY-MM`, `date=YYYY-MM-DD` (a date without a grid opens the nearest overpass and says so),
`at=lat,lon` (picks the nearest cell and goes there), `pts=1` (monitoring points on),
`paper=text|figures|off` (what “From the paper” shows; overrides `js/config.js`).

## The paper's figures

The paper is under review at *Scientific Data* and its figures are published nowhere. The dataset, its README
and its validation files are public on Zenodo. **The lab head decided on 2026-11-18 not to publish the figures
yet (“그림 공개는 아직하지 말자”)**, after a first reading of “그렇게 넣자” as leave to publish them had been
announced and before anything was pushed. Do not switch them on without the lab head saying so. The public
page is built from the public material only:

- `paperSection: "text"` (the public setting): the six plain-words blocks, this site's own two bar charts and
  the six-point table. Every skill number in them is computed by `pipeline/skill.py` from `oof_predictions.csv`
  of the record and read from `data/skill.json`; they equal the manuscript's Tables 5 and 6 and the numbers
  of its Fig. 6 and Fig. 7 (checked 2026-11-18). What the text takes from the paper in words — which inputs
  each network relies on, the spread within a cell — is also in the record's public README.
- `paperSection: "figures"`: the same, with the manuscript's Fig. 2, 4, 5, 6, 7 and 8 beside the blocks. The
  web copies are in `assets/figures/` on the dashboard Mac (made with `pdftoppm -r 220` from the manuscript
  repository's `figures/fig_N.pdf`, 1800 px wide, WebP so that the dashboard's gateway serves them too) and
  **are not in the repository** (`.gitignore`). Lab members can see this version through the dashboard copy:
  `/rd/wq-korea/index.html?paper=figures&data=/rd/wq-korea/data/` (the dashboard page has a button for it).
- **To publish the figures** (only at the lab head's word; expected when the paper is accepted): delete the
  `assets/figures/` line from `.gitignore`, set `paperSection: "figures"` in `js/config.js`, bump its `?v=`
  in `index.html`, commit and push. Refresh the copies first if the manuscript's figures changed.
- `"off"` removes the section and the two links to it; the About tab keeps its skill table.

## The hydroai.net card

**Live at https://hydroai.net/data#wq since 2026-11-18**, at the lab head's word. hydroai.net/data is one HTML
Embed in Webflow, shared by every dataset's card and panel and edited by several sessions; its text is kept in
the HDCA portal's repository (`~/orca/projects/hdca/portal/embed/hydroai-data-page.html`, with the rules for
editing it in that folder's `CLAUDE.md` and `embed/tools/README.md`).

`embed/` here holds the card's loop (`media/wq-v1.*`: the six parameters in turn on the whole country, into
Daecheong Lake, chlorophyll-a there through the year), the tool that makes it (`tools/cap_wq.py`) and the
patch that was applied (`data-page-wq.patch.json`: the card, its panel with the HydroAI and GIST logo bar, its
routing, and the hub's columns for five cards: three across from 1700 px, five across from 2000 px). The
embed is now 33,673 characters, SHA-1 `911d4393…`; editor, live page and the HDCA repository's copy (fe99a9b)
are equal, and that repository's `check_captions.py` and `check_playback.py` pass on the live page.
`embed/README.md` has the details and how to change the card later.

**The card's facts repeat this portal's own** (1 km; 1,012 clear overpass dates, January 2016 to December
2024; six parameters, each with its uncertainty; “Data open on Zenodo (CC BY 4.0); paper under review at
Scientific Data”). When the paper is accepted, or the record changes, change the card's Status line too.
The panel frames the public page with `?embed=1&hidefooter=1`; the line at the top of the portal shows there.

## The home page announcement (made, not used)

**Made 2026-11-19; not used, by the lab head's decision of 2026-11-20** (“올리고 팝업은 쓰지 말자”, said when
the three blocks below went up: the reel's water quality entry, marked “New”, announces the dataset instead). Do not
put it on the site unless the lab head asks for an announcement again; the file and its tools stay for that day. The
lab head had asked for something on the first page, “a popup or the like”, so that a first-time visitor learns
the data are available. `embed/home-announcement.html` is one block for a Webflow Code Embed on the Home page: a dialog
that opens once per browser (the loop beside “New dataset · Now available”, the name, two sentences, three
numbers, the status line, one button to `/data#wq`), then a small pill at the bottom right until it is
followed or hidden; both stop after `ANN.until` (2027-02-28). It uses the card's loop above the text in
narrow windows and an upright version of it (`embed/media/wq-tall-v1.*`, made with the same tool) beside the
text in wide ones. `embed/tools/home_preview.py` shows it on a local copy of the live home page and
`embed/tools/check_home.py` checks it in three browsers. `embed/README.md` has the behaviour, the reasons and
how to change or retire it. Its facts repeat the portal's; no manuscript figure is in it.

## The home page's three blocks

**Live on https://hydroai.net/ since 2026-11-20**, at the lab head's word (“올리고 팝업은 쓰지 말자”). The
lab head asked for a more dynamic first page (“좀 더 동적으로”) and chose three of six ideas (“1,2,3 우선
해보자”). They are three Webflow Code Embeds on the Home page, whose text is three files in `embed/home/`
byte for byte; the files are kept in this repository because the tools for previewing and checking the home
page are here, not because they are about this dataset.

**Which files the site holds (read this first).** Since the publish of 2026-11-20 23:11 UTC (21 November,
08:11 in Korea) the site holds the three files as they are in commit `74650b6`: the **second round**, which
the lab head asked for after seeing the first one live and said to publish (“우선올려”). Seen after that
publish: the three files in the live home page byte for byte, nothing else on the home page changed, the
other pages as they were except the People page, and `check_home_new.py https://hydroai.net/` passing in
three browsers (116 checks in each). It was one publish with the People page's changes and new layout
(`embed/people/`, another session's work for the lab head), clicked by that session; `embed/README.md`
(“The second round”) says how the two were brought together. From 2026-11-20 13:37 UTC until then the site
held the files of `011ae9c`. **When a file here changes and the site has not yet, write that here first**:
until the publish the check fails on the live page, and the next reader must know why.

**Ahead of the site since 2026-11-21 (the commit after `09acf1e`): `hero.html` and `latest.html`.** Having
seen the second round live, the lab head asked for two corrections: the lists' pictures looked cut, with
“another picture” behind them (“News랑 publication 사진이 잘려서... 다른 그림으로 채워져 있는데 백그라운드가. 이거
고쳐줘”), and the soil moisture dataset's line must stress that the data are over dense vegetation (“설명을 over
dense vegetation에서 자료라고 강조해야 함”). Both are in the files and pass the check on the preview (122 checks
in each browser); they are **not in the Designer and not published**, which waits for the lab head's word.
Until then four of the check's lines about the pictures and one about that line fail on the live page.

- `hero.html`: the first screen. The title, one sentence and two buttons; beside them the lab's five open
  datasets in turn, each one's card loop playing once with its captions, in the order the lab head asked for
  (soil moisture, ET, SMAP error, validation site, water quality; water quality marked “New” until
  `REEL.newUntil`, 2027-02-28). Behind the whole panel, the picture the old first screen had: the
  Earth-observing satellites (`embed/media/home-sky-v1.jpg`, the site's own picture with the satellites'
  names taken out by `embed/tools/home_sky.py`). It takes the place of the old hero block and the two
  photographs.
- `latest.html`: “News” and “Recent publications”, the first three entries of `/events` and `/publication`,
  read from those pages when the home page opens. Nobody edits the home page for them.
- `about.html`: the lab in a paragraph with its two axes and the two photographs, then a recruiting band
  with the full call folded away; English or Korean, one at a time. It takes the place of the long paragraph
  above the green tiles, which is kept as `replaced-paragraph.html` (the old hero as `replaced-hero.html`).
  Its Korean was reworded in the second round and is not a line-for-line translation of the English.

`embed/tools/home_new_preview.py` (port 8814) serves the live page with this folder's three files in the
place of its three embeds, so a change is seen on the page as it is, and `embed/tools/check_home_new.py`
checks the preview or the live page in three browsers. The reel uses the cards'
768 px loops and, on large or dense screens, larger versions of all five kept in `embed/media/*-wide-v1.*`,
made by `embed/tools/wide_loops.py` from the other portals' own tools (their previews must be running).
`embed/README.md` has the behaviour, the words' origins, how the blocks went onto the site, the steps for
changing one there, and how to go back.

Things to keep when touching them:

- **A change is not done until the check has passed on the live page.** On the day they went up the local
  check passed and the live one failed: a bar clicked within 0.65 s of a change, on a loop that took longer
  than that to arrive, was left without its loop. The local copy had never been that slow.
- **Publishing sends out everything saved in the Webflow Designer, on every page.** Publish with only
  hydroai.net ticked (the staging domain stays unpublished), save a backup first, and tell any other session
  working on the site before publishing (on 2026-11-20 another session was redoing the People page).
  **When two sessions each have the lab head's word, make one publish, not two.** On 2026-11-21 the lab head
  had told this session to publish and, minutes later, chosen in the other one to publish with a People
  layout that was not yet in the Designer; a publish from here at once would have put live the very state
  just declined there. Read what was chosen in the lab head's own words, not in the other session's
  summary; keep one session in the Designer at a time; and let the session whose go-ahead names everything
  that goes out make the click.
- **A block file begins with its “block N of 3” comment and ends with its one script**: the preview finds a
  block on the live page by them.
- **The lists follow the pages' order, not the entries' dates.** The dates on the Events page are when an
  entry was made (an old AGU entry carries August 2026), so sorting by them would put old news first.
- **Every sentence of the old recruiting list stays on the page** (the folded call); the check compares it
  with `replaced-paragraph.html`. Shorten the band above it freely, not the call.
- **The first screen keeps one height** whichever dataset is on show; a new dataset's name and line must fit
  the room each width reserves (`.hh-reel-info` min-heights), and the check measures it at thirteen sizes.
- **A loop and its wide version share a timeline.** Re-make both together, rename both, and change the
  caption times in `REEL.slides` and on the Data page card.
- **No manuscript figure, no unpublished data**: the loops are the cards', drawn from the public portals.
- **The first screen shows what the lab is, not only its data.** The first version had no satellite picture
  and the lab head missed it at once (“첫페이지에 뭔가 위성 그림이 없으니까 어색해. 우리 연구실의 아이덴티티가
  좀 없는 느낌”). Keep the satellites on the first screen through any redesign.
- **Words on the picture are measured, not judged by eye.** The check pictures the panel with the letters
  taken out and holds every line's colour against the brightest of what lies behind it, at thirteen window
  sizes (4.5 : 1, large text 3 : 1). After a change to the picture, the veil, the dark pools behind the small
  text, or any text size or colour on the first screen, run it.
- **The picture is decoration.** `alt=""`, `aria-hidden`, no pointer events, behind everything; the page is
  whole when it cannot be fetched. Nothing a visitor needs may be only in it, and its own words (the
  satellites' names) are taken out because they crossed the page's.
- **The order of the reel is the lab head's** (soil moisture, ET, SMAP error, validation site, water
  quality). The first dataset's words and still are in the markup as well as in `REEL.slides`.
- **Korean text under the lab's name.** No dashes; sentences in 합니다체 with plain verbs; short lines as
  notes with noun endings; no “차세대”, “핵심”, “열정을 가진”, “~하기 위한 …” headings or labels translated
  word for word; never the same thing under a heading and again below it. The lab head's own sentences are
  changed as little as possible and each change is reported one by one. Have a second reader go over Korean
  text before the lab head sees it (`embed/README.md`, “The words”).

## The People page's block

**Live on https://hydroai.net/people since 2026-11-21** (the publish of 2026-11-20 23:11 UTC), at the lab
head's word. The lab head asked for the “Contact me” block to go and for a cleaner, more modern page, then
for the misspellings corrected, an Alumni group shown briefly, the visiting scholar taken off and no head
counts. One Webflow Code Embed on the People page, right after the navigation bar, holds
`embed/people/people.html` byte for byte; like the home page's files it is kept here because the tools for
previewing and checking the lab's Webflow pages are here.

The block has no content of its own. It reads the people from the CMS lists in the page's tabs, and the group
photographs and the motto from the block above them, and shows them its own way while the page's own section
is not shown: the first group (the PI) as a wide card, the others as cards with a profile that opens over
the page, a group whose tab is named “Alumni” as a name and one line (where the person is now). Whatever stops
it leaves the page as it was. `embed/people/README.md` has what a visitor gets, how a person's text is read,
how someone is moved to Alumni (`member_type` = `alumni`, Occupation = where they are now), how the block
went onto the site, how a changed file goes there and how to go back. `embed/tools/people_preview.py`
(port 8815) serves the live page with the file in the place of its embed; `embed/tools/check_people.py`
checks the preview or the live page in three browsers (134 checks in each on the live page).

Things to keep when touching it:

- **No content in the block.** A person is entered once, in the People collection.
- **Nothing a person wrote is dropped or cut without a way to the whole**; the check compares every word of
  every card with the page's own content.
- **The page must show without the block**, so the page's own section stays on the page.
- **A change is not done until `check_people.py https://hydroai.net/people` has passed**, and a publish
  sends out everything saved in the Designer (see the home page's list above).
- **This repository is public.** What was corrected in whose text, and other remarks about named people,
  are not written here; the lab head has that list.

## Rules that must survive any redesign

- **Say what kind of layer each parameter is.** SS, Chl-a and TP are optical retrievals; TN is a
  catchment-context estimate; WT and DO are meteorologically driven. The layer card names the kind and
  says what it can be used for (`HOWTO` in `app.js`, from the paper's Technical Validation and Usage
  Notes); the About tab has the table. Do not present all six as equally a “satellite measurement”.
- **None of the six replaces a measurement,** and the page says so (first box, About tab).
- **Never hide gaps, never fill them.** A date is an overpass, not a day; a cell without a value on a date
  is drawn empty and listed nowhere as zero. Month, seasonal and record means are this site's own
  averages over the dates with a value and say so (layer card, About tab “What this site adds”); the
  count of dates is a layer of its own.
- **The interval on the charts is the record's own.** The 95 % interval uses the asymmetric multipliers of
  `kr_wq_1km_metadata.json` (`CI` in `app.js`), with the lower limit floored at zero for SS, Chl-a, TN and
  TP. If a new version of the record changes them, change them here. DO's σ is not a filter; the σ layer's
  note says so.
- **1 km is the cell.** Cells are drawn as squares from zoom 8.4; below that as dots that are larger than
  a kilometre on screen, and the hint under the map and the About tab say so.
- **Numbers on the page are computed, or quoted from public text.** Counts come from `catalog.json`; skill
  numbers from `skill.json` (the page fills every `<span data-skill>` from it, the smoke test checks the
  page and its source). What is quoted rather than computed (the spread within a cell, the 52 predictions
  behind a cell, visits per year, matchups per point, the largest measured SS and TP, the dates without a
  file) is in the record's README or metadata as well as in the manuscript, and was checked against both on
  2026-11-18. A new version of the record means rerunning the pipeline and rereading those sentences.
- **The skill table gives the paper's numbers** (the network's single prediction, Tables 5 and 6). The
  grids carry the mean of the dropout passes, which scores within 0.04 of them except for total nitrogen
  followed through time (0.13, not 0.20); the table's note and the nitrogen layer card say so.
- **The line at the top of the page says where the paper stands** (`notice` in `js/config.js`: “The paper on
  this dataset is currently under review at Scientific Data. The data are open on Zenodo.”), on every tab and
  in every copy, as on the Prithvi-ET portal. The lab head asked for it (2026-11-18). Empty it at publication.
- **The paper is under review**: see “The paper's figures”. At acceptance: empty the notice, replace “under
  review” with the reference (use strip, Download and About tabs, the credit line, README, the dashboard
  registry and shell page, the hydroai.net card's Status line) and, at the lab head's word, publish the figures.
- **Fig. 2 of the manuscript still says “1 km daily gridded”;** the page's own words are “one grid per
  clear overpass, not one per day”, as the rest of the manuscript and the Zenodo record now say.
- **Basemap without labels.** Esri World Imagery, dimmed; the only names on the map are six cities, ten
  reservoirs and the monitoring points, all our own text. Public label layers bring the East Sea / Dokdo
  naming problem.
- **Colour ramps run dark to light** (lightness monotonic, checked), because the map is dark: a high
  value is bright and no value disappears into the basemap. WT uses inferno and Chl-a viridis, as in the
  paper's product figure; SS runs from umber to sand so that clear water is not painted rust; every σ
  layer is grey. The charts use one data hue and a de-emphasised grey (checked with the dataviz skill's
  validator together), and the three monitoring-point colours were validated as a set.
- **The monitoring points are the published list** (`station_fold_map.csv` of the record: 1,194 points,
  46,933 matchups) at the coordinates WEIS publishes; `stations.py` asserts both totals. The lab's
  matchup table has more points (1,344): never ship that list.
- **The retrieval code and manuscript repositories are private** and the portal does not link them; the
  code is public inside the Zenodo record, which the Download tab lists.
- **Never leave a visitor on the loading screen** (`webglWorks`, `noMap`, `LOST_WAIT`), as in the HDCA portal.
- **Every block inside `main` is either full width (1640 px) or centred.** Check layouts at 2048 CSS px
  wide (the lab head's display) as well as 1440 and 390 before saying a change is done.
- **The partner strip is HydroAI and GIST** (all four authors are at GIST); `?hidefooter=1` hides it.

## Layout notes

- Standalone page: the map column is sticky from 1061 px, so a cell can be picked while reading the cards
  beside it; the record (calendar) card is the third card on the right.
- Embedded (`?embed=1`): the frame is as tall as the page and nothing scrolls inside it, so nothing can
  stick; the record card goes under the map as a flat strip, which keeps the two columns even when a cell
  is picked.
- The opening: the map starts on the globe over East Asia and flies to the peninsula in 3.2 s while the
  cells fade up (`startIntro`; the fade is driven by `setOpacity` because data-driven paint properties do
  not transition). Any wheel, press or touch ends it. `?intro=0` and `prefers-reduced-motion` skip it.

## Gotchas already paid for

- **Zenodo has a newer version than the dashboard's link.** The review record's data link pointed to
  10.5281/zenodo.21393563 (version 3); the revised manuscript cites 10.5281/zenodo.23750573 (version 4).
  The six grid archives are byte-identical in the two (same MD5), so the portal's data are right for both.
- **A marker element must not set `position`.** MapLibre places markers absolutely; `.pulse-wrap` once had
  `position: relative`, became as wide as the map and sat at its left edge. The smoke test now measures
  where the mark lands.
- **Feature state needs the source loaded.** `paint()` does nothing until the map's `load` event, then
  paints the current layer; `tPrev` remembers what each cell was given.
- **A lost WebGL context takes the style with it.** MapLibre 5 puts its style away when the context is lost
  and builds it again when the context returns. While it is away every call that reaches for a layer throws
  (“Cannot read properties of null”), a rebuilt style refuses changes until it has loaded (“Style is not done
  loading”), and feature state is not part of a style, so the cells came back without colours. Found only on
  the public site, where the first layer's numbers arrive after the map's `load` event; with local data the
  test never touched the map during the loss. Hence `mapOK()` before every such call and `restoreMapState()`
  after `webglcontextrestored`; the smoke test now changes the layer, the opacity and the pick while the
  context is lost and counts the coloured cells afterwards.
- **Over the internet `current` is null for a moment after the map's `load` event.** Anything that waits for
  the page to be ready must wait for `current().vals`, not only for `ready()`.
- **GeoJSON simplification drops small squares.** The cells source has `tolerance: 0`; below zoom 7.5 only
  the dots are drawn.
- **A logarithmic chart axis cannot show a lower limit near zero.** The axis is set by the dots and the
  upper limits; a lower limit below it is cut at the axis and a note under the chart says so; the
  tooltip, the table and the CSV carry the limit itself.
- **NaN crosses from the page to Playwright as NaN,** not null; the test treats both as “no value”.
- **A full-page screenshot of the phone layout sometimes fails once** under software drawing (“Unable to
  capture screenshot”), and a page can take over a minute to settle when several headless browsers run at
  once. Retry before suspecting the page.
- **Bars drawn into a narrow box are drawn at the box's width** (`drawBars`): scaled down from the desktop
  drawing their labels were 6 px tall on a phone.
- **`rm -f dir/*` in zsh stops the whole command line when nothing matches.** Use `find … -delete`.
- **A timer set for one state fired in another** (the home page's reel, 2026-11-20). “Stop the picture that
  has faded out, 0.65 s from now” was right when it was set; a click in between gave that video the next
  dataset, and the timer stopped it. A delayed action checks that what it was set for still holds
  (`front === k && active === k`), and the check holds a loop back a second so that the case cannot hide
  behind a fast network.
- **Typed through the Chrome extension, a space in a Webflow button's label is dropped**; in a paragraph it
  is kept. “Read more” went live as “Readmore” for three minutes. The extension's space key inserts it. Read
  the Designer canvas back before publishing (its frame, `#site-iframe-next`, can be read from the page) and
  compare the published page with the preview afterwards.
- **The Chrome extension answers to one claude.ai account.** On 2026-11-21 the session doing the home page
  lost its browser between saving the embeds and the publish click (“Browser extension is not connected”,
  and the list of connected browsers empty, for seven hours). The cause, read afterwards from the session's
  own transcript (its `attachment` rows of type `session_context` and `credential_org` show which account
  it ran under, and when that changed): every session of the profile shares one sign-in, it had been moved
  to another account in another session, and the extension stayed signed in to the earlier one; the list
  emptied ten minutes after the change (the same had happened on 2026-11-18). Retrying does not help. Asked
  only to “log in again”, the lab head did, and nothing changed; told which account each side was on, they
  matched the two within minutes. So find the two accounts first, and say that either side can be moved to
  the other, or that a click on Publish does it. Never ask the other session to click for this one, least
  of all when its own click was refused.
- **An `overflow: hidden` box can still be scrolled by script.** The dark pools behind the first screen's
  small text reach past the panel's foot, so the panel had something to scroll to: `scrollIntoView` on a link
  inside it shifted its contents against the picture behind them on a phone. The panel has `overflow: clip`
  (after `hidden`, for browsers without it), and the check asks for exactly that scroll and asserts the
  panel's scroll position is still 0.
- **Finding letters in a picture: label first, widen afterwards.** Taking the satellites' names out of the
  home page's picture, widening the found pixels before labelling joined “SMAP” to the bright trail beside
  it, and the rule that drops whatever touches the edge of its box (a satellite, a trail) then kept the name
  in the picture. `home_sky.py` labels the pixels as found and widens each kept piece afterwards; its
  `--sheet` shows every name's place before and after.
- **A hit test needs its target inside the window.** `elementFromPoint` gives nothing for a point below the
  fold, so the check brings each button to the middle of the window (`window.scrollTo`) before asking what a
  click there would reach.

## Not done yet

- On hydroai.net, “technics” in the Home page's description (page settings: search results, link previews)
  and the Teaching page's tab title “Teching” are still as they were. The lab head was told of both on
  2026-11-20 and did not ask for them to be changed.
- The other ideas for the home page were not chosen: the three research sections as one moving block, a
  “now” element (satellite positions or values from the validation site), a globe to drag.
- On the People page, told to the lab head on 2026-11-21 and not asked to be changed: where the block does not
  run, the page's own Alumni tab shows the item's whole card (and the page's source holds it); the icon links
  that are “TBD”; the collection's template pages (`/people/<slug>`), which are the site template's “Teacher”
  page and which nothing links to. `embed/people/README.md` lists them.
- The manuscript's figures stay unpublished by the lab head's decision of 2026-11-18 (“그림 공개는 아직하지 말자”).
- The dashboard's three files for this dataset (`gateway/research_datasets.json`, `gateway/static/wq-korea.html`,
  `gateway/static/shared/nav.js`) are in that repository's working tree, live, and were left uncommitted on
  2026-11-18: commit them there when the lab head says so.
- The review dashboard's project record links Zenodo version 3 (10.5281/zenodo.21393563); the manuscript
  cites version 4 (…23750573). The grids are the same files in both.
- Regional or per-water-body summaries (click a reservoir for its mean series).
- The native 30 m predictions: not in the record, not on the site.
- Korean UI text, a dark page theme.
