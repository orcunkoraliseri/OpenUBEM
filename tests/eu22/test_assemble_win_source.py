from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pandas as pd

from scripts.eu22 import assemble_win_source as asm

FIX = Path(__file__).parent / "fixtures" / "c05_madrid2"
SITE = "ES-MAD-BERRUGUETE"
TREE = f"{SITE}_dw_2099-01-01"


def _tree(tmp_path: Path) -> Path:
    root = tmp_path / "ev"
    tdir = root / TREE
    shutil.copytree(FIX / "idfs", tdir / "idfs")
    shutil.copy2(FIX / "prepared_buildings.csv", tdir / "prepared_buildings.csv")
    return root


def test_assemble_matches_existing_windows_rows_and_leaves_idfs_alone(tmp_path):
    root = _tree(tmp_path)
    tdir = root / TREE
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tdir / "idfs").glob("*.idf")}
    out = asm.assemble(SITE, TREE, 1, root)
    assert out["errors"] == 0 and out["rows"] == 2 and out["stems"] == 2
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tdir / "idfs").glob("*.idf")}
    assert before == after
    new = pd.read_csv(tdir / "windows.csv", dtype={"stem": str}).set_index("stem")
    old = pd.read_csv(FIX / "windows_expected.csv", dtype={"stem": str}).set_index("stem").loc[new.index]
    assert list(new.columns) == list(old.columns)
    for col in ("outdoor_wall_m2", "window_m2", "share_achieved", "share_target", "walls_with_window", "walls_skipped", "u", "shgc", "zones", "preflight_issues"):
        assert (new[col] - old[col]).abs().max() < 0.01, col
    assert (new["skip_reasons"] == old["skip_reasons"]).all()
    assert new["identity_ok"].all()


def test_dwelling_counts_and_changed_stems(tmp_path):
    root = _tree(tmp_path)
    tdir = root / TREE
    asm.assemble(SITE, TREE, 1, root)
    counts = pd.read_csv(tdir / "dwelling_counts_2099-01-01.csv")
    assert list(counts.columns) == ["building_id", "old_count", "new_count", "dwellings_source"]
    assert (counts["old_count"] == counts["new_count"]).all()
    prepared = pd.read_csv(tdir / "prepared_buildings.csv")
    assert counts["new_count"].tolist() == prepared["dwellings_used"].tolist()
    stems = (tdir / "changed_stems.txt").read_text().split()
    assert stems == sorted(p.stem for p in (tdir / "idfs").glob("*.idf"))


def test_tree_name_guard(tmp_path):
    root = _tree(tmp_path)
    try:
        asm.assemble(SITE, f"{SITE}_win_2026-10-06", 1, root)
    except SystemExit as exc:
        assert "STOP" in str(exc)
    else:
        raise AssertionError("expected SystemExit")
