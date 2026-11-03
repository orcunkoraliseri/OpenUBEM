"""OPEN-03 / T03 (PLAN_five-items-2026-08-20-late.md) -- envelope decomposition.

Reads BUILDINGSURFACE:DETAILED / FENESTRATIONSURFACE:DETAILED vertex lists directly out of the
IDF text (stdlib only, no eppy) for the 48 layout_assign sample buildings and their paired
production (`auto`) IDFs, and reports gross exterior wall area, roof area, ground-contact area,
window area, WWR, exterior-surface-per-floor-area, storey count and total floor area, per
building, both arms. No simulation is run.

Bucket definitions (stated once here, restated in the report):
  - exterior wall  : Surface Type "wall",  Outside Boundary Condition "outdoors"
  - roof           : Surface Type "roof",  Outside Boundary Condition "outdoors"
  - ground-contact : Surface Type "floor", OBC in {"ground","groundfcfactormethod"}
                      + Surface Type "wall", OBC "groundfcfactormethod" (below-grade wall)
  - window         : FenestrationSurface:Detailed area (x Multiplier)
                      + BuildingSurface:Detailed Surface Type "window", OBC in
                        {"outdoors","groundfcfactormethod"} (rare, both arms; interior
                        "window" objects with OBC "surface"/"zone" are excluded, diagnostic only)
  - floor_total    : Surface Type "floor", any OBC, restricted to zones whose ZONE object field
                      "Part of Total Floor Area" is not "No" (each physical floor plate is one
                      "floor" object; its "ceiling" counterpart in the zone below is not summed,
                      which would double count) -- see note below on why the zone filter is
                      necessary
  - exposed floor  : Surface Type "floor", OBC "outdoors" -- tracked as a diagnostic column,
                      NOT folded into "ground-contact" (it is not touching the ground) and NOT
                      folded into "exterior surface area" (task defines that as wall+roof+ground)
  - door           : Surface Type "door" -- tracked as a diagnostic column only, not requested
  - exterior surface area = ext_wall + roof + ground_contact  (windows sit inside the wall
    footprint in this IDF style -- confirmed: wall polygons are not punched out for windows --
    so they are not added again). This is the full envelope, unrestricted by zone conditioning
    status -- an Attic's roof/gable walls are still part of the physical building envelope.
  - storey count   : distinct min-Z elevations (rounded to 0.1 m) among Surface Type "wall"
    objects belonging to zones with "Part of Total Floor Area" != "No" -- z-elevation bands are
    the only geometry-only signal present in both arms for every building; the same zone filter
    as floor_total keeps this to occupied storeys, not attic/plenum bands
  - storey_count_floor (OPEN-62 T06, ruling R7) : distinct origin-corrected min-Z elevations among
    ALL Surface Type "floor" objects, UNFILTERED by zone -- counts floors directly instead of "the
    elevations at which a new exterior wall starts", which C9b showed undercounts any building
    whose facade spans multiple floors (TallBuilding: wall-base method reads 11, floor-surface
    reads 20 -- matching CP-2's "Floor surfaces (the independent reader)" measurement, which R7
    itself defines with no zone filter). storey_count_floor_zonefiltered (same but restricted to
    zones with "Part of Total Floor Area" != "No", the wall path's own filter) is also returned by
    parse_idf() for comparison but is NOT written to any CSV -- on TallBuilding it collapses to 11
    (== storey_count) because a zone's floor sits at the same elevation as that zone's own walls,
    and the filter excludes 9 of the file's 20 distinct Z levels entirely (155/164 zones are
    floor-area-counting but concentrate on only 11 Z_Origin values) -- so it is not a substitute
    for storey_count_floor, only a diagnostic. See the T06 report for both numbers.

NOTE -- found during development, corrected here, not left as a silent wrong number: 26 of the
48 layout_assign sample IDFs carry an unconditioned "Attic" zone (a DOE small-office/-residential
prototype-template artifact); 0 of the 48 paired auto IDFs do. The Attic zone's own "floor"
surface (Surface Type floor, OBC Surface) sits at the same elevation as the conditioned zones'
ceiling below it and is a second surface object for a plane already spoken for -- summing it
into floor_total silently doubled (or worse) that building's floor area. Every ZONE object in
both corpora carries "Part of Total Floor Area" (Yes/No), which is the IDF's own signal for
this and is used here instead of a name-matched "Attic" heuristic.

C7 (floor-area agreement, +/-2%) and C8 (does the carried 44% reproduce) are evaluated here and
printed; per-cell medians are printed, never pooled.
"""
import csv
import os
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_ROOT = os.path.join(REPO, "scratchpad", "open03-untrimmed-sample")
AUTO_ROOT = os.path.join(REPO, "evidence", "open48_refleet4")
OUT_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_envelope_decomposition_zfix.csv")
PRE_FIX_CSV = os.path.join(REPO, "openubem", "outputs", "comparisons", "open03_envelope_decomposition.csv")

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

BLANK_LINE_SPLIT_RE = re.compile(r'\n[ \t]*\r?\n')


def split_blocks(txt):
    return BLANK_LINE_SPLIT_RE.split(txt)


def blocks_of_keyword(blocks, keyword):
    pat = re.compile(r'^\s*' + keyword + r'\s*,', re.IGNORECASE)
    for b in blocks:
        if pat.match(b):
            yield b


FIELD_LINE_RE = re.compile(r'^\s*([^!]*?)\s*[,;]\s*!-\s*(.+?)\s*$')
VERTEX_RE = re.compile(
    r'(-?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*[,;]\s*!-\s*Vertex\s+(\d+)\s+([XYZ])coordinate'
)


def parse_fields(obj_text):
    fields = {}
    for ln in obj_text.split('\n'):
        m = FIELD_LINE_RE.match(ln)
        if m:
            fields[m.group(2).strip()] = m.group(1).strip()
    return fields


def parse_vertices(obj_text):
    verts = {}
    for val, idx, axis in VERTEX_RE.findall(obj_text):
        idx = int(idx)
        verts.setdefault(idx, {})[axis] = float(val)
    ordered = [verts[i] for i in sorted(verts)]
    return [(v.get('X', 0.0), v.get('Y', 0.0), v.get('Z', 0.0)) for v in ordered]


def polygon_area_3d(verts):
    n = len(verts)
    if n < 3:
        return 0.0
    nx = ny = nz = 0.0
    for i in range(n):
        x1, y1, z1 = verts[i]
        x2, y2, z2 = verts[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return 0.5 * (nx ** 2 + ny ** 2 + nz ** 2) ** 0.5


def parse_idf(path):
    txt = open(path, encoding='utf-8', errors='replace').read()
    blocks = split_blocks(txt)

    # OPEN-62 fix (PLAN_open62-z-origin-and-three-rulings-2026-08-20.md T01): mirrors
    # openubem/geometry/layout_assigner.py:465-495 -- read GlobalGeometryRules' Coordinate System
    # and each ZONE's own X/Y/Z Origin, and add the origin back into wall vertices before taking
    # the minimum Z when the file is Relative. Missing-object default (WORLD) copies the reference
    # implementation's own default (layout_assigner.py:445) rather than inventing a second one.
    coord_sys = "WORLD"
    ggr_blocks = list(blocks_of_keyword(blocks, "GLOBALGEOMETRYRULES"))
    if ggr_blocks:
        ggr_fields = parse_fields(ggr_blocks[0])
        coord_sys = ggr_fields.get('Coordinate System', 'World').strip().upper()

    zone_is_floor_area = {}
    zone_origins = {}
    for obj in blocks_of_keyword(blocks, "ZONE"):
        f = parse_fields(obj)
        name = f.get('Name', '')
        flag = f.get('Part of Total Floor Area', 'Yes').strip().lower()
        zone_is_floor_area[name] = (flag != 'no')
        x0 = f.get('X Origin', '').strip()
        y0 = f.get('Y Origin', '').strip()
        z0 = f.get('Z Origin', '').strip()
        zone_origins[name] = (
            float(x0) if x0 not in (None, '') else 0.0,
            float(y0) if y0 not in (None, '') else 0.0,
            float(z0) if z0 not in (None, '') else 0.0,
        )

    ext_wall = roof = ground = window = floor_total = exposed_floor = door = 0.0
    window_interior_diag = 0.0
    wall_z_bases_naive = set()
    wall_z_bases = set()
    floor_z_bases = set()
    floor_z_bases_unfiltered = set()
    attic_zone_count = sum(1 for v in zone_is_floor_area.values() if not v)

    for obj in blocks_of_keyword(blocks, "BUILDINGSURFACE:DETAILED"):
        f = parse_fields(obj)
        st = f.get('Surface Type', '').lower()
        bc = f.get('Outside Boundary Condition', '').lower()
        zone = f.get('Zone Name', '')
        counts_as_floor_area = zone_is_floor_area.get(zone, True)
        verts = parse_vertices(obj)
        area = polygon_area_3d(verts)

        if st == 'wall':
            if counts_as_floor_area:
                zs = [v[2] for v in verts]
                if zs:
                    base_naive = min(zs)
                    wall_z_bases_naive.add(round(base_naive, 1))
                    _, _, oz = zone_origins.get(zone, (0.0, 0.0, 0.0))
                    z0 = oz if coord_sys == "RELATIVE" else 0.0
                    wall_z_bases.add(round(base_naive + z0, 1))
            if bc == 'outdoors':
                ext_wall += area
            elif bc == 'groundfcfactormethod':
                ground += area
        elif st == 'roof':
            if bc == 'outdoors':
                roof += area
        elif st == 'floor':
            if counts_as_floor_area:
                floor_total += area
            if bc in ('ground', 'groundfcfactormethod'):
                ground += area
            elif bc == 'outdoors':
                exposed_floor += area
            # OPEN-62 T06 (ruling R7): a storey is a FLOOR, not the elevation a facade happens to
            # restart at -- C9b showed the wall-base method undercounts any building whose exterior
            # wall spans several floors (TallBuilding: wall-base 10/11, floor-surface 20). Mirror the
            # same origin correction as the wall path; unfiltered set is reported separately per T06's
            # "How" so the zone filter's own contribution is never folded silently into storey_count_floor.
            zs = [v[2] for v in verts]
            if zs:
                fbase_naive = min(zs)
                _, _, foz = zone_origins.get(zone, (0.0, 0.0, 0.0))
                fz0 = foz if coord_sys == "RELATIVE" else 0.0
                fbase_corrected = round(fbase_naive + fz0, 1)
                floor_z_bases_unfiltered.add(fbase_corrected)
                if counts_as_floor_area:
                    floor_z_bases.add(fbase_corrected)
        elif st == 'door':
            door += area
        elif st == 'window':
            if bc in ('outdoors', 'groundfcfactormethod'):
                window += area
            else:
                window_interior_diag += area

    for obj in blocks_of_keyword(blocks, "FENESTRATIONSURFACE:DETAILED"):
        f = parse_fields(obj)
        verts = parse_vertices(obj)
        area = polygon_area_3d(verts)
        try:
            mult = float(f.get('Multiplier', '1').strip() or '1')
        except ValueError:
            mult = 1.0
        window += area * mult

    storey_count = len(wall_z_bases)
    storey_count_naive = len(wall_z_bases_naive)
    # OPEN-62 T06 (ruling R7): the primary storey_count_floor is UNFILTERED by zone
    # ("Count distinct FLOOR-surface elevations, origin-corrected" -- R7's own wording carries no
    # zone filter, and this is the value that reproduces CP-2's "Floor surfaces (the independent
    # reader)" row -- 20 on TallBuilding.idf -- which is what C14's pre-registered targets are).
    # storey_count_floor_zonefiltered mirrors the wall path's counts_as_floor_area filter and is
    # kept separate, reported but not written to any CSV: on TallBuilding it collapses to 11,
    # coinciding with storey_count (11) because a zone's floor and its own walls share one base
    # elevation -- filtering by zone removes 9 whole floor levels (155/164 zones are
    # floor-area-counting, but those 155 concentrate on only 11 of the file's 20 distinct zone
    # Z_Origin values), so it is not a useful proxy for "how many floors this building has" and
    # applying it as the primary value would defeat R7's own reason for switching to floor
    # surfaces. See the T06 report for the measured filtered-vs-unfiltered numbers.
    storey_count_floor = len(floor_z_bases_unfiltered)
    storey_count_floor_zonefiltered = len(floor_z_bases)

    return {
        'ext_wall_m2': ext_wall,
        'roof_m2': roof,
        'ground_m2': ground,
        'window_m2': window,
        'window_interior_diag_m2': window_interior_diag,
        'exposed_floor_m2': exposed_floor,
        'door_m2': door,
        'floor_total_m2': floor_total,
        'storey_count': storey_count,
        'storey_count_naive': storey_count_naive,
        'storey_count_floor': storey_count_floor,
        'storey_count_floor_zonefiltered': storey_count_floor_zonefiltered,
        'attic_zone_count': attic_zone_count,
    }


def find_pairs():
    pairs = []
    missing = []
    for cell in CELLS:
        idf_dir = os.path.join(SAMPLE_ROOT, cell, "step3_layout_assign", "idfs")
        for fn in sorted(os.listdir(idf_dir)):
            osm_id = fn[:-4]
            la_path = os.path.join(idf_dir, fn)
            auto_path = os.path.join(AUTO_ROOT, cell, "fleet_staging", "idfs", fn)
            if os.path.exists(auto_path):
                pairs.append((cell, osm_id, la_path, auto_path))
            else:
                missing.append((cell, osm_id))
    return pairs, missing


def main():
    pairs, missing = find_pairs()
    print(f"[pairing] sample=48 found_pairs={len(pairs)} missing={len(missing)}")
    for cell, osm_id in missing:
        print(f"[pairing][MISSING] {cell} {osm_id}")

    rows = []
    per_building = {}
    for cell, osm_id, la_path, auto_path in pairs:
        la = parse_idf(la_path)
        auto = parse_idf(auto_path)
        for arm, d, path in (('layout_assign', la, la_path), ('auto', auto, auto_path)):
            wwr = (d['window_m2'] / d['ext_wall_m2'] * 100.0) if d['ext_wall_m2'] > 0 else float('nan')
            ext_surface = d['ext_wall_m2'] + d['roof_m2'] + d['ground_m2']
            ext_per_floor = (ext_surface / d['floor_total_m2']) if d['floor_total_m2'] > 0 else float('nan')
            rows.append({
                'cell': cell, 'osm_id': osm_id, 'arm': arm,
                'ext_wall_m2': round(d['ext_wall_m2'], 3),
                'roof_m2': round(d['roof_m2'], 3),
                'ground_m2': round(d['ground_m2'], 3),
                'window_m2': round(d['window_m2'], 3),
                'wwr_pct': round(wwr, 3) if wwr == wwr else '',
                'ext_surface_m2': round(ext_surface, 3),
                'floor_total_m2': round(d['floor_total_m2'], 3),
                'ext_surface_per_floor_area': round(ext_per_floor, 5) if ext_per_floor == ext_per_floor else '',
                'storey_count': d['storey_count'],
                'storey_count_naive': d['storey_count_naive'],
                'exposed_floor_m2_diag': round(d['exposed_floor_m2'], 3),
                'door_m2_diag': round(d['door_m2'], 3),
                'window_interior_diag_m2': round(d['window_interior_diag_m2'], 3),
                'unconditioned_zone_count_diag': d['attic_zone_count'],
            })
        per_building[(cell, osm_id)] = {'layout_assign': la, 'auto': auto}

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[csv] wrote {len(rows)} rows -> {OUT_CSV}")

    metrics = ['ext_wall_m2', 'roof_m2', 'ground_m2', 'window_m2', 'wwr_pct',
               'ext_surface_per_floor_area', 'storey_count', 'floor_total_m2']

    print("\n[C7] floor-area agreement (+/-2%), per building")
    excluded = []
    kept = []
    for (cell, osm_id), arms in per_building.items():
        fa_la = arms['layout_assign']['floor_total_m2']
        fa_auto = arms['auto']['floor_total_m2']
        if fa_auto == 0:
            pct = float('inf')
        else:
            pct = abs(fa_la - fa_auto) / fa_auto * 100.0
        if pct > 2.0:
            excluded.append((cell, osm_id, fa_la, fa_auto, pct))
        else:
            kept.append((cell, osm_id))
    print(f"[C7] excluded={len(excluded)} kept={len(kept)} of {len(per_building)}")
    for cell, osm_id, fa_la, fa_auto, pct in excluded:
        print(f"[C7][EXCLUDED] {cell} {osm_id} floor_la={fa_la:.2f} floor_auto={fa_auto:.2f} diff_pct={pct:.2f}")

    print("\n[per-cell median ratios layout_assign/auto, C7-kept buildings only]")
    kept_set = set(kept)
    for cell in CELLS:
        cell_ratios = {m: [] for m in metrics}
        n = 0
        for (c, osm_id), arms in per_building.items():
            if c != cell or (c, osm_id) not in kept_set:
                continue
            n += 1
            la = arms['layout_assign']
            auto = arms['auto']
            ext_la = la['ext_wall_m2']
            ext_auto = auto['ext_wall_m2']
            roof_la = la['roof_m2']
            roof_auto = auto['roof_m2']
            ground_la = la['ground_m2']
            ground_auto = auto['ground_m2']
            window_la = la['window_m2']
            window_auto = auto['window_m2']
            wwr_la = (window_la / ext_la * 100.0) if ext_la > 0 else float('nan')
            wwr_auto = (window_auto / ext_auto * 100.0) if ext_auto > 0 else float('nan')
            epf_la = ((ext_la + roof_la + ground_la) / la['floor_total_m2']) if la['floor_total_m2'] > 0 else float('nan')
            epf_auto = ((ext_auto + roof_auto + ground_auto) / auto['floor_total_m2']) if auto['floor_total_m2'] > 0 else float('nan')
            vals = {
                'ext_wall_m2': (ext_la, ext_auto),
                'roof_m2': (roof_la, roof_auto),
                'ground_m2': (ground_la, ground_auto),
                'window_m2': (window_la, window_auto),
                'wwr_pct': (wwr_la, wwr_auto),
                'ext_surface_per_floor_area': (epf_la, epf_auto),
                'storey_count': (la['storey_count'], auto['storey_count']),
                'floor_total_m2': (la['floor_total_m2'], auto['floor_total_m2']),
            }
            for m, (v_la, v_auto) in vals.items():
                if v_auto and v_auto == v_auto and v_la == v_la:
                    cell_ratios[m].append(v_la / v_auto)
        line = f"{cell} (n={n}): "
        parts = []
        for m in metrics:
            vs = cell_ratios[m]
            if vs:
                parts.append(f"{m}={statistics.median(vs):.4f}")
            else:
                parts.append(f"{m}=NA")
        print(line + " ".join(parts))

    print("\n[diagnostic] storey_count and floor_total_m2 ratios, ALL 48 (not C7-gated) -- explains C7 exclusions")
    for cell in CELLS:
        storey_ratios = []
        floor_ratios = []
        n = 0
        for (c, osm_id), arms in per_building.items():
            if c != cell:
                continue
            n += 1
            la = arms['layout_assign']
            auto = arms['auto']
            if auto['storey_count'] > 0:
                storey_ratios.append(la['storey_count'] / auto['storey_count'])
            if auto['floor_total_m2'] > 0:
                floor_ratios.append(la['floor_total_m2'] / auto['floor_total_m2'])
        sr = statistics.median(storey_ratios) if storey_ratios else float('nan')
        fr = statistics.median(floor_ratios) if floor_ratios else float('nan')
        print(f"{cell} (n={n}): storey_count_ratio_median={sr:.4f} floor_total_ratio_median={fr:.4f}")

    print("\n[C8] wall-ratio check against carried 44%")
    print("Carried figure: nyc_centre/265424467 alone, layout_assign 9122 m2 vs auto 16271 m2"
          " (44% less), from MEASUREMENT_open-03_enduse-localisation.md.")


if __name__ == '__main__':
    sys.exit(main())
