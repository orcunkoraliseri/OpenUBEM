# DECISION REQUEST D-EU-33 — 51/4,186 dwelling-layout coverage is not acceptable; mandate full floor/dwelling division

- **Date:** 2026-08-28
- **Arc:** European locations x Step 8
- **Record:** `openubem/outputs/eu_evidence/EU-12/RESULTS_EU-12.md` §2–§4;
  `validation/VALIDATION_EU-12_dwelling_layout_popup_2026-08-28.md`
- **Finding:** `FINDING EU-12-01` (floor-0-only extrusion), `FINDING EU-12-02` (scheme mismatch vs MVP Figure 4)
- **Blocks:** the pop-up showing a real subdivision for any building outside 51/4,186 (all Madrid)
- **Ruled:** 2026-08-28, by owner instruction — full coverage is mandatory, not aspirational

---

## 1. The one-sentence version

Of 4,186 residential buildings across the four districts, only 51 (all Madrid, 1.2 % of the fleet) show a
drawn dwelling subdivision when clicked; the owner has ruled this is unacceptable and instructed that all
simulated buildings be floor/dwelling-divided.

## 2. What is actually broken, split by mechanism (measured, `RESULTS_EU-12.md` §3)

| Mechanism | Count | Real constraint | Fixable how |
|---|---|---|---|
| `FINDING EU-12-01` — emitted layout only extrudes storey 0 | 51/51 (100% of "successes") | `european_layout_to_zone_specs` called once at `floor_index=0` | Mechanical: stack the same per-floor partition at every storey |
| `NON_CONVEX_TOPOLOGY_UNSUPPORTED` | 609 Madrid | `equal_strip_long_axis` only cuts convex shapes | Algorithmic: general polygon-decomposition partition |
| `COURTYARD_TOPOLOGY_UNSUPPORTED` | 115 Madrid | same partition can't handle a hole | Algorithmic: same fix as above |
| `MISSING_OBSERVED_DWELLING_COUNT` | 382 (3 Madrid + all 297 Lyon + all 82 London) | nothing to partition into | Data-policy: run the existing four-tier imputation cascade, tagged `IMPUTED` |
| `NARROW_FOOTPRINT_LT_8M` | 183 Madrid | ruled `GEO-04` physical minimum for ≥2.5 m facade contact per dwelling | Already floor-divided (massing box, one zone/floor); sub-8 m dwelling-level split has no physical basis under the standing audit |

## 3. Ruling

**Options 1–3 are RULED MANDATORY.** Option 4 is RULED carried as-is, with rationale stated so the owner can
override on sight.

1. **Fix `FINDING EU-12-01` first.** Every `DWELLING_LAYOUT_EMITTED` building must show its dwelling
   partition repeated at every storey (`floors` holds `n_storey` entries, not 1), not a new partition per
   floor — apartment stacks are assumed identical floor-to-floor unless the footprint itself changes.
2. **Extend the partition algorithm to non-convex and courtyard footprints** (724 Madrid buildings) via a
   general method (e.g. convex decomposition of the footprint, then strip-partition each convex piece; or an
   equivalent the executor justifies) — subject to the **same** `audit_european_floor_partition` tolerances
   already ruled (area-error fraction, no overlap/gap, ≥2.5 m facade contact). The audit must not be
   loosened to make more buildings pass.
3. **Impute missing dwelling counts** (382 buildings, Lyon/London entirely) through the existing four-tier
   cascade (`MVP_european_locations.md` Figure 2: fusion → spatial → opt-in ML → statistical), tagged
   `IMPUTED_DWELLING_COUNT` with the tier and source recorded in the side-car — never silently defaulted, and
   never reported as `DWELLING_LAYOUT_EMITTED` on the same footing as an observed count without that tag
   visible in the pop-up.
4. **`NARROW_FOOTPRINT_LT_8M` (183) stays a massing box** — already floor-divided (one zone per floor); a
   sub-8 m footprint cannot host a ≥2.5 m-facade-contact dwelling under the standing `GEO-04` audit without
   relaxing that audit itself, which this DR does not authorise. If the owner wants this relaxed too, that is
   a separate ruling on `GEO-04`, not folded in here.

## 4. What "coverage" must be reported as, after the fix

Every simulated building must land in exactly one of: `DWELLING_LAYOUT_EMITTED` (observed count, any
topology), `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` (imputed count, any topology), or
`FALLBACK_NARROW_FOOTPRINT` (the one surviving fallback reason). `NON_CONVEX_TOPOLOGY_UNSUPPORTED` and
`COURTYARD_TOPOLOGY_UNSUPPORTED` must not appear in the post-fix census at all — if either still does for a
specific footprint, that building's failure must be individually named and justified, not folded into a bulk
fallback count.

## 5. Next free identifiers after this ruling

`D-EU-33` and `D-EU-34` (companion Bologna ruling) are both consumed today. Next free identifier `D-EU-35`.
