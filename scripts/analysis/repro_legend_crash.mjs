// Throwaway repro: does viewer_app.mjs's _buildLegend() throw when a scene
// has zero buildings with a numeric total_eui_kwh_m2 (as observed in both
// broken layout_assign viewer HTML files)? Uses the REAL, unmodified
// quantileBreaks from viewer_logic.mjs -- no mocking of the load-bearing logic.
import { quantileBreaks } from "../../openubem/viz/shell/viewer_logic.mjs";

// Mirrors Viewer._buildAttributeTables() with an empty eui array (T05:
// total_eui_kwh_m2 absent on every CityObject in the broken export).
const eui = [];
const euiBreaks = quantileBreaks(eui, 5);
const euiMin = eui.length ? Math.min(...eui) : 0;
const euiMax = eui.length ? Math.max(...eui) : 1;
console.log("euiBreaks =", JSON.stringify(euiBreaks), " euiMin =", euiMin, " euiMax =", euiMax);

// Mirrors Viewer._buildLegend()'s classified branch verbatim
// (viewer_app.mjs lines 582-589 / bundled viewer.js lines 26231-26238).
const classified = true; // Viewer's default (this.classified = true;)
const breaks = euiBreaks;
try {
  if (classified) {
    const edges = [euiMin, ...breaks, euiMax];
    console.log("edges =", JSON.stringify(edges));
    for (let i = 0; i < 5; i++) {
      const label = `${edges[i].toFixed(0)} - ${edges[i + 1].toFixed(0)}`;
      console.log(`  row ${i}: ${label}`);
    }
  }
  console.log("NO CRASH");
} catch (e) {
  console.log("CRASHED:", e.constructor.name, "-", e.message);
}
