"""Profile the Hugging Face ATL domestic airfare SQLite database."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

DATASET_ID = "egupta/atl-dom-flight-data-sql-db"
TABLE_NAME = "data_table"
PROFILE_SCHEMA_VERSION = 1

REQUIRED_COLUMNS = (
    "id",
    "origin",
    "destination",
    "name",
    "days",
    "price",
    "today",
    "days_ahead",
    "flight_duration",
    "flight_depart",
    "flight_arrive",
    "stops",
    "stops_info",
    "departure_date",
)

# This is a candidate key, not an accepted itinerary identity. The audit measures
# whether the source's available fields make it sufficiently stable.
CANDIDATE_IDENTITY_COLUMNS = (
    "origin",
    "destination",
    "departure_date",
    "name",
    "flight_depart",
    "flight_arrive",
    "flight_duration",
    "stops",
    "stops_info",
)

_PRICE_PATTERN = re.compile(r"^\$?\s*([0-9]+(?:\.[0-9]{1,2})?)$")


class ProfileError(RuntimeError):
    """Raised when the database cannot satisfy the expected source contract."""


def _quote(identifier: str) -> str:
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


def _parse_price_cents(value: object) -> int | None:
    if value is None:
        return None
    normalized = str(value).strip().replace(",", "")
    match = _PRICE_PATTERN.fullmatch(normalized)
    if match is None:
        return None
    try:
        return int(Decimal(match.group(1)) * 100)
    except InvalidOperation, ValueError:
        return None


def _scalar(connection: sqlite3.Connection, query: str) -> int:
    row = connection.execute(query).fetchone()
    if row is None or row[0] is None:
        return 0
    return int(row[0])


def _valid_date(column: str) -> str:
    quoted = _quote(column)
    return f"{quoted} IS NOT NULL AND date({quoted}) = {quoted}"


def _complete_identity() -> str:
    required_values = " AND ".join(
        f"{_quote(column)} IS NOT NULL AND trim(CAST({_quote(column)} AS TEXT)) <> ''"
        for column in CANDIDATE_IDENTITY_COLUMNS
        if column != "stops_info"
    )
    # The source represents nonstop itineraries with stops=0 and blank stops_info.
    stops_info = _quote("stops_info")
    stops = _quote("stops")
    return (
        f"{required_values} AND {stops_info} IS NOT NULL AND "
        f"(trim(CAST({stops_info} AS TEXT)) <> '' OR "
        f"trim(CAST({stops} AS TEXT)) = '0')"
    )


def _lead_time_offsets(connection: sqlite3.Connection) -> dict[str, int]:
    rows = connection.execute(
        "SELECT CAST(julianday(departure_date) - julianday(today) AS INTEGER) "
        "- days_ahead AS offset_days, COUNT(*) "
        f"FROM {_quote(TABLE_NAME)} WHERE {_valid_date('today')} "
        f"AND {_valid_date('departure_date')} AND days_ahead IS NOT NULL "
        "GROUP BY offset_days ORDER BY offset_days"
    )
    return {str(int(row[0])): int(row[1]) for row in rows}


def _database_inventory(
    connection: sqlite3.Connection,
) -> tuple[list[str], list[str], dict[str, str]]:
    tables = [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    if TABLE_NAME not in tables:
        raise ProfileError(
            f"expected table {TABLE_NAME!r}; discovered: {', '.join(tables) or 'none'}"
        )

    column_rows = list(connection.execute(f"PRAGMA table_info({_quote(TABLE_NAME)})"))
    columns = [str(row[1]) for row in column_rows]
    missing = sorted(set(REQUIRED_COLUMNS) - set(columns))
    if missing:
        raise ProfileError(f"{TABLE_NAME!r} is missing columns: {', '.join(missing)}")
    declared_types = {str(row[1]): str(row[2]) for row in column_rows}
    return tables, columns, declared_types


def _temporal_coverage(
    connection: sqlite3.Connection, column: str
) -> dict[str, object]:
    quoted = _quote(column)
    valid = _valid_date(column)
    row = connection.execute(
        f"SELECT MIN(CASE WHEN {valid} THEN {quoted} END), "
        f"MAX(CASE WHEN {valid} THEN {quoted} END), "
        f"SUM(CASE WHEN {valid} THEN 0 ELSE 1 END) FROM {_quote(TABLE_NAME)}"
    ).fetchone()
    assert row is not None
    return {"min": row[0], "max": row[1], "invalid_count": int(row[2] or 0)}


def _route_profile(connection: sqlite3.Connection) -> list[dict[str, object]]:
    today_is_valid = _valid_date("today")
    rows = connection.execute(
        f"SELECT origin, destination, COUNT(*), "
        f"COUNT(DISTINCT CASE WHEN {today_is_valid} THEN today END), "
        f"MIN(CASE WHEN {today_is_valid} THEN today END), "
        f"MAX(CASE WHEN {today_is_valid} THEN today END) "
        f"FROM {_quote(TABLE_NAME)} GROUP BY origin, destination "
        "ORDER BY origin, destination"
    )
    return [
        {
            "origin": row[0],
            "destination": row[1],
            "observation_count": int(row[2]),
            "scrape_days": int(row[3]),
            "first_observation": row[4],
            "last_observation": row[5],
        }
        for row in rows
    ]


def _quality_profile(
    connection: sqlite3.Connection, columns: Sequence[str]
) -> dict[str, object]:
    non_id_columns = [column for column in columns if column != "id"]
    group_columns = ", ".join(_quote(column) for column in non_id_columns)
    duplicate_rows = _scalar(
        connection,
        "SELECT COALESCE(SUM(duplicate_count - 1), 0) FROM ("
        f"SELECT COUNT(*) AS duplicate_count FROM {_quote(TABLE_NAME)} "
        f"GROUP BY {group_columns} HAVING COUNT(*) > 1)",
    )

    null_expressions = ", ".join(
        f"SUM(CASE WHEN {_quote(column)} IS NULL THEN 1 ELSE 0 END)"
        for column in REQUIRED_COLUMNS
    )
    null_row = connection.execute(
        f"SELECT {null_expressions} FROM {_quote(TABLE_NAME)}"
    ).fetchone()
    assert null_row is not None
    lead_time_offset_counts = _lead_time_offsets(connection)

    return {
        "exact_duplicate_rows_excluding_id": duplicate_rows,
        "invalid_price_count": _scalar(
            connection,
            f"SELECT COUNT(*) FROM {_quote(TABLE_NAME)} "
            "WHERE parse_price_cents(price) IS NULL",
        ),
        "nonpositive_price_count": _scalar(
            connection,
            f"SELECT COUNT(*) FROM {_quote(TABLE_NAME)} "
            "WHERE parse_price_cents(price) <= 0",
        ),
        "lead_time_mismatch_count": sum(
            count for offset, count in lead_time_offset_counts.items() if offset != "0"
        ),
        "lead_time_offset_counts": lead_time_offset_counts,
        "null_counts": {
            column: int(null_row[index] or 0)
            for index, column in enumerate(REQUIRED_COLUMNS)
        },
    }


def _identity_profile(connection: sqlite3.Connection) -> dict[str, object]:
    identity = ", ".join(_quote(column) for column in CANDIDATE_IDENTITY_COLUMNS)
    complete_identity = _complete_identity()
    valid_observation = f"{complete_identity} AND {_valid_date('today')}"

    trajectory_row = connection.execute(
        "WITH trajectories AS ("
        f"SELECT {identity}, COUNT(DISTINCT today) AS scrape_days "
        f"FROM {_quote(TABLE_NAME)} WHERE {valid_observation} GROUP BY {identity}) "
        "SELECT COUNT(*), "
        "SUM(CASE WHEN scrape_days >= 2 THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN scrape_days >= 3 THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN scrape_days >= 7 THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN scrape_days >= 14 THEN 1 ELSE 0 END) FROM trajectories"
    ).fetchone()
    assert trajectory_row is not None

    grouping = f"{identity}, today"
    return {
        "candidate_key_version": "hf_atl_composite_v0",
        "candidate_key_columns": list(CANDIDATE_IDENTITY_COLUMNS),
        "rows_with_incomplete_candidate_key": _scalar(
            connection,
            f"SELECT COUNT(*) FROM {_quote(TABLE_NAME)} WHERE NOT ({complete_identity})",
        ),
        "unique_candidate_itineraries": int(trajectory_row[0] or 0),
        "itineraries_by_minimum_scrape_days": {
            "2": int(trajectory_row[1] or 0),
            "3": int(trajectory_row[2] or 0),
            "7": int(trajectory_row[3] or 0),
            "14": int(trajectory_row[4] or 0),
        },
        "same_day_duplicate_groups": _scalar(
            connection,
            "SELECT COUNT(*) FROM ("
            f"SELECT 1 FROM {_quote(TABLE_NAME)} WHERE {valid_observation} "
            f"GROUP BY {grouping} HAVING COUNT(*) > 1)",
        ),
        "same_day_conflicting_price_groups": _scalar(
            connection,
            "SELECT COUNT(*) FROM ("
            f"SELECT 1 FROM {_quote(TABLE_NAME)} WHERE {valid_observation} "
            f"GROUP BY {grouping} "
            "HAVING COUNT(DISTINCT parse_price_cents(price)) > 1)",
        ),
    }


def _price_transition_profile(connection: sqlite3.Connection) -> dict[str, object]:
    identity = ", ".join(_quote(column) for column in CANDIDATE_IDENTITY_COLUMNS)
    valid_observation = f"{_complete_identity()} AND {_valid_date('today')}"
    row = connection.execute(
        "WITH daily_prices AS ("
        f"SELECT {identity}, today, AVG(parse_price_cents(price)) AS price_cents "
        f"FROM {_quote(TABLE_NAME)} WHERE {valid_observation} "
        "AND parse_price_cents(price) IS NOT NULL "
        f"GROUP BY {identity}, today "
        "HAVING COUNT(DISTINCT parse_price_cents(price)) = 1), "
        "transitions AS ("
        "SELECT price_cents, LAG(price_cents) OVER ("
        f"PARTITION BY {identity} ORDER BY today) AS previous_price_cents "
        "FROM daily_prices) "
        "SELECT COUNT(*), "
        "SUM(CASE WHEN price_cents = previous_price_cents THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN price_cents > previous_price_cents THEN 1 ELSE 0 END), "
        "SUM(CASE WHEN price_cents < previous_price_cents THEN 1 ELSE 0 END), "
        "AVG(ABS(price_cents - previous_price_cents)) "
        "FROM transitions WHERE previous_price_cents IS NOT NULL"
    ).fetchone()
    assert row is not None
    count = int(row[0] or 0)
    unchanged = int(row[1] or 0)
    return {
        "comparable_transition_count": count,
        "unchanged_count": unchanged,
        "increased_count": int(row[2] or 0),
        "decreased_count": int(row[3] or 0),
        "unchanged_rate": round(unchanged / count, 6) if count else None,
        "mean_absolute_change_cents": round(float(row[4]), 2)
        if row[4] is not None
        else None,
        "exclusions": "invalid prices and candidate-key/date groups with conflicting prices",
    }


def profile_database(database_path: Path) -> dict[str, object]:
    """Return a deterministic aggregate profile without mutating the database."""
    path = database_path.expanduser().resolve()
    if not path.is_file():
        raise ProfileError(f"database does not exist or is not a file: {path}")

    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        connection.create_function(
            "parse_price_cents", 1, _parse_price_cents, deterministic=True
        )
        try:
            tables, columns, declared_types = _database_inventory(connection)
            routes = _route_profile(connection)
            return {
                "profile_schema_version": PROFILE_SCHEMA_VERSION,
                "source": {"dataset_id": DATASET_ID, "database_file": path.name},
                "database": {
                    "tables": tables,
                    "profiled_table": TABLE_NAME,
                    "columns": columns,
                    "declared_types": declared_types,
                    "row_count": _scalar(
                        connection, f"SELECT COUNT(*) FROM {_quote(TABLE_NAME)}"
                    ),
                },
                "temporal_coverage": {
                    "observation_date": _temporal_coverage(connection, "today"),
                    "departure_date": _temporal_coverage(connection, "departure_date"),
                },
                "routes": {"unique_count": len(routes), "items": routes},
                "quality": _quality_profile(connection, columns),
                "identity": _identity_profile(connection),
                "price_transitions": _price_transition_profile(connection),
            }
        finally:
            connection.close()
    except sqlite3.Error as error:
        raise ProfileError(f"failed to profile {path}: {error}") from error


def main(argv: Sequence[str] | None = None) -> int:
    """Run the source profiler from the command line."""
    parser = argparse.ArgumentParser(
        description="Profile the HF ATL domestic airfare SQLite database."
    )
    parser.add_argument("database", type=Path, help="path to dataDB_domestic.db")
    parser.add_argument("--output", type=Path, help="write JSON to this file")
    args = parser.parse_args(argv)

    try:
        report = profile_database(args.database)
    except ProfileError as error:
        parser.error(str(error))

    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(serialized, end="")
    else:
        args.output.write_text(serialized, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
