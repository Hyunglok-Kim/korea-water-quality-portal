# The card on hydroai.net/data

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
one). The lab head was told of this change before giving the word.

## Changing the card later

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
