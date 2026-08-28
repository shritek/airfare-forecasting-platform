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

## Related Modeling Work

The Hugging Face project
[`matanzig/flight-price-prediction`](https://huggingface.co/matanzig/flight-price-prediction)
is useful related work for Expedia 2022 data handling, EDA hypotheses, and static
fare-estimation comparisons. It does not solve this project's longitudinal target:
it predicts the current `totalFare` and classifies current price tiers rather than
forecasting a later fare for the same itinerary.

Its reported metrics are not baselines for this project. The published notebook
uses random row splits and constructs cluster features by fitting K-means with
`totalFare` before using those clusters in downstream supervised models. That
introduces target information into the features and cannot support a leakage-safe
claim about future performance. We may reproduce useful hypotheses under our own
time-based evaluation, but will not reuse its serialized models or assume that the
repository's MIT license establishes rights to the underlying Expedia dataset.

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
