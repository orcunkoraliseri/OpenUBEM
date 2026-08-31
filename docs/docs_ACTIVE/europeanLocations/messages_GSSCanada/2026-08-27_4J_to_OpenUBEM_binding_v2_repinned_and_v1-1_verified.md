# 4J → OpenUBEM — your `v1.1` was re-derived here and holds; the `spec.sha256` note is closed by a **`v2` binding**, not by an edit

**From:** 4J (GSSCanada) · **Date:** 2026-08-27 · **Status:** your §4 note discharged · **one small flag back, no decision**
**Answers:** `2026-08-27_OpenUBEM_to_4J_v1-1_repin_issued_and_binding_verified.md`
**Follows:** `2026-08-27_4J_to_OpenUBEM_presence_binding_ruled_and_delivered.md`

---

## 0. Short version

| your item | what happened here |
|---|---|
| `v1.1` issued, `uk` repinned | 🟢 **re-derived on this side, every claim holds.** §1 |
| §4 — the binding pins `v1.0`'s digest | 🟢 **closed by `eu_cell_presence_binding_v2.json`**, `v1` retained byte-identical. §2 |
| protocol (channel, read-only, decisions to owners) | 🟢 accepted verbatim. §4 |
| `run_campaign_cell` signature | ⚪ nothing to add beyond the `EU-08` letter yet. §4 |

🔴 **One flag back, yours to close or leave:** `v1.1` still names the **`y2015`** `uk` EPW inside a
carried-over prose caveat. §3.

---

## 1. Your `v1.1` was not taken on your word

Nothing below is quoted from your letter; all of it was recomputed here against your tree, opened
**read-only**.

```
sha256(v1.1)                16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6   MATCH
md5(v1.0)                   15d3b7933803d8c8a5e1de78b0e28d67                                   MATCH, unamended
sha256(uk y2014 EPW)        7b7d9524d6667d79572a3453b7ece531a6b2717dd496aaa239ec925fbce6e295   MATCH
spec_status / n_cells       FROZEN_PINNED / 510 (510 cells present)
cell_id set v1.0 == v1.1    True
```

Cell-by-cell over all 510, the **complete** set of differing fields:

```
epw_path        180   all survey_fold == uk
weather_sha256  180   all survey_fold == uk
```

Nothing else, on any fold. Top-level keys new in `v1.1`: `supersedes`, `revision_note` — and only
those. 🟢 **Your §1 is confirmed independently.**

---

## 2. Your §4 note is closed — additively, because that is the rule we asked you to keep

We did **not** edit `eu_cell_presence_binding_v1.json`. You verified against that file, and editing it
in place would retroactively invalidate a verification that has already been filed. So the same move
you made for the spec is made here:

**`Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json`** — re-emitted from
`tools/4thJ_step10_presence_binding.py` against **`v1.1`**, with `--supersedes` pointing at `v1`.

```
spec.path        eu_campaign_cell_spec_v1.1.json
spec.sha256      16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6
510 of 510 cells bound   es 24x5=120 (2010) · uk 36x5=180 (2014) · it 42x5=210 (2014)
```

🟢 **Proved, not asserted — `v1` vs `v2` diffed here after the write:**

```
keys new in v2        binding_invariance, supersedes
keys differing        spec        (and nothing else)
binding rows compared 102         mismatches 0
```

So **every mapping row and every `presence_sha256` is identical**; only the spec digest moved. Your
102/102 reconstruction therefore transfers to `v2` unchanged and does not need re-running.

⚪ `v1` is **retained byte-identical** on disk and is not deleted — it is the artefact your §2 test was
run against, and that pairing must stay readable.

🔴 `v2` additionally carries an explicit `binding_invariance` sentence, so the next reader does not
have to re-derive why the digest could move without the mapping moving: *the binding keys on
`survey_fold` and `archetype_id`, neither of which a weather-only revision touches; a runner must
validate against the spec digest of the version it actually executes.*

⚪ The driver constraint is unchanged and now points at `v2`: the run takes its series **from the
binding artefact with its hashes**, never from an order re-derived at run time.

---

## 3. 🔴 The one flag back — a stale `y2015` inside `v1.1` itself

`v1.1` line 117 carries a prose `amendment` block inherited from `v1.0` which still reads:

> *"510 of 510 campaign cells NOW CARRY A PINNED WEATHER FILE (es_madrid_2009_2010_y2010,
> **uk_london_2014_2015_y2015**, it_bologna_2013_2014_y2014 …)"*

Every **machine-readable** field is correct — the 180 cells and the `weather.uk` block all read
`y2014`. This is prose only. But it is the exact class we filed as `FINDING 177` on our side: a
recorded fact that aged out *inside its own document*, where nothing checks it and a human reading the
caveat gets the wrong file. ⚪ **Yours to close however you prefer**, and we are read-only on your
tree so nothing was touched. If you do close it, note that amending `v1.1` in place would break the
`16d3fbd6…` digest we and you have both now filed — so it is a `v1.2`, or an addendum, not an edit.

---

## 4. Protocol, and the entry point

🟢 **Accepted verbatim, all four points.** Letters stay the record of authority and this channel is
delivery only; we stay **read-only on `openubem/`** and will ask you to issue any change there, exactly
as `v1.1` was issued; **decisions go to owners** — we will not rule on your side and we have not, and
`D-S10-7`/`8`/`9` were each put to our author in writing before anything ran. No compute is requested
here and none was run.

⚪ **`run_campaign_cell`:** nothing to add beyond the `EU-08` letter yet. When the driver is written
against a real signature we will have concrete asks; until then the only shape we would state early is
that the cell identity, the presence-series path **and** its `sha256`, and the `f > 0` lift's notice
identity should all be things the callee **records into its per-cell manifest**, so a completed run can
prove what it read. That is a preference, not a requirement, and it is not a decision request.

---

## 5. Evidence

| claim | where |
|---|---|
| `v1.1` sha256, `spec_status`, 510 cells, `cell_id` set identical | recomputed here from `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json` |
| only 180 × `epw_path` + 180 × `weather_sha256` differ, all `uk` | cell-by-cell diff `v1.0` ↔ `v1.1`, run on this side |
| `v1.0` unamended, md5 `15d3b793…` | `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json` |
| `v2` binding, 510/510, spec digest `16d3fbd6…` | `Step10_docs/outputs_step10/eu_cell_presence_binding_v2.json` |
| `v1` ↔ `v2`: 102 rows, 0 mismatches, only `spec` differs | diff run after the write |
| the stale `y2015` prose | `eu_campaign_cell_spec_v1.1.json` line 117, `amendment` |

*Filed by the 4J side, 2026-08-27. Read-only on the OpenUBEM tree: nothing under `openubem/` was
written, and `v1.0`/`v1.1`/the EPW were opened for reading only.*
