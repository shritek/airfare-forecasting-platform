# ADR-0002: Conditional Amadeus Live-Fare Pilot

Date: 2026-08-27
Status: Proposed

## Context

Current fare trajectories cannot be backfilled, so collection should begin early.
The provider must support automated live searches, produce fields sufficient for
stable itinerary and fare-product matching, permit private longitudinal retention
and derived ML use, and fit a personal-project budget.

Public documentation was compared for Amadeus Self-Service, Duffel Flights,
Skyscanner Flights Live Prices, and SerpApi Google Flights. None is perfect:
Amadeus has carrier/fare exclusions and account-specific production terms; Duffel
expects bookings; Skyscanner prohibits automated live-price calls without user
action; and SerpApi places downstream-use responsibility on the customer while
providing less explicit fare-product structure.

## Decision

Use Amadeus Self-Service Flight Offers Search as the preferred provider for a
small live-fare qualification pilot, but enable no unattended collection until
every production-terms, retention, quota, budget, payload, and route-coverage gate
in [the live-data contract](../LIVE_DATA.md) passes.

The initial budget is zero paid API calls. The collector must enforce a local cap
no greater than 90% of the verified free quota and no greater than 225 attempts.
The first cohort observes at most five routes by five fixed departure dates once
per day for eight days after a five-call route probe.

This decision does not approve Amadeus as the permanent production provider and
does not claim that its observations represent the full US domestic market.

## Alternatives Considered

### Duffel Flights

Duffel has excellent bookable-offer structure, but its commercial model expects
orders and charges for searches beyond a 1500:1 search-to-order ratio. A research
collector intentionally creating no orders conflicts with that operating model.

### Skyscanner Flights Live Prices

Skyscanner provides broad real-time metasearch content, but its usage guidelines
state that live-pricing calls must be user-generated and that automated calls do
not occur. Scheduled longitudinal collection would violate the documented use
pattern.

### SerpApi Google Flights

SerpApi is accessible, broad, and relatively inexpensive. It is the leading
fallback, but its results are scraped metasearch data with weaker fare-product
detail. Its terms leave downstream legality and result risk with the customer,
and lower-cost plans do not include its legal shield. Written confirmation of the
intended retention and derived-model use is required before choosing it.

### Delay all live collection

This avoids provider cost and legal uncertainty but permanently loses 2026
trajectory history. A tightly gated qualification pilot provides useful evidence
without committing to a long-running integration.

## Rationale

Amadeus is the best technical fit among providers whose public documentation was
reviewed. Its offer schema exposes segment times, marketing and operating carrier,
flight number, aircraft, total/base/grand-total prices, published fare type, fare
basis, booking class, cabin, baggage, and bookable-seat count. Those fields allow
identity and fare comparability to be investigated rather than guessed.

Self-service onboarding and a production free quota support a small pilot without
a booking workflow or an intentionally poor search-to-book ratio. Hard gates are
necessary because the public FAQ excludes major carriers and low-cost content,
the test environment is not complete live data, exact pricing is account-specific,
and production terms are delivered during activation.

## Consequences

- The next implementation may target one provider and one raw envelope instead of
  inventing a premature multi-provider abstraction.
- A user-managed Amadeus account, production credentials, and private terms review
  are prerequisites; secrets never enter Git.
- Candidate routes may be rejected by the live probe and are not guaranteed to
  represent American, Delta, Southwest, other low-cost carriers, or negotiated
  fares.
- A local request ledger and fail-closed budget guard are correctness requirements,
  not optional monitoring.
- Provider offer IDs are not assumed stable across searches; itinerary and
  fare-product identity will be reconstructed and measured from segment/fare data.
- If any gate fails, the collector remains disabled and this ADR must be updated
  before another provider is integrated.

## Revisit When

Reconsider when production terms do not permit private retention or derived ML
use; the free quota cannot support the bounded pilot; fewer than four candidate
routes return usable offers; carrier exclusions make the data unrepresentative for
the intended experiment; pilot trajectory gates fail; prices materially disagree
with independent checks; costs or product terms change; or a provider offers
explicit research/ML rights with better US coverage and comparable identity fields.
