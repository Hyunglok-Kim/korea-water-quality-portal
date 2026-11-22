# The Publications page of hydroai.net

Asked for by the lab head on 2026-11-22, while the site was being remade: the Publications tab should be
remade too, because one has to scroll a long way and page through every earlier entry to see an older one
(“지금 스크롤을 쭉 내려야해서 좀 불편하고, 과거 게시물을 다 넘겨서 봐야해서 힘들어. 네가 퀄리티 좋게 만들어줘”).

`publications.html` is the answer: one block for a Webflow **Code Embed** on the Publications page. Like the
People and project blocks it is kept in this repository because the tools for previewing and checking the
lab's Webflow pages are here, not because it is about this dataset.

**Live on https://hydroai.net/publication since 2026-11-22** (published at 09:50:31 UTC, 18:50 in Korea,
hydroai.net only), at the lab head's word after seeing the preview (“게시 및 고치고 추천으로 진행”). The page
holds this file byte for byte, as the first element of its Body: the file of commit `7780c3d`, 46,382
characters, SHA-1 `af3e7e161c97f017e9ca49291215cc2a84e68b56`. On the live page `check_publications.py` passes
in Chromium, WebKit and Firefox (259 checks in each, 0 failures), `check_home_new.py https://hydroai.net/`
passes as it did before the publish (378 checks), and the page was looked at at 2048, 1440 and 390 px. With
the same publish the second tab's misspelt label was corrected in the Designer (“The page's content” below).

- **Backup in Webflow:** “Before the Publications page's new layout (2026-11-22)” is the site as it was
  before.
- **Going back:** delete the Code Embed and publish (“How it went onto the site” below).

| File | What it is |
|---|---|
| `publications.html` | The block: styles, an empty frame, and the script that fills it from the page |
| `../tools/publications_preview.py` | Serves the live Publications page with this file on it, locally (port 8817) |
| `../tools/check_publications.py` | Checks the block in Chromium, WebKit and Firefox, on the preview or on the live page |

## What was wrong with the page

The journal papers were shown six to a page, each as a card of about 200 px with a large picture and the
whole summary, and the other 45 behind a “Next” button, nine pages in all: to see a paper of 2021 one went
through six pages to the seventh, each a screen and a half long. Nothing could be searched. A paper whose
address was not filled in yet (“TBD”) had a button that led to a page that does not exist. The talks were
one list of 69 cards with the meeting's name repeated on every card.

## What a visitor gets

- **The top.** “Publications”, the page's quotation beside it with who said it, a chip for each of the
  page's lists (no numbers on them) and a search field.
- **Every journal paper on one page, year by year.** A row each: the picture small and whole, the title, the
  journal, month and year, and the link to the paper. A row takes about half the height of a card of the
  page as it was, and none is behind a “Next”.
- **The years beside the list** (in a row above it on a narrow window). They stay in view while the list is
  read, the year being read is marked, and a click leads to a year; the first year leads back to the top of
  the list, with the search field in view.
- **A paper's summary, folded away.** A click anywhere on the row (or on the arrow, which is the button)
  opens it: the picture larger, the summary as the page has it. A second click closes it. The title stays
  text that can be selected and copied. An opened paper has its own address (`/publication#beyond-smap-…`),
  so a paper can be linked to; whoever arrives by such a link finds it open and in view.
- **A figure, full size.** A click on the picture shows it as large as the window allows and never larger
  than the picture is, with the paper's title; arrows and the arrow keys step through the figures of the
  list; the cross, Escape and a click beside it close it.
- **The search** looks through all three lists at once (titles, journals, authors, states, dates, and the
  summaries' words; several words must all be there). The words are marked where they stand, the chips say
  how many entries each list has, and a list with nothing says so and offers the lists that have something.
  `/` puts the cursor in the field from anywhere on the page; Escape and the cross empty it.
- **Under review:** title, authors, journal, and the state as a mark (in revision, under review, to be
  submitted), in the page's order.
- **Conferences:** by year, and in a year the talks of one meeting together under the meeting's name and
  month, each talk with its authors.
- Checked from 2048 px down to a 320 px phone. On a phone a row is the title, then journal and month beside
  the link; the picture comes with the summary.

## Where the content comes from

**The block has no content of its own.** It reads the page it is on:

- the three lists, their names and their order: the CMS lists in the page's tabs and the tabs' labels;
- the quotation: the line above the tabs (its first line, and after a line break who said it).

Those stay on the page and are edited in Webflow exactly as before: a paper in the Publications collection,
a talk in the Conferences collection, a tab's label or the quotation in the Designer. While the block runs,
the page's own section is not shown. In the Designer the page looks as it always did, because the Designer
does not run scripts. **Adding a paper to the collection is all it takes for the page to show it**, and the
home page's “Recent publications”, which reads this page, is not touched by any of this.

**The following pages.** The page lists its journal papers a few at a time (six, with “Next”). The block
shows the first page's papers at once and asks for the following pages itself, four at a time, until one has
no “Next” (for 51 papers: eight requests of about 13 kB, well under a second; the list says “Loading the
earlier entries…” until they are here). If a page cannot be fetched the list says so and offers to try
again; what has arrived stays. Opened on a later page of the list (`?…_page=3`, as an old link or a search
engine may have it), the block reads the list from its first page. If the list is one day set to 100 a page
in the Designer, everything is in the page itself and nothing is asked for; the block works the same.

If the block cannot do its work (no scripts; a browser from before 2022, which has no `<dialog>`; the page
rebuilt so that nothing can be read from it), the page shows as it always did, and in the last case the
browser's console says so (“hydroai publications block: the page is shown as it was”).

### How an entry is read

| On the page | Becomes |
|---|---|
| A journal paper's date, “December 1, 2026” | “Dec 2026” under the year 2026; the whole date shows on pointing at it. (Most days are the 1st: only the month is known.) |
| A link that is an address | “Paper ↗”, opening a new tab (“Google Scholar ↗” for an address there) |
| A link that is `TBD` or `#` | “Link soon”, and no link |
| A journal that is only `-` | Left out |
| A summary | Its paragraphs, line breaks, bold, italic and links; empty lines left out |
| A paper with neither summary nor picture | A row that opens nothing (no arrow) |
| A list whose entries carry dates | Shown by year; entries other than journal papers also by meeting (same name and date) |
| A list whose entries carry no dates | Shown as it stands, each entry's last line (“under review”) as a mark: green for a revision, outlined for under review or consideration, grey otherwise. The first letter is drawn as a capital; the words are the page's |
| A line that explains a mark (“* = …”) | Shown under its list while an entry of the list carries the mark, left out otherwise |
| A tab without entries | No chip |
| A new tab | A chip and a list, read by the same rules |

Nothing else is dropped or changed: `check_publications.py` compares every entry and every word of every
summary with what the page shows.

## Looking at it and checking it

```bash
~/.venvs/hydroai/bin/python embed/tools/publications_preview.py        # http://127.0.0.1:8817/publication   (?old: the page as it is on the site)
~/miniconda3/bin/python embed/tools/check_publications.py              # the preview, in Chromium, WebKit and Firefox
~/miniconda3/bin/python embed/tools/check_publications.py https://hydroai.net/publication     # the live page, once the block is on it
```

`publications_preview.py` fetches the live page and puts this file on it the way the Designer would, as the
first element of the page; the requests for the list's following pages are passed on to the site. Once the
block is on the site it puts the file in the place of the page's own embed, so a change is seen on the page
as it is (and says at the start whether the site's block is the same as the file). `?one` shows the page as
it would be with every paper on its first page.

`check_publications.py` lists what it checks in its docstring: the page; every entry of the three lists and
every word of every summary against the page's own content (it reads the list's pages itself, by the page's
own “Next”); the chips; the years; a paper, its figure and every way in and out; the address; the search;
the following pages (on their way, one that fails, the page opened on a later one); falling back; the block
in another place; the page with changed content (a paper without picture, a picture that cannot be fetched,
a link filled in, a new tab, an emptied one, no quotation …); thirteen window sizes. It exits with the
number of failures. **Run it on the live page too.**

## How it went onto the site (2026-11-22), and how a changed file goes there

In the Webflow Designer, on the Publications page (`data-wf-page` 640cbd423ecaf899c03aa522), at the lab
head's word, after telling the other sessions that work on hydroai.net (a publish sends out everything
saved in the Designer, on every page) and saving a backup (Cmd+Shift+S):

1. Pushed, so that the Designer page could fetch `publications.html` (from raw.githubusercontent.com at the
   commit; the portal's GitHub Pages site serves it too).
2. **Body** selected in the Navigator, a **Code Embed** added (Cmd+E, “Code Embed”, Enter). It lands last
   in Body, after the navigation bar, and its editor opens. The file's text was put into the editor (one
   `view.dispatch`), then Save & Close. (On the Designer's canvas the embed is a grey line that says a
   script only shows on the published site, and the page looks as it always did.)
3. The embed was **moved to be the first element of Body**, before the page's Section. On this page the
   navigation bar comes last in Body, so an embed left after it, as on the People page, would show the
   block under the “Contact me” block. In the Navigator that is a drag of the embed's row to just under
   “Body”. **Through the Chrome extension the tool's drag does nothing there** (the row under the pointer
   is selected, nothing moves): the Navigator follows the mouse on its way. What worked, dispatched from
   the page on the element under each point (`new MouseEvent(type, {bubbles: true, clientX, clientY,
   buttons: 1})`): `mousedown` on the row, a `mousemove` every 5 px up to the top edge of the “Section”
   row (the Navigator then draws the row in its new place), `mouseup` there. Then the canvas was read:
   `[...contentDocument.body.children]` begins with `div.w-embed.w-script`.
4. The Designer was loaded again, the embed opened (select it, Enter) and its text compared with the file:
   equal.
5. The second tab's label was corrected on the canvas: a double-click on the word, one letter replaced,
   Escape. The canvas stayed on the first tab (`data-current="Peer-reviewed"`), which is the tab the page
   opens with.
6. All seven lists of the CMS were looked through to their ends: no item was queued for publishing. (One
   People item has read “Changes in draft” since 2025; a site publish leaves such a draft alone.)
7. `site_snapshot.py fetch` right before the click, Publish with only hydroai.net ticked, `fetch` again and
   `compare`: of the 43 pages only this one differs, by the embed, the label, and the `sizes` of the six
   pictures in the page's own journal list (“… (max-width: 991px) 728px, 940px” became “… 727px, 940px”;
   the block does not use it and nothing looks different). The home page and its pictures' `sizes` are as
   they were. Through the publish only this page's copy passed through the Designer's measuring frame, and
   the tab was visible at the click (`../project/README.md`, “Seen on the way”, says why that is noted).
8. The live page holds the file byte for byte; `check_publications.py https://hydroai.net/publication` and
   `check_home_new.py https://hydroai.net/` (the home page reads this page) passed; the page was looked at
   at 2048, 1440 and 390 px.

**A changed file goes there the same way** without steps 2 and 3: push; in the Designer select the Code
Embed (the first row under Body in the Navigator) and press Enter; replace the whole text, Save & Close,
open it again and compare; a `site_snapshot.py` copy; publish with only hydroai.net ticked; fetch the live
page, compare, and run the two checks. `../README.md`, “Changing a block on the site”, has more on each
step.

The block works wherever it is put on the page (the check tries it last as well), but only before the
page's section is nothing of the old layout ever drawn first, and only there does it stand above the
“Contact me” block. The embed may hold 50,000 characters; the file has about 46,000. If it must grow, the
comment at its head can go.

**Going back to the page's own layout:** delete the Code Embed and publish. The block changes nothing else
on the page. The tab's label stays corrected; the backup has the page with the old one.

## Changing it later

- **Words on buttons and in messages:** `T` in the script. **The title and the small title:** the markup.
- **How many pages are asked for at a time:** `BATCH`.
- **The page's tabs are rebuilt:** run the check. The block finds the entries by `.w-tabs`, `.w-tab-link`,
  `.w-tab-pane`, `.w-dyn-item`; in a journal paper's item `.publications-card`, `h3`, `h4`,
  `.publication_date`, `.w-richtext`, `img`, `a.w-button`; in any other item `h3`, the element after it (the
  authors), `.text-block-4` (journal or meeting) and `.text-block-5` (state or date); the line that explains
  a mark by `.text-block-7`; the list's following pages by `a.w-pagination-next`.
- After a change: preview, check, push, replace the embed's text in the Designer, publish, check the live
  page.

## Things to keep

- **No content in the block.** Titles, summaries, pictures, states and the quotation come from the page.
- **Nothing the page says of an entry is dropped**, and a summary is never cut. The check holds this.
- **The page must show without the block:** the page's own section stays on the page, and whatever stops the
  block leaves it visible.
- **A row is as tall before its picture arrives as after.** Every closed row keeps a place of one size for
  its picture, and the picture stands in it whole, in its own proportions. Before this was so, rows changed
  height as pictures arrived, and a paper opened by its address slid out of view.
- **No address the block uses is the id of an element.** A year's address is `#peer-reviewed-2023`, the
  year's element is `hb-peer-reviewed-2023`. The site's own script scrolls to any id a clicked link names,
  to the very top of the window, under the navigation bar, and did so after the block's own scroll.
- **No numbers on the chips** unless something is being searched (the lab head had the head counts taken
  off the People page).
- **Every block is centred** in the page's 1,348 px, as on the rest of the site; check at 2048, 1440 and 390.
- The script is plain ASCII (characters outside it are written as `\uXXXX`), so that it survives any editor.

## The page's content: what was corrected, and what was only noticed

**Corrected in the Designer on 2026-11-22 at the lab head's word** (“고치고”), with the publish that put the
block on the site: the second tab's label, “Under review / Preperation”, is now “Under review /
Preparation”. The tab's name (`Under-Review`), and with it the list's address `#under-review`, is as it
was.

**Kept as proposed, at the lab head's word** (“추천으로 진행”): a paper whose address is not filled in shows
“Link soon” and no link.

**Only noticed, not changed.** The block shows the page's words as they are. Seen while it was made, each a
matter for the lab head (the item-by-item list was given to the lab head and is not kept here):

- ten journal papers have no address yet (“TBD”): in the page's own layout their button leads to a page
  that does not exist, the block shows “Link soon”;
- a few titles carry a slip (a stray character, a journal's name at the end of a title, a comma at the end),
  one summary breaks off in the middle of a sentence, and a few talks' titles and author lists have
  misspellings;
- some entries of the “under review” list have since appeared in the journal list;
- the line “* = mentored by Dr. Kim” explains a mark that no entry carries at present, so the block leaves
  it out until one does;
- journals and meetings are sometimes written in full and sometimes abbreviated, so the same meeting can
  appear under two names;
- the journal list could be set to 100 a page in the Designer (Collection List settings): the page would
  then hold every paper itself, for a visitor without scripts and for search engines too.
