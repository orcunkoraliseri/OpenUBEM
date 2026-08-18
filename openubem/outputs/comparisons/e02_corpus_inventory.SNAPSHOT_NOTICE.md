# NOTICE — `e02_corpus_inventory.csv` is a snapshot, not current state

**Date of this notice:** 2026-08-18. **CSV mtime:** 2026-08-11 20:58.

`e02_corpus_inventory.csv` records a census taken 2026-08-11. It is **not** re-generated on
read and does not update itself. As of 2026-08-17 16:21, an external process (outside this
repository) deleted the entire E02 IDF corpus under
`%LOCALAPPDATA%\Temp\ubem_e02_fleet\<cell>\step3_<mode>\idfs\`, and separately, 875 of the
40,800 harvest directories under `%LOCALAPPDATA%\Temp\ubem_e02_harvest` never received their
`.sql`/`.end` outputs (see `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md`).

**Two rows in this CSV are already known-falsified by disk, re-verified 2026-08-18:**

| cell | mode | CSV `n_end` | live disk `n_end` |
|---|---|---|---|
| `austin_suburban` | `fast_zone` | 437 | **0** |
| `austin_suburban` | `floor` | 437 | **0** |

No code in this repository reads this CSV back in (`grep -rn e02_corpus_inventory scripts/ openubem/ tests/` finds only the one script that *writes* it, `scripts/analysis/e02_corpus_inventory.py`) — this notice is for human planners only, so the CSV itself is left untouched.

**Planning rule (register OPEN-53, amendment 2026-08-18):** any plan that depends on a
`%LOCALAPPDATA%` E02 artifact (harvest `.sql`/`.end`/`.eio`/`.err`, or fleet `.idf` files)
must re-verify presence on disk at planning time and must not cite this CSV, or any other
dated census, as current state. The one known exception found so far is
`scratchpad/e-la-20-investigation/i03/work_part1/` (4 surviving IDFs for 2 of 3 `E-LA-40`
buildings, mtime 2026-07-25) — and that exception is itself fragile: `scratchpad/` is not a
durable store and carries no guarantee against a future sweep.

Full write-up: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md`, §7.
