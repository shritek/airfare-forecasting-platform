"""Measure future-price label feasibility in the HF ATL airfare source."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from airfare_forecasting.data.hf_atl_sqlite import (
    CANDIDATE_IDENTITY_COLUMNS,
    DATASET_ID,
    TABLE_NAME,
    _complete_identity,
    _database_inventory,
    _parse_price_cents,
    _quote,
    _scalar,
    _valid_date,
)

REPORT_SCHEMA_VERSION = 1
DEFAULT_HORIZONS = (1, 3, 7, 14)


class LabelFeasibilityError(RuntimeError):
    """Raised when label feasibility cannot be measured safely."""


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _prepare_daily_prices(connection: sqlite3.Connection) -> int:
    identity = ", ".join(_quote(column) for column in CANDIDATE_IDENTITY_COLUMNS)
    valid_candidate = (
        f"{_complete_identity()} AND {_valid_date('today')} "
        f"AND {_valid_date('departure_date')} AND departure_date > today"
    )
    connection.execute("PRAGMA temp_store = FILE")
    connection.execute(
        "CREATE TEMP TABLE daily_prices AS "
        f"SELECT {identity}, today, MIN(parse_price_cents(price)) AS price_cents "
        f"FROM {_quote(TABLE_NAME)} WHERE {valid_candidate} "
        f"GROUP BY {identity}, today "
        "HAVING COUNT(*) = COUNT(parse_price_cents(price)) "
        "AND COUNT(DISTINCT parse_price_cents(price)) = 1 "
        "AND MIN(parse_price_cents(price)) > 0"
    )
    index_columns = ", ".join(
        _quote(column) for column in (*CANDIDATE_IDENTITY_COLUMNS, "today")
    )
    connection.execute(
        f"CREATE UNIQUE INDEX daily_prices_identity_date ON daily_prices "
        f"({index_columns})"
    )
    return _scalar(connection, "SELECT COUNT(*) FROM daily_prices")


def _prepare_route_calendar(connection: sqlite3.Connection) -> int:
    connection.execute(
        "CREATE TEMP TABLE route_collection AS "
        "SELECT DISTINCT origin, destination, today "
        f"FROM {_quote(TABLE_NAME)} WHERE {_valid_date('today')}"
    )
    connection.execute(
        "CREATE UNIQUE INDEX route_collection_key ON route_collection "
        "(origin, destination, today)"
    )
    return _scalar(connection, "SELECT COUNT(*) FROM route_collection")


def _metrics(
    *,
    current_count: int,
    departed: int,
    no_collection: int,
    eligible: int,
    labeled: int,
    increased: int,
    unchanged: int,
    decreased: int,
    change_sum_cents: float,
    absolute_change_sum_cents: float,
    percentage_change_sum: float,
) -> dict[str, object]:
    if current_count != departed + no_collection + eligible:
        raise LabelFeasibilityError(
            "current-observation censoring counts do not balance"
        )
    if labeled != increased + unchanged + decreased:
        raise LabelFeasibilityError("labeled price-outcome counts do not balance")
    return {
        "current_observation_count": current_count,
        "censored_departure_count": departed,
        "censored_no_route_collection_count": no_collection,
        "eligible_observation_count": eligible,
        "labeled_observation_count": labeled,
        "unmatched_itinerary_count": eligible - labeled,
        "label_coverage_rate": _rate(labeled, eligible),
        "increased_count": increased,
        "unchanged_count": unchanged,
        "decreased_count": decreased,
        "increase_rate": _rate(increased, labeled),
        "unchanged_rate": _rate(unchanged, labeled),
        "decrease_rate": _rate(decreased, labeled),
        "mean_change_cents": round(change_sum_cents / labeled, 2) if labeled else None,
        "mean_absolute_change_cents": round(absolute_change_sum_cents / labeled, 2)
        if labeled
        else None,
        "mean_percentage_change": round(percentage_change_sum / labeled, 6)
        if labeled
        else None,
    }


def _horizon_profile(
    connection: sqlite3.Connection, horizon_days: int
) -> dict[str, object]:
    future_join = " AND ".join(
        f"future.{_quote(column)} = current.{_quote(column)}"
        for column in CANDIDATE_IDENTITY_COLUMNS
    )
    rows = connection.execute(
        "WITH current_rows AS ("
        "SELECT daily_prices.*, date(today, ?) AS future_date FROM daily_prices) "
        "SELECT current.origin, current.destination, COUNT(*), "
        "SUM(CASE WHEN current.future_date >= current.departure_date "
        "THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN current.future_date < current.departure_date "
        "AND route.today IS NULL THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN current.future_date < current.departure_date "
        "AND route.today IS NOT NULL THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN current.future_date < current.departure_date "
        "AND route.today IS NOT NULL AND future.price_cents IS NOT NULL "
        "THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents > current.price_cents "
        "THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents = current.price_cents "
        "THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents < current.price_cents "
        "THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents IS NOT NULL "
        "THEN future.price_cents - current.price_cents ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents IS NOT NULL "
        "THEN ABS(future.price_cents - current.price_cents) ELSE 0 END), "
        "SUM(CASE WHEN future.price_cents IS NOT NULL "
        "THEN (future.price_cents - current.price_cents) * 1.0 "
        "/ current.price_cents ELSE 0 END) "
        "FROM current_rows AS current "
        "LEFT JOIN route_collection AS route "
        "ON route.origin = current.origin "
        "AND route.destination = current.destination "
        "AND route.today = current.future_date "
        "LEFT JOIN daily_prices AS future "
        f"ON {future_join} AND future.today = current.future_date "
        "GROUP BY current.origin, current.destination "
        "ORDER BY current.origin, current.destination",
        (f"+{horizon_days} days",),
    )

    total_current = 0
    total_departed = 0
    total_no_collection = 0
    total_eligible = 0
    total_labeled = 0
    total_increased = 0
    total_unchanged = 0
    total_decreased = 0
    total_change_sum = 0.0
    total_absolute_change_sum = 0.0
    total_percentage_change_sum = 0.0
    route_slices: list[dict[str, object]] = []

    for row in rows:
        current_count = int(row[2] or 0)
        departed = int(row[3] or 0)
        no_collection = int(row[4] or 0)
        eligible = int(row[5] or 0)
        labeled = int(row[6] or 0)
        increased = int(row[7] or 0)
        unchanged = int(row[8] or 0)
        decreased = int(row[9] or 0)
        change_sum = float(row[10] or 0)
        absolute_change_sum = float(row[11] or 0)
        percentage_change_sum = float(row[12] or 0)
        route_slices.append(
            {
                "origin": row[0],
                "destination": row[1],
                **_metrics(
                    current_count=current_count,
                    departed=departed,
                    no_collection=no_collection,
                    eligible=eligible,
                    labeled=labeled,
                    increased=increased,
                    unchanged=unchanged,
                    decreased=decreased,
                    change_sum_cents=change_sum,
                    absolute_change_sum_cents=absolute_change_sum,
                    percentage_change_sum=percentage_change_sum,
                ),
            }
        )
        total_current += current_count
        total_departed += departed
        total_no_collection += no_collection
        total_eligible += eligible
        total_labeled += labeled
        total_increased += increased
        total_unchanged += unchanged
        total_decreased += decreased
        total_change_sum += change_sum
        total_absolute_change_sum += absolute_change_sum
        total_percentage_change_sum += percentage_change_sum

    return {
        "horizon_days": horizon_days,
        **_metrics(
            current_count=total_current,
            departed=total_departed,
            no_collection=total_no_collection,
            eligible=total_eligible,
            labeled=total_labeled,
            increased=total_increased,
            unchanged=total_unchanged,
            decreased=total_decreased,
            change_sum_cents=total_change_sum,
            absolute_change_sum_cents=total_absolute_change_sum,
            percentage_change_sum=total_percentage_change_sum,
        ),
        "route_slices": route_slices,
    }


def profile_label_feasibility(
    database_path: Path, horizons: Sequence[int] = DEFAULT_HORIZONS
) -> dict[str, object]:
    """Profile exact-horizon labels under explicit source-specific censoring."""
    normalized_horizons = sorted(set(horizons))
    if not normalized_horizons or any(horizon <= 0 for horizon in normalized_horizons):
        raise LabelFeasibilityError("horizons must contain positive day counts")

    path = database_path.expanduser().resolve()
    if not path.is_file():
        raise LabelFeasibilityError(f"database does not exist or is not a file: {path}")

    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        connection.create_function(
            "parse_price_cents", 1, _parse_price_cents, deterministic=True
        )
        try:
            _database_inventory(connection)
            source_row_count = _scalar(
                connection, f"SELECT COUNT(*) FROM {_quote(TABLE_NAME)}"
            )
            daily_price_count = _prepare_daily_prices(connection)
            route_collection_day_count = _prepare_route_calendar(connection)
            return {
                "report_schema_version": REPORT_SCHEMA_VERSION,
                "source": {
                    "dataset_id": DATASET_ID,
                    "database_file": path.name,
                    "source_row_count": source_row_count,
                },
                "preparation": {
                    "usable_candidate_day_count": daily_price_count,
                    "route_collection_day_count": route_collection_day_count,
                    "duplicate_policy": "collapse identical candidate-key/day prices",
                    "exclusion_policy": (
                        "exclude invalid/nonpositive prices, conflicting candidate-key/day "
                        "prices, incomplete keys, invalid dates, and observations on/after "
                        "departure"
                    ),
                },
                "horizons": [
                    _horizon_profile(connection, horizon)
                    for horizon in normalized_horizons
                ],
                "interpretation": {
                    "route_collection_proxy": (
                        "a route is considered collected when any source row exists for "
                        "that origin, destination, and date"
                    ),
                    "unmatched_policy": (
                        "unmatched eligible itineraries are reported, not labeled as "
                        "sold out or as a price movement"
                    ),
                    "identity_status": (
                        "hf_atl_composite_v0 remains a candidate identity pending "
                        "manual stability validation"
                    ),
                },
            }
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise LabelFeasibilityError(
            f"failed to profile labels in {path}: {error}"
        ) from error


def main(argv: Sequence[str] | None = None) -> int:
    """Run label-feasibility profiling from the command line."""
    parser = argparse.ArgumentParser(
        description="Profile exact-horizon labels in the HF ATL airfare database."
    )
    parser.add_argument("database", type=Path, help="path to dataDB_domestic.db")
    parser.add_argument(
        "--horizon",
        type=int,
        action="append",
        dest="horizons",
        help="horizon in days; repeat for multiple values (default: 1, 3, 7, 14)",
    )
    parser.add_argument("--output", type=Path, help="write JSON to this file")
    args = parser.parse_args(argv)

    try:
        report = profile_label_feasibility(
            args.database,
            horizons=args.horizons if args.horizons is not None else DEFAULT_HORIZONS,
        )
    except LabelFeasibilityError as error:
        parser.error(str(error))

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(serialized, end="")
    else:
        args.output.write_text(serialized, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
