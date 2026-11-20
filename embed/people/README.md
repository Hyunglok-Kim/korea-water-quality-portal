# The People page of hydroai.net

Asked for by the lab head on 2026-11-20, while the home page was being remade: take the “Contact me” block
off the People page, and make the page cleaner and more modern (“contact me 우선 삭제하고, 좀 더 people탭
깔끔하고 모던하게 업데이트 해보자”).

`people.html` is the answer to the second half: one block for a Webflow **Code Embed** on the People page.
It is kept in this repository because the tools for previewing and checking the lab's Webflow pages are
here, not because it is about this dataset.

After seeing the preview the lab head asked for four more things (the same night: “오타 등 고쳐. 그리고 Alumni
하나 만들어서, Seongjun Lee 국립산림과학원 이렇게 간략하게만 표시하자. 그리고 visiting scholar지우고, 각 탭에 몇
명인지도 지워.”): the misspellings in people's texts corrected; an **Alumni** group that shows a name and where
the person is now, nothing more; the visiting scholar taken off; no head counts on the groups.

**Status: live on https://hydroai.net/people since 2026-11-21, 08:11 KST** (published 2026-11-20, 23:11:32
UTC), at the lab head's word: asked that morning, with what a publish would send out listed, he chose to
publish, the new layout included.

- **The block:** one Code Embed on the People page, right after the navigation bar, holds `people.html` of
  commit 15a6c87 byte for byte. `check_people.py https://hydroai.net/people` passes on the live page in
  Chromium, WebKit and Firefox (134 checks in each, 0 failures), and the page was looked at at 2048, 1440 and
  390 px.
- **The content changes** saved in Webflow the night before went out with the same publish: the “Contact me”
  block gone from the People page (the other pages keep theirs); the fourth tab “Alumni”, its list taking
  `member_type` = `alumni`; the corrections in ten People items and one former student's move to Alumni
  (the end of this file). So did the home page's second round (`../README.md`). The other eight pages of the
  site are as they were, but for the publish stamp and the names of the style and script bundles.
- **Backups in Webflow:** “Before the People page changes (2026-11-20)” is the site before any of this;
  “Before the People page's new layout (2026-11-21)” is the site with the content changes saved and without
  the block.

| File | What it is |
|---|---|
| `people.html` | The block: styles, an empty frame, and the script that fills it from the page |
| `../tools/people_preview.py` | Serves the live People page with this file on it, locally (port 8815) |
| `../tools/check_people.py` | Checks the block in Chromium, WebKit and Firefox, on the preview or on the live page |

## What was wrong with the page

Every person was a box of a fixed shape with the text scrolling inside it, so most of what people had written
could not be seen without finding the scroll bar of each box; the photographs had different widths; every
student carried three icons (Scholar, GitHub, YouTube) that led to a page that does not exist (the links
are “TBD”); the group photographs were small; only one group could be seen at a time.

## What a visitor gets

- **The top.** “People”, the lab's motto beside it, the group photographs in a row (a click enlarges one;
  arrows and the arrow keys step through them), and a chip for every group (no head counts: the lab head
  asked for them to go).
- **Everyone on one page**, group after group in the order of the page's tabs. A chip shows one group alone;
  “All” shows everyone again. The address follows (`/people#students`), so a group can be linked to.
- **The first group (the PI)** as one wide card: photograph, role, name, links, the text, then *Education*
  and *Experiences* side by side with their dates set apart, and *Professional Services* folded away under
  its heading (a section with more than twelve lines is folded; a list of eight or more short names, as the
  reviewer board is, becomes a row of names).
- **Everyone else** as a card: photograph (all the same shape), role, name, research interests, and the
  links that are really links. Nothing is cut and nothing scrolls inside a card.
- **Alumni** briefly: a small card with the name (without Mr. or Ms.) and one line, where the person is now.
  No photograph, no text, nothing to open. This is how any group whose tab is named “Alumni” is shown.
- **A profile** for whoever has more to show than the card does (publications, awards, education …):
  the name, the photograph and “View profile” open it over the page; the cross, Escape, a click beside it
  and the browser's Back close it. A profile has its own address (`/people#subin-kim`), so a person can be
  linked to. On a phone it fills the screen.
- Two columns of cards from 700 px, one below. Checked from 2048 px down to a 320 px phone.

## Where the content comes from

**The block has no content of its own.** It reads the page it is on:

- the people, their groups and their order: the CMS lists in the page's tabs (PI, Students, Postdocs,
  Alumni, Mascot);
- the group photographs and the motto: the pictures and the line above the tabs.

Those stay on the page and are edited in Webflow exactly as before: a person in the People collection, a
photograph or the motto in the Designer. The block is the only thing that was added; while it runs, the page's
own section is not shown. In the Designer the page looks as it always did, because the Designer does not run
scripts. **Adding a person to the People collection is all it takes for the page to show them.**

**Which tab a person is in** is the item's `member_type` field in the People collection: each tab's list
shows the items whose `member_type` equals its own word (`PI`, `std` for students, `alumni`, …) in the order
of the item's `order` number. An item with any other word is on no tab (the former visiting scholar's item
still says `visiting_scholar`; one student's says `stdd`), and stays in the CMS.

**When someone leaves the lab:** in their item set `member_type` to `alumni` and write where they are now in
**Occupation** (for example “National Institute of Forest Science (국립산림과학원)”); queue or publish the item.
The rest of the item (photograph, texts) can stay: the block does not show it for alumni. Where the block
does not run (a browser without `<dialog>`; the block taken off the page), the page's own Alumni tab shows
the item's whole card, in the design the visiting scholars' tab had: with the headings “Education” and
“Experiences” even when the item has nothing under them. The whole card is also in the page's source.

If the block cannot do its work (no scripts; a browser from before 2022, which has no `<dialog>`; the page
rebuilt so that nobody can be read from it), the page shows as it always did, and in the last case the
browser's console says so (“hydroai people block: the page is shown as it was”).

### How a person's text is read

The cards are written freely in Webflow's rich text, each a little differently. The block reads them by a few
rules; whoever writes a card can rely on these:

| In the text | Becomes |
|---|---|
| A short line all in bold (or a heading), e.g. **Publications** | A heading; the lines under it belong to it |
| The heading **Research Interests** | The list on the card (up to five; the profile has them all) |
| A line beginning `(2024)`, `(2023.08 - 2026.08)`, `(Present)` or `2022/03 – 2022/08 \|` | A dated line: the date set apart in its own column |
| A line beginning `[1]`, `1.` or a bullet, or an item of a list | A line with its mark set apart |
| A link whose line says “Main Project Link” | The card's “Main project” link |
| A line that is only `-` | Left out, with a heading that has nothing else under it |
| A link in the three icons that is `TBD`, `#` or `https://tbd` | Left out; a real address appears, named after its site |
| A bold line with nothing under it | A bold line (not a heading) |
| Text before the first heading | The introduction: on the PI's card, and at the top of a profile |
| (not in the text) A tab named **Alumni** | Its people are shown briefly: the name without “Mr.” or “Ms.”, and the role line |

Nothing else is dropped or changed: `check_people.py` compares every word of every card with what the page
shows (and for alumni, that the name and the role line are all there is).

## Looking at it and checking it

```bash
~/.venvs/hydroai/bin/python embed/tools/people_preview.py        # http://127.0.0.1:8815/people   (?old: the page as it is on the site)
~/miniconda3/bin/python embed/tools/check_people.py              # the preview, in Chromium, WebKit and Firefox
~/miniconda3/bin/python embed/tools/check_people.py https://hydroai.net/people     # the live page, once the block is on it
```

`people_preview.py` fetches the live page and puts this file on it the way the Designer would; once the block
is on the site it puts the file in the place of the page's own embed, so a change is seen on the page as it
is (and says at the start whether the site's block is the same as the file). `check_people.py` lists what it
checks in its docstring: the page; everyone and every word of their texts against the page's own content;
the groups; a profile and every way in and out of it; the photographs; falling back; the block in other
places; the page with changed content (a person without photograph, a filled-in link, a second PI, an emptied
group …); thirteen window sizes. It exits with the number of failures. **Run it on the live page too.**

## How it went onto the site (2026-11-21), and how a changed file goes there

In the Webflow Designer, on the People page (`data-wf-page` 640cbd423ecaf8bd443aa54e), after telling any
other session that works on hydroai.net (a publish sends out everything saved in the Designer, on every
page) and saving a backup (Cmd+Shift+S):

1. Push, so that `people.html` is on the portal's GitHub Pages site (the Designer page fetches it from there).
2. The first time: **Navbar** selected in the Navigator, a **Code Embed** added (Cmd+E, “Code Embed”, Enter).
   The navigation bar is a component, so the embed lands right after it, before the page's section (Body >
   Navbar, Code Embed, Section). For a change: select that Code Embed and press Enter. Put the file's text
   in the editor, Save & Close, open it again and compare. (On the Designer's canvas the embed is an empty
   box and the page looks as it always did: the Designer does not run scripts.)
3. Publish with only hydroai.net ticked.
4. Fetch the live page and see that the file is in it byte for byte; run
   `check_people.py https://hydroai.net/people`; look at it.

The block works wherever it is put on the page (the check tries it first and last as well), but only before
the page's section is nothing of the old layout ever drawn first. The embed may hold 50,000 characters;
the file has about 48,000. If it must grow, the comment at its head can go.

**Going back to the page's own layout:** delete the Code Embed and publish. The block changes nothing else on
the page, so the page's own section then shows again, with the content as it is now (no “Contact me” block,
the Alumni tab with the item's whole card).

## Changing it later

- **Words on buttons, the title, the small title:** `T` in the script; the markup above the script.
- **How many interests a card lists, when a section folds, when a text is cut:** `MAXI`, `FOLD`, `LONG`.
- **A group that should be drawn wide like the first:** the first tab is the wide one; change the order of the
  tabs in Webflow.
- **The page's tabs are rebuilt:** run the check. The block finds the people by `.w-tabs`, `.w-tab-link`,
  `.w-tab-pane`, `.people-card`, and in a card `.name h2`, `.subtext`, `.people-image-wrap img`,
  `a.social-link`, `.w-richtext` (with its heading in `.wrap-people-services`).
- After a change: preview, check, push, replace the embed's text in the Designer, publish, check the live
  page (see `../README.md`, “Changing a block on the site”).

## Things to keep

- **No content in the block.** Names, texts, photographs and the motto come from the page. A person must
  never have to be entered twice.
- **Nothing a person wrote is dropped, and nothing is cut without a way to the whole.** The check holds this.
- **The page must show without the block:** the page's own section stays on the page, and whatever stops the
  block leaves it visible.
- **Every block is centred** in the page's 1,348 px, as on the rest of the site; check at 2048, 1440 and 390.
- The script is plain ASCII (characters outside it are written as `\uXXXX`), so that it survives any editor.

## The page's content: what was corrected, and what was only noticed

**Corrected in the CMS on 2026-11-20/21 at the lab head's word** (“오타 등 고쳐”): misspellings and missing
spaces in the texts and role lines of ten People items (two journals' names, a paper's title, a link's label,
a space before a year in brackets, a doubled comma and the like). Each item was queued and went out with the
site's publish of 2026-11-21; none of the old spellings is on the live page. The item-by-item list was given
to the lab head; it is not kept in this repository, which is public.

In the Designer, on the People page: the fourth tab “Visiting Scholars” was renamed “Alumni” (its label and
its name) and its list now takes `member_type` = `alumni`; the “Contact me” block was deleted from the page.
The former visiting scholar's item was not changed or archived: it is simply on no tab any more.

**Only noticed, not changed** (the lab head was told of each):

- **Links that are no links.** Every student's three icons lead to `TBD` (45 links), and some postdocs'
  missing ones to `#`, `tbd` or `https://tbd`: in the page's own layout a click on them ends on a page that
  does not exist. The block leaves them out; as soon as a real address is filled in, its icon appears.
- **A link field that holds another kind of address** (a personal site in the GitHub field) is shown with a
  globe and named after the site.
- **Roles** are shown as they are written (one has no year), in capitals, as the page did.
- **Photographs:** three are smaller than a sharp screen needs, and three are large files (up to 2.6 MB;
  smaller sizes are served where Webflow made them).
- **A heading with only “-” under it** is left out by the block until there is something to list.
- **Every person has a page of their own that nobody links to** (`/people/<slug>`): the site template's
  “Teacher” page, with the template's filler text and footer. Hiding or deleting the template page is a
  decision for the lab head.
- **Elsewhere on the site:** “technics” in the pages' descriptions (it shows in search results and link
  previews) and the Teaching page's tab title “Teching”.
- All 13 addresses the cards link to answered on 2026-11-20 (two publishers refuse robots, which is not a
  fault of the link).
