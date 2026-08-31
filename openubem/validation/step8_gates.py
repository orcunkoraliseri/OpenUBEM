"""Pre-submission Step 8 campaign gates.

This module contains the local contracts for the Step 8 gates.  It can score
fixtures and retained engine artefacts, but it cannot turn fixture success into
an executed European campaign claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from pathlib import Path
from typing import Iterable, Mapping

from openubem.validation.step8_bands import STEP8_GATE_BANDS


PRE_SUBMISSION_GATES = ("G8.0", "G8.8", "G8.9", "G8.14", "G8.16")
HARD_SEVERITY = "hard"


@dataclass(frozen=True)
class PerturbationExpectation:
    """The pre-registered transition expected from one EU-09 mutation."""

    identifier: str
    description: str
    must_fail: tuple[str, ...]
    must_stay_clean: tuple[str, ...]


# This is deliberately a fixture specification, not campaign evidence.  Its
# identifiers and transitions are the twelve rows of MVP Table 17, so a test
# cannot quietly substitute a smaller or more convenient mutation set.
PERTURBATION_MATRIX = (
    PerturbationExpectation("P01", "two scenarios use the same schedule file", ("G8.8",), ("G8.10",)),
    PerturbationExpectation("P02", "schedule changes without clearing cache", ("G8.9",), ("G8.8",)),
    PerturbationExpectation("P03", "request obsolete Gas:Facility meter", ("G8.10", "G8.11"), ()),
    PerturbationExpectation("P04", "zero one end-use meter", ("G8.10",), ("G8.11",)),
    PerturbationExpectation("P05", "People object points at another schedule", ("G8.12.assignment",), ("G8.12.value",)),
    PerturbationExpectation("P06", "Schedule:File interpolation enabled", ("G8.13",), ("G8.12",)),
    PerturbationExpectation("P07", "copy another cell manifest wholesale", ("G8.14",), ("G8.12",)),
    PerturbationExpectation("P08", "country uses a fold that held it in", ("G8.16",), ("G8.12", "G8.14")),
    PerturbationExpectation("P09", "shift modelled profile two hours", ("G8.6",), ("G8.5",)),
    PerturbationExpectation("P10", "scale annual energy by 1.2", ("G8.1", "G8.3"), ("G8.6",)),
    PerturbationExpectation("P11", "use a different geometry floor area", ("G8.7",), ("G8.1",)),
    PerturbationExpectation("P12", "null perturbation", (), ()),
)


@dataclass(frozen=True)
class PerturbationCoverage:
    """Observed against pre-registered fail/clean transitions for one probe."""

    identifier: str
    passed: bool
    missing_failures: tuple[str, ...]
    dirty_clean_gates: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class GateFinding:
    """One hard, auditable pre-submission gate result."""

    gate: str
    passed: bool
    detail: str
    severity: str = HARD_SEVERITY


@dataclass(frozen=True)
class SavedIdfGeometry:
    """Geometry identity independently recovered from one retained S0 IDF."""

    archetype_id: str
    idf_path: Path
    floor_area_m2: float
    volume_m3: float
    storey_count: int


@dataclass(frozen=True)
class SavedIdfGeometryAudit:
    """V8.d result for one archetype's own saved-IDF geometry readback."""

    archetype_id: str
    passed: bool
    detail: str


def _index_unique(rows: Iterable[Mapping[str, object]], label: str) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        cell_id = str(row.get("cell_id", ""))
        if not cell_id or cell_id in indexed:
            raise ValueError(f"{label} must have exactly one non-empty entry per cell_id")
        indexed[cell_id] = row
    return indexed


def _index_observed(rows: Iterable[Mapping[str, object]]) -> tuple[dict[str, Mapping[str, object]], bool]:
    """Index observed artefacts, retaining a false flag instead of raising.

    A malformed on-disk manifest is precisely what G8.14 must report.  The
    campaign table itself remains strict because it is the declared contract.
    """
    indexed: dict[str, Mapping[str, object]] = {}
    unique_nonempty = True
    for row in rows:
        cell_id = str(row.get("cell_id", ""))
        if not cell_id or cell_id in indexed:
            unique_nonempty = False
            continue
        indexed[cell_id] = row
    return indexed, unique_nonempty


def evaluate_pre_submission_gates(
    campaign_cells: Iterable[Mapping[str, object]],
    manifests: Iterable[Mapping[str, object]],
    cache_records: Iterable[Mapping[str, object]],
    *,
    declared_cell_count: int,
    campaign_table_path: str,
    scoring_table_path: str,
) -> tuple[GateFinding, ...]:
    """Score the non-engine Step 8 gates against one declared campaign table.

    ``campaign_table_path`` and ``scoring_table_path`` must be identical.
    This makes V8.b an executable guard, instead of letting a scorer compare
    results with a neighbouring, similarly named campaign export.
    """
    cells = list(campaign_cells)
    cell_index = _index_unique(cells, "campaign cells")
    manifest_index, manifests_unique = _index_observed(manifests)
    cache_index, cache_unique = _index_observed(cache_records)
    expected_ids = set(cell_index)

    v8a_ok = len(cells) == declared_cell_count
    v8b_ok = bool(campaign_table_path) and campaign_table_path == scoring_table_path
    complete_sets = (
        manifests_unique and cache_unique
        and set(manifest_index) == expected_ids and set(cache_index) == expected_ids
    )
    prerequisites_ok = v8a_ok and v8b_ok and complete_sets

    controls_ok = True
    for cell in cells:
        if float(cell["sensitivity_f"]) <= 0:
            continue
        control_id = str(cell.get("control_cell_id", ""))
        control = manifest_index.get(control_id, {})
        controls_ok = controls_ok and control.get("status") == "success"

    differing_schedules = True
    grouped: dict[str, list[Mapping[str, object]]] = {}
    for cell in cells:
        grouped.setdefault(str(cell["archetype_id"]), []).append(cell)
    for group in grouped.values():
        digests = [str(manifest_index.get(str(cell["cell_id"]), {}).get("schedule_emitted_sha256", "")) for cell in group]
        if len(digests) != len(set(digests)) or any(not digest for digest in digests):
            differing_schedules = False

    fresh_cache = all(
        str(cache_index.get(cell_id, {}).get("dependency_digest", ""))
        == str(manifest_index.get(cell_id, {}).get("dependency_digest", ""))
        and bool(manifest_index.get(cell_id, {}).get("dependency_digest"))
        for cell_id in expected_ids
    )

    immutable_fields = ("cell_id", "platform", "created_utc")
    manifests_complete = manifests_unique and all(
        all(manifest.get(field) for field in immutable_fields)
        and str(manifest.get("cell_id")) == cell_id
        for cell_id, manifest in manifest_index.items()
    )

    fold_correct = manifests_unique and all(
        manifest.get("fold") == f"{cell['survey_fold']}_held_out"
        and manifest.get("held_out_country") == cell["survey_fold"]
        for cell_id, cell in cell_index.items()
        for manifest in (manifest_index.get(cell_id, {}),)
    )

    return (
        GateFinding("G8.0", prerequisites_ok and controls_ok, "all non-zero cells have a successful matching f=0 control"),
        GateFinding("G8.8", prerequisites_ok and differing_schedules, "each archetype has distinct emitted schedule checksums by f level"),
        GateFinding("G8.9", prerequisites_ok and fresh_cache, "every cache record matches its manifest dependency digest"),
        GateFinding("G8.14", prerequisites_ok and manifests_complete, "each cell has its own populated immutable manifest fields"),
        GateFinding("G8.16", prerequisites_ok and fold_correct, "every manifest names its matching held-out fold and country"),
    )


def findings_by_gate(findings: Iterable[GateFinding]) -> dict[str, GateFinding]:
    """Index a gate report and reject accidental duplicate gate records."""
    indexed = {finding.gate: finding for finding in findings}
    if tuple(indexed) != PRE_SUBMISSION_GATES:
        raise ValueError("pre-submission report must contain each supported gate exactly once")
    if any(finding.severity != HARD_SEVERITY for finding in indexed.values()):
        raise ValueError("all Step 8 gate findings must be hard severity")
    return indexed


def _coverage_index(findings: Iterable[GateFinding], label: str) -> dict[str, GateFinding]:
    indexed: dict[str, GateFinding] = {}
    for finding in findings:
        if not finding.gate or finding.gate in indexed:
            raise ValueError("{} must contain one non-empty result per checkpoint".format(label))
        if finding.severity != HARD_SEVERITY:
            raise ValueError("{} checkpoint {} is not hard severity".format(label, finding.gate))
        indexed[finding.gate] = finding
    if not indexed:
        raise ValueError("{} must not be empty".format(label))
    return indexed


def evaluate_perturbation_coverage(
    baseline: Iterable[GateFinding],
    probes: Mapping[str, Iterable[GateFinding]],
) -> tuple[PerturbationCoverage, ...]:
    """Cross-tab the frozen Table 17 probes against a clean local baseline.

    This evaluator rejects a missing probe or an unregistered checkpoint.
    Each expected failure must transition from baseline pass to probe failure;
    each explicitly clean checkpoint must remain passed.  P05 preserves the
    parent document's assignment/value split through the checkpoint names
    ``G8.12.assignment`` and ``G8.12.value``.  P12 is stronger: it must leave
    every observed baseline checkpoint clean.

    The result only establishes the local mutation-contract cross-tab.  It
    must not be presented as evidence that a retained campaign was run.
    """
    baseline_index = _coverage_index(baseline, "baseline")
    expected_ids = {entry.identifier for entry in PERTURBATION_MATRIX}
    actual_ids = set(probes)
    if actual_ids != expected_ids:
        missing = ", ".join(sorted(expected_ids - actual_ids)) or "none"
        extra = ", ".join(sorted(actual_ids - expected_ids)) or "none"
        raise ValueError("probe identifiers differ from the frozen matrix; missing={} extra={}".format(missing, extra))

    report: list[PerturbationCoverage] = []
    for expectation in PERTURBATION_MATRIX:
        probe_index = _coverage_index(probes[expectation.identifier], expectation.identifier)
        required = set(expectation.must_fail) | set(expectation.must_stay_clean)
        if expectation.identifier == "P12":
            required = set(baseline_index)
        missing_checkpoints = sorted(
            (required - set(baseline_index)) | (required - set(probe_index))
        )
        if missing_checkpoints:
            raise ValueError("{} lacks registered checkpoint(s): {}".format(
                expectation.identifier, ", ".join(missing_checkpoints),
            ))
        missing_failures = tuple(sorted(
            gate for gate in expectation.must_fail
            if not baseline_index[gate].passed or probe_index[gate].passed
        ))
        clean_gates = expectation.must_stay_clean if expectation.identifier != "P12" else tuple(baseline_index)
        dirty_clean = tuple(sorted(
            gate for gate in clean_gates
            if not baseline_index[gate].passed or not probe_index[gate].passed
        ))
        passed = not missing_failures and not dirty_clean
        report.append(PerturbationCoverage(
            expectation.identifier,
            passed,
            missing_failures,
            dirty_clean,
            "expected_fail={} observed_fail={} expected_clean={}".format(
                ",".join(expectation.must_fail) or "none",
                ",".join(sorted(gate for gate, finding in probe_index.items() if not finding.passed)) or "none",
                ",".join(clean_gates) or "none",
            ),
        ))
    return tuple(report)


def parse_mdd_meter_names(mdd_text: str) -> frozenset[str]:
    """Read declared meter names from an EnergyPlus ``eplusout.mdd`` artefact.

    The list is intentionally taken from the pinned engine output, rather than
    carrying a historic hard-coded EnergyPlus meter catalogue.  Matching is
    case-insensitive because EnergyPlus meter identifiers are case-insensitive.
    """
    names = re.findall(r"(?im)^\s*Output:Meter\s*,\s*([^,;!\r\n]+)", mdd_text)
    return frozenset(name.strip().casefold() for name in names if name.strip())


def evaluate_meter_gates(
    available_meter_names: Iterable[str],
    required_meter_names: Iterable[str],
    *,
    selected_total: float,
    component_values: Mapping[str, float],
    relative_tolerance: float = STEP8_GATE_BANDS["G8.10.meter_balance_relative_difference"],
) -> tuple[GateFinding, GateFinding]:
    """Evaluate G8.10 balance and G8.11 meter-name evidence for one cell.

    A missing requested meter makes both gates fail.  This deliberately
    implements perturbation 3: the obsolete ``Gas:Facility`` must not merely
    fail name lookup while the balance gate passes on unrelated values.
    """
    if relative_tolerance < 0:
        raise ValueError("relative_tolerance must be non-negative")
    available = {str(name).strip().casefold() for name in available_meter_names if str(name).strip()}
    required = {str(name).strip().casefold() for name in required_meter_names if str(name).strip()}
    names_ok = bool(required) and required <= available
    numeric_values = [selected_total, *component_values.values()]
    numbers_ok = all(math.isfinite(float(value)) and float(value) >= 0 for value in numeric_values)
    components_nonzero = bool(component_values) and all(float(value) > 0 for value in component_values.values())
    residual = abs(float(selected_total) - sum(float(value) for value in component_values.values()))
    denominator = max(abs(float(selected_total)), 1.0)
    balanced = numbers_ok and components_nonzero and residual / denominator <= relative_tolerance
    missing = sorted(required - available)
    return (
        GateFinding(
            "G8.10", names_ok and balanced,
            "selected total reconciles to non-zero components within {:.3%}; missing meters: {}".format(
                relative_tolerance, ", ".join(missing) or "none"
            ),
        ),
        GateFinding(
            "G8.11", names_ok,
            "all requested meter names exist in the parsed pinned-engine MDD; missing: {}".format(
                ", ".join(missing) or "none"
            ),
        ),
    )


def _idf_objects(idf_text: str) -> list[tuple[str, tuple[str, ...]]]:
    """Parse a minimal IDF object view independently of the IDF writer.

    This intentionally handles only ordinary comma/semicolon objects used by
    the Step 8 saved-artifact audit.  It strips comments and keeps fields in
    order, which is enough to independently inspect ``Schedule:File`` and its
    consuming object without trusting an in-memory builder object.
    """
    without_comments = "\n".join(line.split("!", 1)[0] for line in idf_text.splitlines())
    parsed: list[tuple[str, tuple[str, ...]]] = []
    for raw_object in without_comments.split(";"):
        fields = tuple(field.strip() for field in raw_object.split(",") if field.strip())
        if fields:
            parsed.append((fields[0].casefold(), fields[1:]))
    return parsed


def _idf_objects_preserving_empty_fields(idf_text: str) -> list[tuple[str, tuple[str, ...]]]:
    """Parse ordinary IDF objects while retaining positional empty fields.

    The Zone object's area, volume, and ceiling-height fields have fixed IDD
    positions.  Unlike the schedule parser above, this audit must retain
    empty fields so it cannot accidentally interpret a shifted value as one
    of those geometry quantities.
    """
    without_comments = "\n".join(line.split("!", 1)[0] for line in idf_text.splitlines())
    parsed: list[tuple[str, tuple[str, ...]]] = []
    for raw_object in without_comments.split(";"):
        fields = tuple(field.strip() for field in raw_object.split(","))
        if fields and fields[0]:
            parsed.append((fields[0].casefold(), fields[1:]))
    return parsed


def _positive_finite_idf_number(value: str, label: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("saved IDF {} must be numeric".format(label)) from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError("saved IDF {} must be finite and positive".format(label))
    return parsed


def read_saved_idf_geometry(idf_path: Path | str, archetype_id: str) -> SavedIdfGeometry:
    """Read V8.d area, volume, and storeys from *that file's* Zone object.

    This intentionally uses a small positional text parser rather than an
    in-memory generator object.  S0 serializes its equivalent per-storey
    height in ``Zone.Ceiling_Height``; ``V / (A * h)`` must be an integer.
    The archetype token must also be present in a saved surface name, which
    rejects a valid-looking IDF accidentally carried over from another cell.
    """
    path = Path(idf_path)
    if not path.is_file():
        raise ValueError("saved IDF does not exist: {}".format(path))
    identifier = str(archetype_id).strip()
    if not identifier:
        raise ValueError("archetype_id is required for saved-IDF geometry audit")
    objects = _idf_objects_preserving_empty_fields(path.read_text(encoding="utf-8"))
    zones = [fields for kind, fields in objects if kind == "zone"]
    if len(zones) != 1 or len(zones[0]) <= 9:
        raise ValueError("saved IDF must contain exactly one fully positioned Zone object")
    zone = zones[0]
    ceiling_height_m = _positive_finite_idf_number(zone[7], "Zone Ceiling Height")
    volume_m3 = _positive_finite_idf_number(zone[8], "Zone Volume")
    floor_area_m2 = _positive_finite_idf_number(zone[9], "Zone Floor Area")
    storeys_exact = volume_m3 / (floor_area_m2 * ceiling_height_m)
    storey_count = round(storeys_exact)
    if storey_count < 1 or not math.isclose(storeys_exact, storey_count, rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError("saved IDF Zone fields do not encode an integral storey count")
    token = "EU_{}_".format(identifier).casefold()
    if not any(
        kind == "buildingsurface:detailed" and fields and fields[0].casefold().startswith(token)
        for kind, fields in objects
    ):
        raise ValueError("saved IDF does not identify archetype {} in its own surface names".format(identifier))
    return SavedIdfGeometry(identifier, path, floor_area_m2, volume_m3, storey_count)


def audit_saved_idf_geometries(
    saved_idfs: Mapping[str, Path | str],
    expected_geometry: Mapping[str, Mapping[str, object]],
) -> tuple[SavedIdfGeometryAudit, ...]:
    """Apply V8.d to a complete per-archetype saved-IDF set.

    ``expected_geometry`` is used only as the declared comparison target;
    values are always read from the matching retained IDF.  Reusing a path,
    swapping an IDF, missing an archetype, or changing any of area/volume/
    storeys produces a failed audit rather than a borrowed geometry value.
    """
    expected_ids = set(expected_geometry)
    actual_ids = set(saved_idfs)
    if actual_ids != expected_ids:
        missing = ", ".join(sorted(expected_ids - actual_ids)) or "none"
        extra = ", ".join(sorted(actual_ids - expected_ids)) or "none"
        raise ValueError("saved-IDF set differs from expected archetypes; missing={} extra={}".format(missing, extra))
    resolved_paths = [Path(saved_idfs[identifier]).resolve() for identifier in sorted(actual_ids)]
    if len(resolved_paths) != len(set(resolved_paths)):
        raise ValueError("each archetype must retain its own distinct saved IDF path")
    report: list[SavedIdfGeometryAudit] = []
    for identifier in sorted(expected_ids):
        recovered = read_saved_idf_geometry(saved_idfs[identifier], identifier)
        declared = expected_geometry[identifier]
        try:
            expected_area = float(declared["floor_area_m2"])
            expected_volume = float(declared["volume_m3"])
            expected_storeys = int(declared["storey_count"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("expected geometry for {} requires floor_area_m2, volume_m3, storey_count".format(identifier)) from exc
        matches = (
            math.isclose(recovered.floor_area_m2, expected_area, rel_tol=1e-6, abs_tol=1e-9)
            and math.isclose(recovered.volume_m3, expected_volume, rel_tol=1e-6, abs_tol=1e-9)
            and recovered.storey_count == expected_storeys
        )
        report.append(SavedIdfGeometryAudit(
            identifier,
            matches,
            "saved IDF area={:.9g}/{:.9g} m2 volume={:.9g}/{:.9g} m3 storeys={}/{}".format(
                recovered.floor_area_m2, expected_area, recovered.volume_m3,
                expected_volume, recovered.storey_count, expected_storeys,
            ),
        ))
    return tuple(report)


def evaluate_saved_idf_schedule_gates(
    idf_path: Path | str,
    *,
    schedule_name: str,
    schedule_path: Path | str,
    schedule_sha256: str,
    assignment_object_type: str,
    assignment_object_name: str,
) -> tuple[GateFinding, GateFinding]:
    """Audit G8.12/G8.13 from the saved IDF and schedule file on disk.

    G8.12 has both a value arm (the emitted file's measured checksum and the
    matching ``Schedule:File`` path) and an assignment arm (the declared
    consuming object points to that schedule).  G8.13 is intentionally read
    from the same saved artefact but by this independent text parser.
    """
    idf = Path(idf_path)
    schedule = Path(schedule_path)
    objects = _idf_objects(idf.read_text(encoding="utf-8")) if idf.is_file() else []
    expected_path = str(schedule).replace("\\", "/").casefold()
    schedule_objects = [fields for kind, fields in objects if kind == "schedule:file"]
    matching_schedule = next(
        (
            fields for fields in schedule_objects
            if len(fields) >= 8 and fields[0].casefold() == schedule_name.casefold()
            and fields[2].replace("\\", "/").casefold() == expected_path
        ),
        (),
    )
    checksum_ok = schedule.is_file() and _sha256_file(schedule) == schedule_sha256.casefold()
    consumers = [
        fields for kind, fields in objects
        if kind == assignment_object_type.casefold()
        and fields and fields[0].casefold() == assignment_object_name.casefold()
    ]
    assignment_ok = len(consumers) == 1 and any(
        field.casefold() == schedule_name.casefold() for field in consumers[0][1:]
    )
    value_ok = bool(matching_schedule) and checksum_ok
    interpolation_ok = bool(matching_schedule) and matching_schedule[7].casefold() == "no"
    return (
        GateFinding("G8.12", value_ok and assignment_ok, "saved Schedule:File checksum/path and consuming-object assignment match"),
        GateFinding("G8.13", interpolation_ok, "saved Schedule:File uses Interpolate to Timestep = No"),
    )


def _sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _message_kinds(error_text: str, severity: str) -> tuple[str, ...]:
    """Extract distinct EnergyPlus diagnostic kinds without using frequency."""
    pattern = re.compile(r"(?im)^\s*\*\*\s*{}\s*\*\*\s*(.+)$".format(re.escape(severity)))
    kinds: set[str] = set()
    for message in pattern.findall(error_text):
        # Numeric values and object names vary per cell; the stable first clause
        # is the triage kind that must be adjudicated once per category.
        normalized = re.sub(r"\s+", " ", message.strip()).casefold()
        normalized = re.split(r"[=:]", normalized, maxsplit=1)[0].strip()
        if normalized:
            kinds.add(normalized)
    return tuple(sorted(kinds))


def evaluate_warning_gate(error_text: str, approved_warning_kinds: Iterable[str]) -> GateFinding:
    """Evaluate G8.15 with hard failure for severe/fatal or untriaged kinds.

    ``approved_warning_kinds`` is a human-reviewed category list, not a count
    threshold.  A single unclassified ``invalid`` warning therefore fails even
    if it is outnumbered by thousands of known benign warnings (V8.f).
    """
    warnings = _message_kinds(error_text, "warning")
    severe = _message_kinds(error_text, "severe")
    fatal = _message_kinds(error_text, "fatal")
    approved = {str(kind).strip().casefold() for kind in approved_warning_kinds if str(kind).strip()}
    untriaged = tuple(kind for kind in warnings if kind not in approved)
    passed = not severe and not fatal and not untriaged
    return GateFinding(
        "G8.15", passed,
        "warning kinds={} untriaged={} severe={} fatal={}".format(
            len(warnings), ", ".join(untriaged) or "none",
            ", ".join(severe) or "none", ", ".join(fatal) or "none",
        ),
    )


REPRODUCIBILITY_DISCLAIMER = (
    "G8.1-G8.4 are reproducibility gates. They compare a cell against a re-run of itself. "
    "They are not a validation of simulated energy against measured energy, and no such validation "
    "is claimed anywhere in this paper."
)


def _nmbe_and_cvrmse(reference: Iterable[float], rerun: Iterable[float]) -> tuple[float, float]:
    """Return ASHRAE-style NMBE and CV(RMSE) percentages for a same-cell re-run."""
    expected = [float(value) for value in reference]
    observed = [float(value) for value in rerun]
    if len(expected) < 2 or len(expected) != len(observed):
        raise ValueError("reference and rerun series must have the same length of at least two")
    if not all(math.isfinite(value) for value in expected + observed):
        raise ValueError("reproducibility series must be finite")
    mean_expected = sum(expected) / len(expected)
    if mean_expected == 0:
        raise ValueError("reproducibility reference mean must be non-zero")
    degrees_of_freedom = len(expected) - 1
    residuals = [actual - baseline for actual, baseline in zip(observed, expected)]
    nmbe = 100.0 * sum(residuals) / (degrees_of_freedom * mean_expected)
    cvrmse = 100.0 * math.sqrt(sum(value * value for value in residuals) / degrees_of_freedom) / mean_expected
    return nmbe, cvrmse


def evaluate_reproducibility_gates(
    monthly_reference: Iterable[float], monthly_rerun: Iterable[float],
    hourly_reference: Iterable[float], hourly_rerun: Iterable[float],
) -> tuple[GateFinding, GateFinding, GateFinding, GateFinding]:
    """Evaluate G8.1--G8.4 using the fixed monthly/hourly re-run thresholds."""
    monthly_nmbe, monthly_cvrmse = _nmbe_and_cvrmse(monthly_reference, monthly_rerun)
    hourly_nmbe, hourly_cvrmse = _nmbe_and_cvrmse(hourly_reference, hourly_rerun)
    monthly_nmbe_limit = STEP8_GATE_BANDS["G8.1.monthly_nmbe_pct"]
    hourly_nmbe_limit = STEP8_GATE_BANDS["G8.2.hourly_nmbe_pct"]
    monthly_cvrmse_limit = STEP8_GATE_BANDS["G8.3.monthly_cvrmse_pct"]
    hourly_cvrmse_limit = STEP8_GATE_BANDS["G8.4.hourly_cvrmse_pct"]
    return (
        GateFinding("G8.1", abs(monthly_nmbe) <= monthly_nmbe_limit, "monthly re-run NMBE={:.4f}% (limit +/-{}%)".format(monthly_nmbe, monthly_nmbe_limit)),
        GateFinding("G8.2", abs(hourly_nmbe) <= hourly_nmbe_limit, "hourly re-run NMBE={:.4f}% (limit +/-{}%)".format(hourly_nmbe, hourly_nmbe_limit)),
        GateFinding("G8.3", monthly_cvrmse <= monthly_cvrmse_limit, "monthly re-run CV(RMSE)={:.4f}% (limit {}%)".format(monthly_cvrmse, monthly_cvrmse_limit)),
        GateFinding("G8.4", hourly_cvrmse <= hourly_cvrmse_limit, "hourly re-run CV(RMSE)={:.4f}% (limit {}%)".format(hourly_cvrmse, hourly_cvrmse_limit)),
    )


def _finite_series(values: Iterable[float], label: str) -> list[float]:
    series = [float(value) for value in values]
    if not series or not all(math.isfinite(value) and value >= 0 for value in series):
        raise ValueError("{} must be a non-empty finite non-negative series".format(label))
    return series


def _unique_peak_index(values: list[float], label: str) -> int:
    peak = max(values)
    if peak <= 0 or values.count(peak) != 1:
        raise ValueError("{} must have one positive unique peak".format(label))
    return values.index(peak)


def evaluate_peak_gates(
    comparison_series: Iterable[float], modelled_series: Iterable[float], *, comparison_label: str,
) -> tuple[GateFinding, GateFinding]:
    """Score G8.5 and G8.6 against one named, same-interval comparison series.

    G8.5 permits a peak magnitude difference of at most 15 percent; G8.6
    permits a peak timing difference of at most one hourly sample.  A named
    comparison is mandatory so a fixture cannot silently be scored against a
    flat control or an unspecified series.
    """
    if not str(comparison_label).strip():
        raise ValueError("comparison_label is required for G8.5/G8.6")
    reference = _finite_series(comparison_series, "comparison_series")
    modelled = _finite_series(modelled_series, "modelled_series")
    if len(reference) != len(modelled):
        raise ValueError("comparison and modelled peak series must have equal length")
    reference_index = _unique_peak_index(reference, "comparison_series")
    modelled_index = _unique_peak_index(modelled, "modelled_series")
    relative_difference = abs(max(modelled) - max(reference)) / max(reference)
    timing_difference = abs(modelled_index - reference_index)
    peak_difference_limit = STEP8_GATE_BANDS["G8.5.peak_relative_difference"]
    peak_timing_limit = STEP8_GATE_BANDS["G8.6.peak_timing_hours"]
    return (
        GateFinding(
            "G8.5", relative_difference <= peak_difference_limit,
            "{} peak magnitude difference={:.3%} (limit +/-{:.0%})".format(
                comparison_label, relative_difference, peak_difference_limit,
            ),
        ),
        GateFinding(
            "G8.6", timing_difference <= peak_timing_limit,
            "{} peak timing difference={} hourly samples (limit <={} h)".format(
                comparison_label, timing_difference, peak_timing_limit,
            ),
        ),
    )


def evaluate_archetype_eui_band_gate(
    as_modelled_eui_kwh_m2: float,
    as_modelled_band_kwh_m2: tuple[float, float],
    *,
    expected_floor_area_m2: float,
    reported_floor_area_m2: float,
    empirical_eui_kwh_m2: float | None = None,
    empirical_band_kwh_m2: tuple[float, float] | None = None,
) -> GateFinding:
    """Score G8.7's graded as-modelled band and report empirical comparison only.

    The explicit floor-area identity check implements the prescribed
    different-geometry mutation: a plausible EUI must not pass when its
    denominator came from another archetype.  An empirical-band miss is
    deliberately retained in the detail string and never changes ``passed``.
    """
    modelled = float(as_modelled_eui_kwh_m2)
    expected_area = float(expected_floor_area_m2)
    reported_area = float(reported_floor_area_m2)
    lower, upper = (float(value) for value in as_modelled_band_kwh_m2)
    if not all(math.isfinite(value) and value >= 0 for value in (modelled, expected_area, reported_area, lower, upper)):
        raise ValueError("G8.7 EUI, areas, and as-modelled band must be finite and non-negative")
    if expected_area <= 0 or reported_area <= 0 or lower > upper:
        raise ValueError("G8.7 requires positive matching areas and an ordered as-modelled band")
    geometry_ok = math.isclose(expected_area, reported_area, rel_tol=1e-6, abs_tol=1e-9)
    band_ok = lower <= modelled <= upper
    empirical_detail = "empirical comparison not supplied (informational)"
    if empirical_eui_kwh_m2 is not None or empirical_band_kwh_m2 is not None:
        if empirical_eui_kwh_m2 is None or empirical_band_kwh_m2 is None:
            raise ValueError("empirical EUI and band must be supplied together")
        empirical = float(empirical_eui_kwh_m2)
        empirical_lower, empirical_upper = (float(value) for value in empirical_band_kwh_m2)
        if not all(math.isfinite(value) and value >= 0 for value in (empirical, empirical_lower, empirical_upper)) or empirical_lower > empirical_upper:
            raise ValueError("empirical EUI and band must be finite, non-negative, and ordered")
        empirical_detail = "empirical EUI={:.6g}; band=[{:.6g}, {:.6g}]; informational only".format(
            empirical, empirical_lower, empirical_upper,
        )
    return GateFinding(
        "G8.7", band_ok and geometry_ok,
        "as-modelled EUI={:.6g}; band=[{:.6g}, {:.6g}]; geometry {}/{} m2; {}".format(
            modelled, lower, upper, reported_area, expected_area, empirical_detail,
        ),
    )
