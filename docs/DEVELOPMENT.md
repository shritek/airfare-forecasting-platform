# Development

## Toolchain

The project uses Python 3.14 and `uv` for Python installation, dependency locking,
virtual environments, and package builds. Python 3.14 was selected after resolving
and installing a representative data/ML stack (NumPy, pandas, PyArrow, Polars,
DuckDB, scikit-learn, XGBoost, LightGBM, MLflow, Pydantic, and boto3) under Python
3.14. The project is an
installable `src`-layout package so tests and jobs exercise the same import
boundary that built artifacts expose.

Development validation uses:

- Ruff for formatting, import ordering, and linting;
- mypy in strict mode for static type checking; and
- pytest for behavioral and integration tests.

This is a small, reversible toolchain choice rather than an architecture decision,
so it is documented here rather than in an ADR. Add a tool only when it covers a
distinct validation or delivery requirement.

## Prerequisite

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/). The
repository declares its supported `uv` range and Python minor version. `uv` will
download the required Python interpreter when it is not already available.

The representative stack resolved and installed successfully on Python 3.14.6.
XGBoost and LightGBM also require an operating-system OpenMP runtime; on macOS,
installing `libomp` is a separate host prerequisite and is not a Python-version
compatibility signal.

## Setup

From the repository root:

```bash
uv sync --locked --dev
```

Do not install project dependencies globally. Commit `uv.lock` whenever declared
dependencies change.

## Validation Commands

Run the same checks used by CI:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
uv build
git diff --check
```

To apply formatting locally, run `uv run ruff format .`, then rerun the complete
validation set.

## Repository Boundaries

- Production Python belongs under `src/airfare_forecasting/`.
- Tests belong under `tests/` and should mirror important package boundaries.
- Large or restricted datasets, model artifacts, experiment runs, credentials,
  and local environment files are ignored and must not be committed.
- Small synthetic fixtures may be committed under `tests/fixtures/` when they are
  necessary to test data behavior.

The initial package contains no airfare domain abstractions. Those will follow
only after provider and source-schema evidence supports their contracts.
