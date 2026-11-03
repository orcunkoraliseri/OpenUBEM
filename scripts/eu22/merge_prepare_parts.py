from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
from pathlib import Path

CONCAT_FILES = ("prepared_buildings.csv", "fleet.lst")
DIR_NAMES = ("idfs", "schedules", "weather")
OTHER_FILES = ("excluded_buildings.csv", "summary.json")
SUMMED = "population_prepared"
RECOUNTED = "blocker_exclusions"
CENSUS = "context_height_fallback_census"


class MergeError(Exception):
    pass


def _is_manifest(name: str) -> bool:
    return name.endswith("_manifest.csv")


def _check_part(part: Path) -> None:
    if not part.is_dir():
        raise MergeError(f"part is not a folder: {part}")
    allowed = set(CONCAT_FILES) | set(DIR_NAMES) | set(OTHER_FILES)
    for entry in sorted(part.iterdir()):
        if entry.name in allowed:
            continue
        if entry.is_file() and _is_manifest(entry.name):
            continue
        raise MergeError(f"unexpected entry in {part}: {entry.name}")
    for name in DIR_NAMES + CONCAT_FILES + OTHER_FILES:
        if not (part / name).exists():
            raise MergeError(f"missing {name} in {part}")
    if len([e for e in part.iterdir() if e.is_file() and _is_manifest(e.name)]) != 1:
        raise MergeError(f"expected exactly one *_manifest.csv in {part}")


def _lines(path: Path) -> list[bytes]:
    return path.read_bytes().splitlines(keepends=True)


def _concat(paths: list[Path], dedup: bool) -> bytes:
    header = None
    out: list[bytes] = []
    seen: set[bytes] = set()
    for path in paths:
        lines = _lines(path)
        if not lines:
            continue
        if dedup or path.suffix == ".csv":
            head, body = lines[0], lines[1:]
            if header is None:
                header = head
                out.append(head)
            elif head.rstrip(b"\r\n") != header.rstrip(b"\r\n"):
                raise MergeError(f"header differs in {path}")
        else:
            body = lines
        for line in body:
            if dedup:
                if line in seen:
                    continue
                seen.add(line)
            out.append(line)
    return b"".join(out)


def _concat_plain(paths: list[Path]) -> bytes:
    out: list[bytes] = []
    for path in paths:
        out.extend(_lines(path))
    return b"".join(out)


def _blocker_counts(excluded: bytes) -> dict:
    counts: dict[str, int] = {}
    text = excluded.decode("utf-8")
    if not text.strip():
        return counts
    for row in csv.DictReader(io.StringIO(text, newline="")):
        counts[row["blocker"]] = counts.get(row["blocker"], 0) + 1
    return dict(sorted(counts.items()))


def merge(parts: list[Path], out: Path) -> dict:
    parts = [Path(p) for p in parts]
    out = Path(out)
    if out.exists():
        raise MergeError(f"output already exists: {out}")
    if not parts:
        raise MergeError("no parts given")
    for part in parts:
        _check_part(part)

    for sub in ("idfs", "schedules"):
        seen: dict[str, Path] = {}
        for part in parts:
            for entry in (part / sub).iterdir():
                if entry.name in seen:
                    raise MergeError(f"{sub}/{entry.name} is in two parts: {seen[entry.name]} and {part}")
                seen[entry.name] = part

    weather_ref = None
    for part in parts:
        files = {e.name: e.read_bytes() for e in (part / "weather").iterdir() if e.is_file()}
        if weather_ref is None:
            weather_ref = files
        elif files != weather_ref:
            raise MergeError(f"weather differs in {part}")

    summaries = [json.loads((p / "summary.json").read_text(encoding="utf-8")) for p in parts]
    keys = set().union(*[set(s) for s in summaries])
    for key in sorted(keys - {SUMMED, RECOUNTED, CENSUS}):
        values = [json.dumps(s.get(key, "<absent>"), sort_keys=True) for s in summaries]
        if len(set(values)) != 1:
            raise MergeError(f"summary.json key differs across parts: {key}")

    manifest_names = {[e.name for e in p.iterdir() if e.is_file() and _is_manifest(e.name)][0] for p in parts}
    if len(manifest_names) != 1:
        raise MergeError(f"manifest names differ: {sorted(manifest_names)}")
    manifest_name = manifest_names.pop()

    out.mkdir(parents=True)
    (out / "idfs").mkdir()
    (out / "schedules").mkdir()
    (out / "weather").mkdir()
    for part in parts:
        for sub in ("idfs", "schedules"):
            for entry in (part / sub).iterdir():
                target = out / sub / entry.name
                if entry.is_dir():
                    shutil.copytree(entry, target)
                else:
                    shutil.copy2(entry, target)
    for name in weather_ref:
        (out / "weather" / name).write_bytes(weather_ref[name])

    (out / "prepared_buildings.csv").write_bytes(_concat([p / "prepared_buildings.csv" for p in parts], False))
    (out / manifest_name).write_bytes(_concat([p / manifest_name for p in parts], False))
    (out / "fleet.lst").write_bytes(_concat_plain([p / "fleet.lst" for p in parts]))
    excluded = _concat([p / "excluded_buildings.csv" for p in parts], True)
    (out / "excluded_buildings.csv").write_bytes(excluded)

    merged = {k: summaries[0][k] for k in summaries[0] if k not in (SUMMED, RECOUNTED, CENSUS)}
    merged[SUMMED] = sum(int(s[SUMMED]) for s in summaries)
    if any(CENSUS in s for s in summaries):
        census: dict[str, int] = {}
        for s in summaries:
            for key, value in (s.get(CENSUS) or {}).items():
                census[key] = census.get(key, 0) + int(value)
        merged[CENSUS] = dict(sorted(census.items()))
    merged[RECOUNTED] = _blocker_counts(excluded)
    (out / "summary.json").write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        merged = merge(args.parts, args.out)
    except MergeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"out": str(args.out), "population_prepared": merged[SUMMED]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
