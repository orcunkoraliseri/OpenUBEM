# TABULA / EPISCOPE provenance

Source: IEE Projects TABULA + EPISCOPE (www.episcope.eu)

## Derived registry inputs

`tabula_archetypes_es.json`, `tabula_archetypes_gb.json`, and
`tabula_archetypes_it.json` are derived from the parent Step 8 parameter tables
and the pinned `tabula-calculator.xlsx` workbook, sheet `Calc.Set.Building`.
The calculator workbook is identified by MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`; its SHA-256 is carried in every registry
record. The EU boundary-condition join uses `Tab.BoundaryCond` from
`tabula-values.xlsx`, MD5 `7347b2cae3c4d9f5ce78221e9d5fb832`.

Original workbooks are not mirrored in this repository. Reproduce by obtaining
them from the official EPISCOPE calculator distribution and verifying the
recorded hashes before generation.

## AT (Austria) registry, 2026-10-08

`tabula_archetypes_at.json`: 38 records, generated with
`generate_country_registry("AT", workbook, out, exclude_prefixes=("AT.MT.",))`
from `tabula-calculator.xlsx`, sheet `Calc.Set.Building`, rows
`Code_Country == AT` and `Number_BuildingVariant == 1`. Only the national
series `AT.N.` is kept; `AT.MT.` is excluded (23 rows), reason: parallel series
with period gaps (D-EU-153 amendment). Workbook MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`,
SHA-256 `1fe9865deb4030e5194a8c6abcd7d01446867747064681ba6ac8a99eb0c8b7ce`
(carried in every record). Generated 2026-10-08 (D-EU-153).

## HU (Hungary) registry, 2026-10-08

`tabula_archetypes_hu.json`: 16 records, generated with
`generate_country_registry("HU", workbook, out)` from the same workbook and
sheet, rows `Code_Country == HU` and `Number_BuildingVariant == 1`. Workbook MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`, same SHA-256 as above. Generated 2026-10-08
(D-EU-153).

## Third-party terms

Retrieved 2026-08-23 from <https://episcope.eu/communication/download/>:

> Rules for Usage of the TABULA 'Building Typology' Approach (Systematics, Data
> and Tools) by Third Parties:
>
> The usage of the TABULA approach, data, and tools in research projects,
> theses, and software applications by third parties is intended and desired.
> Only non-exclusive utilisations are possible.
>
> A condition for usages of any kind (files, datasets, pictures, ...) is that
> 'IEE Projects TABULA + EPISCOPE (www.episcope.eu)' is visibly mentioned as
> the source.

The registry licence status is `VERIFIED`. This quotation and the retrieval
date are drawn verbatim from the accepted DR09 report.

## FI (Finland) national records, 2026-10-08

`tabula_archetypes_fi.json`: 28 records (SFH, TH, MFH, AB × FI.01–FI.07), built
by `national_records.build_records` from `national_specs/fi_spec.json`
(D-EU-152). Finland has no TABULA data. Every field not listed below is copied
from a Swedish TABULA record (donor, national series `SE.N.`, workbook MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`) and stamped `ASSUMED:donor <id>` in
`parameter_assumptions`. Retrieved 2026-10-08.

Periods (Finnish building-code C3 editions): FI.01 up to 1975, FI.02
1976–1977, FI.03 1978–1984, FI.04 1985–2002, FI.05 2003–2007, FI.06 2008–2009,
FI.07 2010 onward. Donor pairing by period overlap: FI.01 to SE.01, FI.02 and
FI.03 to SE.03, FI.04 to SE.04, FI.05 to FI.07 to SE.05 (SE ends 2005, nearest
used for 2006+). SE has no TH or AB record: TH uses the SE SFH record, AB the SE
MFH record.

Sources:

- Motiva, "Tyypillisiä olemassa olevien vanhojen rakennusten alkuperäisiä
  suunnitteluarvoja" (Energiatodistusoppaan 2018 liite, 1.11.2018),
  <https://www.motiva.fi/wp-content/uploads/sites/2/2025/08/Tyypillisia-olemassa-olevien-vanhojen-rakennusten-alkuperaisia-suunnitteluarvoja-%E2%80%93-Energiatodistusoppaan-2018-liite.pdf>.
  Walls §2.1 pp.5–7, roofs §2.2 pp.7–8, floors §2.3 pp.8–10, windows §2.4
  pp.11–12. Rows used: "1969 RIL-suositus" south of the Oulu–Kajaani–Kuhmo line
  (FI.01), "1975 määräykset" and "1976 määräykset" (FI.02), "1978 määräykset"
  (FI.03), "1985 määräykset" (FI.04), "2007 määräykset" (FI.06, original not
  retrieved).
- Ympäristöministeriö, C3 Rakennuksen lämmöneristys, Määräykset 2003, §3.2.1
  (p.5), <https://ym.fi/documents/1410903/155128351/C3-2003.pdf> (FI.05: wall
  0.25, roof 0.16, ground 0.25, window 1.4 W/m²K).
- Ympäristöministeriö, C3 Rakennusten lämmöneristys, Määräykset 2010, §3.2.1
  (p.7, reference values, warm space),
  <https://ym.fi/documents/1410903/155128351/34163-C3-2010_suomi_221208.pdf>
  (FI.07: wall 0.17, roof 0.09, ground 0.16, window 1.0 W/m²K).
- Statistics Finland, Dwellings and Housing Conditions 2009, appendix table 2
  "Floorarea per dwelling by type of building 1970-2009, whole dwellingstock",
  <https://stat.fi/til/asas/2009/asas_2009_2010-05-26_tau_002_en.html>, row 2009:
  detached houses 108.0 (SFH), attached houses 71.1 (TH), blocks of flats 56.5
  (MFH and AB) m² per dwelling.

Limits: FI.01 values are a design recommendation (RIL 1969), not a measured
stock mean; SFH and TH take the "up to 100 kg/m²" wall and roof class, MFH and AB
the "over 100 kg/m²" class for FI.01–FI.03 (class assignment assumed); window U
values are code or recommended values. Window-to-wall share, window g-value,
thermal-bridge add-on and infiltration have no Finnish source by period and keep
the donor values (`ASSUMED`). Door U stays the donor's. The attribution of every
record adds "national sources per parameter_assumptions".

## AM (Armenia) national records, 2026-10-08

`national_specs/am_spec.json` (every value with `source` or `ASSUMED`) built into
`tabula_archetypes_am.json` (20 records: SFH, TH, MFH, AB x 5 periods) with
`national_records.build_records` (D-EU-152). Donor country BG (workbook MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`). Periods `AM.01` up to 1950, `AM.02` 1951-1970,
`AM.03` 1971-1990, `AM.04` 1991-2015, `AM.05` 2016 and later. Donor of each period,
chosen by most overlapping years from 1900: AM.01 BG.03 (TH: BG.02, no BG.03 TH
record), AM.02 and AM.03 BG.04, AM.04 BG.05, AM.05 BG.06; archetype `.Gen` of the
same building type.

Sources and values:

- Armstat, "RA Housing Stock and Communal Economy 2020",
  <https://armstat.am/file/article/bnakfond_2021_1.pdf> (Armenian; file retrieved
  2026-10-08). Buildings managed by homeowners' associations and trustees, Yerevan
  4,721: by commissioning period, PDF p.50 (printed p.54): up to 1950 344,
  1951-70 1,729, 1971-80 1,213, 1981-90 1,123, 1991-2000 139, 2001-10 91, 2011+ 82;
  Nor Nork 657: 0, 268, 189, 164, 32, 2, 2. By wall material, PDF p.47 (printed
  p.51, table a): Yerevan stone 2,219, panel 2,376, monolithic 126; Nor Nork stone
  205, panel 439, monolithic 13. Nor Nork flats and area, PDF p.50-51 (printed
  p.54-55): 34,417 flats, 2,234,659 m2, so 64.93 m2 per flat (MFH and AB mean flat
  area). Armenia-wide stone 13,281 and panel 4,430 of 19,183 multi-apartment
  buildings (69.2 % and 23.1 %), PDF p.54 (printed p.58).
- Wall: stone 600 mm "midis" wall R = 1.144 m2K/W, U 0.874; prefabricated panel R =
  1.58 m2K/W "at best", U 0.633 (urbanista.am, "Is housing in Armenia affordable?",
  Figure 9, which cites the Armstat table above; the Armstat original of R was not
  found; U = 1/R without surface films, as pinned in the plan). Avan demonstration
  building audit (UNDP-GEF "Improving Energy Efficiency in Buildings",
  <https://nature-ic.am/Content/announcements/7123/Avan-DSK-Audit-Report-ENG.pdf>,
  p.6): 300 mm bearing panels without insulation (qualitative only).
- Period to wall material (ASSUMED): Armstat has no period x material table. Stone
  for AM.01, AM.02 and AM.04, panel for AM.03, inferred from the two Yerevan totals
  above (2,073 buildings up to 1970 against 2,219 stone; 2,336 built 1971-90
  against 2,376 panel; the 312 built after 1990 then hold 146 stone, 40 panel, 126
  monolithic) and from World Housing Encyclopedia reports 202 (stone "mydis" walls,
  1958-1970), 204 (stone, early 1970s to 1988) and 203 (large panel, from the 1970s),
  <https://wheki-dev.globalquakemodel.org/reports/report_202>. In Nor Nork the
  same arithmetic does not close (268 buildings up to 1970 but only 205 stone), so
  the rule is a Yerevan-wide inference. SFH and TH take the multi-apartment value of
  the same period.
- AM.05: RACN 24-01-2016 "Thermal Protection of Buildings" (Order of the Minister of
  Urban Construction No. 120-N of 16 June 2016), PDF from nature-ic.am
  (`RACN for publishing_19.08.2016.pdf`), Table 3 (PDF p.19, printed p.10),
  residential row, base row 1000 degree-days: wall R0 1.8 (U 0.556), floor over
  cold basement R0 2.40 (U 0.417); wall 0.56 and floor 0.42 as listed by World Bank
  Building Green, Armenia, "Passive design (Residential)",
  <https://www.worldbank.org/en/building-green/explorecountries/armenia>. The same
  Table 3 at Yerevan's own heating degree-days (about 2,660 from the Yerevan SEAP:
  140 days, mean 1 degC, indoor 20 degC) would be stricter (formula 3: wall R0 2.33,
  U 0.43).

Limits: roofs, ground floors before 2016, windows, g-value, thermal-bridge add-on,
infiltration, window-to-wall share and all other fields keep the BG donor values
and are stamped `ASSUMED:donor <archetype_id>`; no Armenian existing-stock source
for them was found (the Avan audit report in English and the OECD/IEA Armenia
roadmap give none; the UNECE Armenia study could not be downloaded).
Several wall slots of the donors are stored with a ratio fallback
(`RATIO_FALLBACK: <slot>`). The attribution of every record adds "national sources
per parameter_assumptions".

## KR (South Korea) national records, 2026-10-08

`tabula_archetypes_kr.json`: 28 records (AB, MFH, TH, SFH × KR.01–KR.07), built
by `national_records.build_records` from `national_specs/kr_spec.json`
(D-EU-152). Korea has no TABULA data. Every field not listed below is copied
from a Serbian TABULA record (donor, national series `RS.N.`, workbook MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`) and stamped `ASSUMED:donor <id>` in
`parameter_assumptions`. Retrieved 2026-10-08.

Periods (Korean building energy-saving design standard editions): KR.01 up to
1979, KR.02 1980–1987, KR.03 1988–2000, KR.04 2001–2008, KR.05 2009–2012, KR.06
2013–2017, KR.07 2018 onward. Donor pairing by period overlap (open ends bounded
at 1900 and 2023): KR.01 to RS.02, KR.02 to RS.06, KR.03 to KR.05 to RS.07, KR.06
and KR.07 to RS.08 (TH has no RS.08, so RS.07).

Sources:

- Kwag, Han, Kim, Kim, Kim, "Analysis of the Effects of Strengthening Building
  Energy Policy on Multifamily Residential Buildings in South Korea",
  Sustainability 12(9):3566 (2020), doi:10.3390/su12093566, Table 2 "History of
  building envelope requirements in South Korea", Central zone, Direct column
  (wall, roof, floor, window): Period 2 (1981–1984) 0.58/0.58/1.16/3.49 (KR.02),
  Period 4 (Aug 1987–Jan 2001) 0.58/0.41/0.58/3.37 (KR.03), Period 5 (Feb
  2001–Jul 2008) 0.47/0.29/0.35/3.84 (KR.04), Period 7 (Dec 2010–Sep 2013)
  0.36/0.20/0.30/2.10 (KR.05), Period 9 (Feb 2016 on) 0.21/0.15/0.18/1.20
  (KR.06). Edition for each KR period: the one in force on 1 July in most of the
  period's years, ties to the later edition.
- Korea Energy Agency, 에너지절약설계기준 FAQ (2019), p.114, [별표1] 지역별 건축물
  부위의 열관류율표, the table of MOLIT notice 제2017-881호 (2017-12-28, in force
  2018-09-01), 중부2지역 (Seoul), exposed to outside air, 공동주택: wall 0.170, roof
  0.150, heated floor 0.170, window 1.000 W/m²K (KR.07),
  <https://www.greentogether.go.kr/ebook2019/eais_faq_edition_2019/files/basic-html/page114.html>.
- National Atlas of Korea (대한민국 국가지도집), English edition III (2021),
  "Housing Types", <http://nationalatlas.ngii.go.kr/pages/page_2687.php>:
  "Apartments had the largest living area at 76 m2 per household" (AB mean flat
  area; data year and net or gross basis are not stated on the page).

Limits: the Kwag table is the apartment (공동주택) limit; it is applied to all four
types and all periods (no non-apartment series for 1981–2016 was found, so the
looser 2018 non-apartment limits 0.240 wall and 1.500 window were not used).
Legal limits stand in for the stock mean. Floors use the exposed (heated floor)
limit although ground-contact floors are legally "indirect". Window limit rises
from 3.37 (1987 edition) to 3.84 (2001 edition) as printed in Kwag Table 2.
KR.01 (up to 1979): no Korean study of the uninsulated stock was found; wall,
roof, floor and window U keep the donor values (`ASSUMED`). Window-to-wall share,
window g-value, thermal-bridge add-on, infiltration and the flat area of MFH, TH
and SFH have no Korean source and keep the donor values (`ASSUMED`). The
attribution of every record adds "national sources per parameter_assumptions".

## CA (Canada, Montreal) national records, 2026-10-08

`tabula_archetypes_ca.json`: 24 records (SFH, TH, MFH, AB x CA.01 to CA.06), built
by `national_records.build_records` from `national_specs/ca_spec.json` (D-EU-152;
every value in the spec carries its `source` or an `ASSUMED:` reason). Donor
country SE (workbook MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`, series `SE.N.`).
Periods: CA.01 up to 1945, CA.02 1946-1960, CA.03 1961-1977, CA.04 1978-1983,
CA.05 1984-2011, CA.06 2012+ (Quebec energy regulation of 1983; Partie 11 of the
Construction Code from 2012).

Donor pairing (SE has SFH and MFH only; TH takes the SFH donor and AB the MFH
donor, `ASSUMED`): CA.01 and CA.02 take SE.01 (up to 1960), CA.03 SE.02
(1961-1975), CA.04 SE.03 (1976-1985), CA.05 SE.05 (1996-2005; SE.04 and SE.05
overlap CA.05 by 10 years each, the tie goes to the period holding the middle of
CA.05), CA.06 SE.05 (nearest, no overlap). Every non-overridden field is copied
from the donor and stamped `ASSUMED:donor <id>`.

Sources:

- CA.01 to CA.05 opaque U-values, infiltration and window share: Swan, Ugursal and
  Beausoleil-Morrison, "Canadian housing stock database for building energy
  simulation", eSim 2008 (IBPSA-Canada), p.149, Table 3 (CSDDRD single-detached
  averages by vintage <1946, 1946-1969, 1970-1979, 1980-1989, 1990-2003):
  `https://publications.ibpsa.org/proceedings/esim/2008/papers/esim2008_143_150.pdf`.
  Rows used: ceiling RSI 3.8 / 4.2 / 4.4 / 5.1 / 5.6; living wall RSI 1.6 / 1.8 /
  2.2 / 2.6 / 2.9; basement wall RSI 1.6 / 1.6 / 1.6 / 1.9 / 1.9; ACH50 10.2 / 6.9 /
  5.8 / 5.2 / 4.4; window share 14.2 / 17.2 / 16.4 / 15.6 / 15.2 %. The 1961-1977,
  1978-1983 and 1984-2011 periods straddle columns and take the year-weighted mean
  (9:8, 2:4, 6:22); the last column is extended to 2011. National vintage columns
  are applied to Quebec and to all four types (`ASSUMED`; the paper gives Quebec
  only as an all-vintage average: ceiling 4.6, wall 2.5, basement 2.1, ACH50 6.1,
  window share 16.8 %). U = 1/RSI. The basement-wall value feeds the below-grade
  floor slot (`ASSUMED`). Infiltration n = ACH50 / 20 (`ASSUMED` divisor).
- CA.05 window U 2.85 W/(m2.K): ACQ, Fiche technique Chapitre 1.1, fiche 1 de 5
  (April 2021), p.3, column "Precedemment (REENB)" (Reglement sur l'economie de
  l'energie dans les nouveaux batiments, E-1.1 r.1, 1983), glazed part only.
  `https://www.acq.org/wp-content/uploads/2021/05/residentiel-fiches-techniques-efficacite-energetique-fiche1.pdf`.
  The same table gives the REENB wall RSI 2.38, roof 3.10, floor 2.20 (5000-5999
  degree-days), used as a cross-check only: the CSDDRD stock averages are higher.
- CA.06 (2012+): Gazette officielle du Quebec, 22 February 2012, Partie 2, no 8,
  pp.952-954, draft Partie 11 of the Construction Code, Tableau 11.2.2.1.A
  (<= 6200 degree-days under 18 C): roof RSIT 7.22, above-grade wall 4.31,
  foundation wall 2.99; Tableau 11.2.2.4.A: window U 2.0 with RE 21.
  `https://www.publicationsduquebec.gouv.qc.ca/fileadmin/gazette/pdf_encrypte/lois_reglements/2012F/56849.pdf`.
  This is the published draft text; the adopted text was not checked. Infiltration,
  g-value and thermal-bridge add-on keep the donor values (`ASSUMED`).
- CA.01 to CA.04 window U (4.0, 4.0, 3.0, 3.0): no Canadian stock study of window U
  by vintage was found, so these are `ASSUMED` values.
- Mean flat area of MFH and AB: measured on the Montreal property roll (Unites
  d'evaluation fonciere, donnees.montreal.ca, CC BY 4.0), borough code REM21
  (Le Plateau-Mont-Royal), residential use codes 1000-1999, median of
  SUPERFICIE_BATIMENT / NOMBRE_LOGEMENT per roll record. MFH = 3-4 storeys, median
  per period (95.7, 56.0, 49.2, 105.0, 86.1, 103.2 m2; n = 5443, 170, 196, 37, 201,
  79). AB = 5+ storeys, all periods pooled (64.9 m2; n = 74). SFH and TH keep the
  donor single dwelling. SUPERFICIE_BATIMENT is taken as total floor area
  (`ASSUMED`; its median grows 85, 169, 345 m2 for 1, 2, 3 storeys).

The attribution of every record adds "national sources per parameter_assumptions".

## ZA (South Africa, Cape Town) national records, 2026-10-08

`national_specs/za_spec.json` builds `tabula_archetypes_za.json` (12 records:
AB, MFH, SFH, TH x ZA.01, ZA.02, ZA.03) with `national_records.build_records`
(D-EU-152). Donor country ES (pinned-workbook registry `tabula_archetypes_es.json`,
MD5 `c99ddc9ffcb6dc0ae7391273d9619e37`). Periods: `ZA.01` up to 1950, `ZA.02`
1951-2011 (no thermal requirement), `ZA.03` 2012 onward (SANS 10400-XA, climate
zone 4, Cape Town, temperate coastal).

Donor pairing (period overlap): ZA.01 takes ES.02 (1901-1936, longest bounded
overlap); ZA.02 takes ES.05 (1980-2006, 27 of 61 years); ZA.03 takes ES.06. Exception:
ZA.02 MFH takes `ES.ME.MFH.04` because `ES.ME.MFH.05` has no window area and a
non-numeric window U-value, so it cannot be rescaled.

Sources actually read:

- NHBRC Technical Guidelines, Energy Efficiency
  (<https://nhbrc.org.za/wp-content/uploads/2020/10/IBT-Energy-Efficiency-Guidelines.pdf>):
  Table 4 p.14 roof minimum total R 3.7 m2K/W for zone 4 (citing SANS 10400-XA
  4.4.5); Table 1 p.7 non-masonry wall R 1.9 (zones 2-5) and 2.2 (zones 1, 6);
  p.7 deemed-to-satisfy masonry wall; Table 2 p.8 220 mm rendered brick total R
  0.42 m2K/W; section 4.2 p.8 fenestration at most 15 % of net floor area
  (SANS 10400-XA 4.4.4.1), clear glass accepted; Table 5 p.15 roof layer
  resistances (Ra 0.03, air space 0.18, plasterboard 0.06, Rs 0.11); p.3 the
  regulation was promulgated 9 September 2011 (Government Gazette 34586, R.711).
- Swartland insulation article, sadecor.co.za: "Zone 4: Temperate coastal (Cape
  Town, Port Elizabeth) ... Minimum required total R-value: 3,7" (second source
  for the roof value).
- Emergy / GreenCape presentation, 15 Oct 2013, slide 5: prescriptive walls 1.9-2.2,
  roofs 2.7-3.5, glazing at most 15 % of floor area (consistent, not used as a value).
- Stellenbosch University MPhil thesis (Muringathuparambil, 2016, hdl 10019.1/100440):
  abstract only (uninsulated walls and roofs, missing ceilings, air leakage). The
  full text server answered HTTP 429, so no stock U-value table was read.

Values used:

- Roof ZA.03 U = 1/3.7 = 0.2703 (sourced). Roof ZA.01-02 U = 1/0.38 = 2.6316
  (`ASSUMED` no insulation; layers from NHBRC Table 5 without insulation).
- Wall all periods U = 1/0.42 = 2.3810 (sourced for ZA.03 as the deemed-to-satisfy
  masonry example; `ASSUMED` typical brick for ZA.01-02). The wall conflict in the
  feasibility note (0.35 ... 2.2) resolves as: 1.9 and 2.2 are non-masonry limits;
  0.35 for masonry was seen only in a municipal energy report found by search and
  is not used.
- Window U 5.35 W/m2K, single glazing, all periods (`ASSUMED`, TABULA ES
  single-glazed value of `ES.ME.AB.02`; no South African table retrieved; clear
  single glass remains allowed up to 15 % of floor area).
- Window share: the donor value, unchanged (`ASSUMED`, all periods; resulting shares
  0.07-0.52). Converting the 15 % of net floor area ceiling (SANS 10400-XA 4.4.4.1)
  through the Spanish donor geometry gave shares 0.08-0.49 that reflect the donor
  building, not South Africa (manager ruling 2026-10-08), so no `wwr` entry is set,
  as for Finland, Korea and Armenia.
- Infiltration 0.4 1/h for ZA.02 (`ASSUMED`, unregulated envelope); other periods
  keep the donor value. Floor U, g-value, thermal bridges, areas, flats: donor
  (`ASSUMED:donor`).
- Heat-loss parts are recomputed by the C01 series-resistance rule; slots that fell
  back to the ratio rule are listed in each record's `parameter_assumptions`.

The attribution of every record adds "national sources per parameter_assumptions".
