# DECISION REQUEST D-EU-14 — what CP-C signs when no campaign fold can pin

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.14
- **Findings:** EU-S2-03, EU-S2-04 (closed), **EU-S2-05** (new)
- **Blocks:** the §9.4 signature — nothing else
- **Related:** `DECISION_REQUEST_EU-13_G8.13_scorer_index_2026-08-26.md` (ruled (a), closed)

---

## 1. The one-sentence version

The specification is finished except for **one field per cell**, that field is the weather file, and
**no campaign fold can supply it** — not because the download is unfinished, but because choosing which
of two calendar years each fold uses is a decision this project does not own.

| | |
|---|---|
| Cells specified | **510** (es 120 / uk 180 / it 210) |
| Cells with pinned weather | **0** |
| Cells ever simulated | **0** |
| What is missing | `epw_path` — one field |
| Who owns the missing input | **GSSCanada** (the diary year) |

## 2. The contradiction

Two rules written at different times disagree about what the freeze does.

**Caveat C-16** says the freeze *proceeds*:

> Any fold left `RULED_NOT_PINNED` at freeze time is carried as an open weather dependency, with
> `epw_path` unresolved rather than substituted.

**The freeze script** says the opposite. `scripts/freeze_eu_campaign_cell_spec.py:190-197` refuses with
`NOT_PINNED <fold> <status>` unless **every** fold is pinned. `--allow-unpinned` exists, but it writes
`eu_campaign_cell_spec_v1.0_DRAFT.json` with `spec_status = DRAFT_WEATHER_NOT_PINNED` — never a signed
contract.

Neither is a bug. C-16 protects the deliverable: a specification is still a specification for the folds
that *are* runnable. The refusal protects the signature: an artefact stamped `FROZEN` that nothing can
execute will eventually be quoted as if it could.

## 3. Why the download does not resolve it

This is the part that is easy to get wrong, because for three days the ERA5 acquisition looked like the
last blocker. It is not.

`diary_window` is `None` and `diary_window_status` is `RULED_NOT_PINNED` for `es`, `uk` and `it`. Each
ERA5 window spans **two** calendar years and an EPW is **one** year:

```
es_madrid    2009-01-01/2010-12-31   ->  2009 or 2010?
uk_london    2014-01-01/2015-12-31   ->  2014 or 2015?
it_bologna   2013-01-01/2014-12-31   ->  2013 or 2014?
```

Year selection is a **diary** question, and the diary is GSSCanada-owned (MVP §9, lines 591-599). The
converter refuses to default it — it prints `YEAR_NOT_RULED` rather than silently taking the first year,
which is FINDING **EU-S2-03**.

So with all 75 archives on disk, all seven gate-5 benchmarks in place and all six DR08 gates green on
every candidate EPW, the expected end state is still **zero folds pinned**.

## 4. FINDING EU-S2-05 — the evidence fold is not in the campaign

Found while preparing this decision, and it changes what a partial freeze is worth.

```
CAMPAIGN_FOLDS = ("es", "uk", "it")        openubem/validation/european_campaign.py:14
```

France is **not** a campaign fold. Everything this arc actually simulated — the 31 buildings, the
618 782.3181 kWh, the 19 823.6173 m², the **31.2144 kWh/m²**, the S2 gate report, and the one weather
file that ever passed six gates — is fold **`fr`**, FR-LYO-HAUTCOEURPENTES 2023.

**The evidence bundle and the campaign specification share no fold, no building and no weather file.**

Neither artefact is wrong; they answer different questions. The S2 bundle demonstrates that the pipeline
runs end to end and produces a defensible number. The specification fixes the boundary Step 8 consumes.
But the natural reading — *"the campaign was validated on 31 real buildings"* — is false, and nothing in
the spec said so until this pass. Recorded as caveat **C-19**; the register is now 19 entries.

The consequence for this decision is direct: **a partial freeze would have zero executable cells.** The
pinned France weather cannot lend its `RULED_PINNED_EXCEPTION` status to any campaign cell.

## 5. What *is* finished

Everything except that one field, and it is worth being precise about how much that is:

| Item | State |
|---|---|
| 510 cells, 510 unique `cell_id`, 102 archetypes | Built, `validate_campaign_cells` accepts |
| Five-level `f` ladder, control-cell pairing | Built |
| Every path repo-relative, no absolute path anywhere | Built, test-enforced |
| Caveat register embedded, 19 entries | Built, add-never-remove enforced |
| Six DR08 gates | **Code**, not placeholders |
| Gate 6 against real EnergyPlus 23.1 | PASS, rc 0, 0 severe, 1.19 s |
| Gate 5 against the real France EPW + benchmark | `PASS_WITH_DOCUMENTED_EXCEPTION`, Nov 13.82 %, annual 3.23 % — reproduces the owner's ruling to two decimals |
| Seven fold-year gate-5 benchmarks | Acquired, FINDING EU-S2-04 closed |
| Freeze machinery | Built, refuses correctly |
| `epw_path` on 510 cells | **`PENDING_EU07_WEATHER`** |

## 6. Options

### (a) Freeze a partial contract now

`spec_status = FROZEN_PARTIAL_WEATHER`, `epw_path: null` on all 510 cells, the three carried folds named
in the header, C-16 / C-17 / C-18 / C-19 embedded. §9.4 is signed today.

- **Executable cells: 0 of 510.**
- v1.0 is immutable, so the diary ruling arrives *against a frozen artefact* and forces a v1.1 differing
  from v1.0 in the one field everyone was waiting for.
- Needs machinery that does not exist yet: a distinct `--carry-unpinned` mode — never a loosening of
  `--allow-unpinned` — the `FROZEN_PARTIAL_WEATHER` status value, a `carried_folds` header block, and a
  test asserting no carried-fold cell ever acquires a non-null `epw_path`.

### (b) Stay at DRAFT until the diary rules — **RECOMMENDED**

Hand GSSCanada `_DRAFT.json`, complete in every other respect, together with the year question and the
gate verdicts for both candidate years. The year ruling then produces a **single** frozen v1.0 that is
executable on the day it is signed.

- No signed §9.4 artefact until the ruling arrives.
- Reversible; nothing is stamped immutable prematurely.

### Preparation that needs no ruling — do this either way

Run the six DR08 gates on **both** candidate years of all three folds and store the twelve verdicts. It
substitutes nothing and chooses nothing. But the moment a year is ruled the fold pins with **no further
computation**, and if a candidate year fails a gate, the diary ruling can be made knowing that *before*
it is made rather than after. This is the only remaining work the arc can do on its own authority, and
it is already implemented — `scripts/run_eu_t06_weather_promotion.py --all --all-years`.

## 7. Recommendation — (b), with the preparation executed immediately

This **reverses** the first recommendation written in MVP §12.14 earlier today, which said (a). That
version was written before FINDING EU-S2-05 and assumed the France fold sat inside the campaign, so that
a partial freeze would leave something runnable. It would not.

A `FROZEN` contract with zero executable cells buys a signature and nothing else, and it buys it at the
cost of immutability: the very next event in this arc — the diary ruling — would invalidate it. The
honest artefact today is a DRAFT that is complete in nineteen of twenty respects and says so, plus
twelve gate verdicts that make the ruling cheap to act on.

**Choose (a) only if the hand-off must close before the diary ruling can be obtained.**

## 8. Where to check this

| Path | What it shows |
|---|---|
| `openubem/validation/european_campaign.py:14` | `CAMPAIGN_FOLDS = ("es", "uk", "it")` — France excluded |
| `scripts/freeze_eu_campaign_cell_spec.py:190-197` | The refusal that contradicts C-16 |
| `openubem/data/campaign/eu_campaign_cell_spec_v1.0_DRAFT.json` | 510 cells, all `RULED_NOT_PINNED`, all `PENDING_EU07_WEATHER` |
| `openubem/data/campaign/eu_boundary_caveats_v1.0.json` | C-16, C-17, C-18, C-19 |
| `openubem/data/weather/weather_registry.json` | `diary_window: null` for es / uk / it |
| `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.12e, §12.14 | The finding and this decision, in the authoritative record |

---

**Answer:** **(a) Freeze partial now** ☐   **(b) Stay at DRAFT until the diary rules** ☒

**RULING:** Option (b) approved. Retain `eu_campaign_cell_spec_v1.0_DRAFT.json` with `DRAFT_WEATHER_NOT_PINNED` status pending GSSCanada diary year selection for ES/UK/IT. Execute dual-year DR08 gate evaluations across both candidate years (2009/2010 for ES, 2014/2015 for UK, 2013/2014 for IT) so that a single, executable `v1.0` contract can be signed immediately once diary years are ruled.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26

