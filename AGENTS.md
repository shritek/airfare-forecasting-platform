# AGENTS.md

## Purpose

Build a portfolio-quality, production-style airfare forecasting platform that can
support a defensible BUY/WAIT recommendation. The system must model fare changes
over time from repeated observations of the same itinerary; it is not a static
ticket-price estimator.

## Start Here

- [README.md](README.md): project overview and current status
- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md): goals, constraints, and
  engineering principles
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): intended system boundaries and
  current architectural posture
- [docs/ML_DESIGN.md](docs/ML_DESIGN.md): target, leakage, evaluation, and model
  methodology
- [docs/DATA.md](docs/DATA.md): candidate datasets and required audits
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): evidence gates and
  ordered delivery plan
- [docs/decisions/README.md](docs/decisions/README.md): architecture decision
  record (ADR) index and process

## Non-Negotiable Constraints

- Use only information available at prediction time. Treat temporal leakage as a
  correctness defect.
- Build labels from longitudinal itinerary observations, not unrelated route
  prices.
- Prefer time-based evaluation and compare ML models with useful naive and
  heuristic baselines.
- Do not combine data sources until semantics, identity, temporal coverage, and
  licensing have been audited.
- Prefer the smallest architecture that meets reliability, reproducibility, and
  cost goals. Batch and scale-to-zero services are the default posture.
- Never commit credentials, downloaded proprietary data, or large generated
  artifacts.
- Keep models traceable to code, configuration, data snapshot, and training run.

## Working Agreement

Before changing code or design, inspect the current branch, repository status,
relevant docs, and open work. Make each meaningful change on a descriptive branch
from current `main`, with tests and documentation appropriate to its scope. Create
one reviewable PR, then wait for review before starting dependent work. Do not
merge or force-push unless explicitly requested.

Before the first commit in a work session, verify `git config user.name`,
`git config user.email`, and `gh auth status`. Use the existing user identity and
the user's authenticated GitHub account. Stop if identity is missing or the active
account is unexpected. Never override author/committer identity, modify global Git
identity, or add AI/tool authorship, co-author, or generation-attribution trailers.

Keep commits coherent and descriptive. PR descriptions should explain What, Why,
meaningful design decisions, operation/data flow where useful, exact Validation,
Risks / Limitations, and Review Focus. Avoid mixing unrelated work or building a
long stack of unreviewed dependent PRs.

Record meaningful ML, data, architecture, and infrastructure choices as ADRs in
`docs/decisions/`. Update affected docs in the same PR. Do not create speculative
scaffolding or placeholder documentation.

## Validation

The repository does not yet have an implementation toolchain. For documentation-
only changes, inspect rendered Markdown, verify links, and run:

```bash
git diff --check
```

Add authoritative setup, test, lint, type-check, and infrastructure commands here
when the corresponding tooling is introduced.
