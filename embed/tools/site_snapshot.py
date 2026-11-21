#!/usr/bin/env python3
"""site_snapshot.py — a copy of every page of hydroai.net before a publish, and what differs after it.

    python embed/tools/site_snapshot.py fetch DIR             # the ten top-level pages and every project page
    python embed/tools/site_snapshot.py compare BEFORE AFTER  # page by page: tags and words, and every picture's `sizes`

Why: a publish in Webflow sends out everything saved in the Designer on every page, by whoever saved it, and
that includes values Webflow measured by itself. On 2026-11-21 a publish made for the project pages carried
out new `sizes` attributes for two of the Home page's own pictures, which another session had had open in
the Designer that morning; the pictures have no width of their own, and were laid out 31 px and 108 px wide
until the next publish. The embeds' text and the pages' words were all as expected, so nothing that was
being checked showed it. Hence: `fetch` right before the publish click (not from an earlier publish),
`fetch` again when the new stamp is on the site, `compare`, and read every line it prints.

`compare` leaves out what every publish changes (the stamp, the names of the CSS and JS bundles, their
integrity values). For each page that differs it prints the pictures whose `sizes` changed, then the other
places; a page that is new or gone is named. The exit status is 0 whatever it finds: what is expected is
for the reader to say.

Standard library only.
"""
import difflib
import glob
import os
import re
import sys
import urllib.request

LIVE = "https://hydroai.net/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
PAGES = {"home": "", "about": "about", "contact": "contact", "data": "data", "events": "events", "opportunities": "opportunities",
         "people": "people", "projects": "projects", "publication": "publication", "teaching": "teaching"}
STAMP = re.compile(r"<!-- Last Published: ([^>]*?) -->")


def get(path):
    return urllib.request.urlopen(urllib.request.Request(LIVE + path, headers={"User-Agent": UA}), timeout=40).read().decode("utf-8")


def fetch(out):
    os.makedirs(os.path.join(out, "project"), exist_ok=True)
    stamps = set()

    def keep(name, path):
        text = get(path)
        with open(os.path.join(out, name + ".html"), "w", encoding="utf-8") as f:
            f.write(text)
        m = STAMP.search(text)
        stamps.add(m.group(1)[:24] if m else "no stamp")
        return text

    for name, path in PAGES.items():
        text = keep(name, path)
        if name == "projects":
            slugs = sorted(set(re.findall(r'href="/project/([^"#?]+)"', text)))
    for s in slugs:
        keep("project/" + s, "project/" + s)
    print(f"{len(PAGES)} pages and {len(slugs)} project pages in {out}; stamp: {', '.join(sorted(stamps))}")
    if len(stamps) > 1:
        print("  more than one stamp: a publish was under way, fetch again")


def norm(text):
    text = STAMP.sub("<!-- Last Published -->", text)
    text = re.sub(r'/(css|js)/[\w.-]+\.(css|js)(\?[^"]*)?', r"/\1/BUNDLE.\2", text)
    return re.sub(r'integrity="[^"]*"', 'integrity=""', text)


def pictures(text):
    d = {}
    for m in re.finditer(r"<img\b[^>]*>", text):
        src = re.search(r'\bsrc="([^"]*)"', m.group(0))
        sizes = re.search(r'\bsizes="([^"]*)"', m.group(0))
        d.setdefault(src.group(1).split("/")[-1] if src else "", []).append(sizes.group(1) if sizes else None)
    return d


def files(d):
    return set(os.path.relpath(f, d) for f in glob.glob(os.path.join(d, "*.html")) + glob.glob(os.path.join(d, "project", "*.html")))


def compare(a, b):
    fa, fb = files(a), files(b)
    same = 0
    for f in sorted(fa & fb):
        ta, tb = open(os.path.join(a, f), encoding="utf-8").read(), open(os.path.join(b, f), encoding="utf-8").read()
        xa, xb = re.findall(r"<[^>]+>|[^<]+", norm(ta)), re.findall(r"<[^>]+>|[^<]+", norm(tb))
        if xa == xb:
            same += 1
            continue
        pa, pb = pictures(ta), pictures(tb)
        sized = [(k, pa[k], pb[k]) for k in pa if k in pb and pa[k] != pb[k]]
        ops = [o for o in difflib.SequenceMatcher(None, xa, xb, autojunk=False).get_opcodes() if o[0] != "equal"]
        print(f"CHANGED  {f}: {len(ops)} places, {len(sized)} pictures with another sizes value")
        for k, x, y in sized:
            print(f"    sizes  {k[-46:]}\n           {x}\n        -> {y}")
        for tag, i1, i2, j1, j2 in ops:
            x, y = "".join(xa[i1:i2]), "".join(xb[j1:j2])
            if re.sub(r'sizes="[^"]*"', "", x) == re.sub(r'sizes="[^"]*"', "", y):
                continue      # only a sizes value: listed above
            print(f"    {tag:8}{x[:160]!r}\n        -> {y[:160]!r}")
    for f in sorted(fa - fb):
        print("GONE    ", f)
    for f in sorted(fb - fa):
        print("NEW     ", f)
    print(f"{same} of {len(fa & fb)} pages the same but for the stamp and the bundles")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "fetch":
        fetch(a[1])
    elif len(a) == 3 and a[0] == "compare":
        compare(a[1], a[2])
    else:
        sys.exit(__doc__)
