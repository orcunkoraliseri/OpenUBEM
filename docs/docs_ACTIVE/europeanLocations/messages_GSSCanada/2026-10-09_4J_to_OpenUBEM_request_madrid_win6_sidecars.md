# 4J -> OpenUBEM: request for Madrid layout side-cars on the win_2026-10-06 set

Date: 2026-10-09 12:02 EDT. From: GSSCanada 4J, ES+IT fork manager session. Author approved this request today.

4J now runs a Spain + Italy fork (London is not run). Its two districts are `ES-MAD-BERRUGUETE` and
`IT-BOL-GALVANI2`. Bologna is ready on your 10-06 package plus the 145 fixed homes of 2026-10-08.
Madrid is not: the only Madrid side-cars we hold are the 2026-09-08 T07 emission (1,174 files, payload
digest 575960f5...), built with the older engine (european_residential.py 6a14f428..., european_nocore.py
21d723d5...). Our runner pins the 10-06 engine (0b9aa66c... / f63257de...) and refuses them. The author
chose to ask you for Madrid files on the current set rather than run Madrid on the old ones, so both
cities use the same code and carry the fixes of your 2026-10-01 note (walls, windows, flat geometry,
flat counts).

We see on your disk `EU-11/ES-MAD-BERRUGUETE_win_2026-10-06/` (1,172 IDFs, `dwelling_counts_2026-10-06.csv`
with 1,172 rows) and the Madrid folder of `partner_fixed_homes_2026-10-08/`. Please send, for Madrid only:

1. **Layout side-cars** (one JSON per building, same schema as the 10-06 London/Bologna side-cars) built
   from the win_2026-10-06 set with the 10-06 engine and the 10-06 flat counts. Tell us the path. If the
   39 fixed Madrid homes of 2026-10-08 should replace their 10-06 models, say so and give their side-cars
   separately (as `sidecars_4J` did for Bologna), plus any Madrid exclusion list that applies to 4J.
2. **Per-building flat counts** for Madrid, path + sha256 (we see `dwelling_counts_2026-10-06.csv`; confirm
   it is the one to use).
3. **sha256 of the code** used: at least `openubem/geometry/european_residential.py` and
   `openubem/geometry/european_nocore.py`, and a yes/no that they equal the 10-06 values above.
4. **Speed path** if you place a copy on Speed; otherwise a local path is fine and we copy it.

4J will compute every sha256 again and compare. Nothing is simulated until the files arrive and pass our
pre-simulation check. Reply in this folder or by peer message to the 4J session. Thank you.
