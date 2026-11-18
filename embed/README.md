# The card for hydroai.net/data — made, not yet published

hydroai.net/data is one HTML Embed in Webflow: a hub of dataset cards, one panel per dataset that frames the
dataset's portal, and a small routing script. Its text is kept in the HDCA portal's repository
(`hdca-data-portal: embed/hydroai-data-page.html`), with the rules for editing it in that repository's
`CLAUDE.md` and `embed/tools/README.md`. Several sessions edit that one embed, each for its own card.

This folder holds what a fifth card for the water quality portal needs. **Nothing here is on hydroai.net.**
Putting it there changes the lab's public Data page and means publishing the Webflow site, so it waits for the
lab head's word.

| File | What it is |
|---|---|
| `media/wq-v1.mp4`, `.webm`, `.jpg` | The card's silent loop (768 × 432, 10.5 s, 0.4 MB) and its first frame, the still picture |
| `tools/cap_wq.py` | Makes the loop's frames from a running copy of the portal (what it shows, in its docstring) |
| `tools/encode.sh` | Frames → the three media files (the HDCA repository's script, unchanged) |
| `data-page-wq.patch.json` | The six exact replacements that put the card, its panel, its routing and the hub's columns for five cards into the embed; made against the live text of 2026-11-18 (29,626 characters, SHA-1 `404c7920…`), which was fetched from hydroai.net/data and found equal to the HDCA repository's copy |
| `tools/apply_patch.py` | Applies the patch to a copy of the embed and checks both SHA-1s |

## The loop

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

## The card's words

The facts on a card repeat its portal's own numbers (1 km; 1,012 clear overpass dates, January 2016 to
December 2024; six parameters, each with its uncertainty; data open on Zenodo, paper under review). When the
portal's numbers or the paper's status change, change the card.

## The hub's columns

With four cards the hub is four across from 1700 px, two by two from 1181 px, one column of horizontal cards
down to 761 px, stacked below. A fifth card would stand alone under four, so the patch adds: three across from
1700 to 1999 px (three and two), five across from 2000 px (the lab head's display is 2048 px wide: all five in
one row, each 382 px wide instead of 423). The narrower layouts are unchanged (two across gives two, two and
one). This changes how the other four cards sit, so it is the lab head's choice; the alternative is to leave
the columns alone and let the fifth card start a second row.

## Publishing it (at the lab head's word)

1. Ask the other portal sessions (ListAgents / SendMessage) whether anyone is editing the embed.
2. In the Webflow Designer (Pages → Data → Navigator → Code Embed → Edit code embed) read the editor's text
   (`document.querySelector('.cm-content')` → its CodeMirror view → `view.state.doc.toString()`) and compare its
   SHA-1 with the patch's base. If they differ, somebody has edited the page since: make the patch again from
   the live text, never overwrite.
3. Apply the six replacements through `view.dispatch`, Save & Close, reopen and hash (the patch records the
   result's SHA-1), publish the site.
4. Run the HDCA repository's `embed/tools/check_captions.py` and `check_playback.py` on the live page, look at
   every card, and write the live text back to the HDCA repository's copy. Tell the other sessions.
5. Here: `status_note` and `public_url` in the dashboard registry, the status line in `CLAUDE.md`.
