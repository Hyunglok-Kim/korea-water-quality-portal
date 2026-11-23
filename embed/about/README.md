# The About page of hydroai.net

Asked for by the lab head on 2026-11-22: the About tab had grown very old, and was to be remade with the
lab's dashboard as the reference, in the manner of the tabs the other sessions had remade (“지금 홈페이지
About 탭이 매우 오래되었어. 우리 대시보드 참고해서 좀 더 멋지고 고급지게 업데이트 해줘. 다른 세션 참고해.”). On seeing the first
preview he had the photograph at the top and the four counts (journal papers, conference presentations,
projects, datasets) taken off (“맨 위 사진이랑 저널 페이퍼 등 숫자 나온 것 지워”); they are not to come back. Then
he had the panel with the globe put first and what stood above it moved under it and made smaller (“Three
vantage points < 이 영상 먼저 오게 해. 그리고 그 위 내용들 아래로 내리고 좀 축소해.”).

`about.html` is the design: one block for a Webflow **Code Embed** on the About page (`/about`, page id
`640cbd423ecaf8419d3aa521`), right after the navigation bar, in the place of the page's four old sections.

**Status: live on hydroai.net since 2026-11-22 15:44:35 UTC (00:44 KST on the 23rd)**, at the lab head's
word (“올려”, then “게시해”). The page holds this file of commit 73070f9 byte for byte as the Code Embed right
after the navigation bar; the page's three old sections and its instance of the CTA component (“Contact me”)
were deleted, and the component keeps its other instances. Webflow backup from just before: “Before the About
page's new layout (2026-11-23)”. Compared with a copy of every page made right before the click, only the
About page changed.

| File | What it is |
|---|---|
| `about.html` | The block: styles, the page's words, and a script (about 31,000 of the 50,000 characters an embed may hold) |
| `replaced.html` | The four sections the page held before, as they were on 2026-11-22. For the record; used nowhere |
| `../media/about/` | The globe: `orbit-v1.js`, its library `orbit-lib-v1.js`, the land `orbit-land-v1.json`, the orbits `orbit-tle.json` |
| `../tools/about_tle.py` | Writes `orbit-tle.json` anew from CelesTrak |
| `../tools/about_preview.py` | Serves the live page with this file on it and the old sections taken out, locally (port 8819) |
| `../tools/check_about.py` | Checks the block in Chromium, WebKit and Firefox, on the preview or on the live page |

## What the dashboard gave

The dashboard is where the lab is written down as it is today, and it has one page that looks like nothing
else: the satellites over the globe. Both went into this page.

- **What the lab has and does**: the satellites it follows, its computing and storage, its field equipment,
  the weekly journal club. Only what a visitor may know; no names, no money, no unpublished work, no address
  of a machine.
- **The globe**: the dashboard's satellite page made anew for the site, in the site's colours.

The look is the site's own (the cream page, the green, Plus Jakarta and Satoshi), as on the other remade
tabs; the dashboard's ivory and serif stay where they are.

## What a visitor gets

The page as it was: a headline from the template, four green tiles, “How we do?” in four steps (one of them
“Big data wangling and mining”), three tiles, and the block “Contact me”.

With the block, in the order the lab head set:

1. **Three vantage points** (the dark panel, first on the page and holding its title): the globe with the
   satellites the lab follows, beside what it measures from orbit, from the air and from the ground.
2. **About HydroAI**, smaller: the statement (“AI for observing, understanding and predicting the Earth
   system”), two paragraphs, and who leads it.
3. **The two research axes**, smaller, in the home page's words.
4. **How we work**: observe, model, learn, share; and with what (computing, data, field).
5. **Open data**: a row for each dataset of the Data page, leading to it.
6. **Working with others** and **Teaching and training**.
7. **Find us**, and the band “Join HydroAI”.

The page has no title “About” of its own: the panel's headline is the page's `<h1>`, and the navigation bar
marks the tab.

No photograph of the lab and no counts. English only, like the People, Projects and Publications blocks.

## What is written and what is read

Unlike the other remade tabs this page has no collection behind it, so the block holds its own words. One
thing would go stale, and it is read from the site when its part of the page comes near: the datasets. The
rows are the Data page's cards (`/data`: name, kind, picture, address), in its order; the five rows in the
markup are the fallback for a visitor without scripts or when the Data page does not answer.

Everything else is written in the markup: the statement and the paragraphs, the axes (the home page's
wording, `../home/about.html`), the three lines about the field site (they repeat the Data page's card
“NASA-GIST Core Validation Site”; the check compares the figures), the steps, the three lines about
equipment, the two cards and the address.

## The globe

`../media/about/orbit-v1.js` draws it. The panel is the top of the page, so the block asks for the file at
once; a plain dark disc stands in the globe's place meanwhile (`data-orbit="wait"` on the stage), with the
room the globe's clock, chips and source line will take kept around it, so that the text under the globe
does not jump when it arrives on a phone or a tablet (`room()` in the block's script); and a
picture (the home page's sky, `data-pic` of the stage) is fetched and shown only when the globe cannot be
drawn (`"off"`). A visitor without scripts gets the picture from the `<noscript>` in the stage.

- **What it shows:** the globe opened on Korea, the field site, each satellite as a dot in its family's
  colour with the path behind and ahead of it, the night side, a clock (sixty times faster than time, or
  live), a chip for each family, and for a satellite pointed at or chosen a card: instrument, what it is
  used for, its height now, its mission page. The globe turns when dragged.
- **Where the positions come from:** worked out in the visitor's browser with SGP4 (satellite.js) from the
  orbital elements in `orbit-tle.json`. Nothing is asked of a server of the lab's. When that file is more
  than a week old the browser asks CelesTrak itself, once, and remembers the answer for a day.
- **The satellites** are the roster at the top of `orbit-v1.js` (33 on 2026-11-22, the dashboard's list with
  the mission links that had died replaced). `../tools/about_tle.py` reads the catalogue numbers from it and
  writes `orbit-tle.json` anew; run it before a push when the file is older than a few days.
- **The swaths** (asked for by the lab head on 2026-11-23: “위성이 지나갈 때 실제로 overpass swath가 그 위성
  모양으로, 그리고 어떤 unique한 자료 색으로 지나가게 … 실제 자료가 아니더라도 그 느낌이 나게”): each instrument
  leaves its swath on the ground behind it, in its own shape (SMAP's 1000 km conical scan, ASCAT's two strips,
  a radar's strip to one side, SWOT's two narrow strips, ICESat-2's beams, CYGNSS's four specular-point tracks)
  and in the colours of what it measures (GPM rain, SMOS soil moisture and salinity, AMSR2 water vapour, MODIS
  ET and land temperature, Sentinel-1 speckle, ocean colour ...), fading over the twelve minutes of path. The
  fields are **illustrative, not data**: noise shaped by latitude, season, deserts, coasts and the Sun, the
  same field for every satellite that measures the same thing; the source line under the globe and the card
  say so. At the satellite, what the instrument does now is drawn (the spinning beam, the scan line, the fan
  beams); a picked satellite's card names its swath and the colours, and CYGNSS's shows four delay-Doppler
  maps. `SPEC` and `FIELDS` at the top of `orbit-v1.js` hold it all. The ground is a 0.25° grid kept in the
  browser (about 7 MB); drawing it costs about 2 ms a redraw in Chromium. Live since 2026-11-23 05:11:59 UTC
  (commit 7112dc0, at the lab head's word “올려”); `check_about.py` on the live page right after: 0 failed in the
  three browsers.
- **The colours** of the four families were checked for colour-blind separation on the dark panel; every
  satellite also has its name beside it and the chips name the families, so colour is never the only sign.
- The head of `orbit-v1.js` says how it is built; `HydroOrbit._state()` is what the check reads.

The number of satellites in the block (“33 satellites”) is the globe's roster; the block takes it from the
globe when it is drawn, and the check fails when the figure in the markup differs.

## Looking at it

```bash
~/.venvs/hydroai/bin/python embed/tools/about_preview.py          # http://127.0.0.1:8819/about
~/.venvs/hydroai/bin/python embed/tools/check_about.py            # the preview, three browsers
~/.venvs/hydroai/bin/python embed/tools/check_about.py https://hydroai.net/about      # the live page, once the block is on it
```

`/about?old` is the page as the site has it, `?keep` the block with the old sections left under it,
`?nofetch` the page when the Data page cannot be read. On 2026-11-22 the check passed on the preview in the
three browsers (58 checks each, 0 failed), and the page was looked at at 2048, 1440, 390 and 320 px. On the live page,
right after the publish, it passed in the three browsers too (57 checks each: the embed's size is checked on
the preview only), 0 failed.

## How it went onto the site

Done on 2026-11-22 (UTC) as below. One session in the Designer at a time; tell the other site sessions before
and after.

1. Commit and push `embed/about/`, `embed/media/about/` and the three tools (the globe's files are served
   from GitHub Pages, and the embed's text is taken from the pushed file). Wait for Pages to serve
   `embed/media/about/orbit-v1.js`.
2. `embed/tools/site_snapshot.py fetch DIR` (every page as it is before).
3. A named backup in the Designer (Cmd+Shift+S).
4. The Designer on the page: `https://hydroai-a33ac7.design.webflow.com/?pageId=640cbd423ecaf8419d3aa521`.
5. Select the navigation bar in the Navigator, add a Code Embed (it lands right after the bar), put this
   file's text into it, Save & Close, open it again and compare.
6. Delete the page's four old elements under it, one at a time, reading the selection before each Delete:
   three Sections (`hero-about-us`, `course-process`, `process-tiles`) and `CTA`, the green row of the
   site's “Contact me” component. Delete only this page's instance; the component keeps its other instances
   (seven on 2026-11-22).
7. Publish to hydroai.net only, at the lab head's word.
8. `site_snapshot.py fetch` again and `compare`; `check_about.py https://hydroai.net/about`.

**Going back:** restore the named backup, or delete the Code Embed, put the four sections back from
`replaced.html` by hand, and publish.

## Changing things later

- **The words:** the markup in `about.html`.
- **The datasets:** nothing; they follow the Data page. When `check_about.py` notes that the markup's rows
  are no longer the Data page's, write the new ones into the markup (they are what a visitor without scripts
  sees).
- **The field site's figures:** the three `.ha-view` lines, when the Data page's card changes; the check
  fails until they agree.
- **The satellites:** the roster in `orbit-v1.js`, then `about_tle.py`.
- **The globe's layout** (its clock, chips or source line): the figures in `room()` in the block's script
  follow it; `check_about.py` fails when the text under the globe moves more than 45 px as it arrives.
- **The design:** edit `about.html`, look at the preview, run the check, put the file into the embed (select
  it, Enter, replace the text, Save & Close, open it again and compare), publish, check the live page.

## Things to keep

- **Only what a visitor may know.** The dashboard also holds what is not for the site: people's details,
  funding, work that is not published, the addresses of machines. None of it belongs in this block or in
  this (public) repository.
- **The page must be whole without scripts** and when nothing can be read: every word, the figures and the
  rows of the markup, the picture in the globe's place.
- **The order is the lab head's:** the panel with the globe first, then the lab and its research, smaller.
- **No photograph of the lab at the top and no counts** of papers, presentations, projects or datasets: the
  lab head had them taken off.
- **No address the block uses is the id of an element**: the site's own script scrolls to any id a clicked
  link names.
- Every block is centred in the page's 1,348 px; check at 2048, 1440 and 390.
- The file is plain ASCII, so that it survives any editor.
