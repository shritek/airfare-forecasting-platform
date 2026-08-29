"""Tests for the Hugging Face ATL SQLite profiler."""

import json
import sqlite3
from pathlib import Path

import pytest

from airfare_forecasting.data.hf_atl_sqlite import (
    ProfileError,
    main,
    profile_database,
)

SCHEMA = """
CREATE TABLE data_table (
    id INTEGER PRIMARY KEY,
    origin TEXT,
    destination TEXT,
    name TEXT,
    days INTEGER,
    price TEXT,
    today TEXT,
    days_ahead INTEGER,
    flight_duration TEXT,
    flight_depart TEXT,
    flight_arrive TEXT,
    stops INTEGER,
    stops_info TEXT,
    departure_date TEXT
)
"""


def _row(
    row_id: int,
    *,
    today: str,
    price: str,
    destination: str = "BOS",
    name: str = "Example Air",
    departure_date: str = "2026-09-01",
    flight_depart: str = "08:00",
    stops_info: str = "Nonstop",
) -> tuple[object, ...]:
    days_ahead = 32 - int(today[-2:]) if today.startswith("2026-08-") else 0
    return (
        row_id,
        "ATL",
        destination,
        name,
        1,
        price,
        today,
        days_ahead,
        "2 hr 30 min",
        flight_depart,
        "10:30",
        0,
        stops_info,
        departure_date,
    )


def _create_database(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(SCHEMA)
        rows: list[tuple[object, ...]] = []
        for day in range(1, 15):
            price = "$100" if day <= 7 else "$110"
            rows.append(_row(day, today=f"2026-08-{day:02d}", price=price))

        rows.extend(
            [
                _row(15, today="2026-08-01", price="$200", destination="SFO"),
                _row(16, today="2026-08-02", price="$200", destination="SFO"),
                _row(17, today="2026-08-03", price="$200", destination="SFO"),
                _row(18, today="2026-08-01", price="$100"),
                _row(19, today="2026-08-02", price="$105"),
                _row(
                    20,
                    today="not-a-date",
                    price="unknown",
                    destination="SFO",
                    name="Other Air",
                    flight_depart="12:00",
                ),
            ]
        )
        connection.executemany(
            "INSERT INTO data_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def test_profile_reports_temporal_identity_and_quality_evidence(tmp_path: Path) -> None:
    database = tmp_path / "dataDB_domestic.db"
    _create_database(database)

    report = profile_database(database)

    assert report["database"] == {
        "tables": ["data_table"],
        "profiled_table": "data_table",
        "columns": [
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
        ],
        "declared_types": {
            "id": "INTEGER",
            "origin": "TEXT",
            "destination": "TEXT",
            "name": "TEXT",
            "days": "INTEGER",
            "price": "TEXT",
            "today": "TEXT",
            "days_ahead": "INTEGER",
            "flight_duration": "TEXT",
            "flight_depart": "TEXT",
            "flight_arrive": "TEXT",
            "stops": "INTEGER",
            "stops_info": "TEXT",
            "departure_date": "TEXT",
        },
        "row_count": 20,
    }
    assert report["temporal_coverage"] == {
        "observation_date": {
            "min": "2026-08-01",
            "max": "2026-08-14",
            "invalid_count": 1,
        },
        "departure_date": {
            "min": "2026-09-01",
            "max": "2026-09-01",
            "invalid_count": 0,
        },
    }
    assert report["routes"] == {
        "unique_count": 2,
        "items": [
            {
                "origin": "ATL",
                "destination": "BOS",
                "observation_count": 16,
                "scrape_days": 14,
                "first_observation": "2026-08-01",
                "last_observation": "2026-08-14",
            },
            {
                "origin": "ATL",
                "destination": "SFO",
                "observation_count": 4,
                "scrape_days": 3,
                "first_observation": "2026-08-01",
                "last_observation": "2026-08-03",
            },
        ],
    }

    quality = report["quality"]
    assert isinstance(quality, dict)
    assert quality["exact_duplicate_rows_excluding_id"] == 1
    assert quality["invalid_price_count"] == 1
    assert quality["nonpositive_price_count"] == 0
    assert quality["lead_time_mismatch_count"] == 0
    assert quality["lead_time_offset_counts"] == {"0": 19}

    identity = report["identity"]
    assert isinstance(identity, dict)
    assert identity["unique_candidate_itineraries"] == 2
    assert identity["itineraries_by_minimum_scrape_days"] == {
        "2": 2,
        "3": 2,
        "7": 1,
        "14": 1,
    }
    assert identity["same_day_duplicate_groups"] == 2
    assert identity["same_day_conflicting_price_groups"] == 1

    transitions = report["price_transitions"]
    assert isinstance(transitions, dict)
    assert transitions["comparable_transition_count"] == 14
    assert transitions["unchanged_count"] == 13
    assert transitions["increased_count"] == 1
    assert transitions["decreased_count"] == 0


def test_profile_rejects_database_missing_required_columns(tmp_path: Path) -> None:
    database = tmp_path / "incomplete.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE data_table (id INTEGER PRIMARY KEY)")
    finally:
        connection.close()

    with pytest.raises(ProfileError, match="missing columns"):
        profile_database(database)


def test_profile_handles_an_empty_source_table(tmp_path: Path) -> None:
    database = tmp_path / "empty.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(SCHEMA)
    finally:
        connection.close()

    report = profile_database(database)

    assert report["temporal_coverage"] == {
        "observation_date": {"min": None, "max": None, "invalid_count": 0},
        "departure_date": {"min": None, "max": None, "invalid_count": 0},
    }
    quality = report["quality"]
    assert isinstance(quality, dict)
    null_counts = quality["null_counts"]
    assert isinstance(null_counts, dict)
    assert len(null_counts) == 14
    assert all(value == 0 for value in null_counts.values())
    transitions = report["price_transitions"]
    assert isinstance(transitions, dict)
    assert transitions["comparable_transition_count"] == 0


def test_blank_stops_info_is_valid_for_a_nonstop_itinerary(tmp_path: Path) -> None:
    database = tmp_path / "nonstop.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute(SCHEMA)
        connection.execute(
            "INSERT INTO data_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            _row(1, today="2026-08-01", price="$100", stops_info=""),
        )
        connection.commit()
    finally:
        connection.close()

    identity = profile_database(database)["identity"]

    assert isinstance(identity, dict)
    assert identity["rows_with_incomplete_candidate_key"] == 0
    assert identity["unique_candidate_itineraries"] == 1


def test_cli_writes_deterministic_json(tmp_path: Path) -> None:
    database = tmp_path / "dataDB_domestic.db"
    output = tmp_path / "profile.json"
    _create_database(database)

    assert main([str(database), "--output", str(output)]) == 0
    first_output = output.read_text(encoding="utf-8")
    assert json.loads(first_output)["source"] == {
        "dataset_id": "egupta/atl-dom-flight-data-sql-db",
        "database_file": "dataDB_domestic.db",
    }

    assert main([str(database), "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8") == first_output
