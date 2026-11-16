"""BigQuery Geospatial Analytics Playground scouting queries and summarizers."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence

import pandas as pd

from openubem.acquisition.gmaps_places_fetcher import map_place_types_to_ubem

_BQ_TABLE_ID_RE = re.compile(r"^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_-]+){1,3}$")
_FOOD_SERVICE_TYPES = frozenset(
    {"restaurant", "cafe", "bakery", "bar", "fast_food_restaurant"}
)
_SUPERMARKET_TYPES = frozenset({"supermarket", "grocery_store"})


@dataclass(frozen=True)
class DistrictScoutingReport:
    """District-level archetype and high-process-load scouting summary.

    Attributes:
        total_places: Total POI count observed inside the scouting envelope.
        type_counts: Mapping from Places type identifier to aggregated count.
        ubem_class_shares: Fractional shares mapped to OpenUBEM use classes.
        food_service_count: Combined count of food-service POIs.
        supermarket_count: Combined count of supermarket and grocery POIs.
        high_process_load_share: Share of POIs representing high cooking or
            refrigeration process loads.
        high_process_load_alert: ``True`` when ``high_process_load_share``
            meets or exceeds the configured threshold (default ``0.15``).
        notes: Actionable OpenUBEM Stage 4 calibration notes derived from shares.
    """

    total_places: int
    type_counts: dict[str, int]
    ubem_class_shares: dict[str, float]
    food_service_count: int
    supermarket_count: int
    high_process_load_share: float
    high_process_load_alert: bool
    notes: list[str]


def validate_bq_table_id(table_id: str) -> str:
    """Validates a BigQuery table reference against strict identifier rules.

    Args:
        table_id: Dotted BigQuery table identifier (e.g.,
            ``"project.dataset.table"``).

    Returns:
        Validated stripped table identifier string.

    Raises:
        ValueError: If ``table_id`` fails strict identifier pattern validation.
    """
    cleaned = str(table_id).strip()
    if not _BQ_TABLE_ID_RE.match(cleaned):
        raise ValueError(
            f"Invalid BigQuery table identifier: {table_id!r}. Expected "
            "alphanumeric/underscore/hyphen dotted parts only."
        )
    return cleaned


def build_places_insights_query(
    table_id: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    *,
    included_types: Sequence[str] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Builds a parameterized BigQuery SQL query for Places Insights scouting.

    Args:
        table_id: Validated BigQuery Places Insights table path.
        min_lon: Bounding box western longitude (WGS 84).
        min_lat: Bounding box southern latitude (WGS 84).
        max_lon: Bounding box eastern longitude (WGS 84).
        max_lat: Bounding box northern latitude (WGS 84).
        included_types: Optional filter sequence of Google Places type names.

    Returns:
        Tuple ``(sql_text, query_params)`` using ``@param`` bind variables.
    """
    safe_table = validate_bq_table_id(table_id)
    params: dict[str, Any] = {
        "min_lon": float(min_lon),
        "min_lat": float(min_lat),
        "max_lon": float(max_lon),
        "max_lat": float(max_lat),
    }
    type_clause = ""
    if included_types:
        params["included_types"] = [str(item) for item in included_types]
        type_clause = "\n  AND primary_type IN UNNEST(@included_types)"

    sql = (
        "SELECT\n"
        "  primary_type,\n"
        "  COUNT(*) AS place_count\n"
        f"FROM `{safe_table}`\n"
        "WHERE ST_INTERSECTS(\n"
        "    point,\n"
        "    ST_MAKEENVELOPE(@min_lon, @min_lat, @max_lon, @max_lat)\n"
        "  )"
        f"{type_clause}\n"
        "GROUP BY primary_type\n"
        "ORDER BY place_count DESC"
    )
    return sql, params


def build_street_view_insights_query(
    table_id: str,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> tuple[str, dict[str, Any]]:
    """Builds a parameterized BigQuery SQL query for Street View Insights.

    Args:
        table_id: Validated BigQuery Street View Insights table path.
        min_lon: Bounding box western longitude (WGS 84).
        min_lat: Bounding box southern latitude (WGS 84).
        max_lon: Bounding box eastern longitude (WGS 84).
        max_lat: Bounding box northern latitude (WGS 84).

    Returns:
        Tuple ``(sql_text, query_params)`` using ``@param`` bind variables.
    """
    safe_table = validate_bq_table_id(table_id)
    params: dict[str, Any] = {
        "min_lon": float(min_lon),
        "min_lat": float(min_lat),
        "max_lon": float(max_lon),
        "max_lat": float(max_lat),
    }
    sql = (
        "SELECT\n"
        "  asset_id,\n"
        "  capture_time,\n"
        "  geometry,\n"
        "  wwr_observed,\n"
        "  levels_observed\n"
        f"FROM `{safe_table}`\n"
        "WHERE ST_INTERSECTS(\n"
        "    geometry,\n"
        "    ST_MAKEENVELOPE(@min_lon, @min_lat, @max_lon, @max_lat)\n"
        "  )"
    )
    return sql, params


def summarize_places_insights_df(
    df: pd.DataFrame,
    *,
    process_load_threshold: float = 0.15,
) -> DistrictScoutingReport:
    """Aggregates Places Insights rows into an OpenUBEM archetype scouting report.

    Args:
        df: DataFrame with ``primary_type`` (or ``place_type``) and
            ``place_count`` (or ``count``) columns.
        process_load_threshold: Fraction above which cooking/refrigeration
            commercial load dominates district schedules.

    Returns:
        Structured :class:`DistrictScoutingReport`.

    Raises:
        ValueError: If required count or type columns are missing.
    """
    if df.empty:
        return DistrictScoutingReport(
            total_places=0,
            type_counts={},
            ubem_class_shares={},
            food_service_count=0,
            supermarket_count=0,
            high_process_load_share=0.0,
            high_process_load_alert=False,
            notes=["No Places Insights POIs observed inside the query envelope."],
        )

    type_col = "primary_type" if "primary_type" in df.columns else "place_type"
    count_col = "place_count" if "place_count" in df.columns else "count"
    if type_col not in df.columns or count_col not in df.columns:
        raise ValueError(
            "Places Insights DataFrame must include type and count columns."
        )

    type_counts: dict[str, int] = {}
    class_totals: dict[str, int] = {}
    food_count = 0
    market_count = 0
    total = 0

    for _, row in df.iterrows():
        raw_type = row[type_col]
        if pd.isna(raw_type):
            continue
        ptype = str(raw_type).strip().lower()
        cnt = int(row[count_col]) if pd.notna(row[count_col]) else 0
        if cnt <= 0:
            continue
        type_counts[ptype] = type_counts.get(ptype, 0) + cnt
        total += cnt

        ubem_class, _tag = map_place_types_to_ubem(ptype)
        class_totals[ubem_class] = class_totals.get(ubem_class, 0) + cnt
        if ptype in _FOOD_SERVICE_TYPES:
            food_count += cnt
        if ptype in _SUPERMARKET_TYPES:
            market_count += cnt

    shares = (
        {k: round(v / total, 4) for k, v in sorted(class_totals.items())}
        if total > 0
        else {}
    )
    high_load_share = (
        round((food_count + market_count) / total, 4) if total > 0 else 0.0
    )
    alert = high_load_share >= float(process_load_threshold)

    notes: list[str] = []
    if alert:
        notes.append(
            f"High process-load alert: food-service + supermarket POIs account "
            f"for {high_load_share:.1%} of district POIs (threshold "
            f"{process_load_threshold:.0%}). Expect elevated baseline cooking "
            "and refrigeration schedules in Stage 4."
        )
    else:
        notes.append(
            f"Moderate commercial process-load share ({high_load_share:.1%})."
        )

    return DistrictScoutingReport(
        total_places=total,
        type_counts=type_counts,
        ubem_class_shares=shares,
        food_service_count=food_count,
        supermarket_count=market_count,
        high_process_load_share=high_load_share,
        high_process_load_alert=alert,
        notes=notes,
    )


def summarize_svi_df(df: pd.DataFrame) -> dict[str, Any]:
    """Summarizes Street View Insights facade observations for envelope calibration.

    Args:
        df: DataFrame of Street View Insights asset detections containing optional
            ``wwr_observed`` and ``levels_observed`` columns.

    Returns:
        Summary dictionary with observation counts and descriptive quantiles.
    """
    summary: dict[str, Any] = {
        "n_assets": int(len(df)),
        "wwr_mean": None,
        "wwr_median": None,
        "levels_mean": None,
        "levels_median": None,
    }
    if df.empty:
        return summary

    if "wwr_observed" in df.columns:
        wwr = pd.to_numeric(df["wwr_observed"], errors="coerce").dropna()
        if not wwr.empty:
            summary["wwr_mean"] = round(float(wwr.mean()), 4)
            summary["wwr_median"] = round(float(wwr.median()), 4)

    if "levels_observed" in df.columns:
        lvls = pd.to_numeric(df["levels_observed"], errors="coerce").dropna()
        if not lvls.empty:
            summary["levels_mean"] = round(float(lvls.mean()), 3)
            summary["levels_median"] = round(float(lvls.median()), 3)

    return summary


def _bq_parameter_from_value(bigquery_mod: Any, name: str, value: Any) -> Any:
    """Converts a Python value into a typed BigQuery query parameter object.

    Args:
        bigquery_mod: Imported ``google.cloud.bigquery`` module.
        name: Query parameter identifier without ``@``.
        value: Scalar or list parameter value.

    Returns:
        Configured BigQuery ``ScalarQueryParameter`` or ``ArrayQueryParameter``.
    """
    if isinstance(value, (list, tuple, set)):
        seq = list(value)
        elem_type = "INT64" if seq and isinstance(seq[0], int) else "STRING"
        return bigquery_mod.ArrayQueryParameter(name, elem_type, seq)
    if isinstance(value, bool):
        return bigquery_mod.ScalarQueryParameter(name, "BOOL", value)
    if isinstance(value, int):
        return bigquery_mod.ScalarQueryParameter(name, "INT64", value)
    if isinstance(value, float):
        return bigquery_mod.ScalarQueryParameter(name, "FLOAT64", value)
    return bigquery_mod.ScalarQueryParameter(name, "STRING", str(value))


def execute_parameterized_bq_query(
    sql: str,
    params: dict[str, Any],
    *,
    project_id: str | None = None,
    client: Any | None = None,
) -> pd.DataFrame:
    """Executes parameterized BigQuery SQL using optional ``google-cloud-bigquery``.

    Args:
        sql: Parameterized BigQuery Standard SQL query string.
        params: Mapping of parameter names to values passed via ``QueryJobConfig``.
        project_id: Optional GCP billing project identifier.
        client: Optional pre-built or mocked BigQuery ``Client`` object.

    Returns:
        Query results decoded into a ``pandas.DataFrame``.

    Raises:
        ImportError: If ``client`` is ``None`` and ``google-cloud-bigquery``
            is not installed.
    """
    if client is not None:
        job = client.query(sql, job_config=params)
        return job.to_dataframe() if hasattr(job, "to_dataframe") else pd.DataFrame(job)

    try:
        from google.cloud import bigquery  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ImportError(
            "google-cloud-bigquery is required for live BigQuery execution. "
            "Install it with: pip install google-cloud-bigquery"
        ) from exc

    bq_client = bigquery.Client(project=project_id)
    bq_params = [_bq_parameter_from_value(bigquery, k, v) for k, v in params.items()]
    job_config = bigquery.QueryJobConfig(query_parameters=bq_params)
    return bq_client.query(sql, job_config=job_config).to_dataframe()
