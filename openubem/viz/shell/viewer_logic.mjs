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
