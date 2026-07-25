// Pure, framework-free viewer logic (no three.js, no DOM) so the load-bearing
// faithfulness rules — quantile classification determinism (T10) and the LOD-Z
// gate + provenance-badge states (T12) — are unit-testable under plain node.

// ---- T10: quantile classification (pinned, computed once from full scene) ----

// nClasses-1 internal break values from the full value set; deterministic
// (sorted linear interpolation), never recomputed per camera move.
export function quantileBreaks(values, nClasses = 5) {
  const v = values.filter((x) => typeof x === "number" && !Number.isNaN(x))
    .slice().sort((a, b) => a - b);
  if (v.length === 0) return [];
  const breaks = [];
  for (let i = 1; i < nClasses; i++) {
    const p = i / nClasses;
    const idx = p * (v.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    breaks.push(lo === hi ? v[lo] : v[lo] + (v[hi] - v[lo]) * (idx - lo));
  }
  return breaks;
}

// Bin index 0..nClasses-1 for a value, given quantile breaks. null/NaN -> -1
// (the caller renders that as the reserved no-data grey, kept off the ramp).
export function classifyQuantile(value, breaks) {
  if (typeof value !== "number" || Number.isNaN(value)) return -1;
  let i = 0;
  while (i < breaks.length && value >= breaks[i]) i++;
  return i;
}

// Continuous (unclassed) position 0..1 within a fixed/pinned [min,max] domain.
// null/NaN -> -1 (no-data). Domain is never rescaled to the in-view subset.
export function normalizeContinuous(value, domainMin, domainMax) {
  if (typeof value !== "number" || Number.isNaN(value)) return -1;
  if (domainMax <= domainMin) return 0;
  const t = (value - domainMin) / (domainMax - domainMin);
  return Math.max(0, Math.min(1, t));
}

// ---- T12: LOD-Z gate (Rule V04-RMG-01 + PLAN §9.6) ----
// Procedural zone synthesis is PROHIBITED: a strategy with no real zone
// geometry yields a disabled control with a disclosure string, full stop.
export function lodZGate(zoningStrategy) {
  switch (zoningStrategy) {
    case "perimeter_core":
    case "room_layout":
      return { zoneBreakdown: true, floorLevel: false, disclosure: null };
    case "one_zone_per_floor":
      return { zoneBreakdown: false, floorLevel: true, disclosure: null };
    case "single_zone":
      return {
        zoneBreakdown: false, floorLevel: false,
        disclosure: "single zone — no interior subdivision modelled",
      };
    default:
      return {
        zoneBreakdown: false, floorLevel: false,
        disclosure: "not recorded — no real zone geometry",
      };
  }
}

// ---- T12: merged trust badge (shape glyph, never hue alone) ----
// trust_confidence is min(imputation float, rank(archetype)); absent (both-sides
// -absent legacy runs) -> the distinct "not recorded" state, never a default.
export function trustBadge(trustConfidence) {
  if (trustConfidence === null || trustConfidence === undefined) {
    return { glyph: "not_recorded", label: "not recorded" };
  }
  if (trustConfidence >= 0.75) return { glyph: "solid", label: "HIGH" };
  if (trustConfidence >= 0.25) return { glyph: "half", label: "MEDIUM" };
  return { glyph: "hollow", label: "LOW" };
}

// ---- T12: resolution-mode border treatment (no border when not recorded) ----
export function resolutionBorder(resolutionMode) {
  switch (resolutionMode) {
    case "building": return { weight: "thin", label: "building" };
    case "floor": return { weight: "medium", label: "floor" };
    case "fast_zone": return { weight: "heavy", label: "fast_zone" };
    case "zone": return { weight: "heavy", label: "zone" };
    case "auto": return { weight: "medium", label: "auto" };
    default: return { weight: "none", label: "not recorded" };
  }
}

// A field that is absent from the run's artifacts renders as "not recorded",
// never blank and never a fabricated default (T12 detail pane).
export function displayToken(value) {
  if (value === null || value === undefined || value === "") return "not recorded";
  return String(value);
}

// ---- T17 (Phase E, F1): basemap ground-plane placement (pure geometry, no
// THREE/DOM, so it is unit-testable without a browser) ----
// `extentLocal` = [minx, miny, maxx, maxy], scene-local metres (UTM minus
// `+common_origin_utm`) — the SAME frame T04's `context` is emitted in.
// `center` is the loader's recenter offset expressed in that same frame
// (viewer_app.mjs derives it exactly like `_buildContext` derives its own
// `center` from `this.boundingBox.getCenter()` — the documented proxy for
// `this.loaderMatrix`, PLAN Phase-E "Scene seam"). Returns the plane's local
// centre + size so the textured quad registers exactly like `context` does.
export function basemapPlaneLayout(extentLocal, center) {
  const [minx, miny, maxx, maxy] = extentLocal;
  const cx = center && typeof center.x === "number" ? center.x : 0;
  const cy = center && typeof center.y === "number" ? center.y : 0;
  return {
    width: maxx - minx,
    height: maxy - miny,
    x: (minx + maxx) / 2 - cx,
    y: (miny + maxy) / 2 - cy,
  };
}

// A basemap is rendered only when the scene payload actually carries one
// (T19 graceful-degrade: no cached raster for this run -> `scene.basemap` is
// omitted entirely, never a placeholder/fabricated tile).
export function shouldRenderBasemap(basemap) {
  return !!(basemap && Array.isArray(basemap.extent_local)
    && basemap.extent_local.length === 4 && typeof basemap.image === "string"
    && basemap.image.length > 0);
}

// ---- T25: UTCI ground-plane layer -- same well-formed-payload shape check as
// `shouldRenderBasemap`, kept as its own function (not an alias) so a caller
// reading this file finds the UTCI-layer contract documented on its own,
// distinct from the basemap's. `scene.utci_layer` is OMITTED entirely (never
// a placeholder) whenever no run passed `utci_layer_path` to
// `viewer_export.build_scene` (plan §6a: Stage 6 is invoked explicitly, never
// part of a standard run) -- this predicate is what lets the viewer degrade
// to "no UTCI layer at all", same as `shouldRenderBasemap` degrades for a run
// with no cached basemap.
export function shouldRenderUtciLayer(utciLayer) {
  return !!(utciLayer && Array.isArray(utciLayer.extent_local)
    && utciLayer.extent_local.length === 4 && typeof utciLayer.image === "string"
    && utciLayer.image.length > 0);
}

// ---- T18 (Phase E, F2): flat-footprint clarity — derived from EXISTING
// bound provenance (`data_quality_flag` / `provenance_height_m`), NEVER a new
// fabricated attribute. Geometry stays unchanged (Phase-E binding constraint
// 1) — this only flags a distinct visual treatment + a detail-pane line. ----
const NO_HEIGHT_BADGE_TEXT =
  "Height: not in OSM — footprint only (no above-ground massing).";

export function heightMissing(attrs) {
  if (!attrs) return false;
  const flag = attrs.data_quality_flag;
  // Real runs mix "," (Step-1 osm_fetcher tokens) and "|" (Step-2 provenance
  // append) separators in the SAME string — verified on the pilot's own
  // flagged buildings (relation/11171793 / relation/11171765):
  // "no_floors,no_height,no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT". No other
  // token in the vocabulary contains "no_height" as a substring, so a plain
  // substring test is exact and separator-agnostic.
  if (typeof flag === "string" && flag.includes("no_height")) return true;
  return attrs.provenance_height_m === "OSM_MISSING";
}

export function flatFootprintBadge(attrs) {
  return heightMissing(attrs) ? NO_HEIGHT_BADGE_TEXT : null;
}
