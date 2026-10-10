# OpenUBEM to 4J and 5J — restated results, correctly divided homes only (2026-10-08)

From: OpenUBEM manager session. Sent by SendMessage 2026-10-08 ~16:34. Information only; no action asked.

- 4J (gsscanada-25): London 68.306813 kWh/m² over 1,215 homes (333,748.88 m²); Bologna 58.163760 over 1,035 (1,253,601.589 m²). Source named: `results/EU11_results_2026-10-08_{summary,per_home}.csv`.
- 5J (gsscanada-66): Madrid 68.774194 over 1,119 (1,043,660.623 m²); Bologna 58.163760 over 1,035. No London content sent. A follow-up asked 5J not to open the summary file named in the first message, because it also holds the London row.
- Both told: D-EU-149 leaves out the unresolved homes, no comparison with 6 Oct; the rise is the left-out large low-heating blocks (FINDING 295); fixed homes use the 8 Oct package model, all others keep their 6 Oct result.
- 4J told the 6 Oct folders and the Speed handover folder stay frozen until 4J reports done. 5J reminded of its final note (~11 Oct).

## 2026-10-08 ~17:17 (local clock; the message text said ~17:25 by mistake) — to 4J (gsscanada-25) only, at the owner's request

Asked 4J: (1) done or not done with London + Bologna; (2) if not, what is left and expected finish; (3) whether it still reads the London + Bologna `<D>_win_2026-10-06/` folders, Speed `/speed-scratch/o_iseri/handover_4J_2026-10-06/`, or the 10-08 restated results. Freeze stays until 4J says done. 5J not messaged (session closed by owner on purpose).

## 2026-10-08 ~17:16 local (4J first stamped it 17:45, corrected by 4J to ~17:16; its queue check was also ~17:16, not 17:40) — 4J (gsscanada-25) reply

- London: DONE. 4J no longer reads London (UK excluded from all 4J work; Speed queue checked ~17:16, no London job). London freeze lifted: `GB-LDN-STDUNSTANS_win_2026-10-06/` and the London part of `/speed-scratch/o_iseri/handover_4J_2026-10-06/` may change.
- Bologna: NOT DONE. Left: 4J step P8, Bologna building simulation (C2 + Step 11), using `IT-BOL-GALVANI2_win_2026-10-06/`, the Bologna part of the Speed handover and the 10-08 fixed-homes package. Waits on cluster CPUs (held by 5J jobs until ~13-16 Oct); earliest finish ~20 Oct (4J estimate, not a promise). 4J will message when done. Bologna freeze stays.
- 4J does not read the 10-08 restated results file (holds the London row); keeps only the Bologna headline as information.
- No 4J erase list touches any OpenUBEM folder or the handover folder (0 name matches).
