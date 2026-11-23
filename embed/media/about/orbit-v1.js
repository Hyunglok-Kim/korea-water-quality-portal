/* orbit-v1.js: the globe on the About page of hydroai.net (HydroAI lab, GIST).

   It shows where the Earth-observing satellites the lab works with are at this moment: a globe that opens
   on Korea, each satellite as a dot in the colour of its family, the path it has just flown and the path
   ahead of it, the night side where the Sun is not, and the lab's field site. Nothing is fetched from a
   server of ours: the positions are worked out in the visitor's browser with SGP4 from orbital elements.

       <script src=".../embed/media/about/orbit-v1.js"></script>
       HydroOrbit.mount(el, { base: ".../embed/media/about/" }).then(function (globe) { ... });

   mount(el, opts) returns a Promise that never rejects. It resolves to { destroy() } when the globe is
   drawn, and to null when it could not be (a file did not load, no canvas, an error at the start). `el`
   keeps what it holds: the globe is added as one more child, and el gets data-orbit="on" when the globe
   is drawn, data-orbit="off" when it is not or has been taken away, so the page can show a picture
   instead. opts.base is the folder of the four files; without it the folder this file came from is used.

   The files, all in one folder:
       orbit-v1.js          this file
       orbit-lib-v1.js      d3-array + d3-geo and satellite.js (they set window.d3 and window.satellite)
       orbit-land-v1.json   the outlines of the land (Natural Earth 110 m), one GeoJSON MultiPolygon
       orbit-tle.json       the orbital elements, rewritten by embed/tools/about_tle.py

   When orbit-tle.json is more than a week old the browser asks CelesTrak itself, once, in the background,
   and remembers the answer for a day (localStorage, one key). Every failure there is silent.

   The list of satellites below is the only one: about_tle.py reads the catalogue numbers from it.
   HydroOrbit._state() and HydroOrbit._subpoint(key, ms) are for the checks, not for pages. */
(function () {
  "use strict";

  var W = window, D = document;
  if (W.HydroOrbit && typeof W.HydroOrbit.mount === "function") return;

  var SELF = (D.currentScript && D.currentScript.src) || "";
  var SELF_BASE = SELF ? SELF.replace(/[?#].*$/, "").replace(/[^\/]*$/, "") : "";

  var LIB = "orbit-lib-v1.js", LAND = "orbit-land-v1.json", TLE = "orbit-tle.json";

  /* The four families. The colours were checked for colour-blind separation on the dark panel. */
  var FAMILIES = [
    { id: "soil", name: "Soil moisture", color: "#c98500" },
    { id: "sar", name: "Radar (SAR)", color: "#d55181" },
    { id: "optical", name: "Optical & thermal", color: "#008300" },
    { id: "water", name: "Rain, water & ice", color: "#3987e5" }
  ];

  /* The satellites: catalogue number (NORAD), key, name, agency, family, instrument, what it is used for,
     mission page, and for satellites that fly as a group the one name the group shares on the globe.
     One satellite on one line, between the two marks: embed/tools/about_tle.py reads the numbers here. */
  var ROSTER = [
    // roster:begin
    [40376, "smap", "SMAP", "NASA/JPL", "soil", "L-band radiometer (1.41 GHz)", "Surface soil moisture (0–5 cm), freeze/thaw", "https://smap.jpl.nasa.gov/"],
    [36036, "smos", "SMOS", "ESA", "soil", "MIRAS L-band interferometric radiometer", "Surface soil moisture, VOD", "https://earth.esa.int/eogateway/missions/smos"],
    [38771, "metopb", "MetOp-B", "EUMETSAT", "soil", "ASCAT C-band scatterometer (2×550 km)", "Soil moisture (saturation), ocean wind", "https://www.eumetsat.int/metop"],
    [43689, "metopc", "MetOp-C", "EUMETSAT", "soil", "ASCAT C-band scatterometer (2×550 km)", "Soil moisture (saturation), ocean wind", "https://www.eumetsat.int/metop"],
    [38337, "gcomw1", "GCOM-W1", "JAXA", "soil", "AMSR2 multi-frequency MW radiometer", "Soil moisture, precip, snow, vapor", "https://global.jaxa.jp/projects/sat/gcom_w/"],
    [64694, "gosatgw", "GOSAT-GW", "JAXA", "soil", "AMSR3 multi-frequency MW radiometer", "Soil moisture, precip, snow (AMSR2 continuity)", "https://www.satnavi.jaxa.jp/files/project/gosat-gw/en/"],
    [39634, "s1a", "Sentinel-1A", "ESA", "sar", "C-band SAR (IW 250 km, right-looking)", "Flood mapping, paddies, hi-res soil moisture", "https://sentinels.copernicus.eu/copernicus/sentinel-1"],
    [62261, "s1c", "Sentinel-1C", "ESA", "sar", "C-band SAR (IW 250 km, right-looking)", "Flood mapping, paddies, hi-res soil moisture", "https://sentinels.copernicus.eu/copernicus/sentinel-1"],
    [66315, "s1d", "Sentinel-1D", "ESA", "sar", "C-band SAR (IW 250 km, right-looking)", "Flood mapping, paddies, hi-res soil moisture", "https://sentinels.copernicus.eu/copernicus/sentinel-1"],
    [65053, "nisar", "NISAR", "NASA/ISRO", "sar", "L+S-band SAR (242 km, left-looking)", "200-m soil moisture, inundation, wetlands, snow", "https://nisar.jpl.nasa.gov/"],
    [39227, "k5", "KOMPSAT-5", "KARI", "sar", "COSI X-band SAR (30 km std / 100 km wide)", "Korea flood/reservoir monitoring, soil moisture R&D", "https://www.kari.re.kr/kor/contents/34"],
    [25994, "terra", "Terra", "NASA", "optical", "MODIS 36-band imaging radiometer", "ET (MOD16), snow (MOD10), LST", "https://terra.nasa.gov/"],
    [27424, "aqua", "Aqua", "NASA", "optical", "MODIS 36-band imaging radiometer", "ET, snow (MYD10), LST", "https://aqua.nasa.gov/"],
    [39084, "l8", "Landsat 8", "NASA/USGS", "optical", "OLI + TIRS (30 m optical, 100 m thermal)", "ET (thermal), surface water, snow, irrigation", "https://landsat.gsfc.nasa.gov/satellites/landsat-8/"],
    [49260, "l9", "Landsat 9", "NASA/USGS", "optical", "OLI-2 + TIRS-2", "ET (thermal), surface water, snow, irrigation", "https://landsat.gsfc.nasa.gov/satellites/landsat-9/"],
    [40697, "s2a", "Sentinel-2A", "ESA", "optical", "MSI 13-band multispectral (10–60 m)", "Surface water, snow, crop water use, quality", "https://sentinels.copernicus.eu/copernicus/sentinel-2"],
    [42063, "s2b", "Sentinel-2B", "ESA", "optical", "MSI 13-band multispectral (10–60 m)", "Surface water, snow, crop water use, quality", "https://sentinels.copernicus.eu/copernicus/sentinel-2"],
    [60989, "s2c", "Sentinel-2C", "ESA", "optical", "MSI 13-band multispectral (10–60 m)", "Surface water, snow, crop water use, quality", "https://sentinels.copernicus.eu/copernicus/sentinel-2"],
    [41335, "s3a", "Sentinel-3A", "ESA/EUMETSAT", "optical", "OLCI (1270 km, west-tilted) + SLSTR + SRAL altimeter", "River/reservoir levels (SRAL), quality, LST", "https://sentinels.copernicus.eu/copernicus/sentinel-3"],
    [43437, "s3b", "Sentinel-3B", "ESA/EUMETSAT", "optical", "OLCI (1270 km, west-tilted) + SLSTR + SRAL altimeter", "River/reservoir levels (SRAL), quality, LST", "https://sentinels.copernicus.eu/copernicus/sentinel-3"],
    [43065, "gcomc", "GCOM-C", "JAXA", "optical", "SGLI 19-ch optical radiometer", "Snow properties, vegetation, inland water, LST", "https://global.jaxa.jp/projects/sat/gcom_c/"],
    [39574, "gpm", "GPM Core", "NASA/JAXA", "water", "GMI radiometer (885 km) + DPR radar (245 km)", "Precipitation rate and type (calibrates IMERG)", "https://gpm.nasa.gov/"],
    [54754, "swot", "SWOT", "NASA/CNES", "water", "KaRIn interferometric altimeter (2×50 km)", "River/lake levels, storage, discharge", "https://swot.jpl.nasa.gov/"],
    [43476, "gracefo1", "GRACE-FO 1", "NASA/GFZ", "water", "Twin-sat microwave + laser ranging", "Total water storage / groundwater (monthly)", "https://gracefo.jpl.nasa.gov/", "GRACE-FO"],
    [43477, "gracefo2", "GRACE-FO 2", "NASA/GFZ", "water", "Twin-sat microwave + laser ranging", "Total water storage / groundwater (monthly)", "https://gracefo.jpl.nasa.gov/", "GRACE-FO"],
    [43613, "icesat2", "ICESat-2", "NASA", "water", "ATLAS photon-counting laser altimeter (6 beams)", "Snow depth, lake levels (ATL13), cryosphere", "https://science.nasa.gov/mission/icesat-2/"],
    [41887, "cygfm01", "CYGNSS FM01", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41886, "cygfm02", "CYGNSS FM02", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41891, "cygfm03", "CYGNSS FM03", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41885, "cygfm04", "CYGNSS FM04", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41884, "cygfm05", "CYGNSS FM05", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41890, "cygfm07", "CYGNSS FM07", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"],
    [41888, "cygfm08", "CYGNSS FM08", "NASA/UMich", "soil", "DDMI GNSS-R (reflected GPS L1)", "Soil moisture, inundation/wetland extent (sub-daily)", "https://science.nasa.gov/mission/cygnss/", "CYGNSS"]
    // roster:end
  ];

  /* Whose name is placed first when names would run into each other, and the order the arrow keys step in.
     The rest follow in the order of the list above. */
  var PRIORITY = ["smap", "nisar", "s1a", "s1c", "s1d", "l8", "l9", "s2a", "s2b", "s2c", "gpm", "swot", "gracefo1", "gracefo2"];

  /* What each instrument sees, painted on the ground behind it as it flies: the shape of its swath and a
     made-up field in the colours of what it measures. The fields are illustrative, not data: noise shaped
     by latitude, season, deserts, coasts and the Sun, the same field for every satellite that measures the
     same thing. Distances in km; across the track, + is to the right of the direction of flight.

       band   [near, far] across the track        two    the band and its mirror on the left (ASCAT, SWOT)
       west   the band is turned to the west       beams  single lines across the track (ICESat-2)
       spec   specular points of reflected GPS     none   nothing on the ground (the second GRACE-FO)
       inner  a narrower band inside (GPM's radar) day    only where the Sun is up (reflected sunlight)
       land, sea   what is shown there (a field below, or a choice of two); nothing: only the swath's outline
       look   what is drawn at the satellite: cone, arc, hex, line, whisk, side, fan, gpm, swot, twin, laser, spec
       show   the fields the card's legend names */
  var FIELDS = {
    sm: { name: "Soil moisture", lo: "dry", hi: "wet", a: 0.88, stops: ["#7a4a1c", "#b98a4e", "#e2d3a0", "#86c9b4", "#2f93c0", "#2353a6"] },
    frozen: { name: "Frozen ground", lo: "", hi: "", a: 0.8, stops: ["#bcd9f5", "#eaf5ff"] },
    sss: { name: "Sea surface salinity", lo: "32 psu", hi: "38 psu", a: 0.85, stops: ["#2b3990", "#2f7fc1", "#5fc3c8", "#e7e58f", "#f39a46", "#c7362f"] },
    ascat: { name: "Soil moisture (degree of saturation)", lo: "0%", hi: "100%", a: 0.86, stops: ["#f4e9a0", "#b6e3a1", "#4fb7b3", "#2b7bba", "#283593"] },
    wind: { name: "Ocean wind speed", lo: "calm", hi: "gale", a: 0.78, stops: ["#3b2c7e", "#5e3c99", "#8d4fb3", "#c873c4", "#f2b5e1"] },
    tpw: { name: "Water vapour", lo: "dry air", hi: "moist air", a: 0.8, stops: ["#46327e", "#365c8d", "#277f8e", "#1fa187", "#4ac16d", "#a0da39", "#fde725"] },
    sst: { name: "Sea surface temperature", lo: "cold", hi: "warm", a: 0.8, stops: ["#313695", "#4575b4", "#74add1", "#e0f3f8", "#fee090", "#f46d43", "#a50026"] },
    snow: { name: "Snow", lo: "thin", hi: "deep", a: 0.9, stops: ["#9fc2e6", "#d6e9fb", "#ffffff"] },
    sar: { name: "Radar backscatter (flooded: dark blue)", lo: "low", hi: "high", a: 0.92, stops: [[0, "#0a2552"], [0.07, "#123a78"], [0.08, "#2e2e2e"], [1, "#f4f4f4"]] },
    sarsea: { name: "", lo: "", hi: "", a: 0.75, stops: ["#151d26", "#3a4652", "#77828e"] },
    nisar: { name: "L-band radar (HH, HV, HH/HV)", lo: "forest", hi: "fields", a: 0.92, stops: ["#1d6b33", "#38b056", "#a2d880", "#e8b3dc", "#c843b0", "#6e1f86"] },
    xsar: { name: "X-band radar backscatter", lo: "low", hi: "high", a: 0.92, stops: [[0, "#081a3a"], [0.07, "#0e2c5c"], [0.08, "#161616"], [1, "#ffffff"]] },
    et: { name: "Evapotranspiration", lo: "low", hi: "high", a: 0.86, stops: ["#efe2a8", "#c8e08a", "#78c25a", "#2f9e55", "#0f7462", "#0b4f6c"] },
    lst: { name: "Land surface temperature", lo: "cold", hi: "hot", a: 0.86, stops: ["#3a2a7a", "#6a1f84", "#b02f7a", "#e3555a", "#f88f3e", "#fcd25a", "#fff6c0"] },
    fcc: { name: "False colour (vegetation red)", lo: "water", hi: "dense crops", a: 0.92, stops: [[0, "#0d1b2a"], [0.1, "#173352"], [0.11, "#6f97a6"], [0.35, "#a8a49a"], [0.6, "#b5675f"], [0.85, "#d42a24"], [1, "#ff4a3a"]] },
    ndvi: { name: "Vegetation (NDVI)", lo: "bare", hi: "green", a: 0.9, stops: ["#8c5a2b", "#c9a465", "#ece0a8", "#a9d46b", "#4fae4a", "#13702f"] },
    chl: { name: "Chlorophyll (ocean colour)", lo: "clear", hi: "blooming", a: 0.86, stops: ["#2a1a6e", "#2457b3", "#1e9bb0", "#47c48b", "#b8e04a", "#f2c12e", "#e8622c"] },
    sgli: { name: "Leaf area", lo: "sparse", hi: "dense", a: 0.86, stops: ["#5b5a2c", "#6f8f34", "#8fbf45", "#bde46a", "#e6f7a8"] },
    rain: { name: "Rain rate", lo: "light", hi: "heavy", a: 0.94, stops: ["#7fd3f7", "#2a9df4", "#2fbf4a", "#f7e03b", "#f79a2e", "#e8352b", "#c2187a"] },
    ssha: { name: "Sea surface height", lo: "low", hi: "high", a: 0.9, stops: ["#1b3f8c", "#3f7cc4", "#9cc6e6", "#f2f2f2", "#f2a98a", "#d9583b", "#9e1b1b"] },
    tws: { name: "Water storage change", lo: "losing", hi: "gaining", a: 0.62, stops: ["#8c510a", "#d8b365", "#f2ecd6", "#7cc8bd", "#01665e"] },
    elev: { name: "Surface height (photons)", lo: "low", hi: "high", a: 0.95, stops: ["#1f7a3d", "#3fd36b", "#9dffb3", "#effff2"] },
    cygland: { name: "Reflected signal over land", lo: "dry", hi: "wet", a: 0.95, stops: ["#2b4aa0", "#2f8fd8", "#5fd0b0", "#e8e35a", "#f58a2e", "#e0362e"] },
    cygwind: { name: "Ocean wind speed", lo: "calm", hi: "storm", a: 0.9, stops: ["#d6ecff", "#a5cdf2", "#6fa3e3", "#4e6fd0", "#5b3fb3"] }
  };

  var SAR1 = { band: [240, 490], look: "side", land: "sar", sea: "sarsea", desc: "250 km, right of the track", show: ["sar"] };
  var ASCAT = { band: [336, 886], two: true, look: "fan", land: "ascat", sea: "wind", desc: "2 × 550 km, six fan beams", show: ["ascat", "wind"] };
  var LANDSAT = { band: [-92, 92], look: "line", land: "fcc", day: true, desc: "185 km, by day", show: ["fcc"] };
  var S2 = { band: [-145, 145], look: "line", land: "ndvi", day: true, desc: "290 km, by day", show: ["ndvi"] };
  var S3 = { band: [-270, 1000], west: true, look: "line", sea: "chl", day: true, desc: "1270 km, tilted west; by day", show: ["chl"] };
  var CYG = { spec: 4, look: "spec", land: "cygland", sea: "cygwind", desc: "4 specular points, 25 km tracks", show: ["cygland", "cygwind"], ddm: true };
  var GRACE = { band: [-300, 300], look: "twin", land: "tws", desc: "None: the twins, 220 km apart, sense mass", show: ["tws"] };
  var SPEC = {
    smap: { band: [-500, 500], look: "cone", r: 500, land: "smft", desc: "1000 km, conical scan", show: ["sm", "frozen"] },
    smos: { band: [-500, 500], look: "hex", r: 520, land: "sm", sea: "sss", desc: "About 1000 km, hexagonal view", show: ["sm", "sss"] },
    metopb: ASCAT, metopc: ASCAT,
    gcomw1: { band: [-725, 725], look: "arc", r: 725, land: "sm", sea: "tpw", desc: "1450 km, conical scan", show: ["sm", "tpw"] },
    gosatgw: { band: [-765, 765], look: "arc", r: 765, land: "smsnow", sea: "sst", desc: "1530 km, conical scan", show: ["sst", "snow"] },
    s1a: SAR1, s1c: SAR1, s1d: SAR1,
    nisar: { band: [-460, -218], look: "side", land: "nisar", sea: "sarsea", desc: "242 km, left of the track", show: ["nisar"] },
    k5: { band: [250, 350], look: "side", land: "xsar", sea: "sarsea", desc: "100 km, right of the track", show: ["xsar"] },
    terra: { band: [-1165, 1165], look: "whisk", land: "et", day: true, desc: "2330 km, scanning mirror; by day", show: ["et"] },
    aqua: { band: [-1165, 1165], look: "whisk", land: "lstsnow", desc: "2330 km, scanning mirror", show: ["lst", "snow"] },
    l8: LANDSAT, l9: LANDSAT, s2a: S2, s2b: S2, s2c: S2, s3a: S3, s3b: S3,
    gcomc: { band: [-575, 575], look: "line", land: "sglisnow", day: true, desc: "1150 km, by day", show: ["sgli", "snow"] },
    gpm: { band: [-442, 442], inner: [-122, 122], look: "gpm", r: 442, land: "rain", sea: "rain", desc: "885 km; radar 245 km inside", show: ["rain"] },
    swot: { band: [10, 60], two: true, look: "swot", sea: "ssha", desc: "2 × 50 km, 20 km gap", show: ["ssha"] },
    gracefo1: GRACE,
    gracefo2: { none: true, look: "none", desc: GRACE.desc, show: ["tws"] },
    icesat2: { beams: [-46, -40, -3, 3, 40, 46], look: "laser", land: "elev", sea: "elev", desc: "6 beams in 3 pairs (drawn wider)", show: ["elev"] },
    cygfm01: CYG, cygfm02: CYG, cygfm03: CYG, cygfm04: CYG, cygfm05: CYG, cygfm07: CYG, cygfm08: CYG
  };

  /* Where the browser asks when the file is old: two group files, and one request each for the satellites
     that are in neither (the dashboard's plan). CelesTrak renews its files about every two hours. */
  var CELESTRAK = "https://celestrak.org/NORAD/elements/gp.php?";
  var CELESTRAK_GROUPS = ["resource", "weather"];
  var CELESTRAK_CATNR = [62261, 66315, 65053, 43476, 43477, 38337, 43065, 64694];

  var HOME = [-127.5, -30];                       // d3 rotation: Korea a little above the centre
  var SITE = { lat: 35.015, lon: 126.551, name: "Core Validation Site" };
  var MINT = "#75fb92";
  var STEP = 30000;                               // ms of flight between two points worked out with SGP4
  var SPAN = 12 * 60000;                          // ms of path shown behind a satellite, and ahead of it
  var FAST = 60;                                  // the fast clock: one minute a second
  var STALE = 7 * 864e5, KEEP = 864e5, MEMORY = "hydroorbit:tle:v1";
  var WIDE = 560;                                 // px: from this width the clock and the card lie over the square
  var DEG = Math.PI / 180, TAU = Math.PI * 2;
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  var CSS = [
    ".ho-root{position:relative;isolation:isolate;display:flex;flex-direction:column;width:100%;min-width:0;margin:0;padding:0;color:#fff;font:500 14px/1.4 Satoshi,sans-serif;letter-spacing:0;text-align:left;text-transform:none;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;-webkit-tap-highlight-color:transparent}",
    ".ho-root *,.ho-root *::before,.ho-root *::after{box-sizing:border-box}",
    ".ho-root [hidden]{display:none!important}",
    ".ho-root button{-webkit-appearance:none;appearance:none;margin:0;padding:0;border:0;border-radius:0;background:none;box-shadow:none;color:inherit;font:inherit;letter-spacing:inherit;text-transform:none;text-decoration:none;line-height:1;min-width:0;min-height:0;cursor:pointer}",
    ".ho-root button:focus,.ho-root a:focus,.ho-root .ho-globe:focus{outline:none}",
    ".ho-root button:focus-visible,.ho-root a:focus-visible{outline:3px solid #75fb92;outline-offset:2px}",
    ".ho-root .ho-globe:focus-visible{outline:3px solid #75fb92;outline-offset:-11px;outline-offset:calc(3px - var(--ho-gap,14px))}",

    ".ho-root .ho-top{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px 12px;margin:0 0 10px}",
    ".ho-root.ho-wide .ho-top{position:absolute;z-index:3;top:0;left:0;right:0;margin:0;pointer-events:none}",
    ".ho-root.ho-wide .ho-top>*{pointer-events:auto}",
    ".ho-root .ho-clock{display:flex;align-items:center;gap:8px;min-height:34px;margin:0;font:500 13px/1 Satoshi,sans-serif;color:rgba(255,255,255,.82);font-variant-numeric:tabular-nums;white-space:nowrap}",
    ".ho-root .ho-speed{display:inline-block;padding:4px 7px;border-radius:999px;background:rgba(117,251,146,.14);color:#75fb92;font:700 11.5px/1 Satoshi,sans-serif;letter-spacing:.02em}",
    ".ho-root.ho-narrow .ho-speed{display:none}",
    ".ho-root .ho-switch{display:inline-flex;flex:none;padding:3px;border-radius:999px;background:rgba(255,255,255,.08)}",
    ".ho-root .ho-seg{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 13px;border-radius:999px;font:500 13px/1 Satoshi,sans-serif;color:rgba(255,255,255,.72);transition:background-color .15s,color .15s}",
    "@media (hover:hover){.ho-root .ho-seg:hover{color:#fff}}",
    ".ho-root .ho-seg[aria-pressed=\"true\"]{background:rgba(255,255,255,.18);color:#fff}",
    ".ho-root .ho-pip{width:6px;height:6px;border-radius:50%;background:rgba(255,255,255,.4);transition:background-color .15s}",
    ".ho-root .ho-seg[aria-pressed=\"true\"] .ho-pip{background:#75fb92}",

    ".ho-root .ho-stage{position:relative;flex:none;width:100%;-webkit-user-select:none;user-select:none}",
    ".ho-root .ho-stage::before{content:\"\";display:block;padding-top:100%}",
    ".ho-root .ho-globe{position:absolute;top:0;left:0;width:100%;height:100%;border-radius:50%;cursor:grab;touch-action:pan-y}",
    ".ho-root .ho-canvas{position:absolute;top:0;left:0;display:block;max-width:none;max-height:none;margin:0;padding:0;border:0;touch-action:pan-y}",
    ".ho-root .ho-recentre{position:absolute;z-index:3;left:0;top:0;display:inline-flex;align-items:center;gap:7px;height:34px;padding:0 14px 0 11px;border-radius:999px;background:rgba(16,32,32,.88);box-shadow:inset 0 0 0 1px rgba(255,255,255,.16);color:rgba(255,255,255,.92);font:500 13px/1 Satoshi,sans-serif;transition:background-color .15s}",
    ".ho-root.ho-wide .ho-recentre{top:40px}",
    "@media (hover:hover){.ho-root .ho-recentre:hover{background:rgba(38,64,61,.96)}}",
    ".ho-root .ho-ico{flex:none;display:block;fill:none;stroke:currentColor;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round}",

    ".ho-root .ho-chips{display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin:14px 0 0;padding:0}",
    ".ho-root .ho-chip{display:inline-flex;align-items:center;gap:8px;height:34px;padding:0 14px 0 12px;border-radius:999px;background:rgba(255,255,255,.08);box-shadow:inset 0 0 0 1px rgba(255,255,255,0);color:rgba(255,255,255,.9);font:500 13.5px/1 Satoshi,sans-serif;white-space:nowrap;transition:background-color .15s,color .15s,box-shadow .15s}",
    ".ho-root .ho-chip[aria-pressed=\"true\"]{background:rgba(255,255,255,.14);box-shadow:inset 0 0 0 1px rgba(255,255,255,.14)}",
    ".ho-root .ho-chip[aria-pressed=\"false\"]{color:rgba(255,255,255,.56)}",
    "@media (hover:hover){.ho-root .ho-chip:hover{background:rgba(255,255,255,.12)}.ho-root .ho-chip[aria-pressed=\"true\"]:hover{background:rgba(255,255,255,.19)}}",
    ".ho-root .ho-dot{flex:none;display:block;width:9px;height:9px;border-radius:50%;transition:opacity .15s}",
    ".ho-root .ho-chip[aria-pressed=\"false\"] .ho-dot{opacity:.35}",

    ".ho-root .ho-card{margin:0;padding:0}",
    ".ho-root.ho-wide .ho-card{position:absolute;z-index:4;right:0;bottom:0;width:276px;width:min(276px,44%);pointer-events:none}",
    ".ho-root.ho-wide .ho-card.ho-left{right:auto;left:0}",
    ".ho-root.ho-wide .ho-card.ho-pinned{pointer-events:auto}",
    ".ho-root.ho-narrow .ho-box{margin:12px 0 0}",
    ".ho-root .ho-box{position:relative;padding:14px 16px 15px;border-radius:14px;background:rgba(16,32,32,.92);border:1px solid rgba(255,255,255,.14);box-shadow:0 14px 34px rgba(0,0,0,.32);color:#fff;font:400 14px/1.4 Satoshi,sans-serif;animation:ho-in .16s ease-out}",
    "@keyframes ho-in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}",
    ".ho-root .ho-fam{display:flex;align-items:center;gap:7px;margin:0 30px 7px 0;font:500 12.5px/1.2 Satoshi,sans-serif;color:rgba(255,255,255,.74)}",
    ".ho-root .ho-name{margin:0;font:700 19px/1.2 \"Plus Jakarta\",sans-serif;letter-spacing:-.01em;color:#fff}",
    ".ho-root .ho-agency{margin:2px 0 0;font:400 13px/1.3 Satoshi,sans-serif;color:rgba(255,255,255,.64)}",
    ".ho-root .ho-facts{display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 12px;margin:11px 0 0;padding:11px 0 0;border-top:1px solid rgba(255,255,255,.12)}",
    ".ho-root .ho-facts dt{margin:0;padding:1px 0 0;font:500 12.5px/1.4 Satoshi,sans-serif;color:rgba(255,255,255,.6);white-space:nowrap}",
    ".ho-root .ho-facts dd{margin:0;padding:0;font:400 14px/1.4 Satoshi,sans-serif;color:rgba(255,255,255,.95);font-variant-numeric:tabular-nums}",
    ".ho-root .ho-far{margin:9px 0 0;font:400 13px/1.35 Satoshi,sans-serif;color:rgba(255,255,255,.64)}",
    ".ho-root .ho-link{display:inline-flex;align-items:center;gap:6px;margin:12px 0 0;border-radius:4px;font:700 14px/1.2 Satoshi,sans-serif;color:#75fb92;text-decoration:none}",
    "@media (hover:hover){.ho-root .ho-link:hover{text-decoration:underline}}",
    ".ho-root .ho-x{position:absolute;top:8px;right:8px;display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:50%;color:rgba(255,255,255,.72);transition:background-color .15s,color .15s}",
    "@media (hover:hover){.ho-root .ho-x:hover{background:rgba(255,255,255,.12);color:#fff}}",

    ".ho-root .ho-legend{margin:11px 0 0;padding:10px 0 0;border-top:1px solid rgba(255,255,255,.12)}",
    ".ho-root .ho-lgh{margin:0 0 7px;padding:0;font:500 12px/1.3 Satoshi,sans-serif;color:rgba(255,255,255,.6)}",
    ".ho-root .ho-lg{display:grid;grid-template-columns:auto minmax(0,1fr) auto;align-items:center;gap:3px 7px;margin:0 0 7px}",
    ".ho-root .ho-lg:last-child{margin-bottom:0}",
    ".ho-root .ho-lgname{grid-column:1/-1;margin:0;font:500 13px/1.3 Satoshi,sans-serif;color:rgba(255,255,255,.92)}",
    ".ho-root .ho-end{font:400 11.5px/1.2 Satoshi,sans-serif;color:rgba(255,255,255,.6);white-space:nowrap}",
    ".ho-root .ho-bar{display:block;height:7px;border-radius:4px}",
    ".ho-root .ho-plain{grid-template-columns:auto 44px}",
    ".ho-root .ho-plain .ho-lgname{grid-column:auto}",
    ".ho-root .ho-ddms{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;margin:0 0 10px}",
    ".ho-root .ho-ddm{display:block;width:100%;height:auto;max-width:none;margin:0;border-radius:4px;background:#000;image-rendering:auto}",
    ".ho-root .ho-source{margin:12px 0 0;padding:0;max-width:none;font:400 12.5px/1.45 Satoshi,sans-serif;color:rgba(255,255,255,.56);text-align:center}",
    "@media (prefers-reduced-motion:reduce){.ho-root .ho-box{animation:none}.ho-root *{transition:none!important}}"
  ].join("\n");

  /* ---------- small things ---------- */

  function h(tag, cls, text) {
    var n = D.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function icon(size, d) {
    var ns = "http://www.w3.org/2000/svg", s = D.createElementNS(ns, "svg"), p = D.createElementNS(ns, "path");
    s.setAttribute("class", "ho-ico");
    s.setAttribute("width", size); s.setAttribute("height", size);
    s.setAttribute("viewBox", "0 0 14 14");
    s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false");
    p.setAttribute("d", d);
    s.appendChild(p);
    return s;
  }

  function rgbOf(hex) {
    return parseInt(hex.slice(1, 3), 16) + "," + parseInt(hex.slice(3, 5), 16) + "," + parseInt(hex.slice(5, 7), 16);
  }
  function rgba(rgb, a) {
    return "rgba(" + rgb + "," + (a <= 0 ? 0 : a >= 1 ? 1 : Math.round(a * 1000) / 1000) + ")";
  }
  function wrap180(x) { return ((x + 180) % 360 + 360) % 360 - 180; }
  function clamp(x, a, b) { return x < a ? a : x > b ? b : x; }
  function ease(p) { return p <= 0 ? 0 : p >= 1 ? 1 : p * p * (3 - 2 * p); }
  function pad2(n) { return (n < 10 ? "0" : "") + n; }
  function sq(x) { return x * x; }
  function sstep(a, b, x) { x = clamp((x - a) / (b - a), 0, 1); return x * x * (3 - 2 * x); }
  function frac(x) { return x - Math.floor(x); }

  /* Noise for the illustrative fields: value noise on the unit sphere (no seam at the date line), a few
     octaves of it, and a hash for speckle. */
  function hsh(i, j, k, s) {
    var n = Math.imul(i, 73856093) ^ Math.imul(j, 19349663) ^ Math.imul(k, 83492791) ^ Math.imul(s, 1103515245);
    n = Math.imul(n ^ (n >>> 15), -2048144777);
    n = Math.imul(n ^ (n >>> 13), -1028477379);
    n ^= n >>> 16;
    return (n >>> 0) / 4294967295;
  }
  function vnoise(x, y, z, s) {
    var i = Math.floor(x), j = Math.floor(y), k = Math.floor(z);
    var u = x - i, v = y - j, w = z - k;
    u = u * u * (3 - 2 * u); v = v * v * (3 - 2 * v); w = w * w * (3 - 2 * w);
    var a = hsh(i, j, k, s), b = hsh(i + 1, j, k, s), c = hsh(i, j + 1, k, s), d = hsh(i + 1, j + 1, k, s);
    var e = hsh(i, j, k + 1, s), f = hsh(i + 1, j, k + 1, s), g = hsh(i, j + 1, k + 1, s), q = hsh(i + 1, j + 1, k + 1, s);
    a += (b - a) * u; c += (d - c) * u; e += (f - e) * u; g += (q - g) * u;
    a += (c - a) * v; e += (g - e) * v;
    return a + (e - a) * w;
  }
  function fbm(x, y, z, f, s, n) {               // 0..1, .5 on average; spread out again with stretch()
    var sum = 0, amp = 1, norm = 0, o;
    for (o = 0; o < n; o++) {
      sum += amp * vnoise(x * f + 17.3 * o, y * f - 9.1 * o, z * f + 5.7 * o, s + o);
      norm += amp; amp *= 0.5; f *= 2.07;
    }
    return sum / norm;
  }
  function stretch(v, k) { return clamp(0.5 + (v - 0.5) * k, 0, 1); }
  function inBox(la, lo, b) {                    // [lat0, lat1, lon0, lon1, weight], soft at the edges
    return sstep(b[0] - 3, b[0] + 3, la) * (1 - sstep(b[1] - 3, b[1] + 3, la)) *
      sstep(b[2] - 3, b[2] + 3, lo) * (1 - sstep(b[3] - 3, b[3] + 3, lo)) * b[4];
  }
  function anyBox(la, lo, list) {
    var m = 0, i;
    for (i = 0; i < list.length; i++) m = Math.max(m, inBox(la, lo, list[i]));
    return m;
  }
  var DESERTS = [[15, 33, -17, 35, 1], [13, 32, 35, 60, 1], [24, 38, 55, 75, 0.6], [36, 48, 55, 112, 0.6],
    [-32, -18, 115, 142, 0.85], [24, 38, -118, -103, 0.7], [-28, -17, 12, 25, 0.6], [-30, -18, -72, -67, 0.6]];
  var HIGHLANDS = [[27, 38, 76, 103, 1], [44, 48, 5, 16, 0.8], [36, 58, -125, -104, 0.8], [-55, -28, -74, -67, 0.8]];
  var EDDIES = [[25, 42, 122, 165, 1], [28, 46, -80, -40, 1], [-62, -38, -180, 180, 0.8], [-45, -33, 15, 40, 1]];

  /* A colour ramp of 256 steps from stops ("#rrggbb", or [place 0..1, "#rrggbb"]), as 0xBBGGRR for ImageData. */
  function ramp(stops) {
    var pts = stops.map(function (s, i) {
      return typeof s === "string" ? [i / (stops.length - 1), s] : s;
    }), out = new Uint32Array(256), i, k, p, a, b, f;
    for (i = 0; i < 256; i++) {
      p = i / 255;
      for (k = 0; k < pts.length - 2 && p > pts[k + 1][0]; k++) { /* find the stretch */ }
      a = pts[k]; b = pts[k + 1];
      f = clamp((p - a[0]) / Math.max(b[0] - a[0], 1e-6), 0, 1);
      var ca = parseInt(a[1].slice(1), 16), cb = parseInt(b[1].slice(1), 16);
      var r = Math.round(((ca >> 16) & 255) * (1 - f) + ((cb >> 16) & 255) * f);
      var g = Math.round(((ca >> 8) & 255) * (1 - f) + ((cb >> 8) & 255) * f);
      var bl = Math.round((ca & 255) * (1 - f) + (cb & 255) * f);
      out[i] = (bl << 16) | (g << 8) | r;
    }
    return out;
  }
  function gradientCss(stops) {
    return "linear-gradient(90deg," + stops.map(function (s, i) {
      return typeof s === "string" ? s + " " + Math.round(i / (stops.length - 1) * 100) + "%" : s[1] + " " + Math.round(s[0] * 100) + "%";
    }).join(",") + ")";
  }
  function dateText(ms) {
    var d = new Date(ms);
    return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }
  function perf() { return W.performance && performance.now ? performance.now() : Date.now(); }

  function hasLib() {
    return !!(W.d3 && typeof W.d3.geoOrthographic === "function" && typeof W.d3.geoPath === "function" &&
      typeof W.d3.geoCircle === "function" && typeof W.d3.geoGraticule === "function" &&
      W.satellite && typeof W.satellite.twoline2satrec === "function" &&
      typeof W.satellite.propagate === "function" && typeof W.satellite.eciToGeodetic === "function");
  }

  var libPromise = null;
  function loadLib(base) {
    if (hasLib()) return Promise.resolve();
    if (libPromise) return libPromise;
    var p = new Promise(function (resolve, reject) {
      var s = D.createElement("script");
      s.src = base + LIB;
      s.async = true;
      s.onload = function () { if (hasLib()) resolve(); else reject(new Error("orbit: library")); };
      s.onerror = function () {
        if (s.parentNode) s.parentNode.removeChild(s);
        reject(new Error("orbit: library"));
      };
      (D.head || D.documentElement).appendChild(s);
    });
    libPromise = p;
    p.then(null, function () { if (libPromise === p) libPromise = null; });   // a later mount may try again
    return p;
  }

  /* fetch with a time limit; `as` is "json" or "text". Rejects on anything but a 2xx answer. */
  function get(url, ms, as, hold) {
    return new Promise(function (resolve, reject) {
      var ctl = typeof AbortController === "function" ? new AbortController() : null;
      var timer = setTimeout(function () {
        if (ctl) ctl.abort();
        reject(new Error("orbit: timeout"));
      }, ms);
      if (hold && ctl) hold.push(ctl);
      fetch(url, ctl ? { signal: ctl.signal, credentials: "omit" } : { credentials: "omit" }).then(function (r) {
        if (!r.ok) throw new Error("orbit: " + r.status);
        return as === "json" ? r.json() : r.text();
      }).then(function (d) { clearTimeout(timer); resolve(d); }, function (e) { clearTimeout(timer); reject(e); });
    });
  }

  function folder(base) {
    if (typeof base !== "string" || !base) return "";
    try { base = new URL(base, D.baseURI).href; } catch (e) { /* as given */ }
    return base.replace(/[?#].*$/, "").replace(/\/?$/, "/");
  }

  /* ---------- mount ---------- */

  var mounts = typeof WeakMap === "function" ? new WeakMap() : null;
  var instances = [];

  function mount(el, opts) {
    if (!el || el.nodeType !== 1 || !mounts) return Promise.resolve(null);
    var had = mounts.get(el);
    if (had) return had;
    var p = new Promise(function (resolve) {
      var off = function () {
        mounts.delete(el);
        try { el.setAttribute("data-orbit", "off"); } catch (e) { /* nothing to do */ }
        resolve(null);
      };
      try {
        var base = folder(opts && opts.base) || SELF_BASE;
        var probe = D.createElement("canvas");
        if (!base || !probe.getContext || !probe.getContext("2d") || typeof fetch !== "function" ||
            typeof requestAnimationFrame !== "function") { off(); return; }
        Promise.all([loadLib(base), get(base + LAND, 20000, "json"), get(base + TLE, 20000, "json")]).then(function (got) {
          resolve(create(el, got[1], got[2]));
        }).then(null, off);
      } catch (e) { off(); }
    });
    mounts.set(el, p);
    return p;
  }

  /* ---------- one globe ---------- */

  function create(el, land, doc) {
    var d3 = W.d3, sat = W.satellite;
    if (!land || (land.type !== "MultiPolygon" && land.type !== "Polygon") || !Array.isArray(land.coordinates)) throw new Error("orbit: land");
    if (!doc || !doc.tle || typeof doc.tle !== "object") throw new Error("orbit: elements");

    var reduced = !!(W.matchMedia && W.matchMedia("(prefers-reduced-motion: reduce)").matches);
    var dead = false, running = false, onScreen = true, raf = 0, calm = 0, freshTimer = 0, dirty = false;
    var holds = [];                                // AbortControllers of the requests to CelesTrak

    /* ----- the satellites ----- */

    var fams = {}, famList = FAMILIES.map(function (f) {
      return (fams[f.id] = { id: f.id, name: f.name, color: f.color, rgb: rgbOf(f.color), on: true, a: 1, chip: null });
    });
    var sats = ROSTER.map(function (r, i) {
      var p = PRIORITY.indexOf(r[1]);
      return { norad: r[0], key: r[1], name: r[2], agency: r[3], fam: fams[r[4]], inst: r[5], use: r[6], url: r[7],
               tag: r[8] || r[2], pri: p < 0 ? PRIORITY.length + i : p,
               rec: null, epoch: 0, grid: null, ok: false, vis: false,
               ex: 0, ey: 0, ez: 0, x: 0, y: 0, depth: 0, hx: 0, hy: 0, hv: false,
               la: 0, lt: 0, side: 0 };
    });
    var byPri = sats.slice().sort(function (a, b) { return a.pri - b.pri; });
    var byKey = {};
    sats.forEach(function (s) { byKey[s.key] = s; });

    /* Sub-satellite point (geodetic latitude and longitude in degrees, height in km) at a time in ms:
       the same three calls as the dashboard's OrbitEngine.geoAt. null when SGP4 gives no position. */
    function geoAt(rec, ms) {
      var date = new Date(ms), pv = sat.propagate(rec, date);
      if (!pv || !pv.position || typeof pv.position !== "object") return null;
      var gd = sat.eciToGeodetic(pv.position, sat.gstime(date));
      var lat = gd.latitude / DEG, lon = ((gd.longitude / DEG + 540) % 360) - 180, alt = gd.height;
      if (!isFinite(lat) || !isFinite(lon) || !(alt > 80) || !(alt < 5000)) return null;
      return { lat: lat, lon: lon, alt: alt };
    }
    function epochOf(rec) {
      var yr = rec.epochyr < 57 ? 2000 + rec.epochyr : 1900 + rec.epochyr;
      return Date.UTC(yr, 0, 1) + (rec.epochdays - 1) * 864e5;
    }
    /* Two lines to a record for satellite.js, or null: the lines have to be the two of this satellite and
       give a position at their own epoch. The lines go nowhere else. */
    function record(pair, norad) {
      if (!pair || typeof pair[0] !== "string" || typeof pair[1] !== "string") return null;
      var l1 = pair[0].replace(/\s+$/, ""), l2 = pair[1].replace(/\s+$/, "");
      if (l1.length !== 69 || l2.length !== 69 || l1.slice(0, 2) !== "1 " || l2.slice(0, 2) !== "2 ") return null;
      if (parseInt(l1.slice(2, 7), 10) !== norad || parseInt(l2.slice(2, 7), 10) !== norad) return null;
      try {
        var rec = sat.twoline2satrec(l1, l2);
        if (!rec || rec.error) return null;
        var ep = epochOf(rec);
        return isFinite(ep) && geoAt(rec, ep) ? rec : null;
      } catch (e) { return null; }
    }
    /* Takes the elements of `map` ({number: [line 1, line 2]}) for the satellites it has good lines for.
       With newerOnly, a satellite keeps what it has unless the new epoch is later. */
    function take(map, newerOnly) {
      var n = 0;
      sats.forEach(function (s) {
        var rec = record(map[s.norad], s.norad);
        if (!rec) return;
        var ep = epochOf(rec);
        if (newerOnly && s.rec && !(ep > s.epoch)) return;
        s.rec = rec; s.epoch = ep; s.grid = null;
        n++;
      });
      return n;
    }
    function elementsAt() {                        // the median epoch of the elements in use
      var e = [];
      sats.forEach(function (s) { if (s.rec) e.push(s.epoch); });
      e.sort(function (a, b) { return a - b; });
      return e.length ? e[e.length >> 1] : NaN;
    }
    function remembered() {
      try {
        var m = JSON.parse(localStorage.getItem(MEMORY) || "null");
        return m && typeof m.at === "number" && m.tle && typeof m.tle === "object" ? m : null;
      } catch (e) { return null; }
    }

    var fileAt = Date.parse(doc.at), source = "file";
    if (!take(doc.tle, false)) throw new Error("orbit: elements");
    var mem = remembered();
    if (mem && mem.at > (fileAt || 0) && Date.now() - mem.at < KEEP && take(mem.tle, true)) source = "memory";
    var wantFresh = !(Date.now() - fileAt < STALE) && !(mem && Date.now() - mem.at < KEEP);

    /* ----- the page ----- */

    if (!D.getElementById("ho-style")) {
      var st = h("style");
      st.id = "ho-style";
      st.textContent = CSS;
      (D.head || D.documentElement).appendChild(st);
    }

    var root = h("div", "ho-root ho-narrow");
    var top = h("div", "ho-top");
    var clock = h("div", "ho-clock"), clockTime = h("span", "ho-time"), clockSpeed = h("span", "ho-speed", "×" + FAST);
    clockSpeed.title = "The clock runs " + FAST + " times faster than real time: one minute a second";
    clock.appendChild(clockTime); clock.appendChild(clockSpeed);
    var sw = h("div", "ho-switch");
    sw.setAttribute("role", "group"); sw.setAttribute("aria-label", "Speed of the clock");
    var bLive = h("button", "ho-seg"), bFast = h("button", "ho-seg", "×" + FAST);
    bLive.type = bFast.type = "button";
    bLive.appendChild(h("span", "ho-pip")); bLive.appendChild(D.createTextNode("Live"));
    bLive.title = "Real time"; bFast.title = "One minute a second";
    sw.appendChild(bLive); sw.appendChild(bFast);
    top.appendChild(clock); top.appendChild(sw);

    var stage = h("div", "ho-stage");
    var globe = h("div", "ho-globe");
    globe.tabIndex = 0;
    globe.setAttribute("role", "group");
    var cv = h("canvas", "ho-canvas");
    cv.setAttribute("aria-hidden", "true");
    globe.appendChild(cv);
    var bHome = h("button", "ho-recentre");
    bHome.type = "button"; bHome.hidden = true; bHome.title = "Turn the globe back to Korea";
    bHome.appendChild(icon(14, "M7 1.5v2.2M7 10.3v2.2M1.5 7h2.2M10.3 7h2.2M10.2 7a3.2 3.2 0 1 1-6.4 0a3.2 3.2 0 0 1 6.4 0z"));
    bHome.appendChild(D.createTextNode("Recenter"));
    stage.appendChild(globe); stage.appendChild(bHome);

    var card = h("div", "ho-card");
    card.setAttribute("aria-live", "polite");
    var box = h("div", "ho-box");
    box.hidden = true;
    var cFam = h("div", "ho-fam"), cDot = h("span", "ho-dot"), cFamName = h("span");
    cFam.appendChild(cDot); cFam.appendChild(cFamName);
    var cName = h("div", "ho-name"), cAgency = h("div", "ho-agency");
    var facts = h("dl", "ho-facts");
    var cInst = h("dd"), cUse = h("dd"), cAlt = h("dd");
    cAlt.setAttribute("aria-live", "off");
    facts.appendChild(h("dt", "", "Instrument")); facts.appendChild(cInst);
    facts.appendChild(h("dt", "", "Used for")); facts.appendChild(cUse);
    facts.appendChild(h("dt", "", "Altitude now")); facts.appendChild(cAlt);
    var cSw = h("dd");
    facts.appendChild(h("dt", "", "Swath")); facts.appendChild(cSw);
    var cLeg = h("div", "ho-legend"), cDdms = h("div", "ho-ddms"), ddmCv = [], ddmAt = 0, ddmFor = null;
    for (var di = 0; di < 4; di++) {
      var dc = h("canvas", "ho-ddm");
      dc.width = 64; dc.height = 48;
      dc.setAttribute("aria-hidden", "true");
      ddmCv.push(dc); cDdms.appendChild(dc);
    }
    var cFar = h("div", "ho-far", "Out of view: over the far side of the globe.");
    cFar.hidden = true;
    var cLink = h("a", "ho-link");
    cLink.target = "_blank"; cLink.rel = "noopener";
    cLink.appendChild(D.createTextNode("Mission page"));
    cLink.appendChild(icon(12, "M4 10L10 4M5 4h5v5"));
    var cClose = h("button", "ho-x");
    cClose.type = "button"; cClose.hidden = true; cClose.setAttribute("aria-label", "Close");
    cClose.appendChild(icon(12, "M3 3l8 8M11 3l-8 8"));
    box.appendChild(cFam); box.appendChild(cName); box.appendChild(cAgency); box.appendChild(facts); box.appendChild(cLeg);
    box.appendChild(cFar); box.appendChild(cLink); box.appendChild(cClose);
    card.appendChild(box);

    var chips = h("div", "ho-chips");
    chips.setAttribute("role", "group"); chips.setAttribute("aria-label", "Families of satellites: show or hide");
    famList.forEach(function (f) {
      var b = h("button", "ho-chip"), d = h("span", "ho-dot");
      b.type = "button";
      b.setAttribute("aria-pressed", "true");
      d.style.background = f.color;
      b.appendChild(d); b.appendChild(D.createTextNode(f.name));
      b.addEventListener("click", function () { guard(function () { toggleFamily(f); }); });
      f.chip = b;
      chips.appendChild(b);
    });

    var sourceLine = h("p", "ho-source");

    root.appendChild(top); root.appendChild(stage); root.appendChild(chips); root.appendChild(card); root.appendChild(sourceLine);

    function describe() {
      var n = 0;
      sats.forEach(function (s) { if (s.rec) n++; });
      globe.setAttribute("aria-label", "Globe: present positions of " + n +
        " Earth-observing satellites. Use the arrow keys to step through them.");
      var at = elementsAt();
      sourceLine.textContent = "Positions computed in your browser with SGP4 from CelesTrak orbital elements" +
        (isFinite(at) ? " of " + dateText(at) + "." : ".") + " The swaths' colours are illustrative, not data.";
    }

    /* ----- drawing surfaces ----- */

    var ctx = cv.getContext("2d");
    var baseCv = D.createElement("canvas"), bctx = baseCv.getContext("2d");      // sea, graticule, land: redrawn on a turn or a resize
    var ovCv = D.createElement("canvas"), octx = ovCv.getContext("2d");          // night, sunlight, paths, limb: a few times a second
    var seaCv = D.createElement("canvas"), sctx = seaCv.getContext("2d");        // what a turn does not change, painted once for a size:
    var rimCv = D.createElement("canvas"), rctx = rimCv.getContext("2d");        // the sea under the land, and the dark toward the edge over it
    if (!ctx || !bctx || !octx || !sctx || !rctx) throw new Error("orbit: canvas");
    /* precision(0): no resampling between the points. The longest edge of the land is under 6 degrees and the
       limb is followed in steps of 6, so a straight line is never more than 0.4 px from the curve. */
    var proj = d3.geoOrthographic().clipAngle(90).precision(0);
    var bpath = d3.geoPath(proj, bctx), opath = d3.geoPath(proj, octx);
    var graticule = d3.geoGraticule().step([15, 15])();
    var circle = d3.geoCircle().precision(4);

    var size = 0, dpr = 1, wide = false, R = 1, cx = 0, cy = 0, gap = 8;
    var rot = HOME.slice(), away = false, turn = null;
    var m00 = 1, m01 = 0, m02 = 0, m10 = 0, m11 = 1, m20 = 0, m21 = 0, m22 = 1;
    var px = 0, py = 0, pd = 0;                    // where the last projected point fell, and how far toward us it is
    var baseKey = "", ovForce = true, ovWall = -1e9, ovT = 0;

    /* d3's orthographic projection with rotate([a, b]) as a matrix on unit vectors, so that a point costs
       nine multiplications. pd > 0 is the side of the globe that faces us. */
    function setRot(r) {
      rot = r;
      var a = r[0] * DEG, b = r[1] * DEG, ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b);
      m00 = ca * cb; m01 = -sa * cb; m02 = -sb;
      m10 = sa; m11 = ca;
      m20 = ca * sb; m21 = -sa * sb; m22 = cb;
      proj.rotate(r);
    }
    function pj(x, y, z) {
      pd = m00 * x + m01 * y + m02 * z;
      px = cx + R * (m10 * x + m11 * y);
      py = cy - R * (m20 * x + m21 * y + m22 * z);
    }
    function pjv(v, k) { pj(v[k], v[k + 1], v[k + 2]); }

    var siteV = (function () {
      var la = SITE.lat * DEG, lo = SITE.lon * DEG;
      return [Math.cos(la) * Math.cos(lo), Math.cos(la) * Math.sin(lo), Math.sin(la)];
    })();

    /* ----- where a satellite is ----- */

    /* Each satellite keeps points of its ground track on a fixed grid of times (every STEP since 1970), as
       unit vectors. The window slides with the clock, so SGP4 runs for a new point only: twice a second
       per satellite on the fast clock. Between two points the track is all but straight. */
    function point(arr, s, i) {
      var g = geoAt(s.rec, i * STEP);
      if (!g) { arr.push(NaN, NaN, NaN); return; }
      var la = g.lat * DEG, lo = g.lon * DEG, c = Math.cos(la);
      arr.push(c * Math.cos(lo), c * Math.sin(lo), Math.sin(la));
    }
    function ensureGrid(s, t) {
      var i0 = Math.floor((t - SPAN) / STEP) - 1, i1 = Math.ceil((t + SPAN) / STEP) + 1, g = s.grid, i;
      if (!g || i1 < g.i0 || i0 > g.i0 + g.n) g = s.grid = { i0: i0, n: 0, v: [] };
      if (i0 < g.i0) {
        var head = [];
        for (i = i0; i < g.i0; i++) point(head, s, i);
        g.v = head.concat(g.v); g.n += g.i0 - i0; g.i0 = i0;
      }
      for (i = g.i0 + g.n; i <= i1; i++) { point(g.v, s, i); g.n++; }
      var drop = i0 - g.i0 - 24;
      if (drop > 24) { g.v.splice(0, drop * 3); g.i0 += drop; g.n -= drop; }
      var over = g.i0 + g.n - 1 - (i1 + 48);
      if (over > 0) { g.v.length -= over * 3; g.n -= over; }
    }
    function locate(s, t) {
      ensureGrid(s, t);
      var g = s.grid, q = t / STEP, i = Math.floor(q), f = q - i, k = (i - g.i0) * 3, v = g.v;
      var x = v[k] + (v[k + 3] - v[k]) * f, y = v[k + 1] + (v[k + 4] - v[k + 1]) * f, z = v[k + 2] + (v[k + 5] - v[k + 2]) * f;
      var n = Math.sqrt(x * x + y * y + z * z);
      if (!(n > 0)) return false;
      s.ex = x / n; s.ey = y / n; s.ez = z / n;
      return true;
    }

    /* Where the Sun stands overhead (the dashboard's solarSubpoint; good to a third of a degree). */
    function sunAt(ms) {
      var n = ms / 864e5 + 2440587.5 - 2451545.0;
      var L = (280.460 + 0.9856474 * n) % 360, g = ((357.528 + 0.9856003 * n) % 360) * DEG;
      var lam = (L + 1.915 * Math.sin(g) + 0.020 * Math.sin(2 * g)) * DEG, eps = (23.439 - 0.0000004 * n) * DEG;
      var dec = Math.asin(Math.sin(eps) * Math.sin(lam)), ra = Math.atan2(Math.cos(eps) * Math.sin(lam), Math.cos(lam));
      return { lat: dec / DEG, lon: wrap180((ra - sat.gstime(new Date(ms))) / DEG) };
    }

    /* ----- swaths: what each instrument sees, left on the ground behind it ----- */

    /* The ground is a grid of quarter-degree cells (28 km at the equator), like a gridded product. A cell
       keeps when it was seen, by which satellite, which field and its value; it fades over the twelve
       minutes of path drawn behind a satellite. Rows across each track are laid every ROW ms of flight;
       a field is worked out once for a cell and a pass. */
    var GW = 1440, GH = 720, NC = GW * GH, RE = 6371, CELL = TAU * RE / GW;
    var ROW = 2000, FADE = SPAN, FADE_S = FADE / 1000, T0 = Date.now();
    var cT = new Float32Array(NC), cS = new Uint8Array(NC), cD = new Uint8Array(NC), cV = new Uint8Array(NC);
    cT.fill(-1e9);
    var fieldIds = Object.keys(FIELDS), FID = {}, LUT = new Uint32Array((fieldIds.length + 2) * 256), LA = new Float32Array(fieldIds.length + 2);
    fieldIds.forEach(function (id, i) {
      var f = FIELDS[id];
      FID[id] = i + 2;                             // 0: the faint inside of a swath with nothing to show, 1: its edge
      LUT.set(ramp(f.stops), (i + 2) * 256);
      LA[i + 2] = f.a;
    });
    var FADEL = new Float32Array(256);
    for (var fi = 0; fi < 256; fi++) FADEL[fi] = fi < 26 ? 1 : Math.pow(1 - (fi - 26) / 230, 1.35);
    var LM = landMask(land), COAST = coastness(LM);

    function landMask(geo) {
      var m = new Uint8Array(NC), c = D.createElement("canvas");
      c.width = GW; c.height = GH;
      var x = c.getContext("2d");
      if (!x) return m;
      var pr = d3.geoEquirectangular().scale(GW / TAU).translate([GW / 2, GH / 2]).precision(0.2);
      x.beginPath(); d3.geoPath(pr, x)(geo);
      x.fillStyle = "#000"; x.fill();
      var px4 = x.getImageData(0, 0, GW, GH).data, i;
      for (i = 0; i < NC; i++) m[i] = px4[i * 4 + 3] > 127 ? 1 : 0;
      return m;
    }
    /* How much land there is within a few degrees, on a one-degree grid: coasts for the ocean fields. */
    function coastness(lm) {
      var w = 360, hh = 180, a = new Float32Array(w * hh), b = new Float32Array(w * hh), i, j, k, d, s;
      for (j = 0; j < GH; j++) for (i = 0; i < GW; i++) if (lm[j * GW + i]) a[(j >> 2) * w + (i >> 2)] += 1 / 16;
      for (k = 0; k < 2; k++) {
        for (j = 0; j < hh; j++) for (i = 0; i < w; i++) {
          for (s = 0, d = -4; d <= 4; d++) s += a[j * w + (i + d + w) % w];
          b[j * w + i] = s / 9;
        }
        for (j = 0; j < hh; j++) for (i = 0; i < w; i++) {
          for (s = 0, d = -4; d <= 4; d++) s += b[clamp(j + d, 0, hh - 1) * w + i];
          a[j * w + i] = s / 9;
        }
      }
      return a;
    }

    /* the fields: 0..1 at a cell (la, lo in degrees, x y z its unit vector); dec is the Sun's latitude */
    var dec = 0, sunX = 1, sunY = 0, sunZ = 0;
    function wetness(la, lo, x, y, z) {
      var base = stretch(fbm(x, y, z, 7, 11, 4), 2.6);
      var c = 0.3 + 0.38 * Math.exp(-sq(la / 11)) + 0.14 * Math.exp(-sq((Math.abs(la) - 55) / 14)) - 0.42 * anyBox(la, lo, DESERTS);
      return clamp(c + (base - 0.5) * 0.55, 0.02, 1);
    }
    function warmth(la) { return Math.pow(Math.max(Math.cos((la - dec * 0.8) * DEG), 0), 1.4); }
    function snowAt(la, lo, x, y, z, shift) {     // how much snow (0 none); shift > 0 reaches further from the pole (frozen ground)
      var jit = (fbm(x, y, z, 5, 21, 2) - 0.5) * 18, edgeN = 58 + dec * 0.45 - shift + jit, edgeS = -(58 - dec * 0.45) + shift + jit;
      var s = Math.max(sstep(edgeN, edgeN + 6, la), 1 - sstep(edgeS - 6, edgeS, la));
      if (la > 60 && lo > -73 && lo < -12) s = 1;                        // Greenland
      var hi = anyBox(la, lo, HIGHLANDS);
      if (hi > 0) {
        var winter = la > 0 ? clamp(-dec / 15, 0, 1) : clamp(dec / 15, 0, 1);
        s = Math.max(s, hi * winter * sstep(0.45, 0.6, fbm(x, y, z, 14, 23, 3)) + (shift ? hi * winter * 0.3 : 0));
      }
      return s;
    }
    function speck(ci, si, tS) { return hsh(ci, si, Math.floor(tS / 900), 7); }
    function value(f, ci, la, lo, x, y, z, tS, si, inner, day) {
      var v, a, w, n;
      switch (f) {
        case "sm": return wetness(la, lo, x, y, z);
        case "frozen": return 0.4 + 0.6 * hsh(ci, 1, 2, 3);
        case "snow": return clamp(snowAt(la, lo, x, y, z, 0) * (0.6 + 0.4 * fbm(x, y, z, 12, 25, 2)), 0, 1);
        case "sss":
          v = 34.9 + 1.7 * Math.exp(-sq((Math.abs(la) - 24) / 10)) - 0.9 * Math.exp(-sq((la - 7) / 6)) - 1.8 * sstep(42, 68, Math.abs(la)) +
            0.5 * inBox(la, lo, [-40, 60, -75, 15, 1]) + 2.2 * inBox(la, lo, [30, 45, -5, 36, 1]) + 1.2 * inBox(la, lo, [12, 30, 32, 58, 1]) -
            2.6 * inBox(la, lo, [5, 23, 80, 98, 1]) - 1.4 * coastAt(la, lo) + (fbm(x, y, z, 9, 31, 3) - 0.5) * 2.2;
          return clamp((v - 32) / 6, 0, 1);
        case "ascat": return clamp(wetness(la, lo, x, y, z) * 1.15 + (fbm(x, y, z, 20, 33, 2) - 0.5) * 0.3, 0, 1);
        case "wind": case "cygwind":
          v = 0.22 + 0.42 * Math.exp(-sq((Math.abs(la) - 52) / 11)) + 0.18 * Math.exp(-sq((Math.abs(la) - 14) / 7)) +
            (stretch(fbm(x, y, z, 6, 51, 3), 2.4) - 0.5) * 0.5;
          return clamp(f === "cygwind" ? v + (speck(ci, si, tS) - 0.5) * 0.18 : v, 0, 1);
        case "tpw": return clamp(0.1 + 0.8 * Math.exp(-sq((la - dec * 0.5) / 20)) + (stretch(fbm(x, y, z, 5, 61, 4), 2.6) - 0.5) * 0.5, 0, 1);
        case "sst": return clamp(Math.pow(Math.max(Math.cos((la - dec * 0.4) * DEG), 0), 2.2) * 1.02 - 0.04 + (stretch(fbm(x, y, z, 6, 71, 3), 2.2) - 0.5) * 0.2, 0, 1);
        case "et": return clamp(wetness(la, lo, x, y, z) * 1.3 * warmth(la) - 0.06 + (fbm(x, y, z, 16, 73, 2) - 0.5) * 0.25, 0, 1);
        case "lst":
          v = 0.12 + 0.6 * warmth(la) + 0.3 * anyBox(la, lo, DESERTS) - (day ? 0 : 0.24) + (fbm(x, y, z, 10, 75, 3) - 0.5) * 0.3;
          return clamp(v, 0, 1);
        case "fcc":
          if (fbm(x, y, z, 30, 81, 2) > 0.72) return 0.04;                  // a lake
          return clamp(0.12 + wetness(la, lo, x, y, z) * warmth(la) * 0.95 + (speck(ci, si, 0) - 0.5) * 0.18, 0.12, 1);
        case "ndvi": case "sgli":
          return clamp(wetness(la, lo, x, y, z) * 1.2 * warmth(la) - 0.05 + (fbm(x, y, z, 22, 83, 2) - 0.5) * 0.3, 0, 1);
        case "chl":
          v = 0.2 + 0.6 * coastAt(la, lo) + 0.32 * sstep(35, 58, Math.abs(la)) + 0.3 * inBox(la, lo, [-4, 4, -150, -80, 1]) +
            0.25 * inBox(la, lo, [-30, -5, -20, 15, 0.8]) - 0.12 * Math.exp(-sq((Math.abs(la) - 25) / 9)) +
            (stretch(fbm(x, y, z, 14, 91, 4), 2.8) - 0.5) * 0.4;
          return clamp(v, 0, 1);
        case "rain":
          w = 0.5 * Math.exp(-sq((la - 6 - dec * 0.3) / 9)) + 0.4 * Math.exp(-sq((Math.abs(la) - 47) / 11)) + 0.08;
          w *= 1 - 0.85 * anyBox(la, lo, DESERTS);
          n = stretch(fbm(x + tS / 3600 * 0.02, y - tS / 3600 * 0.012, z, 9, 41, 4), 2.6);
          a = 0.9 - 0.5 * w;
          if (n < a) return -1;
          v = (n - a) / (1 - a) * (0.6 + 0.4 * fbm(x, y, z, 45, 43, 2) * 1.4);
          return clamp(inner ? Math.pow(v, 0.7) * 1.1 : v * 0.85, 0.02, 1);
        case "ssha":
          a = 0.35 + 0.65 * anyBox(la, lo, EDDIES);
          return clamp(0.5 + (stretch(fbm(x, y, z, 16, 101, 3), 3.2) - 0.5) * a * 1.3, 0, 1);
        case "tws": return stretch(fbm(x, y, z, 2.4, 111, 2), 4);
        case "sar": case "xsar":
          if (fbm(x, y, z, 26, 121, 2) > 0.73 || (coastAt(la, lo) > 0.55 && fbm(x, y, z, 40, 125, 2) > 0.66)) return 0.03 + 0.03 * speck(ci, si, tS);
          v = 0.5 * stretch(fbm(x, y, z, 30, 123, 2), 2.2) + 0.5 * speck(ci, si, tS);
          return clamp(f === "xsar" ? 0.1 + v * 0.95 : 0.15 + v * 0.75, 0.09, 1);
        case "sarsea": return clamp(0.2 + 0.45 * fbm(x * 3, y, z, 30, 127, 2) + (speck(ci, si, tS) - 0.5) * 0.5, 0, 1);
        case "nisar": return clamp(stretch(fbm(x, y, z, 24, 131, 3), 2.5) * 0.85 + (speck(ci, si, tS) - 0.5) * 0.35 + (1 - wetness(la, lo, x, y, z)) * 0.15, 0, 1);
        case "elev": return clamp(0.2 + stretch(fbm(x, y, z, 8, 141, 4), 2.4) * 0.6 + snowAt(la, lo, x, y, z, 0) * 0.3, 0, 1);
        case "cygland":
          return clamp(wetness(la, lo, x, y, z) * 0.95 + 0.25 * coastAt(la, lo) + (speck(ci, si, tS) - 0.5) * 0.3 - 0.08, 0, 1);
      }
      return -1;
    }
    function coastAt(la, lo) {
      var i = clamp(Math.floor(lo + 180), 0, 359), j = clamp(Math.floor(90 - la), 0, 179);
      return clamp(COAST[j * 360 + i] * 2.2, 0, 1);
    }
    /* which field a satellite shows at a cell, or "" for the faint inside of the swath */
    function pick(sp, onLand, la, lo, x, y, z, day) {
      var f = onLand ? sp.land : sp.sea;
      if (!f || (sp.day && !day)) return "";
      if (f === "smft") return snowAt(la, lo, x, y, z, 5) > 0.5 ? "frozen" : "sm";
      if (f === "smsnow") return snowAt(la, lo, x, y, z, 0) > 0.5 ? "snow" : "sm";
      if (f === "lstsnow") return snowAt(la, lo, x, y, z, 0) > 0.5 ? "snow" : "lst";
      if (f === "sglisnow") return snowAt(la, lo, x, y, z, 0) > 0.5 ? "snow" : "sgli";
      return f;
    }

    function stampCell(ci, si, sp, tS, edge, inner) {
      var age = tS - cT[ci], ds = 0, v = 0;
      if (age < 0) return;                                                  // laying rows backward: what is newer stays
      if (cS[ci] === si + 1 && age >= 0 && age < 40) {                    // this pass has it already
        cT[ci] = tS;
        if (edge && cD[ci] < 2) cD[ci] = 1;
        return;
      }
      if (edge) ds = 1;
      else {
        var la = 90 - (Math.floor(ci / GW) + 0.5) * 0.25, lo = -180 + (ci % GW + 0.5) * 0.25;
        var cl = Math.cos(la * DEG), x = cl * Math.cos(lo * DEG), y = cl * Math.sin(lo * DEG), z = Math.sin(la * DEG);
        var day = x * sunX + y * sunY + z * sunZ > 0.03;
        var f = pick(sp, LM[ci] === 1, la, lo, x, y, z, day);
        if (f) {
          v = value(f, ci, la, lo, x, y, z, tS, si, inner, day);
          if (v >= 0) { ds = FID[f]; v = Math.round(v * 255); } else v = 0;
        }
      }
      if (ds < 2 && cD[ci] > 1 && age >= 0 && age < FADE_S * 0.5) return;  // an outline never covers what another has just seen
      cT[ci] = tS; cS[ci] = si + 1; cD[ci] = ds; cV[ci] = v;
    }

    /* where a satellite is at time t, from its grid of points, without moving it */
    var P = [0, 0, 0], FW = [0, 0, 0], RT = [0, 0, 0], QA = [0, 0, 0], QB = [0, 0, 0];
    var qx = 0, qy = 0, qz = 0;
    function at(s, t, o) {
      var g = s.grid;
      if (!g) return false;
      var q = t / STEP, i = Math.floor(q), f = q - i, k = (i - g.i0) * 3, v = g.v;
      if (i < g.i0 || i + 1 >= g.i0 + g.n) return false;
      var x = v[k] + (v[k + 3] - v[k]) * f, y = v[k + 1] + (v[k + 4] - v[k + 1]) * f, z = v[k + 2] + (v[k + 5] - v[k + 2]) * f;
      var n = Math.sqrt(x * x + y * y + z * z);
      if (!(n > 0)) return false;
      o[0] = x / n; o[1] = y / n; o[2] = z / n;
      return true;
    }
    /* the point under the satellite (P), the way it flies (FW) and its right (RT), all unit vectors */
    function axes(s, t) {
      if (!at(s, t, P)) return false;
      var a = at(s, t - 4000, QA), b = at(s, t + 4000, QB);
      if (!a && !b) return false;
      if (!a) { QA[0] = P[0]; QA[1] = P[1]; QA[2] = P[2]; }
      if (!b) { QB[0] = P[0]; QB[1] = P[1]; QB[2] = P[2]; }
      var dx = QB[0] - QA[0], dy = QB[1] - QA[1], dz = QB[2] - QA[2], dp = dx * P[0] + dy * P[1] + dz * P[2];
      dx -= dp * P[0]; dy -= dp * P[1]; dz -= dp * P[2];
      var n = Math.sqrt(dx * dx + dy * dy + dz * dz);
      if (!(n > 0)) return false;
      FW[0] = dx / n; FW[1] = dy / n; FW[2] = dz / n;
      RT[0] = FW[1] * P[2] - FW[2] * P[1]; RT[1] = FW[2] * P[0] - FW[0] * P[2]; RT[2] = FW[0] * P[1] - FW[1] * P[0];
      return true;
    }
    /* the point `a` km ahead and `c` km to the right of the one under the satellite (qx, qy, qz) */
    function offset(a, c) {
      var d = Math.sqrt(a * a + c * c);
      if (d < 1e-6) { qx = P[0]; qy = P[1]; qz = P[2]; return; }
      var th = d / RE, cs = Math.cos(th), sn = Math.sin(th) / d;
      qx = P[0] * cs + (FW[0] * a + RT[0] * c) * sn;
      qy = P[1] * cs + (FW[1] * a + RT[1] * c) * sn;
      qz = P[2] * cs + (FW[2] * a + RT[2] * c) * sn;
    }
    function cellOf(x, y, z) {
      var la = Math.asin(clamp(z, -1, 1)), lo = Math.atan2(y, x);
      var i = Math.floor((lo + Math.PI) / TAU * GW), j = Math.floor((Math.PI / 2 - la) / Math.PI * GH);
      return clamp(j, 0, GH - 1) * GW + clamp(i, 0, GW - 1);
    }
    /* CYGNSS: where specular point k of satellite si is, km ahead and to the right; the GPS satellites
       move too, so the points wander slowly round the one they belong to */
    function specular(si, k, t) {
      var ph = hsh(si, k, 7, 3) * TAU + t / (2.4e6 + 0.9e6 * k) * TAU * (k % 2 ? 1 : -1);
      var r = 170 + 560 * hsh(si, k, 9, 5);
      QA[0] = 0.45 * r * Math.sin(ph); QA[1] = r * Math.cos(ph);
    }

    function stampRow(s, si, sp, t) {
      if (!sp || sp.none || !axes(s, t)) return;
      var tS = (t - T0) / 1000, k, n, c, c0, c1, b;
      if (sp.spec) {
        for (k = 0; k < sp.spec; k++) {
          specular(si, k, t);
          offset(QA[0], QA[1]);
          stampCell(cellOf(qx, qy, qz), si, sp, tS, false, false);
        }
        return;
      }
      if (sp.beams) {
        for (k = 0; k < sp.beams.length; k++) { offset(0, sp.beams[k]); stampCell(cellOf(qx, qy, qz), si, sp, tS, false, false); }
        return;
      }
      var step = CELL * 0.62 * Math.max(Math.sqrt(1 - P[2] * P[2]), 0.12);
      var lo = sp.band[0], hi = sp.band[1];
      if (sp.west) {                               // the right of the track is west when the track runs south
        var east = (-P[1] * RT[0] + P[0] * RT[1]);
        if (east > 0) { lo = -sp.band[1]; hi = -sp.band[0]; }
      }
      for (b = 0; b < (sp.two ? 2 : 1); b++) {
        c0 = b ? -hi : lo; c1 = b ? -lo : hi;
        n = Math.max(1, Math.ceil((c1 - c0) / step));
        for (k = 0; k <= n; k++) {
          c = c0 + (c1 - c0) * k / n;
          offset(0, c);
          stampCell(cellOf(qx, qy, qz), si, sp, tS, (k === 0 || k === n) && n > 3,
                    !!(sp.inner && c >= sp.inner[0] && c <= sp.inner[1]));
        }
        if (sp.inner) {
          offset(0, sp.inner[0]); stampCell(cellOf(qx, qy, qz), si, sp, tS, true, false);
          offset(0, sp.inner[1]); stampCell(cellOf(qx, qy, qz), si, sp, tS, true, false);
        }
      }
    }
    function stampRows(t) {
      for (var i = 0; i < sats.length; i++) if (sats[i].rec && sats[i].grid) stampRow(sats[i], i, SPEC[sats[i].key], t);
    }
    function sunVector(t) {
      var su = sunAt(t), la = su.lat * DEG, lo = su.lon * DEG;
      dec = su.lat; sunX = Math.cos(la) * Math.cos(lo); sunY = Math.cos(la) * Math.sin(lo); sunZ = Math.sin(la);
    }

    /* Rows are laid up to stampK (time stampK * ROW). On a start, a jump or a run back, the twelve minutes
       behind the clock are laid again, newest first, a few ms a frame, so the swaths grow back behind the
       satellites. */
    var stampK = NaN, fill = null, fillMs = 0, cells = 0;
    function clearAfter(tS) {
      for (var i = 0; i < NC; i++) if (cT[i] > tS) cT[i] = -1e9;
    }
    function stampTo(t) {
      var k = Math.floor(t / ROW), j, c0;
      sunVector(t);
      if (stampK !== stampK || k < stampK - 1 || k - stampK > FADE / ROW) {
        if (stampK === stampK && k < stampK) {
          if (simAnim) return;                     // on the way back to the present: what lies ahead of the clock is hidden
          clearAfter((t - T0) / 1000);
        }
        stampK = k; fill = { k: k, lo: Math.ceil((t - FADE) / ROW) };
      } else if (k > stampK) {
        for (j = stampK + 1; j <= k; j++) stampRows(j * ROW);
        stampK = k;
      }
      if (fill) {
        c0 = perf();
        while (fill.k >= fill.lo && perf() - c0 < 6) { stampRows(fill.k * ROW); fill.k--; }
        fillMs += perf() - c0;
        if (fill.k < fill.lo) fill = null;
        ovForce = true; dirty = true;
      }
    }

    /* The cells on the globe: a square of up to 640 px over the disc, each pixel looking up its cell
       through a map that is made again only when the globe turns or changes size. */
    var dCv = D.createElement("canvas"), dctx = dCv.getContext("2d"), dKey = "", dRes = 0;
    var dImg = null, dBuf = null, dMap = null, dLimb = null, dataMs = 0;
    var satA = new Float32Array(sats.length), famC = new Uint32Array(sats.length);
    sats.forEach(function (s, i) {
      var c = parseInt(s.fam.color.slice(1), 16);
      famC[i] = ((c & 255) << 16) | (c & 0xff00) | ((c >> 16) & 255);
    });
    function dataMap() {
      var res = Math.max(32, Math.min(Math.round(2 * R * dpr), 640));
      var key = res + "|" + rot[0].toFixed(2) + "," + rot[1].toFixed(2);
      if (key === dKey) return;
      dKey = key;
      if (res !== dRes) {
        dRes = res; dCv.width = dCv.height = res;
        dImg = dctx.createImageData(res, res);
        dBuf = new Uint32Array(dImg.data.buffer);
        dMap = new Int32Array(res * res); dLimb = new Float32Array(res * res);
      }
      var i, j, p = 0, u, w, d, x, y, z, ci, cj, inv = 2 / res;
      for (j = 0; j < res; j++) {
        w = 1 - (j + 0.5) * inv;
        for (i = 0; i < res; i++, p++) {
          u = (i + 0.5) * inv - 1;
          d = 1 - u * u - w * w;
          if (d <= 0) { dMap[p] = -1; continue; }
          d = Math.sqrt(d);
          x = m00 * d + m10 * u + m20 * w; y = m01 * d + m11 * u + m21 * w; z = m02 * d + m22 * w;
          ci = Math.floor((Math.atan2(y, x) + Math.PI) / TAU * GW);
          cj = Math.floor((Math.PI / 2 - Math.asin(z > 1 ? 1 : z < -1 ? -1 : z)) / Math.PI * GH);
          dMap[p] = (cj < GH ? cj : GH - 1) * GW + (ci < GW ? ci : GW - 1);
          dLimb[p] = d < 0.2 ? d * 5 : 1;
        }
      }
    }
    function drawData(c, t) {
      if (!dctx) return;
      var c0 = perf();
      dataMap();
      var nowS = (t - T0) / 1000, inv = 255 / FADE_S, n = dRes * dRes, buf = dBuf, p, ci, age, a, si, ds, col, i, s;
      for (i = 0; i < sats.length; i++) { s = sats[i]; satA[i] = s.fam.a * (s === focus ? 1 : 1 - 0.55 * dim); }
      cells = 0;
      for (p = 0; p < n; p++) {
        ci = dMap[p];
        if (ci < 0) { buf[p] = 0; continue; }
        age = nowS - cT[ci];
        if (age < 0 || age >= FADE_S) { buf[p] = 0; continue; }
        si = cS[ci] - 1; ds = cD[ci];
        a = FADEL[(age * inv) | 0] * satA[si] * dLimb[p];
        if (ds > 1) { col = LUT[(ds << 8) | cV[ci]]; a *= LA[ds]; }
        else { col = famC[si]; a *= ds ? 0.5 : 0.1; }
        if (a < 0.004) { buf[p] = 0; continue; }
        buf[p] = ((((a * 255) | 0) << 24) | col) >>> 0;
        cells++;
      }
      dctx.putImageData(dImg, 0, 0);
      c.drawImage(dCv, cx - R, cy - R, 2 * R, 2 * R);
      a = perf() - c0;
      dataMs = dataMs ? dataMs * 0.9 + a * 0.1 : a;
    }

    /* ----- what each instrument is doing now, drawn at the satellite every frame ----- */

    var on = false;
    function trace(pts) {                          // [a0, c0, a1, c1, ...] in km round the satellite: a line through the visible part
      on = false;
      for (var i = 0; i < pts.length; i += 2) {
        offset(pts[i], pts[i + 1]); pj(qx, qy, qz);
        if (pd > 0) { if (on) ctx.lineTo(px, py); else ctx.moveTo(px, py); on = true; } else on = false;
      }
    }
    function arcPts(a0, r, from, to, n) {           // a circle round a point a0 km ahead, angles from the way it flies
      var pts = [], i, th;
      for (i = 0; i <= n; i++) { th = (from + (to - from) * i / n) * DEG; pts.push(a0 + r * Math.cos(th), r * Math.sin(th)); }
      return pts;
    }
    function dotAt(a, c, rad, fill) {
      offset(a, c); pj(qx, qy, qz);
      if (pd <= 0) return false;
      ctx.beginPath(); ctx.arc(px, py, rad, 0, TAU); ctx.fillStyle = fill; ctx.fill();
      return true;
    }
    function horseshoe(x, y, k) {                  // a delay-Doppler map in small: the peak and its two arms
      ctx.beginPath();
      for (var u = -1; u <= 1.001; u += 0.25) { var xx = x + u * 7 * k, yy = y - 2 * k + u * u * 8 * k; if (u === -1) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy); }
      ctx.stroke();
      ctx.beginPath(); ctx.arc(x, y - 2 * k, 1.8 * k, 0, TAU); ctx.fill();
    }
    function drawLooks(now) {
      var i, s, sp, k, hi, col, glow, ph, j, sx, sy, o, tw;
      var spin = reduced ? 0.15 : now;
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (i = byPri.length - 1; i >= 0; i--) {
        s = byPri[i]; sp = SPEC[s.key];
        if (!sp || sp.look === "none" || !s.ok || s.fam.a < 0.01 || s.depth < -0.25 || !axes(s, simT)) continue;
        hi = s === focus;
        k = s.fam.a * (hi ? 1 : 1 - 0.65 * dim);
        if (k < 0.02) continue;
        col = rgba(s.fam.rgb, (hi ? 0.95 : 0.6) * k);
        glow = "rgba(255,255,255," + ((hi ? 0.95 : 0.75) * k).toFixed(3) + ")";
        ctx.lineWidth = hi ? 1.6 : 1.1; ctx.strokeStyle = col;
        switch (sp.look) {
          case "cone":                             // SMAP: the whole circle, and the beam going round it
            ctx.beginPath(); trace(arcPts(0, sp.r, 0, 360, 48)); ctx.stroke();
            ph = (spin / 4100) * 360;
            ctx.lineWidth = hi ? 2.6 : 2; ctx.strokeStyle = glow;
            ctx.beginPath(); trace(arcPts(0, sp.r, ph - 40, ph, 8)); ctx.stroke();
            dotAt(sp.r * Math.cos(ph * DEG), sp.r * Math.sin(ph * DEG), hi ? 3 : 2.4, glow);
            break;
          case "arc": case "gpm":                  // AMSR, GMI: the forward arc, swept over and over
            ctx.beginPath(); trace(arcPts(0, sp.r, -72, 72, 24)); ctx.stroke();
            ph = -72 + 144 * frac(spin / 1900);
            dotAt(sp.r * Math.cos(ph * DEG), sp.r * Math.sin(ph * DEG), hi ? 2.8 : 2.2, glow);
            if (sp.look === "gpm") {               // the radar's line across the track
              ctx.lineWidth = hi ? 2.4 : 1.8; ctx.strokeStyle = glow;
              ctx.beginPath(); trace([0, sp.inner[0], 0, sp.inner[1]]); ctx.stroke();
            }
            break;
          case "hex":                              // SMOS: the hexagon of its two-dimensional view
            ctx.beginPath(); trace(arcPts(160, sp.r, 30, 390, 6));
            ctx.fillStyle = rgba(s.fam.rgb, 0.1 * k); ctx.fill(); ctx.stroke();
            ctx.lineWidth = 0.8; ctx.strokeStyle = rgba(s.fam.rgb, 0.35 * k);
            ctx.beginPath(); trace(arcPts(160, sp.r * 0.55, 30, 390, 6)); ctx.stroke();
            break;
          case "line": case "whisk":               // a line across the swath; MODIS's mirror sweeps along it
            ctx.lineWidth = hi ? 2 : 1.5; ctx.strokeStyle = col;
            var b0 = sp.band[0], b1 = sp.band[1];
            if (sp.west && (-P[1] * RT[0] + P[0] * RT[1]) > 0) { b0 = -sp.band[1]; b1 = -sp.band[0]; }
            ctx.beginPath(); trace([0, b0, 0, (b0 + b1) / 2, 0, b1]); ctx.stroke();
            if (sp.look === "whisk") { ph = frac(spin / 700); dotAt(0, b0 + (b1 - b0) * ph, hi ? 2.6 : 2, glow); }
            break;
          case "side":                             // a radar: the line of sight off to the side, and the strip it lights
            ctx.lineWidth = 0.8; ctx.strokeStyle = rgba(s.fam.rgb, 0.4 * k);
            ctx.beginPath(); trace([0, 0, 0, sp.band[0]]); ctx.stroke();
            ph = reduced ? 1 : 0.55 + 0.45 * Math.abs(Math.sin(now / 260));
            ctx.lineWidth = hi ? 3 : 2.4; ctx.strokeStyle = "rgba(255,255,255," + (ph * k * (hi ? 0.95 : 0.8)).toFixed(3) + ")";
            ctx.beginPath(); trace([0, sp.band[0], 0, sp.band[1]]); ctx.stroke();
            break;
          case "fan":                              // ASCAT: three beams on either side, fore, mid and aft
            ctx.lineWidth = hi ? 1.8 : 1.3; ctx.strokeStyle = col;
            for (j = 0; j < 6; j++) {
              o = [45, 90, 135][j % 3] * DEG; tw = j < 3 ? 1 : -1;
              ctx.beginPath();
              trace([sp.band[0] * Math.cos(o) * 1.2, tw * sp.band[0] * Math.sin(o), sp.band[1] * Math.cos(o) * 1.05, tw * sp.band[1] * Math.sin(o)]);
              ctx.stroke();
            }
            break;
          case "swot":                             // two narrow strips and the gap between them
            ctx.lineWidth = hi ? 3.2 : 2.6; ctx.strokeStyle = glow;
            ctx.beginPath(); trace([-45, 35, 45, 35]); ctx.stroke();
            ctx.beginPath(); trace([-45, -35, 45, -35]); ctx.stroke();
            break;
          case "twin":                             // GRACE-FO: the microwave and laser link to its twin
            var t2 = byKey.gracefo2;
            if (t2 && t2.ok && t2.vis && s.vis) {
              ctx.save();
              ctx.setLineDash([3, 4]); ctx.lineDashOffset = reduced ? 0 : -(now / 40) % 7;
              ctx.lineWidth = hi ? 1.8 : 1.4; ctx.strokeStyle = glow;
              ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t2.x, t2.y); ctx.stroke();
              ctx.restore();
            }
            break;
          case "laser":                            // ICESat-2: six green spots of its laser
            ctx.fillStyle = "rgba(120,255,150," + (0.95 * k).toFixed(3) + ")";
            for (j = 0; j < sp.beams.length; j++) dotAt(0, sp.beams[j], hi ? 1.9 : 1.5, ctx.fillStyle);
            break;
          case "spec":                             // CYGNSS: its four specular points, and their maps when it is picked
            sx = s.x; sy = s.y;
            for (j = 0; j < sp.spec; j++) {
              specular(sats.indexOf(s), j, simT);
              offset(QA[0], QA[1]); pj(qx, qy, qz);
              if (pd <= 0) continue;
              if (s.vis) {
                ctx.lineWidth = 0.7; ctx.strokeStyle = rgba(s.fam.rgb, (hi ? 0.6 : 0.28) * k);
                ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(px, py); ctx.stroke();
              }
              if (hi) {
                ctx.lineWidth = 1.3; ctx.strokeStyle = "rgba(255,240,170,.95)"; ctx.fillStyle = "rgba(255,255,255,.95)";
                horseshoe(px, py, 1);
              } else {
                ctx.beginPath(); ctx.arc(px, py, 1.8, 0, TAU); ctx.fillStyle = glow; ctx.fill();
              }
            }
            break;
        }
      }
    }

    /* ----- the clock ----- */

    var speed = reduced ? 1 : FAST, simT = Date.now(), simAnim = null, last = perf(), clockShown = "";

    function showClock() {
      var d = new Date(simT);
      var text = dateText(simT) + " · " + pad2(d.getUTCHours()) + ":" + pad2(d.getUTCMinutes()) + " UTC";
      if (text !== clockShown) { clockShown = text; clockTime.textContent = text; }
    }
    function showSpeed() {
      bLive.setAttribute("aria-pressed", speed === 1 ? "true" : "false");
      bFast.setAttribute("aria-pressed", speed === 1 ? "false" : "true");
      clockSpeed.hidden = speed === 1;
    }
    function setSpeed(v) {
      if (v === speed) return;
      speed = v;
      if (v === 1) {                               // back to the present: a short run back, not a jump
        var back = Math.abs(simT - Date.now());
        if (!reduced && back > 2000 && back < 3 * 3600e3) simAnim = { from: simT, t0: perf(), ms: 700 };
        else { simAnim = null; simT = Date.now(); }
      } else simAnim = null;
      showSpeed();
      ovForce = true;
      measure();
      pace();
      invalidate();
    }

    /* ----- what is picked ----- */

    var pinned = null, hover = null, focus = null, shown = null, dim = 0;
    var mouse = null, ptr = null, cursor = "";
    var cardLeft = false, cardW = 0, cardH = 0, altAt = 0, altShown = "", farShown = false;
    var obst = [];                                 // boxes of the HTML that lies over the canvas, in canvas px

    function setCursor(c) { if (c !== cursor) { cursor = c; globe.style.cursor = c; } }

    function refocus() {
      focus = pinned || hover;
      var s = pinned || (wide ? hover : null);     // under the canvas the card is for a pinned satellite only
      ovForce = true;
      if (s !== shown || (s && card.classList.contains("ho-pinned") !== (s === pinned))) { shown = s; showCard(); }
    }
    function showCard() {
      var s = shown;
      if (!s) {
        box.hidden = true;
        card.classList.remove("ho-pinned");
        measure();
        return;
      }
      cDot.style.background = s.fam.color;
      cFamName.textContent = s.fam.name;
      cName.textContent = s.name;
      cAgency.textContent = s.agency;
      cInst.textContent = s.inst;
      cUse.textContent = s.use;
      cLink.href = s.url;
      legend(s);
      cLink.setAttribute("aria-label", s.name + " mission page (opens in a new tab)");
      altShown = ""; altAt = 0; farShown = false; cFar.hidden = true;
      showAltitude(perf());
      cClose.hidden = s !== pinned;
      card.classList.toggle("ho-pinned", s === pinned);
      box.hidden = false;
      measure();
      seat();
    }
    /* The card's account of the swath: its shape, and the colours left on the ground (with CYGNSS, the
       four delay-Doppler maps it makes, one for each specular point). */
    function legend(s) {
      var sp = SPEC[s.key] || {};
      cSw.textContent = sp.desc || "";
      while (cLeg.firstChild) cLeg.removeChild(cLeg.firstChild);
      cLeg.hidden = !sp.show;
      if (!sp.show) return;
      if (sp.ddm) {
        cLeg.appendChild(h("p", "ho-lgh", "Its four delay-Doppler maps (illustrative)"));
        cLeg.appendChild(cDdms);
        ddmAt = 0; ddmFor = null;
      }
      cLeg.appendChild(h("p", "ho-lgh", "On the ground behind it (illustrative)"));
      sp.show.forEach(function (id) {
        var f = FIELDS[id], row = h("div", "ho-lg"), bar = h("span", "ho-bar");
        bar.style.background = gradientCss(f.stops);
        row.appendChild(h("span", "ho-lgname", f.name));
        if (f.lo || f.hi) { row.appendChild(h("span", "ho-end", f.lo)); row.appendChild(bar); row.appendChild(h("span", "ho-end", f.hi)); }
        else { row.className = "ho-lg ho-plain"; row.appendChild(bar); }
        cLeg.appendChild(row);
      });
    }
    var DDMLUT = ramp(["#000004", "#2c0b57", "#7b1d6e", "#c43c4e", "#f1731d", "#fbbf2b", "#fcffa4"]);
    function drawDdms(now) {
      var sp = SPEC[shown.key];
      if (!sp || !sp.ddm || (now - ddmAt < 240 && ddmFor === shown) || (reduced && ddmFor === shown)) return;
      ddmAt = now; ddmFor = shown;
      var si = sats.indexOf(shown), slot = Math.floor(simT / 60000);
      ddmCv.forEach(function (dc, k) {
        var x2 = dc.getContext("2d");
        if (!x2) return;
        var w2 = dc.width, h2 = dc.height, img = x2.createImageData(w2, h2), b = new Uint32Array(img.data.buffer), r, q, dl, dp, arm, pw;
        var gain = 0.55 + 0.45 * hsh(si, k, slot, 9), coh = hsh(si, k, slot, 11);
        for (r = 0; r < h2; r++) {
          dl = r / (h2 - 1) * 1.3 - 0.25;          // delay: later downward
          for (q = 0; q < w2; q++) {
            dp = q / (w2 - 1) * 2 - 1;              // Doppler
            arm = dl - 0.8 * dp * dp;
            pw = Math.exp(-arm * arm / 0.007) * Math.exp(-Math.max(dl, 0) * 1.5) * (dl > -0.05 ? 1 : 0.15) * gain +
              coh * 0.9 * Math.exp(-(dp * dp / 0.012 + dl * dl / 0.004)) + Math.random() * 0.13;
            b[r * w2 + q] = (0xff000000 | DDMLUT[clamp((pw * 235) | 0, 0, 255)]) >>> 0;
          }
        }
        x2.putImageData(img, 0, 0);
      });
    }
    function showAltitude(now) {
      if (!shown || now - altAt < 400) return;
      altAt = now;
      var g = shown.rec ? geoAt(shown.rec, simT) : null;
      var text = g ? Math.round(g.alt) + " km" : "–";
      if (text !== altShown) { altShown = text; cAlt.textContent = text; }
      var far = shown.ok && !shown.vis;
      if (far !== farShown) { farShown = far; cFar.hidden = !far; measure(); }
    }
    /* On a wide square the card sits in a lower corner: the right one, or the left one while the
       satellite it is about is under the right one. */
    function seat() {
      if (!shown || !wide || !cardW || !shown.vis) return;
      var x = shown.x, y = shown.y, m = 22;
      if (y < size - cardH - m) return;
      var inRight = x > size - cardW - m, inLeft = x < cardW + m;
      var left = cardLeft ? !(inLeft && !inRight) : (inRight && !inLeft);
      if (left !== cardLeft) {
        cardLeft = left;
        card.classList.toggle("ho-left", left);
        measure();
      }
    }
    /* Where the clock, the buttons and the card lie on the canvas, so that no name is drawn under them.
       Called when one of them changes, never from the frame loop. */
    function measure() {
      obst.length = 0;
      cardW = cardH = 0;
      if (!size) return;
      var c = cv.getBoundingClientRect();
      [clock, sw, bHome, box].forEach(function (n) {
        if (n.hidden) return;
        var r = n.getBoundingClientRect();
        if (!r.width || r.right < c.left || r.left > c.right || r.bottom < c.top || r.top > c.bottom) return;
        obst.push(r.left - c.left - 5, r.top - c.top - 4, r.right - c.left + 5, r.bottom - c.top + 4);
        if (n === box) { cardW = r.width; cardH = r.height; }
      });
    }

    function pin(s, show) {
      pinned = s;
      refocus();
      if (show) reveal(s);
      invalidate();
    }
    function unpin() {
      if (!pinned) return;
      if (card.contains(D.activeElement)) globe.focus();
      pinned = null;
      refocus();
      invalidate();
    }
    function stepPick(dir) {
      var list = byPri.filter(function (s) { return s.rec && s.fam.on; });
      if (!list.length) return;
      var i = list.indexOf(pinned);
      i = i < 0 ? (dir > 0 ? 0 : list.length - 1) : (i + dir + list.length) % list.length;
      pin(list[i], true);
    }
    /* A satellite picked with the keys may be behind the globe: turn it into view, the short way. */
    function reveal(s) {
      if (!s.rec || !locate(s, simT)) return;
      var d = Math.acos(clamp(m00 * s.ex + m01 * s.ey + m02 * s.ez, -1, 1));
      if (d < 68 * DEG) return;
      var a = -rot[0] * DEG, b = -rot[1] * DEG;    // the point in the middle of the view
      var c0 = Math.cos(b) * Math.cos(a), c1 = Math.cos(b) * Math.sin(a), c2 = Math.sin(b);
      var sd = Math.sin(d), f = (d - 46 * DEG) / d;
      if (sd < 1e-3) { turnTo([rot[0] + 130, rot[1]], 700); return; }
      var w0 = Math.sin((1 - f) * d) / sd, w1 = Math.sin(f * d) / sd;
      var x = w0 * c0 + w1 * s.ex, y = w0 * c1 + w1 * s.ey, z = w0 * c2 + w1 * s.ez;
      turnTo([-Math.atan2(y, x) / DEG, clamp(-Math.asin(clamp(z, -1, 1)) / DEG, -89, 89)], 700);
    }
    function toggleFamily(f) {
      f.on = !f.on;
      f.chip.setAttribute("aria-pressed", f.on ? "true" : "false");
      if (!f.on && pinned && pinned.fam === f) { if (card.contains(D.activeElement)) globe.focus(); pinned = null; }
      if (!f.on && hover && hover.fam === f) hover = null;
      refocus();
      invalidate();
    }

    /* ----- turning ----- */

    function turnTo(target, ms) {
      if (reduced || !(ms > 0)) { turn = null; setRot(target); settle(); invalidate(); return; }
      turn = { from: rot.slice(), d0: wrap180(target[0] - rot[0]), d1: target[1] - rot[1], t0: perf(), ms: ms };
      invalidate();
    }
    function settle() {                            // "Recentre" is there only while the globe is turned away
      var now = Math.abs(wrap180(rot[0] - HOME[0])) > 0.5 || Math.abs(rot[1] - HOME[1]) > 0.5;
      if (now === away) return;
      away = now;
      if (!now && D.activeElement === bHome) globe.focus();
      bHome.hidden = !now;
      measure();
    }

    /* ----- layers ----- */

    function drawStill() {                         // once for a size: three gradients that a turn leaves as they are
      var c = sctx, g;
      c.clearRect(0, 0, size, size);
      g = c.createRadialGradient(cx, cy, R - 1, cx, cy, R + gap);       // a breath of air outside the limb
      g.addColorStop(0, "rgba(150,232,214,.14)");
      g.addColorStop(1, "rgba(150,232,214,0)");
      c.beginPath(); c.arc(cx, cy, R + gap, 0, TAU); c.fillStyle = g; c.fill();
      g = c.createRadialGradient(cx - R * 0.36, cy - R * 0.42, R * 0.08, cx, cy, R * 1.05);   // the sea, lifted toward the upper left
      g.addColorStop(0, "#183533");
      g.addColorStop(1, "#0f2322");
      c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.fillStyle = g; c.fill();
      c = rctx;
      c.clearRect(0, 0, size, size);
      g = c.createRadialGradient(cx, cy, R * 0.72, cx, cy, R);          // the globe falls away at its edge
      g.addColorStop(0, "rgba(6,18,17,0)");
      g.addColorStop(1, "rgba(6,18,17,.34)");
      c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.fillStyle = g; c.fill();
    }

    function drawBase() {
      var c = bctx;
      c.clearRect(0, 0, size, size);
      c.drawImage(seaCv, 0, 0, size, size);
      c.beginPath(); bpath(graticule);                                  // half a px wide: a hairline, which is quick to draw
      c.strokeStyle = "rgba(255,255,255,.072)"; c.lineWidth = 0.5; c.stroke();
      c.beginPath(); bpath(land);
      c.fillStyle = "#31554d"; c.fill();                                // light enough to stand out from the sea on the night side too
      c.drawImage(rimCv, 0, 0, size, size);
    }

    var DUSK = 9;                                       // caps round the point opposite the Sun, 90 degrees down to 78: twilight, then .38 of night
    var SHADE = "rgba(0,0,0," + (1 - Math.pow(1 - 0.38, 1 / DUSK)).toFixed(4) + ")";   // nine of these, one on the other, are .38
    var AHEAD = [0.5, 0.34, 0.18];                      // how strong the path ahead is, in three stretches of four minutes
    var rx = [], ry = [], ra = [], nr = 0;

    function behind(a) { return 0.92 * Math.pow(1 - clamp(a, 0, 1), 1.5); }
    function strokeRun(c, rgb, k) {
      var n = nr, i;
      nr = 0;
      if (n < 2) return;
      var x0 = rx[0], y0 = ry[0], x1 = rx[n - 1], y1 = ry[n - 1], dx = x1 - x0, dy = y1 - y0;
      c.beginPath(); c.moveTo(x0, y0);
      for (i = 1; i < n; i++) c.lineTo(rx[i], ry[i]);
      if (dx * dx + dy * dy < 4) c.strokeStyle = rgba(rgb, behind((ra[0] + ra[n - 1]) / 2) * k);
      else {
        var g = c.createLinearGradient(x0, y0, x1, y1);
        g.addColorStop(0, rgba(rgb, behind(ra[0]) * k));
        g.addColorStop(0.5, rgba(rgb, behind((ra[0] + ra[n - 1]) / 2) * k));
        g.addColorStop(1, rgba(rgb, behind(ra[n - 1]) * k));
        c.strokeStyle = g;
      }
      c.stroke();
    }

    function drawOverlay(t) {
      var c = octx, i, j, b, n, s, g, v, k, isF, any, ax, ay, bx, by, av;
      c.clearRect(0, 0, size, size);
      drawData(c, t);

      var sun = sunAt(t);
      c.save();
      c.beginPath(); c.arc(cx, cy, R, 0, TAU); c.clip();
      circle.center([wrap180(sun.lon + 180), -sun.lat]);
      c.fillStyle = SHADE;
      for (i = 0; i < DUSK; i++) {
        c.beginPath(); opath(circle.radius(90 - i * 1.5)());
        c.fill();
      }
      c.restore();
      /* Sunlight as light, not as a picture of the Sun: warmest under the Sun, gone at the terminator.
         When the Sun is behind the globe the light comes in from that edge. */
      var sl = sun.lat * DEG, so = sun.lon * DEG;
      pj(Math.cos(sl) * Math.cos(so), Math.cos(sl) * Math.sin(so), Math.sin(sl));
      var gx = px, gy = py;
      if (pd < 0) {
        var vx = px - cx, vy = py - cy, len = Math.sqrt(vx * vx + vy * vy);
        if (len > 1) {
          var out = R * (1 + (Math.acos(clamp(pd, -1, 1)) - Math.PI / 2) / (Math.PI / 2) * 0.9);
          gx = cx + vx / len * out; gy = cy + vy / len * out;
        } else { gx = cx; gy = cy; }
      }
      g = c.createRadialGradient(gx, gy, 0, gx, gy, R * 1.3);
      g.addColorStop(0, "rgba(255,243,212,.17)");
      g.addColorStop(0.45, "rgba(255,228,170,.07)");
      g.addColorStop(1, "rgba(255,214,130,0)");
      c.beginPath(); opath(circle.center([sun.lon, sun.lat]).radius(90)());     // only the half that the Sun is over
      c.fillStyle = g; c.fill();

      /* The paths. Behind a satellite: solid, fading to nothing twelve minutes back. Ahead: dashes, each
         the first half of a 30 s step of the time grid, so they stay where they are on the ground and the
         satellite flies along them. */
      var iH = Math.floor(t / STEP), iT = Math.ceil((t - SPAN) / STEP), iF = Math.floor((t + SPAN) / STEP);
      var band = Math.ceil((iF - iH) / 3);
      c.lineJoin = "round";
      for (n = byPri.length - 1; n >= 0; n--) {
        s = byPri[n];
        s.hv = false;
        if (!s.ok || s.fam.a < 0.01) continue;
        isF = s === focus;
        k = s.fam.a * (isF ? 1 : 1 - 0.72 * dim);
        g = s.grid; v = g.v;
        s.hx = s.x; s.hy = s.y; s.hv = s.vis;

        c.lineCap = "round"; c.lineWidth = isF ? 2.3 : 1.6;
        nr = 0;
        for (j = iT; j <= iH; j++) {
          pjv(v, (j - g.i0) * 3);
          if (pd > 0) { rx[nr] = px; ry[nr] = py; ra[nr] = (t - j * STEP) / SPAN; nr++; }
          else strokeRun(c, s.fam.rgb, k);
        }
        if (s.vis) { rx[nr] = s.x; ry[nr] = s.y; ra[nr] = 0; nr++; }
        strokeRun(c, s.fam.rgb, k);

        c.lineCap = "butt"; c.lineWidth = isF ? 1.5 : 1.1;
        for (b = 0; b < 3; b++) {
          any = false;
          c.beginPath();
          for (j = iH + b * band; j < iH + (b + 1) * band && j < iF; j++) {
            pjv(v, (j - g.i0) * 3); ax = px; ay = py; av = pd > 0;
            pjv(v, (j + 1 - g.i0) * 3); bx = (ax + px) / 2; by = (ay + py) / 2;
            if (!av || !(pd > 0)) continue;
            if (j === iH) {                        // the step the satellite is in: what is left of its dash
              if (!s.vis || (s.x - ax) * (bx - ax) + (s.y - ay) * (by - ay) > (bx - ax) * (bx - ax) + (by - ay) * (by - ay)) continue;
              ax = s.x; ay = s.y;
            }
            c.moveTo(ax, ay); c.lineTo(bx, by); any = true;
          }
          if (any) { c.strokeStyle = rgba(s.fam.rgb, AHEAD[b] * k * (isF ? 1.6 : 1)); c.stroke(); }
        }
      }

      c.beginPath(); c.arc(cx, cy, R, 0, TAU);
      c.strokeStyle = "rgba(255,255,255,.22)"; c.lineWidth = 1; c.stroke();
    }

    /* ----- names ----- */

    var HALO = "rgba(7,20,19,.88)", INK = "rgba(255,255,255,.95)", RING = "rgba(7,20,19,.92)";
    var labelFont = "", labelPx = 11.5, labelH = 15, dotR = 4.3, widths = {};
    var boxes = [], nb = 0, tagAt = {}, holder = {}, frameNo = 0, labels = 0;
    var siteVis = false, siteX = 0, siteY = 0, siteSide = 0;

    function textW(text) { return widths[text] || (widths[text] = ctx.measureText(text).width); }
    function hits(x0, y0, x1, y1, self) {
      var i, s, r = dotR + 2;
      for (i = 0; i < nb; i += 4) if (x0 < boxes[i + 2] && x1 > boxes[i] && y0 < boxes[i + 3] && y1 > boxes[i + 1]) return true;
      for (i = 0; i < sats.length; i++) {
        s = sats[i];
        if (s !== self && s.vis && s.fam.on && x0 < s.x + r && x1 > s.x - r && y0 < s.y + r && y1 > s.y - r) return true;
      }
      return false;
    }
    function keep(x0, y0, x1, y1) { boxes[nb] = x0; boxes[nb + 1] = y0; boxes[nb + 2] = x1; boxes[nb + 3] = y1; nb += 4; }
    /* The corner a name starts from, for the four places round a dot: right, left, above, below. */
    function spot(side, x, y, w, r) {
      if (side === 0) { px = x + r + 5; py = y - labelH / 2; }
      else if (side === 1) { px = x - r - 5 - w; py = y - labelH / 2; }
      else if (side === 2) { px = x - w / 2; py = y - r - 4 - labelH; }
      else { px = x - w / 2; py = y + r + 4; }
    }
    function place(s, text) {
      var w = textW(text), a, side;
      for (a = 0; a < 5; a++) {
        side = a === 0 ? s.side : a - 1;
        if (a > 0 && side === s.side) continue;
        spot(side, s.x, s.y, w, dotR);
        if (px < 3 || py < 3 || px + w > size - 3 || py + labelH > size - 3) continue;
        if (hits(px - 2, py - 1, px + w + 2, py + labelH + 1, s)) continue;
        if (side !== s.side) { s.side = side; s.la = 0; }
        keep(px - 2, py - 1, px + w + 2, py + labelH + 1);
        return true;
      }
      return false;
    }
    /* Names in the order of PRIORITY; one that would run into an earlier one, into a dot or into the HTML
       over the canvas is left out. Satellites that share a name (CYGNSS, GRACE-FO) show it once, and on
       the same one for as long as that works. */
    function layout() {
      var i, s, t, lead;
      nb = 0;
      for (i = 0; i < obst.length; i++) boxes[nb++] = obst[i];
      if (siteVis) {
        var w = textW(SITE.name);
        spot(siteSide, siteX, siteY, w, 4);
        if (px + w > size - 3 || px < 3) { siteSide = siteSide ? 0 : 1; spot(siteSide, siteX, siteY, w, 4); }
        keep(px - 2, py - 1, px + w + 2, py + labelH + 1);
        keep(siteX - 6, siteY - 6, siteX + 6, siteY + 6);
      }
      for (i = 0; i < sats.length; i++) sats[i].lt = 0;
      if (focus && focus.vis && focus.fam.on && place(focus, focus.name)) focus.lt = 1;
      for (i = 0; i < byPri.length; i++) {
        s = byPri[i];
        if (s === focus || !s.vis || !s.fam.on || s.depth < 0.06) continue;
        t = s.tag;
        if (t !== s.name) {
          if (tagAt[t] === frameNo) continue;
          lead = holder[t];
          if (lead && lead !== s && lead !== focus && lead.vis && lead.fam.on && lead.depth >= 0.06 && place(lead, t)) {
            lead.lt = 1; tagAt[t] = frameNo;
            continue;
          }
          if (place(s, t)) { s.lt = 1; tagAt[t] = frameNo; holder[t] = s; }
        } else if (place(s, t)) s.lt = 1;
      }
    }

    /* ----- one frame ----- */

    var drawn = 0, cost = 0, frames = 0;

    function step(now) {
      var c0 = perf(), dt = clamp(now - last, 0, 1000), i, s, k, f, a;
      last = now;
      frames++; frameNo++;

      if (speed === 1) {
        if (simAnim) {
          a = (now - simAnim.t0) / simAnim.ms;
          if (a >= 1) { simAnim = null; simT = Date.now(); }
          else { simT = simAnim.from + (Date.now() - simAnim.from) * ease(a); dirty = true; }
          ovForce = true;
        } else simT = Date.now();
      } else simT += dt * speed;

      if (turn) {
        a = (now - turn.t0) / turn.ms;
        setRot([turn.from[0] + turn.d0 * ease(a), turn.from[1] + turn.d1 * ease(a)]);
        if (a >= 1) { turn = null; settle(); } else dirty = true;
      }
      showClock();
      if (!size) return;

      k = reduced ? 1 : 1 - Math.exp(-dt / 110);
      for (i = 0; i < famList.length; i++) {
        f = famList[i]; a = f.on ? 1 : 0;
        if (Math.abs(a - f.a) > 0.004) { f.a += (a - f.a) * k; ovForce = true; dirty = true; } else f.a = a;
      }

      drawn = 0;
      for (i = 0; i < sats.length; i++) {
        s = sats[i];
        s.ok = s.vis = false;
        if (!s.rec || s.fam.a < 0.01 || !locate(s, simT)) continue;
        pj(s.ex, s.ey, s.ez);
        s.ok = true; s.x = px; s.y = py; s.depth = pd; s.vis = pd > 0;
        if (s.vis && s.fam.on) drawn++;
      }
      stampTo(simT);

      /* what the pointer is on */
      var turning = ptr && ptr.mode === "turn";
      if (mouse && !turning) {
        var near = nearest(mouse.x, mouse.y, 16);
        if (!near && hover && hover.vis && hover.fam.on) {
          a = hover.x - mouse.x; k = hover.y - mouse.y;
          if (a * a + k * k < 22 * 22) near = hover;
        }
        if (near !== hover) { hover = near; refocus(); }
        setCursor(near ? "pointer" : "");
      } else {
        if (hover) { hover = null; refocus(); }
        setCursor(turning ? "grabbing" : "");
      }
      k = reduced ? 1 : 1 - Math.exp(-dt / 110);
      a = focus && focus.vis ? 1 : 0;
      if (Math.abs(a - dim) > 0.004) { dim += (a - dim) * k; ovForce = true; dirty = true; } else dim = a;

      /* the three layers */
      var key = rot[0].toFixed(2) + "," + rot[1].toFixed(2);
      if (key !== baseKey) { baseKey = key; drawBase(); ovForce = true; }
      if (ovForce || now - ovWall >= (speed === 1 ? 1000 : 250) || simT < ovT) {
        drawOverlay(simT);
        ovForce = false; ovWall = now; ovT = simT;
      }
      ctx.clearRect(0, 0, size, size);
      ctx.drawImage(baseCv, 0, 0, size, size);
      ctx.drawImage(ovCv, 0, 0, size, size);

      /* the field site */
      pj(siteV[0], siteV[1], siteV[2]);
      siteVis = pd > 0.03; siteX = px; siteY = py;
      if (siteVis) {
        var sa = clamp(pd / 0.15, 0, 1), ph = reduced ? 0.42 : (now % 3200) / 3200;
        ctx.beginPath(); ctx.arc(siteX, siteY, 4.5 + 13 * (1 - (1 - ph) * (1 - ph)), 0, TAU);
        ctx.strokeStyle = "rgba(117,251,146," + (reduced ? 0.38 : 0.62 * (1 - ph) * (1 - ph)).toFixed(3) + ")";
        ctx.lineWidth = 1.3; ctx.globalAlpha = sa; ctx.stroke();
        ctx.beginPath(); ctx.arc(siteX, siteY, 5.2, 0, TAU); ctx.fillStyle = RING; ctx.fill();
        ctx.beginPath(); ctx.arc(siteX, siteY, 3.7, 0, TAU); ctx.fillStyle = MINT; ctx.fill();
        ctx.globalAlpha = 1;
      }

      drawLooks(now);

      /* each satellite: the bit of path flown since the paths were last drawn, then its dot */
      var iH = Math.floor(simT / STEP), j, g, fa;
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (i = byPri.length - 1; i >= 0; i--) {
        s = byPri[i];
        if (!s.vis || s.fam.a < 0.01) continue;
        fa = s.fam.a * (s === focus ? 1 : 1 - 0.6 * dim) * clamp(s.depth / 0.1, 0, 1);
        if (s.hv && simT > ovT && (Math.abs(s.x - s.hx) > 0.35 || Math.abs(s.y - s.hy) > 0.35)) {
          g = s.grid;
          ctx.beginPath(); ctx.moveTo(s.hx, s.hy);
          for (j = Math.floor(ovT / STEP) + 1; j <= iH; j++) { pjv(g.v, (j - g.i0) * 3); if (pd > 0) ctx.lineTo(px, py); }
          ctx.lineTo(s.x, s.y);
          ctx.strokeStyle = rgba(s.fam.rgb, 0.92 * s.fam.a * (s === focus ? 1 : 1 - 0.72 * dim));
          ctx.lineWidth = s === focus ? 2.3 : 1.6;
          ctx.stroke();
        }
        if (s === focus) continue;
        ctx.globalAlpha = fa;
        ctx.beginPath(); ctx.arc(s.x, s.y, dotR + 1.5, 0, TAU); ctx.fillStyle = RING; ctx.fill();
        ctx.beginPath(); ctx.arc(s.x, s.y, dotR, 0, TAU); ctx.fillStyle = s.fam.color; ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (focus && focus.vis) {
        s = focus;
        ctx.globalAlpha = clamp(s.depth / 0.1, 0, 1) * s.fam.a;
        ctx.beginPath(); ctx.arc(s.x, s.y, dotR + 5.6, 0, TAU);
        ctx.strokeStyle = "rgba(255,255,255,.9)"; ctx.lineWidth = 1.4; ctx.stroke();
        ctx.beginPath(); ctx.arc(s.x, s.y, dotR + 2.6, 0, TAU); ctx.fillStyle = RING; ctx.fill();
        ctx.beginPath(); ctx.arc(s.x, s.y, dotR + 1, 0, TAU); ctx.fillStyle = s.fam.color; ctx.fill();
        ctx.globalAlpha = 1;
      }

      /* the names */
      ctx.font = labelFont; ctx.textAlign = "left"; ctx.textBaseline = "middle";
      ctx.lineWidth = 3; ctx.strokeStyle = HALO;
      layout();
      labels = 0;
      k = reduced ? 1 : 1 - Math.exp(-dt / 90);
      for (i = byPri.length - 1; i >= -1; i--) {
        s = i < 0 ? focus : byPri[i];
        if (!s || (i >= 0 && s === focus)) continue;
        if (!s.vis) { s.la = 0; continue; }
        if (Math.abs(s.lt - s.la) > 0.02) { s.la += (s.lt - s.la) * k; dirty = true; } else s.la = s.lt;
        if (s.la < 0.02) continue;
        var text = s === focus ? s.name : s.tag;
        spot(s.side, s.x, s.y, textW(text), dotR);
        ctx.globalAlpha = s.la * s.fam.a * clamp(s.depth / 0.1, 0, 1) * (s === focus ? 1 : 1 - 0.5 * dim);
        ctx.strokeText(text, px, py + labelH / 2 + 0.5);
        ctx.fillStyle = INK;
        ctx.fillText(text, px, py + labelH / 2 + 0.5);
        labels++;
      }
      if (siteVis) {
        spot(siteSide, siteX, siteY, textW(SITE.name), 4);
        ctx.globalAlpha = clamp(pdSite() / 0.15, 0, 1);
        ctx.strokeText(SITE.name, px, py + labelH / 2 + 0.5);
        ctx.fillStyle = MINT;
        ctx.fillText(SITE.name, px, py + labelH / 2 + 0.5);
      }
      ctx.globalAlpha = 1;

      if (shown) { showAltitude(now); seat(); drawDdms(now); }
      a = perf() - c0;
      cost = cost ? cost * 0.94 + a * 0.06 : a;
    }
    function pdSite() { return m00 * siteV[0] + m01 * siteV[1] + m02 * siteV[2]; }

    function nearest(x, y, rad) {
      var best = null, bd = rad * rad, i, s, d;
      for (i = 0; i < sats.length; i++) {
        s = sats[i];
        if (!s.vis || !s.fam.on) continue;
        d = (s.x - x) * (s.x - x) + (s.y - y) * (s.y - y);
        if (d < bd || (d === bd && best && s.pri < best.pri)) { bd = d; best = s; }
      }
      return best;
    }

    /* ----- the loop: only while the square is on screen and the tab is in front ----- */

    function fail() {                              // an error while drawing: give the square back to the page
      destroy();
    }
    function guard(fn) {
      if (dead) return;
      try { fn(); } catch (e) { fail(); }
    }
    function continuous() { return !(reduced && speed === 1); }
    function frame(now) {
      raf = 0;
      if (dead || !running) return;
      dirty = false;
      try { step(now); } catch (e) { fail(); return; }
      if (running && (dirty || continuous())) raf = requestAnimationFrame(frame);
    }
    function invalidate() {
      dirty = true;
      if (running && !raf) raf = requestAnimationFrame(frame);
    }
    function pace() {                              // with reduced motion and the live clock: a frame every three seconds
      if (calm) { clearInterval(calm); calm = 0; }
      if (running && !continuous()) calm = setInterval(invalidate, 3000);
    }
    function run() {
      var r = !dead && onScreen && !D.hidden;
      if (r === running) return;
      running = r;
      if (r) { last = perf(); invalidate(); }
      else if (raf) { cancelAnimationFrame(raf); raf = 0; }
      pace();
    }

    /* ----- size ----- */

    function resize() {
      if (dead) return;
      var w = Math.floor(stage.getBoundingClientRect().width);
      var d = Math.min(W.devicePixelRatio || 1, 2);
      var wd = root.getBoundingClientRect().width >= WIDE;
      if (wd !== wide) {
        wide = wd;
        root.classList.toggle("ho-wide", wd);
        root.classList.toggle("ho-narrow", !wd);
        if (wd) stage.appendChild(card); else root.insertBefore(card, sourceLine);
        refocus();
      }
      if (w !== size || d !== dpr) {
        size = w; dpr = d;
        var pxs = Math.max(1, Math.round(w * d));
        [cv, baseCv, ovCv, seaCv, rimCv].forEach(function (c) { c.width = pxs; c.height = pxs; });
        cv.style.width = cv.style.height = w + "px";
        [ctx, bctx, octx, sctx, rctx].forEach(function (c) { c.setTransform(pxs / Math.max(w, 1), 0, 0, pxs / Math.max(w, 1), 0, 0); });
        gap = w >= WIDE ? 14 : w >= 380 ? 10 : 8;
        root.style.setProperty("--ho-gap", gap + "px");
        R = Math.max(10, w / 2 - gap); cx = cy = w / 2;
        proj.translate([cx, cy]).scale(R);
        dotR = w >= 480 ? 4.3 : w >= 340 ? 3.7 : 3.2;
        labelPx = w >= 480 ? 11.5 : 10.5; labelH = labelPx + 3.5;
        labelFont = "600 " + labelPx + "px \"Plus Jakarta\", sans-serif";
        widths = {};
        drawStill();
        baseKey = ""; ovForce = true;
      }
      measure();
      invalidate();
    }

    /* ----- pointer and keys ----- */

    function onDown(e) {
      if (e.button > 0 || (ptr && ptr.id !== e.pointerId)) return;
      var touch = e.pointerType === "touch";
      ptr = { id: e.pointerId, x: e.clientX, y: e.clientY, rot: rot.slice(), touch: touch, mode: "wait" };
      turn = null;
      if (!touch) { try { cv.setPointerCapture(e.pointerId); } catch (x) { /* fine without */ } }
    }
    function onMove(e) {
      if (e.pointerType !== "touch") {
        mouse = { x: e.offsetX, y: e.offsetY };
        if (!ptr) invalidate();
      }
      if (!ptr || e.pointerId !== ptr.id) return;
      var dx = e.clientX - ptr.x, dy = e.clientY - ptr.y;
      if (ptr.mode === "wait") {
        if (dx * dx + dy * dy < (ptr.touch ? 64 : 16)) return;
        /* A finger that sets off up or down is scrolling the page (touch-action: pan-y hands that to the
           browser, which then cancels this pointer); one that sets off sideways turns the globe. */
        if (ptr.touch && Math.abs(dy) > Math.abs(dx)) { ptr.mode = "scroll"; return; }
        ptr.mode = "turn"; ptr.x = e.clientX; ptr.y = e.clientY; dx = dy = 0;
        if (ptr.touch) { try { cv.setPointerCapture(e.pointerId); } catch (x) { /* fine without */ } }
      }
      if (ptr.mode !== "turn") return;
      var k = 72 / R;                              // degrees per px: the globe keeps up with the hand
      setRot([ptr.rot[0] + dx * k, clamp(ptr.rot[1] - dy * k, -89, 89)]);
      settle();
      invalidate();
    }
    function onUp(e) {
      if (!ptr || e.pointerId !== ptr.id) return;
      var was = ptr;
      ptr = null;
      if (was.mode === "wait") {                   // no drag: a click or a tap
        var s = nearest(e.offsetX, e.offsetY, was.touch ? 24 : 16);
        if (s) pin(s, false); else unpin();
      }
      invalidate();
    }
    function onCancel(e) {
      if (ptr && e.pointerId === ptr.id) { ptr = null; invalidate(); }
    }
    function onLeave(e) {
      if (e.pointerType !== "touch") { mouse = null; invalidate(); }
    }
    function onKey(e) {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      var k = e.key;
      if (k === "Escape" || k === "Esc") {
        if (pinned) { e.preventDefault(); unpin(); }
      } else if (e.target === globe && (k === "ArrowRight" || k === "Right" || k === "ArrowLeft" || k === "Left")) {
        e.preventDefault();
        stepPick(k === "ArrowRight" || k === "Right" ? 1 : -1);
      }
    }
    function listen(node, type, fn) { node.addEventListener(type, function (e) { guard(function () { fn(e); }); }); }
    listen(cv, "pointerdown", onDown);
    listen(cv, "pointermove", onMove);
    listen(cv, "pointerup", onUp);
    listen(cv, "pointercancel", onCancel);
    listen(cv, "lostpointercapture", onCancel);
    listen(cv, "pointerleave", onLeave);
    listen(root, "keydown", onKey);
    listen(bLive, "click", function () { setSpeed(1); });
    listen(bFast, "click", function () { setSpeed(FAST); });
    listen(bHome, "click", function () { turnTo(HOME.slice(), 650); });
    listen(cClose, "click", function () { globe.focus(); unpin(); });

    /* ----- newer elements, when the file is old ----- */

    function refresh() {
      freshTimer = 0;
      if (dead) return;
      var found = {}, want = {};
      sats.forEach(function (s) { want[s.norad] = true; });
      var urls = CELESTRAK_GROUPS.map(function (g) { return CELESTRAK + "GROUP=" + g + "&FORMAT=tle"; })
        .concat(CELESTRAK_CATNR.map(function (id) { return CELESTRAK + "CATNR=" + id + "&FORMAT=tle"; }));
      Promise.all(urls.map(function (u) {
        return get(u, 12000, "text", holds).then(function (text) {
          var lines = String(text).split(/\r?\n/), i, id;
          for (i = 0; i + 1 < lines.length; i++) {
            if (lines[i].slice(0, 2) !== "1 " || lines[i + 1].slice(0, 2) !== "2 ") continue;
            id = parseInt(lines[i].slice(2, 7), 10);
            if (want[id] === true && record([lines[i], lines[i + 1]], id)) found[id] = [lines[i].replace(/\s+$/, ""), lines[i + 1].replace(/\s+$/, "")];
          }
        }, function () { /* this request failed: the others may not have */ });
      })).then(function () {
        if (dead) return;
        var mine = {}, n = 0;
        sats.forEach(function (s) { if (found[s.norad]) { mine[s.norad] = found[s.norad]; n++; } });
        if (!n) return;
        try { localStorage.setItem(MEMORY, JSON.stringify({ at: Date.now(), tle: mine })); } catch (e) { /* no storage: fine */ }
        if (take(mine, true)) {
          source = "celestrak";
          guard(function () { describe(); ovForce = true; invalidate(); });
        }
      }).then(null, function () { /* silent: what is shown stays */ });
    }

    /* ----- start ----- */

    var ro = null, io = null;
    function onVisible() { guard(run); }
    function onWindow() { guard(resize); }
    function onFonts() { widths = {}; guard(measure); invalidate(); }

    function destroy() {
      if (dead) return;
      dead = true; running = false;
      if (raf) cancelAnimationFrame(raf);
      if (calm) clearInterval(calm);
      if (freshTimer) clearTimeout(freshTimer);
      holds.forEach(function (c) { try { c.abort(); } catch (e) { /* done already */ } });
      if (ro) ro.disconnect();
      if (io) io.disconnect();
      D.removeEventListener("visibilitychange", onVisible);
      W.removeEventListener("resize", onWindow);
      if (D.fonts && D.fonts.removeEventListener) D.fonts.removeEventListener("loadingdone", onFonts);
      if (root.parentNode) root.parentNode.removeChild(root);
      try { el.setAttribute("data-orbit", "off"); } catch (e) { /* nothing to do */ }
      mounts.delete(el);
      var i = instances.indexOf(api);
      if (i >= 0) instances.splice(i, 1);
    }

    var api = {
      handle: { destroy: destroy },
      state: function () {
        var total = 0, on = 0, f = {};
        sats.forEach(function (s) { if (s.rec) { total++; if (s.fam.on) on++; } });
        famList.forEach(function (x) { f[x.id] = x.on; });
        return {
          total: total, shown: on, drawn: drawn, labels: labels, families: f,
          simTime: simT, speed: speed, live: speed === 1, picked: pinned ? pinned.key : null,
          hover: hover ? hover.key : null, card: shown ? shown.key : null,
          rot: [rot[0], rot[1]], turned: away, running: running, reduced: reduced, wide: wide,
          size: size, dpr: dpr, frames: frames, frameMs: cost,
          elements: { source: source, at: elementsAt(), fileAt: fileAt },
          swaths: { cells: cells, filling: !!fill, fillMs: fillMs, dataMs: dataMs, res: dRes },
          sun: sunAt(simT),
          sats: sats.filter(function (s) { return s.rec; }).map(function (s) {
            return { key: s.key, name: s.name, family: s.fam.id, visible: s.vis && s.fam.on, x: s.x, y: s.y,
                     lat: s.ok ? Math.asin(clamp(s.ez, -1, 1)) / DEG : null, lon: s.ok ? Math.atan2(s.ey, s.ex) / DEG : null };
          })
        };
      },
      subpoint: function (key, ms) { var s = byKey[key]; return s && s.rec ? geoAt(s.rec, ms) : null; }
    };

    try {
      setRot(HOME.slice());
      describe();
      showSpeed();
      el.appendChild(root);
      resize();
      step(perf());
    } catch (e) {
      if (root.parentNode) root.parentNode.removeChild(root);
      throw e;
    }
    el.setAttribute("data-orbit", "on");
    instances.push(api);

    /* The square is watched, not the whole of the globe's markup: what resize() changes (the clock and the card
       moving in or out of the square) leaves the square's size alone, so the observer is never called in a loop. */
    if (typeof ResizeObserver === "function") { ro = new ResizeObserver(function () { guard(resize); }); ro.observe(stage); }
    W.addEventListener("resize", onWindow);
    if (typeof IntersectionObserver === "function") {
      io = new IntersectionObserver(function (list) {
        onScreen = list[list.length - 1].isIntersecting;
        guard(run);
      });
      io.observe(root);
    }
    D.addEventListener("visibilitychange", onVisible);
    if (D.fonts) {
      if (D.fonts.addEventListener) D.fonts.addEventListener("loadingdone", onFonts);
      if (D.fonts.load) {
        try { D.fonts.load("600 12px \"Plus Jakarta\"").then(onFonts, function () { /* the fallback font is fine */ }); } catch (e) { /* fine */ }
      }
    }
    run();
    if (wantFresh) freshTimer = setTimeout(refresh, 1500);

    return api.handle;
  }

  W.HydroOrbit = {
    mount: mount,
    _state: function () { var i = instances[instances.length - 1]; return i ? i.state() : null; },
    _subpoint: function (key, ms) { var i = instances[instances.length - 1]; return i ? i.subpoint(key, ms) : null; }
  };
})();
