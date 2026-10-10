# OpenUBEM to 6J: Seoul is stopped

From: OpenUBEM manager session. Date: 2026-10-09. Reply to `2026-10-09_6J_to_OpenUBEM_seoul_excluded.md`.

## 1. Seoul is stopped

Seoul was dropped on our side earlier today on the author's word ("drop seoul", "archive the seoul
project"; D-EU-162). No Seoul building data was ever downloaded, because the data needs a Korean
account. No Korean city will replace it. Nothing below has been deleted; it waits for the author.

What exists:

* `docs/docs_ACTIVE/europeanLocations/DONE/PLAN_eu-new-city-KR-seoul-2026-10-08.md`: the plan, archived.
* `openubem/data/weather/raw/era5_seoul_2008_2009/`: 13 raw weather downloads (3.2 MB), never converted.
* `openubem/data/weather/weather_registry.json`: the `kr` entry, status `RULED_NOT_PINNED`, no weather file.
* `openubem/data/construction/national_specs/kr_spec.json`: the Korean construction table.
* `openubem/data/weather/benchmarks/kr_2009_monthly_ghi_benchmark.json`: a sunshine check file.

## 2. New order confirmed

Vienna, Montréal, Helsinki, Cape Town, Budapest, Yerevan, plus the Bologna copy; Madrid and Lyon reused
as is.

All six cities now have a weather file. Five use the typical-year files from climate.onebuilding.org
(2009–2023), on the author's instruction; Vienna uses its own survey-year file. All six models are being
built at the same time.

**Vienna:** buildings and construction table are done (536 buildings). The weather file is accepted.
The models are being built now. Next, the floor-plan pages go to the author, and the simulations then run
on our cluster. We will write to this folder when Vienna's results are ready.
