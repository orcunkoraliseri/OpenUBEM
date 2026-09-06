# DECISION REQUEST D-EU-37 — extend the `D-EU-04-G` typology table to recover Lyon's 176 mid-rise buildings?

- **Date:** 2026-09-04
- **Arc:** European locations — full-fleet expansion
- **Record:** `STATE_european_locations_v5.md` `FINDING 254`, `FINDING 251`/`D-EU-101`;
  `previous/STATE_european_locations_v2.md:280-284` (original `D-EU-37`, opened 2026-08-28, never ruled)
- **Finding:** `FINDING 254` — root-cause classification of the remaining full-fleet gap
- **Blocks:** nothing downstream today (fleet ships at 2,890/4,186 either way); only the fleet-coverage ceiling
- **Ruled:** **2026-09-04 — option 1 taken.** Owner's own words: *"100% full"* / *"make it possible."*
  Implemented as `FINDING 255`: `openubem/semantic/european_archetype_mapping.py:199-200`. Lyon
  `population_prepared` 293→469 (+176, exact match to the 176-building measurement below). Fleet
  2,890→3,066/4,186 (73.2 %).

---

## 1. The one-sentence version

Lyon has 186 residential buildings excluded as `TYPOLOGY_SIGNALS_DISAGREE` because they fall between the two
occupied buckets of the `D-EU-04-G` typology rule; 176 of them are an unambiguous, tightly-clustered shape
(2–12 dwellings, 5–9 storeys) that the rule was never given a bucket for, and recovering them means adding a
new numeric threshold that no file in the repo currently justifies.

## 2. What the rule does today (`openubem/semantic/european_archetype_mapping.py:185-201`)

```
dwellings == 1  & storeys <= 4   -> SFH/TH (by footprint adjacency)
2 <= dwellings <= 12 & storeys <= 4   -> MFH
dwellings >= 15 & storeys >= 5   -> AB
dwellings in (13, 14)            -> excluded (registry gap, separate code)
everything else                  -> TYPOLOGY_SIGNALS_DISAGREE
```

Measured live against Lyon's manifest (`openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg`),
the 186 excluded split three ways:

| Shape | Count | Falls through because |
|---|---|---|
| `2 <= dwellings <= 12`, `storeys` 5–9 (57/71/37/9/2 by storey) | **176** | too tall for the `MFH` bucket (needs `storeys <= 4`), too few dwellings for the `AB` bucket (needs `dwellings >= 15`) |
| `dwellings >= 15`, `storeys <= 4` | 8 | too short for `AB` (needs `storeys >= 5`), too many dwellings for `MFH` (needs `dwellings <= 12`) |
| `dwellings == 1`, `storeys >= 5` | 2 | too tall for the single-dwelling bucket (needs `storeys <= 4`) |

The 176-building group is the only one worth ruling on: it is a single, coherent shape (ordinary low-rise
apartment blocks, no outliers in the storey distribution), not scattered noise.

## 3. Why this needs a ruling, not a fix

`tabula_archetypes_fr.json` (the file the module's own docstring cites as the source for "every threshold
below") carries type and period codes only — no per-storey or per-dwelling-count calibration data. There is no
number in the repo that says where the `MFH`/`AB` boundary should sit for a 5–9-storey, 2–12-dwelling building.
Any threshold added here is a new policy call, not a transcription — exactly what the standing rule ("stop and
ask on spec ambiguity, never invent") requires be put to the owner rather than picked by an executor.

This is not a new question: `D-EU-37` was opened 2026-08-28 asking the identical thing (then against
`UNMAPPABLE_RESIDENTIAL_TYPE` — Lyon 226, Madrid 77, London 345) and was never ruled; the recommendation on
file was "measure first." Madrid's and London's shares of that original gap have since closed by unrelated
fixes (footprint-adjacency tag mapping, `FINDING 251`/`253`) — Lyon's 186 is what's left of the same open
question, now measured exactly.

## 4. Options

1. **Widen the rule to cover the 176-building shape.** Add a fourth bucket, e.g.
   `2 <= dwellings <= 12 & 5 <= storeys <= 9 -> MFH` (or a separate mid-rise code if the owner wants heating
   demand distinguished from the low-rise `MFH` archetype). Recovers 176 of Lyon's 186; fleet rises from
   2,890 to ~3,066 of 4,186 (73.2 %). The 8 short-and-dense and 2 tall-and-single outliers stay excluded
   either way — too few to generalize a rule from, and not part of this request.
2. **Leave the rule as is.** Lyon's 186 remain a documented, fail-closed exclusion; no new threshold is
   invented. **This is not "the ceiling"** — 4,186/4,186 is the only ceiling. It means this specific 176
   stays unrecovered while the true hard-data-gap buildings (crashes, missing storeys, no-EPC match,
   period-straddle — genuinely un-fixable without inventing source data) stay unrecovered for a different,
   non-policy reason.

**Director's read, not a ruling:** the rule was deliberately built to read every number off a source document
and refuse to guess (module docstring, line 41) — this is the only remaining exclusion category where "push
further" means inventing a number rather than fixing a bug or filling a hard data gap. Either option is
defensible; this is exactly the kind of call the standing rule reserves for the owner, not the director.

## 5. Next free identifiers after this ruling

`FINDING 254` and `D-EU-101` are consumed. This request reopens `D-EU-37` rather than claiming a new number.
Next free: `FINDING 255`, `D-EU-102`.
