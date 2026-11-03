"""OPEN-33 T07(b): sweep live documents for dead docs/ path citations.

Scope (per PLAN_five-item-sweep-2026-08-12.md T07):
  live document set = docs/docs_ACTIVE/, docs/docs_EXPLANATION/, docs/docs_REPORTS/,
  docs/PROJECT_CHECKLIST.md.
  Standing exclusions (never scanned as citing files, and never used as repair targets):
  docs/docs_DONE/, docs/docs_main/, docs/docs_TODO/layoutgenerator/.

Resolution: a candidate path is checked directly against disk first; if that fails, it is
resolved BY FILENAME against an index of every file under docs/ (basename, with any leading
DONE_/DONE- prefix stripped on both sides of the comparison, since two of the four files
renamed by the 2026-08-06 move gained exactly that prefix).

"new_since_2026-08-06" is computed against git commit 9270ac7 (the commit that introduced the
migration-map table into PROJECT_CHECKLIST.md, dated 2026-08-05 21:44 local / documented in the
checklist itself as "added 2026-08-06"): a citing file absent from that commit is wholly new; for
a citing file present then, a cited_path string not found verbatim in that historical revision is
a new citation.
"""
from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_COMMIT = "9270ac7"

LIVE_DIRS = [
    REPO_ROOT / "docs" / "docs_ACTIVE",
    REPO_ROOT / "docs" / "docs_EXPLANATION",
    REPO_ROOT / "docs" / "docs_REPORTS",
]
LIVE_SINGLE_FILES = [
    REPO_ROOT / "docs" / "PROJECT_CHECKLIST.md",
]

BACKTICK_RE = re.compile(r"`([^`\n]+)`")
LINE_REF_RE = re.compile(r":[\d,\-]+$")
EXT_RE = re.compile(r"\.[A-Za-z0-9]{1,6}(?=[\s)\]\"'`,;:]|$)")
STRIP_TRAILING = ")]}'\",;:`"
NON_LITERAL_MARKERS = ("*", "{", "}", "<", ">", "..")


def norm_basename(name: str) -> str:
    n = name
    for _ in range(2):
        low = n.lower()
        if low.startswith("done_") or low.startswith("done-"):
            n = n[5:]
        else:
            break
    return n.lower()


def build_filename_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    docs_root = REPO_ROOT / "docs"
    for p in docs_root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(REPO_ROOT).as_posix()
            key = norm_basename(p.name)
            index.setdefault(key, []).append(rel)
    return index


def _clean_candidate(raw: str) -> str | None:
    raw = raw.split("#", 1)[0]
    raw = LINE_REF_RE.sub("", raw)
    raw = raw.rstrip(STRIP_TRAILING)
    raw = raw.rstrip(".")
    raw = raw.strip()
    if any(marker in raw for marker in NON_LITERAL_MARKERS):
        return None
    last_seg = raw.rsplit("/", 1)[-1]
    if "." not in last_seg:
        return None
    if raw.startswith("docs//"):
        return None
    return raw


def extract_candidates(text: str) -> list[str]:
    out: list[str] = []
    consumed_spans: list[tuple[int, int]] = []
    for m in BACKTICK_RE.finditer(text):
        span_text = m.group(1)
        if "docs/" not in span_text:
            continue
        idx = span_text.find("docs/")
        while idx != -1:
            rest = span_text[idx:]
            next_idx = rest.find("docs/", 1)
            segment = rest if next_idx == -1 else rest[:next_idx]
            candidate = _clean_candidate(segment)
            if candidate:
                out.append(candidate)
            idx = idx + next_idx if next_idx != -1 else -1
        consumed_spans.append(m.span())

    mask = list(text)
    for start, end in consumed_spans:
        for i in range(start, end):
            mask[i] = " "
    remainder = "".join(mask)

    for line in remainder.splitlines():
        idx = line.find("docs/")
        while idx != -1:
            rest = line[idx:]
            next_idx = rest.find("docs/", 1)
            segment = rest if next_idx == -1 else rest[:next_idx]
            ext_matches = list(EXT_RE.finditer(segment))
            if ext_matches:
                segment = segment[: ext_matches[-1].end()]
                candidate = _clean_candidate(segment)
                if candidate:
                    out.append(candidate)
            advance = next_idx if next_idx != -1 else len(rest)
            idx = idx + advance if next_idx != -1 else -1
    return out


def resolve(cited: str, index: dict[str, list[str]]) -> tuple[bool, str, str]:
    direct = REPO_ROOT / cited
    if direct.exists() and direct.is_file():
        return True, "direct", cited
    key = norm_basename(Path(cited).name)
    matches = index.get(key, [])
    if len(matches) == 1:
        return True, "filename", matches[0]
    if len(matches) > 1:
        return True, f"filename(ambiguous:{len(matches)})", matches[0]
    return False, "none", ""


def infer_arc(cited: str, resolved_path: str) -> str:
    p = resolved_path or cited
    parts = p.split("/")
    if len(parts) < 2:
        return "unknown"
    top = parts[1] if parts[0] == "docs" else parts[0]
    if top == "docs_ACTIVE" and len(parts) > 2:
        return parts[2]
    if top == "docs_DONE" and len(parts) > 3:
        return parts[3]
    if top == "docs_DONE" and len(parts) > 2:
        return parts[2]
    if top == "docs_TODO" and len(parts) > 2:
        return parts[2]
    return top


def git_show(rev: str, path: str) -> str | None:
    res = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if res.returncode != 0:
        return None
    return res.stdout


def baseline_file_list(rev: str) -> set[str]:
    res = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", rev],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
        encoding="utf-8",
        errors="replace",
    )
    return set(res.stdout.splitlines())


def is_new_since_baseline(citing_rel: str, cited: str, baseline_files: set[str],
                           cache: dict[str, str | None]) -> bool:
    if citing_rel not in baseline_files:
        return True
    if citing_rel not in cache:
        cache[citing_rel] = git_show(BASELINE_COMMIT, citing_rel)
    hist = cache[citing_rel]
    if hist is None:
        return True
    return cited not in hist


def gather_live_files() -> list[Path]:
    files: list[Path] = []
    for d in LIVE_DIRS:
        files.extend(sorted(d.rglob("*.md")))
    files.extend(LIVE_SINGLE_FILES)
    return files


def main() -> None:
    index = build_filename_index()
    baseline_files = baseline_file_list(BASELINE_COMMIT)
    hist_cache: dict[str, str | None] = {}

    rows = []
    live_files = gather_live_files()
    for f in live_files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        text = f.read_text(encoding="utf-8")
        candidates = sorted(set(extract_candidates(text)))
        for cited in candidates:
            if cited == rel:
                continue
            resolves, via, resolved_path = resolve(cited, index)
            arc = infer_arc(cited, resolved_path)
            new_since = is_new_since_baseline(rel, cited, baseline_files, hist_cache)
            rows.append({
                "citing_file": rel,
                "cited_path": cited,
                "resolves": resolves,
                "resolved_via": via,
                "arc": arc,
                "new_since_2026-08-06": new_since,
            })

    out_path = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open33_dead_path_sweep_2026-08-12.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "citing_file", "cited_path", "resolves", "resolved_via", "arc", "new_since_2026-08-06",
        ])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    total = len(rows)
    dead = [r for r in rows if not r["resolves"]]
    new_dead = [r for r in dead if r["new_since_2026-08-06"]]
    print(f"scanned files: {len(live_files)}")
    print(f"total candidate citations: {total}")
    print(f"dead (unresolved): {len(dead)}")
    print(f"new_since_2026-08-06 among dead: {len(new_dead)}")
    print(f"out: {out_path}")
    for r in dead:
        print(f"  DEAD: {r['citing_file']} -> {r['cited_path']} (arc={r['arc']}, new={r['new_since_2026-08-06']})")


if __name__ == "__main__":
    main()
