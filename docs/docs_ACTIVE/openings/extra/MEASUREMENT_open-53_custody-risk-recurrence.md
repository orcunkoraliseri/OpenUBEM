# OPEN-53 — the 874-of-875 finding, re-derived, and a live recurrence of the risk it left open

**Written 2026-08-20 (evening) by the director, at the user's request.** The item had been carried
untouched for several passes. This re-derives what it actually established, and reports one thing
found in the process that is **happening right now**.

---

## 1. What the 874-of-875 finding was, and what it turned out to be

The original count, from the E02 harvest census:

| | count |
|---|---:|
| `n_building_dirs` | 40,800 |
| `.eio` / `.err` present | 40,800 (both exact, zero empty) |
| `.sql` present | **39,926** — short by **874** |
| `.end` present | **39,925** — short by **875** |

**Three explanations were tested and two were retired:**

1. ~~OPEN-37's problem~~ — retired. Every short directory still carries its `.eio` and `.err`.
2. ~~An incomplete-simulation signature~~ — **retired by measurement (T02, 2026-08-18)**: the `.err`
   was read for **all 875** plus a 200-directory healthy control. **874 of 875 report `EnergyPlus
   Completed Successfully`, 0 fatal**, indistinguishable from the control. The one exception
   (`nyc_centre_fast_zone`) was truncated mid-input-processing and is not determinable from `.err`.
3. **A deletion by a process outside this repo** — confirmed at CP-1, 2026-08-18. The files were
   produced, harvested and inventoried on **2026-08-11**, then deleted at **2026-08-17 16:21** by a
   sweep that also emptied the whole E02 IDF corpus.

The concentration is total, not statistical: **874 of 875 fall in `austin_suburban_fast_zone` and
`austin_suburban_floor` — 100 % of both** — while every other mode for the same buildings is fully
populated.

✅ **The original question is answered. No published number was ever affected.** What kept the item
open is narrower and was stated precisely: **nothing prevents recurrence**, and
`e02_corpus_inventory.csv` (2026-08-11) is falsified by disk for two rows and must be read as a
snapshot, not as current state.

The exposure was then quantified (X06, 2026-08-18): **152.4 GB across three corpora, 145 GB of it
`.sql`**, none yet carrying the 2026-08-17 sweep signature. The conclusion recorded at the time was
that **under 0.12 GB preserves every finding this arc cites**, and that the 76 GB of `.sql` is "the
bait" and is **re-derivable**.

---

## 2. 🔴 That conclusion was right about cost and wrong about risk, and OPEN-61 is the proof

"Re-derivable" was priced at zero. **It was not zero.**

On 2026-08-20 the fleet `.sql` corpus was deleted under W9's prune. OPEN-61 then needed to size a
newly-found defect against those exact files — and could not re-read them. It had to **re-simulate
the entire fleet**, at a cost now measured rather than estimated: **97.2 CPU-hours**.

⚠️ **The retention policy was designed around the wrong question.** "Under 0.12 GB preserves every
finding this arc cites" is a true statement about **findings already made**. Every defect in this
register that was found by an executor auditing its own arithmetic — OPEN-58, OPEN-60, OPEN-61 — was
a question **nobody had asked yet** when the retention decision was taken. Raw `.sql` is not kept to
defend published numbers; it is kept so the *next* unasked question does not cost a re-simulation.

**Restated as a price:** deleting 76 GB of `.sql` bought back disk. The first new question that
needed it cost **97.2 CPU-hours**. That is the exchange rate, and it is now measured.

---

## 3. 🔴 The risk is recurring right now, while this document is being written

The OPEN-61 census — the 97.2 CPU-hour re-simulation that exists *because* the previous corpus was
deleted — is **regenerating that corpus into an ephemeral temp directory.**

Measured on disk at the time of writing:

| | value |
|---|---|
| `.sql` files retained so far | **5,138** |
| Size so far | **24 GB** |
| Projected at 8,153 buildings | **≈38 GB** |
| Location | `%LOCALAPPDATA%\Temp\claude\…\<session-id>\scratchpad\open61_census_fleet_work` |

That path is:

- **under `AppData\Local\Temp`** — ephemeral by design, and the same class of location as the one
  swept on 2026-08-17 16:21;
- **keyed to a session ID** that will not exist in a later session;
- **outside the repository**, so no `.gitignore` rule, retention note or inventory covers it;
- **not mentioned in any plan** as an artifact to preserve.

🔴 **If it is swept, the next question that needs these files costs another 97.2 CPU-hours.** This is
not a hypothetical — it is the identical sequence OPEN-53 already recorded once, at the identical
stage (files present, inventoried nowhere, in a directory nobody owns).

⚠️ **Note the related pattern, since it is the same failure at smaller scale:** the C12 control for
OPEN-62 was measured against 18 geomeppy-resaved IDFs that were also sitting only in an agent
scratchpad. They were preserved to `scratchpad/open03_proto_saved/` during today's CP-1 audit. That
one was caught by luck, in an audit that was looking at something else.

---

## 4. What is needed from the user

**One decision, and it is time-sensitive** — the census finishes in a few hours and the directory
becomes stale the moment the session ends:

1. **Preserve or discard the ≈38 GB `.sql` corpus.** If preserve, it needs a durable path outside
   `Temp` and a one-line entry in an inventory that is checked, not written once. ⚠️ **I have not
   moved or copied it** — a 24 GB copy during a CPU-saturated run is a real cost, and the disk budget
   is the user's call, not mine.
2. **Whether OPEN-53 should carry the general rule** rather than staying a record of one incident.
   The rule the two episodes suggest: *simulation outputs that cost more to regenerate than to store
   do not live in a directory nobody owns.* That is a policy, and policies are the user's.

**Recommendation:** preserve, and decide **before** the census completes rather than after. The cost
of being wrong in one direction is disk; in the other it is 97.2 CPU-hours, and that number is no
longer an estimate.

---

## 5. What this document does not claim

- **It does not claim any published number is affected.** OPEN-53 established the opposite at CP-1
  and nothing here revisits it.
- **It does not claim the 2026-08-17 sweep and the 2026-08-20 W9 prune are the same actor.** They are
  the same *consequence*; attribution was not investigated and is not needed for the point.
- **It does not size the current corpus's value.** Whether these 38 GB will ever be re-read is
  unknowable — which is precisely why the decision is about the price of the option, not about a
  forecast.

---

## Sources

- `INVESTIGATION_open-items-register-II.md` §2 OPEN-53 row (census, T02 `.err` read, CP-1 ruling,
  X06 exposure quantification) and the OPEN-61 row (W9 prune, re-simulation not re-read, 97.2 h).
- `scripts/analysis/open61_census_build_2026-08-20.py:97-101` — the scratchpad root; `:271` —
  `eplusout.sql` written under `work_dir/sim_out`; `:328-331` — `shutil.rmtree(WORK)` at the start of
  a re-run, which is a second, independent way this corpus disappears.
- Disk measurement taken directly, 2026-08-20 evening.
