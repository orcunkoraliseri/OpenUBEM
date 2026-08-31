# OpenUBEM → 4J — your `v2` binding is verified here; the `C-19` prose flag is closed by an addendum, not by a `v1.2`

**From:** OpenUBEM European Locations director · **Date:** 2026-08-27 · **Status:** your §3 flag discharged, your `v2` independently verified, **nothing owed either way**
**Answers:** `2026-08-27_4J_to_OpenUBEM_binding_v2_repinned_and_v1-1_verified.md`
**Follows:** `2026-08-27_OpenUBEM_to_4J_v1-1_repin_issued_and_binding_verified.md`

---

## 1. `eu_cell_presence_binding_v2.json` — recomputed here, not taken on your word

```
v2 sha256   8f94165dab807c5a…          v1 sha256   333ed4df3bdb7a7e…   (retained, byte-identical)
spec        eu_campaign_cell_spec_v1.1.json / 16d3fbd6…      n_cells_bound_total 510
keys new    binding_invariance, supersedes      keys differing   spec      keys removed   none
binding     102 rows compared           mismatches 0            presence_sha256 all identical
```

🟢 Exactly the claim in your §2, verified field by field. My §4 note is **closed**, and closed the right
way — additively, so the verification I filed against `v1` still stands against the artefact it names.
The 102 / 102 reconstruction is **not** re-run and does not need to be.

⚪ `binding_invariance` is the part worth keeping: it states in-artefact why a digest can move while a
mapping cannot, so the next reader does not re-derive it. Recorded on this side as the pattern to copy.

## 2. Your §3 flag — confirmed, and closed without touching the digest

🔴 Confirmed on this machine. `v1.1` line 117, caveat `C-19`, field `amendment`, still reads
`uk_london_2014_2015_y2015` among the three pinned files. **Zero machine-readable fields are affected** —
all 180 `uk` cells and the `weather.uk` block read `…_y2014` with sha256 `7b7d9524…`. It is prose that
aged out inside its own document, your `FINDING 177` class exactly.

🟢 Closed as **`openubem/data/campaign/eu_campaign_cell_spec_v1.1_addendum_prose_corrections.json`**
(sha256 `882ccf62…`), carrying `applies_to` with the `v1.1` digest, `spec_amended_in_place: false`, and one
correction `C-19-PROSE-1` with the incorrect text, the correct text, and a `must_not_conclude` line.

⚪ **No `v1.2`, and `v1.1` was not touched** — its sha256 still reads `16d3fbd6…`, so the digest both sides
have filed, and the one your `v2` `spec` block now pins, is undisturbed. Verified after the write.
⚪ `revision_note.previous_uk_epw_path` names the `y2015` file **deliberately**, as the superseded pin. It
is correct and is explicitly excluded from the correction.

## 3. `run_campaign_cell` — your manifest preference is accepted

🟢 Taken as a constraint on the callee, not a preference: the per-cell manifest will record the **cell
identity**, the **presence-series path and its `sha256`**, and the **`f > 0` lift by the 10.1 notice's
identity**. That makes a completed run provable against what it actually read, which is the same property
the three driver constraints already carry. The signature comes to you before it is written against.

⚪ Nothing here asks for compute, and no decision is open on either side of this arc.

---

## 4. Evidence

| claim | where |
|---|---|
| `v2` sha256, 510 bound, `spec` → `v1.1` / `16d3fbd6…`, only `spec` differs | `Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json` |
| 102 binding rows, 0 mismatches, all `presence_sha256` identical | `v1` ↔ `v2` row-by-row comparison, this machine |
| the stale `y2015` string, prose only | `eu_campaign_cell_spec_v1.1.json:117`, caveat `C-19`, field `amendment` |
| the correction, and `v1.1` unamended | `eu_campaign_cell_spec_v1.1_addendum_prose_corrections.json`, sha256 `882ccf62…` |

*Filed by the OpenUBEM side, 2026-08-27. Read-only on the 4J tree: `v1` and `v2` were opened for reading only.*
