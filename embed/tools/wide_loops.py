#!/usr/bin/env python3
"""wide_loops.py TOOL [the tool's own arguments] — the other datasets' card loops, drawn larger for the home page.

The loops on the hydroai.net/data cards are 768 px wide. The home page's first screen shows them up to about
700 CSS px wide, which on a dense screen is 1,400 to 1,750 screen pixels, so it has a second, larger set
(`embed/media/*-wide-v1.*`). This runs the tools that made the card loops, as they are in their own
repositories, with one thing changed: the pixel density of the frames (SCALE, default 1.6: 1536 x 864 for a
960 x 540 view), and with it the size of the chart panel that two of them draw over the map. Camera, stages
and frame counts are the tools' own, so a wide loop has its card loop's timeline and the card's captions fit it.

    TOOL            what it runs                                                   needs running
    tca_cap         tv_TCA/portal/embed/tools/cap_tca_westus.py                    the TCA preview (port 8793)
    tca_compose     tv_TCA/portal/embed/tools/compose_tca_westus.py
    hdca_cap        hdca/portal/embed/tools/cap_hdca_amazon.py                     the HDCA preview (port 8792)
    hdca_compose    hdca/portal/embed/tools/compose_hdca_amazon.py
    et_cap          hdca/portal/embed/tools/cap_et.py                              the ET preview on the PUBLIC copy of the tiles (port 8791)
    et_cap_v3       hdca/portal/embed/tools/cap_et_v3.py  (the loop with France)   the ET preview with both regions' public tiles
    cvs             hdca/portal/embed/tools/make_cvs.py  (1280 x 720: the drone mosaic is 1 m, no finer)

    W=frames                                                   # any scratch folder
    # water quality (this repository's own tool takes the density itself)
    python embed/tools/cap_wq.py "http://127.0.0.1:8797/index.html?intro=0&data=/data/" $W/wq size=960x540 scale=1.6
    embed/tools/encode.sh $W/wq/final wq-wide-v1 embed/media 30 44 1536 24
    # TCA
    python embed/tools/wide_loops.py tca_cap "http://127.0.0.1:8793/?intro=0&hidefooter=1&data=/data/" $W/tca/raw
    python embed/tools/wide_loops.py tca_compose $W/tca/raw ~/orca/projects/tv_TCA/portal/embed/tools/westus_sigma.json $W/tca/final
    embed/tools/encode.sh $W/tca/final tca-wide-v1 embed/media 30 44 1536 24
    # HDCA
    python embed/tools/wide_loops.py hdca_cap "http://127.0.0.1:8792/?intro=0&data=/data/" $W/hdca/raw
    python embed/tools/wide_loops.py hdca_compose $W/hdca/raw ~/orca/projects/hdca/portal/embed/tools/amazon_sm.json $W/hdca/final
    embed/tools/encode.sh $W/hdca/final hdca-wide-v1 embed/media 30 44 1536 24
    # ET: the preview must serve the public copy (dev_server.py --data <public-tiles> --port 8791), as for the card
    python embed/tools/wide_loops.py et_cap "http://127.0.0.1:8791/?data=/data/prithvi-openet-tiles-1/&intro=0" $W/et
    embed/tools/encode.sh $W/et et-wide-v1 embed/media 31 44 1536 24
    # ET with France (et-v3, 2026-11-21): the preview must serve the public tiles of both regions; the tool checks that it does
    python embed/tools/wide_loops.py et_cap_v3 "http://127.0.0.1:8853/?data=/data/prithvi-openet-tiles-1/&intro=0" $W/et3
    embed/tools/encode.sh $W/et3 et-wide-v2 embed/media 31 44 1536 24
    # the validation site
    CVS_FPS=15 CVS_HOLD=10 CVS_FADE=8 python embed/tools/wide_loops.py cvs ~/orca/projects/hampyeong-cal-val $W/cvs
    embed/tools/encode.sh $W/cvs cvs-wide-v1 embed/media 29 42 1280 15

Add `test` after a capture's arguments for a handful of frames. The rules those loops keep are their own
repositories' (hdca-data-portal: embed/tools/README.md): only what is published is drawn, the ET loop from the
public copy of the tiles with its background named in the first caption, and a re-made loop gets a new name.
When a card's loop is re-made, re-make its wide one too and give both new names here and in embed/home/hero.html.
Each replacement below must match its tool exactly once; if a tool has changed, this stops and says which.
"""
import sys
from pathlib import Path

REPOS = Path.home() / "orca/projects"
SCALE = "float(__import__('os').environ.get('SCALE', '1.6'))"
CAPTURE = [("device_scale_factor=1).new_page()", f"device_scale_factor={SCALE}).new_page()")]
TIMELINE = [('json.dumps({"fps": FPS, "W": W, "H": H,', 'json.dumps({"scale": ' + SCALE + ', "fps": FPS, "W": W, "H": H,')]
COMPOSE = [     # the chart panel: its place, its drawing and its rise, all in frame pixels
    ('W, H, FPS = tl["W"], tl["H"], tl["fps"]', 'W, H, FPS = tl["W"], tl["H"], tl["fps"]; S_ = tl.get("scale", 1)'),
    ("PX0, PY0, PX1, PY1, R = 24, 318, 936, 480, 14", "PX0, PY0, PX1, PY1, R = [int(round(v * S_)) for v in (24, 318, 936, 480, 14)]"),
    ("fig = plt.figure(figsize=(pw / 100, ph / 100), dpi=100)", "fig = plt.figure(figsize=(pw / (100 * S_), ph / (100 * S_)), dpi=100 * S_)"),
    ("ax = fig.add_axes([60 / pw, 30 / ph, (pw - 60 - 26) / pw, (ph - 30 - 50) / ph])", "ax = fig.add_axes([60 * S_ / pw, 30 * S_ / ph, (pw - 86 * S_) / pw, (ph - 80 * S_) / ph])"),
    ("fig.text(1 - 22 / pw, 1 - 18 / ph,", "fig.text(1 - 22 * S_ / pw, 1 - 18 * S_ / ph,"),
    ("fig.text(22 / pw, 1 - 20 / ph,", "fig.text(22 * S_ / pw, 1 - 20 * S_ / ph,"),
    ("fig.text(1 - 22 / pw, 1 - 46 / ph,", "fig.text(1 - 22 * S_ / pw, 1 - 46 * S_ / ph,"),
    ("dy_ = int(round((1 - a) * 24))", "dy_ = int(round((1 - a) * 24 * S_))"),
    ("outline=(255, 255, 255, 34), width=s)", "outline=(255, 255, 255, 34), width=int(round(s * S_)))"),
]
CVS = [         # a larger frame, and the stations' marks larger with it
    ("W, H, FPS = 960, 540, int(os.environ.get('CVS_FPS', 24))", "W, H, FPS = 1280, 720, int(os.environ.get('CVS_FPS', 24)); K_ = W / 960"),
    ("rr = (7.5 + 3.5 * ph) * S", "rr = (7.5 + 3.5 * ph) * S * K_"),
    ("width=int(1.2 * S))", "width=int(1.2 * S * K_))"),
    ("r0 = 3.6 * S", "r0 = 3.6 * S * K_"),
    ("dr.ellipse([px - r0 - S, py - r0 - S, px + r0 + S, py + r0 + S], fill=(20, 24, 30, 200))", "dr.ellipse([px - r0 - S * K_, py - r0 - S * K_, px + r0 + S * K_, py + r0 + S * K_], fill=(20, 24, 30, 200))"),
]
TOOLS = {
    "tca_cap": (REPOS / "tv_TCA/portal/embed/tools/cap_tca_westus.py", CAPTURE + TIMELINE),
    "tca_compose": (REPOS / "tv_TCA/portal/embed/tools/compose_tca_westus.py", COMPOSE),
    "hdca_cap": (REPOS / "hdca/portal/embed/tools/cap_hdca_amazon.py", CAPTURE + TIMELINE),
    "hdca_compose": (REPOS / "hdca/portal/embed/tools/compose_hdca_amazon.py", COMPOSE),
    "et_cap": (REPOS / "hdca/portal/embed/tools/cap_et.py", CAPTURE),
    "et_cap_v3": (REPOS / "hdca/portal/embed/tools/cap_et_v3.py", CAPTURE),
    "cvs": (REPOS / "hdca/portal/embed/tools/make_cvs.py", CVS),
}

if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
    sys.exit(__doc__)
path, changes = TOOLS[sys.argv[1]]
code = path.read_text(encoding="utf-8")
for old, new in changes:
    assert code.count(old) == 1, f"{path.name} has changed: expected once, found {code.count(old)} times: {old}"
    code = code.replace(old, new)
sys.argv = [str(path)] + sys.argv[2:]
exec(compile(code, str(path), "exec"), {"__name__": "__main__", "__file__": str(path)})
