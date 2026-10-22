# 4J (GSSCanada) to OpenUBEM - Bologna C2 run stopped (2026-10-13 11:15 EDT)

- The Bologna C2 building run on Speed (jobs 1445743-47) was STOPPED on purpose by the author on 2026-10-13 11:14. It was not an OpenUBEM or EnergyPlus problem.
- Reason: our diary generator gave identical diaries to identical synthetic people (a per-request sampling seed in vLLM). The occupancy schedules fed to Madrid C2 and Bologna C2 came from those copied diaries.
- State at stop: 11,324 cells completed + 200 failed (the 13 known geometry buildings) of 11,620. Files kept in `/speed-scratch/o_iseri/4J_esit/p8/c2_bol/out/IT-BOL-GALVANI2`, marked "copied pool"; not used as results. Madrid C2 outputs: same label.
- Plan: re-make the diaries without the copying, then re-run Madrid and Bologna C2 with the same campaign tools. Nothing is asked of OpenUBEM now; we will tell you when the re-runs start.
