#!/usr/bin/env python3
"""Step 4 — the skill numbers the portal shows, computed from the record's public validation file.

oof_predictions.csv of the Zenodo record holds the 281,598 out-of-fold predictions (46,933 matchups x six
parameters) of the released model: each monitoring point predicted by a model that never saw it. Everything the
portal says about skill is a grouping of that one file; this step does the groupings so that the page shows
computed numbers, not copied ones. Needs only the standard library and NumPy.

    skill.py --oof work/oof_predictions.csv --out out/skill.json

Per parameter (keys of "params", in the order of the stores: wt, ss, chla, do, tn, tp):
  n, points          matchups and monitoring points
  r2                 R2 over all matchups, in the parameter's unit (the network's single, deterministic prediction: y_pred)
  r2_log             the same on the logarithmic scale, for the four parameters trained on it
  rmse               root-mean-square error of y_pred, in the unit
  within             R2 after removing each point's own mean from observations and predictions: following one place through time
  between            R2 of an oracle that knows each point's long-term mean and nothing else (a ceiling, not a model)
  worse_share        share of the points with ten or more matchups at which the prediction does worse than the point's own mean
  recover_top1       how much of the departure of the top one percent of observations from the median the predictions recover,
                     in the space the parameter was trained in
  r2_mu, r2_log_mu, within_mu     the same three scores for mu_pred, the mean of the dropout passes that the grids carry
  cover_raw, cover_cal            share of observations inside mu_pred +/- 1.96 sigma, before (sigma_pred) and after (sigma_cal) calibration
  calib_c            the calibration factor, sigma_cal / sigma_pred
  rho_sigma          Spearman rank correlation of sigma_cal with the absolute error of mu_pred

"sites": the six monitoring points the paper draws as time series (its Fig. 7), each predicted by the fold that held it
out: matchups and the point's own R2 for water temperature and chlorophyll-a (y_pred, in units).
"""
import argparse
import csv
import json
import time

import numpy as np

ORDER = [("wt", "WT", False), ("ss", "SS", True), ("chla", "Chl-a", True), ("do", "DO", False), ("tn", "TN", True), ("tp", "TP", True)]
SITES = ["1302A40", "2022A20", "5008A10", "1302B10", "3201B20", "5003B10"]      # Jusu Stream, Yangsan Stream 2, Muan 2, Gyeongpo Lake 1, Daeho 2, Naju Dam 2

ap = argparse.ArgumentParser()
ap.add_argument("--oof", default="/data/personal_data/project_wq_portal/work/oof_predictions.csv")
ap.add_argument("--out", default="/data/personal_data/project_wq_portal/out/skill.json")
ap.add_argument("--source", default="oof_predictions.csv of doi:10.5281/zenodo.23750573")
a = ap.parse_args()
t0 = time.time()

cols = {p: {"pt": [], "y": [], "p": [], "mu": [], "sr": [], "sc": []} for _, p, _ in ORDER}
kind = {}
with open(a.oof, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        kind[r["ptNo"]] = r["st_type"]
        c = cols[r["parameter"]]
        c["pt"].append(r["ptNo"]); c["y"].append(float(r["y_true"])); c["p"].append(float(r["y_pred"]))
        c["mu"].append(float(r["mu_pred"])); c["sr"].append(float(r["sigma_pred"])); c["sc"].append(float(r["sigma_cal"]))


def r2(y, p):
    return 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum()


def rank(x):
    """Average ranks (ties share their mean rank)."""
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x)); r[order] = np.arange(len(x), dtype=float)
    xs = x[order]
    start = np.flatnonzero(np.r_[True, xs[1:] != xs[:-1]])
    end = np.r_[start[1:], len(x)]
    for s, e in zip(start, end):
        if e - s > 1:
            r[order[s:e]] = (s + e - 1) / 2
    return r


out = {}
for key, name, is_log in ORDER:
    c = cols[name]
    y, p, mu, sr, sc = (np.array(c[k]) for k in ("y", "p", "mu", "sr", "sc"))
    pts, inv = np.unique(np.array(c["pt"]), return_inverse=True)
    n_pt = np.bincount(inv)
    mean_of = lambda v: (np.bincount(inv, weights=v) / n_pt)[inv]          # each row's own point mean
    yc, pc, mc = y - mean_of(y), p - mean_of(p), mu - mean_of(mu)
    sst_pt = np.bincount(inv, weights=yc ** 2)                              # around the point's own mean
    sse_pt = np.bincount(inv, weights=(y - p) ** 2)
    big = n_pt >= 10
    f = np.log if is_log else (lambda v: v)
    ty, tp = f(y), f(p)
    top = ty >= np.quantile(ty, 0.99)
    row = {
        "n": int(y.size), "points": int(pts.size),
        "r2": r2(y, p), "rmse": float(np.sqrt(((y - p) ** 2).mean())),
        "within": 1 - ((yc - pc) ** 2).sum() / (yc ** 2).sum(),
        "between": 1 - (yc ** 2).sum() / ((y - y.mean()) ** 2).sum(),
        "points_10": int(big.sum()), "worse_share": float((sse_pt[big] > sst_pt[big]).mean()),
        "recover_top1": float((np.median(tp[top]) - np.median(tp)) / (np.median(ty[top]) - np.median(ty))),
        "r2_mu": r2(y, mu), "within_mu": 1 - ((yc - mc) ** 2).sum() / (yc ** 2).sum(),
        "cover_raw": float((np.abs(y - mu) <= 1.96 * sr).mean()), "cover_cal": float((np.abs(y - mu) <= 1.96 * sc).mean()),
        "calib_c": float(np.median(sc / sr)),
        "rho_sigma": float(np.corrcoef(rank(sc), rank(np.abs(y - mu)))[0, 1]),
    }
    if is_log:
        row["r2_log"] = r2(np.log(y), np.log(p))
        row["r2_log_mu"] = r2(np.log(y), np.log(mu))
    out[key] = {k: (v if isinstance(v, int) else round(float(v), 6)) for k, v in row.items()}
    print(f"{name:5s} R2 {out[key]['r2']:.3f}  log {out[key].get('r2_log', float('nan')):.3f}  RMSE {out[key]['rmse']:.4g}  within {out[key]['within']:.3f}"
          f"  worse at {out[key]['worse_share'] * 100:.0f} % of {out[key]['points_10']} points  cover {out[key]['cover_raw']:.3f} -> {out[key]['cover_cal']:.3f}"
          f"  c {out[key]['calib_c']:.2f}  rho {out[key]['rho_sigma']:.2f}  top 1 % recovered {out[key]['recover_top1']:.2f}", flush=True)

sites = []
for pt in SITES:
    row = {"id": pt, "type": kind[pt]}
    for key, name in (("wt", "WT"), ("chla", "Chl-a")):
        c = cols[name]
        sel = np.array(c["pt"]) == pt
        y, p = np.array(c["y"])[sel], np.array(c["p"])[sel]
        row["n"] = int(sel.sum()); row["r2_" + key] = round(float(r2(y, p)), 6)
    sites.append(row)
    print(f"site {pt} ({row['type']}): {row['n']} matchups, R2 WT {row['r2_wt']:.2f}, Chl-a {row['r2_chla']:.2f}", flush=True)

ns = {v["n"] for v in out.values()}
assert len(ns) == 1 and len({v["points"] for v in out.values()}) == 1, "the six parameters should share matchups and points"
json.dump({"source": a.source, "what": "station-held-out five-fold cross-validation of the released model; see pipeline/skill.py for each key",
           "matchups": ns.pop(), "points": out["wt"]["points"], "params": out, "sites": sites}, open(a.out, "w"), indent=1)
print(f"{a.out} written in {time.time() - t0:.0f}s")
