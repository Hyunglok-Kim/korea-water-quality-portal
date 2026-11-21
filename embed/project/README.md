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

A page explains a broad idea: the opening line, “The challenge”, “Our focus”, “Why it matters”, 115 to 170
words, and a facts card whose “Approach” names kinds of tools (land models, artificial intelligence), not a
method. A figure is drawn for the page from public data (SMAP, GPM IMERG, GRACE, GK2A, Sentinel-2, MODIS,
ERA5-Land, GLEAM), in one look for all pages, 2000 px wide as WebP (50 to 450 kB), and its caption ends with
“Figure by the lab from public data: …”. `python tools/build_site.py` (with a Python that has Pillow)
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
