#!/usr/bin/env python3
"""Step 3 — the monitoring points behind the product, for the portal's optional point layer.

The published record lists the 1,194 WEIS monitoring points of the training set in station_fold_map.csv
(point number, water-body type, held-out fold, number of matchups) but not where they are. Their names and
coordinates are public WEIS information (National Institute of Environmental Research, KOGL Type 1); the lab's
matchup table carries them. This step joins the two and keeps only what the published list names.

    stations.py --fold-map work/station_fold_map.csv --matchups <final_dataset/matchups_train_pm3.csv> --out out/stations.json

Output: {"types": [...], "points": [[ptNo, name, lat, lon, type index, matchups], ...]}  (WEIS coordinate, 5 decimals)
"""
import argparse
import csv
import json

TYPES = ["river", "reservoir", "lake_dam"]

ap = argparse.ArgumentParser()
ap.add_argument("--fold-map", default="/data/personal_data/project_wq_portal/work/station_fold_map.csv")
ap.add_argument("--matchups", default="/home/data_4/finished_projects/project_water_quality/datasets/final_dataset/matchups_train_pm3.csv")
ap.add_argument("--out", default="/data/personal_data/project_wq_portal/out/stations.json")
a = ap.parse_args()

where = {}
with open(a.matchups, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        k = r["ptNo"]
        here = (r["ptNm"], round(float(r["obs_lat"]), 5), round(float(r["obs_lon"]), 5), r["st_type"])
        assert where.setdefault(k, here) == here, f"{k}: two different names, coordinates or types"

points, n_match = [], 0
with open(a.fold_map, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        name, lat, lon, typ = where[r["ptNo"]]                 # KeyError = a published point the lab table lacks
        assert typ == r["st_type"], f"{r['ptNo']}: type {typ} here, {r['st_type']} in the published list"
        points.append([r["ptNo"], name, lat, lon, TYPES.index(typ), int(r["n_matchups"])])
        n_match += int(r["n_matchups"])
points.sort(key=lambda p: p[0])
assert len(points) == 1194 and n_match == 46933, (len(points), n_match)
json.dump({"source": "Water Environment Information System (WEIS), National Institute of Environmental Research; list and matchup "
                     "counts from station_fold_map.csv of the Zenodo record", "types": TYPES, "points": points},
          open(a.out, "w"), ensure_ascii=False, separators=(",", ":"))
by = {t: sum(1 for p in points if p[4] == i) for i, t in enumerate(TYPES)}
print(f"{len(points)} points ({by}), {n_match} matchups -> {a.out}")
