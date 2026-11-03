# G6 — Institutional cellular

> **Layout family:** classroom-wing (schools/college) + cellular-departmental (hospital/outpatient/lab) ·
> **Template applies:** ✅ **yes** (corridor + cellular rooms + assembly blocks; hospital = functional-proxy
> core+perim) · **Locked step:** S5 (hardest, last). Backing design:
> `../Design_layoutgenerator.md` §5.3 (Family C classroom-wing), §5.7 (Family B′ cellular-departmental),
> §3.1 (G6), §10 (College + Laboratory corrections).

## Members (6 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones (as-modeled) | Status |
|---|---|---|---|---|
| `ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled_NECB17_Z7A_v221.idf` | PrimarySchool | classroom-wing | **25** (classrooms + pods + assembly), 1 storey | ❌ no engine |
| `ASHRAE901_SchoolSecondary_STD2022_Buffalo_50pct_downscaled_NECB17_Z7A_v221.idf` | SecondarySchool | classroom-wing | **46** total · ~23/floor, 2 storeys | ❌ no engine |
| `College_90.1-2019_6A_Buffalo_NECB17_Z7A_v221.idf` | College | **classroom-wing** (§10 correction) | **117** | ❌ no engine |
| `ASHRAE901_Hospital_STD2022_Buffalo_NECB17_Z7A_v221.idf` | Hospital | cellular-departmental → functional-proxy core+perim | **55** total · 15–17/floor | ❌ no engine (degrades) |
| `ASHRAE901_OutPatientHealthCare_STD2022_Buffalo_NECB17_Z7A_v221.idf` | Outpatient | core+perimeter | **118** total · 5/floor (clean core/perim) | ❌ no engine (degrades) |
| `Laboratory_90.1-2019_6A_Buffalo_NECB17_Z7A_v221.idf` | Laboratory | **cellular-departmental** hybrid (§10 correction) | **24** (lab wing + office wing) | ❌ no engine |

**Why grouped together:** cellular buildings — many small rooms off corridors, plus large single-space
assembly blocks (gym, cafeteria, auditorium, labs). Floorplates read as **wing/pod (finger-plan)** for
schools/college and **SE/NW corridor splits (L/cross)** for hospital/outpatient (§10). **§10 corrections:**
College is classroom-wing (not a MediumOffice proxy); Laboratory is a lab-wing + office-wing hybrid.

## Kit-of-parts (zero-fitted)

- **Classroom-wing (schools/college):** corridor **2.44 m** (8 ft; IBC 1020 min + Neufert K-12);
  classroom module **9.14 × 9.14 m ≈ 83.6 m²**, cap **110 m²/room**, perimeter depth 5.0 m. Assembly
  blocks (gym/cafeteria/auditorium/library) = **single zones**, not packed.
- **Cellular-departmental / hospital proxy:** reuse Family B core+perim — **5–6 zones/floor**
  (4 cardinal perimeter + core [+ corridor]). Perimeter ← envelope-sensitive programs (patient/exam rooms,
  offices); core ← internal-load programs (OR, ICU, labs) via area-weighted load blend (a LATER phase).
  Patient-room module 4.57 × 6.10 m (27.87 m²) is reference-only. **OSM gives no department map** — locating
  departments is fabricated precision (L10 §3), so the functional proxy is the only defensible design.

## Recipe + shape behaviour

- **Schools/college:** decompose footprint into **classroom wings** (narrow, high aspect) vs **assembly
  blocks** (wide, compact) via a shape-split heuristic → wings take Family A corridor recipe with the
  classroom module → assembly blocks = single zones. Secondary school stacks 2 storeys with aligned cores.
  The **wing-vs-block split is the novel/hardest design piece.**
- **Hospital/outpatient/lab:** Family B core+perim geometry; only the load-blend differs (later). Outpatient
  is already a clean 5-zone core/perim.

## Alternatives to render (A = DOE default)

- **A** double-loaded corridor wings + single-zone assembly blocks.
- **B** single-loaded daylit wings (schools) / single-corridor (hospital).
- **C** racetrack double-corridor (hospital) / courtyard finger-plan (schools).

## Reference figure

Pending (S5, hardest / last). No G6 figure signed yet.

## Status caveat

**DECISION (user 2026-07-04, revisable): Hospital is SKIPPED in layout generation** — its layout is already
highly complex, so we keep the DOE structure and only handle rectangular/square footprints; complex shapes
stay per-floor. Hospital is effectively **out of the layout generator**.

Schools/college still need the new **wing/block classifier** (the deferred "T13c" slice, depends on Family A).
Outpatient is a clean 5-zone core/perim and stays in that family. No engine today.

## Provenance

Design §3.1 (G6), §5.3 (Family C classroom-wing), §5.7 (Family B′ hospital proxy), §10 (College +
Laboratory corrections, verified zone counts), open decision #4 (hospital proxy).
