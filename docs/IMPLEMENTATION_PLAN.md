# Implementation Plan

## Planning Principle

Start long-lead current-data accumulation as early as safely possible, then
resolve the highest-risk data and label assumptions before committing to model or
cloud architecture. Each item below is intended as a separate reviewable PR or a
small group of PRs with an explicit dependency. Stop for review between dependent
steps.

## Decision Gates

| Decision | Evidence required | Current posture |
| --- | --- | --- |
| Live provider | terms, total-price semantics, identity fields, cost, limits, and reliability | Amadeus conditionally selected in ADR-0002; qualification gates remain |
| Historical source | dates, trajectory density, identity, semantics, quality, license, access cost | Audit both independently |
| Itinerary identity | collision/stability analysis and manual samples across search dates | Source key is not trusted |
| Target and horizon | exact-label coverage, censoring, change distribution, baseline utility | One target and horizon first |
| Source combination | aligned semantics plus source-held-out and temporal experiments | Do not concatenate |
| Processing engine | measured runtime/memory on representative and full-scale scans | Prefer DuckDB/Polars; no Spark yet |
| Storage layout | observed read patterns, file sizes, cardinality, and compaction needs | Parquet likely; partitions open |
| AWS/orchestration | job durations, frequency, retries, dependencies, and cost model | Batch/scale-to-zero |
| Model family | baseline results, feature representation, training/serving constraints | XGBoost is a candidate |
| Retraining/promotion | label arrival rate, variance, drift, calibration, and operational SLOs | Define after production evidence |

## Proposed Delivery Sequence

### 0. Repository context (this PR)

Persist goals, constraints, architectural posture, data/ML methodology, review
workflow, and decision process. No production stack is selected here.

### 1. Reproducible development foundation

Choose the Python/runtime and packaging approach; add a `src` layout, test/lint/
type-check tooling, secret and data ignores, task commands, and CI. Use a tiny
smoke test to prove the toolchain, not speculative domain abstractions.

### 2. Live-provider feasibility and collection contract

Compare candidate providers using primary-source terms, total-price semantics,
itinerary fields, historical consistency, quotas, cost, reliability, and storage/
redistribution restrictions. Define a small fixed route and departure-horizon
universe, collection cadence, budget ceiling, secret handling, and immutable raw
observation envelope. Select the pilot provider in an ADR before integrating it.

### 3. Minimal live-data collection pilot

Implement a cost-capped collector that persists raw provider responses, request
parameters, observation time, source identifiers, and run metadata without
assuming the final canonical airfare schema. Make retries idempotent and expose
failures, freshness, request counts, and spend. Validate price semantics, identity
stability, rate limits, and collection gaps before expanding the universe.

Starting this pilot early is intentional: current trajectories require elapsed
calendar time and cannot be backfilled later. Once it is running, historical
profiling can proceed while live observations accumulate.

### 4. Dataset access manifests and source-specific profilers

Document acquisition and license evidence without committing raw data. Implement
streaming/query-based profilers with deterministic aggregate outputs, first on
small fixtures and then on real local data. Keep Expedia and Hugging Face adapters
separate. Publish aggregate audit reports and measured resource usage. This work
is independent of ongoing scheduled live collection after the pilot is stable.

### 5. Select a bootstrap dataset

Compare audits and record an ADR covering suitability, limitations, licensing,
and the role of the unselected source (for example, temporal/OOD validation). If
neither supports trajectories, stop and revise the data strategy.

### 6. Canonical observation contract and itinerary identity

Define the minimal canonical schema from observed source fields. Implement and
test deterministic normalization, duplicate policy, composite identity versions,
collision checks, and mutation handling. Record identity assumptions in an ADR.

### 7. Label feasibility and target decision

Construct candidate future labels with explicit time tolerance and censoring.
Report coverage and change behavior for a small set of horizons. Select exactly
one initial target/horizon in an ADR, including product loss and disappearance
policy.

### 8. Versioned dataset and baseline evaluation

Build point-in-time-correct snapshots and chronological splits. Add leakage tests
and no-change, booking-window/route, and simple statistical baselines. This is the
go/no-go gate for more complex modeling.

### 9. First nonlinear challenger and experiment lineage

Train and tune XGBoost only if baselines leave useful headroom. Add slice metrics,
calibration where relevant, explainability, serialization/interface tests, and
MLflow tracking with code/config/data lineage. Compare under the same split.

### 10. Cloud data and batch prediction vertical slice

Use Terraform to provision the minimum AWS storage, scheduled compute,
permissions, encryption, logging, alerts, and budget controls needed for raw
ingestion through stored prediction. Choose services from measured job needs.

### 11. Delayed labels, monitoring, and model governance

Join predictions to future observations using the approved label contract. Add
data quality/freshness, feature and prediction drift, actual performance slices,
and champion/challenger comparison. Establish thresholds and retraining/promotion
policy only after enough labels establish expected variance.

### 12. Product surface

Add a dashboard or read API after the prediction artifacts and monitoring are
reliable. Online inference requires a separate latency/user requirement and ADR.

## Immediate Next PR

After the provider-feasibility PR is reviewed, complete the private Amadeus
production-access checklist from `docs/LIVE_DATA.md`. If every qualification gate
passes, implement the minimal collector, immutable raw envelope, request ledger,
fail-closed budget cap, and synthetic integration tests. If a gate fails, update
ADR-0002 with the evidence before integrating a fallback provider.
