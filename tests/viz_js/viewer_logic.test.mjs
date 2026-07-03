// Node-native unit tests (no deps) for the load-bearing, framework-free viewer
// logic: T10 quantile-classification determinism + no-data separation, and the
// T12 LOD-Z gate against ALL FOUR zoning_strategy values. Run: `node --test`.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  quantileBreaks, classifyQuantile, normalizeContinuous,
  lodZGate, trustBadge, resolutionBorder, displayToken,
} from "../../openubem/viz/shell/viewer_logic.mjs";
import {
  NO_DATA_GREY, sampleRamp, classColor, archetypeColor, archetypeSector,
  SECTOR_COLOR,
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
