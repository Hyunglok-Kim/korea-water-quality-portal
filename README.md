# Inland water quality of South Korea — data portal

A web portal for the 1 km gridded inland water quality dataset for South Korea, 2016–2024: water
temperature, suspended solids, chlorophyll-a, dissolved oxygen, total nitrogen and total phosphorus
on each of the 1,012 dates on which a cloud-free satellite overpass allowed it, every value with a
calibrated uncertainty. HydroAI Lab, Gwangju Institute of Science and Technology.

**Live:** https://hyunglok-kim.github.io/korea-water-quality-portal/

**The data** are on Zenodo, open, under CC BY 4.0: https://doi.org/10.5281/zenodo.23750573
(Lee, S. and Kim, H., 2026). The paper describing them (Lee, S., Lee, J., Lee, D., and Kim, H., “A
satellite-reanalysis deep-learning 1 km gridded inland water quality dataset for South Korea,
2016–2024”) is a Data Descriptor under review at *Scientific Data*. Please cite both.

## What it does

- Opens on the globe and flies down to the peninsula; every 1 km water cell of the product is on
  the map, drawn as the square it is (as a dot when seen from afar, so rivers can be followed).
- Six parameters, each as its value or its uncertainty, in four views: one overpass date as
  released, the mean of a month, the mean of a calendar month over all years, and the mean of the
  whole record. A seventh layer counts the dates with a value at each cell.
- Says what kind of layer each parameter is (optical retrieval, catchment-context estimate,
  meteorologically driven) and what that kind can and cannot be used for, as the paper does, with the
  skill numbers computed from the record's public validation file.
- Click a cell for every overpass at that cell with its 95 % interval, for the chosen year and for
  the whole record, small charts of all six parameters, a table and a CSV.
- Optional layer of the 1,194 national monitoring points the model was trained and tested on, and
  a list of reservoirs, river reaches and the six monitoring points shown in the paper.
- Download tab with direct links to every file of the Zenodo record; code examples in Python and R.
- The map needs WebGL. In a browser that does not provide it, the page says so where the map would
  be and what to do about it; the cards and the other tabs still work.

## How it works

The site is static: one HTML page, one script, no build step, no server. The map does not show
pictures of the data. The product is sparse (8,558 cells ever carry a value; 1.53 million
cell-values per layer in the whole record), so the browser reads the numbers themselves from two
[PMTiles](https://docs.protomaps.com/pmtiles/) archives used as range-readable key-value stores:
one ordered by date for the map, one by cell for the series. [MapLibre GL JS](https://maplibre.org/)
draws the cells and colours them through feature state, which keeps the legend adjustable and the
cursor readout equal to the stored value.

```
index.html, css/, js/     the portal
assets/                   logos, the link-preview picture
data/                     catalog.json, the two stores, the monitoring points, the skill numbers (71 MB)
pipeline/                 GeoTIFFs → stores + catalog (Python, GDAL), validation file → skill numbers;
                          runs in under a minute
tests/                    headless-browser smoke test (Playwright) and its reference values
```

`CLAUDE.md` has the details: the layout of the stores, how to rebuild them, how to run and test,
and the rules the design must keep.

## Try it locally

```bash
pip install uvicorn starlette
python dev_server.py --data data        # then open http://127.0.0.1:8797/
```

Any web server that answers HTTP Range requests will do (`python -m http.server` does not).

## Credits

Map rendering: MapLibre GL JS. Archive format: PMTiles (Protomaps). Satellite imagery: Esri World
Imagery. The dataset contains modified Copernicus Climate Change Service information (ERA5-Land) and
Copernicus DEM data, and information from the Water Environment Information System and the
Environmental Geographic Information Service of the Republic of Korea; it was produced using data
from the Harmonized Landsat Sentinel-2 project (NASA/USGS) and the Global Surface Water Occurrence
layer (European Commission Joint Research Centre).

Contact: HydroAI Lab — hyunglokkim@gist.ac.kr
