# 4J to OpenUBEM: progress on the win_2026-10-06 London + Bologna runs (2026-10-06 11:20 EDT)

Reply to your status check of 2026-10-06. Please keep both trees and the Speed handover copy frozen; we will message when done.

1. **Stage: running.**
   - London (GB-LDN-STDUNSTANS): full run RUNNING on Speed since 10:16 EDT. 550 of 12,400 runs done = 55 of 1,240 buildings complete, 0 failed. (Each building = 2 cases x 5 levels = 10 runs.)
   - Bologna (IT-BOL-GALVANI2): queued behind London (starts when London ends). We simulate 1,161 of your 1,164 ids: 30835, 33610 and 81117 have no layout side-car in the package, as stated in our 10-06 message, so they are left out and reported as a limitation.
   - Before the full run: deploy check passed on both districts (payload digests London 168f0ef6..., Bologna 4bdb1cb8...); test runs 80/80 passed, including 30 runs on buildings whose flats span several storey zones (your zone -> flat map: one household on every storey zone of its flat).

2. **Blockers / needs: none.**

3. **Expected done (estimate, not yet measured on the largest Bologna buildings):** London ~6 Oct night, Bologna ~8-9 Oct, our post-processing ~9 Oct. Based on test timings and the September Bologna run (8,941 runs in 1,014 CPU-hours). We will tell you when both are done so you can unfreeze.
