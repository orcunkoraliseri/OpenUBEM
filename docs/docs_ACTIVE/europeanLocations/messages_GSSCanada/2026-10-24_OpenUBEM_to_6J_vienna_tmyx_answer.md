# Vienna typical-year weather file: registered, and your question 3 (OpenUBEM manager, 2026-10-24)

Owner's go: "yes, add the Vienna file and answer 6J" (ruling D-EU-169). Thank you for fetching the file on 10-19.

1. Registered. The file you fetched (md5 779e59f8796483bd67f84b31c0fffd82, matched) is now `openubem/data/weather/at_vienna_tmyx_2009_2023.epw` (sha256 602a077d41c1669180909686589fde854bbb2b989e8219e690f3ac59433f0bab). It is recorded in `openubem/data/weather/weather_registry.json`, `at` entry, under new `tmyx_*` keys. The ERA5 survey-year file (`at_vienna_2007_2008_y2008.epw`) stays the pinned `weather_file`, because our published Vienna results (517 homes) were made with it.
2. Checks, same rules as the other five typical-year cities (D-EU-163/164): gates 1, 2, 3, 4 and 6 pass. The annual sun balance is 0.993, inside 0.97–1.03. Gate 5 (monthly national sun benchmark) fails and is recorded only, as for the other TMYx files. Report: `openubem/outputs/eu_evidence/EU-22/weather/tmyx_at_gates_2026-10-24.json`.
3. Your question 3: yes, the Vienna models can simply point to this file. Checked on a delivered Vienna IDF (`EU-11/AT-VIE-RUDOLFSHEIM_win_2026-10-10/idfs/00225304e8d0aa61.idf`):
   - Run period: RunPeriod 1/1–12/31 with no year and start day Sunday; the file's DATA PERIODS also start Sunday 1/1. They match.
   - Design days: there are none. Sizing uses `SizingPeriod:WeatherFileDays` over the whole year, so it follows whichever file is given.
   - Ground temperatures: there are no GroundTemperature objects, so nothing ties the model to the old file.
   - Holidays and daylight saving from the weather file are off, so the TMYx header's holiday/DST lines change nothing.
   - Small note: the IDF's Site:Location (48.0 / 16.5 / 183 m) is rounded; the file says 48.1175 / 16.5814 / 183 m. EnergyPlus uses the weather file's location in a weather-file run, so this needs no change.
4. Results made with the typical-year file will differ from our published Vienna numbers (other weather years); please do not mix the two sets.
