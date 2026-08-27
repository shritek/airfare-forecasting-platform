# Architecture Decision Records

ADRs preserve meaningful data, ML, architecture, and infrastructure decisions so
they do not exist only in conversations or pull requests.

## Index

| ADR | Status | Summary |
| --- | --- | --- |
| [0001](0001-batch-first-inference.md) | Accepted | Use batch-first inference unless an online requirement emerges |
| [0002](0002-amadeus-live-fare-pilot.md) | Proposed | Use Amadeus for a gated live-fare qualification pilot |

## Process

Create an ADR in the PR that introduces or materially changes a significant
decision. Use the next four-digit number and a short kebab-case filename. Include:

- context and the uncertainty being resolved;
- the decision and realistic alternatives;
- evidence and rationale;
- positive and negative consequences; and
- concrete evidence that should trigger reconsideration.

Use `Proposed` while a decision is under review and `Accepted` once adopted.
Supersede rather than rewriting history when a later decision reverses an accepted
ADR; link both records and update this index.

Do not create ADRs for routine implementation details. Unresolved questions belong
in the implementation plan until evidence supports a decision.
