#!/usr/bin/env python3
"""apply_patch.py PATCH.json SRC OUT — put the water quality card into a copy of the lab's Data-page embed.

SRC must be the text the patch was made against (its SHA-1 is in the patch); every edit is an exact replacement
that must match exactly once. Prints the result's SHA-1, which the patch also records. The same edits are what
goes into the Webflow Designer's editor, one exact replacement at a time (see ../README.md)."""
import hashlib, json, sys
patch, src = json.load(open(sys.argv[1], encoding="utf-8")), open(sys.argv[2], encoding="utf-8").read()
sha = hashlib.sha1(src.encode()).hexdigest()
if sha != patch["base"]["sha1"]:
    sys.exit(f"the source is not the text this patch was made against: {sha} (expected {patch['base']['sha1']}). Somebody has edited the page since; make the patch again from the live text.")
for e in patch["edits"]:
    n = src.count(e["find"])
    if n != 1:
        sys.exit(f"edit “{e['what']}” matches {n} times, not once")
    src = src.replace(e["find"], e["replace"])
open(sys.argv[3], "w", encoding="utf-8").write(src)
print(len(src), "chars, sha1", hashlib.sha1(src.encode()).hexdigest(), "(expected", patch["result"]["sha1"] + ")")
