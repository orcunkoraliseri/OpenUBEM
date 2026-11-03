"""Derive per-census-division end-use fractions from CBECS-2018 microdata.

DD1: reuse %TEMP%/cbecs_2018_raw/cbecs2018_final_public.csv.
DD2: divisions 2=middle_atlantic, 9=pacific, 7=west_south_central.
DD3: FINALWT-weighted MF end-use BTU columns -> 9 V16 fraction keys (CBECS modeled_frac).
DD3b (CP-1 RULING, ratio-tilt): use CBECS for cross-region RELATIVE deviation only,
     anchored on the validated national table4 level (cancels the CBECS "Other"-allocation
     level artifact). r_factor = mf_cb_reg/mf_cb_nat; mf_adj = clamp(mf_t4 * r_factor);
     rebuild 9 fracs from table4 national set scaled to hit mf_adj.
DD4: PBA->group via cbecs_pba_map.json + archetype_map inversion.
DD5: multifamily/data-center/null-PBA groups keep national fractions.
DD6: thin-cell (n < 25) falls back to national.
DD8: output enduse_fractions_regional.json with national block verbatim.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

_CBECS_CSV = Path(tempfile.gettempdir()) / "cbecs_2018_raw" / "cbecs2018_final_public.csv"
_CBECS_URL = (
    "https://www.eia.gov/consumption/commercial/data/2018/xls/cbecs2018_final_public.csv"
)
_TABLE4_JSON = ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_table4.json"
_PBA_MAP_JSON = ROOT / "openubem" / "data" / "cbecs_pba_map.json"
_OUT_JSON = ROOT / "openubem" / "data" / "service_loads" / "enduse_fractions_regional.json"

# DD2
_DIVISIONS = {2: "middle_atlantic", 9: "pacific", 7: "west_south_central"}

# DD3: MF column -> V16 fraction key groupings
_MF_COL_MAP = {
    "space_heat":    ["MFHTBTU"],
    "space_cool":    ["MFCLBTU"],
    "vent_fans":     ["MFVNBTU"],
    "swh_dhw":       ["MFWTBTU"],
    "lighting":      ["MFLTBTU"],
    "equip_plug":    ["MFOFBTU", "MFPCBTU"],
    "refrig":        ["MFRFBTU"],
    "cooking_other": ["MFCKBTU", "MFOTBTU"],
    "pumps":         [],  # no separate CBECS column; DD3 folds into cooking_other
}
_MF_TOTAL_COL = "MFBTU"
_MODELED_FRAC_KEYS = ("space_heat", "space_cool", "lighting", "equip_plug")
_NONMODELED_KEYS = ("vent_fans", "pumps", "swh_dhw", "refrig", "cooking_other")

# DD6
_THIN_CELL_THRESHOLD = 25

# DD3b clamp bounds
_MF_ADJ_LO = 0.30
_MF_ADJ_HI = 0.97


def _ensure_cbecs() -> Path:
    if not _CBECS_CSV.exists():
        import urllib.request
        _CBECS_CSV.parent.mkdir(parents=True, exist_ok=True)
        print(f"Downloading CBECS from {_CBECS_URL} ...")
        urllib.request.urlretrieve(_CBECS_URL, _CBECS_CSV)
    return _CBECS_CSV


def _build_pba_to_group() -> dict[int, list[str]]:
    """Invert cbecs_pba_map.json (archetype->PBA) + archetype_map (archetype->group)."""
    with open(_PBA_MAP_JSON, encoding="utf-8") as fh:
        pba_map = json.load(fh)["pba_map"]
    with open(_TABLE4_JSON, encoding="utf-8") as fh:
        table4 = json.load(fh)
    archetype_map = table4["archetype_map"]

    result: dict[int, set] = {}
    for archetype, pba in pba_map.items():
        if pba is None or pba == "distribution_only":
            continue
        group = archetype_map.get(archetype)
        if group is None:
            continue
        pba_int = int(pba)
        result.setdefault(pba_int, set()).add(group)

    return {pba: sorted(groups) for pba, groups in result.items()}


def _cbecs_modeled_frac(subset: pd.DataFrame) -> "float | None":
    """FINALWT-weighted CBECS modeled_frac (sh+sc+lt+ep) / total over a building slice.

    Returns None on zero/empty total BTU.
    """
    w = subset["FINALWT"].values
    total_btu = (subset[_MF_TOTAL_COL].values * w).sum()
    if total_btu <= 0:
        return None

    modeled_btu = 0.0
    for frac_key in _MODELED_FRAC_KEYS:
        for c in _MF_COL_MAP[frac_key]:
            if c in subset.columns:
                modeled_btu += (subset[c].values * w).sum()
    return float(modeled_btu / total_btu)


def _rebuild_fracs_from_table4(nat_fracs: dict[str, float], mf_adj: float) -> dict[str, float]:
    """DD3b: rebuild 9 fractions from table4 national set scaled to hit mf_adj.

    Scale the 4 modeled fracs by mf_adj/mf_t4 (-> sum to mf_adj); scale the 5
    non-modeled fracs by (1-mf_adj)/(1-mf_t4) (-> sum to 1-mf_adj). Total = 1.0.
    """
    mf_t4 = sum(nat_fracs[k] for k in _MODELED_FRAC_KEYS)
    nonmod_t4 = sum(nat_fracs[k] for k in _NONMODELED_KEYS)

    s_mod = mf_adj / mf_t4
    s_non = (1.0 - mf_adj) / nonmod_t4 if nonmod_t4 > 0 else 0.0

    out: dict[str, float] = {}
    for k in _MODELED_FRAC_KEYS:
        out[k] = nat_fracs[k] * s_mod
    for k in _NONMODELED_KEYS:
        out[k] = nat_fracs[k] * s_non
    return out


def main() -> dict:
    csv_path = _ensure_cbecs()
    print(f"Loading CBECS from {csv_path} ...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} cols.")

    # coerce numeric columns
    num_cols = ["CENDIV", "PBA", "FINALWT", _MF_TOTAL_COL]
    all_mf_cols: list[str] = []
    for cols in _MF_COL_MAP.values():
        all_mf_cols.extend(cols)
    all_mf_cols = list(dict.fromkeys(all_mf_cols))

    for c in num_cols + all_mf_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # clean: drop rows with NaN/zero MFBTU, NaN FINALWT (mirror extract_cbecs_reference)
    bad = df[_MF_TOTAL_COL].isna() | (df[_MF_TOTAL_COL] <= 0) | df["FINALWT"].isna()
    df = df[~bad].copy()
    for c in all_mf_cols:
        if c in df.columns:
            df[c] = df[c].fillna(0.0)
    print(f"  Clean rows after filtering: {len(df)}")

    # load table4 for national fracs (verbatim copy, DD8)
    with open(_TABLE4_JSON, encoding="utf-8") as fh:
        table4 = json.load(fh)
    national_fracs: dict[str, dict[str, float]] = table4["fractions"]

    # build PBA -> [group, ...] mapping (DD4), then invert to group -> [PBA codes]
    pba_to_groups = _build_pba_to_group()
    group_to_pbas: dict[str, list[int]] = {}
    for pba, groups in pba_to_groups.items():
        for g in groups:
            group_to_pbas.setdefault(g, []).append(pba)

    # DD5: residential/data-center groups keep national
    dd5_national_groups = {"mid_rise_apartment"}

    # ── DD3b step 1: CBECS NATIONAL modeled_frac per group (ALL CENDIVs) ────────
    print("\n=== CBECS national modeled_frac per group (all CENDIVs) ===")
    mf_cb_nat: dict[str, float] = {}
    for group, pba_list in sorted(group_to_pbas.items()):
        subset = df[df["PBA"].isin(pba_list)]
        mf = _cbecs_modeled_frac(subset)
        if mf is None:
            continue
        mf_cb_nat[group] = mf
        print(f"  {group}: n={len(subset)}, mf_cb_nat={mf:.4f}")

    # ── DD3b step 2: per region x group ratio-tilt rebuild ──────────────────────
    fractions_by_region: dict[str, dict[str, dict[str, float]]] = {}
    thin_fallbacks: list[str] = []
    # diagnostics captured for memo / guard
    diag: dict[str, dict[str, dict]] = {}  # region -> group -> {n, mf_cb_reg, r_factor, mf_adj, mf_t4, fallback}

    for cendiv, div_name in _DIVISIONS.items():
        print(f"\n=== Division {cendiv} ({div_name}) ===")
        df_div = df[df["CENDIV"] == cendiv].copy()
        print(f"  Division rows: {len(df_div)}")

        div_fracs: dict[str, dict[str, float]] = {}
        diag[div_name] = {}

        for group, nat_frac_dict in national_fracs.items():
            mf_t4 = sum(nat_frac_dict[k] for k in _MODELED_FRAC_KEYS)

            if group in dd5_national_groups:
                continue  # DD5: no regional split; national path handles it

            pba_list = group_to_pbas.get(group)
            if not pba_list:
                thin_fallbacks.append(f"{div_name}x{group}: no PBA mapping -> national (r_factor=1)")
                diag[div_name][group] = {
                    "n": 0, "mf_cb_reg": None, "r_factor": 1.0,
                    "mf_adj": mf_t4, "mf_t4": mf_t4, "fallback": "no_pba_mapping",
                }
                continue

            subset = df_div[df_div["PBA"].isin(pba_list)]
            n_rows = len(subset)

            # DD6 thin-cell -> national (equivalently r_factor=1, mf_adj=mf_t4)
            if n_rows < _THIN_CELL_THRESHOLD:
                msg = f"{div_name}x{group}: n={n_rows} < {_THIN_CELL_THRESHOLD} -> national (r_factor=1)"
                thin_fallbacks.append(msg)
                print(f"  THIN: {msg}")
                diag[div_name][group] = {
                    "n": n_rows, "mf_cb_reg": None, "r_factor": 1.0,
                    "mf_adj": mf_t4, "mf_t4": mf_t4, "fallback": "thin_cell",
                }
                # national: do not write a regional override (national path applies)
                continue

            mf_cb_reg = _cbecs_modeled_frac(subset)
            mf_cb_n = mf_cb_nat.get(group)
            if mf_cb_reg is None or mf_cb_n is None or mf_cb_n <= 0:
                msg = f"{div_name}x{group}: zero/None CBECS mf -> national (r_factor=1)"
                thin_fallbacks.append(msg)
                print(f"  ZEROBTU: {msg}")
                diag[div_name][group] = {
                    "n": n_rows, "mf_cb_reg": mf_cb_reg, "r_factor": 1.0,
                    "mf_adj": mf_t4, "mf_t4": mf_t4, "fallback": "zero_cbecs_mf",
                }
                continue

            r_factor = mf_cb_reg / mf_cb_n
            mf_adj_raw = mf_t4 * r_factor
            mf_adj = min(_MF_ADJ_HI, max(_MF_ADJ_LO, mf_adj_raw))

            rebuilt = _rebuild_fracs_from_table4(nat_frac_dict, mf_adj)
            s = sum(rebuilt.values())
            if abs(s - 1.0) > 1e-6:
                raise AssertionError(
                    f"{div_name}x{group}: rebuilt fracs sum to {s:.8f}, expected 1.0"
                )

            div_fracs[group] = rebuilt
            diag[div_name][group] = {
                "n": n_rows, "mf_cb_reg": mf_cb_reg, "r_factor": r_factor,
                "mf_adj": mf_adj, "mf_adj_raw": mf_adj_raw, "mf_t4": mf_t4,
                "fallback": None,
            }
            print(
                f"  {div_name}|{group}: n={n_rows},"
                f" mf_cb_reg={mf_cb_reg:.4f}, r_factor={r_factor:.4f},"
                f" mf_t4={mf_t4:.4f}, mf_adj={mf_adj:.4f}"
            )

        fractions_by_region[div_name] = div_fracs

    # ── GUARD ASSERTION (DD3b): large_office MA > 0.83 > PAC ─────────────────────
    print("\n=== GUARD ASSERTION (large_office: MA > 0.83 > PAC) ===")
    g = "large_office"
    mf_t4_office = sum(national_fracs[g][k] for k in _MODELED_FRAC_KEYS)
    ma = diag["middle_atlantic"].get(g, {}).get("mf_adj")
    pac = diag["pacific"].get(g, {}).get("mf_adj")
    wsc = diag["west_south_central"].get(g, {}).get("mf_adj")
    print(f"  mf_cb_nat[large_office] = {mf_cb_nat.get(g)}")
    print(f"  mf_t4[large_office]     = {mf_t4_office:.4f}")
    print(f"  mf_adj MA={ma}, PAC={pac}, WSC={wsc}")
    guard_ok = (ma is not None and pac is not None
                and ma > mf_t4_office > pac)
    if guard_ok:
        print(f"  GUARD PASS: MA({ma:.4f}) > {mf_t4_office:.4f} > PAC({pac:.4f})")
    else:
        print(f"  GUARD FAIL: ordering MA({ma}) > {mf_t4_office:.4f} > PAC({pac}) does NOT hold")

    # validate: every region x group regional override sums to 1.0
    print("\n=== Fraction sum validation (regional overrides) ===")
    all_ok = True
    for region, groups in fractions_by_region.items():
        for group, fracs in groups.items():
            s = sum(fracs.values())
            if abs(s - 1.0) > 1e-6:
                print(f"  FAIL {region}|{group}: sum={s:.8f}")
                all_ok = False
    if all_ok:
        print("  All regional override fraction sets sum to 1.0 +/- 1e-6: PASS")

    # build output JSON (DD8)
    out = {
        "fractions": table4["fractions"],
        "archetype_map": table4["archetype_map"],
        "fractions_by_region": fractions_by_region,
    }
    _OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(_OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nWritten: {_OUT_JSON}")

    if thin_fallbacks:
        print("\nThin-cell / no-mapping fallbacks:")
        for msg in thin_fallbacks:
            print(f"  {msg}")

    # modeled_frac summary per region x group (regional override only)
    print("\n=== regional mf_adj summary (overrides only) ===")
    print(f"{'region':<22} {'group':<25} {'mf_adj':>8} {'mf_t4':>8} {'r_factor':>9}")
    for region, groups in fractions_by_region.items():
        for group in sorted(groups.keys()):
            d = diag[region][group]
            print(f"{region:<22} {group:<25} {d['mf_adj']:>8.4f} {d['mf_t4']:>8.4f} {d['r_factor']:>9.4f}")

    return {
        "mf_cb_nat": mf_cb_nat,
        "diag": diag,
        "fractions_by_region": fractions_by_region,
        "guard_ok": guard_ok,
        "thin_fallbacks": thin_fallbacks,
        "all_sums_ok": all_ok,
    }


if __name__ == "__main__":
    main()
