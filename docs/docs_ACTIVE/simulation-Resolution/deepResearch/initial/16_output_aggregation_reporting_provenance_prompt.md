# Deep-Research Prompt 16 — OUTPUT AGGREGATION, REPORTING & PROVENANCE across resolution

> SCOPE GUARD — READ FIRST. This is a **results-pipeline** task. The deliverable is how to **roll
> multi-zone EnergyPlus output back to a single building EUI/carbon record** consistently across
> modes, so the same building is comparable regardless of zone count — plus how the chosen
> `resolution_mode` is **recorded as provenance**. It is NOT about the simulation physics (Prompts
> 01–14). If you are writing about anything other than **how per-zone results aggregate to building
> totals, the EUI denominator, and provenance recording**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on the results layer. OpenUBEM parses EnergyPlus output into per-building
EUI, end-use splits, carbon, and IOD (Step 5). When a building has 1 vs N vs ~5N zones, the per-zone
meters must aggregate to the **same building-total semantics** so EUI is comparable across modes, and
the EUI **denominator must stay `footprint × num_floors`** in every mode. We also need the
`resolution_mode` stamped into the artifacts for reproducibility. Treat each cell as a question.

## Role

Building-energy-modelling results analyst. Trace every rule to: the **EnergyPlus I/O Reference**
(meter vs zone-level output: `Output:Meter` building-level totals vs `Zone`-level variables; how
`Zone Multiplier` is already reflected in meters), OpenUBEM's existing Step-5 schema (EUI by end-use,
carbon factors, IOD), and standard reproducibility practice (provenance columns). SI.

## Why this matters (so you scope correctly)

If results are summed from per-zone variables, the aggregation must (a) include every zone exactly
once, (b) correctly account for `Zone Multiplier` if used (Prompt 05) — EnergyPlus meters already do,
zone variables may not — and (c) divide by the **same floor area** in all modes. A subtle error here
makes a resolution comparison meaningless. And the `resolution_mode` must be queryable per building so
results carry their fidelity. We need the aggregation + provenance rules.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Aggregating per-zone output to building totals

| Quantity | Source (building `Output:Meter` vs sum of zone vars) | Zone-Multiplier-safe? | Recommended | Source |
|---|---|---|---|---|
| Total site/source energy | | (meters auto-include multiplier) | | |
| End-use splits (heating/cooling/lights/equip/fans) | | | | |
| Per-zone temperatures (for IOD) | | (area-weighted across zones?) | | |
| Peak demand | | | | |

> Recommend reading **building-level `Output:Meter`** (which already reflects multipliers and all
> zones) rather than summing zone variables, where possible — confirm and note exceptions (IOD needs
> zone temperatures).

### Table 2 — EUI denominator consistency

| Item | Rule | Source |
|---|---|---|
| Floor area = `footprint_area_m2 × num_floors` in ALL modes | (must be identical) | |
| Does splitting/multiplier change the conditioned floor area E+ reports? | | |
| Reconcile E+ reported area vs OpenUBEM's contract area (use contract area?) | | |

### Table 3 — IOD / comfort metric across zones

| Item | Method | Source |
|---|---|---|
| IOD from a single zone (building mode) | | |
| IOD aggregation across N zones (area-weighted? worst zone?) | | |
| Consistency of IOD definition across modes | | |

### Table 4 — Provenance & reproducibility

| Field | Record where | Source |
|---|---|---|
| `resolution_mode` per building | (manifest + Step-5 results column) | |
| `zoning_strategy` actually used (incl. fallbacks) | (already recorded) | |
| `num_zones` per building | (already in manifest) | |
| Seed / version stamping unchanged | | |

---

## Part C — Synthesis (aggregation + provenance rule)

Give: (1) the **aggregation rule** — prefer building-level meters; for zone-level metrics (IOD)
specify the weighting; ensure every zone counted once and multipliers respected; (2) the **denominator
rule** — always `footprint × num_floors`, reconciled with E+ reported area; and (3) the **provenance
fields** to add (`resolution_mode`) so results are self-describing and modes are comparable.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C aggregation + provenance rule.
3. Cite E+ meter-vs-zone-variable semantics and multiplier handling.
4. **"Confidence and caveats":** the aggregation pitfall most likely to corrupt a mode comparison.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Recommend building-meter aggregation** (multiplier-safe) over zone-variable summing, with exceptions.
- **Lock the EUI denominator** to `footprint × num_floors` in every mode.
- **Specify IOD aggregation** across zones.
- **List the provenance fields** to record (`resolution_mode` at minimum).
- **No fabricated precision;** flag GAPs. **Stay on topic** — results aggregation/provenance only.
