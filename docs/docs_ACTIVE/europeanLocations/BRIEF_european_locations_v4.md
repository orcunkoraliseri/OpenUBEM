# European locations — the brief (v4)

**2026-08-31.** One page: what we are trying to do, what is wrong, how it gets fixed, in what order.
Detail lives in `STATE_european_locations_v4.md`; this is the plain version.

🔴 **v3 is cancelled. v4 is the only track.** The owner stopped the Speed runs and the v3 tasks on
2026-08-31 (`D-EU-53`): the `D-EU-47` Bologna rebuild wave and the `D-EU-48` Lyon timeout resubmit are
dead, and `BRIEF_european_locations_v3.md` / `STATE_european_locations_v3.md` are superseded by this
document and its `STATE_european_locations_v4.md`. Nothing in v3 is executed any further.

---

## 1. The goal

Unchanged. Four real European residential neighbourhoods — **Madrid Berruguete, Lyon Hauts de
Croix-Rousse, London St Dunstan's, Bologna Galvani 2** — every residential building modelled the way the
published method models one: real footprint, real storey count, **each floor divided into residential
thermal zones plus an unconditioned circulation core**, each building simulated on its own but
**surrounded by its real neighbours** so shading is right.

Method of record: MVP §4.2–§4.4, `IMP_step8/outputs/floor_layout_generation_report.md` §5–§9, and
*Energy & Buildings* 337 (2025) 115620 Fig. 4.

---

## 2. What is done

`EU-01`–`EU-16` are built and have run. The context work landed: **every one of the 2,544 IDFs now
carries shading geometry** (0 before), and 89.4 / 86.5 / 70.7 / 80.7 % of them carry adiabatic party
walls. Dwelling counts are conserved. Areas balance exactly — conditioned + circulation = gross to
1.2 × 10⁻⁶.

The floor plans are the part that did **not** land.

---

## 3. What is wrong — three things

### Problem 1 — the box rule refuses four buildings in ten

The ruled route only accepts a plate it can fit inside a rectangle. A footprint whose area moves more
than **2 %** when it is squared off is refused (`european_residential.py:32`, `:918`, `:986`); an
L-shape is split at its re-entrant corner and refused if the split fails (`:983`); a courtyard is
unfolded and refused if the unfold fails; a plate narrower than **8 m** is refused (`:1008`). A refused
building is not drawn as an L or a U — it becomes **one undivided box per floor**, no dwellings, no
corridor, no stair core. That is exactly what you saw in the viewer.

Measured today over all 2,544 side-cars:

| District | refused by the ruled route | worst cause |
|---|---:|---|
| `ES-MAD-BERRUGUETE` | **35.9 %** (345 of 961) | L-shape 22.9 % |
| `FR-LYO-HAUTCOEURPENTES` | **33.3 %** (99 of 297) | L-shape 25.3 % |
| `GB-LDN-STDUNSTANS` | **51.2 %** (42 of 82) | L-shape 25.6 %, >8 dwellings 22.0 % |
| `IT-BOL-GALVANI2` | **50.7 %** (610 of 1,204) | L-shape 26.0 %, courtyard 13.2 % |
| **fleet** | **43.1 %** (1,096 of 2,544) | L-shape 24.7 % |

Ruled coverage is therefore **56.9 %** (Madrid 64.1, Lyon 66.7, London 48.8, Bologna 49.3). The bar
`D-EU-39` set is **≥ 95 % in every district**. `EU-15` was recorded Completed and did not move this
number: it was 57.81 % before `EU-15` and it is 56.92 % now.

### Problem 2 — what actually ran is worse than what the viewer shows

The viewer draws the side-car. The side-car is regenerated from the geometry code; the IDF is built by a
separate path that can quietly give up and rebuild the building as a plain stacked block. Measured on
the IDFs themselves:

| District | IDFs that are one undivided box per floor | IDFs carrying a stair core |
|---|---:|---:|
| `ES-MAD-BERRUGUETE` | **54.1 %** (520 of 961) | 19.6 % (188) |
| `FR-LYO-HAUTCOEURPENTES` | **50.8 %** (151 of 297) | 19.2 % (57) |
| `GB-LDN-STDUNSTANS` | **73.2 %** (60 of 82) | 15.9 % (13) |
| `IT-BOL-GALVANI2` | **68.4 %** (824 of 1,204) | 26.9 % (324) |
| **fleet** | **61.1 %** (1,555 of 2,544) | **22.9 %** (582) |

**459 buildings** are drawn in the viewer with a ruled grid and a carved core that **do not exist in the
IDF that ran**, and only 2 of them say so in the manifest. So the honest answer to "what fraction fails
the box rule" is two numbers: **43.1 %** refused at layout time, **61.1 %** actually simulated as a box.

### Problem 3 — the EUI denominator never moved

`D-EU-39` ruled that circulation is carved out and every EUI denominator moves with it. Both areas are
published, but the denominator is still the **gross** area on **2,544 of 2,544** rows
(`run_eu_s2_district_campaign.py:416`). On the 582 buildings that do carry a core the denominator is
4–5 % too large on average (down to 48 % too large on one Bologna building).

---

## 4. The new rules (owner, 2026-08-31)

- **`D-EU-49` — one storey, no circulation.** A single-storey building needs no stair core. 46 buildings
  are single-storey today and 3 of them carry a core; those 3 lose it.
- **`D-EU-50` — the box rule is relaxed.** The ruled scheme must express L, U, T, courtyard and narrow
  plates, not only rectangles. The ≥ 95 %-per-district bar stands and is **proven on disk before any
  simulation**, not after.
- **`D-EU-51` — nothing goes to Speed until the plans are seen.** Every campaign is preceded by (a) an
  HTML floor-plan atlas, one page per district, every building, **drawn from the IDF that will run**, and
  (b) a sample EnergyPlus battery on the non-box buildings only. This is the standing working method from
  now on, not a one-off.
- **`D-EU-52` — the arc keeps its own error index**, `debugs/DEBUG_REFERENCES_european_locations.md`,
  house format, searched before any debugging and appended after any fix.

---

## 5. How it is planned

Three packages, in order, executed by fresh Sonnet sessions, never by this session.

| | Package | What it does | Ends at |
|---|---|---|---|
| 1 | **`EU-17`** — relax the box | Carry the ruled grid onto non-rectangular plates: wing decomposition that cannot refuse, courtyard unfolding, narrow-plate rule, single-storey exemption | ≥ 95 % ruled in **every** district, measured on the IDFs |
| 2 | **`EU-18`** — prove it without simulating | Floor-plan atlas per district built from the IDFs; side-car ↔ IDF parity gate that fails closed; sample EnergyPlus battery on ~5 non-box classes × 4 districts, locally | Atlas reviewed by the owner + battery green |
| 3 | **`EU-19`** — resimulate | Four districts on Speed, `--time=7-00:00:00`, harvest, viewers | Four fresh district EUIs |

No `sbatch` before package 2 has been read and accepted. Walltime is 7 days minimum — the cancelled v3
wave recorded a Lyon 3 h resubmit timing out twice.

Carried into `EU-19`, not lost: Bologna's 177 failed tasks and Lyon's 9 timed-out ones stay recorded as
failures with a named class. They were never recovered, they are never pooled around, and their recovery
now happens inside the resimulation on the new plans.

---

## 6. What is deliberately not in scope

`D-EU-37` (extending the typology table, which would recover Lyon's 226 and London's 345 excluded
buildings) stays an unruled owner decision. The `DR16` Bologna and `DR15` London verdicts are reported,
never tuned into a band. No district EUI may be quoted until `EU-19` lands.
