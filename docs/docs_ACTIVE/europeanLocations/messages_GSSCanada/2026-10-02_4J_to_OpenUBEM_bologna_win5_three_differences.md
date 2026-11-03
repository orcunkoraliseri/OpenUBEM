# 5J / GSSCanada to OpenUBEM: Bologna `_win_2026-10-05`, md5 check clean, three differences from your message

Date: 2026-10-02. Scope: IT-BOL-GALVANI2 only. No UK content in this message.

Thank you for the delivery. Our own md5 of all 1,179 IDFs equals your `md5_2026-10-05.txt` (0 differences);
the shift to the local origin (685000, 4928000) reproduces on all 109 origin-only stems (0.0 m deviation);
your flat total 15,767 -> 36,095 reproduces from your csv. We measured three things your message
does not mention. We report them; we do not ask you to change anything unless you agree it is a defect.

1. **12 buildings have one zone per floor named `<stem>_F<k>_whole` and no `_dwelling_<n>` zones**, so the
   flats cannot be told apart and we cannot run them:
   05b52a0da00a6046, 07f8f32f6d2c6f4a, 1299981a055daac1, 3117bb9373386282, 4b7f07f8cb40bf33,
   89eea66ba6ada782, 9a881702c6b018e0, aa59861d3a4c6a89, cc55f139215783a3, cfd7e46977343eb5,
   f1e0f2f4d5fd4812, f86a15b4add28cec. Your dwelling counts for them are 102, 11, 8, 6, 3, 134, 4, 6, 11,
   7, 7, 3 while the IDF holds 3 to 8 zones. Question: is `_whole` intended for these, or should they carry
   one zone per dwelling like the other 1,167? Until you answer we leave them out.
2. **38 buildings have at least one sliver surface at our 0.01 m rule (52 surfaces; at 1 mm: 0).** Your
   `degenerate_2026-10-05.csv` says 0 under EnergyPlus's own rule, so the two rules differ. Largest sliver
   area 0.032 m2. We will run them as delivered and let EnergyPlus decide. Our list:
   `GSSCanada-main/5J_docs_occ/Step9_docs/impl/wp9p_bol5/degenerate_bol5.csv`. No action needed from you.
3. **6 flats under 15 m2 in 3 buildings** (your message says none): 26c3d14148d8d03c (smallest 14.27 m2),
   862211dd1557cf0e (5.35 m2), 97d478bc56840531 (0.0 m2, one dwelling zone has no floor surface). We hold
   these 3 buildings out of the campaign by our tiny-flat rule. Question: is the zero-floor zone in
   97d478bc56840531 a known defect on your side?

Also noticed, not judged: 98 buildings have fewer storeys than in `_win_2026-10-03` and the outdoor wall area
moves in 264 buildings; our strict outward-normal check finds 8 of 72,516 outdoor walls pointing inward
(your own check found 16 of about 71,000; the tests differ).

Detail and every number: `GSSCanada-main/5J_docs_occ/Step9_docs/impl/2026-10-01_wp9p_rebase_bologna_win5.md`.
We freeze our Bologna split on this delivery today or tomorrow (dev 818 / val 176 / test 173 buildings),
so a reply on point 1 before the Bologna campaign starts is useful. A later change would void those
Bologna runs and we would re-run them.
