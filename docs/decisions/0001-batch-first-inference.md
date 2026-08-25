# ADR-0001: Batch-First Inference

Date: 2026-08-24
Status: Accepted

## Context

Airfare recommendations change on the cadence of new fare observations and future
price horizons measured in days. No current product requirement calls for
millisecond scoring. This portfolio project must keep cloud cost and operational
surface area controlled while still demonstrating automated production inference.

## Decision

Generate predictions in scheduled batches after fare collection and feature
computation. Store results for downstream consumption and delayed-label
evaluation. Do not provision an always-on model endpoint by default.

## Alternatives Considered

- Synchronous online inference for every user request.
- A hybrid system with scheduled predictions and an online fallback.
- Event-driven scoring for each newly ingested observation.

## Rationale

Batch execution matches the expected data arrival and user decision cadence,
supports scale-to-zero compute, simplifies reproducibility and delayed evaluation,
and avoids an unjustified availability/latency burden. Stored predictions also
provide a natural audit record for champion/challenger comparison.

## Consequences

Costs and operations are simpler, and identical model/data versions can be scored
as a unit. Recommendations may be stale between scheduled runs, and unseen ad hoc
itineraries cannot be scored immediately. Collection, transformation, and
prediction schedules need explicit freshness objectives and failure alerts.

## Revisit When

Reconsider if user research requires scoring previously unseen itineraries on
demand, the provider supports request-time pricing more reliably than controlled
collection, measured batch freshness misses the product objective, or another
consumer establishes a justified latency SLO.
