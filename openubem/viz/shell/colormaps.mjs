// Colour system (T10). One source of truth for the viewer palette. Sequential
// ramps are perceptually-uniform + CVD-tolerant (viridis default, cividis for
// the CVD toggle). Categorical archetypes are grouped into sector hue-families
// with ALWAYS-shown text labels (never colour alone) — the 30-archetype vocab
// far exceeds any 8-colour ceiling. One neutral grey is reserved for no-data,
// kept OFF every ramp.

import { classifyQuantile, normalizeContinuous } from "./viewer_logic.mjs";

export const NO_DATA_GREY = [176, 176, 176]; // distinct from every ramp colour

// 10-stop anchors (matplotlib), linearly interpolated.
const VIRIDIS = [
  [68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142], [38, 130, 142],
  [31, 158, 137], [53, 183, 121], [110, 206, 88], [181, 222, 43], [253, 231, 37],
];
const CIVIDIS = [
  [0, 32, 77], [0, 51, 111], [57, 72, 107], [87, 93, 109], [112, 113, 115],
  [138, 135, 121], [166, 157, 117], [196, 181, 108], [228, 207, 91], [255, 234, 70],
];

export const RAMPS = { viridis: VIRIDIS, cividis: CIVIDIS };

export function sampleRamp(name, t) {
  const anchors = RAMPS[name] || VIRIDIS;
  const x = Math.max(0, Math.min(1, t)) * (anchors.length - 1);
  const lo = Math.floor(x);
  const hi = Math.min(anchors.length - 1, lo + 1);
  const f = x - lo;
  return [0, 1, 2].map((k) =>
    Math.round(anchors[lo][k] + (anchors[hi][k] - anchors[lo][k]) * f));
}

// Quantile class colour: sample the ramp at the class midpoint.
export function classColor(name, binIndex, nClasses) {
  if (binIndex < 0) return NO_DATA_GREY.slice();
  return sampleRamp(name, (binIndex + 0.5) / nClasses);
}

// Sector hue-families. Distinct, roughly CVD-tolerant; text labels always shown
// so hue is never the sole channel (WCAG non-colour-only, PLAN §9.3).
export const SECTOR_COLOR = {
  "Office": [0, 114, 178],        // blue
  "Retail": [213, 94, 0],         // vermillion
  "Food Service": [230, 159, 0],  // orange
  "Lodging": [204, 121, 167],     // reddish purple
  "Residential": [0, 158, 115],   // bluish green
  "Healthcare": [86, 180, 233],   // sky blue
  "Education": [240, 228, 66],    // yellow
  "Government": [140, 86, 75],     // brown
  "Data Center": [148, 103, 189],  // purple
  "Research": [23, 190, 207],      // cyan
  "Industrial": [127, 127, 127],   // grey-neutral (warehouses)
  "High-Rise": [188, 189, 34],     // olive
  // Present-but-unknown classification (OpenUBEMUnknown / any unmapped id). MUST
  // be visibly distinct from NO_DATA_GREY: a present class is never absence. Muted
  // dark slate-violet — off both ramps, clear of every sector hue, darker than
  // no-data grey (verified byte-distinct + margin in FALLBACK_SECTOR test).
  "Fallback": [108, 96, 128],
};

// archetype_id -> sector (from openubem/data/openstudio_archetypes.json, 30 ids).
export const ARCHETYPE_SECTOR = {
  SmallOffice: "Office", SmallOfficeDetailed: "Office", MediumOffice: "Office",
  MediumOfficeDetailed: "Office", LargeOffice: "Office", LargeOfficeDetailed: "Office",
  RetailStandalone: "Retail", RetailStripmall: "Retail", SuperMarket: "Retail",
  FullServiceRestaurant: "Food Service", QuickServiceRestaurant: "Food Service",
  SmallHotel: "Lodging", LargeHotel: "Lodging",
  MidriseApartment: "Residential", HighriseApartment: "Residential",
  Hospital: "Healthcare", Outpatient: "Healthcare",
  PrimarySchool: "Education", SecondarySchool: "Education", College: "Education",
  Courthouse: "Government",
  SmallDataCenterHighITE: "Data Center", SmallDataCenterLowITE: "Data Center",
  LargeDataCenterHighITE: "Data Center", LargeDataCenterLowITE: "Data Center",
  Laboratory: "Research", Warehouse: "Industrial",
  TallBuilding: "High-Rise", SuperTallBuilding: "High-Rise",
  OpenUBEMUnknown: "Fallback",
};

export function archetypeColor(archetypeId) {
  const sector = ARCHETYPE_SECTOR[archetypeId] || "Fallback";
  return (SECTOR_COLOR[sector] || NO_DATA_GREY).slice();
}

export function archetypeSector(archetypeId) {
  return ARCHETYPE_SECTOR[archetypeId] || "Fallback";
}

// ---- T22 (Phase F) constants — UNUSED since the debug fix (D01, PLAN_3dviz_
// debug_representation.md §6.2): kept exported so the diff stays minimal, but
// no longer read by `buildingFillColor` / `buildingFillOpacity`. Footprint-only
// buildings now show their real EUI/archetype fill; "no OSM height" is
// conveyed only by the dashed outline overlay + detail-pane badge, not fill.
export const FOOTPRINT_ONLY_MUTED = [228, 223, 214]; // #E4DFD6
export const FOOTPRINT_ONLY_OPACITY = 0.45;

// One source of truth for per-building fill colour (T10/T11). Debug fix
// (docs/docs_ACTIVE/3D/debug/PLAN_3dviz_debug_representation.md D01): the
// former T22 footprint-only mute short-circuited here BEFORE the EUI/archetype
// lookup, painting a flat beige over real simulation output for any building
// whose OSM height was missing (up to 100% of buildings in some cells). EUI
// and archetype are real and bound in `attrs` regardless of height provenance
// — footprint-only buildings now flow through to the same lookup as every
// other building. The "no OSM height" fact is conveyed ONLY by the dashed
// outline overlay (`viewer_app.mjs::_buildFlatFootprintOverlay`) and the
// detail-pane badge (`flatFootprintBadge`), never by fill colour/opacity.
// `attrs` = the bound CityJSON attributes for one building; `opts` = { mode,
// classified, rampName, breaks, min, max } from the Viewer's current view state.
export function buildingFillColor(attrs, opts) {
  if (opts.mode === "archetype") {
    // routes unmapped ids to the distinct Fallback swatch, never no-data grey.
    return attrs.archetype_id === undefined ? NO_DATA_GREY.slice() : archetypeColor(attrs.archetype_id);
  }
  const v = attrs.total_eui_kwh_m2;
  if (typeof v !== "number" || Number.isNaN(v)) return NO_DATA_GREY.slice();
  if (opts.classified) {
    return classColor(opts.rampName, classifyQuantile(v, opts.breaks), 5);
  }
  return sampleRamp(opts.rampName, normalizeContinuous(v, opts.min, opts.max));
}

export function buildingFillOpacity(attrs) {
  return 1.0;
}
