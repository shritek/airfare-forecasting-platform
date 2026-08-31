"""Tests for HF ATL future-price label feasibility."""

import sqlite3
from pathlib import Path

import pytest

from airfare_forecasting.data.hf_atl_labels import (
    LabelFeasibilityError,
    profile_label_feasibility,
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
    stops TEXT,
    stops_info TEXT,
    departure_date TEXT
)
"""


def _row(
    row_id: int,
    *,
    name: str,
    today: str,
    price: str,
    destination: str = "BOS",
    departure_date: str = "2026-09-01",
) -> tuple[object, ...]:
    return (
        row_id,
        "ATL",
        destination,
        name,
        1,
        price,
        today,
        0,
        "2 hr 30 min",
        "08:00",
        "10:30",
        "0",
        "",
        departure_date,
    )


def _create_database(path: Path) -> None:
    rows = [
        _row(1, name="A", today="2026-08-01", price="$100"),
        _row(2, name="A", today="2026-08-01", price="$100"),
        _row(3, name="A", today="2026-08-08", price="$120"),
        _row(4, name="B", today="2026-08-01", price="$200"),
        _row(
            5,
            name="C",
            today="2026-08-01",
            price="$150",
            departure_date="2026-08-05",
        ),
        _row(
            6,
            name="D",
            today="2026-08-01",
            price="$250",
            destination="SFO",
        ),
        _row(7, name="F", today="2026-08-01", price="$300"),
        _row(8, name="F", today="2026-08-08", price="$300"),
        _row(9, name="F", today="2026-08-08", price="$310"),
        _row(10, name="E", today="2026-08-01", price="$400"),
        _row(11, name="E", today="2026-08-01", price="$410"),
        _row(12, name="G", today="2026-08-01", price="unknown"),
        _row(13, name="H", today="2026-08-01", price="$0"),
    ]
    connection = sqlite3.connect(path)
    try:
        connection.execute(SCHEMA)
        connection.executemany(
            "INSERT INTO data_table VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def test_exact_horizon_profile_separates_labels_from_censoring(tmp_path: Path) -> None:
    database = tmp_path / "labels.db"
    _create_database(database)

    report = profile_label_feasibility(database, horizons=(7,))

    assert report["preparation"] == {
        "usable_candidate_day_count": 6,
        "route_collection_day_count": 3,
        "duplicate_policy": "collapse identical candidate-key/day prices",
        "exclusion_policy": (
            "exclude invalid/nonpositive prices, conflicting candidate-key/day "
            "prices, incomplete keys, invalid dates, and observations on/after "
            "departure"
        ),
    }
    assert report["horizons"] == [
        {
            "horizon_days": 7,
            "current_observation_count": 6,
            "censored_departure_count": 1,
            "censored_no_route_collection_count": 2,
            "eligible_observation_count": 3,
            "labeled_observation_count": 1,
            "unmatched_itinerary_count": 2,
            "label_coverage_rate": 0.333333,
            "increased_count": 1,
            "unchanged_count": 0,
            "decreased_count": 0,
            "increase_rate": 1.0,
            "unchanged_rate": 0.0,
            "decrease_rate": 0.0,
            "mean_change_cents": 2000.0,
            "mean_absolute_change_cents": 2000.0,
            "mean_percentage_change": 0.2,
            "route_slices": [
                {
                    "origin": "ATL",
                    "destination": "BOS",
                    "current_observation_count": 5,
                    "censored_departure_count": 1,
                    "censored_no_route_collection_count": 1,
                    "eligible_observation_count": 3,
                    "labeled_observation_count": 1,
                    "unmatched_itinerary_count": 2,
                    "label_coverage_rate": 0.333333,
                    "increased_count": 1,
                    "unchanged_count": 0,
                    "decreased_count": 0,
                    "increase_rate": 1.0,
                    "unchanged_rate": 0.0,
                    "decrease_rate": 0.0,
                    "mean_change_cents": 2000.0,
                    "mean_absolute_change_cents": 2000.0,
                    "mean_percentage_change": 0.2,
                },
                {
                    "origin": "ATL",
                    "destination": "SFO",
                    "current_observation_count": 1,
                    "censored_departure_count": 0,
                    "censored_no_route_collection_count": 1,
                    "eligible_observation_count": 0,
                    "labeled_observation_count": 0,
                    "unmatched_itinerary_count": 0,
                    "label_coverage_rate": None,
                    "increased_count": 0,
                    "unchanged_count": 0,
                    "decreased_count": 0,
                    "increase_rate": None,
                    "unchanged_rate": None,
                    "decrease_rate": None,
                    "mean_change_cents": None,
                    "mean_absolute_change_cents": None,
                    "mean_percentage_change": None,
                },
            ],
        }
    ]


def test_horizons_are_positive(tmp_path: Path) -> None:
    database = tmp_path / "labels.db"
    _create_database(database)

    with pytest.raises(LabelFeasibilityError, match="positive day counts"):
        profile_label_feasibility(database, horizons=(0,))
