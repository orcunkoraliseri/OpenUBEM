# Why the full fleet cannot reach 100 %

**2026-09-04.** One page. Full evidence: `debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_claude-opus-5.md`.

**Fleet: 4,186 buildings. Prepared today: 3,096 (74.0 %). Ceiling: ~3,430 (≈82 %).**

---

## The rule that decides everything

Every building needs a **construction period** and a **storey count** from a real, cited source.
No source → the building is excluded and told you why. Nothing is guessed, interpolated or filled in.
That is the design, not a bug — a fabricated build year silently becomes a fabricated heating demand.

---

## What is left, and why it stays left

| # | Population | Count | Why it cannot be recovered |
|---|---|---|---|
| 1 | London, **no EPC exists** | **418** | A UK certificate is only issued on sale, let, or new build since 2008. Long-held stock has none. 395 have a UPRN but no certificate ever lodged; 23 have no UPRN at all. Nothing to read. |
| 2 | London, **certificates contradict each other** | **269** | The footprint's own certificates place it on both sides of a TABULA period boundary (70 buildings) or leave it ambiguous (199). More data does not resolve a disagreement inside the data. |
| 3 | London **apartment blocks**, no storey count | **14** | The certificate describes one flat, never the block. Needs a height raster we do not have. |
| 4 | **Courtyard IDF failures** | **13** | Real unresolved interior-ring interzone pairs. Reproduced; the `FINDING 249` carve-out already ran and does not reach them. |
| 5 | Lyon + Madrid, **missing build year** | **19** | Source field traced and genuinely null (`date_d_apparition`, Catastro `dateOfConstruction`). |
| 6 | Bologna, **census section publishes no epoch** | **4** | ISTAT `E8…E16` partitions *occupied* residential buildings; these sections have `E3 = 0`. The number does not exist upstream. |
| 7 | Lyon typology outliers | **10** | Out of scope by `D-EU-37` §4. |
| 8 | Misc. dwelling counts | **2** | Source field null. |

**≈ 750 buildings. Dominated by London: 687 of them (items 1–3).**

---

## What *is* recoverable, and is being taken

- **+30 — ✅ done 2026-09-04 (`FINDING 256`)** — an observed `construction_year` was already sitting in the
  EPC cache and had never been read. 24 buildings had a year but no age band; 6 had a year that resolves a
  straddle. London 389→419, fleet 3,066→3,096. All 389 baseline buildings re-emit byte-identical.
  Plan: `implementation/PLAN_eu-epc-construction-year-2026-09-04.md`.
- **+163 max (Madrid)** — Catastro publishes storeys on `BuildingPart`, not `Building`; one authorised fetch.
- **+168 (needs your ruling)** — straddle tie-break by full constraint intersection (+69), the 13–14 dwelling
  gap (+38), `house`/`terrace` storeys from floor dimensions (+33), `D-EU-58` tolerance widening (+4),
  ISTAT tie policy (+12), `building=residential` under the Bologna ladder (+6).

Everything above, taken at its most optimistic, lands at **≈ 3,430 / 4,186 ≈ 82 %**.

---

## The one-sentence answer

**100 % would require inventing a build year for 418 London buildings that have never had one recorded
anywhere — which is the one thing this pipeline is built never to do.**
