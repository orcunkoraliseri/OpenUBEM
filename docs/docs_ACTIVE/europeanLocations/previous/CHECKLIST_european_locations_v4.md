# European locations × Step 8 — progress checklist (v4)

Tracking view only — no rulings, no findings, no numbers live here. Source of truth stays
[`STATE_european_locations_v4.md`](STATE_european_locations_v4.md) (findings/rulings) and
[`implementation/PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md`](implementation/PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md)
(task detail). Updated by the director after each dispatch audit — not by an executor.

---

## Work packages

| WP | What | Status |
|---|---|---|
| `EU-01`…`EU-12` | TABULA loader → results/dossier → district campaign → viewer | ✅ Completed |
| `EU-13`/`EU-14`/`EU-13B`/`EU-14B` | Layout coverage, Bologna construction year, ruled grid, layout binding | ✅ Completed |
| `EU-15` | Ruled thermal zoning to ≥95 % bar | ✅ Completed — bar not met (`FINDING 211`) |
| `EU-16` | Context geometry + 4-district resimulation | 🟥 Stopped (`D-EU-53`) |
| `EU-18a` | `plans3D/` pages from today's IDFs (T01–T03) | ✅ Completed |
| `EU-17` | Relax the box rule (T04–T11) | ✅ Completed — regression found on rebuild, see `EU-17a` |
| `EU-17a` | Root-cause the T10 population-loss/rules-regression crash (T14) | ✅ Completed — not a bug, root cause traced (`FINDING 220`) |
| `EU-17b` | Apply `D-EU-58` fallback tier (T15) | ✅ Completed — 633/633 recovered, 0 residual, `FINDING 220` closed |
| `EU-18b` | Regenerate pages + gate (T12), sample battery (T13) | 🟡 T12 dispatched |
| `EU-19` | Four-district resimulation on proven plans | ⬜ Blocked — needs owner read of `plans3D/` **and** `D-EU-55` |

---

## Task checklist

**`EU-18a`**
- [x] T01 — IDF floor-plan reader
- [x] T02 — `plans3D/` pages from today's IDFs
- [x] T03 — parity gate (report-only)

**`EU-17`**
- [x] T04 — deep refusal census
- [x] T05 — wing decomposition, no whole-building refusal
- [x] T06 — courtyard unfolding hardened
- [x] T07 — narrow plates (<8 m) corridor-free rule
- [x] T08 — `D-EU-49` single-storey ⇒ no circulation
- [x] T09 — kill IDF/side-car divergence at source (partial)
- [x] T10 — rebuild all four districts, census on IDFs — 🔴 STOP: coverage collapsed, 633/2,544 buildings lost, 0/8 rules regression (`FINDING 220`)
- [x] T11 — settle EUI denominator (`FINDING 214`)

**`EU-17a`** (owner ruling `D-EU-57`, 2026-09-01: diagnose first)
- [x] T14 — diagnose population loss + rules regression — ✅ STOP: not a bug, architectural gap outside `EU-17` scope (`scripts/run_eu_s2_campaign.py:516-534`), decision `D-EU-58` escalated

**`EU-17b`** (owner ruling `D-EU-58`, 2026-09-01: option (a))
- [x] T15 — fallback tier in `run_eu_s2_campaign.py`, rebuild `EU-17` tree, close `FINDING 220`

**`EU-18b`**
- [ ] T12 — regenerate pages + parity gate on corrected `EU-17` tree — dispatched 2026-09-01
- [ ] T13 — non-box sample battery — 🔴 hard-blocked on owner's own words (`D-EU-55`)

**`EU-19`**
- [ ] Owner reads `plans3D/` pages and confirms (`D-EU-54`)
- [ ] Owner gives explicit simulation permission (`D-EU-55`)
- [ ] Speed queue confirmed empty (`D-EU-53` item 4)
- [ ] Resimulation dispatched

---

## Gates that need you, specifically

- 🔴 `plans3D/` read + confirmation (`D-EU-54`) — after T12.
- 🔴 Simulation permission, your own sentence, per wave (`D-EU-55`) — before T13 and before `EU-19`.

Everything else on this list runs without a check-in per your standing "continue to the end" instruction.
