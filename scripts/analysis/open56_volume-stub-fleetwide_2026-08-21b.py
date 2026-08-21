import re
import csv
from pathlib import Path

ROOT = Path("evidence/open48_refleet4")
CELLS = ["austin", "la", "nyc"]
SUBS = ["centre", "rural", "suburban", "urban"]

HEADER_PREFIX = "! <Zone Information>,"
ZONE_LABEL = " Zone Information,"

zone_out = Path("openubem/outputs/comparisons/open56_volume-stub-zones_2026-08-21b.csv")
bldg_out = Path("openubem/outputs/comparisons/open56_volume-stub-buildings_2026-08-21b.csv")

PART_RE = re.compile(r"_part\d+$", re.IGNORECASE)


def stem_to_osm_id(stem: str):
    m = PART_RE.search(stem)
    has_part = bool(m)
    base = stem[: m.start()] if m else stem
    osm_id = base.replace("_", "/", 1)
    return osm_id, has_part


def parse_header_fields(line: str):
    return [f.strip() for f in line.rstrip("\n").split(",")]


zone_rows = []
n_files = 0
n_files_with_header = 0
n_zones_total = 0
n_zones_stub = 0

bldg_records = {}

sim_dirs = []
for city in CELLS:
    for sub in SUBS:
        cell = f"{city}_{sub}"
        sim_out = ROOT / cell / "sim_out"
        if not sim_out.is_dir():
            continue
        for d in sorted(sim_out.iterdir()):
            if d.is_dir():
                sim_dirs.append((cell, d))

for cell, d in sim_dirs:
    eio = d / "eplusout.eio"
    if not eio.is_file():
        continue
    n_files += 1
    stem = d.name
    osm_id, has_part = stem_to_osm_id(stem)

    header_fields = None
    zi_idx = None
    vol_idx = fa_idx = ch_idx = mult_idx = minz_idx = maxz_idx = None

    try:
        text = eio.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue

    lines = text.splitlines()
    for line in lines:
        if line.startswith(HEADER_PREFIX):
            header_fields = parse_header_fields(line)
            zi_idx = header_fields.index("Zone Name")
            vol_idx = header_fields.index("Volume {m3}")
            fa_idx = header_fields.index("Floor Area {m2}")
            ch_idx = header_fields.index("Ceiling Height {m}")
            mult_idx = header_fields.index("Zone Multiplier")
            minz_idx = header_fields.index("Minimum Z {m}")
            maxz_idx = header_fields.index("Maximum Z {m}")
            break

    if header_fields is None:
        continue
    n_files_with_header += 1

    b_n_zones = 0
    b_n_stub = 0
    b_vol_built = 0.0
    b_vol_expected = 0.0

    for line in lines:
        if not line.startswith(ZONE_LABEL):
            continue
        parts = [p.strip() for p in line.rstrip("\n").split(",")]
        try:
            zone_name = parts[zi_idx]
            volume = float(parts[vol_idx])
            floor_area = float(parts[fa_idx])
            ceiling_height = float(parts[ch_idx])
            zone_mult = float(parts[mult_idx])
            min_z = float(parts[minz_idx])
            max_z = float(parts[maxz_idx])
        except (IndexError, ValueError):
            continue

        expected_volume = floor_area * ceiling_height
        volume_ratio = volume / expected_volume if expected_volume != 0 else None
        is_stub = abs(volume - 10.0) < 1e-9

        n_zones_total += 1
        b_n_zones += 1
        if is_stub:
            n_zones_stub += 1
            b_n_stub += 1

        b_vol_built += volume
        b_vol_expected += expected_volume

        zone_rows.append([
            cell, stem, osm_id, has_part, zone_name,
            volume, floor_area, ceiling_height, zone_mult,
            min_z, max_z, expected_volume,
            f"{volume_ratio:.6f}" if volume_ratio is not None else "",
            is_stub,
        ])

    rec = bldg_records.setdefault(osm_id, {
        "cells": set(), "stems": [], "n_zones": 0, "n_stub": 0,
        "vol_built": 0.0, "vol_expected": 0.0,
    })
    rec["cells"].add(cell)
    rec["stems"].append(stem)
    rec["n_zones"] += b_n_zones
    rec["n_stub"] += b_n_stub
    rec["vol_built"] += b_vol_built
    rec["vol_expected"] += b_vol_expected

zone_out.parent.mkdir(parents=True, exist_ok=True)
with zone_out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "cell", "stem", "osm_id", "has_part", "zone_name",
        "volume", "floor_area", "ceiling_height", "zone_multiplier",
        "min_z", "max_z", "expected_volume", "volume_ratio", "is_stub",
    ])
    w.writerows(zone_rows)

n_bldg_all_stub = 0
n_bldg_some_stub = 0
n_bldg_no_stub = 0
with bldg_out.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "osm_id", "cells", "n_stems", "n_zones", "n_stub_zones",
        "frac_stub", "all_stubbed", "vol_built", "vol_expected", "vol_ratio",
    ])
    for osm_id, rec in sorted(bldg_records.items()):
        n_zones = rec["n_zones"]
        n_stub = rec["n_stub"]
        frac_stub = (n_stub / n_zones) if n_zones else None
        all_stub = (n_zones > 0 and n_stub == n_zones)
        vol_ratio = (rec["vol_built"] / rec["vol_expected"]) if rec["vol_expected"] else None
        if all_stub:
            n_bldg_all_stub += 1
        elif n_stub > 0:
            n_bldg_some_stub += 1
        else:
            n_bldg_no_stub += 1
        w.writerow([
            osm_id, "|".join(sorted(rec["cells"])), len(rec["stems"]), n_zones, n_stub,
            f"{frac_stub:.6f}" if frac_stub is not None else "",
            all_stub,
            f"{rec['vol_built']:.4f}", f"{rec['vol_expected']:.4f}",
            f"{vol_ratio:.6f}" if vol_ratio is not None else "",
        ])

ratio_values = []
for row in zone_rows:
    vr = row[12]
    if vr != "":
        ratio_values.append(float(vr))
ratio_values.sort()

def pct(vals, p):
    if not vals:
        return None
    k = (len(vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(vals) - 1)
    if f == c:
        return vals[f]
    return vals[f] + (vals[c] - vals[f]) * (k - f)

total_vol_built = sum(r["vol_built"] for r in bldg_records.values())
total_vol_expected = sum(r["vol_expected"] for r in bldg_records.values())
fleet_ratio = total_vol_built / total_vol_expected if total_vol_expected else None

n_buildings = len(bldg_records)
n_parts = sum(1 for r in bldg_records.values() if len(r["stems"]) > 1)

print("=== T02 summary ===")
print(f"sim_out dirs found: {len(sim_dirs)}")
print(f"eio files present: {n_files}")
print(f"eio files with Zone Information header: {n_files_with_header}")
print(f"total zones parsed: {n_zones_total}")
print(f"zones with volume == 10.0 (stub): {n_zones_stub} / {n_zones_total} = {n_zones_stub/n_zones_total:.4%}" if n_zones_total else "no zones")
print(f"distinct buildings (osm_id): {n_buildings}")
print(f"buildings composed of >1 sim dir (parts): {n_parts}")
print(f"buildings with ALL zones stubbed: {n_bldg_all_stub} / {n_buildings} = {n_bldg_all_stub/n_buildings:.4%}")
print(f"buildings with SOME (not all) zones stubbed: {n_bldg_some_stub} / {n_buildings}")
print(f"buildings with NO stubbed zones: {n_bldg_no_stub} / {n_buildings}")
print(f"fleet volume as-built (sum): {total_vol_built:.2f} m3")
print(f"fleet volume as-expected (floor_area x ceiling_height, sum): {total_vol_expected:.2f} m3")
print(f"fleet volume ratio (built/expected): {fleet_ratio:.6f}" if fleet_ratio is not None else "n/a")
print(f"per-zone volume_ratio distribution (n={len(ratio_values)}): "
      f"min={ratio_values[0]:.4f} p10={pct(ratio_values,0.10):.4f} "
      f"p25={pct(ratio_values,0.25):.4f} median={pct(ratio_values,0.50):.4f} "
      f"p75={pct(ratio_values,0.75):.4f} p90={pct(ratio_values,0.90):.4f} "
      f"max={ratio_values[-1]:.4f}" if ratio_values else "no ratio values")
print(f"wrote zone csv: {zone_out} ({len(zone_rows)} rows)")
print(f"wrote building csv: {bldg_out} ({n_buildings} rows)")
