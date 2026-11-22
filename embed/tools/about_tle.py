#!/usr/bin/env python3
"""about_tle.py [--from FILE] — the orbital elements for the globe on the About page, renewed.

    python embed/tools/about_tle.py               # fetch from CelesTrak, rewrite embed/media/about/orbit-tle.json
    python embed/tools/about_tle.py --from FILE   # the same from a file instead of CelesTrak: TLE text, or the
                                                  # dashboard's cache (~/.hydroai/cache/satellite_tle.json,
                                                  # a JSON with the text under `text` and the time under `at`)

Why: the globe (embed/media/about/orbit-v1.js) works out where each satellite is in the visitor's browser,
with SGP4, from two-line orbital elements (TLE). Elements go stale: a low satellite drawn from elements two
weeks old is seconds to minutes away from where it really is. The page starts from orbit-tle.json at once,
and only when that file is more than seven days old does the browser ask CelesTrak by itself. So this file
is worth renewing every few days, and after any change to the list of satellites; then commit and push it.

Which satellites: the ones listed in orbit-v1.js, on the lines between `// roster:begin` and `// roster:end`.
There is no second list here. The file written holds exactly those, in that order:

    {"at": "<when the elements were fetched, UTC>", "source": "CelesTrak",
     "tle": {"40376": ["1 40376U ...", "2 40376 ..."], ...}}

From CelesTrak it takes the dashboard's plan: the two group files `resource` and `weather`, then one request
by catalogue number for each satellite of the list that neither file has. The dashboard's plan names eight
of those (Sentinel-1C and 1D, NISAR, GRACE-FO 1 and 2, GCOM-W1, GCOM-C, GOSAT-GW); one that a group file
has come to hold is not asked for a second time, and one added to the list later is asked for without a
change here. Ten requests at most today.

Politeness: CelesTrak renews its files about every two hours and asks that nobody fetch them more often than
that. This tool names the lab's site in its User-Agent, waits a second between requests, and will not fetch
when orbit-tle.json says its elements were fetched less than two hours ago. `--from` is not a fetch and
always runs; with a text file the time written is the file's own.

It fails loudly, and leaves the old orbit-tle.json as it was, when a satellite of the list is missing from
what it got, when a line is not 69 characters or its checksum is wrong, or when CelesTrak does not answer.
Not a failure, but said: elements more than 14 days old, which is what a satellite that is no longer
tracked looks like; that one is for the list in orbit-v1.js, not for this tool.

Standard library only.
"""
import datetime
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ABOUT = Path(__file__).resolve().parents[1] / "media" / "about"
MODULE = ABOUT / "orbit-v1.js"
OUT = ABOUT / "orbit-tle.json"
CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php?"
GROUPS = ["resource", "weather"]
UA = "hydroai.net-about-page/1 (orbital elements for the globe on https://hydroai.net/about; embed/tools/about_tle.py)"
UTC = datetime.timezone.utc


def roster():
    """[(catalogue number, name)] from the list in orbit-v1.js."""
    text = MODULE.read_text(encoding="utf-8")
    m = re.search(r"// roster:begin\n(.*?)// roster:end", text, re.S)
    if not m:
        sys.exit(f"no list between `// roster:begin` and `// roster:end` in {MODULE}")
    sats = []
    for line in m.group(1).splitlines():
        if not line.strip():
            continue
        row = re.match(r'\s*\[(\d+),\s*"[^"]+",\s*"([^"]+)"', line)
        if not row:
            sys.exit(f"a line of the list in {MODULE.name} that is not a satellite:\n  {line.strip()[:100]}")
        sats.append((int(row.group(1)), row.group(2)))
    if not sats or len(set(n for n, _ in sats)) != len(sats):
        sys.exit(f"the list in {MODULE.name} is empty or has a catalogue number twice")
    return sats


def checksum_ok(line):
    return line[68].isdigit() and sum(int(c) if c.isdigit() else c == "-" for c in line[:68]) % 10 == int(line[68])


def epoch(line1):
    """The epoch of line 1 (two-digit year, day of the year with a fraction) as a datetime in UTC."""
    yy, day = int(line1[18:20]), float(line1[20:32])
    return datetime.datetime(2000 + yy if yy < 57 else 1900 + yy, 1, 1, tzinfo=UTC) + datetime.timedelta(days=day - 1)


def elements(text):
    """{catalogue number: (line 1, line 2)} from TLE text; of two sets for one satellite the later epoch."""
    lines = [s.rstrip() for s in text.splitlines()]
    found, bad = {}, []
    for a, b in zip(lines, lines[1:]):
        if not (a.startswith("1 ") and b.startswith("2 ")):
            continue
        if len(a) != 69 or len(b) != 69 or not a[2:7].strip().isdigit() or a[2:7] != b[2:7] or not (checksum_ok(a) and checksum_ok(b)):
            bad.append(a[:24])
            continue
        n = int(a[2:7])
        try:
            if n not in found or epoch(a) > epoch(found[n][0]):
                found[n] = (a, b)
        except ValueError:
            bad.append(a[:24])
    return found, bad


def fetch(query):
    time.sleep(1)
    req = urllib.request.Request(CELESTRAK + query + "&FORMAT=tle", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.read().decode("utf-8", "replace")
    except OSError as e:                            # no answer, or an answer that is an error
        sys.exit(f"CelesTrak did not answer for {query} ({e}): nothing written, {OUT.name} is as it was")


def from_celestrak(sats):
    if OUT.exists():
        try:
            last = datetime.datetime.fromisoformat(json.loads(OUT.read_text(encoding="utf-8"))["at"].replace("Z", "+00:00"))
            age = datetime.datetime.now(UTC) - last
            if age < datetime.timedelta(hours=2):
                sys.exit(f"{OUT.name} was fetched {int(age.total_seconds() // 60)} minutes ago, and CelesTrak asks for two hours "
                         "between fetches: nothing fetched, nothing written (--from FILE works at any time)")
        except (KeyError, ValueError):
            pass                                    # an unreadable old file is no reason to wait
    found, bad = {}, []
    for g in GROUPS:
        f, b = elements(fetch("GROUP=" + g))
        if not f:
            sys.exit(f"CelesTrak gave no elements for the group {g}: nothing written")
        print(f"  group {g}: {len(f)} satellites")
        found.update({n: v for n, v in f.items() if n not in found or epoch(v[0]) > epoch(found[n][0])})
        bad += b
    for n, name in sats:
        if n not in found:
            f, b = elements(fetch(f"CATNR={n}"))
            print(f"  {n} {name}: {'found' if n in f else 'NOT FOUND'}")
            found.update(f)
            bad += b
    return found, bad, datetime.datetime.now(UTC)


def from_file(path):
    raw = Path(path).read_text(encoding="utf-8")
    at = datetime.datetime.fromtimestamp(os.path.getmtime(path), UTC)
    if raw.lstrip().startswith("{"):                # the dashboard's cache: {"at": ms, "source": ..., "text": ...}
        d = json.loads(raw)
        raw = d["text"]
        if isinstance(d.get("at"), (int, float)):
            at = datetime.datetime.fromtimestamp(d["at"] / 1000, UTC)
    found, bad = elements(raw)
    return found, bad, at


def main(argv):
    if argv and argv[0] in ("-h", "--help") or len(argv) not in (0, 2) or (argv and argv[0] != "--from"):
        sys.exit(__doc__)
    sats = roster()
    print(f"{len(sats)} satellites in the list of {MODULE.name}")
    found, bad, at = from_file(argv[1]) if argv else from_celestrak(sats)
    missing = [f"{n} {name}" for n, name in sats if n not in found]
    if missing:
        hint = f" ({len(bad)} sets of lines were left out as damaged: {', '.join(bad[:5])})" if bad else ""
        sys.exit(f"NOT WRITTEN, {OUT.name} is as it was: no elements for {len(missing)} of the {len(sats)} satellites: "
                 + "; ".join(missing) + hint)
    rows = [f'  "{n}": {json.dumps(list(found[n]))}' for n, _ in sats]
    text = ('{\n "at": "' + at.strftime("%Y-%m-%dT%H:%M:%SZ") + '",\n "source": "CelesTrak",\n "tle": {\n'
            + ",\n".join(rows) + "\n }\n}\n")
    json.loads(text)                                # what is written is JSON, or nothing is written
    tmp = OUT.with_name(OUT.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, OUT)
    epochs = sorted(epoch(found[n][0]) for n, _ in sats)
    print(f"wrote {OUT} ({len(text)} bytes): {len(sats)} satellites, fetched {at:%Y-%m-%d %H:%M} UTC, "
          f"epochs {epochs[0]:%Y-%m-%d %H:%M} to {epochs[-1]:%Y-%m-%d %H:%M} UTC")
    for n, name in sats:
        old = (at - epoch(found[n][0])).days
        if old > 14:
            print(f"  note: the elements of {n} {name} are {old} days old; is it still tracked?")


if __name__ == "__main__":
    main(sys.argv[1:])
