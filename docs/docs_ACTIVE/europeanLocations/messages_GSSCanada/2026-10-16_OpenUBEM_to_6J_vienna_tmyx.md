# Vienna typical-year weather file for 6J (written 2026-10-19 09:41 EDT by the 6J manager, on the author's request)

No OpenUBEM session answered the 10-16 request; the author asked the 6J manager to fetch the file.

1. Station: Wien-Schwechat airport (WMO 110360), TMYx 2009-2023. Airport chosen because the other TMYx cities also use airport stations (Helsinki-Vantaa, Budapest Liszt Ferenc, Cape Town Intl, Montreal Trudeau). Other Vienna stations on the site (Innere Stadt 110340, Hohe Warte 110350) were not used.
2. Source: https://climate.onebuilding.org/WMO_Region_6_Europe/AUT_Austria/NO_Lower_Austria/AUT_NO_Wien-Schwechat.AP.110360_TMYx.2009-2023.zip (downloaded 2026-10-19 09:38 EDT). Citation as given on the site: Lawrie LK, Crawley DB. 2026. Development of Global Typical Meteorological Years (TMYx).
   Local: `openubem/data/weather/raw/tmyx_at/` (zip + epw). Speed: `/speed-scratch/o_iseri/6J/weather/vienna_tmyx/` (epw only). md5 779e59f8796483bd67f84b31c0fffd82 both sides.
   Header: LOCATION Wien-Schwechat.AP, AUT, SRC-TMYx; Period of Record 2009-2023; 8760 rows; DATA PERIODS start Sunday 1/1. The 6J W3 Vienna gate (`step5w3_common.vienna_gate`) returns OK on this file.
3. Not done: `weather_registry.json` not edited (left to OpenUBEM); no Vienna run started.
