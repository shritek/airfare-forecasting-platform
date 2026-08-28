# Hugging Face ATL Domestic Airfare Source

## Source

- Dataset: [`egupta/atl-dom-flight-data-sql-db`](https://huggingface.co/datasets/egupta/atl-dom-flight-data-sql-db)
- Collection code: [`EkanshGupta/flights`](https://github.com/EkanshGupta/flights)
- Published artifact: `dataDB_domestic.db` (9.37 GB SQLite database)
- Dataset upload: May 2025; the actual observation range remains unverified
- Displayed license tag: MIT

The source page describes domestic one-way Google Flights searches from ATL to
BOS, PHX, DFW, LAS, SEA, DEN, LIH, OGG, SAN, and SFO for one adult in economy,
with no checked bag and one carry-on. The collection repository describes roughly
700 Google requests per run using a reverse-engineered Base64-encoded request.

## Known Schema and Identity Risk

The reported `data_table` columns are `id`, `origin`, `destination`, `name`,
`days`, `price`, `today`, `days_ahead`, `flight_duration`, `flight_depart`,
`flight_arrive`, `stops`, `stops_info`, and `departure_date`.

The schema lacks flight numbers, segment-level carriers and times, cabin/fare
product identifiers, currency, and an explicit total-fare definition. The first
profiler therefore evaluates this candidate identity without treating it as an
accepted contract:

```text
origin + destination + departure_date + name +
flight_depart + flight_arrive + flight_duration + stops + stops_info
```

Same-day duplicate and conflicting-price groups expose obvious collisions, but a
low collision count cannot prove identity stability. Manual samples and comparison
with richer sources remain necessary before label generation.

## License and Use Gate

The MIT tag clearly covers repository code only where the copyright holder has
the authority to grant it. It does not by itself establish that Google Flights
observations may be downloaded, retained, redistributed, or used for model
training. Before committing aggregate results or using the data beyond local
evaluation, record evidence for the dataset artifact's license, collection terms,
and permitted derived use. Do not commit the database or source rows.

## Local Profiling Runbook

After acquiring the database outside Git, record its download date, source
revision, byte size, and SHA-256 checksum in the private experiment/run record.
Then run:

```bash
uv run airfare-profile-hf-atl /path/to/dataDB_domestic.db \
  --output /path/to/hf-atl-profile.json
```

The command opens SQLite in read-only mode and produces deterministic JSON with:

- discovered tables, columns, and exact row count;
- valid observation/departure date bounds and invalid-date counts;
- route counts, scrape-day coverage, and date bounds;
- nulls, invalid/nonpositive prices, exact duplicates, and lead-time mismatches;
- candidate-key completeness, trajectory counts spanning 2, 3, 7, and 14 days;
- same-day duplicate and conflicting-price groups; and
- adjacent comparable price-transition counts and unchanged-fare rate.

The report is evidence for source selection and later label feasibility. It is not
a canonical transformation or training dataset.
