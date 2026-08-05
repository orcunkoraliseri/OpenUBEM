"""Post-process the four existing layout_assign 3D viewer HTML files so they
render a basemap + real-building attributes instead of flat NO_DATA_GREY
blocks. Pure post-processing of already-generated HTML -- does not touch the
generating pipeline (openubem/), does not re-run EnergyPlus, does not run
export_viewer() again.

For each target file:
  1. Archives the pre-edit original to figures/before_viewer_enrich/<name>.
  2. Transplants the donor's `basemap` object into the target payload verbatim
     (same scene-local frame -- verified identical
     cityjson.metadata["+common_origin_utm"] between target and donor).
  3. Joins levels / height_m / footprint_area_m2 from the donor's matching
     CityObject (by exact key) into the target's attributes -- these are the
     REAL building's values, not a description of the substituted prototype
     that is actually drawn.
  4. Computes rendered_height_m per target CityObject from its own geometry
     (max(z) - min(z) over every vertex index reachable from
     geometry[*].boundaries, in the file's declared transform) -- this is
     what is actually drawn.
  5. Patches `this.mode = "eui";` -> `this.mode = "archetype";` and inserts
     "rendered_height_m", into DETAIL_FIELDS (each must match exactly once).
  6. Inserts a fixed-position caption banner so a reader cannot misread the
     scene as ground truth.
  7. Writes the file back in place, UTF-8, CRLF preserved byte-for-byte
     everywhere except the touched spans.

Run with ./.venv/Scripts/python.exe -- see plan doc PLAN_storey-matching_implementation.md,
E-LA-34 remediation.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
FIG_DIR = (
    REPO / "docs" / "docs_ACTIVE" / "simulation-Resolution" / "layoutAssigner"
    / "debug" / "storey-Matching" / "figures"
)
ARCHIVE_DIR = FIG_DIR / "before_viewer_enrich"

PAIRS = [
    ("nyc_suburban_layout_assign_viewer.html", "nyc_suburban_real_auto_viewer.html"),
    ("nyc_suburban_layout_assign_pre_B05_pipeline_viewer.html", "nyc_suburban_real_auto_viewer.html"),
    ("la_suburban_layout_assign_viewer.html", "la_suburban_real_auto_viewer.html"),
    ("la_suburban_layout_assign_pre_B05_pipeline_viewer.html", "la_suburban_real_auto_viewer.html"),
]

SCENE_PREFIX = '<script id="scene-data"'
JOIN_FIELDS = ("levels", "height_m", "footprint_area_m2")

MODE_OLD = 'this.mode = "eui";'
MODE_NEW = 'this.mode = "archetype";'
DETAIL_OLD = '    "height_m",'
DETAIL_NEW = '    "height_m",\n    "rendered_height_m",'

VIEWER_ANCHOR = '<div id="ubem-viewer"></div>'
CAPTION_HTML = (
    '<div class="ubem-caveat" style="position:absolute; bottom:12px; right:12px; '
    'width:280px; background: rgba(18, 24, 38, 0.92); border: 1px solid #2a3345; '
    'border-radius: 8px; padding: 10px 12px; font-size: 11px; line-height: 1.4; '
    'backdrop-filter: blur(4px); box-shadow: 0 4px 18px rgba(0,0,0,0.4); z-index: 10; '
    'color: #e8ecf2; font-family: -apple-system, \'Segoe UI\', Roboto, sans-serif;">'
    '<div style="font-weight:600; font-size:12px; margin-bottom:6px; '
    'border-bottom:1px solid #2a3345; padding-bottom:4px;">Reading this scene</div>'
    '<ul style="margin:0; padding-left:16px;">'
    '<li>Massing is a substituted DOE prototype, not the real building footprint.</li>'
    '<li>Rendered height is prototype-native and does NOT follow the real storey count '
    '(E-LA-33). <code>levels</code> / <code>height_m</code> in the detail panel are the '
    "REAL building's values; <code>rendered_height_m</code> is what is drawn.</li>"
    '<li>No simulation results are joined to this scene — colouring is by archetype, '
    'not EUI.</li>'
    '</ul></div>'
)


def find_scene_line(lines: list[str], label: str) -> int:
    idxs = [i for i, l in enumerate(lines) if l.startswith(SCENE_PREFIX)]
    if len(idxs) != 1:
        raise RuntimeError(f"{label}: expected exactly 1 scene-data line, found {len(idxs)}")
    return idxs[0]


def extract_payload(line: str, label: str) -> tuple[str, int, int]:
    gt = line.find(">")
    if gt == -1:
        raise RuntimeError(f"{label}: no '>' found after scene-data prefix")
    if line.count("</script>") != 1:
        raise RuntimeError(f"{label}: expected exactly 1 </script> on scene-data line, found {line.count('</script>')}")
    end = line.rfind("</script>")
    return line[gt + 1:end], gt, end


def collect_vertex_indices(geometry: list) -> set[int]:
    idxs: set[int] = set()

    def walk(node):
        if isinstance(node, list):
            if node and all(isinstance(x, int) for x in node):
                idxs.update(node)
            else:
                for x in node:
                    walk(x)

    for geom in geometry:
        walk(geom.get("boundaries", []))
    return idxs


def load_payload(path: Path, label: str) -> tuple[list[str], int, dict]:
    text = path.read_bytes().decode("utf-8")
    lines = text.splitlines(keepends=True)
    idx = find_scene_line(lines, label)
    payload_str, _gt, _end = extract_payload(lines[idx], label)
    data = json.loads(payload_str)
    return lines, idx, data


def replace_exactly_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected literal {old!r} exactly once, found {n}")
    return text.replace(old, new, 1)


def process_pair(target_name: str, donor_name: str, height_by_archetype: dict) -> dict:
    target_path = FIG_DIR / target_name
    donor_path = FIG_DIR / donor_name

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / target_name
    original_bytes = target_path.read_bytes()
    if not archive_path.exists():
        archive_path.write_bytes(original_bytes)
    archive_ok = archive_path.read_bytes() == original_bytes

    target_lines, t_idx, target_data = load_payload(target_path, target_name)
    _donor_lines, _d_idx, donor_data = load_payload(donor_path, donor_name)

    target_origin = target_data["cityjson"]["metadata"].get("+common_origin_utm")
    donor_origin = donor_data["cityjson"]["metadata"].get("+common_origin_utm")
    if target_origin != donor_origin:
        raise RuntimeError(
            f"{target_name}: common_origin_utm mismatch target={target_origin} donor={donor_origin}"
        )

    n_cityobjects_before = len(target_data["cityjson"]["CityObjects"])

    # Step 2: transplant basemap verbatim
    target_data["basemap"] = donor_data["basemap"]
    donor_image_len = len(donor_data["basemap"]["image"])

    # Steps 3+4: join real attributes + compute rendered_height_m
    target_cos = target_data["cityjson"]["CityObjects"]
    donor_cos = donor_data["cityjson"]["CityObjects"]
    vertices = target_data["cityjson"]["vertices"]
    scale_z = target_data["cityjson"]["transform"]["scale"][2]
    translate_z = target_data["cityjson"]["transform"]["translate"][2]

    n_joined = 0
    n_rendered = 0
    for key, co in target_cos.items():
        donor_co = donor_cos.get(key)
        if donor_co is not None:
            donor_attrs = donor_co["attributes"]
            if all(f in donor_attrs for f in JOIN_FIELDS):
                for f in JOIN_FIELDS:
                    co["attributes"][f] = donor_attrs[f]
                n_joined += 1

        idxs = collect_vertex_indices(co.get("geometry", []))
        if idxs:
            zs = [vertices[i][2] * scale_z + translate_z for i in idxs]
            rh = round(max(zs) - min(zs), 2)
            co["attributes"]["rendered_height_m"] = rh
            n_rendered += 1
            arche = co["attributes"].get("archetype_id")
            if arche in ("MidriseApartment", "SmallOffice"):
                height_by_archetype.setdefault(arche, set()).add(rh)

    # Re-serialize the scene-data line
    new_payload_str = json.dumps(target_data, ensure_ascii=False, separators=(",", ":"))
    line = target_lines[t_idx]
    gt = line.find(">")
    end = line.rfind("</script>")
    target_lines[t_idx] = line[: gt + 1] + new_payload_str + line[end:]

    text = "".join(target_lines)

    # Step 5: patch the two JS literals
    text = replace_exactly_once(text, MODE_OLD, MODE_NEW, target_name)
    text = replace_exactly_once(text, DETAIL_OLD, DETAIL_NEW, target_name)

    # Step 6: caption banner
    if text.count(VIEWER_ANCHOR) != 1:
        raise RuntimeError(f"{target_name}: expected viewer anchor exactly once, found {text.count(VIEWER_ANCHOR)}")
    text = text.replace(VIEWER_ANCHOR, VIEWER_ANCHOR + CAPTION_HTML, 1)

    # Step 7: write back in place
    target_path.write_bytes(text.encode("utf-8"))

    # Re-parse to verify
    reread_lines = target_path.read_bytes().decode("utf-8").splitlines(keepends=True)
    r_idx = find_scene_line(reread_lines, target_name)
    r_payload_str, _g, _e = extract_payload(reread_lines[r_idx], target_name)
    reparsed = json.loads(r_payload_str)
    n_cityobjects_after = len(reparsed["cityjson"]["CityObjects"])
    reparse_ok = n_cityobjects_after == n_cityobjects_before
    basemap_ok = "basemap" in reparsed and len(reparsed["basemap"]["image"]) == donor_image_len

    return {
        "target": target_name,
        "donor": donor_name,
        "archive_ok": archive_ok,
        "n_cityobjects_before": n_cityobjects_before,
        "n_cityobjects_after": n_cityobjects_after,
        "reparse_ok": reparse_ok,
        "basemap_ok": basemap_ok,
        "donor_image_len": donor_image_len,
        "n_joined": n_joined,
        "n_rendered": n_rendered,
    }


def main():
    height_by_archetype: dict = {}
    results = []
    for target_name, donor_name in PAIRS:
        print(f"=== {target_name} <- {donor_name} ===")
        rec = process_pair(target_name, donor_name, height_by_archetype)
        for k, v in rec.items():
            print(f"  {k}: {v}")
        results.append(rec)

    print("\n=== rendered_height_m by archetype (across all 4 files) ===")
    for arche in ("MidriseApartment", "SmallOffice"):
        vals = sorted(height_by_archetype.get(arche, set()))
        print(f"  {arche}: {vals}")

    all_ok = all(
        r["archive_ok"] and r["reparse_ok"] and r["basemap_ok"]
        and r["n_cityobjects_before"] == r["n_cityobjects_after"]
        for r in results
    )
    print(f"\nALL_OK: {all_ok}")


if __name__ == "__main__":
    main()
