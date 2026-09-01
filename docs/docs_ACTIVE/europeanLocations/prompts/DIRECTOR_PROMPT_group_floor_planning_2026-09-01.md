# Director prompt — floor planning for the ten building groups

**Opened 2026-09-01. Self-contained: nothing else has to be read to start.**
Replaces `previous/DIRECTOR_PROMPT_european_locations.md` and
`previous/PROMPT_EU-18c_viewer_idf_plans_2026-09-01.md`.

---

## 0. The job

Every residential building in the four districts must get a floor plan: **thermal zones (flats) plus one
circulation zone**, cut from its own footprint. The owner's pipeline, in his words:

> *filter: dividing building floor plans into the group · assign floor type: based on the floor groups
> assign floor types with circulation and thermal zones · reach 95 % floor assignment for all residential
> buildings*

Work **one group at a time**. Never rebuild the whole fleet to test an idea — the owner has said so twice:
*"every time we are trying to edit all buildings and we are consuming a lot of resources."*

The visible deliverable is one file:

**`docs/docs_ACTIVE/europeanLocations/rules/RULES_dwelling_layout_groups_2026-09-01.html`**

Ten sheets, one per group. Each sheet shows the same building twice — the plate as surveyed, then the same
plate cut into flats and a core — beside the filter that selects the group, the plate statistics, the
circulation rule, the zone count and the scheme name. This document *is* the specification. When a rule
changes, the sheet changes with it.

---

## 1. The ten groups

Classifier: first match wins, terminal bucket last (`scripts/eu20_morphology_atlas.py:200-224`).
Counts measured over the four districts, 2026-09-01.

| # | Group key | Shown as | Filter | Buildings | With a plan today | Missing at 95 % |
|---|---|---|---|---|---|---|
| 01 | `COURTYARD` | Courtyard | `n_interior_rings >= 1` | 362 | 47 | 297 |
| 02 | `SLIVER` | Sliver | `min_rot_rect_w_m < 8.0` | 637 | 216 | 390 |
| 03 | `SQUARE` | Square | `rect >= 0.90`, aspect < 1.5 | 220 | 64 | 145 |
| 04 | `RECTANGLE` | Rectangle | `rect >= 0.90`, 1.5 ≤ aspect < 3.0 | 203 | 51 | 142 |
| 05 | `SLAB` | Slab | `rect >= 0.90`, aspect ≥ 3.0 | 28 | 10 | 17 |
| 06 | `TRIANGLE` | Triangle or trapezoid | ≤ 3 long edges, no reflex corner | 54 | 18 | 34 |
| 07 | `TRAPEZOID` | Parallelogram | no reflex corner, `rect < 0.90` | 87 | 20 | 63 |
| 08 | `L_SHAPE` | L shape | 1 reflex corner | 259 | 34 | 213 |
| 09 | `U_OR_T_SHAPE` | U or T shape | 2 reflex corners | 269 | 39 | 217 |
| 10 | `COMPLEX_MULTI_WING` | Complex multi-wing | everything else | 425 | 42 | 362 |
| | | | **2,544** | **541 (21 %)** | **1,876** |

Districts: `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 · `GB-LDN-STDUNSTANS` 82 ·
`IT-BOL-GALVANI2` 1,204. The 95 % bar is **2,417** buildings.

Display names 06 and 07 were corrected by the owner and are **display only** — the on-disk keys
`TRIANGLE` and `TRAPEZOID` never change. Measured: only 8 of the 54 "triangles" are carried by two long
edges, and all 87 "trapezoids" have four long edges with 65 having exactly four vertices.

---

## 2. The floor-plan law — `D-EU-64`, ruled by the owner 2026-09-01

> *"generally circulation or core area is in the center … keeping the centered one as core zone and adding
> the other core zones inside the flats, it is highly possible … if there are extra spaces adding to the
> thermal zones (flats)."*

1. **One circulation zone per plate, and one only.** It is the interior piece — the one that does not run
   along the outer wall.
2. **Every other pocket goes into the flat it adjoins**, chosen by largest shared area. A corner recess is
   usable room, not a second staircase.
3. **No unassigned space.** Flats + core = footprint. Coverage is checked and must read ≥ 99.9 %.
4. **The drawn flat count must match the claimed flat count.** Fragments are welded until a sheet that
   says three flats draws `F1…F3`.
5. `SLIVER` is the one exception: zero circulation zones is correct there — direct street entry, a private
   stair inside each dwelling.

**Where this stands:** the law is applied in the *document*, as a post-pass
(`scripts/eu21/02_one_core_per_plate.py`). **The engine still emits the extra pockets.** Closing that gap
— making `openubem/geometry/european_residential.py` produce one core directly — is the next real task and
has not been ordered yet. Say so plainly rather than implying the engine already does it.

Measured effect of the law on the ten drawn plates: cores 2 → 1 on groups 08, 09 and 10; circulation falls
from 23 % / 31 % / 36 % of the plate to **8 % / 7 % / 6 %**, in line with the ~9 % the regular grids give.

---

## 3. How to rebuild the document

Three scripts, run in order, from `scripts/eu21/`:

```
python scripts/eu21/01_cut_group_plans.py      # picks one real building per group, cuts it with the engine
python scripts/eu21/02_one_core_per_plate.py   # applies the D-EU-64 law; prints coverage per group
python scripts/eu21/03_build_rules_html.py     # writes the HTML into rules/
```

`01` and `02` share `scripts/eu21/group_plans.json`. `03` holds the per-group prose in its `SPEC` dict —
that dict is the right-hand column of every sheet, and it is where a rule change gets written. The page CSS
is read from the frozen 2026-08-28 document so the two can never drift apart.

Inputs already on disk: `openubem/outputs/eu_evidence/EU-20/morphology_census.csv` (2,544 rows, one per
building) and `representatives.json` (one chosen building per group).
Engine entry point: `generate_european_ruled_storey_layout` at
`openubem/geometry/european_residential.py:1078`. Four proposed schemes sit beside it at `:1465` (courtyard
perimeter band), `:1544` (row-house depth bands), `:1595` (wing spine decomposition), `:1723` (regularized
envelope grid). A fifth, `courtyard_gallery_ring` — a 1.80 m deck-access gallery round the void — is drawn
on sheet 01 but exists **only in `01_cut_group_plans.py`**, not in the engine, and is captioned as such.

---

## 4. Rules that are not negotiable

- **No EnergyPlus run of any kind without the owner's own sentence** (`D-EU-55`). A relayed "continue", an
  approved plan or a signed checkpoint is not permission. Writing geometry is fine; running it is not.
- **Never edit `rules/RULES_dwelling_layout_scheme_2026-08-28.html`.** It is frozen. Read its CSS, nothing
  more.
- **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The working tree
  is dirty and belongs to the owner.
- **Never write into `openubem/outputs/eu_evidence/EU-17/`.** Frozen. New evidence goes to `EU-21/`.
- **No `.py` files under `docs/`, ever.** Scripts live in `scripts/`.
- **Create nothing that was not asked for** — no extra docs, boards, reports or "helpful extras".
- `circulation_pct_of_plate` in the engine is a **fraction, not a percentage**. Any displayed share must be
  computed as `circulation_area_m2 / area_m2 * 100`.
- Executors are **fresh Sonnet sessions**, `model: "sonnet"` passed explicitly, one dispatch per task, the
  exact commands in the prompt. The director plans and audits; it does not write feature code.
- Every error solved must be registered in
  `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` before the task closes.

---

## 5. What is done, and what is next

**Done.** The ten groups exist and are counted. The document exists, has been reviewed group by group by
the owner, and now obeys the `D-EU-64` law on all ten sheets: one core each, 99.9 %+ coverage, both figures
the same building, honest names on 06 and 07.

**Open, in the order the owner cares about:**

1. **Write the one-core law into the engine** so the fleet gets what the document promises.
2. **Close the gap to 95 %** group by group, biggest first: `COMPLEX_MULTI_WING` (362 missing),
   `SLIVER` (390), `COURTYARD` (297), `U_OR_T_SHAPE` (217), `L_SHAPE` (213).
3. **Decide on `courtyard_gallery_ring` (S5)** — drawn, not in the engine, waiting on the owner.
4. **939 buildings are demoted at IDF-writing time**, not by morphology: `ZeroDivisionError` in
   `geomeppy/geom/vectors.py:105` and `IndexError` at `openubem/idf/surfaces.py:863-864`. A better floor
   plan does not fix these; they are a separate defect and must not be counted as a morphology failure.
5. **Publish the plans into `plans3D/`** under the existing `PLANS_<district>.html` filenames — geometry
   only, no energy results.

**Done means:** 2,417 of 2,544 residential buildings carry a floor plan with flats and exactly one
circulation zone, each cut by a rule that is written on its group's sheet, and the rules generalise to
countries not yet in the database.
