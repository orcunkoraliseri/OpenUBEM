from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
OUT_DIR = ROOT / "openubem" / "outputs"
EVID = OUT_DIR / "eu_evidence" / "EU-11"
RES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "results"
OUT_CSV = CMP / "paper_eu_hdd_2026-10-21.csv"
OUT_PNG = OUT_DIR / "paper_eu_eui_vs_hdd.png"

BASE_C = 18.0
DRY_BULB_COL = 6
SITES = {
    "ES-MAD-BERRUGUETE": ("Spain", "win_2026-10-06"),
    "FR-LYO-HAUTCOEURPENTES": ("France", "win_2026-10-06"),
    "GB-LDN-STDUNSTANS": ("United Kingdom", "win_2026-10-06"),
    "IT-BOL-GALVANI2": ("Italy", "win_2026-10-06"),
    "CA-MTL-PLATEAU": ("Canada", "win_2026-10-09"),
    "AM-EVN-NORNORK": ("Armenia", "win_2026-10-09"),
    "ZA-CPT-WOODSTOCK": ("South Africa", "win_2026-10-09"),
    "FI-HEL-KALLIO": ("Finland", "win_2026-10-10"),
    "AT-VIE-RUDOLFSHEIM": ("Austria", "win_2026-10-10"),
    "HU-BUD-ERZSEBETVAROS": ("Hungary", "win_2026-10-10"),
}
INTERNAL_ONLY = {"ZA-CPT-WOODSTOCK"}
FOUR = {"ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"}


def read_epw(path: Path) -> tuple[str, np.ndarray]:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    header = lines[0].strip()
    temps = np.array([float(r.split(",")[DRY_BULB_COL]) for r in lines[8:] if r.strip()])
    return header, temps


def heating_degree_days(hourly: np.ndarray, base: float = BASE_C) -> float:
    n_days = len(hourly) // 24
    daily = np.asarray(hourly[: n_days * 24], dtype=float).reshape(n_days, 24).mean(axis=1)
    return float(np.clip(base - daily, 0.0, None).sum())


def eui_row(site: str) -> dict:
    if site in FOUR:
        d = json.loads((RES / "EU11_results_2026-10-08_summary.json").read_text())["districts"][site]
        return dict(d, vintage="2026-10-08")
    f = glob.glob(str(RES / f"EU22_results_{site}_*_summary.json"))[0]
    s = json.loads(Path(f).read_text())
    return dict(s["districts"][site], vintage=s["tag"].replace("win_", ""))


def build() -> pd.DataFrame:
    rows = []
    for site, (country, tag) in SITES.items():
        epw = glob.glob(str(EVID / f"{site}_{tag}" / "weather" / "*.epw"))[0]
        header, t = read_epw(Path(epw))
        e = eui_row(site)
        rows.append(dict(
            site=site, country=country, epw_file=Path(epw).name, epw_location=header, hours=len(t),
            mean_dry_bulb_c=round(float(t.mean()), 3), hdd18_c_days=round(heating_degree_days(t), 2),
            homes_in_result=e["homes_with_result"], floor_area_m2=e["floor_area_m2"],
            heating_eui_kwh_m2=e["eui_heating_kwh_m2"],
            heating_kwh_m2_per_hdd=round(e["eui_heating_kwh_m2"] / heating_degree_days(t), 5),
            internal_only=site in INTERNAL_ONLY, vintage=e["vintage"]))
    return pd.DataFrame(rows)


def figure(df: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pub = df[~df["internal_only"]]
    fig, ax = plt.subplots(figsize=(7.5, 5.5), constrained_layout=True)
    ax.scatter(pub["hdd18_c_days"], pub["heating_eui_kwh_m2"], s=pub["homes_in_result"] / 6, color="#0072B2",
               alpha=0.8, edgecolor="black", linewidth=0.5)
    for r in pub.itertuples():
        ax.annotate(r.site.split("-")[1], (r.hdd18_c_days, r.heating_eui_kwh_m2), xytext=(6, 4),
                    textcoords="offset points", fontsize=9)
    rho = pub["hdd18_c_days"].corr(pub["heating_eui_kwh_m2"], method="spearman")
    ax.set_xlabel("Heating degree days, base 18 C (from each district's own weather file)")
    ax.set_ylabel("Pooled heating EUI (kWh/m2, correctly divided homes)")
    ax.set_title(f"Heating demand against climate, {len(pub)} districts (Spearman rho {rho:.2f}); "
                 "marker size = homes", fontsize=10)
    ax.grid(alpha=0.3)
    fig.savefig(OUT_PNG, dpi=150)
    plt.close(fig)


def main() -> None:
    df = build()
    df.to_csv(OUT_CSV, index=False)
    figure(df)
    print(df[["site", "epw_file", "hdd18_c_days", "heating_eui_kwh_m2", "homes_in_result"]].to_string(index=False))
    print("rows", len(df))


if __name__ == "__main__":
    main()
