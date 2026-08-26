# EU-07 Lyon-Bron ERA5 weather gates

## Gate 6 - EnergyPlus smoke

- EPW: `openubem/data/weather/fr_lyon_bron_2023_era5.epw`
- EnergyPlus: 23.1 executable configured by the project
- Return code: `0`
- Severe errors: `0`
- Completion marker: `EnergyPlus Completed Successfully`
- Result: **PASS**

## Gate 5 - monthly national-station benchmark

The Lyon-Bron Météo-France station (WMO 07480; 45.72 N, 4.95 E) reports 2023 monthly mean temperatures and sunshine hours. The published monthly mean temperatures are:

`[5.5, 5.9, 9.9, 11.2, 16.5, 22.2, 23.9, 24.3, 21.8, 16.8, 9.2, 6.5] C`

The ERA5 EPW monthly means are:

`[5.27, 5.24, 9.49, 11.11, 16.11, 21.54, 23.56, 23.91, 20.55, 15.79, 8.58, 6.19] C`

The maximum absolute temperature difference is 1.25 K, within the DR08 limit of 1.5 K.

The station page does not publish monthly GHI. Sunshine hours are not substituted for GHI, so the required `|Delta GHI| <= 10%` test is not evidenced.

## G5-A PVGIS/JRC independent GHI benchmark

The approved G5-A benchmark was queried from the European Commission Joint Research Centre PVGIS MRcalc service at latitude 45.72, longitude 4.95, using the 2023 monthly horizontal irradiation values (`H(h)_m`, kWh/m2). The API endpoint was:

`https://re.jrc.ec.europa.eu/api/v5_3/MRcalc?lat=45.72&lon=4.95&horirrad=1&outputformat=json`

ERA5 EPW versus PVGIS 2023 monthly GHI (kWh/m2):

| Month | ERA5 | PVGIS | Absolute relative difference |
|---|---:|---:|---:|
| Jan | 37.12 | 37.42 | 0.8% |
| Feb | 70.64 | 74.04 | 4.6% |
| Mar | 113.04 | 107.01 | 5.6% |
| Apr | 135.21 | 134.95 | 0.2% |
| May | 168.00 | 172.81 | 2.8% |
| Jun | 199.24 | 206.59 | 3.6% |
| Jul | 194.43 | 208.60 | 6.8% |
| Aug | 160.66 | 171.72 | 6.4% |
| Sep | 141.92 | 145.60 | 2.5% |
| Oct | 89.53 | 88.91 | 0.7% |
| Nov | 36.79 | 42.69 | **13.8%** |
| Dec | 31.40 | 33.68 | 6.8% |

Result: **NOT PASS under the adopted per-month 10% limit** because November exceeds tolerance. The EPW remains out of `weather_registry.json` pending an owner ruling on this measured exception; no value has been hidden or averaged away.

PVGIS documentation: [JRC PVGIS monthly radiation](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/pvgis-5-tools/monthly-radiation_en) and [PVGIS API](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/api-non-interactive-service_en).

Source: [Infoclimat Lyon-Bron 2023 climatology](https://www.infoclimat.fr/climatologie/annee/2023/lyon-bron/valeurs/07480.html) (station identity, coordinates, monthly observations).
