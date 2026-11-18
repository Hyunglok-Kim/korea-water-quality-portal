#!/usr/bin/env bash
# Build everything the portal reads, on the lab CPU server as `discover`. The whole run takes under a minute.
#
#   run.sh scan       read the 6,072 GeoTIFFs once, check them, keep the cells with a value   -> work/cube.npz, work/scan.json
#   run.sh store      the two stores and the catalog                                           -> out/*.pmtiles, out/catalog.json
#   run.sh stations   the monitoring points behind the product                                 -> out/stations.json
#   run.sh skill      the skill numbers the page shows, from the record's validation file      -> out/skill.json
#   run.sh all        the four in order
#
# Environment: ROOT (workspace), SRC (folder of <year>/kr_wq_<param>_1km_<yyyymmdd>.tif), ZENODO (record number), PROCS
set -euo pipefail
ROOT=${ROOT:-/data/personal_data/project_wq_portal}
SRC=${SRC:-/home/data_4/finished_projects/project_water_quality/datasets/predictions_1km}
MATCHUPS=${MATCHUPS:-/home/data_4/finished_projects/project_water_quality/datasets/final_dataset/matchups_train_pm3.csv}
ZENODO=${ZENODO:-23750573}
PROCS=${PROCS:-24}
UA="hydroai-data-portal-build/1.0 (+https://hydroai.net)"   # Zenodo refuses curl's default User-Agent from the lab network
PY=$ROOT/venv/bin/python
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$ROOT/out" "$ROOT/work" "$ROOT/logs"

step() {
  case "$1" in
    scan)     "$PY" "$HERE/scan.py" --src "$SRC" --work "$ROOT/work" --procs "$PROCS" 2>&1 | tee "$ROOT/logs/scan.log" ;;
    store)    # the Zenodo record's file list (names, sizes, checksums) goes into the catalog
              curl -fsS -m 60 -A "$UA" "https://zenodo.org/api/records/$ZENODO" -o "$ROOT/work/zenodo.json"
              "$PY" "$HERE/build_store.py" --work "$ROOT/work" --out "$ROOT/out" --zenodo "$ROOT/work/zenodo.json" 2>&1 | tee "$ROOT/logs/store.log" ;;
    stations) curl -fsSL -m 60 -A "$UA" "https://zenodo.org/api/records/$ZENODO/files/station_fold_map.csv/content" -o "$ROOT/work/station_fold_map.csv"
              "$PY" "$HERE/stations.py" --fold-map "$ROOT/work/station_fold_map.csv" --matchups "$MATCHUPS" --out "$ROOT/out/stations.json" 2>&1 | tee "$ROOT/logs/stations.log" ;;
    skill)    [ -s "$ROOT/work/oof_predictions.csv" ] || curl -fsSL -m 600 -A "$UA" "https://zenodo.org/api/records/$ZENODO/files/oof_predictions.csv/content" -o "$ROOT/work/oof_predictions.csv"
              "$PY" "$HERE/skill.py" --oof "$ROOT/work/oof_predictions.csv" --out "$ROOT/out/skill.json" --source "oof_predictions.csv of doi:10.5281/zenodo.$ZENODO" 2>&1 | tee "$ROOT/logs/skill.log" ;;
    *) echo "usage: $0 scan | store | stations | skill | all" >&2; exit 2 ;;
  esac
}
if [ "${1:-}" = all ]; then step scan; step store; step stations; step skill; else step "${1:-}"; fi
