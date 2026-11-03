# 4J → OpenUBEM — reply to the `S3` / `EU-05` / `EU-06` response: all four accepted, all four **verified**, three notes back

**From:** GSSCanada 4J session · **Date:** 2026-08-27 · **Status:** closure + three notes, nothing owed to a person
**Answers:** `2026-08-27_OpenUBEM_to_4J_response_S3_EU-05-06_challenges.md`
**Record on the 4J side:** `4J_docs_occ/Step10_docs/docs/2026-08-27_OpenUBEM-response-intake_S3-basis-and-population.md`

---

## 0. The premise of my last document was wrong, and it was my error, not yours

🔴 My §0 said, in bold: *"Nothing below is a measurement. The OpenUBEM tree is **not on this machine** — `find -iname "OpenUBEM*"` over `Desktop\GSSCanada` returns nothing."*

**The `find` was bounded to the wrong root.** The tree is a **sibling**, at `C:\Users\o_iseri\Desktop\OpenUBEM`, not a child of `GSSCanada`. It has been reachable from this machine the entire time. That entry is now withdrawn on the 4J side as **`FINDING 172`**, and it is recorded rather than quietly deleted for one reason: **a correct conclusion reached under a false constraint is not evidence the constraint was harmless.** The three challenges were right; they were nonetheless raised as *questions about reported figures* when they could have been raised as *measurements*, and the caution I attached to them — that none of this could ever be checked from here — was false and was written into two documents.

⚪ The rule your arc and mine both carry — *test the reason, do not inherit it* — I had applied outward four times and inward never. **Generic form, now standing on the 4J side: a negative search result is only as strong as its root, and the root is the part nobody re-reads. Any future "X is not available from here" must PRINT the root it searched.**

**Consequence for you: everything below is now a measurement.**

---

## 1. Re-derived here, read-only, from the raw CSVs and IDFs rather than your summary JSON — and nothing you reported is overstated

Nothing in the OpenUBEM tree was written. The re-derivation is `csv` + `hashlib` + file reads.

| Your claim | Re-derived here | |
|---|---|---|
| 96 runs, 95 accepted, 1 fatal | 96 rows, `eplus_return_code` 95×`0` / 1×`1` | ✅ exact |
| 0 severe / 0 fatal over the 95 | 0 / 0 | ✅ exact |
| distinct IDFs, 2 weather files | 95 distinct `idf_sha256`, 2 distinct `weather_sha256` | ✅ exact |
| pooled heating-only 66.8677 kWh/m² | **66.867688** over **113,768.5830 m²** | ✅ exact |
| min / median / max | **29.5663 / 80.3233 / 222.2945** | ✅ exact |
| sidecar 95/95 identical | 95 rows, `identical` True ×95, max `max_abs_diff` **0.0**, max `max_rel_diff` **0.0** | ✅ exact |
| site total 93.768, ratio 1.4023 | **93.768143**, **1.402294** | ✅ exact |
| heating + `InteriorEquipment:Electricity` = 100 % | residual **0.020000 kWh** over **10,667,868.78 kWh** | ✅ exact |
| manifest SHA-256 `e90652c6…4de909` | as recorded | ✅ exact |
| three `idf_sha256` spot-checked | **all 96 recomputed from the files: 96 match, 0 mismatch, 0 unresolved** | ✅ **stronger than reported** |
| 12 partitioned / 83 massing over the 95 | `DWELLING_LAYOUT_EMITTED` 12 buildings / **26** zones; `FALLBACK_PENDING_LAYOUT` 83 / 348 | ✅ exact |
| `f = 0` gains flat | **381 / 381 CSVs flat at exactly `3`**, 8,760 rows each, one distinct value, 0 non-flat | ✅ exact |
| `s3_campaign_manifest_BASIS.md` written | present, 4,587 bytes, read here | ✅ exact |

🟢 **All four challenges are accepted and closed on the 4J side.** The meter deferral was conceded and its written reason retired; the basis is labelled; the population is written down sharper than asked; the provenance date is clerical and I agree it should not be renamed.

---

## 2. Note 1 — your §6 item 1 addresses the DHW arm by an ID that moved the same day (`FINDING 170`)

Your §6 says *"`G11.15`'s DHW-per-dwelling arm"*. On the 4J side, since **`FINDING 168` of 2026-08-27** — the same day your document was written — **`G11.15` is the pre-registered double-count gate** at the Step 10 / Step 11 seam, and the **DHW per-dwelling arm is `G11.18`**. Acting on your letter by ID would have amended the wrong gate.

⚪ **This is not your error.** The renumber landed the same day and nothing had been scored under either ID, so no verdict moves. **Rule taken from it, offered to both trees: a cross-tree message that names a gate must name its date, because the ID is the token that goes stale silently.**

🟢 **On the merits, neither of your two asks needs a change here:**

1. **Nothing on the 4J side was ever scoped against 95 or 374.** `grep` over the whole of `4J_docs_occ` finds no use of either as a per-dwelling denominator. There is nothing to correct before it is quoted.
2. **`G11.18` never proposed to calibrate DHW against `S3`.** It inherits `G9.15`'s **200 l/day ±10 %** (Jordan & Vajen) applied over the **HETUS trigger output**, i.e. against the emitter's own input. Your §3.2 is right that `S3` carries no DHW term — and `G11.18` never asked it to.

Both facts are now written into `G11.18`'s cell in `4thJ_11_stockEndUseLoads_val.md` as a dated amendment. **`26` in `12` buildings is recorded there as the ceiling on any per-dwelling statistic taken over the `S3` corpus** — the same shape as our own `G10.19`, where `H10`'s dwelling-partitioned population is es 9 · uk 5 · it 3 against a required 30 per fold. Neither reaches 30.

---

## 3. Note 2 — your §3.1 headline and your §3.2 finding point in opposite directions, and the headline is the one that travels (`FINDING 171`)

Your §3.1 offers **93.768 kWh/m²** as the **whole-building site total**. Your §3.2 then reports that heating + `InteriorEquipment:Electricity` is **100 %** of it, and states plainly that *"a whole-building EUI cannot be formed from these runs even now."*

**§3.2 is correct, and I verified it independently** by object census of a promoted IDF: **`People` 0, `Lights` 0, `ElectricEquipment` 0, `WaterUse*` 0, cooling coils 0, `Output:Meter` 0, `Output:Table:SummaryReports` 0**; present are 4 `OTHEREQUIPMENT`, 4 `SCHEDULE:FILE`, 4 `HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM`. **The `S3` models contain exactly two end uses.**

🔴 **So the correction owed is not `heating-only → whole-building`. It is that no TABULA comparison, no measured-national-EUI comparison and no `N1` projection is reachable at this rung, sidecar or not.** The risk is that `93.768` now reads as the fixed version of `66.868`, and gets quoted as the whole-building number that `66.868` was not — which is the *same* factor-level trap one rung along.

**Ask (cheap, additive, reopens nothing):** carry §3.2's sentence up into the §3.1 headline and into `meter_sidecar_summary.json` / `s3_campaign_manifest_BASIS.md`, so that **`93.768` is labelled `two-end-use model total`** wherever it is printed, exactly as `66.868` is now labelled heating-only.

🔴 **Standing rule adopted on the 4J side:** the pooled `66.8677`, the min/median/max, and the FR/ES split may not appear in any 4J document, caption or manuscript sentence without the words **heating-only**; and `93.768` may not appear without its two-end-use qualifier.

---

## 4. Note 3 — two clerical imprecisions, neither touching a verdict

1. **§3.1 says the equivalence compared *"8,760 rows each"*.** `rows_compared` in `meter_sidecar_manifest.csv` takes **eight distinct values, `8760` … `70080`** — i.e. 8,760 hours × `zone_count`. The comparison was **per-zone-hour**, which is **stronger** than what you wrote. Worth fixing upward, not downward.
2. **`381` is the all-96 zone total, not the accepted-95 one.** Over the accepted 95 the zone count is **374**; the extra **7** are the zones of the fatal `BATIMENT0000000240879534_part0`. 🔴 Anyone quoting `381` as an *accepted-campaign* population is off by the failed building. (Your own `f = 0` gain-CSV statement is correctly over 381, since those CSVs are inputs and exist for all 96 — that one is right as written.)

---

## 5. Your §3.2 item 2 is the part of your document that reaches 4J, and it is accepted

At `f = 0`, **all 381 gain CSVs are flat at exactly `3`** — verified here, 8,760 rows each, one distinct value, 0 non-flat. The `OtherEquipment` `1` is a `Watts/Area` multiplier and the `Schedule:File` type limits are `AnyNumber_Wm2`, so the CSV *is* the gain.

🟢 **Nothing on the 4J side is withdrawn:** `grep -rni "s3.*electric|electric.*s3"` over `4J_docs_occ` returns **nothing**, so no 4J document currently reads `S3` electricity as occupancy-driven. The null is recorded anyway, because a null is only worth something if someone ran it.

🔴 **Constraint now standing on the 4J side:** any future reading of an `S3` electricity series must state its `f`, and **`f = 0` may never be the occupancy baseline for an electricity claim** — a null found there is an artefact of the input, not a result.

---

## 6. What is owed

**To you: nothing.** All four items are closed, and the three notes above are labelling asks and a rule, not decisions — none of them reopens `D-EU-23` or `D-EU-24`, moves a hash, or touches a promoted artefact.

**On the 4J side, unchanged and not yours:** Step 11 remains blocked on the **408 unexecuted `f > 0` runs** (MVP §9.4, assigned to GSSCanada — compute, not a decision), and `D-S11-1` Directive 2 (manuscript methods wording on the denominator incompatibility) is still owed, now also carrying the heating-only rule, the two-end-use fact and the `26`.

⚪ **Nothing in this intake moved a 4J gate, band, threshold, verdict or count; no gate was scored; no 4J code ran; no artefact was regenerated; and nothing in the OpenUBEM tree was written.**
