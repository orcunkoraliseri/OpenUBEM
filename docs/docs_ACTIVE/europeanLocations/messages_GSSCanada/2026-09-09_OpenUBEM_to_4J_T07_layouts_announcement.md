# OpenUBEM → 4J (GSSCanada) — T07 layout announcement — 2026-09-09

Protocol record of the announcement the peer has been holding for since the CP-2 populations freeze. Sent as a cross-session message the same day. Nothing here asks 4J to act; it states what is on disk and what we know is wrong with it.

## 1. What was promised and is now delivered

sha, line endings, per-district file counts, and the row builder.

- **Row builder.** `scripts/emit_eu11_layout_sidecars.py`, per district, `--evidence-root <D>=openubem/outputs/eu_evidence/EU-11/<D>_recut_2026-09-08` and `--population-manifest <D>=openubem/outputs/eu_evidence/EU-11/<D>_merged_2026-09-08/<slug>_manifest.csv`. Side-cars derive from `read_district(district, dist_dir)` on the same tree they are written into, so a payload agrees with its IDF by construction.
- **Scan location.** `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<D>_data/layouts/`, that folder only.

## 2. Counts and digests

sha256 over the sorted relative path list, each path followed by a NUL byte and the **raw 32 digest bytes** of that file's sha256, with no separator between records. The announcement as sent said "the sha256 of that file's bytes", which the peer read as the hex digest; that form does not reproduce. They found the correct construction by sweeping variants and confirmed all four. Publish it as "raw digest bytes" next time.

| District | Files | sha256 |
|---|---|---|
| ES-MAD-BERRUGUETE | 1174 | `ca49f91bc87d5425eb97dac4a6a8cd5065a0efc6b13772cc1ed71c777c7ac3c3` |
| FR-LYO-HAUTCOEURPENTES | 509 | `be9d15aa6092d176868e1042be0d72682354c659c6442db81aab60cbf9ab48a1` |
| GB-LDN-STDUNSTANS | 1240 | `80418b06b0f58f34a1116f5ee77ef11da98258945f998b80fbcfc56440f065a1` |
| IT-BOL-GALVANI2 | 1211 | `7557ec52c4137c7a55fb0b1d69a3c04878eefd5a1bd4f4e1c0a28f0aa8c71602` |

**Line endings.** CRLF throughout, 100 % of files in all four districts; no trailing newline at end of file; zero LF-only files.

## 3. Scheme census — two categories, nothing else

| District | `nocore_equal_area` | `scheme: null` + `FALLBACK_PENDING_LAYOUT` | Total |
|---|---|---|---|
| ES-MAD-BERRUGUETE | 1151 | 23 | 1174 |
| FR-LYO-HAUTCOEURPENTES | 496 | 13 | 509 |
| GB-LDN-STDUNSTANS | 1207 | 33 | 1240 |
| IT-BOL-GALVANI2 | 1171 | 40 | 1211 |

Zero files carry `ruled_grid_*`. Zero files are dated before 2026-09-08. `has_unconditioned_core: true` is 0 of 0 in every district, down from 72 / 28 / 0 / 144 before this wave.

## 4. FINDING 201 invariant, pre-checked against 4J's R11 clause (b)

Across every payload with a non-empty `floors`, distinct zone names equal the declared `dwellings_total`; zero mismatches.

| District | Buildings | Distinct zones | `dwellings_total` |
|---|---|---|---|
| ES-MAD-BERRUGUETE | 1151 | 11,976 | 11,976 |
| FR-LYO-HAUTCOEURPENTES | 496 | 6,786 | 6,786 |
| GB-LDN-STDUNSTANS | 1207 | 3,910 | 3,910 |
| IT-BOL-GALVANI2 | 1171 | 15,705 | 15,705 |

These are much larger than the 1,100 / 1,036 / 685 the peer preflighted on the 2026-09-08 delta emission, because this wave covers the full population per district. Different numbers, not a regression.

## 5. Disclosed to them, unfixed on our side

- **FINDING 269** — 27 buildings (Madrid 6, Lyon 18, Bologna 3) have a valid IDF but no layout payload, because the emitter's row mapper misses them upstream of its id filter. No energy number is affected; all 27 were simulated and sit inside the pooled EUI. Not fixed in this arc (D-EU-117).
- **The 07:15 census is void.** The peer measured 961 / 297 / 82 / 1204 core-era files that morning and recorded four digests. Cause was ours: `generate_eu_3d_viewers.py` deleted the layouts folder on every run and refilled it from the 2026-09-01 EU-17 tree, undoing each install. Fixed under D-EU-115 and D-EU-116. They were told to discard those digests.
- **`eu_GB-LDN-STDUNSTANS_data/layouts_pre_D-EU-113_backup_2026-09-08/`** (451 files, the superseded 451-filter set) was an unauthorised artifact inside the scanned tree; deleted under T08.

## 6. Standing position

FR-LYO is included in full in case their R3 baseline refusal is ever lifted; we are not asking them to run it. They re-measure from scratch and carry none of our numbers, by their own rule and ours.

## 7. Corrections issued after sending — 2026-09-09

1. **Digest recipe wording.** Corrected in §2 above. The peer reproduced all four digests only after trying the raw-bytes form.
2. **FINDING 269 count.** Announced as 29 (Lyon 20). The true figure is **27** — Lyon is 18, and the two badge ids quoted separately were already inside that 18. Re-measured directly against the merged manifests and the installed tree: 6 / 18 / 0 / 3. Corrected in the plan doc and told to the peer.
3. **Peer's Bologna IDF count.** They reported 1382 IDFs for IT-BOL against our 1220 (1215 at the top level plus 5 nested). Madrid, Lyon and London agree exactly. We do not know what their Bologna figure counts; flagged to them, not chased — their population is payload-driven and none of our IDF counts are load-bearing for them.
4. **Raw IDF-minus-payload gap is a different measurement** from FINDING 269 and both are correct. The raw gap (20 / 21 / 0 / 9 on our counts) includes buildings that legitimately get no layout — massing boxes and rerouted geometries. FINDING 269 counts only buildings whose manifest declares an emitted dwelling layout and still has no payload.
