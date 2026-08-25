# Airfare Forecasting Platform

A production-oriented ML system for forecasting how an observed airline fare is
likely to change and eventually supporting a traveler-facing BUY/WAIT
recommendation.

This project focuses on fare evolution: it must connect repeated searches for the
same itinerary into a time series, construct future outcomes without leakage, and
evaluate models on later time periods. Its intended scope includes historical and
live ingestion, reproducible datasets, training and model governance, scheduled
inference, delayed-label evaluation, drift monitoring, and cost-aware AWS
infrastructure.

## Status

The project is in its definition and data-investigation phase. No dataset, target,
prediction horizon, live provider, or detailed cloud service map has been selected
yet. Those decisions require profiling and documented evidence.

The first implementation objective is a reproducible dataset profiler that can
answer whether candidate sources contain stable, useful fare trajectories. See
[the implementation plan](docs/IMPLEMENTATION_PLAN.md) for the proposed sequence.

## Product Direction

The product question is:

> Given the current price of an itinerary, should a traveler buy now or wait
> because its price is likely to decrease?

Classification (probability of an increase) and regression (future fare or fare
change) are both candidates. The initial target and horizon will be chosen after
measuring label coverage, censoring, volatility, and baseline behavior.

## Design Priorities

- correct temporal methodology and explicit leakage prevention
- longitudinal itinerary identity and data quality
- meaningful baselines before model complexity
- reproducible, traceable training and evaluation
- batch-first, cost-controlled operations
- small, reviewable pull requests and durable decision records

## Documentation

Start with [AGENTS.md](AGENTS.md), then use the detailed documents under
[`docs/`](docs/PROJECT_CONTEXT.md). Significant decisions are indexed in
[`docs/decisions/`](docs/decisions/README.md).

## Development

The language, package manager, and validation toolchain will be introduced in a
separate repository-foundation PR. Until then, this repository contains project
and design documentation only.
