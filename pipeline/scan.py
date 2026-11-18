#!/usr/bin/env python3
"""Step 1 — read every released GeoTIFF once and keep only the cells that carry a value.

The product is sparse: a 470 x 510 grid of which a few thousand water cells have a value on a given
date. This step turns the 6,072 rasters (six parameters x 1,012 dates, two bands each) into one
compact table and checks, while reading, the things the portal relies on:

  * every file has the same grid (size, origin, pixel size, EPSG:4326) and two Float32 bands;
  * on a date the six parameters and both bands share one mask (the Data Descriptor says so);
  * no value is zero or negative where the log encoding of step 2 needs it positive.

Output (work/):
  cube.npz     dates[D] (yyyymmdd), cell_row[C], cell_col[C] (cells with a value on at least one date,
               row-major), start[D+1] (offsets into the cell-day table), cell[N] (cell index of each
               cell-day, ascending within a date), val[N, 12] float32 in the order
               wt_mu, wt_sigma, ss_mu, ss_sigma, chla_mu, chla_sigma, do_mu, do_sigma, tn_mu, tn_sigma, tp_mu, tp_sigma
  scan.json    grid georeference, counts, file sizes per parameter and year, anything unexpected

Run on the lab CPU server (system Python 3.10 with GDAL):  scan.py --src <predictions_1km> --work <work>
"""
import argparse
import glob
import json
import os
import re
import time
from multiprocessing import Pool

import numpy as np
from osgeo import gdal

PARAMS = ["wt", "ss", "chla", "do", "tn", "tp"]
gdal.UseExceptions()


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def read_date(args):
    """One date: six files -> (date, valid flat indices, values[n, 12], notes, bytes per param, georef)."""
    date, files = args
    notes, sizes, georef = [], {}, None
    stack = np.full((12, 470 * 510), np.nan, np.float32)
    masks = []
    for k, p in enumerate(PARAMS):
        f = files.get(p)
        if f is None:
            notes.append(f"{date}: no file for {p}")
            continue
        sizes[p] = os.path.getsize(f)
        ds = gdal.Open(f)
        gt = ds.GetGeoTransform()
        g = (ds.RasterXSize, ds.RasterYSize, ds.RasterCount, gt, ds.GetRasterBand(1).DataType)
        if georef is None:
            georef = g
        elif g != georef:
            notes.append(f"{date}: {p} has a different grid {g}")
        a = ds.ReadAsArray().astype(np.float32)          # (2, rows, cols)
        if a.shape != (2, 470, 510):
            notes.append(f"{date}: {p} has shape {a.shape}")
            continue
        stack[2 * k] = a[0].ravel()
        stack[2 * k + 1] = a[1].ravel()
        masks.append(np.isfinite(a[0].ravel()))
        if not np.array_equal(masks[-1], np.isfinite(a[1].ravel())):
            notes.append(f"{date}: {p} mu and sigma masks differ")
        ds = None
    union = np.zeros(470 * 510, bool)
    for m in masks:
        union |= m
    for k, m in enumerate(masks):
        if not np.array_equal(m, union):
            notes.append(f"{date}: mask of {PARAMS[k]} differs from the union ({int(m.sum())} vs {int(union.sum())})")
    idx = np.flatnonzero(union).astype(np.int32)
    return date, idx, stack[:, idx].T.copy(), notes, sizes, georef


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/home/data_4/finished_projects/project_water_quality/datasets/predictions_1km")
    ap.add_argument("--work", default="/data/personal_data/project_wq_portal/work")
    ap.add_argument("--procs", type=int, default=24)
    a = ap.parse_args()
    t0 = time.time()

    by_date = {}
    for f in sorted(glob.glob(os.path.join(a.src, "20??", "kr_wq_*_1km_*.tif"))):
        m = re.match(r"kr_wq_([a-z]+)_1km_(\d{8})\.tif$", os.path.basename(f))
        if not m or m.group(1) not in PARAMS:
            log(f"unexpected file name: {f}")
            continue
        by_date.setdefault(m.group(2), {})[m.group(1)] = f
    dates = sorted(by_date)
    log(f"{sum(len(v) for v in by_date.values())} files on {len(dates)} dates, {dates[0]} .. {dates[-1]}")

    with Pool(a.procs) as pool:
        res = pool.map(read_date, [(d, by_date[d]) for d in dates], chunksize=8)
    log(f"read in {time.time() - t0:.0f}s")

    notes, georefs = [], set()
    size_py = {}                                    # bytes per parameter and year
    ever = np.zeros(470 * 510, bool)
    for date, idx, vals, nts, sizes, georef in res:
        notes += nts
        georefs.add(georef)
        ever[idx] = True
        for p, s in sizes.items():
            size_py.setdefault(p, {}).setdefault(date[:4], [0, 0])
            size_py[p][date[:4]][0] += 1
            size_py[p][date[:4]][1] += s
    flat = np.flatnonzero(ever)
    cell_of = np.full(470 * 510, -1, np.int32)
    cell_of[flat] = np.arange(flat.size)

    start = np.zeros(len(dates) + 1, np.int64)
    for i, r in enumerate(res):
        start[i + 1] = start[i] + r[1].size
    cell = np.concatenate([cell_of[r[1]] for r in res]).astype(np.uint16)
    val = np.concatenate([r[2] for r in res]).astype(np.float32)
    assert cell.size == start[-1] and (cell_of[flat] >= 0).all() and flat.size < 65535

    nonfinite = int((~np.isfinite(val)).sum())
    if nonfinite:
        notes.append(f"{nonfinite} values are not finite inside the shared mask")
    nonpos = {f"{PARAMS[k // 2]}_{'mu' if k % 2 == 0 else 'sigma'}": int((val[:, k] <= 0).sum()) for k in range(12)}
    nonpos = {k: v for k, v in nonpos.items() if v}

    np.savez(os.path.join(a.work, "cube.npz"), dates=np.array(dates), cell_row=(flat // 510).astype(np.int16),
             cell_col=(flat % 510).astype(np.int16), start=start, cell=cell, val=val)
    g = sorted(georefs)[0]
    n_per_date = np.diff(start)
    out = {"n_files": int(sum(len(v) for v in by_date.values())), "n_dates": len(dates), "first": dates[0], "last": dates[-1],
           "grids_seen": len(georefs), "width": g[0], "height": g[1], "bands": g[2], "geotransform": list(g[3]), "gdal_dtype": g[4],
           "cells_ever": int(flat.size), "cell_days": int(start[-1]),
           "cells_per_date": {"median": float(np.median(n_per_date)), "p10": float(np.percentile(n_per_date, 10)),
                              "p90": float(np.percentile(n_per_date, 90)), "min": int(n_per_date.min()), "max": int(n_per_date.max())},
           "nonpositive": nonpos, "bytes": size_py, "notes": notes[:200], "n_notes": len(notes)}
    json.dump(out, open(os.path.join(a.work, "scan.json"), "w"), indent=1)
    log(f"cells with a value on at least one date: {flat.size}; cell-days: {start[-1]}; "
        f"per date median {np.median(n_per_date):.0f} (p10 {np.percentile(n_per_date, 10):.0f}, p90 {np.percentile(n_per_date, 90):.0f})")
    log(f"non-positive values: {nonpos or 'none'}; notes: {len(notes)}")
    for n in notes[:20]:
        log("  " + n)
    log(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
