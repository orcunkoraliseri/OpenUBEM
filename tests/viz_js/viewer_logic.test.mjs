// Node-native unit tests (no deps) for the load-bearing, framework-free viewer
// logic: T10 quantile-classification determinism + no-data separation, and the
// T12 LOD-Z gate against ALL FOUR zoning_strategy values. Run: `node --test`.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  quantileBreaks, classifyQuantile, normalizeContinuous,
  lodZGate, trustBadge, resolutionBorder, displayToken,
  basemapPlaneLayout, shouldRenderBasemap, heightMissing, flatFootprintBadge,
} from "../../openubem/viz/shell/viewer_logic.mjs";
import {
  NO_DATA_GREY, sampleRamp, classColor, archetypeColor, archetypeSector,
  SECTOR_COLOR, FOOTPRINT_ONLY_MUTED, FOOTPRINT_ONLY_OPACITY,
  buildingFillColor, buildingFillOpacity,
} from "../../openubem/viz/shell/colormaps.mjs";

// ---- T10: quantile classification is deterministic + pinned ----
test("quantileBreaks is deterministic across repeated + reordered input", () => {
  const a = [10, 200, 55, 87, 300, 42, 130, 78, 999, 5, 62, 210];
  const b = a.slice().reverse();
  const ba = quantileBreaks(a, 5);
  const bb = quantileBreaks(b, 5);
  assert.deepEqual(ba, bb, "order independence");
  assert.deepEqual(quantileBreaks(a, 5), ba, "repeat determinism");
  assert.equal(ba.length, 4, "n-1 internal breaks for 5 classes");
  for (let i = 1; i < ba.length; i++) assert.ok(ba[i] >= ba[i - 1], "monotone breaks");
});

test("classifyQuantile bins land in 0..nClasses-1 and NaN/null -> -1 (no-data)", () => {
  const breaks = quantileBreaks([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5);
  for (const v of [1, 5.5, 10]) {
    const b = classifyQuantile(v, breaks);
    assert.ok(b >= 0 && b <= 4, `bin ${b} in range`);
  }
  assert.equal(classifyQuantile(NaN, breaks), -1);
  assert.equal(classifyQuantile(null, breaks), -1);
  assert.equal(classifyQuantile(undefined, breaks), -1);
});

test("no-data grey is distinct from every ramp class colour", () => {
  for (const ramp of ["viridis", "cividis"]) {
    for (let i = 0; i < 5; i++) {
      const c = classColor(ramp, i, 5);
      assert.notDeepEqual(c, NO_DATA_GREY, `${ramp} class ${i} != no-data grey`);
    }
  }
  // bin index -1 maps to the reserved grey.
  assert.deepEqual(classColor("viridis", -1, 5), NO_DATA_GREY);
});

test("normalizeContinuous clamps to [0,1] over a fixed domain", () => {
  assert.equal(normalizeContinuous(50, 0, 100), 0.5);
  assert.equal(normalizeContinuous(-10, 0, 100), 0);
  assert.equal(normalizeContinuous(500, 0, 100), 1);
  assert.equal(normalizeContinuous(NaN, 0, 100), -1);
});

test("sampleRamp endpoints are stable", () => {
  assert.deepEqual(sampleRamp("viridis", 0), [68, 1, 84]);
  assert.deepEqual(sampleRamp("viridis", 1), [253, 231, 37]);
});

// ---- T12: LOD-Z gate against ALL FOUR zoning_strategy values ----
test("lodZGate: perimeter_core + room_layout enable zone breakdown", () => {
  for (const s of ["perimeter_core", "room_layout"]) {
    assert.deepEqual(lodZGate(s), { zoneBreakdown: true, floorLevel: false, disclosure: null });
  }
});

test("lodZGate: one_zone_per_floor enables floor-level only", () => {
  assert.deepEqual(lodZGate("one_zone_per_floor"),
    { zoneBreakdown: false, floorLevel: true, disclosure: null });
});

test("lodZGate: single_zone disables both with a disclosure (no synthesis)", () => {
  const g = lodZGate("single_zone");
  assert.equal(g.zoneBreakdown, false);
  assert.equal(g.floorLevel, false);
  assert.ok(g.disclosure && g.disclosure.length > 0);
});

test("lodZGate: unknown/legacy strategy -> disabled + 'not recorded'", () => {
  const g = lodZGate(undefined);
  assert.equal(g.zoneBreakdown, false);
  assert.equal(g.floorLevel, false);
  assert.match(g.disclosure, /not recorded/);
});

// ---- T12: trust badge + resolution border + verbatim token ----
test("trustBadge: shape glyph, distinct not-recorded for absent", () => {
  assert.equal(trustBadge(null).glyph, "not_recorded");
  assert.equal(trustBadge(undefined).glyph, "not_recorded");
  assert.equal(trustBadge(0.9).glyph, "solid");
  assert.equal(trustBadge(0.5).glyph, "half");
  assert.equal(trustBadge(0.1).glyph, "hollow");
});

test("resolutionBorder: absent mode -> no border, not a fabricated default", () => {
  assert.equal(resolutionBorder(undefined).weight, "none");
  assert.equal(resolutionBorder("building").weight, "thin");
  assert.equal(resolutionBorder("zone").weight, "heavy");
});

test("displayToken: absent -> 'not recorded', never blank", () => {
  assert.equal(displayToken(undefined), "not recorded");
  assert.equal(displayToken(null), "not recorded");
  assert.equal(displayToken(""), "not recorded");
  assert.equal(displayToken(0), "0");
  assert.equal(displayToken("PrimarySchool"), "PrimarySchool");
});

// ---- colormaps: 30-archetype vocab maps into sector hue-families ----
test("archetypeColor + sector labels resolve for known + unknown ids", () => {
  assert.equal(archetypeSector("MediumOffice"), "Office");
  assert.equal(archetypeSector("MidriseApartment"), "Residential");
  assert.equal(archetypeSector("NotAnArchetype"), "Fallback");
  assert.equal(archetypeColor("NotAnArchetype").length, 3);
});

// ---- CP-2 FIX: present-but-unknown (Fallback) must never be pixel-identical to
// true no-data. This distinctness invariant is the regression guard. ----
test("Fallback swatch is byte-distinct from no-data grey", () => {
  assert.notDeepEqual(SECTOR_COLOR.Fallback, NO_DATA_GREY,
    "present-but-unknown classification must not reuse the no-data grey");
});

test("Fallback swatch is byte-distinct from every sequential ramp class", () => {
  for (const ramp of ["viridis", "cividis"]) {
    for (let i = 0; i < 5; i++) {
      assert.notDeepEqual(SECTOR_COLOR.Fallback, classColor(ramp, i, 5),
        `Fallback collides with ${ramp} class ${i}`);
    }
  }
});

test("Fallback swatch is byte-distinct from every other sector colour", () => {
  for (const [name, rgb] of Object.entries(SECTOR_COLOR)) {
    if (name === "Fallback") continue;
    assert.notDeepEqual(SECTOR_COLOR.Fallback, rgb, `Fallback collides with ${name}`);
  }
});

test("OpenUBEMUnknown (present) routes to Fallback, NOT to no-data grey", () => {
  assert.deepEqual(archetypeColor("OpenUBEMUnknown"), SECTOR_COLOR.Fallback);
  assert.notDeepEqual(archetypeColor("OpenUBEMUnknown"), NO_DATA_GREY);
  // an unmapped-but-present id must also land on Fallback, never no-data grey.
  assert.deepEqual(archetypeColor("SomeFutureArchetype"), SECTOR_COLOR.Fallback);
  assert.notDeepEqual(archetypeColor("SomeFutureArchetype"), NO_DATA_GREY);
});

// ---- T17 (Phase E, F1): basemap ground-plane placement ----
test("basemapPlaneLayout: size + centre derived from extent_local, no center offset", () => {
  const layout = basemapPlaneLayout([0, 0, 100, 40], null);
  assert.deepEqual(layout, { width: 100, height: 40, x: 50, y: 20 });
});

test("basemapPlaneLayout: subtracts the loader recenter offset (same frame as context)", () => {
  const layout = basemapPlaneLayout([1000, 2000, 1100, 2040], { x: 1000, y: 2000, z: 0 });
  assert.equal(layout.width, 100);
  assert.equal(layout.height, 40);
  assert.equal(layout.x, 50); // (1000+1100)/2 - 1000
  assert.equal(layout.y, 20); // (2000+2040)/2 - 2000
});

test("basemapPlaneLayout: center with only some numeric fields degrades safely", () => {
  const layout = basemapPlaneLayout([0, 0, 10, 10], {});
  assert.equal(layout.x, 5);
  assert.equal(layout.y, 5);
});

test("shouldRenderBasemap: present + well-formed scene.basemap -> true", () => {
  assert.equal(shouldRenderBasemap({
    image: "data:image/png;base64,AAAA", extent_local: [0, 0, 1, 1],
  }), true);
});

test("shouldRenderBasemap: absent/malformed -> false, never a fabricated placeholder", () => {
  assert.equal(shouldRenderBasemap(undefined), false);
  assert.equal(shouldRenderBasemap(null), false);
  assert.equal(shouldRenderBasemap({}), false);
  assert.equal(shouldRenderBasemap({ image: "data:...", extent_local: [0, 0, 1] }), false);
  assert.equal(shouldRenderBasemap({ image: "", extent_local: [0, 0, 1, 1] }), false);
});

// ---- T18 (Phase E, F2): flat-footprint clarity ----
test("heightMissing: data_quality_flag containing no_height (pipe-joined) -> true", () => {
  assert.equal(heightMissing({ data_quality_flag: "no_year|no_height" }), true);
});

test("heightMissing: real pilot value — mixed comma+pipe separators -> true", () => {
  // Verbatim from the pilot's relation/11171793 (Grand Central Terminal):
  assert.equal(heightMissing({
    data_quality_flag: "no_floors,no_height,no_year|VINTAGE_NAN_PERMISSIVE_DEFAULT",
  }), true);
});

test("heightMissing: provenance_height_m OSM_MISSING alone -> true", () => {
  assert.equal(heightMissing({ provenance_height_m: "OSM_MISSING", data_quality_flag: "" }), true);
});

test("heightMissing: normal building (neither signal) -> false", () => {
  assert.equal(heightMissing({ data_quality_flag: "no_year", provenance_height_m: "OSM_OBSERVED" }), false);
  assert.equal(heightMissing({}), false);
  assert.equal(heightMissing(undefined), false);
});

test("flatFootprintBadge: text only when height is missing, null otherwise", () => {
  assert.match(flatFootprintBadge({ data_quality_flag: "no_height" }), /not in OSM/);
  assert.equal(flatFootprintBadge({ data_quality_flag: "no_year" }), null);
});

// ---- Debug fix D03 (docs_ACTIVE/3D/debug/PLAN_3dviz_debug_representation.md):
// footprint-only buildings still show their real value ----
// The former T22 mute painted a flat beige over real EUI/archetype output for
// ANY building with missing OSM height (up to 100% of buildings in some
// cells). Corrected contract: footprint-only buildings flow through to the
// SAME colour lookup as every other building, at full opacity; "no OSM
// height" is conveyed only by the dashed outline overlay + detail-pane badge.
const EUI_OPTS = { mode: "eui", classified: true, rampName: "viridis", breaks: quantileBreaks([50, 100, 150, 200, 250], 5), min: 50, max: 250 };

test("buildingFillColor: footprint-only building still gets its real viridis EUI colour, NOT the old muted placeholder", () => {
  const footprintOnly = { data_quality_flag: "no_floors,no_height,no_year", total_eui_kwh_m2: 180 };
  const color = buildingFillColor(footprintOnly, EUI_OPTS);
  const expected = classColor("viridis", classifyQuantile(180, EUI_OPTS.breaks), 5);
  assert.deepEqual(color, expected, "footprint-only must flow through to the same EUI ramp as any other building");
  assert.notDeepEqual(color, FOOTPRINT_ONLY_MUTED, "must not paint over the real value with the retired beige");
});

test("buildingFillColor: normal building (real OSM height) is unaffected — same EUI colour path", () => {
  const normal = { data_quality_flag: "no_year", total_eui_kwh_m2: 180 };
  const color = buildingFillColor(normal, EUI_OPTS);
  const expected = classColor("viridis", classifyQuantile(180, EUI_OPTS.breaks), 5);
  assert.deepEqual(color, expected);
  assert.notDeepEqual(color, FOOTPRINT_ONLY_MUTED);
});

test("buildingFillColor: footprint-only building still gets its real archetype sector colour in archetype mode", () => {
  const footprintOnly = { data_quality_flag: "no_height", archetype_id: "MediumOffice" };
  const color = buildingFillColor(footprintOnly, { mode: "archetype" });
  assert.deepEqual(color, archetypeColor("MediumOffice"));
  assert.notDeepEqual(color, FOOTPRINT_ONLY_MUTED);
});

test("FOOTPRINT_ONLY_MUTED constant (kept but unused) is still byte-distinct from NO_DATA_GREY and Fallback", () => {
  assert.notDeepEqual(FOOTPRINT_ONLY_MUTED, NO_DATA_GREY,
    "must not be confused with never-simulated / failed buildings");
  assert.notDeepEqual(FOOTPRINT_ONLY_MUTED, SECTOR_COLOR.Fallback,
    "must not be confused with present-but-unclassified archetype");
});

test("FOOTPRINT_ONLY_MUTED constant (kept but unused) is still byte-distinct from every EUI ramp class colour", () => {
  for (const ramp of ["viridis", "cividis"]) {
    for (let i = 0; i < 5; i++) {
      assert.notDeepEqual(FOOTPRINT_ONLY_MUTED, classColor(ramp, i, 5),
        `collides with ${ramp} class ${i}`);
    }
  }
});

test("buildingFillOpacity: footprint-only AND normal buildings both fully opaque (1.0) — fill is never muted", () => {
  assert.equal(buildingFillOpacity({ data_quality_flag: "no_height" }), 1.0);
  assert.equal(buildingFillOpacity({ data_quality_flag: "no_year" }), 1.0);
  assert.equal(buildingFillOpacity({}), 1.0);
  assert.ok(FOOTPRINT_ONLY_OPACITY > 0 && FOOTPRINT_ONLY_OPACITY < 1, "retired constant shape unchanged (kept but unused)");
});
