# The project pages of hydroai.net

Asked for by the lab head on 2026-11-21, after the People page: each student's card there should lead to a
page about their main project, with figures from the research and a good design (“main project 이제 만들어서
연결할거야. … 학생이 하고 있는 연구 중 각종 그림들 포함해서 디자인 잘해서 만들어줘”). The Projects tab itself stays
as it is for now and is to be remade later; interns are left out until they have a main project.

`project.html` is the design: one block for a Webflow **Code Embed** on the Projects *template* page, so that
every project page (`/project/<slug>`), old or new, is shown the same way. Like the People block it is kept
in this repository because the tools for previewing and checking the lab's Webflow pages are here.

**Status: live on hydroai.net since 2026-11-21**, at the lab head's word. On the site: one Code Embed on the
Projects template page that holds `project.html` byte for byte (37,140 characters), twelve items of the
Projects collection (one main project for each student who is not an intern), and the line “[Main Project
Link]” in thirteen items of the People collection (the twelve students and a postdoctoral fellow who shares
one of the projects).

The content went up twice on that day. In the morning (the publish of 01:41:15 UTC) each page described its
project broadly, with illustrative figures from the students' own material (“메인 프로젝트를 브로드하게만 설명하는
식으로 하자”, “올려”). In the evening the lab head asked for no method detail at all, broader concepts, and
figures made from public data, at a moderate size and with very good design (“지금 학생들 연구 방법 등 너무
구체적인 방법론은 나오지 않게 해. 그대신 좀 더 브로드한 개념으로 설명하고 필요하면 위성 및 모델 재분석 등 자료써서 네가 그림
만들어”; “용량은 적당히 조절하고 디자인 퀄리티는 매우 좋아야해”). **That version is what the site shows since the
publish of 09:29:53 UTC**: each page says what the project is about, why it is hard, what the lab works on in
general words and why it matters, with a card of facts and one or two figures drawn for the page from
satellite products, reanalysis and public imagery; eight pages got a title and an address that name the
theme instead of the method. Seen after that publish: `check_project.py` passing on the twelve pages and on
two older ones in three browsers (621 checks), `check_people.py` passing on the People page (402), the People
page changed in the eight link addresses and nowhere else, the Projects tab with the twelve new cards, seven
other pages as they were. **Home was not as it had been, for the second time that day**: this publish, like
the morning's, carried out `sizes` values Webflow had saved for Home's own pictures (“Seen on the way”).

**A third version is on the site since the publish of 19:01:02 UTC that night.** The lab head asked for more
explanation of the basic concepts, with figures (“학생들 연구프로젝트 좀 더 구체적으로 기본 개념 등 그림 넣으면서 설명 더
넣어줘”) and, asked whether it should go onto the site, wrote “게시 해”. Each page now has a section “The basics”
between its first figure and “The challenge”: the concept the project rests on, in general words, with one
concept drawing. Seen after that publish: `check_project.py` passing on the twelve pages and on two older
ones in three browsers (675 checks), `check_people.py` passing on the People page (402), the words of the
twelve live pages equal to their source word for word, the pages looked at 2048, 1440 and 390 px, nine other
pages the same but for the stamp, and **Home's `sizes` as they were before the click** (“Seen on the way”).
The request had named the content and not its publication, so the click waited for his word: what was
already queued in the CMS would have gone out with any other session's publish in the meantime, and the
other sessions were told so.

The texts and figures are written outside this repository (see “The content” below).

| File | What it is |
|---|---|
| `project.html` | The block: styles, an empty frame, and the script that fills it from the page |
| `../tools/project_preview.py` | Serves project pages with this file on them, locally (port 8816) |
| `../tools/check_project.py` | Checks the block in Chromium, WebKit and Firefox, on the preview or on live pages |
| `../tools/site_snapshot.py` | Keeps a copy of every page of the site before a publish and says what differs after it |

## What a visitor gets

- **The top.** “Projects / Main project”, the title, the opening line, then whose main project it is
  (photograph, role, name, a link to their card on the People page) and the date; a green mark for the state
  of the work if the text gives one. Beside it, a card with the facts (theme, data, method, region …).
- **The first figure large**, on white, with its caption. A click enlarges any figure over the page; arrows
  and the arrow keys step through all figures of the page; “Open full size” opens the picture itself.
- **The text section by section**, the heading beside its text on a wide screen (it stays in view while the
  section is read), figures as wide as the column. A quote is set apart as the key sentence.
- **“More figures”** side by side, **links** as buttons, and **other projects** as cards: first those that
  are somebody's main project, with the name, beginning with the ones that follow this project in the list.
- One column below 900 px. Checked from 2048 px down to a 320 px phone.

## Where the content comes from

**The block has no content of its own.** It reads the page it is on:

- title, date, text and pictures: the project's item in the **Projects collection** (the template's title,
  date and rich text; the picture behind the old header is used only if the text has no picture);
- the other projects: the template's list at the foot of the page;
- **whose project it is: the People page.** The block fetches `/people` and looks for cards whose text
  links to this page as “Main Project Link”. So the one link that a person's card needs is also what puts
  their name on the project page, and nothing has to be entered twice. Two people may link to one project.

If the block cannot do its work (no scripts; a browser from before 2022; a page without the template's
parts), the page shows as it always did. If the People page cannot be read, the project page simply names
nobody.

### How a project's text is read

Whoever writes a project in Webflow's rich text can rely on these rules:

| In the text | Becomes |
|---|---|
| The first paragraph | The opening line under the title |
| A heading | A section. A heading of up to 44 characters stands beside its text, a longer one above it |
| A picture with its caption | A figure. The first one of the page is shown large under the title |
| The heading **At a glance**, then a list | The facts card: `Data: SMAP, ASCAT` (a bold label, or the words before the colon) |
| In that list, `Status: …` | The green mark beside the name |
| A quote | The key sentence, set apart |
| The heading **More figures** | Its pictures side by side |
| The heading **Links**, then links | Buttons at the foot of the text |
| A video | Shown at full width |
| Empty lines, floats, inline styles | Left out |

Nothing else is dropped or changed: `check_project.py` compares every word and every picture of the page
with what the block shows.

## The content

**What the site shows is the Projects collection in Webflow.** The folder the twelve pages are made in is
`~/.hydroai/web/projects/` on the lab head's machine, outside this repository and outside the synced Drive:

```
src/NN_name.py     one project each: title, summary, facts, paragraphs, figures with captions (what is on the site)
figures/           the figures: the reduced data, the scripts that drew them, the outputs (a README of its own)
site/              what the preview serves: projects.json, <slug>/body.html (as Webflow's rich text), pictures
tools/             build_site.py (src -> site), make_update_csv.py (site -> the file that updates the items)
NOTES.md           what each page is, the addresses before and after, what is still open
src_broad_v1/ src_detailed/ dossier/   the earlier versions and their sources: unpublished work, never public
```

A page explains a broad idea: the opening line, a facts card whose “Approach” names kinds of tools (land
models, artificial intelligence), not a method, then “The basics”, “The challenge”, “Our focus” and “Why it
matters”, 236 to 362 words. “The basics” (since the night of 2026-11-21) explains the concept the project
rests on in general words, as a textbook would, with one concept drawing: what data assimilation does, where
the sun's energy goes over a wet and a dry field, how a satellite covers the Earth strip by strip, the water
budget of the land, and so on. A figure is drawn for the page from public data (SMAP, GPM IMERG, GRACE, GK2A,
Sentinel-2, MODIS, ERA5-Land, GLEAM), in one look for all pages, 2000 px wide as WebP (45 to 450 kB), and its
caption ends with “Figure by the lab from public data: …”; a concept drawing's caption ends with “Drawing by
the lab.”, and a drawing made with invented numbers says so in the picture and in the caption. `python tools/build_site.py` (with a Python that has Pillow)
rebuilds `site/` after an edit of `src/`, and the preview then shows the edited page on the live template.
An edit there does not reach the site by itself: bring it into the items as described under “Changing things
later”, or the two drift apart.

## Looking at it and checking it

```bash
~/.venvs/hydroai/bin/python embed/tools/project_preview.py --site ~/.hydroai/web/projects/site     # http://127.0.0.1:8816/
~/miniconda3/bin/python embed/tools/check_project.py                                              # every page of the preview, three browsers
~/miniconda3/bin/python embed/tools/check_project.py https://hydroai.net/project/SLUG ...          # live pages
```

The preview builds the page of a project in the `--site` folder the way Webflow publishes its item (the
live template with the title, date, text and pictures in the places of the item's fields), so an edit is
seen before the item is changed; it shows any other project as it is on the site, with this folder's
`project.html` in the place of the embed; and it serves `/people` with the main-project links of
`projects.json`, so that the two pages can be walked both ways. A project of the folder that stands for a page
of the site (the same slug, or the slug it names as `replaces`) is shown once, in its new form, also in the
lists of other projects. `?old` shows a page without the block. The
pictures it serves are not public and it sends no header that would let another site's page read them.

## How it went onto the site (2026-11-21)

In the Webflow Designer, through the Chrome extension (`../people/README.md` and `../README.md` have the
general steps: a backup first, one session in the Designer at a time, publish with only hydroai.net ticked).

1. **The pictures** (34) were uploaded to the site's Assets panel, because the import needs a public address
   for each picture. On import Webflow copies every picture into the collection's own store, and the pages
   use those copies.
2. **The items** came in by CSV (CMS, Projects, Import), one row per project: `Title`, `Slug`, the three
   fields that put a project under the Projects page's tabs (`rs`, `lsm`, `ml`: `yes` or `no`), `Thumbnail
   Image` and `Main image` (addresses of pictures), `Short description`, and `Post content` as HTML. Of the
   HTML the rich text keeps paragraphs, headings, lists, bold, links, and a `figure` with its `img` (the
   `alt` too) and `figcaption`; it drops classes and other attributes. The switch `OnOFF` cannot be mapped
   from a file and is on in a new item. Imported items are “Queued to publish”. One row was imported first
   and its item read back before the other eleven.
3. **The embed:** on the Projects template page, the Navbar selected, Cmd+E, “Code Embed”; it lands right
   after the navigation bar. The text was set in the editor, saved, opened again and compared with the file.
4. **The links:** in each person's item of the People collection, in “Short description”, the line
   `[Main Project Link]` after “Research Interests”, the words between the brackets linked to
   `https://www.hydroai.net/project/<slug>` (three people had the line already and only its address
   changed). Each item was then queued (“Queue for next site publish”), never published by itself.
5. **One publish**, after telling the other sessions that work on the site, then the checks on the live
   pages and a look at them at 2048, 1440 and 390 px.

Seen on the way, and worth knowing:

- **A new item has no date until the site is published a second time.** The template's date is the item's
  publish date, which is still empty while the item's first publish is being written. The block then simply
  shows no date. The twelve pages had none for an hour and a quarter and carry “November 21, 2026” since
  the next publish.
- **A link that begins `https://www.hydroai.net/` is answered with a redirect to `https://hydroai.net/`.**
  It works, and it is how the links in the People collection were written before; the block compares paths
  only, so either form names the person.
- **The picture a page shows is the collection's copy.** To take one down, remove it from the item's text
  and publish; then delete the uploaded original in the Assets panel as well. **Neither takes the file off
  Webflow's servers:** a deleted asset and the collection's copy keep answering at their addresses (Webflow
  keeps them on its CDN by design and removes a file only on a request to its support, with a list of the
  links; its help article “Asset privacy”). The 34 pictures of the morning's version were deleted from the
  Assets panel on the lab head's word that evening (asset manager, “Select”, the tiles, “Delete selected
  assets”; the panel went from 303 to 269 files); their 68 addresses, originals and copies, still answered
  afterwards. The addresses are long random names that no page holds any more.
- **Publishing carries out whatever Webflow has saved for any page that was open in the Designer**,
  including new `sizes` values it measured for that page's own pictures, by whoever had the page open. On
  this day's publish that made two pictures on Home small (they have no width of their own and take it from
  `sizes`), and changed the pictures of the template's list here from 728 px to 727 px at one width, which
  shows nowhere. So: keep a copy of every page from right before a publish, and afterwards compare the
  pictures' `sizes` on all of them, not only the embeds' text and the pages' words:
  `site_snapshot.py fetch DIR` before the click, again when the new stamp is on the site, then
  `site_snapshot.py compare BEFORE AFTER`.
- **Where Webflow measures pictures for `sizes`, and a third publish that left Home alone** (the night of
  2026-11-21). The Designer page holds a second iframe, `#responsive-images-iframe`: 240 px wide by an inline
  style, placed above the window, `src="/site/empty.html"`. Webflow puts a copy of the page on the canvas
  into it (pictures as placeholders, each `img` marked `data-w-responsive`) and sets its width, in one task,
  to 992, 1214, 1315, 1439, 1440, 10000, 768, 991, 480, 767, 240 and 479 px, then back to 240: a measurement
  at the ends of each breakpoint's range, 240 px standing for phones. That is how a logo 230 px wide on a
  phone gets “96vw”, and Home's wrong values are what comes out when every step is measured at 240 px (144 is
  60 % and 108 is 45 % of 240). A passive log through the whole third publish for these pages (a
  MutationObserver on that iframe's `style` with the old values, a look every 20 ms at which document it
  holds, and the tab's `visibilityState`) showed only the template's copy in it, from opening the Designer to
  after “Published”, with the same widths at every pass, the canvas on the template at 1439 px and the tab
  visible at the click. **That publish (19:01:02 UTC) changed nothing on Home.** It differed from the two
  that did in two ways that are known: no People item was edited in its form in the CMS view (both earlier
  sessions did that, one item after another), and the tab was seen to be visible. Neither is shown to be the
  cause. The tab of the Designer is at times hidden to the browser for seconds while nobody acts through the
  extension (the extension works in the lab head's own Chrome, and a tab behind another one or a covered
  window counts as hidden).
- **The twelve cards' pictures got their smaller files with the next publish.** After the evening's import
  the twelve thumbnails went out as one file each, without `srcset`; the publish of that night carried them
  with `srcset` and `sizes` (“223px” and “100vw” on the Projects tab, “(max-width: 767px) 100vw, (max-width:
  991px) 727px, 940px” in the template's list), as every older card already had, at the same addresses.
  Probably Webflow had made the smaller versions in the hours between; that was not looked into. What it
  means for the comparison after a publish: all 33 project pages and the Projects tab were reported as
  changed, in exactly those pictures, and nothing looks different.
- **The same happened again in the evening, and the cause is not known.** The evening publish sent out wrong
  `sizes` for the same three pictures of Home (“31px”, “45vw, 108px”, “60vw, 144px”; 108 and 144 are 45 % and
  60 % of 240 px, the Designer's smallest canvas), although Home was never opened in the session that
  published. The pictures kept their size, because they had been given explicit widths in the morning, but
  the browser took the smallest file for them. The session that looks after Home keeps a copy of Home after
  every publish, and its record shows: sessions that had Home open published clean, the publish after such a
  session was clean twice, and the two changed publishes both followed work on these pages (long stretches in
  the CMS view, asset uploads, a CSV import, and a pass through the other collections in the CMS view a minute
  before the click). Which of these does it, if any, has not been found. Until it is: copy every page right
  before the click, compare right after, and tell the session that looks after Home at once.
- **Items are updated by a CSV, not only created.** A file with the columns `Item ID` and `Collection ID`
  (as in Webflow's own export) is offered as “Update matching items and import remaining as new”; the
  default choice in that dialog is “Import all as new items”, so choose and check. An update replaces the
  mapped fields (title, slug, texts, pictures; the three tab fields were written with their present values to
  be safe) and leaves a switch field alone; the item is then “Queued to publish” and still “Published” with
  its old content until the site is published. A new slug makes the old address answer 404: change the links
  in the People items in the same publish, and add a redirect in the site's settings if the old address
  matters (none was added for these eight: the old addresses named the methods and had been public for eight
  hours, and the lab head chose to leave them answering 404).
- **For a search engine or a link preview every project page is called “HydroAI”,** with no description and
  no picture: the template page's settings give that fixed title, as they did before. The block sets the
  browser tab's title to the project's when it runs. Binding the template's SEO title, description and Open
  Graph picture to the item's fields (page settings of the Projects template) would mend it; not asked for.
- **An alumnus whose card still has a main project link is named on that project's page** and on its card
  among “More projects”, with where they are now as the line above the name. Whether that is wanted is the
  lab head's to say; taking the link out of the person's item ends it.

## The postdoctoral fellows' pages (2026-11-22)

On 2026-11-22 the lab head asked for a main project for every postdoctoral fellow too (until then only one of the four had
the link, to a page shared with a student). Three pages were added in the same form, **live since the publish of
11:29:08 UTC that day**: `soil-moisture-under-the-forest-canopy`, `how-well-does-artificial-intelligence-forecast-rain` and
`forecasting-flash-droughts-weeks-ahead`. The site now has fifteen main-project pages, and sixteen People items carry the
line “[Main Project Link]”. Nothing in `project.html` changed. `check_project.py` passed on the three new pages, the shared
page and two older ones in three browsers (321 checks), `check_people.py` on the People page (402).

What this round added to “How it went onto the site”:

- **New items by CSV.** A file without the `Item ID` column goes straight to the mapping screen (no question about
  matching items). New items are “Not published · Queued to publish”.
- **Two publishes for a new item's date.** The first publish leaves the date empty (see “Seen on the way”); a second one
  right after it, with nothing else queued, fills it. Around that second publish only the new pages differed.
- **An item that reads “Changes in draft”.** Queueing sends the whole draft out. One People item had carried that mark for
  over a year: before queueing, every field of its form was compared with the live card (the rich texts by a hash of
  their text, the photograph by its size, the links, role and address), and nothing visible differed.
- **One Webflow session per account.** A sign-in on another computer ends the running one: the Designer then leads to the
  login page, and the CMS lists read “No items” although every item is there. Never import or create in that state; sign
  in again and keep Webflow closed elsewhere while a session works.
- **What a publish changed elsewhere:** nothing on Home and the six other top pages; on the Publications page the `sizes`
  of the six pictures of its own list went from “727px” to “728px” (it had gone the other way with the publish before).

## Pages on published papers (2026-11-22, night)

The lab head then asked that a postdoctoral fellow's paper, once it is published, be explained in more detail, and
named the fellows with published first-author papers. The rule of the main-project pages (a broad idea only) is for work
that is not published. A published paper may be explained fully: the question, the method in plain words, the paper's
own numbers and figures, what the result does not say, the citation, links to the paper, its data and its code.

- One fellow's main-project page was made detailed in place (`soil-moisture-under-the-forest-canopy`).
- Five pages are new, one per paper: `a-longer-record-of-soil-moisture-from-an-older-radar`,
  `a-slow-groundwater-response-as-a-sign-of-flash-drought`, `soil-moisture-from-reflected-navigation-signals`,
  `how-storms-carry-water-and-carbon-out-of-farmland` and `streamflow-where-the-gauges-are-few`.
  **Live since the publishes of 13:30:43 and 13:31:39 UTC that day.**
- These five are nobody's "Main project", so the block shows no photograph and name at the top: it reads those from the
  "Main Project Link" of a People card, and a card has one. The fact "Lead author" in the page's "At a glance" list names
  the fellow, and the fellow's main-project page leads to the paper pages by link buttons. Nothing in `project.html`
  changed, and no People item was touched.
- A page's own text may now link to another project page ("Links", then links to `/project/…`). `project_preview.py`
  looked for a project's card from the top of the page and failed on such a link; it now looks from the list of other
  projects on.
- `check_project.py` passed on the five new pages and the three pages that received link buttons, in three browsers, on
  the preview and on the live site (411 checks each), `check_people.py` on the People page (402).
- An item updated by CSV shows the date of that update: the page shared by a student and a fellow went from
  "November 21, 2026" to "November 22, 2026" when its buttons were added.

## Changing things later

- **A project's text or figures:** edit `src/NN_name.py` in the private folder, build, look at the preview
  and run the check on it; upload changed pictures to the site's Assets panel; `tools/make_update_csv.py`
  writes the file that updates the items (CMS, Projects, Import, “Update matching items …”); publish; run the
  check on the live page. A small change of words can also be typed into the item directly (queue it, never
  “Publish now”), but then make it in `src/` as well.
- **A new project page:** a new item (by hand, or one row of a CSV as above), the line in the person's
  People item, one publish. Nothing in `project.html` changes.
- **Whose project it is:** the People collection only. Two people may link to one page.
- **The design:** edit `project.html`, look at the preview, run `check_project.py` on it, then put the file
  into the embed (select the embed, Enter, replace the text, Save & Close, open it again and compare),
  publish, and run the check on the live pages. The embed holds 37,140 of the 50,000 characters it may.

**Going back:** delete the Code Embed and publish; the pages then show in the template's own layout. To take
a project off the site, archive its item and remove the line from the person's People item. The morning's
version of the twelve pages is kept in the private folder (`src_broad_v1/`, `site_v1/`), and Webflow made a
backup right before each import of the evening's.

## Things to keep

- **No content in the block**, and a person entered once: the People page says whose project it is.
- **Nothing a project's text says is dropped**, and no figure. The check holds this.
- **The page must show without the block.**
- **Unpublished work stays out of this repository**, and off the site: a figure in a public repository's
  history cannot be taken back.
- **A page explains a broad idea, not a student's method** (the lab head, 2026-11-21, evening): no model or
  technique names, no experiment design, no findings, no state of a manuscript. What the lab works on is said
  in general words.
- **Figures are made for the page from public data**, say so in their caption, and illustrate the idea;
  nothing from a manuscript or a student's notes. One look for all pages, a moderate file size, and design
  that is worth showing (the lab head: “디자인 퀄리티는 매우 좋아야해”).
- Every block is centred in the page's 1,348 px; check at 2048, 1440 and 390.
- The file is plain ASCII, so that it survives any editor.
