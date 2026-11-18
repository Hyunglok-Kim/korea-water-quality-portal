/* Korea inland water quality data portal — single-page app, no build step.

   How the map gets its data
     The product is sparse: a 470 x 510 grid on which 8,558 cells ever carry a value, and 1.53 million
     cell-values per layer in all. So the browser reads the numbers themselves, not pictures of them.
     catalog.json lists the cells, the 1,012 dates and how the 16-bit numbers decode. Two PMTiles archives,
     used as range-readable key-value stores, hold the rest:
       fields store   by date — one entry per layer and year (plus the cells that had a value on each
                      date), and one per layer with the record and calendar-month means;
       series store   by cell — one entry per cell with every overpass, both bands of all six parameters.
     The cells are drawn as the 1 km squares they are (as dots when seen from afar), coloured through
     feature state, so the cursor readout is the stored value and a click needs one small request. */
(() => {
"use strict";

/* ───────────────────────────── configuration ───────────────────────────── */
const CFG = Object.assign({ dataBase: "./data/", zenodoDoi: "", conceptDoi: "", contactEmail: "", dataContact: "", nasPath: "", paperSection: "text" }, window.PORTAL_CONFIG || {});
const Q = new URLSearchParams(location.search);
{
  const d = Q.get("data");                       // same-origin absolute path only
  if (d && /^\/(?!\/)[\w\-./]*\/$/.test(d)) CFG.dataBase = d;
  const nas = Q.get("nas");                      // lab storage path, shown on the internal copy
  if (nas && /^\/[\w\-./]+$/.test(nas)) CFG.nasPath = nas;
}
const EMBED = Q.get("embed") === "1";
if (EMBED) document.documentElement.classList.add("embed");
if (Q.get("hidefooter") === "1") document.body.classList.add("hide-footer");   // as on the other HydroAI portals
const DATA = new URL(CFG.dataBase, location.href).href;
/* "From the paper": "figures" (text with the manuscript's figures), "text" (text and this site's own charts), "off".
   ?paper= overrides the setting, e.g. on the lab's own copy, where the figure files are. */
const PAPER = (() => {
  const q = Q.get("paper"), v = q != null ? q : CFG.paperSection;
  return v === true || v === "figures" ? "figures" : v === false || v === "off" || v === "0" ? "off" : "text";
})();
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const INTRO = !REDUCED && Q.get("intro") !== "0";   // opening sequence: in from the globe, data fades up, cards rise

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
/* Colour ramps for a dark map: lightness rises with the value (checked to be monotonic), so high values stand
   out and no value disappears into the basemap. One ramp per parameter, so the layers are told apart at a
   glance; water temperature and chlorophyll-a use the ramps of the paper's own product figure. */
const RAMPS = {
  wt: ["#4a0c6b", "#71196e", "#972766", "#bc3754", "#db503b", "#f1731d", "#fb9d07", "#f9cb35", "#f3f68a"].map(hex),     // inferno
  ss: ["#553c2b", "#784a20", "#965b12", "#b0710d", "#c58a27", "#d5a54c", "#e3c076", "#f0dba4", "#fef6d4"].map(hex),     // umber to sand: clear water stays dark, turbid water is bright
  chla: ["#433e85", "#375b8d", "#2b748e", "#228d8d", "#21a685", "#40bd72", "#77d153", "#bade28", "#fde725"].map(hex),   // viridis
  do: ["#084a91", "#1865ac", "#3181bd", "#4f9bcb", "#74b3d8", "#9dcae1", "#bfd8ed", "#d6e6f4", "#ebf3fb"].map(hex),
  tn: ["#4c1888", "#5e3a98", "#705ca9", "#8380bb", "#9c98c7", "#b4b4d7", "#cdcde4", "#e2e2ef", "#f2f0f7"].map(hex),
  tp: ["#6f0174", "#9b017b", "#c4198a", "#e5459a", "#f871a4", "#fa9eb5", "#fcbfbe", "#fdd7d4", "#feece9"].map(hex),
  sigma: ["#5a5a5a", "#707070", "#888888", "#a2a2a2", "#bdbdbd", "#d1d1d1", "#e2e2e2", "#f1f1f1", "#fcfcfc"].map(hex),  // every uncertainty layer: no hue
  n: ["#005321", "#087432", "#268f4a", "#3fac74", "#5ebe9b", "#87d0bc", "#b2e2d7", "#d5efed", "#e9f7fa"].map(hex),
};
/* The six parameters, in the order of the files and of the stores' layers (layer = 2 x index, +1 for sigma).
   fixed / sfixed: colour-scale range of the value and of its uncertainty, close to the 2nd–98th percentile of the
   whole record; log: trained and drawn on a logarithmic scale. */
const ORDER = ["wt", "ss", "chla", "do", "tn", "tp"];
const PARAMS = {
  wt: { name: "Water temperature", short: "WT", units: "°C", log: false, fixed: [0, 30], sfixed: [1, 4], kind: "met" },
  ss: { name: "Suspended solids", short: "SS", units: "mg/L", log: true, fixed: [1, 30], sfixed: [1, 50], kind: "opt" },
  chla: { name: "Chlorophyll-a", short: "Chl-a", units: "µg/L", log: true, fixed: [2, 60], sfixed: [2, 100], kind: "opt" },
  do: { name: "Dissolved oxygen", short: "DO", units: "mg/L", log: false, fixed: [6, 14], sfixed: [1.2, 2.4], kind: "met" },
  tn: { name: "Total nitrogen", short: "TN", units: "mg/L", log: true, fixed: [0.7, 5], sfixed: [0.5, 5], kind: "ctx" },
  tp: { name: "Total phosphorus", short: "TP", units: "mg/L", log: true, fixed: [0.01, 0.15], sfixed: [0.01, 0.1], kind: "opt" },
};
const KINDS = { opt: "Optical retrieval", ctx: "Catchment-context estimate", met: "Meteorologically driven" };
/* How to read each layer, from the paper's Technical Validation and Usage Notes. Shown under the layer card.
   The R² in brackets is read from skill.json (computed from the record's validation file) and left out if that
   file is not there. For total nitrogen the mapped value, the mean of the dropout passes, scores lower than the
   network's single prediction, and both are given. */
let SKILL = null;
const sk = (p, k, d = 2) => SKILL.params[p][k].toFixed(d);
const through = (p) => (SKILL ? ` (R² ${sk(p, "within")} following one place through time)` : "");
const HOWTO = {
  wt: () => `Usable as a series at a fixed place${through("wt")}, though nearly all of that skill comes from the calendar and the weather, not from the satellite.`,
  do: () => `Usable as a series at a fixed place${through("do")}, weakest in summer. The satellite adds little to it.`,
  ss: () => `A screening layer: compare water bodies and locate turbid water on a date. It follows one place through time only weakly${SKILL ? ` (R² ${sk("ss", "within")})` : ""}, and high values are understated.`,
  chla: () => `A screening layer: compare water bodies and locate elevated algal biomass on a date. It follows one place through time only weakly${SKILL ? ` (R² ${sk("chla", "within")})` : ""}, and high values are understated.`,
  tp: () => `A screening layer: it ranks water bodies but hardly follows one place through time${SKILL ? ` (R² ${sk("tp", "within")})` : ""}, and it never exceeds 0.174 mg/L although measurements go far higher.`,
  tn: () => `Inferred from the land around the water, not from its colour. Read it as a contrast between water bodies, not as a series at one place${SKILL ? ` (R² ${sk("tn", "within")}; ${sk("tn", "within_mu")} for the mapped mean)` : ""}.`,
};
/* Multipliers of sigma_cal for a 95 % interval, from kr_wq_1km_metadata.json of the record
   (uncertainty_asymmetric.multipliers): lower = mu + q_lower x sigma (floored at zero where clip), upper = mu + q_upper x sigma. */
const CI = { wt: [-2.0697, 2.0182, false], ss: [-0.6909, 1.8599, true], chla: [-0.7627, 2.2456, true],
  do: [-2.1787, 2.1054, false], tn: [-1.1173, 2.4608, true], tp: [-0.6409, 1.5452, true] };
const N_WATER = 13469;                      // cells with predictable water: the ceiling of the product (Data Descriptor)
const SERIES = "#2a78d6", CONTEXT = "#8C8A80";   // the one data hue of the charts, and the de-emphasised comparison
const COVER_STEPS = ["#D6E4F7", "#A9C8EF", "#6FA5E3", "#2a78d6", "#1c5cab"];   // one hue, light → dark
const PT_COLORS = ["#3987e5", "#d95926", "#199e70"], PT_TYPES = ["river", "reservoir", "lake or dam"];   // validated as a set (CVD and normal vision)
/* Places for the "Go to…" list. Lakes and reaches: centres of the product's own cells there. Points: the six
   monitoring points of the paper's Fig. 7, at their published WEIS coordinates. */
const LAKES = [["Soyang Lake", 127.90, 37.95], ["Paldang Lake", 127.33, 37.52], ["Chungju Lake", 128.12, 36.98], ["Daecheong Lake", 127.53, 36.41],
  ["Andong and Imha lakes", 128.88, 36.56], ["Yongdam Lake", 127.50, 35.91], ["Okjeong Lake", 127.10, 35.58], ["Hapcheon Lake", 128.03, 35.58],
  ["Jinyang Lake", 128.00, 35.17], ["Juam Lake", 127.21, 35.00]];
const REACHES = [["Han River at Seoul", 127.03, 37.53], ["Nakdong River near Daegu", 128.44, 35.84], ["Nakdong River estuary", 128.94, 35.16],
  ["Geum River estuary", 126.81, 36.04], ["Yeongsan Lake (estuarine: read with caution)", 126.52, 34.82]];
const POINTS = [["Jusu Stream", "1302A40", 129.04167, 37.61361], ["Yangsan Stream 2", "2022A20", 129.02889, 35.34417], ["Muan 2", "5008A10", 126.44861, 34.78639],
  ["Gyeongpo Lake 1", "1302B10", 128.91028, 37.79861], ["Daeho 2", "3201B20", 126.48222, 36.97333], ["Naju Dam 2", "5003B10", 126.84861, 34.92750]];
const POINT_NAME = Object.fromEntries(POINTS.map((p) => [p[1], p[0]]));
const CITIES = [["Seoul", 126.978, 37.5665], ["Busan", 129.0756, 35.1796], ["Daegu", 128.6014, 35.8714], ["Daejeon", 127.3845, 36.3504],
  ["Gwangju", 126.8526, 35.1595], ["Gangneung", 128.8761, 37.7519]];
const HOME = [[125.95, 34.2], [129.65, 38.2]];    // the cells' extent with a margin

/* ───────────────────────────── small helpers ───────────────────────────── */
const $ = (s) => document.querySelector(s);
function el(tag, attrs, kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") n.className = v;
    else if (k.startsWith("on")) n.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) n.setAttribute(k, v === true ? "" : v);
  }
  for (const c of [].concat(kids == null ? [] : kids)) n.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return n;
}
const svgEl = (tag, attrs) => {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
  return n;
};
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const fmt = (v, d = 0) => (v == null || Number.isNaN(v) ? "—" : v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }));
/* Three significant digits: 12.4, 7.56, 0.0246, 1,074 */
function sig(v, n = 3) {
  if (v == null || Number.isNaN(v)) return "—";
  if (v === 0) return "0";
  const d = clamp(n - 1 - Math.floor(Math.log10(Math.abs(v))), 0, 6);
  return v.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
}
const tick = (v) => String(+v.toPrecision(6));             // axis and legend ticks: 0.05, 2.5, 100
const pad2 = (n) => String(n).padStart(2, "0");
const ymLabel = (ym) => `${MONL[+ym.slice(5, 7) - 1]} ${ym.slice(0, 4)}`;
const dLabel = (d) => `${+d.slice(8, 10)} ${MON[+d.slice(5, 7) - 1]} ${d.slice(0, 4)}`;
function fmtBytes(b) { return b >= 1e9 ? (b / 1e9).toFixed(2) + " GB" : b >= 1e6 ? (b / 1e6).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1e3)) + " KB"; }
const DAY0 = Date.UTC(2016, 0, 1);
const dayNum = (iso) => Math.round((Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)) - DAY0) / 86400e3);
function niceStep(x) {
  const p = Math.pow(10, Math.floor(Math.log10(x))), n = x / p;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p;
}
/* 1-2-5 values around a range, for logarithmic scales */
function oneTwoFive(lo, hi) {
  const out = [];
  for (let k = Math.floor(Math.log10(lo)) - 1; k <= Math.ceil(Math.log10(hi)) + 1; k++) for (const m of [1, 2, 5]) out.push(+(m * Math.pow(10, k)).toPrecision(6));
  return out;
}
/* a finer set of round values, for a colour scale stretched to the data: 1, 1.5, 2, 3, 4, 5, 6, 8 */
function manyRound(lo, hi) {
  const out = [];
  for (let k = Math.floor(Math.log10(lo)) - 1; k <= Math.ceil(Math.log10(hi)) + 1; k++) for (const m of [1, 1.5, 2, 3, 4, 5, 6, 8]) out.push(+(m * Math.pow(10, k)).toPrecision(6));
  return out;
}
function logBounds(lo, hi, fine) {
  const c = fine ? manyRound(lo, hi) : oneTwoFive(lo, hi);
  let a = c[0], b = c[c.length - 1];
  for (const v of c) { if (v <= lo * 1.0001) a = v; }
  for (let i = c.length - 1; i >= 0; i--) { if (c[i] >= hi * 0.9999) b = c[i]; }
  if (b <= a) b = c[c.indexOf(a) + 1];
  return [a, b];
}
function download(name, text, type) {
  const a = el("a", { href: URL.createObjectURL(new Blob([text], { type })), download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
async function copyText(text, btn) {
  try { await navigator.clipboard.writeText(text); } catch {
    const t = el("textarea", { style: "position:fixed;opacity:0" }, text); document.body.append(t); t.select();
    document.execCommand("copy"); t.remove();
  }
  if (btn) { const old = btn.textContent; btn.textContent = "Copied"; setTimeout(() => { btn.textContent = old; }, 1400); }
}
const tip = $("#tip");
function showTip(nodes, x, y) {
  tip.replaceChildren(...nodes); tip.hidden = false;
  const r = tip.getBoundingClientRect();
  tip.style.left = clamp(x + 14, 6, innerWidth - r.width - 6) + "px";
  tip.style.top = clamp(y - r.height - 12 < 6 ? y + 16 : y - r.height - 12, 6, innerHeight - r.height - 6) + "px";
}
const hideTip = () => { tip.hidden = true; };

/* ───────────────────────────── state ───────────────────────────── */
let CAT = null, map = null, mapReady = false, pickMarker = null, placeMarker = null;
let C = 0, W = 0, H = 0, G = null, cellRow = null, cellCol = null, cellOf = null;
let dISO = [], dN = [], dDay = [], offInYear = [], dIndex = new Map(), ymDates = new Map(), monthByYm = new Map();
const state = { var: "chla", band: "mu", mode: "all", climMonth: 8, ym: null, date: null, scale: "fixed", pick: null, seriesYear: null, playing: null, pts: false, opacity: 1 };
let chartModel = null, recordModel = null, current = null, flagText = "";

/* ───────────────────────────── catalog ───────────────────────────── */
async function loadCatalog() {
  const r = await fetch(DATA + "catalog.json", { cache: "no-cache" });
  if (r.status === 401 || r.status === 403) {
    if (window.parent !== window) window.parent.postMessage({ type: "portalAuth" }, "*");
    throw new Error("Sign-in required — open this page from the lab dashboard.");
  }
  if (!r.ok) throw new Error(`Could not load the catalog (HTTP ${r.status}).`);
  CAT = await r.json();
  G = CAT.grid; C = CAT.cells.n; W = G.width; H = G.height;
  cellRow = Int16Array.from(CAT.cells.row); cellCol = Int16Array.from(CAT.cells.col);
  cellOf = new Int32Array(W * H).fill(-1);
  for (let i = 0; i < C; i++) cellOf[cellRow[i] * W + cellCol[i]] = i;
  dISO = CAT.dates.d.map((d) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}`);
  dN = CAT.dates.n; dDay = dISO.map(dayNum);
  let off = 0, yPrev = "";
  dISO.forEach((d, i) => {
    if (d.slice(0, 4) !== yPrev) { off = 0; yPrev = d.slice(0, 4); }
    offInYear[i] = off; off += dN[i];
    dIndex.set(d, i);
    const ym = d.slice(0, 7);
    if (!ymDates.has(ym)) ymDates.set(ym, []);
    ymDates.get(ym).push(i);
  });
  monthByYm = new Map(CAT.months.map((m) => [m.ym, m]));
  /* Opens on the date of the paper's product figure (3 December 2023) when the Date view is chosen. */
  state.date = dIndex.has("2023-12-03") ? "2023-12-03" : dISO[dN.indexOf(Math.max(...dN))];
  const vq = Q.get("var"); if (vq && (PARAMS[vq] || vq === "n")) state.var = vq;
  if (Q.get("band") === "sigma" && state.var !== "n") state.band = "sigma";
  const mq = Q.get("mode"); if (["all", "clim", "month", "date"].includes(mq)) state.mode = mq;
  const cm = +Q.get("month"); if (cm >= 1 && cm <= 12) state.climMonth = cm;
  const dq = Q.get("date");
  if (dq && /^\d{4}-\d{2}-\d{2}$/.test(dq)) {
    state.mode = "date"; state.date = dIndex.has(dq) ? dq : nearestDate(dq);
    if (state.date !== dq) flagText = `${dLabel(dq)} has no grid — showing ${dLabel(state.date)}, the nearest overpass with one.`;
  }
  state.ym = state.date.slice(0, 7);
  const yq = Q.get("ym"); if (yq && ymDates.has(yq)) { state.ym = yq; if (!dq) { state.mode = mq || "month"; state.date = dISO[ymDates.get(yq)[0]]; } }
  state.seriesYear = state.ym.slice(0, 4);
  if (state.var === "n" && state.mode === "date") state.mode = "month";
}
const P = () => PARAMS[state.var];
const YEARS = () => CAT.years.map((y) => String(y.year));
const RECORD_YEARS = () => `${CAT.record.first.slice(0, 4)}–${CAT.record.last.slice(0, 4)}`;
function nearestDate(iso) {
  const t = dayNum(iso);
  let best = 0;
  for (let i = 1; i < dDay.length; i++) if (Math.abs(dDay[i] - t) < Math.abs(dDay[best] - t)) best = i;
  return dISO[best];
}

/* What is on the map. L is the store's layer (-1 for the count of dates). */
function layerSpec() {
  const v = state.var, isN = v === "n", band = isN ? "mu" : state.band;
  const spec = { var: v, band, isN, mode: state.mode, L: isN ? -1 : ORDER.indexOf(v) * 2 + (band === "sigma" ? 1 : 0),
    climMonth: state.climMonth, ym: state.ym, date: state.date };
  spec.log = !isN && PARAMS[v].log;
  spec.units = isN ? "dates" : PARAMS[v].units;
  spec.key = `${v}|${band}|${state.mode}|${state.mode === "all" ? "" : state.mode === "clim" ? pad2(state.climMonth) : state.mode === "month" ? state.ym : state.date}`;
  return spec;
}
function currentRange(spec, st) {
  if (state.scale === "fixed" || st.n < 2) {
    if (spec.isN) return spec.mode === "all" ? [0, 400] : spec.mode === "clim" ? [0, 60] : [0, 12];
    return spec.band === "mu" ? PARAMS[spec.var].fixed : PARAMS[spec.var].sfixed;
  }
  if (spec.log) return logBounds(st.p02, st.p98, true);
  const step = spec.isN ? Math.max(1, niceStep((st.p98 - st.p02) / 4 || 1)) : niceStep((st.p98 - st.p02) / 4 || 1);
  const lo = Math.floor(st.p02 / step) * step, hi = Math.ceil(st.p98 / step) * step;
  return [lo, hi > lo ? hi : lo + step];
}

/* ───────────────────────────── the stores ───────────────────────────── */
let fieldsArc = null, seriesArc = null;
const entries = new Map(), luts = new Map();
function openStores() {
  fieldsArc = new pmtiles.PMTiles(new pmtiles.FetchSource(DATA + CAT.store.fields.file));
  seriesArc = new pmtiles.PMTiles(new pmtiles.FetchSource(DATA + CAT.store.series.file));
}
/* One entry of the fields store as 16-bit numbers. pmtiles.js inflates the gzip itself. */
function fieldEntry(x, y) {
  const k = `${x}/${y}`;
  let p = entries.get(k);
  if (!p) {
    p = fieldsArc.getZxy(CAT.store.zoom, x, y).then((res) => {
      if (!res || !res.data || !res.data.byteLength) throw new Error(`the fields store has no entry ${k}`);
      return new Uint16Array(res.data);
    });
    p.catch(() => entries.delete(k));
    entries.set(k, p);
  }
  return p;
}
/* DN -> value for a layer: 65,536 values, built once. */
function lut(L) {
  let t = luts.get(L);
  if (!t) {
    const e = CAT.layers[L];
    t = new Float32Array(65536);
    if (e.enc === "lin") for (let i = 0; i < 65535; i++) t[i] = i * e.scale + e.offset;
    else for (let i = 0; i < 65535; i++) t[i] = e.v0 * Math.exp(i * e.k);
    t[CAT.store.nodata] = NaN;
    luts.set(L, t);
  }
  return t;
}
/* The values to draw: Float32Array[cells], NaN where the cell has none. */
const displays = new Map();
function getDisplay(spec) {
  let p = displays.get(spec.key);
  if (p) { displays.delete(spec.key); displays.set(spec.key, p); return p; }
  p = computeDisplay(spec);
  p.catch(() => displays.delete(spec.key));
  displays.set(spec.key, p);
  if (displays.size > 90) displays.delete(displays.keys().next().value);
  return p;
}
async function computeDisplay(spec) {
  const vals = new Float32Array(C).fill(NaN), F = CAT.store.fields;
  if (spec.mode === "all" || spec.mode === "clim") {
    const o = (spec.mode === "all" ? 0 : spec.climMonth) * C;
    if (spec.isN) { const cnt = await fieldEntry(F.x_count, F.y_clim); for (let c = 0; c < C; c++) if (cnt[o + c]) vals[c] = cnt[o + c]; }
    else { const dn = await fieldEntry(spec.L, F.y_clim), t = lut(spec.L); for (let c = 0; c < C; c++) vals[c] = t[dn[o + c]]; }
    return vals;
  }
  const idx = spec.mode === "date" ? [dIndex.get(spec.date)] : (ymDates.get(spec.ym) || []);
  if (!idx.length || idx[0] == null) return vals;
  const yi = +dISO[idx[0]].slice(0, 4) - CAT.store.year0;
  const [mask, dn] = await Promise.all([fieldEntry(F.x_mask, yi), spec.isN ? null : fieldEntry(spec.L, yi)]);
  if (dn && dn.length !== mask.length) throw new Error("fields store: a layer and its mask differ in length");
  if (spec.mode === "date") {
    const t = lut(spec.L), a = offInYear[idx[0]], b = a + dN[idx[0]];
    for (let j = a; j < b; j++) vals[mask[j]] = t[dn[j]];
    return vals;
  }
  const sum = new Float64Array(C), cnt = new Uint16Array(C), t = spec.isN ? null : lut(spec.L);
  for (const i of idx) for (let j = offInYear[i], b = j + dN[i]; j < b; j++) { cnt[mask[j]]++; if (t) sum[mask[j]] += t[dn[j]]; }
  for (let c = 0; c < C; c++) if (cnt[c]) vals[c] = spec.isN ? cnt[c] : sum[c] / cnt[c];
  return vals;
}
function fieldStats(vals) {
  const a = [];
  for (let c = 0; c < C; c++) if (!Number.isNaN(vals[c])) a.push(vals[c]);
  const s = Float32Array.from(a).sort(), n = s.length, q = (p) => (n ? s[Math.min(n - 1, Math.round(p * (n - 1)))] : NaN);
  return { n, median: q(0.5), p02: q(0.02), p98: q(0.98), min: n ? s[0] : NaN, max: n ? s[n - 1] : NaN };
}

/* ───────────────────────────── colouring ─────────────────────────────
   Each cell's position on the colour ramp (0..1, or -1 for no value) is its feature state "t"; the layers'
   paint reads it. Changing the layer touches only the cells whose position changed. */
let tPrev = null;
const T_OF = ["coalesce", ["feature-state", "t"], -1];
const HAS = [">=", T_OF, 0];
function rampExpr(ramp) {
  const e = ["interpolate", ["linear"], ["max", T_OF, 0]];
  ramp.forEach((c, i) => e.push(i / (ramp.length - 1), `rgb(${c.join(",")})`));
  return e;
}
const rampOf = (spec) => (spec.isN ? RAMPS.n : spec.band === "sigma" ? RAMPS.sigma : RAMPS[spec.var]);
const fillOpacity = (op) => ["interpolate", ["linear"], ["zoom"], 7.5, 0, 8.4, ["case", HAS, op, 0]];
const dotOpacity = (op) => ["interpolate", ["linear"], ["zoom"], 7.7, ["case", HAS, op, 0], 8.6, 0];
function norm(spec, lo, hi) {
  if (spec.log) { const a = Math.log(lo), d = Math.log(hi) - a; return (v) => clamp((Math.log(v) - a) / d, 0, 1); }
  const d = hi - lo; return (v) => clamp((v - lo) / d, 0, 1);
}
let rampKey = "";
function paint() {
  if (!mapReady || !current || !current.vals) return;
  const { spec, vals, lo, hi } = current, f = norm(spec, lo, hi), key = spec.isN ? "n" : spec.band === "sigma" ? "sigma" : spec.var;
  if (key !== rampKey) {
    const e = rampExpr(rampOf(spec));
    map.setPaintProperty("cells-fill", "fill-color", e); map.setPaintProperty("cells-fill", "fill-outline-color", e); map.setPaintProperty("cells-dot", "circle-color", e);
    rampKey = key;
  }
  if (!tPrev) tPrev = new Float32Array(C).fill(-2);
  for (let c = 0; c < C; c++) {
    const v = vals[c], t = Number.isNaN(v) ? -1 : Math.round(f(v) * 1000) / 1000;
    if (t !== tPrev[c]) { tPrev[c] = t; map.setFeatureState({ source: "cells", id: c }, { t }); map.setFeatureState({ source: "dots", id: c }, { t }); }
  }
}
function setOpacity(op) {
  state.opacity = op;
  if (!mapReady) return;
  map.setPaintProperty("cells-fill", "fill-opacity", fillOpacity(op));
  map.setPaintProperty("cells-dot", "circle-opacity", dotOpacity(op));
  map.setPaintProperty("cells-dot", "circle-stroke-opacity", dotOpacity(op * 0.6));
  map.setPaintProperty("cells-line", "line-opacity", ["case", HAS, op, 0]);
}

/* Switch the map to the layer the controls describe. Fetches the numbers first so the statistics, legend and card agree. */
let applySeq = 0;
async function applyLayer() {
  const seq = ++applySeq, spec = layerSpec();
  renderWhen(); renderCalendar();
  let vals = null, err = "";
  try { vals = await getDisplay(spec); } catch (e) { console.warn("[fields]", e.message); err = e.message; }
  if (seq !== applySeq) return;
  const st = vals ? fieldStats(vals) : { n: 0, median: NaN, p02: NaN, p98: NaN };
  const [lo, hi] = currentRange(spec, st);
  current = { spec, vals, stats: st, lo, hi, err };
  paint();
  renderLayerCard(); renderLegend();
  if (!state.pick) renderNational(); else renderPickCharts();
}

/* ───────────────────────────── map ───────────────────────────── */
/* MapLibre draws with WebGL and has no other way. Where the browser gives no WebGL context — graphics
   acceleration switched off, or lost (Chrome switches it off for the rest of the session once its graphics
   process has failed a few times, and no longer falls back to drawing in software) — there can be no map.
   The page then says so in the map's place instead of sitting on its loading screen for ever. Everything on
   it that is not the map still works: applyLayer allows for there being no map. */
function webglWorks() {
  try {
    const c = document.createElement("canvas"), gl = c.getContext("webgl2") || c.getContext("webgl");
    if (!gl) return false;
    const lose = gl.getExtension("WEBGL_lose_context");
    if (lose) lose.loseContext();                                  // hand the test context back
    return true;
  } catch (e) { return false; }
}
function handle() {
  return { map, state, CAT: () => CAT, current: () => current, getDisplay, layerSpec, getSeries, cellAt, pickCell, cellIndex: (row, col) => cellOf[row * W + col],
    ready: () => mapReady, lut };
}
function noMap(on, why) {
  document.documentElement.classList.toggle("nomap", on);
  $("#noMap").hidden = !on;
  const boot = $("#boot");
  if (boot) { boot.classList.add("out"); setTimeout(() => boot.remove(), 500); }
  if (on && why) console.warn("[map] not drawn:", why);
  if (!window.__portal) window.__portal = handle();              // the handle for tests, without a map
  window.__portal.noMap = on;
  sendHeight();
}
const LOST_WAIT = 6000;          // ms a lost WebGL context is given to come back before the page says the map is gone

function homePadding() {
  const el = $("#map"), w = el.clientWidth || 900;
  return w < 620 ? { top: 54, bottom: 150, left: 14, right: 14 } : { top: 40, bottom: 40, left: 40, right: 40 };
}
const homeCamera = () => map.cameraForBounds(HOME, { padding: homePadding() }) || { center: [127.8, 36.2], zoom: 6.3 };

function cellPolygon(i) {
  const x = G.x0 + cellCol[i] * G.dx, y = G.y0 - cellRow[i] * G.dy;
  return [[[x, y], [x + G.dx, y], [x + G.dx, y - G.dy], [x, y - G.dy], [x, y]]];
}
const cellCentre = (i) => [G.x0 + (cellCol[i] + 0.5) * G.dx, G.y0 - (cellRow[i] + 0.5) * G.dy];

function initMap() {
  const squares = { type: "FeatureCollection", features: [] }, centres = { type: "FeatureCollection", features: [] };
  for (let i = 0; i < C; i++) {
    squares.features.push({ type: "Feature", id: i, properties: {}, geometry: { type: "Polygon", coordinates: cellPolygon(i) } });
    centres.features.push({ type: "Feature", id: i, properties: {}, geometry: { type: "Point", coordinates: cellCentre(i) } });
  }
  const op0 = INTRO ? 0 : 1;
  map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      projection: { type: "globe" },
      sky: { "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 4, 1, 6, 0] },
      sources: {
        sat: { type: "raster", tileSize: 256, maxzoom: 17,
               tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
               attribution: "Imagery © Esri, Maxar, Earthstar Geographics" },
        cells: { type: "geojson", data: squares, tolerance: 0, buffer: 4, maxzoom: 12,
                 attribution: "Water quality: Lee et al., HydroAI Lab (GIST) · HLS (NASA/USGS), ERA5-Land (C3S), WEIS (NIER)" },
        dots: { type: "geojson", data: centres, maxzoom: 9,
                attribution: "Water quality: Lee et al., HydroAI Lab (GIST) · HLS (NASA/USGS), ERA5-Land (C3S), WEIS (NIER)" },
        pick: { type: "geojson", data: { type: "FeatureCollection", features: [] } },
      },
      layers: [
        { id: "bg", type: "background", paint: { "background-color": "#0F1318" } },
        { id: "sat", type: "raster", source: "sat", paint: { "raster-saturation": -0.55, "raster-brightness-max": 0.58, "raster-contrast": -0.1 } },
        { id: "cells-dot", type: "circle", source: "dots", maxzoom: 8.6, paint: {
            "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 0.5, 5, 1.2, 6.5, 1.9, 7.6, 2.3, 8.6, 2.6],
            "circle-color": rampExpr(RAMPS.chla), "circle-opacity": dotOpacity(op0),
            "circle-stroke-width": 0.6, "circle-stroke-color": "#0b0e12", "circle-stroke-opacity": dotOpacity(op0 * 0.6) } },
        { id: "cells-fill", type: "fill", source: "cells", minzoom: 7.5, paint: {
            "fill-color": rampExpr(RAMPS.chla), "fill-outline-color": rampExpr(RAMPS.chla), "fill-opacity": fillOpacity(op0) } },
        { id: "cells-line", type: "line", source: "cells", minzoom: 9.6, paint: {
            "line-color": "#0b0e12", "line-width": ["interpolate", ["linear"], ["zoom"], 9.6, 0.2, 12, 1],
            "line-opacity": ["case", HAS, op0, 0] } },
        { id: "pick-case", type: "line", source: "pick", paint: { "line-color": "#0b0e12", "line-width": 5 } },
        { id: "pick-line", type: "line", source: "pick", paint: { "line-color": "#ffffff", "line-width": 2.2 } },
      ],
    },
    ...(INTRO ? { center: [108, 26], zoom: 2.1 } : { bounds: HOME, fitBoundsOptions: { padding: homePadding() } }),
    minZoom: 1.2, maxZoom: 14,
    attributionControl: { compact: true }, dragRotate: false, pitchWithRotate: false, touchPitch: false,
  });
  rampKey = "chla";
  map.touchZoomRotate.disableRotation();
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric", maxWidth: 110 }), "bottom-left");
  window.__portal = handle();

  map.on("error", (e) => console.warn("[map]", e && e.error ? e.error.message : e));
  /* A context lost while the page is open usually comes back within a second or two (the browser restarts
     its graphics process) and MapLibre carries on. If it has not come back after a while, the page says that
     the map is gone; if it comes back later after all, the map returns. */
  let lost = 0;
  map.on("webglcontextlost", () => { clearTimeout(lost); lost = setTimeout(() => noMap(true, "the WebGL context was lost and has not come back"), LOST_WAIT); });
  map.on("webglcontextrestored", () => { clearTimeout(lost); if (document.documentElement.classList.contains("nomap")) { noMap(false); map.resize(); } });
  map.on("load", () => {
    mapReady = true; window.__portal.map = map;
    $("#boot").classList.add("out");
    setTimeout(() => { const b = $("#boot"); if (b) b.remove(); }, 500);
    rampKey = ""; paint();
    addLabels();
    foldCredits(); map.on("resize", foldCredits);
    if (INTRO) startIntro(); else setOpacity(state.opacity);
    if (state.pts) showPoints(true);
    const at = /^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/.exec(Q.get("at") || "");      // ?at=lat,lon picks the nearest cell
    if (at) { const c = cellAt(+at[2], +at[1], 6); if (c >= 0) { stopIntro(); map.jumpTo({ center: cellCentre(c), zoom: 10.2 }); pickCell(c); } }
  });
  map.on("zoom", onZoom);
  map.on("mousemove", onHover);
  map.on("mouseout", () => { $("#roVal").textContent = ""; });
  map.on("click", onClick);
}
/* On a phone-width map the credits start folded behind the (i): unfolded they cover the legend. */
function foldCredits() {
  if ($("#map").clientWidth >= 700) return;
  const at = document.querySelector(".maplibregl-ctrl-attrib");
  if (at) { at.classList.remove("maplibregl-compact-show"); at.removeAttribute("open"); }
}
/* ── opening sequence ──
   The map opens on the globe over East Asia and flies down to the peninsula in about three seconds, while the
   cells fade up and the boxes and cards rise (html.intro). Any wheel, drag or touch ends it at once.
   Off with ?intro=0 and prefers-reduced-motion. */
let introOn = false, introRAF = 0;
function startIntro() {
  introOn = true;
  document.documentElement.classList.add("intro");
  setTimeout(() => document.documentElement.classList.remove("intro"), 3000);
  setTimeout(() => { if (introOn) map.flyTo({ ...homeCamera(), duration: 3200, curve: 1.25, essential: true }); }, 350);
  const t0 = performance.now() + 1500, dur = 1700;
  const step = (now) => {
    const k = clamp((now - t0) / dur, 0, 1);
    setOpacity(k * k * (3 - 2 * k));
    if (k < 1 && introOn) introRAF = requestAnimationFrame(step); else { setOpacity(+$("#opacity").value / 100); introOn = false; }
  };
  introRAF = requestAnimationFrame(step);
  ["wheel", "mousedown", "touchstart"].forEach((ev) => map.once(ev, stopIntro));
}
function stopIntro() {
  if (!introOn) return;
  introOn = false; cancelAnimationFrame(introRAF);
  setOpacity(+$("#opacity").value / 100);
}

let labelMarkers = [];
function addLabels() {
  const mk = (name, lng, lat, cls, minZoom) => {
    const m = new maplibregl.Marker({ element: el("div", {}, el("span", { class: "city " + cls }, name)), anchor: cls ? "center" : "left" }).setLngLat([lng, lat]).addTo(map);
    labelMarkers.push([m, minZoom]);
  };
  CITIES.forEach(([n, x, y]) => mk("● " + n, x, y, "", 5.6));
  LAKES.forEach(([n, x, y]) => mk(n.replace(/ lakes?$/i, ""), x, y + 0.085, "water", 8.4));
  onZoom();
}
function onZoom() {
  if (!map) return;
  const z = map.getZoom();
  for (const [m, zmin] of labelMarkers) m.getElement().firstChild.style.opacity = z >= zmin && z < 12.5 ? "1" : "0";
  if (pickMarker) pickMarker.getElement().style.display = z < 10.4 ? "" : "none";
}
/* The product cell under a point, or the nearest one within `reach` cells (thin rivers are hard to hit); -1 if none. */
function cellAt(lng, lat, reach = 0) {
  const col = Math.floor((lng - G.x0) / G.dx), row = Math.floor((G.y0 - lat) / G.dy);
  let best = -1, bd = 1e9;
  for (let dr = -reach; dr <= reach; dr++) for (let dc = -reach; dc <= reach; dc++) {
    const r = row + dr, c = col + dc;
    if (r < 0 || r >= H || c < 0 || c >= W) continue;
    const i = cellOf[r * W + c], d = dr * dr + dc * dc;
    if (i >= 0 && d < bd) { bd = d; best = i; }
  }
  return best;
}
/* How far the pointer may be from a cell and still mean it: about five screen pixels. */
const reachAt = (z) => (z >= 10.5 ? 0 : z >= 9.2 ? 1 : z >= 8.2 ? 2 : z >= 7.2 ? 3 : 5);
let hoverRAF = 0;
function onHover(e) {
  cancelAnimationFrame(hoverRAF);
  hoverRAF = requestAnimationFrame(() => {
    const out = $("#roVal");
    if (!current || !current.vals) { out.textContent = ""; return; }
    const c = cellAt(e.lngLat.lng, e.lngLat.lat, reachAt(map.getZoom()));
    if (c < 0) { out.textContent = ""; return; }
    const v = current.vals[c], sp = current.spec;
    out.textContent = Number.isNaN(v) ? (sp.mode === "date" ? "no value on this date" : "no value in this period")
      : sp.isN ? `${fmt(v)} ${v === 1 ? "date" : "dates"}` : `${sp.band === "sigma" ? "σ " : ""}${sig(v)} ${sp.units}`;
  });
}
function onClick(e) {
  const z = map.getZoom(), c = cellAt(e.lngLat.lng, e.lngLat.lat, reachAt(z) + 1);
  if (c < 0) return;
  stopIntro();
  if (z < 8.2) map.flyTo({ center: cellCentre(c), zoom: 9.8, duration: 1400 });
  pickCell(c);
}

/* ── monitoring points (optional layer) ── */
let pointsLoaded = null;
function showPoints(on) {
  state.pts = on;
  const btn = $("#btnPts"); btn.setAttribute("aria-pressed", String(on));
  const lg = $("#lgPts");
  lg.hidden = !on;
  if (on) lg.replaceChildren(...PT_TYPES.map((t, i) => el("span", {}, [el("i", { style: `background:${PT_COLORS[i]}` }), t])), el("span", {}, "monitoring points"));
  if (!mapReady) return;
  if (!on) { if (map.getLayer("stations")) map.setLayoutProperty("stations", "visibility", "none"); hideTip(); return; }
  if (!pointsLoaded) pointsLoaded = fetch(DATA + "stations.json").then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }).then((s) => {
    map.addSource("stations", { type: "geojson", data: { type: "FeatureCollection", features: s.points.map(([id, name, lat, lon, ty, n]) =>
      ({ type: "Feature", geometry: { type: "Point", coordinates: [lon, lat] }, properties: { id, name, ty, n } })) } });
    map.addLayer({ id: "stations", type: "circle", source: "stations", paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 5, 1.6, 8, 3.2, 11, 5.5, 13, 7],
      "circle-color": ["match", ["get", "ty"], 0, PT_COLORS[0], 1, PT_COLORS[1], PT_COLORS[2]],
      "circle-stroke-color": "#ffffff", "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 5, 0.4, 9, 1.2] } }, "pick-case");
    map.on("mousemove", "stations", (e) => {
      const p = e.features[0].properties, o = e.originalEvent;
      map.getCanvas().style.cursor = "pointer";
      showTip([el("div", { class: "t-h" }, `WEIS monitoring point ${p.id}`), el("div", { class: "t-r" }, el("b", {}, p.name)),
        el("div", {}, `${PT_TYPES[p.ty]} · ${fmt(+p.n)} matchups in the training set`)], o.clientX, o.clientY);
    });
    map.on("mouseleave", "stations", () => { map.getCanvas().style.cursor = ""; hideTip(); });
    window.__portal.points = s.points.length;
  });
  pointsLoaded.then(() => map.setLayoutProperty("stations", "visibility", state.pts ? "visible" : "none"))
    .catch((e) => { console.warn("[monitoring points]", e.message); pointsLoaded = null; btn.setAttribute("aria-pressed", "false"); lg.hidden = true; state.pts = false; });
}

/* ───────────────────────────── layer controls ───────────────────────────── */
function renderWhen() {
  const box = $("#when"); box.replaceChildren();
  const isN = state.var === "n";
  document.querySelectorAll("#varSeg button").forEach((b) => b.classList.toggle("on", b.dataset.var === state.var));
  document.querySelectorAll("#bandSeg button").forEach((b) => { b.classList.toggle("on", !isN && b.dataset.band === state.band); b.disabled = isN; });
  document.querySelectorAll("#modeSeg button").forEach((b) => { b.classList.toggle("on", b.dataset.mode === state.mode); b.disabled = isN && b.dataset.mode === "date"; });
  $("#modeSeg").querySelector('[data-mode="all"]').textContent = isN ? "Whole record" : "Record mean";
  if (state.mode === "all") { box.append(el("span", { class: "sub" }, `Every overpass of ${RECORD_YEARS()}`)); return; }
  if (state.mode === "clim") {
    box.append(el("div", { class: "mon", role: "group", "aria-label": "Month" }, MON.map((name, i) =>
      el("button", { class: state.climMonth === i + 1 ? "on" : "", title: MONL[i], onclick: () => { stopPlay(); state.climMonth = i + 1; applyLayer(); } }, name))));
    box.append(playBtn());
    return;
  }
  const ym = state.mode === "month" ? state.ym : state.date.slice(0, 7), y = ym.slice(0, 4);
  box.append(el("select", { "aria-label": "Year", onchange: (e) => { stopPlay(); setYear(e.target.value); } },
    YEARS().map((yy) => el("option", { value: yy, selected: yy === y }, yy))));
  box.append(el("div", { class: "mon", role: "group", "aria-label": "Month" }, MON.map((name, i) =>
    el("button", { class: +ym.slice(5, 7) === i + 1 ? "on" : "", disabled: !ymDates.has(`${y}-${pad2(i + 1)}`), title: MONL[i], onclick: () => { stopPlay(); setMonth(i + 1); } }, name))));
  if (state.mode === "date") {
    const top = CAT.record.cells_per_date.max;
    box.append(el("div", { class: "daynav" }, [
      el("button", { class: "mbtn", title: "Previous overpass", "aria-label": "Previous overpass", onclick: () => { stopPlay(); stepDate(-1); } }, "◀"),
      el("div", { class: "chips", role: "group", "aria-label": `Overpass dates of ${ymLabel(ym)}` }, (ymDates.get(ym) || []).map((i) =>
        el("button", { class: "chip" + (dISO[i] === state.date ? " on" : ""), title: `${dLabel(dISO[i])} · ${fmt(dN[i])} cells`, "aria-label": `${dLabel(dISO[i])}, ${fmt(dN[i])} cells`,
          onclick: () => { stopPlay(); setDate(dISO[i]); } }, [String(+dISO[i].slice(8)), el("i", {}, el("b", { style: `width:${Math.max(4, Math.sqrt(dN[i] / top) * 100)}%` }))]))),
      el("button", { class: "mbtn", title: "Next overpass", "aria-label": "Next overpass", onclick: () => { stopPlay(); stepDate(+1); } }, "▶"),
    ]));
  }
  box.append(playBtn());
}
function playBtn() {
  return el("button", { class: "play", onclick: togglePlay, "aria-pressed": state.playing ? "true" : "false" }, state.playing ? "Pause" : "Play");
}
function setYear(y) {
  if (state.mode === "month") {
    const have = [...ymDates.keys()].filter((k) => k.startsWith(y));
    state.ym = have.includes(`${y}-${state.ym.slice(5)}`) ? `${y}-${state.ym.slice(5)}` : have[0];
    state.date = dISO[ymDates.get(state.ym)[0]];
  } else {
    state.date = nearestDate(`${y}-${state.date.slice(5)}`);
    if (state.date.slice(0, 4) !== y) state.date = dISO[dISO.findIndex((d) => d.startsWith(y))];
    state.ym = state.date.slice(0, 7);
  }
  state.seriesYear = y;
  applyLayer();
}
function setMonth(m) {
  const y = (state.mode === "month" ? state.ym : state.date).slice(0, 4), ym = `${y}-${pad2(m)}`;
  if (!ymDates.has(ym)) return;
  state.ym = ym;
  const list = ymDates.get(ym), day = +state.date.slice(8);
  state.date = dISO[list.reduce((b, i) => (Math.abs(+dISO[i].slice(8) - day) < Math.abs(+dISO[b].slice(8) - day) ? i : b), list[0])];
  applyLayer();
}
function setDate(iso) {
  state.date = iso; state.ym = iso.slice(0, 7);
  state.seriesYear = iso.slice(0, 4);
  applyLayer();
}
function stepDate(dir) {
  const i = clamp(dIndex.get(state.date) + dir, 0, dISO.length - 1);
  if (dISO[i] !== state.date) setDate(dISO[i]);
}
function stopPlay() { if (state.playing) { clearInterval(state.playing); state.playing = null; } }
function togglePlay() {
  if (state.playing) { stopPlay(); renderWhen(); return; }
  if (state.mode === "date") state.playing = setInterval(() => { if (dIndex.get(state.date) >= dISO.length - 1) setDate(dISO[0]); else stepDate(+1); }, 900);
  else if (state.mode === "month") state.playing = setInterval(() => {
    const keys = [...ymDates.keys()], k = keys.indexOf(state.ym);
    state.ym = keys[(k + 1) % keys.length]; state.date = dISO[ymDates.get(state.ym)[0]]; state.seriesYear = state.ym.slice(0, 4);
    applyLayer();
  }, 1200);
  else state.playing = setInterval(() => { state.climMonth = state.climMonth % 12 + 1; applyLayer(); }, 1300);
  renderWhen();
}

/* ───────────────────────────── legend + layer card ───────────────────────────── */
/* Tick values of a colour scale: 1-2-5 on a logarithmic scale, round steps on a linear one; both ends are always labelled. */
function scaleTicks(lo, hi, log, f) {
  let t;
  if (log) t = oneTwoFive(lo, hi).filter((v) => v >= lo * 0.9999 && v <= hi * 1.0001);
  else { const step = niceStep((hi - lo) / 4); t = []; for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi * 1.0000001; v += step) t.push(+v.toPrecision(6)); }
  const near = (a, b) => Math.abs(f(a) - f(b)) < 0.15;
  if (!t.length || Math.abs(t[0] - lo) > 1e-9 * Math.abs(lo || 1)) { while (t.length && near(t[0], lo)) t.shift(); t.unshift(lo); }
  if (Math.abs(t[t.length - 1] - hi) > 1e-9 * Math.abs(hi || 1)) { while (t.length > 1 && near(t[t.length - 1], hi)) t.pop(); t.push(hi); }
  return t;
}
function renderLegend() {
  const { spec, lo, hi, stats, vals } = current, ramp = rampOf(spec), f = norm(spec, lo, hi);
  $("#lgTitle").textContent = spec.isN ? "Dates with a value" : `${spec.band === "sigma" ? "σ " : ""}${PARAMS[spec.var].short} · ${spec.units}${spec.log ? " · log" : ""}`;
  $("#lgBar").style.background = `linear-gradient(90deg, ${ramp.map((c) => `rgb(${c.join(",")})`).join(",")})`;
  const ticks = scaleTicks(lo, hi, spec.log, f), under = stats.n && stats.min < lo, over = stats.n && stats.max > hi;
  $("#lgTicks").replaceChildren(...ticks.map((v, i) => el("span", { class: i === 0 ? "first" : i === ticks.length - 1 ? "last" : "", style: `left:${(f(v) * 100).toFixed(1)}%` },
    (i === 0 && under ? "≤ " : i === ticks.length - 1 && over ? "≥ " : "") + tick(v))));
  $("#lgNodata").textContent = spec.mode === "date" ? "No colour: no value on this date (cloud, or under 80 % of the water seen)" : "No colour: no value in this period";
  document.querySelectorAll("#scaleSeg button").forEach((b) => b.classList.toggle("on", b.dataset.scale === state.scale));
  const c = $("#lgHist"), LW = 240, LH = 34, dpr = Math.min(2, devicePixelRatio || 1);
  c.width = LW * dpr; c.height = LH * dpr;
  const g = c.getContext("2d"); g.scale(dpr, dpr); g.clearRect(0, 0, LW, LH);
  if (!stats.n) return;
  const NB = 60, bins = new Float64Array(NB);
  for (let i = 0; i < C; i++) { const v = vals[i]; if (!Number.isNaN(v)) bins[Math.min(NB - 1, Math.floor(f(v) * NB))]++; }
  const top = Math.max(...bins.slice(1, NB - 1), 1), bw = LW / NB;
  g.fillStyle = "#8C8A80";
  for (let b = 0; b < NB; b++) { const h = Math.min(LH, bins[b] / top * (LH - 2)); if (h > 0.3) g.fillRect(b * bw + 0.5, LH - h, bw - 1, h); }
}
function renderLayerCard() {
  if (!current) return;
  const { spec, stats } = current, isN = spec.isN, p = isN ? null : PARAMS[spec.var], yrs = RECORD_YEARS();
  const what = isN ? "Dates with a value" : spec.band === "sigma" ? `Uncertainty of ${p.name.toLowerCase()}` : p.name;
  let title, sub;
  if (spec.mode === "all") {
    title = isN ? `Dates with a value, ${yrs}` : `${what}, mean of ${yrs}`;
    sub = isN ? `How many of the ${fmt(CAT.record.n)} overpass dates have a value at each cell.`
      : "Mean over the dates with a value at each cell. It leans toward the well-sampled seasons, spring and late autumn.";
  } else if (spec.mode === "clim") {
    const cm = CAT.clim_months[spec.climMonth - 1], mn = MONL[spec.climMonth - 1];
    title = isN ? `Dates with a value in ${mn}, ${yrs}` : `${what}, ${mn} mean of ${yrs}`;
    sub = isN ? `How many of the ${cm.dates} ${mn} overpass dates of ${yrs} have a value at each cell.`
      : `Mean over the ${cm.dates} ${mn} overpass dates of ${yrs}, at the cells that had a value.`;
  } else if (spec.mode === "month") {
    const rec = monthByYm.get(spec.ym);
    title = isN ? `Dates with a value, ${ymLabel(spec.ym)}` : `${what}, ${ymLabel(spec.ym)} mean`;
    sub = isN ? `How many of the month's ${rec.dates} overpass dates have a value at each cell.`
      : `Mean over the month's ${rec.dates} overpass ${rec.dates === 1 ? "date" : "dates"}, at the cells that had a value.`;
  } else {
    title = `${what}, ${dLabel(spec.date)}`;
    sub = `One overpass, as released: ${fmt(dN[dIndex.get(spec.date)])} cells met the coverage rule that day.`;
  }
  $("#lyTitle").textContent = title; $("#lySub").textContent = sub;
  const rg = $("#lyRegime"); rg.hidden = isN; if (!isN) rg.textContent = KINDS[p.kind];
  $("#lyMeanL").textContent = "Median over the cells shown";
  $("#lyMean").textContent = !stats.n ? "—" : isN ? fmt(stats.median) : sig(stats.median);
  $("#lyUnit").textContent = isN ? "dates" : spec.units;
  $("#lyCoverL").textContent = "Cells with a value";
  $("#lyCover").textContent = fmt(stats.n);
  const of = $("#lyCoverOf"); of.className = "of"; of.textContent = `of ${fmt(N_WATER)} water cells`;
  $("#lyCoverBar").style.width = Math.min(100, stats.n / N_WATER * 100) + "%";
  const flag = $("#lyFlag");
  let f = flagText; flagText = "";
  if (!f && current.err) f = "The data for this layer could not be read: " + current.err;
  else if (!f && isN) f = "Counts follow cloud and the satellites: fewest in July under the monsoon, and thinner before July 2017, when only one Sentinel-2 was flying.";
  else if (!f && spec.band === "sigma") f = "σ is the calibrated uncertainty of each value, in the same unit: the value ± 1.96 σ holds about 95 % of held-out measurements."
    + (spec.var === "do" ? " For dissolved oxygen σ is unrelated to the error and should not be used as a filter." : p.log ? " For this parameter the lower limit falls below zero and is read as zero." : "");
  else if (!f) f = HOWTO[spec.var]();
  flag.hidden = !f; flag.textContent = f || "";
}

/* ───────────────────────────── charts (SVG) ─────────────────────────────
   drawLine: n equally spaced slots (months), series as values[n] with nulls for gaps.
   drawDots: points in time (overpasses), each with an optional interval, plus an optional context line. */
function drawLine(box, model) {
  box.replaceChildren();
  const all = model.series.flatMap((s) => s.values).filter((v) => v != null);
  if (!all.length) { box.append(el("p", { class: "chart-empty" }, model.empty || "No data.")); return; }
  if (model.series.length > 1) box.append(el("div", { class: "chart-legend" }, model.series.map((s) => el("span", {}, [el("i", { class: "key", style: `border-color:${s.color}` }), s.name]))));
  const CW = 360, CH = model.height || 200, m = { l: 38, r: model.rightPad == null ? 12 : model.rightPad, t: 8, b: 22 }, pw = CW - m.l - m.r, ph = CH - m.t - m.b;
  const n = model.n, yMin = model.yMin == null ? 0 : model.yMin;
  let yMax = model.yMax, nY = model.yLines || 4;
  if (yMax == null) {                                             // round steps: 0, 10, 20, 30 rather than 0, 12.5, 25, 37.5
    const top = (Math.max(...all) - yMin) * 1.04 || 1, step = niceStep(top / nY);
    nY = Math.max(1, Math.ceil(top / step - 1e-9)); yMax = yMin + nY * step;
  }
  const X = (i) => m.l + (n === 1 ? pw / 2 : pw * i / (n - 1)), Y = (v) => m.t + ph * (1 - (v - yMin) / (yMax - yMin));
  const svg = svgEl("svg", { viewBox: `0 0 ${CW} ${CH}`, role: "img", tabindex: "0", "aria-label": `${model.title}. Use the table below for values.` });
  const stepY = (yMax - yMin) / nY;
  for (let k = 0; k <= nY; k++) {
    const v = yMin + stepY * k, y = Y(v);
    svg.append(svgEl("line", { class: k ? "gridline" : "axisline", x1: m.l, x2: CW - m.r, y1: y, y2: y }));
    const t = svgEl("text", { x: m.l - 6, y: y + 3.5, "text-anchor": "end" }); t.textContent = tick(v); svg.append(t);
  }
  for (const [i, lb] of model.ticks) {
    if (model.tickMarks) svg.append(svgEl("line", { class: "axisline", x1: X(i), x2: X(i), y1: m.t + ph, y2: m.t + ph + 3 }));
    const t = svgEl("text", { x: X(i), y: CH - 6, "text-anchor": "middle" }); t.textContent = lb; svg.append(t);
  }
  const ends = [];
  for (const s of model.series) {
    let d = "", pen = false, last = -1; const lone = [];
    s.values.forEach((v, i) => {
      if (v == null) { pen = false; return; }
      d += `${pen ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen = true; last = i;
      if (s.values[i - 1] == null && s.values[i + 1] == null) lone.push(i);
    });
    svg.append(svgEl("path", { d, fill: "none", stroke: s.color, "stroke-width": s.width || 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    for (const i of lone) svg.append(svgEl("circle", { cx: X(i), cy: Y(s.values[i]), r: n > 60 ? 1.4 : 2.5, fill: s.color }));
    if (last >= 0 && model.endLabels) ends.push({ s, i: last, y: Y(s.values[last]) });
  }
  ends.sort((a, b) => a.y - b.y);
  for (let k = 1; k < ends.length; k++) if (ends[k].y - ends[k - 1].y < 12) { const mid = (ends[k].y + ends[k - 1].y) / 2; ends[k - 1].ly = mid - 6; ends[k].ly = mid + 6; }
  for (const e of ends) {
    svg.append(svgEl("circle", { cx: X(e.i), cy: e.y, r: 4, fill: e.s.color, stroke: "#fff", "stroke-width": 2 }));
    const t = svgEl("text", { class: "lbl", x: X(e.i) + 8, y: (e.ly ?? e.y) + 3.5 }); t.textContent = e.s.short || e.s.name; svg.append(t);
  }
  const cross = svgEl("line", { class: "cross", y1: m.t, y2: m.t + ph, visibility: "hidden" });
  const dots = model.series.map((s) => svgEl("circle", { r: 4, fill: s.color, stroke: "#fff", "stroke-width": 2, visibility: "hidden" }));
  svg.append(cross, ...dots);
  let cur = -1;
  const show = (i, cxp, cyp) => {
    cur = i;
    cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("visibility", "visible");
    model.series.forEach((s, k) => {
      const v = s.values[i];
      dots[k].setAttribute("visibility", v == null ? "hidden" : "visible");
      if (v != null) { dots[k].setAttribute("cx", X(i)); dots[k].setAttribute("cy", Y(v)); }
    });
    showTip([el("div", { class: "t-h" }, model.tipHead(i)),
      ...model.series.map((s) => el("div", { class: "t-r" }, [el("i", { class: "key", style: `border-color:${s.color}` }),
        el("b", {}, s.values[i] == null ? (model.noneText || "no value") : `${model.fmt(s.values[i])} ${model.units}`.trim()), el("span", { class: "n" }, s.name)])),
      ...(model.tipFoot ? [model.tipFoot(i)].filter(Boolean) : [])], cxp, cyp);
  };
  const hide = () => { cur = -1; cross.setAttribute("visibility", "hidden"); dots.forEach((d) => d.setAttribute("visibility", "hidden")); hideTip(); };
  svg.addEventListener("pointermove", (e) => {
    const r = svg.getBoundingClientRect(), x = (e.clientX - r.left) / r.width * CW;
    show(clamp(Math.round((x - m.l) / pw * (n - 1)), 0, n - 1), e.clientX, e.clientY);
  });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const i = clamp((cur < 0 ? 0 : cur) + (cur < 0 ? 0 : e.key === "ArrowRight" ? 1 : -1), 0, n - 1), r = svg.getBoundingClientRect();
    show(i, r.left + X(i) / CW * r.width, r.top + r.height * 0.35);
  });
  box.append(svg);
}
function lineTable(model) {
  return el("table", { class: "grid" }, [
    el("thead", {}, el("tr", {}, [el("th", {}, model.rowLabel || "When"), ...model.series.map((s) => el("th", { class: "num" }, `${s.name}${model.units ? ` (${model.units})` : ""}`))])),
    el("tbody", {}, Array.from({ length: model.n }, (_, i) => i).filter((i) => model.series.some((s) => s.values[i] != null))
      .map((i) => el("tr", {}, [el("td", {}, model.rowName(i)), ...model.series.map((s) => el("td", { class: "num" }, s.values[i] == null ? (model.noneText || "—") : model.fmt(s.values[i])))]))),
  ]);
}
function lineCSV(model) {
  const rows = [[model.csvKey || "when", ...model.series.map((s) => s.csvName || s.name)].join(",")];
  for (let i = 0; i < model.n; i++) if (model.series.some((s) => s.values[i] != null)) rows.push([model.rowName(i), ...model.series.map((s) => (s.values[i] == null ? "" : s.values[i]))].join(","));
  return `# ${model.title}\n# ${model.note || ""}\n` + rows.join("\n") + "\n";
}
const monthTicks = () => MON.map((mn, i) => [i, mn[0]]);

/* Points in time. model: { pts: [{x, y, lo, hi, s, date}], x0, x1, ticks: [[x, label]], log, units, name, ctx: {name, pts}, join, r, compact, height } */
function drawDots(box, model) {
  box.replaceChildren();
  const pts = model.pts, ctx = model.ctx && model.ctx.pts.length ? model.ctx : null;
  if (!pts.length) { box.append(el("p", { class: "chart-empty" }, model.empty || "No value in this period.")); if (!ctx) return; }
  const whisk = pts.some((p) => p.hi != null);
  if (!model.compact) {
    const keys = [el("span", {}, [el("i", { class: "key", style: `border-color:${SERIES}` }), model.name])];
    if (whisk) keys.push(el("span", {}, [el("i", { class: "key", style: `border-color:${SERIES};opacity:.35;border-top-width:5px` }), "95 % interval"]));
    if (ctx) keys.push(el("span", {}, [el("i", { class: "key", style: `border-color:${CONTEXT}` }), ctx.name]));
    if (keys.length > 1) box.append(el("div", { class: "chart-legend" }, keys));
  }
  const K = model.compact, CW = K ? 172 : 360, CH = model.height || (K ? 74 : 200);
  const m = K ? { l: 27, r: 5, t: 6, b: 13 } : { l: 40, r: 12, t: 8, b: 22 }, pw = CW - m.l - m.r, ph = CH - m.t - m.b;
  /* Value axis. Linear: from zero (or below) to the largest upper limit. Logarithmic: set by the dots and the upper
     limits; a lower limit that falls far below the dots (it often does, towards zero) is cut at the axis, which
     reaches a third of the smallest dot at most. The tooltip and the table give the limit itself. */
  let lo = Infinity, hi = -Infinity, wlo = Infinity;
  for (const p of pts) { if (p.y < lo) lo = p.y; if (p.y > hi) hi = p.y; if (p.hi != null && p.hi > hi) hi = p.hi; if (p.lo != null && p.lo < wlo) wlo = p.lo; }
  if (ctx) for (const p of ctx.pts) { if (p.y < lo) lo = p.y; if (p.y > hi) hi = p.y; }
  if (lo === Infinity) { lo = 1; hi = 10; }
  let a, b, ticks, Y, cut = false;
  if (model.log) {
    const floorAt = whisk ? Math.max(Math.min(wlo, lo), lo / 3) : lo;
    cut = whisk && wlo < floorAt;
    [a, b] = logBounds(floorAt, hi);
    ticks = oneTwoFive(a, b).filter((v) => v >= a * 0.9999 && v <= b * 1.0001);
    if (K) ticks = [a, b];
    const la = Math.log(a), ld = Math.log(b) - la;
    Y = (v) => m.t + ph * (1 - (Math.log(Math.max(v, a)) - la) / ld);
    const kept = []; let last = null;                             // labels at least 13 px apart, from the top down
    for (const v of [...ticks].sort((u, w) => w - u)) { const y = Y(v); if (last == null || y - last >= 13) { kept.push(v); last = y; } }
    if (!kept.includes(a)) kept[kept.length - 1] = a;
    ticks = kept.reverse();
  } else {
    const base = Math.min(0, lo, wlo), step = niceStep((hi * 1.02 - base) / (K ? 2 : 4) || 1);
    a = Math.floor(base / step) * step; b = Math.ceil(hi * 1.02 / step) * step; if (b <= a) b = a + step;
    ticks = []; for (let v = a; v <= b * 1.0000001; v += step) ticks.push(+v.toPrecision(6));
    if (K) ticks = [a, b];
    Y = (v) => m.t + ph * (1 - (v - a) / (b - a));
  }
  const X = (x) => m.l + pw * (x - model.x0) / (model.x1 - model.x0);
  const svg = svgEl("svg", { viewBox: `0 0 ${CW} ${CH}`, role: "img", tabindex: K ? "-1" : "0", "aria-label": `${model.title}. Use the table below for values.` });
  ticks.forEach((v) => {
    const y = Y(v);
    svg.append(svgEl("line", { class: v === a ? "axisline" : "gridline", x1: m.l, x2: CW - m.r, y1: y, y2: y }));
    const t = svgEl("text", { x: m.l - (K ? 3 : 6), y: y + 3.5, "text-anchor": "end" }); t.textContent = tick(v); svg.append(t);
  });
  for (const [x, lb] of model.ticks) {
    svg.append(svgEl("line", { class: "axisline", x1: X(x), x2: X(x), y1: m.t + ph, y2: m.t + ph + (K ? 2 : 3) }));
    const t = svgEl("text", { x: X(x), y: CH - (K ? 2 : 6), "text-anchor": model.tickAnchor || "middle" }); t.textContent = lb; svg.append(t);
  }
  if (ctx) {
    svg.append(svgEl("path", { class: "ctxline", d: ctx.pts.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join("") }));
    for (const p of ctx.pts) svg.append(svgEl("circle", { cx: X(p.x), cy: Y(p.y), r: 2, fill: CONTEXT }));
  }
  if (whisk) for (const p of pts) if (p.hi != null) svg.append(svgEl("line", { class: "whisk", x1: X(p.x), x2: X(p.x), y1: Y(model.log ? Math.max(p.lo, a) : p.lo), y2: Y(p.hi), stroke: SERIES, "stroke-opacity": 0.28 }));
  if (model.join && pts.length > 1) svg.append(svgEl("path", { class: "join", stroke: SERIES, "stroke-opacity": 0.45, d: pts.map((p, i) => `${i ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`).join("") }));
  const r = model.r || (K ? 1.25 : 2.6);
  for (const p of pts) svg.append(svgEl("circle", { cx: X(p.x), cy: Y(p.y), r, fill: SERIES, ...(r >= 2.4 ? { stroke: "#fff", "stroke-width": 1 } : {}) }));
  const cross = svgEl("line", { class: "cross", y1: m.t, y2: m.t + ph, visibility: "hidden" });
  const ring = svgEl("circle", { r: K ? 3 : 4.5, fill: SERIES, stroke: "#fff", "stroke-width": 2, visibility: "hidden" });
  svg.append(cross, ring);
  let cur = -1;
  const show = (i, cxp, cyp) => {
    if (!pts.length) return;
    cur = i; const p = pts[i];
    cross.setAttribute("x1", X(p.x)); cross.setAttribute("x2", X(p.x)); cross.setAttribute("visibility", "visible");
    ring.setAttribute("cx", X(p.x)); ring.setAttribute("cy", Y(p.y)); ring.setAttribute("visibility", "visible");
    showTip(model.tip(p), cxp, cyp);
  };
  const hide = () => { cur = -1; cross.setAttribute("visibility", "hidden"); ring.setAttribute("visibility", "hidden"); hideTip(); };
  svg.addEventListener("pointermove", (e) => {
    if (!pts.length) return;
    const rc = svg.getBoundingClientRect(), x = (e.clientX - rc.left) / rc.width * CW;
    let best = 0, bd = Infinity;
    for (let i = 0; i < pts.length; i++) { const d = Math.abs(X(pts[i].x) - x); if (d < bd) { bd = d; best = i; } }
    show(best, e.clientX, e.clientY);
  });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (e) => {
    if ((e.key !== "ArrowLeft" && e.key !== "ArrowRight") || !pts.length) return;
    e.preventDefault();
    const i = clamp((cur < 0 ? 0 : cur) + (cur < 0 ? 0 : e.key === "ArrowRight" ? 1 : -1), 0, pts.length - 1), rc = svg.getBoundingClientRect();
    show(i, rc.left + X(pts[i].x) / CW * rc.width, rc.top + rc.height * 0.35);
  });
  box.append(svg);
  if (cut && !K && !model.noNote) box.append(el("p", { class: "chart-note" }, "Logarithmic axis. Intervals that reach below it are cut at the axis; the table has the limits."));
}
/* Tooltip of one overpass: the value leads, then its interval and sigma. */
function ptTip(par, band) {
  const p = PARAMS[par];
  return (pt) => [el("div", { class: "t-h" }, dLabel(pt.date)),
    el("div", { class: "t-r" }, [el("i", { class: "key", style: `border-color:${SERIES}` }), el("b", {}, `${band === "sigma" ? "σ " : ""}${sig(pt.y)} ${p.units}`), el("span", { class: "n" }, p.short)]),
    ...(pt.hi != null ? [el("div", {}, `95 % interval ${sig(pt.lo)} – ${sig(pt.hi)}`), el("div", {}, `σ ${sig(pt.s)} ${p.units}`)] : [])];
}
function dotsTable(model, par, band) {
  const p = PARAMS[par], w = model.pts.some((x) => x.hi != null);
  return el("table", { class: "grid" }, [
    el("thead", {}, el("tr", {}, [el("th", {}, "Date"), el("th", { class: "num" }, `${band === "sigma" ? "σ of " : ""}${p.short} (${p.units})`),
      ...(w ? [el("th", { class: "num" }, "σ"), el("th", { class: "num" }, "95 % interval")] : [])])),
    el("tbody", {}, model.pts.map((x) => el("tr", {}, [el("td", {}, x.date), el("td", { class: "num" }, sig(x.y)),
      ...(w ? [el("td", { class: "num" }, sig(x.s)), el("td", { class: "num" }, `${sig(x.lo)} – ${sig(x.hi)}`)] : [])]))),
  ]);
}

/* Horizontal grouped bars: one row per parameter, one bar per series, from a common baseline.
   model: { title, rows: [{label, kind}], series: [{name, color, values}], max, ticks, fmt, target: {value, label}, labelSeries } */
function drawBars(box, model) {
  box.replaceChildren();
  box.append(el("div", { class: "chart-legend" }, model.series.map((sr) => el("span", {}, [el("i", { class: "swatch", style: `background:${sr.color}` }), sr.name]))));
  /* The same frame for every such chart, so two side by side line up. In a narrow box (a phone) the drawing is as
     wide as the box, so its text keeps its size, and each row's name goes above its bars instead of beside them. */
  const bw = box.clientWidth || 560, narrow = bw < 440;
  const CW = narrow ? Math.max(280, Math.round(bw)) : 560, BAR = 10, GAP = 2, PITCH = narrow ? 50 : 38, m = narrow ? { l: 2, r: 44, t: 16, b: 22 } : { l: 132, r: 46, t: 16, b: 22 };
  const n = model.rows.length, k = model.series.length, pw = CW - m.l - m.r, CH = m.t + n * PITCH + m.b;
  const X = (v) => m.l + pw * clamp(v, 0, model.max) / model.max;
  const svg = svgEl("svg", { viewBox: `0 0 ${CW} ${CH}`, role: "img", tabindex: "0", "aria-label": `${model.title}. Use the table below for values.` });
  for (const v of model.ticks) {
    svg.append(svgEl("line", { class: v ? "gridline" : "axisline", x1: X(v), x2: X(v), y1: m.t, y2: m.t + n * PITCH }));
    const t = svgEl("text", { x: X(v), y: CH - 7, "text-anchor": "middle" }); t.textContent = model.fmt(v); svg.append(t);
  }
  const bands = [];
  model.rows.forEach((row, i) => {
    const y0 = m.t + i * PITCH, top = narrow ? y0 + 20 : y0 + (PITCH - (k * BAR + (k - 1) * GAP)) / 2;
    const band = svgEl("rect", { class: "rowband", x: 0, y: y0, width: CW, height: PITCH, fill: "transparent" });
    bands.push(band); svg.append(band);
    const t = svgEl("text", narrow ? { class: "lbl", x: m.l, y: y0 + 14 } : { class: "lbl", x: m.l - 10, y: y0 + PITCH / 2 + 4, "text-anchor": "end" }); t.textContent = row.label; svg.append(t);
    model.series.forEach((sr, j) => {
      const v = sr.values[i], y = top + j * (BAR + GAP), w = Math.max(0, X(Math.max(0, v)) - m.l), r = Math.min(4, w);
      if (w > 0.5) svg.append(svgEl("path", { fill: sr.color, d: `M${m.l},${y}h${(w - r).toFixed(1)}a${r},${r} 0 0 1 ${r},${r}v${BAR - 2 * r}a${r},${r} 0 0 1 ${-r},${r}h${(-(w - r)).toFixed(1)}z` }));
      if (j === model.labelSeries) {                               // the value at the bar's tip, clear of a target line it has not reached
        const tip = X(Math.max(0, v)), tx = model.target ? X(model.target.value) : -1;
        const lb = svgEl("text", { class: "val", x: (tx > tip - 2 && tx < tip + 30 ? tx : tip) + 6, y: y + BAR - 1 }); lb.textContent = model.fmt(v); svg.append(lb);
      }
    });
  });
  if (model.target) {
    const x = X(model.target.value);
    svg.append(svgEl("line", { class: "target", x1: x, x2: x, y1: m.t - 3, y2: m.t + n * PITCH }));
    const t = svgEl("text", { class: "lbl", x, y: m.t - 6, "text-anchor": "middle" }); t.textContent = model.target.label; svg.append(t);
  }
  let cur = -1;
  const show = (i, cx, cy) => {
    cur = i; bands.forEach((b, j) => b.setAttribute("fill", j === i ? "rgba(31,30,29,.05)" : "transparent"));
    showTip([el("div", { class: "t-h" }, `${model.rows[i].label} · ${model.rows[i].kind}`),
      ...model.series.map((sr) => el("div", { class: "t-r" }, [el("i", { class: "swatch", style: `background:${sr.color}` }), el("b", {}, model.fmt(sr.values[i])), el("span", { class: "n" }, sr.name)]))], cx, cy);
  };
  const hide = () => { cur = -1; bands.forEach((b) => b.setAttribute("fill", "transparent")); hideTip(); };
  svg.addEventListener("pointermove", (e) => {
    const r = svg.getBoundingClientRect(), y = (e.clientY - r.top) / r.height * CH, i = Math.floor((y - m.t) / PITCH);
    if (i >= 0 && i < n) show(i, e.clientX, e.clientY); else hide();
  });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
    e.preventDefault();
    const i = clamp(cur < 0 ? 0 : cur + (e.key === "ArrowDown" ? 1 : -1), 0, n - 1), r = svg.getBoundingClientRect();
    show(i, r.left + r.width * 0.5, r.top + (m.t + (i + 0.5) * PITCH) / CH * r.height);
  });
  box.append(svg);
}
function barsTable(model) {
  return el("table", { class: "grid" }, [
    el("thead", {}, el("tr", {}, [el("th", {}, "Parameter"), el("th", {}, "Kind of layer"), ...model.series.map((sr) => el("th", { class: "num" }, sr.name))])),
    el("tbody", {}, model.rows.map((row, i) => el("tr", {}, [el("td", {}, row.label), el("td", {}, row.kind), ...model.series.map((sr) => el("td", { class: "num" }, model.fmt(sr.values[i])))]))),
  ]);
}

/* ───────────────────────────── skill numbers (data/skill.json) ─────────────────────────────
   Computed by pipeline/skill.py from the record's public validation file. They fill the numbers in the text
   (<span data-skill>), the About tab's table, the table of the paper's six points and this site's two charts. */
const BY_KIND = ["wt", "do", "ss", "chla", "tp", "tn"];          // meteorologically driven, optical, catchment context
const minus = (t) => t.replace("-", "−");                         // a real minus sign in tables
function skillText(spec) {
  const part = spec.split("|");
  if (part[0] === "site_min" || part[0] === "site_max") {
    const v = SKILL.sites.map((x) => x["r2_" + part[1]]);
    return (part[0] === "site_min" ? Math.min(...v) : Math.max(...v)).toFixed(2);
  }
  const [key, agg, plist, dec] = part;
  const vals = (plist === "all" ? ORDER : plist.split(",")).map((p) => SKILL.params[p][key]);
  const v = agg === "min" ? Math.min(...vals) : agg === "max" ? Math.max(...vals) : vals[0];
  if (dec === "int") return fmt(v);
  return dec.startsWith("pct") ? (v * 100).toFixed(+dec.slice(3)) : v.toFixed(+dec);
}
function renderSkill() {
  document.querySelectorAll("[data-skill]").forEach((n) => { n.textContent = skillText(n.dataset.skill); });
  const P_ = SKILL.params, rows = BY_KIND.map((p) => ({ label: PARAMS[p].name, kind: KINDS[PARAMS[p].kind] }));
  const rmse = (v) => v.toFixed(v < 1 ? 4 : 2);
  $("#abSkill tbody").replaceChildren(...BY_KIND.map((p) => el("tr", {}, [el("td", {}, PARAMS[p].name), el("td", {}, KINDS[PARAMS[p].kind]),
    el("td", { class: "num" }, P_[p].r2.toFixed(3)), el("td", { class: "num" }, P_[p].r2_log == null ? "—" : P_[p].r2_log.toFixed(3)),
    el("td", { class: "num" }, `${rmse(P_[p].rmse)} ${PARAMS[p].units}`), el("td", { class: "num" }, P_[p].within.toFixed(3))])));
  const st = $("#siteTable tbody");
  if (st) st.replaceChildren(...SKILL.sites.map((x) => el("tr", {}, [el("td", {}, `${POINT_NAME[x.id] || x.id} (${x.id})`), el("td", {}, x.type === "river" ? "river" : "lake or dam"),
    el("td", { class: "num" }, fmt(x.n)), el("td", { class: "num" }, minus(x.r2_wt.toFixed(2))), el("td", { class: "num" }, minus(x.r2_chla.toFixed(2)))])));
  if (PAPER === "off") return;
  const two = (v) => v.toFixed(2), pct = (v) => `${Math.round(v * 100)} %`;
  const models = [
    ["#barsSkill", { title: "R² at held-out monitoring points, over all places and dates and following one place through time", rows, max: 1, ticks: [0, 0.25, 0.5, 0.75, 1], fmt: two, labelSeries: 1,
      series: [{ name: "Over all places and dates", color: "#2a78d6", values: BY_KIND.map((p) => P_[p].r2) }, { name: "Following one place through time", color: "#eb6834", values: BY_KIND.map((p) => P_[p].within) }] }],
    ["#barsCover", { title: "Share of held-out measurements inside the 95 % interval, before and after calibration", rows, max: 1, ticks: [0, 0.25, 0.5, 0.75, 1], fmt: pct, labelSeries: 1,
      target: { value: 0.95, label: "95 %" },
      series: [{ name: "Dropout spread alone", color: CONTEXT, values: BY_KIND.map((p) => P_[p].cover_raw) }, { name: "Calibrated σ, as released", color: SERIES, values: BY_KIND.map((p) => P_[p].cover_cal) }] }],
  ];
  for (const [id, model] of models) {
    drawBars($(id), model);
    $(id + "Table").replaceChildren(barsTable(model));
    const btn = $(id + "Btn");
    btn.onclick = () => { const t = $(id + "Table"); t.hidden = !t.hidden; btn.textContent = t.hidden ? "Show table" : "Hide table"; btn.setAttribute("aria-expanded", String(!t.hidden)); sendHeight(); };
  }
}
let barsWidth = 0;
function redrawBarsOnResize() {                                   // the bars are drawn to their box: draw again when it changes between narrow and wide
  const b = $("#barsSkill"); if (!b || !SKILL) return;
  const w = b.clientWidth;
  if (w && (w < 440) !== (barsWidth < 440) || (w < 440 && Math.abs(w - barsWidth) > 12)) { barsWidth = w; renderSkill(); }
}
async function loadSkill() {
  try {
    const r = await fetch(DATA + "skill.json", { cache: "no-cache" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    SKILL = await r.json();
    barsWidth = ($("#barsSkill") || {}).clientWidth || 560;
    renderSkill();
    addEventListener("resize", () => { clearTimeout(redrawBarsOnResize.t); redrawBarsOnResize.t = setTimeout(redrawBarsOnResize, 150); });
    if (current && !flagText) renderLayerCard();
  } catch (e) {
    console.warn("[skill numbers]", e.message);
    SKILL = null;
    $("#abSkill tbody").replaceChildren(el("tr", {}, el("td", { colspan: "6" }, "The skill numbers could not be loaded. They are in the paper and can be computed from oof_predictions.csv of the record.")));
    document.querySelectorAll(".own-charts").forEach((n) => n.remove());
    const st = $("#siteTable"); if (st) st.closest(".tablewrap").remove();
  }
  sendHeight();
}

/* ───────────────────────────── all cells (no cell picked) ───────────────────────────── */
function renderNational() {
  const sp = current.spec, y = state.seriesYear, isN = sp.isN, p = isN ? null : PARAMS[sp.var], yrs = RECORD_YEARS();
  $("#srKicker").textContent = "Seasonal cycle"; $("#srTitle").textContent = "All cells"; $("#srReset").hidden = true;
  $("#recordBox").hidden = true; recordModel = null; $("#srYearNav").hidden = false; $("#srYear").textContent = y;
  const yr = MON.map((_, i) => { const r = monthByYm.get(`${y}-${pad2(i + 1)}`); return !r || !r.dates ? null : isN ? r.dates : r.median[sp.L]; });
  const nYears = CAT.years.length;
  const clim = CAT.clim_months.map((c) => (isN ? c.dates / nYears : c.median[sp.L]));
  $("#srSub").textContent = isN ? `Overpass dates with a grid in each month of ${y}, against the ${yrs} average. 2016 to mid-2017 had one satellite instead of two. The number of dates changes little through the year; what the summer monsoon thins is the number of cells each date delivers.`
    : `Median of ${sp.band === "sigma" ? "the uncertainty of " : ""}${p.name.toLowerCase()} over every cell-value of each month of ${y}, against the same months of ${yrs}. The cells differ from date to date, so read it as a rough guide, not a national mean.`;
  chartModel = { kind: "line", title: isN ? "Overpass dates with a grid per month" : `Monthly median ${p.name.toLowerCase()}${sp.band === "sigma" ? " uncertainty" : ""}, all cells`, n: 12, ticks: monthTicks(),
    units: isN ? "dates" : sp.units, fmt: isN ? (v) => fmt(v, Number.isInteger(v) ? 0 : 1) : sig, rowLabel: "Month", rowName: (i) => `${y}-${pad2(i + 1)}`, csvKey: "month",
    tipHead: (i) => MONL[i], endLabels: true, rightPad: 44, noneText: "no grid",
    tipFoot: (i) => { const r = monthByYm.get(`${y}-${pad2(i + 1)}`); return r && r.dates ? el("div", {}, `${r.dates} overpass ${r.dates === 1 ? "date" : "dates"} · ${fmt(r.cell_days)} cell-values`) : null; },
    note: isN ? "overpass dates with a released grid" : "median over all cell-values of the month; the set of cells changes from date to date",
    series: [{ name: y, short: y, color: SERIES, values: yr, csvName: `${sp.var}${sp.band === "sigma" ? "_sigma" : ""}_${y}` },
      { name: `${yrs}`, short: "all years", color: CONTEXT, values: clim, csvName: `${sp.var}${sp.band === "sigma" ? "_sigma" : ""}_all_years` }] };
  drawLine($("#chart"), chartModel); renderSeriesTable();
}
function renderSeriesTable() {
  const w = $("#srTable"); w.replaceChildren();
  if (!chartModel) return;
  w.append(chartModel.kind === "line" ? lineTable(chartModel) : dotsTable(chartModel, chartModel.par, chartModel.band));
}

/* ───────────────────────────── a cell's record ─────────────────────────────
   The series store holds one entry per cell: n, the date index of each overpass with a value, then the 12 layers. */
const seriesCache = new Map();
async function getSeries(i) {
  if (seriesCache.has(i)) return seriesCache.get(i);
  const res = await seriesArc.getZxy(CAT.store.zoom, cellCol[i], cellRow[i]);
  if (!res || !res.data || !res.data.byteLength) throw new Error("the series store has no entry for this cell");
  const u = new Uint16Array(res.data), n = u[0];
  if (u.length !== 1 + 13 * n) throw new Error(`series entry has ${u.length} numbers, expected ${1 + 13 * n}`);
  const out = { n, di: Array.from(u.subarray(1, 1 + n)), vals: [] };
  for (let L = 0; L < 12; L++) { const t = lut(L), a = new Float32Array(n), o = 1 + n + L * n; for (let k = 0; k < n; k++) a[k] = t[u[o + k]]; out.vals.push(a); }
  if (seriesCache.size > 60) seriesCache.delete(seriesCache.keys().next().value);
  seriesCache.set(i, out);
  return out;
}
/* The overpasses of one parameter at a cell as chart points (optionally one year only), with the 95 % interval. */
function pointsOf(S, par, band, year) {
  const k = ORDER.indexOf(par), mu = S.vals[2 * k], sg = S.vals[2 * k + 1], [ql, qh, clip] = CI[par], out = [];
  for (let j = 0; j < S.n; j++) {
    const date = dISO[S.di[j]];
    if (year && !date.startsWith(year)) continue;
    if (band === "sigma") out.push({ x: dDay[S.di[j]], y: sg[j], date });
    else { const lo = mu[j] + ql * sg[j]; out.push({ x: dDay[S.di[j]], y: mu[j], s: sg[j], lo: clip ? Math.max(0, lo) : lo, hi: mu[j] + qh * sg[j], date }); }
  }
  return out;
}
function pickCell(i) {
  const [lng, lat] = cellCentre(i);
  state.pick = { i, row: cellRow[i], col: cellCol[i], lat, lng };
  if (map && mapReady) {
    map.getSource("pick").setData({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: cellPolygon(i) } });
    if (!pickMarker) pickMarker = new maplibregl.Marker({ color: "#B85434", scale: 0.7 });
    pickMarker.setLngLat([lng, lat]).addTo(map); onZoom();
  }
  renderPickCharts();
}
function clearPick() {
  state.pick = null; recordModel = null; $("#recordBox").hidden = true;
  if (pickMarker) pickMarker.remove();
  if (map && mapReady) map.getSource("pick").setData({ type: "FeatureCollection", features: [] });
  if (current) renderNational();
}
const yearTicks = () => { const t = []; for (let y = +CAT.record.first.slice(0, 4); y <= +CAT.record.last.slice(0, 4); y++) t.push([dayNum(`${y}-01-01`), String(y).slice(2)]); return t; };
let pickSeq = 0;
async function renderPickCharts() {
  const c = state.pick, seq = ++pickSeq;
  if (!c || !current) return;
  const where = `${c.lat.toFixed(3)}°N, ${c.lng.toFixed(3)}°E`, sp = current.spec, y = state.seriesYear, yrs = RECORD_YEARS();
  $("#srKicker").textContent = `1 km cell · row ${c.row}, column ${c.col}`; $("#srTitle").textContent = where; $("#srReset").hidden = false;
  $("#srYearNav").hidden = false; $("#srYear").textContent = y;
  let S;
  try { S = await getSeries(c.i); } catch (e) { $("#srSub").textContent = "Could not read the series store: " + e.message; return; }
  if (seq !== pickSeq) return;
  const x0 = dayNum(`${y}-01-01`), x1 = dayNum(`${y}-12-31`), ticksY = MON.map((mn, i) => [dayNum(`${y}-${pad2(i + 1)}-01`), mn[0]]);
  const inYear = S.di.filter((d) => dISO[d].startsWith(y)).length;
  if (sp.isN) {
    const perMonth = (yy) => MON.map((_, i) => (ymDates.has(`${yy}-${pad2(i + 1)}`) ? S.di.filter((d) => dISO[d].startsWith(`${yy}-${pad2(i + 1)}`)).length : null));
    const mean = MON.map((_, i) => S.di.filter((d) => +dISO[d].slice(5, 7) === i + 1).length / CAT.years.length);
    $("#srSub").textContent = `${fmt(S.n)} of the ${fmt(CAT.record.n)} overpass dates have a value at this cell, ${inYear} of them in ${y}. Blue: dates per month in ${y}; grey: the ${yrs} average.`;
    chartModel = { kind: "line", title: `Dates with a value per month at ${where}`, n: 12, ticks: monthTicks(), units: "dates", fmt: (v) => fmt(v, Number.isInteger(v) ? 0 : 1), rowLabel: "Month",
      rowName: (i) => `${y}-${pad2(i + 1)}`, csvKey: "month", tipHead: (i) => MONL[i], endLabels: true, rightPad: 44, noneText: "no grid", note: `cell row ${c.row}, column ${c.col}, centre ${where}`,
      series: [{ name: y, short: y, color: SERIES, values: perMonth(y), csvName: `dates_${y}` }, { name: yrs, short: "all years", color: CONTEXT, values: mean, csvName: "dates_mean" }] };
    drawLine($("#chart"), chartModel);
    const keys = CAT.months.map((m) => m.ym);
    recordModel = { kind: "line", S, pick: c, where, title: `Dates with a value per month at ${where}, ${yrs}`, n: keys.length, units: "dates", fmt: (v) => fmt(v), height: 150, yLines: 2, rowLabel: "Month",
      rowName: (i) => keys[i], csvKey: "month", tickMarks: true, ticks: keys.map((k, i) => [i, k]).filter(([, k]) => k.endsWith("-01")).map(([i, k]) => [i, k.slice(2, 4)]),
      tipHead: (i) => ymLabel(keys[i]), noneText: "no grid",
      series: [{ name: "dates", color: SERIES, width: 1.5, values: keys.map((k) => (ymDates.has(k) ? S.di.filter((d) => dISO[d].startsWith(k)).length : null)), csvName: "dates" }] };
    $("#rcSub").textContent = "Dates with a value in each month of the record.";
    drawLine($("#chartRecord"), recordModel);
    $("#rcTable").replaceChildren(lineTable(recordModel));
  } else {
    const par = sp.var, band = sp.band, p = PARAMS[par], k = ORDER.indexOf(par), arr = S.vals[2 * k + (band === "sigma" ? 1 : 0)];
    const sum = new Float64Array(12), cnt = new Float64Array(12);
    for (let j = 0; j < S.n; j++) { const mo = +dISO[S.di[j]].slice(5, 7) - 1; sum[mo] += arr[j]; cnt[mo]++; }
    const ctxPts = []; for (let mo = 0; mo < 12; mo++) if (cnt[mo]) ctxPts.push({ x: dayNum(`${y}-${pad2(mo + 1)}-15`), y: sum[mo] / cnt[mo] });
    const what = `${band === "sigma" ? "uncertainty of " : ""}${p.name.toLowerCase()}`;
    $("#srSub").textContent = `${inYear} ${inYear === 1 ? "overpass" : "overpasses"} of ${y} have a value at this cell (${fmt(S.n)} in the whole record). Dots: ${what} on each overpass${band === "mu" ? ", with its 95 % interval" : ""}; grey: this cell's own ${yrs} mean of each calendar month.`;
    chartModel = { kind: "dots", par, band, title: `${p.name}${band === "sigma" ? " uncertainty" : ""} at ${where}, ${y}`, name: `${band === "sigma" ? "σ of " : ""}${p.short}, ${p.units}`, pts: pointsOf(S, par, band, y),
      x0, x1, ticks: ticksY, log: p.log, units: p.units, join: true, ctx: { name: "monthly mean, all years", pts: ctxPts }, tip: ptTip(par, band), empty: `No overpass of ${y} has a value at this cell.` };
    drawDots($("#chart"), chartModel);
    recordModel = { kind: "dots", S, pick: c, where, par, band, title: `${p.name}${band === "sigma" ? " uncertainty" : ""} at ${where}, ${yrs}`, name: `${band === "sigma" ? "σ of " : ""}${p.short}, ${p.units}`,
      pts: pointsOf(S, par, band, null), x0: dayNum(`${CAT.record.first.slice(0, 4)}-01-01`), x1: dayNum(`${CAT.record.last.slice(0, 4)}-12-31`), ticks: yearTicks(), tickAnchor: "start",
      log: p.log, units: p.units, r: 1.7, height: 160, noNote: true, tip: ptTip(par, band) };
    $("#rcSub").textContent = `Every overpass with a value, ${yrs}: ${fmt(S.n)} of ${fmt(CAT.record.n)} dates. Gaps are cloud, or dates on which less than 80 % of the cell's water was seen. Nothing is filled in.`;
    drawDots($("#chartRecord"), recordModel);
    $("#rcTable").replaceChildren(dotsTable(recordModel, par, band));
  }
  renderSeriesTable();
  $("#recordBox").hidden = false;
  renderSix(S, where);
  sendHeight();
}
/* Small multiples: the six parameters at the picked cell, each on its own scale. */
function renderSix(S, where) {
  const box = $("#six"); box.replaceChildren();
  const x0 = dayNum(`${CAT.record.first.slice(0, 4)}-01-01`), x1 = dayNum(`${CAT.record.last.slice(0, 4)}-12-31`);
  const ticks = [[dayNum("2016-01-01"), "2016"], [dayNum("2020-01-01"), "2020"], [dayNum("2024-01-01"), "2024"]];
  for (const par of ORDER) {
    const p = PARAMS[par], pts = pointsOf(S, par, "mu", null).map(({ x, y, date }) => ({ x, y, date }));
    const sorted = pts.map((q) => q.y).sort((u, v) => u - v), med = sorted.length ? sorted[Math.floor(sorted.length / 2)] : NaN;
    const fig = el("figure", { class: "chart", style: "margin:0" });
    const b = el("button", { class: state.var === par ? "on" : "", title: `Show ${p.name.toLowerCase()} on the map`, "aria-label": `${p.name}: median ${sig(med)} ${p.units} at this cell. Show it on the map.`,
      onclick: () => { stopPlay(); state.var = par; state.band = "mu"; applyLayer(); } },
      [el("div", { class: "six-t" }, [el("span", {}, p.short), el("small", {}, `median ${sig(med)} ${p.units}`)]), fig]);
    box.append(b);
    drawDots(fig, { compact: true, title: `${p.name} at ${where}`, name: p.short, pts, x0, x1, ticks, tickAnchor: "start", log: p.log, units: p.units, tip: ptTip(par, "x") });
  }
}
function recordCSV() {
  const R = recordModel; if (!R) return "";
  const c = R.pick, S = R.S, prec = (v) => (Number.isNaN(v) ? "" : String(+v.toPrecision(5)));
  const rows = [];
  for (let j = 0; j < S.n; j++) rows.push([dISO[S.di[j]], ...S.vals.map((a) => prec(a[j]))].join(","));
  return [`# Korea inland water quality, 1 km grid: cell row ${c.row}, column ${c.col} (centre ${c.lat.toFixed(5)}N ${c.lng.toFixed(5)}E), ${CAT.version}`,
    `# Dataset doi:${CFG.zenodoDoi}. One row per overpass date with a value at this cell; dates without a row have no value (cloud, or under 80 % of the water seen).`,
    "# mu = predictive mean (band 1), sigma = calibrated uncertainty (band 2). Units: wt degC, ss mg/L, chla ug/L, do mg/L, tn mg/L, tp mg/L.",
    "# Values from the portal's store (16-bit; within 0.0005 for wt and do, 0.014 % for the others). Use the GeoTIFF files for analysis.",
    "date," + ORDER.map((p) => `${p}_mu,${p}_sigma`).join(","), ...rows].join("\n") + "\n";
}
function seriesCSV() {
  const M = chartModel; if (!M) return "";
  if (M.kind === "line") return lineCSV(M);
  const w = M.pts.some((x) => x.hi != null), p = PARAMS[M.par];
  return [`# ${M.title}`, `# Units: ${p.units}. ${w ? "lo95 and hi95: 95 % interval from sigma with the multipliers of the record's metadata (lower limit floored at zero where it applies)." : ""}`,
    w ? "date,mu,sigma,lo95,hi95" : "date,sigma", ...M.pts.map((x) => (w ? [x.date, x.y, x.s, x.lo, x.hi] : [x.date, x.y]).map((v) => (typeof v === "number" ? +v.toPrecision(5) : v)).join(","))].join("\n") + "\n";
}

/* ───────────────────────────── calendar of the record ───────────────────────────── */
function renderCalendar() {
  const box = $("#cal"); box.replaceChildren(el("span"));
  MON.forEach((mn) => box.append(el("span", { class: "cal-h" }, mn[0])));
  const top = Math.max(...CAT.months.map((m) => m.dates));
  const selYm = state.mode === "month" ? state.ym : state.mode === "date" ? state.date.slice(0, 7) : null;
  for (const yr of CAT.years) {
    box.append(el("span", { class: "cal-y train" }, String(yr.year)));
    for (let mo = 1; mo <= 12; mo++) {
      const ym = `${yr.year}-${pad2(mo)}`, r = monthByYm.get(ym);
      let node, lines;
      if (!r || !r.dates) {
        node = el("span", { class: "cal-c pending", tabindex: "0" });
        lines = [ymLabel(ym), "no overpass with a grid"];
      } else {
        node = el("button", { class: "cal-c built" + (selYm === ym ? " sel" : ""), style: `background:${COVER_STEPS[clamp(Math.ceil(r.dates / top * 5) - 1, 0, 4)]}`,
          "aria-label": `${ymLabel(ym)}, ${r.dates} overpass dates`,
          onclick: () => { stopPlay(); if (state.mode !== "date") state.mode = "month"; state.ym = ym; state.date = dISO[ymDates.get(ym)[0]]; state.seriesYear = ym.slice(0, 4); applyLayer(); } });
        lines = [ymLabel(ym), `${r.dates} overpass ${r.dates === 1 ? "date" : "dates"} with a grid`, `${fmt(r.cell_days)} cell-values · ${fmt(r.cells)} cells with at least one`];
      }
      const tipNodes = () => [el("div", { class: "t-h" }, lines[0]), ...lines.slice(1).map((s) => el("div", {}, s))];
      node.addEventListener("pointerenter", (e) => showTip(tipNodes(), e.clientX, e.clientY));
      node.addEventListener("pointerleave", hideTip);
      node.addEventListener("focus", () => { const b = node.getBoundingClientRect(); showTip(tipNodes(), b.left, b.top); });
      node.addEventListener("blur", hideTip);
      box.append(node);
    }
  }
  $("#calSub").textContent = `${fmt(CAT.record.n)} dates from ${dLabel(CAT.record.first)} to ${dLabel(CAT.record.last)}: one grid for each overpass that cloud allowed, not one a day. Click a month to show it.`;
  $("#calLegend").replaceChildren(
    el("span", {}, ["Dates in the month: ", ...COVER_STEPS.map((c) => el("i", { style: `background:${c}` })), ` 1 → ${top}`]),
    el("span", {}, [el("i", { style: "box-shadow:inset 0 0 0 1px #D9D5C7;background:#FAF9F5" }), "none"]));
}

/* ───────────────────────────── download + code ───────────────────────────── */
const OTHER_FILES = {
  "README_zenodo.md": "Read this first: contents, conventions and limitations of the record.",
  "kr_wq_1km_metadata.json": "Machine-readable metadata: grid, bands, units, counts, and the multipliers for the asymmetric 95 % interval.",
  "code_v1.0.zip": "The pipeline that made the grids: thirteen notebooks and three scripts, a helper that rebuilds the study-area polygon, the static inputs they need, and the environment specification (MIT).",
  "deploy_models.zip": "The six deployment models that generated the grids, with their input scalers. Fitted on every matchup: use them to reproduce or extend the product, not to measure skill.",
  "mlp_folds.zip": "The 30 cross-validation models (six parameters × five folds) behind the reported skill.",
  "station_fold_map.csv": "Which monitoring point was held out in which fold, with its water-body type and number of matchups.",
  "oof_predictions.csv": "The 281,598 out-of-fold predictions (46,933 matchups × six parameters) from which every skill figure of the paper is computed.",
  "baseline_oof_predictions.csv": "Out-of-fold predictions of the comparison models: random forest, XGBoost, two satellite-free baselines and the ablation's all-feature reference.",
  "ablation_oof_predictions.csv": "Out-of-fold predictions of the tree-based model for the six input-group configurations.",
  "ablation_mlp_oof_predictions.csv": "The same six input-group configurations for the multi-layer perceptron.",
  "matchup_aerosol_flags.csv": "Aerosol levels of each matchup's satellite window, used in the paper's aerosol test.",
  "hydrolakes_station_match.csv": "HydroLAKES polygons matched to the reservoir and lake points, used in the paper's morphometry test.",
};
function renderDownload() {
  const files = new Map((CAT.files || []).map((f) => [f.name, f]));
  const link = (f, text) => el("a", { href: f.url, rel: "noopener" }, text || f.name);
  $("#dlNDates").textContent = fmt(CAT.record.n);
  const notice = $("#dlNotice"); notice.replaceChildren();
  if (CFG.nasPath) notice.append(el("b", {}, "Lab members: "), "the same files, in folders by year, are on the lab storage under ", el("code", {}, CFG.nasPath.replace(/\/$/, "") + "/"), " (CPU server).");
  notice.hidden = !CFG.nasPath;
  let bytes = 0;
  $("#dlProduct tbody").replaceChildren(...ORDER.map((par) => {
    const p = PARAMS[par], f = files.get(`kr_wq_${par}_1km_2016-2024.zip`);
    if (f) bytes += f.bytes;
    return el("tr", {}, [el("td", {}, `${p.name} (${p.short})`), el("td", {}, p.units), el("td", {}, KINDS[p.kind]),
      el("td", { class: "mono" }, f ? link(f) : `kr_wq_${par}_1km_2016-2024.zip`), el("td", { class: "num" }, f ? fmtBytes(f.bytes) : "—"),
      el("td", { class: "mono" }, `${par}/kr_wq_${par}_1km_<yyyymmdd>.tif`)]);
  }));
  $("#dlTotal").textContent = `${fmt(CAT.record.rasters)} files in all, ${fmtBytes(bytes)} to download, ${fmtBytes(CAT.record.bytes)} unpacked.`
    + (CFG.nasPath ? " The files are identical to those on the lab storage; only the folders differ (by parameter on Zenodo, by year in the lab)." : "");
  const others = (CAT.files || []).filter((f) => !/^kr_wq_[a-z]+_1km_/.test(f.name));
  const order = Object.keys(OTHER_FILES);
  others.sort((a, b) => (order.indexOf(a.name) + 1 || 99) - (order.indexOf(b.name) + 1 || 99));
  $("#dlOther tbody").replaceChildren(...others.map((f) => el("tr", {}, [el("td", { class: "mono" }, link(f)), el("td", { class: "num" }, fmtBytes(f.bytes)), el("td", {}, OTHER_FILES[f.name] || "")])));
  const sel = $("#dlYear");
  sel.replaceChildren(el("option", { value: "" }, "All years"), ...CAT.years.map((y) => el("option", { value: String(y.year) }, String(y.year))));
  const body = $("#dlTable tbody"), iso = (d) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}`;
  const draw = () => {
    const rows = CAT.years.filter((y) => !sel.value || String(y.year) === sel.value);
    body.replaceChildren(...rows.map((y) => el("tr", {}, [el("td", {}, String(y.year)), el("td", { class: "num" }, fmt(y.dates)), el("td", { class: "num" }, fmt(y.files)),
      el("td", { class: "num" }, fmt(y.cell_days)), el("td", {}, iso(y.first)), el("td", {}, iso(y.last))])));
    $("#dlYearTotal").textContent = `${fmt(rows.reduce((a, y) => a + y.dates, 0))} dates · ${fmt(rows.reduce((a, y) => a + y.files, 0))} files`;
  };
  sel.onchange = draw; draw();
  $("#dlMissing").textContent = "Of the 1,110 HLS S30 mosaic dates of 2016–2024, 98 have no file: on 74 no 30 m pixel could be predicted, and on 24 more no cell met the coverage rule. A missing date is a real gap, not a packaging error.";
  $("#dlCopy").onclick = (e) => copyText(CAT.dates.d.filter((d) => !sel.value || d.startsWith(sel.value)).join("\n"), e.currentTarget);
}
function renderCode() {
  $("#cdCells").textContent = fmt(C);
  $("#codeOne").textContent =
`import numpy as np
import rasterio

with rasterio.open("chla/kr_wq_chla_1km_20231203.tif") as src:
    mu = src.read(1)             # chlorophyll-a, µg/L; NaN where the cell has no value
    sigma = src.read(2)          # calibrated uncertainty, µg/L
    print(src.tags())            # units, coverage rule, definition of predictable water

print("cells with a value:", int(np.isfinite(mu).sum()))
print("median:", float(np.nanmedian(mu)))`;
  $("#codePt").textContent =
`import glob
import pandas as pd
import rasterio

lon, lat = 127.53, 36.41                                  # Daecheong Lake
rows = []
for f in sorted(glob.glob("chla/kr_wq_chla_1km_*.tif")):
    with rasterio.open(f) as src:
        r, c = src.index(lon, lat)                        # the same grid in every file
        mu, sigma = src.read(window=((r, r + 1), (c, c + 1)))[:, 0, 0]
    rows.append((pd.to_datetime(f[-12:-4]), mu, sigma))

s = pd.DataFrame(rows, columns=["date", "mu", "sigma"]).set_index("date").dropna()
print(len(s), "overpasses with a value at this cell")
# A date is an overpass, not a day: the index is irregular. Do not resample it to daily
# without deciding what the gaps mean for your purpose.`;
  $("#codeCi").textContent =
`import json
import numpy as np
import rasterio

with rasterio.open("chla/kr_wq_chla_1km_20231203.tif") as src:
    mu, sigma = src.read(1), src.read(2)

# default: mu ± 1.96 sigma, an approximate 95 % interval
lower, upper = mu - 1.96 * sigma, mu + 1.96 * sigma
lower = np.maximum(lower, 0)          # ss, chla, tn, tp: read a negative lower limit as zero

# asymmetric interval, with the multipliers shipped in the record's metadata
q = json.load(open("kr_wq_1km_metadata.json"))["uncertainty_asymmetric"]["multipliers"]["chla"]
lower = mu + q["q_lower"] * sigma
upper = mu + q["q_upper"] * sigma
if q["clip_zero"]:
    lower = np.maximum(lower, 0)

# sigma as a filter (every parameter except dissolved oxygen): keep the more certain three quarters
keep = sigma <= np.nanpercentile(sigma, 75)
mu_filtered = np.where(keep, mu, np.nan)`;
  $("#codeMap").textContent =
`import glob
import numpy as np
import rasterio

def band1(path):
    with rasterio.open(path) as src:
        return src.read(1)

files = sorted(f for f in glob.glob("chla/kr_wq_chla_1km_*.tif") if f[-8:-6] in ("03", "04", "05"))   # March–May, all years
stack = np.stack([band1(f) for f in files])                        # (dates, 470, 510), NaN = no value

n = np.isfinite(stack).sum(axis=0)                                 # dates with a value at each cell
mean = np.where(n >= 10, np.nansum(stack, axis=0) / np.maximum(n, 1), np.nan)   # keep cells with ten dates or more

with rasterio.open(files[0]) as src:
    profile = src.profile
profile.update(count=2, dtype="float32", nodata=np.nan)
with rasterio.open("chla_spring_mean.tif", "w", **profile) as dst:
    dst.write(mean.astype("float32"), 1)
    dst.write(n.astype("float32"), 2)                              # always keep the count beside a mean`;
  $("#codeR").textContent =
`library(terra)

r <- rast("chla/kr_wq_chla_1km_20231203.tif")      # two layers
names(r) <- c("mu_pred", "sigma_cal")
global(r$mu_pred, "notNA")                           # cells with a value

pt <- vect(cbind(127.53, 36.41), crs = "EPSG:4326")  # Daecheong Lake
extract(r, pt)`;
  document.querySelectorAll(".copy").forEach((b) => { b.onclick = () => copyText($("#" + b.dataset.copy).textContent, b); });
}

/* ───────────────────────────── tabs, embed, wiring ───────────────────────────── */
function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) => { const on = t.dataset.tab === name; t.classList.toggle("on", on); t.setAttribute("aria-selected", on); });
  document.querySelectorAll(".tabpane").forEach((p) => { const on = p.id === "tab-" + name; p.hidden = !on; p.classList.toggle("on", on); });
  if (name === "explore" && map) map.resize();
  hideTip(); sendHeight();
}
function sendHeight() {
  if (window.parent === window) return;
  const h = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
  window.parent.postMessage({ type: "portalHeight", height: h }, "*");
}
function flyToPlace(lng, lat, zoom, label) {
  stopIntro();
  map.flyTo({ center: [lng, lat], zoom, duration: 1700 });
  if (placeMarker) { placeMarker.remove(); placeMarker = null; }
  if (label) placeMarker = new maplibregl.Marker({ element: el("div", { class: "pulse-wrap" }, [el("div", { class: "pulse" }), el("span", { class: "pulse-label" }, label)]) }).setLngLat([lng, lat]).addTo(map);
}
function wire() {
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.tab)));
  document.querySelectorAll("#varSeg button").forEach((b) => b.addEventListener("click", () => {
    stopPlay(); state.var = b.dataset.var;
    if (state.var === "n" && state.mode === "date") { state.mode = "month"; state.ym = state.date.slice(0, 7); }
    applyLayer();
  }));
  document.querySelectorAll("#bandSeg button").forEach((b) => b.addEventListener("click", () => { if (b.disabled) return; stopPlay(); state.band = b.dataset.band; applyLayer(); }));
  document.querySelectorAll("#modeSeg button").forEach((b) => b.addEventListener("click", () => {
    if (b.disabled) return; stopPlay(); state.mode = b.dataset.mode;
    if (state.mode === "month") state.ym = state.date.slice(0, 7);
    if (state.mode === "date" && state.date.slice(0, 7) !== state.ym) state.date = dISO[ymDates.get(state.ym)[0]];
    applyLayer();
  }));
  document.querySelectorAll("#scaleSeg button").forEach((b) => b.addEventListener("click", () => { state.scale = b.dataset.scale; applyLayer(); }));
  $("#opacity").addEventListener("input", (e) => { stopIntro(); setOpacity(e.target.value / 100); });
  const places = [...LAKES.map((s) => [s[0], s[1], s[2], 10.2, ""]), ...REACHES.map((s) => [s[0], s[1], s[2], 10, ""]), ...POINTS.map((s) => [`${s[0]} (${s[1]})`, s[2], s[3], 11.6, s[0]])];
  const og1 = el("optgroup", { label: "Reservoirs and lakes" }), og2 = el("optgroup", { label: "Rivers and estuaries" }), og3 = el("optgroup", { label: "Monitoring points in the paper (Fig. 7)" });
  places.forEach((p, i) => (i < LAKES.length ? og1 : i < LAKES.length + REACHES.length ? og2 : og3).append(el("option", { value: i }, p[0])));
  $("#jump").append(og1, og2, og3);
  $("#jump").onchange = (e) => {
    const p = places[+e.target.value];
    if (e.target.value !== "" && p && map) flyToPlace(p[1], p[2], p[3], p[4]);
    e.target.value = "";
  };
  $("#btnHome").onclick = () => { if (!map) return; stopIntro(); map.flyTo({ ...homeCamera(), duration: 1600 }); };
  $("#btnPts").onclick = () => showPoints(!state.pts);
  document.querySelectorAll(".novelty-more").forEach((a) => a.addEventListener("click", (e) => {   // scrolls to the plain-words section below the map
    const t = document.getElementById(a.getAttribute("href").slice(1)); if (!t) return;
    e.preventDefault(); t.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "start" });
  }));
  $("#srReset").onclick = clearPick;
  const stepYear = (d) => { const ys = YEARS(), k = clamp(ys.indexOf(state.seriesYear) + d, 0, ys.length - 1); if (ys[k] !== state.seriesYear) { state.seriesYear = ys[k]; if (state.pick) renderPickCharts(); else renderNational(); } };
  $("#srYearPrev").onclick = () => stepYear(-1); $("#srYearNext").onclick = () => stepYear(+1);
  const toggle = (btn, box) => { box.hidden = !box.hidden; btn.textContent = box.hidden ? "Show table" : "Hide table"; btn.setAttribute("aria-expanded", String(!box.hidden)); sendHeight(); };
  $("#rcTableBtn").onclick = (e) => toggle(e.currentTarget, $("#rcTable"));
  $("#srTableBtn").onclick = (e) => toggle(e.currentTarget, $("#srTable"));
  $("#rcCsv").onclick = () => { if (recordModel) download(`kr_wq_1km_cell_r${recordModel.pick.row}_c${recordModel.pick.col}.csv`, recordCSV(), "text/csv"); };
  $("#srCsv").onclick = () => { if (chartModel) download("kr_wq_1km_series.csv", seriesCSV(), "text/csv"); };
  /* In-page links of the About tab: inside an auto-height frame the frame itself never scrolls, so
     ask the browser to bring the heading into view (it scrolls whichever ancestor can). */
  document.querySelectorAll(".toc a").forEach((lnk) => lnk.addEventListener("click", (e) => {
    const target = document.getElementById(lnk.getAttribute("href").slice(1));
    if (!target) return;
    e.preventDefault();
    target.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth", block: "start" });
  }));
  addEventListener("resize", sendHeight);
  if (window.ResizeObserver) new ResizeObserver(sendHeight).observe(document.body);
}
async function main() {
  try {
    await loadCatalog();
  } catch (e) {
    $("#bootMsg").textContent = e.message; document.querySelector(".boot-mark").style.display = "none";
    return;
  }
  const f = CAT.record.first, l = CAT.record.last;
  $("#factRecord").textContent = `${MON[+f.slice(5, 7) - 1]} ${f.slice(0, 4)} – ${MON[+l.slice(5, 7) - 1]} ${l.slice(0, 4)} · ${fmt(CAT.record.n)} dates`;
  $("#abRecord").textContent = `${dLabel(f)} to ${dLabel(l)}`;
  $("#abDates").textContent = fmt(CAT.record.n); $("#abCells").textContent = fmt(C);
  $("#glRecord").textContent = `${dLabel(f)} – ${dLabel(l)} · ${fmt(CAT.record.n)} dates`;
  $("#abContact").textContent = CFG.dataContact || "";
  $("#abMail").textContent = CFG.contactEmail; $("#abMail").href = "mailto:" + CFG.contactEmail;
  $("#footVer").textContent = `Data: ${CAT.version}`;
  state.pts = Q.get("pts") === "1";
  document.documentElement.classList.add("paper-" + PAPER);
  if (PAPER === "off") {                                           // no account of the paper on the page (config.js)
    const sec = $("#paper"); if (sec) sec.remove();
    document.querySelectorAll(".novelty-more").forEach((a) => a.remove());
    document.querySelectorAll(".needs-paper").forEach((n) => n.remove());
  } else if (PAPER === "figures") {                                // the manuscript's figures: their files are fetched only now
    document.querySelectorAll("#paper img[data-src]").forEach((im) => { im.src = im.dataset.src; });
  } else {
    document.querySelectorAll("#paper .pf > figure, #paper .fig-only").forEach((n) => n.remove());
  }
  openStores(); wire(); renderDownload(); renderCode(); loadSkill();
  if (!webglWorks()) noMap(true, "the browser gives no WebGL context");
  else { try { initMap(); } catch (e) { noMap(true, e.message); } }
  await applyLayer();
  const tab = Q.get("tab"); if (tab && document.getElementById("tab-" + tab)) showTab(tab);
  sendHeight();
}
main();
})();
