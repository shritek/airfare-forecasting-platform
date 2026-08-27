# Data

## Live Source

Amadeus Self-Service Flight Offers Search is the preferred conditional pilot
provider under [ADR-0002](decisions/0002-amadeus-live-fare-pilot.md). Production
terms, private-retention/derived-use permission, account quota, budget controls,
payload fields, and route coverage must pass the gates in
[LIVE_DATA.md](LIVE_DATA.md) before unattended collection begins. The provider's
known carrier and fare exclusions mean live observations will not be treated as a
representative sample of the full US domestic market.

## Candidate Historical Sources

### Expedia Flight Prices

The reported 2022 Kaggle corpus is large (roughly 82 million observations and
31 GB), covers major US airports, and exposes rich fare and segment attributes.
Its central unknown is whether `legId` or a reconstructable composite key remains
stable across search dates. Reported collection dates, schema semantics, and
license/redistribution terms must be verified from primary source material.

### `egupta/atl-dom-flight-data-sql-db`

The Hugging Face dataset is reported as a 9+ GB SQLite-backed collection centered
on ATL domestic routes. Its 2025 upload date is not evidence of observation dates.
The database must be queried for actual `today` coverage, routes, scrape density,
price semantics, duplicates, and licensing before it is selected.

The sources will not be concatenated by default. Reasonable experiments include
historical training with newer temporal/OOD validation, source-specific models,
or canonicalized joint training, but only after comparability is measured.

## Canonical Observation Requirements

The eventual canonical contract needs:

- source and source-record lineage;
- search/observation timestamp and departure timestamp;
- origin, destination, segments, carriers, flight identifiers, and stop structure;
- cabin and fare-product attributes needed to compare like with like;
- clearly defined currency and total-versus-base price semantics;
- availability when trustworthy;
- ingestion timestamp and deterministic duplicate/identity keys; and
- quality status rather than silent coercion or row loss.

The schema will be proposed only after inspecting real source schemas.

## First Profiling Report

Each source-specific profiler should produce machine-readable metrics and a concise
human report covering:

1. schema, row count, file/table inventory, and exact observation/departure dates;
2. routes, carriers, cabins, stops, and search/departure lead-time coverage;
3. candidate key uniqueness, exact duplicates, and conflicting duplicates;
4. trajectory length distribution and counts spanning 2, 3, 7, and 14+ search
   dates;
5. candidate identity stability under source keys and reconstructed composite keys;
6. unchanged-fare rate and absolute/percentage change distributions by interval;
7. gaps and disappearance patterns, separated from collection gaps when possible;
8. nulls, impossible timestamps, invalid prices, currencies, and outliers;
9. which fields are genuinely available at prediction time; and
10. price meaning, collection methodology, license, and redistribution constraints.

For the Hugging Face database, the audit must begin by discovering tables and then
run equivalents of the requested `MIN(today)`, `MAX(today)`, total-count, and
route-level scrape-day queries. For Expedia, identity analysis must compare
`legId` with increasingly strict segment-level composite keys across search dates.

## Artifact Policy

Downloaded source data, credentials, local databases, generated Parquet datasets,
models, and profiling extracts with redistribution restrictions do not belong in
Git. Small synthetic fixtures and aggregate reports may be committed when they do
not expose restricted source records. Future manifests will record checksums,
source versions, acquisition context, and transformation lineage.
