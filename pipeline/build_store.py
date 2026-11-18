#!/usr/bin/env python3
"""Step 2 — the portal's two stores and its catalog, from the compact table of step 1 (work/cube.npz).

Why not map tiles or pictures. The product has 8,558 cells that ever carry a value and 1.53 million
cell-days in all. The whole record, both bands of all six parameters, is 37 MB as 16-bit numbers. So the
browser gets the numbers themselves, draws the cells as the squares they are and reads values exactly;
nothing is resampled and no tile server is involved.

Numbers are stored as unsigned 16-bit integers (little-endian), 65535 = no value:
    lin   value = DN * scale + offset              WT and DO (mean and uncertainty)
    log   value = v0 * exp(DN * k)                 SS, Chl-a, TN, TP (mean and uncertainty): a constant
                                                   relative step of 0.028 % over 0.001 .. 100,000
Layer index L: 0 wt_mu, 1 wt_sigma, 2 ss_mu, 3 ss_sigma, 4 chla_mu, 5 chla_sigma, 6 do_mu, 7 do_sigma,
               8 tn_mu, 9 tn_sigma, 10 tp_mu, 11 tp_sigma

Both stores are PMTiles archives used as range-readable key-value stores (the lab dashboard serves only
.json and .pmtiles from a portal's data folder). Every entry is gzip-compressed; pmtiles.js inflates on read.

  kr_wq_1km_fields.pmtiles      everything the map needs, by date            address z = 10, x, y
      x = 12, y = year index    the mask of that year: for each date in order, the cell indices (ascending)
                                that carry a value; how many per date is catalog.dates.n
      x = L,  y = year index    layer L for the same cell-days, in the same order
      x = L,  y = 20            [13][cells]: mean over the cell's dates in the whole record (0) and in each
                                calendar month over all years (1..12)
      x = 13, y = 20            [13][cells]: number of dates with a value, same slots
    year index = year - 2016

  kr_wq_1km_series.pmtiles      everything a click needs, by cell             address z = 10, x = column, y = row
      one entry per cell:  n, date index [n], then [12 layers][n] values       (date index into catalog.dates.d)

  catalog.json                  grid, cells, dates, encodings, statistics, the Zenodo file list
  work/field_ref.json           reference values for the browser test (tests/smoke.py)
"""
import argparse
import gzip
import json
import math
import os
import time

import numpy as np
from pmtiles.tile import Compression, TileType, zxy_to_tileid
from pmtiles.writer import Writer

PARAMS = [
    {"id": "wt", "label": "WT", "name": "Water temperature", "units": "°C", "regime": "meteorological", "log": False},
    {"id": "ss", "label": "SS", "name": "Suspended solids", "units": "mg/L", "regime": "optical", "log": True},
    {"id": "chla", "label": "Chl-a", "name": "Chlorophyll-a", "units": "µg/L", "regime": "optical", "log": True},
    {"id": "do", "label": "DO", "name": "Dissolved oxygen", "units": "mg/L", "regime": "meteorological", "log": False},
    {"id": "tn", "label": "TN", "name": "Total nitrogen", "units": "mg/L", "regime": "catchment context", "log": True},
    {"id": "tp", "label": "TP", "name": "Total phosphorus", "units": "mg/L", "regime": "optical", "log": True},
]
LAYERS = [f"{p['id']}_{b}" for p in PARAMS for b in ("mu", "sigma")]
NODATA = 65535
LOG_V0, LOG_VMAX = 1e-3, 1e5
LOG_K = math.log(LOG_VMAX / LOG_V0) / 65534
Z = 10
X_MASK, X_COUNT, Y_CLIM, Y0 = 12, 13, 20, 2016


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def encoding(layer):
    p = layer.split("_")[0]
    if p == "wt":
        return {"enc": "lin", "scale": 0.001, "offset": -5.0 if layer.endswith("_mu") else 0.0}
    if p == "do":
        return {"enc": "lin", "scale": 0.001, "offset": 0.0}
    return {"enc": "log", "v0": LOG_V0, "k": LOG_K}


def encode(v, e):
    """float array -> uint16 DN, NaN -> 65535. Returns (dn, number of values that had to be clipped)."""
    v = np.asarray(v, np.float64)
    ok = np.isfinite(v)
    x = np.zeros(v.shape, np.float64)
    if e["enc"] == "lin":
        x[ok] = np.rint((v[ok] - e["offset"]) / e["scale"])
    else:
        x[ok] = np.rint(np.log(np.maximum(v[ok], 1e-300) / e["v0"]) / e["k"])
    clipped = int(((x < 0) | (x > 65534))[ok].sum())
    dn = np.full(v.shape, NODATA, np.uint16)
    dn[ok] = np.clip(x[ok], 0, 65534).astype(np.uint16)
    return dn, clipped


def decode(dn, e):
    dn = np.asarray(dn)
    out = dn * e["scale"] + e["offset"] if e["enc"] == "lin" else e["v0"] * np.exp(dn * e["k"])
    return np.where(dn == NODATA, np.nan, out)


def gz(a):
    return gzip.compress(np.ascontiguousarray(a).tobytes(), 9, mtime=0)


def write_archive(path, entries, meta, bounds):
    entries.sort(key=lambda t: t[0])
    tmp = path + ".part"
    w, s, e, n = bounds
    with open(tmp, "wb") as fh:
        wr = Writer(fh)
        for tid, data in entries:
            wr.write_tile(tid, data)
        wr.finalize({"tile_type": TileType.UNKNOWN, "tile_compression": Compression.GZIP,
                     "min_lon_e7": int(w * 1e7), "min_lat_e7": int(s * 1e7), "max_lon_e7": int(e * 1e7), "max_lat_e7": int(n * 1e7),
                     "center_zoom": 6, "center_lon_e7": int((w + e) / 2 * 1e7), "center_lat_e7": int((s + n) / 2 * 1e7)}, meta)
    os.replace(tmp, path)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", default="/data/personal_data/project_wq_portal/work")
    ap.add_argument("--out", default="/data/personal_data/project_wq_portal/out")
    ap.add_argument("--zenodo", default="", help="JSON of the Zenodo record (https://zenodo.org/api/records/<id>), for the file list")
    ap.add_argument("--build", default=time.strftime("%Y-%m-%d"))
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)

    z = np.load(os.path.join(a.work, "cube.npz"))
    scan = json.load(open(os.path.join(a.work, "scan.json")))
    dates = [str(d) for d in z["dates"]]
    row, col = z["cell_row"].astype(int), z["cell_col"].astype(int)
    start, cell, val = z["start"], z["cell"].astype(np.int64), z["val"]
    D, C, N = len(dates), row.size, cell.size
    gt = scan["geotransform"]
    assert scan["grids_seen"] == 1 and scan["n_notes"] == 0 and not scan["nonpositive"], "step 1 found something unexpected; read work/scan.json"
    assert abs(gt[1] + gt[5]) < 1e-15 and gt[2] == 0 and gt[4] == 0
    bounds = (gt[0], gt[3] + gt[5] * scan["height"], gt[0] + gt[1] * scan["width"], gt[3])
    n_date = np.diff(start).astype(int)
    date_of = np.repeat(np.arange(D), n_date)                       # date index of each cell-day
    year_of = np.array([int(d[:4]) for d in dates])
    mon_of = np.array([int(d[4:6]) for d in dates])
    years = sorted(set(year_of.tolist()))
    assert years[0] == Y0
    encs = {L: encoding(L) for L in LAYERS}
    log(f"{D} dates, {C} cells, {N} cell-days")

    # ── encode the whole table once ──
    dn = np.empty((N, 12), np.uint16)
    for k, L in enumerate(LAYERS):
        dn[:, k], clipped = encode(val[:, k], encs[L])
        assert clipped == 0, f"{L}: {clipped} values outside the encoding range"
        back = decode(dn[:, k], encs[L])
        err = np.abs(back - val[:, k]) / (1 if encs[L]["enc"] == "lin" else val[:, k])
        log(f"  {L:11s} {encs[L]['enc']}  max {'abs' if encs[L]['enc'] == 'lin' else 'rel'} error {err.max():.2e}")

    # ── fields store ──
    entries, raw_bytes = [], 0
    for y in years:
        d0, d1 = np.searchsorted(year_of, y), np.searchsorted(year_of, y, "right")
        s0, s1 = start[d0], start[d1]
        blob = cell[s0:s1].astype("<u2")
        entries.append((zxy_to_tileid(Z, X_MASK, y - Y0), gz(blob))); raw_bytes += blob.nbytes
        for k in range(12):
            blob = dn[s0:s1, k].astype("<u2")
            entries.append((zxy_to_tileid(Z, k, y - Y0), gz(blob))); raw_bytes += blob.nbytes

    # per-cell aggregates: record (slot 0) and calendar months (1..12)
    cnt = np.zeros((13, C), np.int64)
    np.add.at(cnt[0], cell, 1)
    mon_cd = mon_of[date_of]
    for m in range(1, 13):
        np.add.at(cnt[m], cell[mon_cd == m], 1)
    assert cnt.max() < NODATA and (cnt[0] > 0).all() and (cnt[1:].sum(0) == cnt[0]).all()
    blob = cnt.astype("<u2")
    entries.append((zxy_to_tileid(Z, X_COUNT, Y_CLIM), gz(blob))); raw_bytes += blob.nbytes
    clim = np.full((12, 13, C), np.nan)
    for k in range(12):
        v = val[:, k].astype(np.float64)
        s = np.zeros((13, C))
        np.add.at(s[0], cell, v)
        for m in range(1, 13):
            sel = mon_cd == m
            np.add.at(s[m], cell[sel], v[sel])
        with np.errstate(invalid="ignore", divide="ignore"):
            clim[k] = np.where(cnt > 0, s / cnt, np.nan)
        blob, clipped = encode(clim[k], encs[LAYERS[k]])
        assert clipped == 0
        blob = blob.astype("<u2")
        entries.append((zxy_to_tileid(Z, k, Y_CLIM), gz(blob))); raw_bytes += blob.nbytes
    fields_meta = {"name": "kr_wq 1 km fields", "type": "fields", "addressing": "z=10; see the catalog's store.fields",
                   "layers": LAYERS, "nodata": NODATA, "encoding": encs, "dtype": "uint16 little-endian, gzip"}
    fb = write_archive(os.path.join(a.out, "kr_wq_1km_fields.pmtiles"), entries, fields_meta, bounds)
    log(f"fields store: {len(entries)} entries, {raw_bytes / 1e6:.1f} MB raw -> {fb / 1e6:.1f} MB")

    # ── series store: one entry per cell ──
    order = np.argsort(cell, kind="stable")                         # cell-days grouped by cell, dates ascending inside
    c_start = np.zeros(C + 1, np.int64)
    c_start[1:] = np.cumsum(cnt[0])
    entries, raw_bytes = [], 0
    for c in range(C):
        sel = order[c_start[c]:c_start[c + 1]]
        n = sel.size
        blob = np.concatenate([np.array([n], "<u2"), date_of[sel].astype("<u2"), dn[sel].T.astype("<u2").ravel()])
        entries.append((zxy_to_tileid(Z, int(col[c]), int(row[c])), gz(blob))); raw_bytes += blob.nbytes
    series_meta = {"name": "kr_wq 1 km cell series", "type": "series", "addressing": "z=10, x=column, y=row",
                   "layout": "uint16 little-endian, gzip: n, date index [n], then [12 layers][n]", "layers": LAYERS,
                   "nodata": NODATA, "encoding": encs}
    sb = write_archive(os.path.join(a.out, "kr_wq_1km_series.pmtiles"), entries, series_meta, bounds)
    log(f"series store: {len(entries)} entries, {raw_bytes / 1e6:.1f} MB raw -> {sb / 1e6:.1f} MB")

    # ── statistics for the catalog ──
    def r(x, nd=6):
        return float(f"{float(x):.{nd}g}")

    layer_stats = {}
    for k, L in enumerate(LAYERS):
        v = val[:, k]
        q = np.percentile(v, [0.1, 2, 25, 50, 75, 98, 99.9])
        layer_stats[L] = {"min": r(v.min()), "p001": r(q[0]), "p02": r(q[1]), "p25": r(q[2]), "p50": r(q[3]), "p75": r(q[4]),
                          "p98": r(q[5]), "p999": r(q[6]), "max": r(v.max()), "mean": r(v.mean())}
    months = []
    for y in years:
        for m in range(1, 13):
            di = np.flatnonzero((year_of == y) & (mon_of == m))
            if not di.size:
                months.append({"ym": f"{y}-{m:02d}", "dates": 0, "cell_days": 0, "cells": 0})
                continue
            s0, s1 = start[di[0]], start[di[-1] + 1]
            months.append({"ym": f"{y}-{m:02d}", "dates": int(di.size), "cell_days": int(s1 - s0), "cells": int(np.unique(cell[s0:s1]).size),
                           "median": [r(np.median(val[s0:s1, k]), 5) for k in range(12)]})
    clim_months = []
    for m in range(1, 13):
        sel = mon_cd == m
        clim_months.append({"month": m, "dates": int((mon_of == m).sum()), "cell_days": int(sel.sum()), "cells": int((cnt[m] > 0).sum()),
                            "median": [r(np.median(val[sel, k]), 5) for k in range(12)]})
    year_rows = []
    for y in years:
        di = np.flatnonzero(year_of == y)
        b = sum(scan["bytes"][p["id"]][str(y)][1] for p in PARAMS)
        year_rows.append({"year": y, "dates": int(di.size), "files": int(di.size) * 6, "cell_days": int(start[di[-1] + 1] - start[di[0]]),
                          "bytes": int(b), "first": dates[di[0]], "last": dates[di[-1]]})
    iso = lambda d: f"{d[:4]}-{d[4:6]}-{d[6:]}"

    files = []
    if a.zenodo:
        zr = json.load(open(a.zenodo))
        rec = zr["id"]
        for f in sorted(zr["files"], key=lambda f: f["key"]):
            files.append({"name": f["key"], "bytes": f["size"], "md5": f["checksum"].replace("md5:", ""),
                          "url": f"https://zenodo.org/records/{rec}/files/{f['key']}?download=1"})
        product = {"title": zr["metadata"]["title"], "doi": zr["doi"], "concept_doi": zr.get("conceptdoi"), "record": rec,
                   "published": zr["metadata"]["publication_date"], "license": "CC BY 4.0 (data, models) · MIT (code)"}
    else:
        product = {}

    catalog = {
        "version": f"Zenodo v4 (grids unchanged since v3) · portal build {a.build}",
        "product": product,
        "record": {"first": iso(dates[0]), "last": iso(dates[-1]), "n": D, "with_tiles": D, "cell_days": N, "rasters": scan["n_files"],
                   "bytes": int(sum(yr["bytes"] for yr in year_rows)),
                   "cells_per_date": {"median": float(np.median(n_date)), "p10": float(np.percentile(n_date, 10)), "p90": float(np.percentile(n_date, 90)),
                                      "min": int(n_date.min()), "max": int(n_date.max())}},
        "grid": {"crs": "EPSG:4326", "width": scan["width"], "height": scan["height"], "x0": gt[0], "y0": gt[3], "dx": gt[1], "dy": -gt[5],
                 "cells_total": scan["width"] * scan["height"], "cells_inside_boundary": 99950, "cells_predictable_water": 13469},
        "cells": {"n": C, "row": row.tolist(), "col": col.tolist()},
        "dates": {"d": dates, "n": n_date.tolist()},
        "params": PARAMS,
        "layers": [{"id": L, "x": k, **encs[L], "stats": layer_stats[L]} for k, L in enumerate(LAYERS)],
        "months": months, "clim_months": clim_months, "years": year_rows,
        "store": {"nodata": NODATA, "zoom": Z, "year0": Y0,
                  "fields": {"file": "kr_wq_1km_fields.pmtiles", "bytes": fb, "x_mask": X_MASK, "x_count": X_COUNT, "y_clim": Y_CLIM},
                  "series": {"file": "kr_wq_1km_series.pmtiles", "bytes": sb}},
        "files": files,
    }
    json.dump(catalog, open(os.path.join(a.out, "catalog.json"), "w"), separators=(",", ":"), ensure_ascii=False)
    log(f"catalog.json: {os.path.getsize(os.path.join(a.out, 'catalog.json')) / 1e3:.0f} KB")

    # ── reference values for the browser test, straight from the float table ──
    ref = {"dates": {}, "cells": {}, "clim": {}}
    for d in [dates[0], "20181025", "20231203", dates[-1]]:
        i = dates.index(d)
        s0, s1 = int(start[i]), int(start[i + 1])
        picks = sorted({s0, (s0 + s1) // 2, s1 - 1})
        ref["dates"][d] = {"n": s1 - s0, "sum": [float(val[s0:s1, k].astype(np.float64).sum()) for k in range(12)],
                           "at": [{"cell": int(cell[j]), "row": int(row[cell[j]]), "col": int(col[cell[j]]), "v": [float(x) for x in val[j]]} for j in picks]}
    for c in [0, int(np.argmax(cnt[0])), C // 2, C - 1]:
        sel = order[c_start[c]:c_start[c + 1]]
        ref["cells"][str(c)] = {"row": int(row[c]), "col": int(col[c]), "n": int(sel.size), "first": dates[date_of[sel[0]]], "last": dates[date_of[sel[-1]]],
                                "mean": [float(val[sel, k].astype(np.float64).mean()) for k in range(12)]}
        ref["clim"][str(c)] = {"count": cnt[:, c].tolist(), "all": [float(clim[k, 0, c]) for k in range(12)]}
    json.dump(ref, open(os.path.join(a.work, "field_ref.json"), "w"), indent=1)
    log(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
