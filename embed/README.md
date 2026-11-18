# On hydroai.net: the Data page card and the home page announcement

Two pieces of the lab's Webflow site are kept here: the dataset's **card** on hydroai.net/data (live), and an
**announcement** for the home page that tells a first-time visitor the dataset is available (made 2026-11-19,
**not on the site yet**: it waits for the lab head's word; see the second half of this file).

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

## The announcement on the home page

Asked for by the lab head on 2026-11-19: something on the first page, “a popup or the like”, so that a
first-time visitor learns that the data are available. `home-announcement.html` is that, as one block of
styles, markup and script for a Webflow **Code Embed** on the Home page. It changes nothing else on the page.

**Status: made and checked on a local copy of the home page; not on hydroai.net.** Putting it there changes
the lab's front page and means publishing the Webflow site, so it waits for the lab head's word, as the card
did.

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
reduced motion, blocked storage, the last day, a background tab); it exits with the number of failures.

### Announcing something else, or taking it down

- Another announcement: change the words and the loops, and give `ANN.id` a new value. Every browser then
  sees the dialog once more, including those that closed this one. Set `ANN.until`.
- Taking it down: delete the Code Embed from the Home page and publish. Nothing else refers to it.
