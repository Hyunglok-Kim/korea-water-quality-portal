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
    var cFar = h("div", "ho-far", "Out of view: over the far side of the globe.");
    cFar.hidden = true;
    var cLink = h("a", "ho-link");
    cLink.target = "_blank"; cLink.rel = "noopener";
    cLink.appendChild(D.createTextNode("Mission page"));
    cLink.appendChild(icon(12, "M4 10L10 4M5 4h5v5"));
    var cClose = h("button", "ho-x");
    cClose.type = "button"; cClose.hidden = true; cClose.setAttribute("aria-label", "Close");
    cClose.appendChild(icon(12, "M3 3l8 8M11 3l-8 8"));
    box.appendChild(cFam); box.appendChild(cName); box.appendChild(cAgency); box.appendChild(facts);
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
        (isFinite(at) ? " of " + dateText(at) + "." : ".");
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
      cLink.setAttribute("aria-label", s.name + " mission page (opens in a new tab)");
      altShown = ""; altAt = 0; farShown = false; cFar.hidden = true;
      showAltitude(perf());
      cClose.hidden = s !== pinned;
      card.classList.toggle("ho-pinned", s === pinned);
      box.hidden = false;
      measure();
      seat();
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

      if (shown) { showAltitude(now); seat(); }
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
