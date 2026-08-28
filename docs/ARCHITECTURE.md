# Architecture

## Current Posture

This is a target logical architecture, not a commitment to specific AWS services.
The first vertical slice should run locally on representative data with the same
contracts intended for scheduled cloud jobs. [ADR-0001](decisions/0001-batch-first-inference.md)
sets batch inference as the default.

[ADR-0002](decisions/0002-serpapi-live-fare-pilot.md) conditionally selects
SerpApi Google Flights for a bounded qualification pilot. The collector remains
disabled until the retention, derived-use, quota, budget, payload, price-semantics,
and route gates in
[LIVE_DATA.md](LIVE_DATA.md) pass.

```text
historical source ─┐
                   ├─> immutable raw observations
live fare source ──┘             │
                                 v
                        validation + normalization
                                 │
                                 v
                    trajectories + point-in-time features
                              /          \
                             v            v
                    versioned training   batch inference
                         snapshot             │
                             │                v
                             v          stored predictions
                     train + evaluate         │
                             │                │ future observation
                             v                v
                     model registry <── delayed-label evaluation
                             │                │
                             └──── champion/challenger + monitoring
```

## Data Zones and Boundaries

- **Raw:** immutable source payloads plus ingestion metadata. Reprocessing starts
  here; source quirks are preserved.
- **Canonical:** validated observations with explicit price semantics, event time,
  search time, source, and reconstructed itinerary identity/version.
- **ML datasets:** immutable, versioned feature/label snapshots with split metadata
  and lineage. These are never silently updated beneath an experiment.
- **Predictions and outcomes:** append-oriented prediction records containing
  model/version context, later joined to eligible observations by a deterministic
  label policy.

Exact object layout and partition keys depend on measured access patterns and file
sizes. `search_date` is a likely pruning dimension, but route-level partitioning
could produce too many small files and is not yet selected.

## Runtime Shape

Scheduled collection, transformation, training, inference, and evaluation are
separate idempotent jobs connected through durable artifacts. A failure should be
retryable without duplicating logical observations or overwriting immutable
inputs. Job runs need structured logs, run identifiers, counts, freshness, and
failure alerts.

AWS is preferred eventually, with S3 as the likely durable object store. Compute,
orchestration, catalog, registry hosting, and alerting will be chosen only after
local pipeline shape, frequency, scale, and operational requirements are known.
Terraform will own provisioned cloud resources; deployments should not depend on
console changes.

## Deferred Architecture Decisions

- DuckDB versus Polars (or both by boundary); Spark only after a measured need
- exact Parquet layout, compaction, catalog, and snapshot/version mechanism
- SerpApi qualification and collector execution environment
- scheduler/orchestrator and retry semantics
- MLflow tracking and registry hosting model
- retraining trigger implementation and promotion authority
- whether a read API or UI provides enough value to justify online components
