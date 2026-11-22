# The Publications page of hydroai.net

Asked for by the lab head on 2026-11-22, while the site was being remade: the Publications tab should be
remade too, because one has to scroll a long way and page through every earlier entry to see an older one
(“지금 스크롤을 쭉 내려야해서 좀 불편하고, 과거 게시물을 다 넘겨서 봐야해서 힘들어. 네가 퀄리티 좋게 만들어줘”).

`publications.html` is the answer: one block for a Webflow **Code Embed** on the Publications page. Like the
People and project blocks it is kept in this repository because the tools for previewing and checking the
lab's Webflow pages are here, not because it is about this dataset.

**Status (2026-11-22): made and checked on a local copy of the live page; not on hydroai.net.** Putting it
there means publishing the Webflow site, which waits for the lab head's word (`../README.md`). On the preview
`check_publications.py` passes in Chromium, WebKit and Firefox (261 checks in each, 0 failures), and the page
was looked at at 2048, 1440 and 390 px.

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

## How it goes onto the site

In the Webflow Designer, on the Publications page (`data-wf-page` 640cbd423ecaf899c03aa522), at the lab
head's word, after telling any other session that works on hydroai.net (a publish sends out everything
saved in the Designer, on every page) and saving a backup (Cmd+Shift+S):

1. Push, so that `publications.html` is on the portal's GitHub Pages site (the Designer page fetches it from
   there).
2. The first time: **Body** selected in the Navigator, a **Code Embed** added (Cmd+E, “Code Embed”, Enter)
   and moved to be the **first** element of the page, before the page's Section (on this page the navigation
   bar comes last in Body). For a change: select that Code Embed and press Enter. Put the file's text in the
   editor, Save & Close, open it again and compare. (On the Designer's canvas the embed is an empty box and
   the page looks as it always did.)
3. Publish with only hydroai.net ticked.
4. Fetch the live page and see that the file is in it byte for byte; run
   `check_publications.py https://hydroai.net/publication` and `check_home_new.py https://hydroai.net/` (the
   home page reads this page); look at it at 2048, 1440 and 390 px.

The block works wherever it is put on the page (the check tries it last as well), but only before the
page's section is nothing of the old layout ever drawn first. The embed may hold 50,000 characters; the file
has about 46,000. If it must grow, the comment at its head can go.

**Going back to the page's own layout:** delete the Code Embed and publish. The block changes nothing else
on the page.

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

## Only noticed, not changed

The block shows the page's words as they are. Seen while it was made, each a matter for the lab head (the
item-by-item list was given to the lab head and is not kept here):

- the second tab's label is misspelt (“Preperation”);
- ten journal papers have no address yet (“TBD”): on the page as it is their button leads to a page that
  does not exist, the block shows “Link soon”;
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
