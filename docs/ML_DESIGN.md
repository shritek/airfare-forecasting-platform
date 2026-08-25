# ML Design

## Problem Framing

The model consumes an itinerary observation at search time and forecasts a later
fare outcome. The product may use either:

- classification: probability the fare increases (or decreases) within horizon
  `N`; or
- regression: future fare, absolute change, or percentage change after `N` days.

We will begin with one target and one horizon. Selection depends on exact-match
label coverage, outcome censoring, price-change distribution, calibration needs,
and usefulness of the resulting recommendation—not headline model metrics.

## Label Contract

A label must be computed only from a later observation of the same stable
itinerary under documented matching and time-tolerance rules. The label builder
must distinguish at least:

- an observed unchanged or changed fare;
- a missing scrape or source failure;
- an itinerary that disappeared or sold out; and
- an itinerary whose relevant attributes changed.

Those cases must not be collapsed into an assumed price movement. The exact
censoring policy is an evidence-gated decision.

## Leakage and Splitting

Features must be reproducible from data whose event time is no later than the
prediction timestamp. Rolling statistics are itinerary-scoped and left-looking;
aggregates need an explicit fit window. Future fare, future availability, and
statistics computed over the full dataset are prohibited.

Evaluation uses chronological train, validation, and held-out test windows with a
gap when feature or label horizons make one necessary. The audit must also check
whether the same departures crossing split boundaries create leakage. Random row
splits are not an acceptable default.

## Baselines and Initial Model

Required baselines are a no-change forecast, a booking-window/route historical
movement heuristic, and a simple statistical model. XGBoost is the leading first
nonlinear candidate for mixed tabular features, but it is not selected until the
target and data representation are established. LightGBM and CatBoost are useful
challengers only when the comparison controls data, features, and tuning budget.
Deep temporal models require evidence that tabular approaches leave meaningful
value unexplained.

## Evaluation

Regression candidates should report MAE and RMSE, with relative-error metrics only
where their behavior near small denominators is acceptable. Classification should
report PR-AUC, ROC-AUC, precision/recall tradeoffs, and calibration. Product
evaluation must include decision costs or regret associated with BUY versus WAIT.

Metrics should be sliced by route, airline, booking horizon, fare bucket, and
other sufficiently supported cohorts. Every result must include label coverage,
sample counts, temporal window, dataset version, and baseline deltas.

## Model Governance

Training runs will capture the Git commit, immutable dataset reference, feature
configuration, parameters, metrics, artifacts, and duration. The production
champion publishes recommendations; challengers may produce shadow predictions.
Promotion occurs only after eligible delayed labels arrive and explicit aggregate,
slice, calibration, and operational gates pass. Thresholds remain unresolved.
