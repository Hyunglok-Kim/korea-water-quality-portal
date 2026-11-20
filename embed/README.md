# On hydroai.net: the Data page card, the home page's three blocks, and an announcement that is not used

Three pieces for the lab's Webflow site are kept here:

- the dataset's **card** on hydroai.net/data (live since 2026-11-18);
- three **blocks that remake the top of the home page** (**live since 2026-11-20**): the lab's datasets in
  motion on the first screen, news and papers that keep themselves up to date, and the long text cut down,
  with recruiting in one band. A **second round** (the satellites' picture behind the first screen, the
  datasets in the order the lab head asked for, the Korean reworded) is in these files and saved in the
  Webflow Designer since 2026-11-21, and **not yet published**: see “The second round” below;
- an **announcement** dialog for the home page (made 2026-11-19, **not used**: when the blocks went up the lab
  head decided against a popup, “올리고 팝업은 쓰지 말자”, 2026-11-20). The reel's water quality entry, marked
  “New”, announces the dataset instead.

Anything on hydroai.net means publishing the Webflow site, which sends out whatever is saved in the Designer,
so every change waits for the lab head's word, and other sessions working on the site are told before a
publish.

## The card on hydroai.net/data

hydroai.net/data is one HTML Embed in Webflow: a hub of dataset cards, one panel per dataset that frames the
dataset's portal, and a small routing script. Its text is kept in the HDCA portal's repository
(`hdca-data-portal: embed/hydroai-data-page.html`), with the rules for editing it in that repository's
`CLAUDE.md` and `embed/tools/README.md`. Several sessions edit that one embed, each for its own card.

This folder holds the fifth card, for the water quality portal. **It has been live at
https://hydroai.net/data#wq since 2026-11-18**, published at the lab head's word (“올려”). The embed as it is
now: 33,673 characters, SHA-1 `911d4393a1a8a7da5ebc13bfd967f34680c5ff6e`; the Designer's editor, the live page
and the HDCA repository's copy (`hdca-data-portal` fe99a9b) were compared and are equal. `check_captions.py`
and `check_playback.py` of the HDCA repository pass on the live page with all five cards.

| File | What it is |
|---|---|
| `media/wq-v1.mp4`, `.webm`, `.jpg` | The card's silent loop (768 × 432, 10.5 s, 0.4 MB) and its first frame, the still picture |
| `tools/cap_wq.py` | Makes the loop's frames from a running copy of the portal (what it shows, in its docstring) |
| `tools/encode.sh` | Frames → the three media files (the HDCA repository's script, unchanged) |
| `data-page-wq.patch.json` | The six exact replacements that put the card, its panel, its routing and the hub's columns for five cards into the embed; made against the live text before it (29,626 characters, SHA-1 `404c7920…`). **Applied on 2026-11-18**: it no longer applies to the live text and is kept as the record of what was changed |
| `tools/apply_patch.py` | Applies the patch to a copy of the embed and checks both SHA-1s |
| `home-announcement.html` | The home page announcement: one self-contained block for a Webflow Code Embed (below) |
| `media/wq-tall-v1.mp4`, `.webm`, `.jpg` | The announcement's upright loop (810 × 834, 10.5 s, 0.9 MB) and its first frame |
| `tools/home_preview.py` | Serves the live home page with the announcement put in, locally, to look at a change before it is published |
| `tools/check_home.py` | Checks the announcement in Chromium, WebKit and Firefox, on the preview or on the live page |

### The loop

The six parameters in turn on the whole country (record means: water temperature, suspended solids, dissolved
oxygen, total nitrogen, total phosphorus, chlorophyll-a), then into Daecheong Lake, where the dots become the
1 km cells they are, then chlorophyll-a there through the twelve calendar months, with a strip of months
marking which. Everything in it is drawn by the public portal from the public data. Its first frame, the still
picture, is the whole country with water temperature on it.

```bash
python embed/tools/cap_wq.py "http://127.0.0.1:8797/index.html?intro=0&data=/data/" frames/wq     # add 'test' for a handful of frames
embed/tools/encode.sh frames/wq/final wq-v1 embed/media 30 44 768 24
```

`frames/wq/timeline.json` gives the second at which each stage begins; the card's `data-caps` times in the
patch are those. A re-made loop gets a new file name (`wq-v2`), so that a cached copy of the old picture never
plays under new captions, and its caption times are re-made with it.

### The card's words

The facts on a card repeat its portal's own numbers (1 km; 1,012 clear overpass dates, January 2016 to
December 2024; six parameters, each with its uncertainty; data open on Zenodo, paper under review). When the
portal's numbers or the paper's status change, change the card.

### The hub's columns

With four cards the hub is four across from 1700 px, two by two from 1181 px, one column of horizontal cards
down to 761 px, stacked below. A fifth card would stand alone under four, so the patch adds: three across from
1700 to 1999 px (three and two), five across from 2000 px (the lab head's display is 2048 px wide: all five in
one row, each 382 px wide instead of 423). The narrower layouts are unchanged (two across gives two, two and
one). The lab head was told of this change before giving the word.

### Changing the card later

The embed is shared, and the Chrome extension that drives the Designer must be signed in to the same claude.ai
account as the Claude Code session (on 2026-11-18 it was not at first, and no session could open the Designer).

1. Ask the other portal sessions (ListAgents / SendMessage) whether anyone is editing the embed.
2. In the Webflow Designer (`…design.webflow.com/?pageId=<the Data page's data-wf-page>` → Navigator → Section →
   Code Embed → the pencil) read the editor's text (`document.querySelector('.cm-content')` → `cmTile || cmView`
   → `view.state.doc.toString()`) and compare its SHA-1 with the HDCA repository's copy. If they differ,
   somebody has edited the page since: start from the live text, never overwrite. The browser tool hides a
   bare 40-character hash in its output: compare inside the page and return true or false, or return the hash
   in groups of four.
3. Make exact replacements through `view.dispatch` (a dry run on a copy of the text first; each `find` must
   occur exactly once), Save & Close, reopen and hash, then Publish → hydroai.net only (the staging domain
   stays unticked) → “Publish to selected domains”.
4. Fetch the live page and compare; run `check_captions.py` and `check_playback.py` on it; look at every card.
5. Write the live text back to the HDCA repository's copy, commit and push there, and tell the other sessions
   the new SHA-1.

## The announcement for the home page (made, not used)

Asked for by the lab head on 2026-11-19: something on the first page, “a popup or the like”, so that a
first-time visitor learns that the data are available. `home-announcement.html` is that, as one block of
styles, markup and script for a Webflow **Code Embed** on the Home page. It changes nothing else on the page.

**Status: made and checked on a local copy of the home page; not on hydroai.net, and not to be put there.**
On 2026-11-20, when the three blocks below went up, the lab head decided against it (“올리고 팝업은 쓰지
말자”): the first screen now shows the dataset in the reel, marked “New”, and a dialog on top of
that would say the same thing twice. The file and its tools stay for an announcement that may be wanted later; what
follows describes it as it was made.

### What a visitor gets

- **The first time** a browser opens the home page, the page is shown first and after about a second a dialog
  comes in: the loop on one side, and on the other “New dataset · Now available”, the dataset's name, two
  sentences, three numbers (1 km, 6 parameters, 1,012 overpass dates), the status line (data open on Zenodo
  under CC BY 4.0; paper under review at *Scientific Data*) and one button, **Explore the data →**, which
  leads to `/data#wq`. “Maybe later”, the cross, Escape or a click beside the card close it.
- **After that** the dialog never opens again in that browser. A small pill stays at the bottom right
  (“New dataset · Inland water quality of South Korea →”) until the visitor follows it or hides it; whoever
  follows the button or the pill is not shown the pill again.
- **After `ANN.until`** (28 February 2027, Korea time) the block does nothing: an announcement that nobody
  remembers to take down should not say “new” for years. Change the date to keep it longer.
- Nothing is sent anywhere. What a browser has seen is one entry in its own `localStorage`
  (`hydroai-announcement`: `{id, seen, pillHidden}`). Where that cannot be written (storage blocked), the
  dialog is not shown at all, since it would return on every visit; the pill is.
- With reduced motion, or the browser's data saver, the picture is the loop's first frame and no video is
  fetched. In a tab opened in the background the dialog waits until the tab is looked at.
- It is a modal dialog for assistive technology too (`role="dialog"`, labelled by its title, focus moved into
  it and kept there by Tab, the page behind held still), and it is not printed.

### The two loops

Both are the Data page card's loop, stage for stage and second for second (same `timeline.json`), so one list
of captions serves both.

| Layout | When | Loop |
|---|---|---|
| Picture beside the text | windows from 881 px wide, and short wide ones (from 600 px wide, under 600 px high: a phone held sideways) | `wq-tall-v1`: upright (the country fills it), 540 × 556 CSS px drawn at 1.5×; nothing is drawn into the frames |
| Picture above the text | narrower windows | `wq-v1`, the card's own 16:9 loop, with its strip of months drawn in |

The page crops the upright loop to whatever shape the text beside it gives the picture (`object-fit: cover`),
so the strip of months is not in its frames: the script lights the months itself from the same timeline
(`ANN.months`, eight frames a month), where no crop can cut them. The style sheet's condition for “picture
above” and the script's (`stacked`) are the same media query on purpose; change them together.

```bash
python embed/tools/cap_wq.py "http://127.0.0.1:8797/index.html?intro=0&data=/data/" frames/wq_tall size=540x556 scale=1.5 pad=40,30,40,30 strip=none
embed/tools/encode.sh frames/wq_tall/final wq-tall-v1 embed/media 30 44 810 24
```

A re-made loop gets a new name (`wq-tall-v2`) and `ANN.tall` with it, as for the card.

### Its words

The same facts as the card and the portal (1 km; six parameters, each with a calibrated uncertainty; 1,012
overpass dates, 2016–2024; data open on Zenodo, CC BY 4.0; paper under review at *Scientific Data*). No figure
of the manuscript is used: the pictures are the public portal's own map. When the paper is accepted, change
the status line here together with the card's and the portal's top line.

### Looking at it and checking it

```bash
~/.venvs/hydroai/bin/python embed/tools/home_preview.py            # http://127.0.0.1:8813/   (?fresh shows the dialog again)
~/miniconda3/bin/python embed/tools/check_home.py                  # the preview, in Chromium, WebKit and Firefox
~/miniconda3/bin/python embed/tools/check_home.py https://hydroai.net/     # the live page, once it is there
```

`home_preview.py` fetches the live home page and puts this file before `</body>`, as the embed would; with
`--local-media` the loops come from `embed/media/` here, for a loop that is not pushed yet. `check_home.py`
lists what it checks in its docstring (first visit, later visits, every way out, thirteen window sizes,
reduced motion, blocked storage, the last day, a background tab); it exits with the number of failures. It
last passed on 2026-11-19, on the home page as it was before the three blocks; run it again on the page as it
is now before using the announcement for anything.

### If an announcement is wanted later

- Change the words and the loops, and give `ANN.id` a new value (every browser then sees the dialog once,
  including those that closed an earlier one). Set `ANN.until`.
- It would go on the Home page as one more Code Embed, last in Body. The reel waits behind the dialog while
  it is open (`dialog()` in `home/hero.html` looks for the announcement's element), which was tried on
  2026-11-20 in Chromium and WebKit.
- Taking it down again: delete that Code Embed and publish. Nothing else refers to it.


## The home page's three blocks

Asked for by the lab head on 2026-11-20: the first page should be more dynamic (“좀 더 동적으로”). Of six
ideas the lab head chose the first three (“1,2,3 우선 해보자”): the lab's own data in motion on the first screen; news
and recent papers that appear by themselves; the long text shortened, with recruiting in one band.
`embed/home/` holds them as three Webflow **Code Embeds**, each one self-contained (styles, markup, script).

**Status: live on https://hydroai.net/ since 2026-11-20**, at the lab head's word (“올리고 팝업은 쓰지
말자”), as the files of commit `011ae9c`: on that day the Home page's three Code Embeds held the three files
byte for byte, and `check_home_new.py https://hydroai.net/` passed in Chromium, WebKit and Firefox (264
checks).

**The second round is not on the site yet.** After seeing the live page the lab head asked for three changes
(“The second round” below); `hero.html` and `about.html` as they are here carry them and are saved in the
Designer's two embeds since 2026-11-21, the lab head has said to publish (“우선올려”), and the publish itself
is still to be done. Until then the site shows the files of `011ae9c`, the check as it is here fails on the
live page (it expects the new order and the picture), and this section describes the files, not the site.

| File | What a visitor sees | What it takes the place of |
|---|---|---|
| `home/hero.html` | The first screen: the title, one sentence, two buttons (Data, Opportunities), and beside them the five datasets in turn, each one's loop with its captions, its name, one line and its link; behind all of it the picture of the Earth-observing satellites that the old first screen had | The dark block with the title and two paragraphs over the satellite picture, and the two photographs under it |
| `home/latest.html` | “News” and “Recent publications”: the first three entries of the Events page and of the Publications page | Nothing: it is new |
| `home/about.html` | The lab in one paragraph and its two research axes beside the two photographs; then “Join HydroAI”: three kinds of position, the year's topics, and the full call folded away. English or Korean, one at a time | The long paragraph above the four green tiles (introduction in two languages, then the recruiting list) |
| `home/replaced-paragraph.html` | (not shown) That paragraph as it was on the site until 2026-11-20: the record of what was replaced, and what the check compares the folded call with | |
| `home/replaced-hero.html` | (not shown) The old hero block and the photographs' container as they were on the site until 2026-11-20: the record of the other things replaced | |

Nothing is sent anywhere by any of them, and none of them uses a figure of a manuscript: the pictures are the
loops made for the Data page's cards, from the portals' own public maps, and the picture behind the first
screen is the one the site has always had there.

### How each behaves

**The first screen.** The datasets come in the order the lab head asked for on 2026-11-20: soil moisture
(HDCA), 30 m ET, SMAP error, the validation site, water quality (the newest, marked “New” while it is on
show, until `REEL.newUntil`). Each dataset's loop plays once, then the next comes with a short dissolve;
five bars under the picture fill as they play, with the datasets' names under them where there is room. A
click on a bar shows that dataset; the round button pauses and plays. The whole picture and “Open dataset →” lead to
the dataset on the Data page. The loops stop while the tab is hidden, while the picture is scrolled out of
view, and while the announcement dialog (if the page has it) is open. Only the loop on show is fetched, and
the next one a few seconds before it is needed. A loop that cannot be fetched does not hold the reel: its
still picture stays for twelve seconds, then the next dataset comes. With reduced motion or the browser's
data saver nothing plays and no video is fetched until the visitor presses play; the bars still change the
dataset, as still pictures. The block keeps one height whichever dataset is on show (each width reserves
room for the longest name and line), so nothing below it moves.

**The picture behind it.** The Earth-observing satellites, the Moon and the Earth lie behind the whole panel
(on a phone behind its upper part, fading out before the dataset's picture), under a thin veil; it fades in
once it has arrived and is decoration only (no words for a screen reader, never in the way of a click). If it
cannot be fetched the panel is the dark green it was, and everything else works. See “The picture behind the
first screen” below for how it was made and how the words on it stay readable.

**The two lists.** They are read from `/events` and `/publication` when the home page opens: the list items
of each page's first tab, in the order the page lists them (the Events page's own order, not the dates on
the entries, which are when an entry was made). A paper whose address is not filled in on the Publications
page (“TBD”) leads to the Publications page; the others open in a new tab. What was read is re-used for
fifteen minutes within a browser tab (`sessionStorage`, `hydroai-home-latest-v1`). If a page cannot be read,
or is rebuilt so that nothing can be found in it, its list is left out, and if both are, the whole block is:
the check below says so when it happens. **Adding an entry to the Events or Publications page in Webflow is
all it takes for the home page to show it.**

**The section in two languages.** A visitor sees Korean if the browser's language is Korean and English
otherwise, can switch with the two buttons, and the browser remembers the choice (`localStorage`,
`hydroai-home-lang`). Without scripts both languages show, one after the other. The recruiting list that was
on the page is kept under “Read the full call” / “모집 내용 자세히 보기”, word for word but for one
misspelling corrected (가족기숙자 → 가족기숙사) and one Korean sentence reworded in the second round (“The
words” below); the band above it says the same more briefly, and the three cards lead to the Opportunities
page.

### The words

- The hero's sentence is the old hero's two paragraphs made into one (what the lab studies, with what, and to
  what end). The title is unchanged.
- The English introduction is the old one with its first sentence turned into the heading; the two research
  axes were only in Korean on the old page, and their English lines here are translations of those.
- The band's short lines (three positions, three topics) summarise the recruiting list and the Opportunities
  page; the list itself is in the folded call. When the list changes each year, change the three `.hh-chip`
  lines and the list in `.hh-call`, in both languages.
- The datasets' names and one-line descriptions repeat the Data page's cards. When a card changes, change
  its entry in `REEL.slides`. Year ranges are written with a hyphen here (“2015-2025”); the cards have en
  dashes.
- **The Korean was reworded on 2026-11-20**, when the lab head found that it did not read as a Korean
  researcher's own writing and asked for that to be put right. It is not a line-for-line translation of the
  English any more, and what was taken out shows what to keep out: dashes set into a sentence; “~하기 위한
  AI” as a heading (now “…예측하는 AI”);
  “그리고 최신 … 기술”, “차세대”, “핵심 기반”, “그 자체의 발전”, “이는 … 위한 시도입니다”, “열정을 가진”;
  an English noun phrase left standing as a fragment; labels translated word for word (“첫째 축” is “연구
  방향 1”); the same thing said under a heading and again under it (the Korean band has no sentence under its
  heading, the English one has). Sentences are in 합니다체 with plain verbs; the short lines of the cards and
  chips are notes with noun endings (“… 운영”, “… 파인튜닝”), as the lab head writes them. The first axis's
  text is the lab head's own and was left as it was; of the lab head's five sentences in the folded call, one
  was reworded (“… 방법론 적용 연구에 대한 열정을 가지고 있는 …” → “… 방법론을 적용해 연구하고 싶은 …”),
  and the check knows that one. Two places where the Korean and the English of the call say different
  things were so on the old page and were left for the lab head: “수재해 예측” (water-related disasters)
  beside “natural disaster prediction”, and “유출량 … 측정” (measurement) beside “runoff estimation”.

### The loops, in two sizes

The reel shows the Data page cards' loops (`media` in `REEL.slides`: 768 × 432, from the three portals'
repositories). Where the picture is drawn on about 1,100 screen pixels or more (a desktop or tablet with a
dense screen), it fetches a larger version of the same loop instead (`wide`), all five kept here:

| File | Size | Made with |
|---|---|---|
| `media/wq-wide-v1.*` | 1536 × 864, 10.5 s, 1.0–1.3 MB | `tools/cap_wq.py … size=960x540 scale=1.6` |
| `media/et-wide-v1.*` | 1536 × 864, 13.7 s, 2.0–2.6 MB | `tools/wide_loops.py et_cap` (the ET preview on the public copy of the tiles) |
| `media/hdca-wide-v1.*` | 1536 × 864, 10.5 s, 2.4–2.7 MB | `tools/wide_loops.py hdca_cap`, `hdca_compose` |
| `media/tca-wide-v1.*` | 1536 × 864, 9.5 s, 1.9–2.3 MB | `tools/wide_loops.py tca_cap`, `tca_compose` |
| `media/cvs-wide-v1.*` | 1280 × 720, 12 s, 1.0–1.4 MB (the drone mosaic is 1 m, no finer) | `tools/wide_loops.py cvs` |

`tools/wide_loops.py` runs the tools that made the card loops, unchanged, from their own repositories, with
the frames drawn at 1.6 device pixels per CSS pixel and the chart panels scaled with them; its docstring has
the commands. Camera, stages and frame counts are the same, so a wide loop has its card loop's timeline and
the card's captions fit both. The rules of those loops are their repositories' (`hdca-data-portal:
embed/tools/README.md`): only what is published is drawn; the ET loop is drawn from the public copy of the
tiles and its first caption names the background product; a re-made loop gets a new file name. When a card's
loop is re-made, re-make its wide one and change both names and the caption times in `REEL.slides`.

### The picture behind the first screen

The first page the lab had until 2026-11-20 showed its title over one picture: the Earth-observing
satellites streaming from the Moon's side towards the Earth. The first version of the new first screen left
it out, and the lab head missed it at once (“첫페이지에 뭔가 위성 그림이 없으니까 어색해. 우리 연구실의
아이덴티티가 좀 없는 느낌”). It is back as the backdrop of the whole panel: **the first screen has to show
what the lab is (satellites, Earth observation), not only its data.**

- **The file.** `media/home-sky-v1.jpg` (1500 × 1125, 139 kB, progressive), made by `tools/home_sky.py` from
  the site's own asset (`satellites.jpg`, 887 kB) with two changes. The nineteen satellite names printed in
  the picture are taken out, because behind the page's own words they read as broken text and at some window
  size one of them is always cut by the edge of the reel: each name is found inside a box placed by eye, as
  near-white pixels standing out from what is round them, and filled in from its surroundings. Pieces that
  touch the edge of their box are left alone (they are a satellite, a trail or a cloud), and the letters are
  labelled as found, not widened first: widened, “SMAP” joined the trail beside it and was left in. And it is
  saved smaller. `--sheet FILE` writes every name's place before and after, to look at. If the site's picture
  is ever replaced the boxes are wrong; a re-made picture gets a new file name, and `hero.html` with it.
- **In the block.** `.hh-hero-sky` is the panel's first child, behind everything (`z-index: -1` inside the
  panel's own stacking context), with `alt=""`, `aria-hidden` and no pointer events; the script holds it at
  opacity 0 until it has arrived. On a window of 960 px or more it covers the panel; below that it covers the
  upper 58 % and fades out, so that the dataset's picture does not sit on another picture.
- **Words stay readable by measurement, not by eye.** A thin veil lies over the whole picture, darker to the
  left and to the foot; the small text (the sentence, the dataset's name and line) has a soft dark pool behind
  it that runs down to the foot of the panel; the title and the label above it carry a text shadow.
  `check_home_new.py` measures the result at each of its thirteen window sizes: it takes a picture of the
  panel with the letters made transparent, and holds each line's colour against the brightest of what lies
  behind that line (the 97th percentile of luminance in its box, so that a single star does not decide it).
  Every line must reach WCAG's 4.5 : 1 (3 : 1 for large text), also when the picture cannot be fetched.
  After any change to the picture, the veil, the pools or the text, run it.
- **The panel clips, it does not hide.** `.hh-hero` has `overflow: hidden; overflow: clip`. With `hidden`
  alone the panel is a box that can be scrolled inside itself, and `scrollIntoView` on something in it shifted
  its contents against the picture on a phone; `clip` cannot be scrolled (`hidden` stays for browsers
  without `clip`). The check asserts that the panel's scroll position stays 0.

### Looking at it and checking it

```bash
~/.venvs/hydroai/bin/python embed/tools/home_new_preview.py                 # http://127.0.0.1:8814/
~/.venvs/hydroai/bin/python embed/tools/home_new_preview.py --local-media   # this repository's loops from embed/media/ (for a loop that is not pushed yet)
~/miniconda3/bin/python embed/tools/check_home_new.py                       # the preview, in Chromium, WebKit and Firefox
~/miniconda3/bin/python embed/tools/check_home_new.py https://hydroai.net/  # the live page
```

`home_new_preview.py` fetches the live home page with its Events and Publications pages and puts this
folder's three files in the place of the page's three Code Embeds, so a change to a block is seen and checked
on the page as it is before it goes into the Designer; with the files as published it serves the live page
byte for byte. `/?live` shows the page as it is on the site, `/?lang=ko` or `en` sets the section's language.
`check_home_new.py` lists what it checks in its docstring (the page's structure; the picture behind the first
screen, and that the words on it can be read; the reel through all five datasets in their order, a click on a
bar at any moment, pause, a hidden tab, scrolling away, loops that cannot be fetched, reduced motion; the two
lists against the two pages, and either page unreadable; the two languages, and every sentence of the
replaced recruiting list still on the page; thirteen window sizes): 116 checks in each browser. It exits
with the number of failures. **Run it on the live page too, not only on the preview**: the one defect so far
showed only there (below). It describes the files as they are here, so it passes on the live page only once
the site holds them.

### How it went onto the site (2026-11-20)

In the Webflow Designer, on the Home page (`data-wf-page` 640cbd423ecaf883c33aa530), after saving a backup
(Cmd+Shift+S: “Before the home page's new blocks (2026-11-20)”, the site as it was):

1. In the hero's container (`teaching-detail-wrap hero`): a **Code Embed** with `home/hero.html` was added,
   and the old `hero-block` and the photographs' container (`container-6`) were deleted
   (`home/replaced-hero.html` keeps them).
2. Last in the first section (`section hero-home`), after the two navbars: two **Code Embeds**,
   `home/latest.html`, then `home/about.html`.
3. The long paragraph above the tiles (`home/replaced-paragraph.html` keeps it) and the stray “Heading” at
   the foot of the page were deleted; “Rede more” and “improvments” in the Satellite Remote Sensing section
   were corrected.
4. Published with only hydroai.net ticked (13:16 UTC). The other pages came out byte for byte as they were,
   but for the publish stamp and the names of the style and script bundles; the backups list showed that
   nobody had worked in the Designer since the publish of 18 November.

Two things then had to be put right, each with one more publish:

- **“Readmore”.** The label typed into the button had lost its space: typed through the Chrome extension, a
  space in a *button's* text is dropped (in a paragraph it is kept). Seen in the comparison with the preview,
  corrected with the space key, published again (13:19 UTC). Read the canvas text back before publishing.
- **A bar clicked just after a change.** The check on the live page failed where the local one had passed:
  0.65 s after a change the reel stops the picture that has faded out, and a bar clicked within that time had
  just given that video the next dataset. Where the loop took longer than that to arrive, it was stopped
  before it began, the loop before went on playing under the new words, and twelve seconds later the reel
  moved on. `hero.html` was corrected (the timer leaves a video alone once it has a new dataset to show),
  the check got the case with a loop held back a second, and the embed was replaced (13:37 UTC).

Not changed, because not asked for: “technics” in the Home page's description (page settings; it shows in
search results and link previews) and the Teaching page's tab title “Teching”.

### The second round (2026-11-21): saved in the Designer, not yet published

After seeing the live page the lab head asked for three things:

- “첫페이지에 뭔가 위성 그림이 없으니까 어색해. 우리 연구실의 아이덴티티가 좀 없는 느낌”: the satellites'
  picture is behind the first screen again (“The picture behind the first screen” above).
- “오른쪽 데이터 셋 수질 먼저 나오지 말고, 토양수분, 증발산, 토양수분 에러, 코어사이트, 그리고 수질 자료
  나오게 해줘”: the reel's order. Water quality is last and keeps its “New” mark; the first dataset's words
  and still picture in the markup are HDCA's now.
- The Korean wording, which did not read as a Korean researcher's own: the Korean of `about.html` was
  reworded, after two independent rewrites were compared and the result read once more (“The words” above).
  The English is as it was.

`hero.html` and `about.html` changed (commit `74650b6`); `latest.html` did not. On a preview that carries
exactly these files, with the picture and the loops from the public site, the check passed in Chromium,
WebKit and Firefox (116 each).

In the Designer, on 2026-11-21, after the backup “Before the home page's second round (2026-11-21)”: the
text of the first and of the third Code Embed was replaced with the two files and each embed was opened
again and found equal to the pushed file. The lab head said to publish (“우선올려”). **The publish has not
happened yet**: the browser connection used for the Designer was lost just before it (see step 4 of
“Changing a block on the site”). The same publish will also send out what another session saved for the
People page that night (the “Contact me” block removed, misspellings corrected, the “Visiting Scholars” tab
made “Alumni”), which the lab head asked for there and was told of here.

After the publish, by whoever clicks it: fetch the pages and see that the home page is the page from before
with these two embeds exchanged and that the pages nobody worked on are unchanged, run
`check_home_new.py https://hydroai.net/`, and bring this section and the status above up to date.

### Changing a block on the site

1. Edit the file; look at it in the preview; run the check on the preview. Keep the file's first comment
   (“block N of 3”) and its one script at the end: the preview finds the block on the live page by them.
2. Push, so that the file is on the portal's GitHub Pages site.
3. Tell any other session working on hydroai.net (a publish sends out everything saved in the Designer).
4. In the Designer: Navigator → the Code Embed (the hero's is inside `Teaching Detail Wrap`; the other two
   close the first Section) → Enter opens its editor → replace the whole text → Save & Close. Through the
   Chrome extension the editor is CodeMirror and takes the text with one `view.dispatch` (the page may
   `fetch` the file from GitHub Pages, or from raw.githubusercontent.com at the commit, with
   `cache: 'no-store'`); open the embed again and compare before publishing. Save a backup first
   (Cmd+Shift+S) and name it. **The Chrome extension answers only to sessions signed in to the claude.ai
   account it is signed in to**: on 2026-11-21 the session doing this was cut off between “Save & Close” and
   the publish (apparently by a login under another account in another session), and no retry brings it
   back (no browser is listed as connected); the lab head has to sign the session in again, or click
   Publish.
5. Publish with only hydroai.net ticked. Fetch the live page and see that the file is in it byte for byte,
   and that the pages nobody worked on are the same but for the publish stamp and the bundles' names, then
   run `check_home_new.py https://hydroai.net/`.

**Going back.** To the first round's blocks: put `hero.html` and `about.html` of commit `011ae9c` back into
the first and third embeds (`git show 011ae9c:embed/home/hero.html`). The Webflow backup “Before the home
page's second round (2026-11-21)” is the site with the first round's blocks and with the People page edits
saved by then; “Before the home page's new blocks (2026-11-20)” is the whole site as it was before any of
this. Restoring a backup also undoes whatever anyone has changed on any page since, so ask first. By hand,
all the way back: delete the three embeds and build the old hero and paragraph again from
`home/replaced-hero.html` and `home/replaced-paragraph.html`.

### Changing it later

- **A new dataset.** Add an entry to `REEL.slides` with `isNew: true` and set `REEL.newUntil`: after that day
  nothing is marked new, so the mark never outstays its news. Where it goes in the order is the lab head's to
  say (water quality, the newest, was moved from first to last on 2026-11-20). The first entry's name, line,
  link and still picture are also in the markup, for a page without scripts: change both together, and the
  order in the check (`SLIDES`, `FIRST_CAPS`).
- **More or fewer entries in the lists.** `CFG` in `home/latest.html`.
- **The Events or Publications page is rebuilt.** Run the check; if a list is gone, the selectors in
  `read` (in `home/latest.html`) need the new page's class names.
- **The year turns.** The band's label carries the year (“Topics for 2026” / “2026년도 연구 주제”, as the old
  page's list did); change it with the chips and the folded call (see “The words”).
- **Korean text.** Keep to what “The words” says of it, and have a second reader go over it before it is
  shown to the lab head.
