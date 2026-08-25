# Project Context

## Objective

Build a small but genuine production ML platform around airfare price forecasting.
It should ingest historical and current observations, create reproducible
training data, train and govern models, generate scheduled predictions, join those
predictions to delayed outcomes, monitor behavior and performance, and support
evidence-based retraining and promotion.

The portfolio claim must be earned by working software and experiments. The goal
is not to assemble an inventory of fashionable services.

## User and Product Outcome

For a concrete itinerary and its currently observed fare, provide a calibrated
forecast and an actionable BUY/WAIT recommendation. A possible eventual result is
a probability of a fare increase within seven days, optionally accompanied by an
expected future fare. The initial prediction target and horizon remain open.

The system predicts change over time. Route-level rows without repeated,
reliably matched itinerary observations cannot support the core product claim.

## Required Capabilities

The intended lifecycle is:

1. ingest immutable raw historical and live observations;
2. validate and normalize them into a canonical schema;
3. reconstruct itinerary trajectories and create point-in-time-correct features
   and labels;
4. version training snapshots and run time-based model evaluation;
5. register candidates and publish champion batch predictions;
6. retain predictions until future observations provide labels;
7. monitor freshness, quality, drift, calibration, and realized performance; and
8. train challengers and promote them under explicit criteria.

## Engineering Principles

- Start simple, but make correctness, observability, and reproducibility part of
  the first usable vertical slice.
- Measure before adding distributed processing, external features, or complex
  infrastructure.
- Treat data contracts, identity, label construction, and leakage prevention as
  production logic with focused tests.
- Prefer Parquet and analytical engines suited to tens of millions of rows over
  giant CSV workflows. Spark must be justified by measured limits.
- Prefer scheduled batch workloads and scale-to-zero AWS components. Avoid an
  always-on endpoint unless a measured product need appears.
- Make failures visible and keep cloud cost bounded.
- Keep notebooks optional and exploratory; production paths must be packaged,
  configured, tested, and repeatable.

## Reproducibility Contract

Every registered model should be traceable to a model artifact, training run,
metrics, parameters, feature configuration, immutable dataset snapshot, and Git
commit. A future operator must be able to answer exactly what produced a model.

## Delivery and Review

All meaningful work goes through a focused pull request from current `main`.
Changes include relevant tests, documentation, validation results, assumptions,
risks, and review guidance. Significant choices are recorded in an ADR in the same
PR. Dependent work waits for review unless explicitly requested otherwise.

Commits and PRs use the repository user's existing Git and authenticated GitHub
identity, without AI/tool authorship or generation attribution. Verify identity
before committing; never change global identity or commit credentials and data.

## Current Unknowns

The project must not silently assume:

- candidate dataset dates, trajectory density, semantic compatibility, or license;
- stable itinerary keys or treatment of disappearance and itinerary mutation;
- classification versus regression, prediction horizon, or decision threshold;
- a live provider, sampling universe, cadence, rate limits, or cost;
- detailed storage partitions, orchestration, MLflow hosting, or AWS topology; or
- retraining, drift, and champion-promotion thresholds.

The investigation order and evidence required to resolve these questions are in
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).
