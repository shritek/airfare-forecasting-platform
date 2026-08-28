# ADR-0002: Conditional SerpApi Live-Fare Pilot

Date: 2026-08-27
Status: Proposed

## Context

Current fare trajectories cannot be backfilled, so collection should begin early.
The provider must support automated live searches, produce fields sufficient for
stable itinerary matching, permit private longitudinal retention and derived ML
use, and fit a personal-project budget.

Public documentation was compared for SerpApi Google Flights, Amadeus Self-
Service, Duffel Flights, Skyscanner Flights Live Prices, direct Google Flights
scraping, and airline-direct NDC access. None is perfect. SerpApi provides the
lowest-friction automated pilot and broad US results, but it is scraped metasearch
data with weaker fare-product semantics and customer-held downstream-use risk.

## Decision

Use SerpApi Google Flights as the preferred provider for a small qualification
pilot, but enable no unattended collection until every retention, derived-use,
quota, budget, payload, price-semantics, and route-coverage gate in
[the live-data contract](../LIVE_DATA.md) passes.

Use exactly one project account. The initial budget is zero paid API calls. The
collector must fail closed at no more than 225 total Google Flights attempts and
225 quota-counted successful searches in a monthly cycle, preserving at least 25
of the documented 250 free searches. The first cohort observes at most five
routes by five fixed departure dates once per day for eight days after a five-call
route probe.

This decision does not approve SerpApi as the permanent production provider, does
not authorize multiple accounts to bypass quotas, and does not treat Google
Flights results or price-history fields as authoritative airline ground truth.

## Alternatives Considered

### Amadeus Self-Service

Amadeus exposes stronger fare-basis, booking-class, base/tax, cabin, baggage, and
operating-carrier detail. It remains the leading fallback if SerpApi's displayed
prices cannot be compared consistently. It was not selected first because its
production terms and exact quota are account-specific and its published coverage
excludes several major and low-cost carriers needed for a US domestic pilot.

### Duffel Flights

Duffel has excellent bookable-offer structure, but its commercial model expects
orders and measures search-to-order ratio. A research collector intentionally
creating no orders conflicts with that operating model.

### Skyscanner Flights Live Prices

Skyscanner provides broad real-time content without a published per-call price,
but its usage guidelines require live-price calls to be user-generated and expect
booking deeplink traffic. Scheduled longitudinal collection conflicts with that
documented use pattern unless Skyscanner grants explicit written permission.

### Airline-Direct NDC APIs

Direct airline shopping offers would provide authoritative fare products, but
production access generally targets accredited travel sellers and requires
carrier onboarding, certification, and contracts. Each integration would cover
only that carrier. Airline-direct access remains attractive if a carrier grants
explicit low-volume research and derived-ML permission.

### Direct Google Flights Scraping

A custom scraper avoids per-call vendor fees but would own browser automation,
anti-bot failures, proxies, undocumented interfaces, and silent extraction drift.
Google's terms restrict automated access contrary to machine-readable
instructions, and its current robots file disallows flight-search result paths.
This is not an acceptable production source without explicit authorization.

### Delay All Live Collection

This avoids provider cost and data-use uncertainty but permanently loses 2026
trajectory history. A tightly gated free-tier pilot provides evidence without
committing to a long-running integration.

## Rationale

SerpApi is the fastest and least expensive way to test the project's immediate
unknown: whether repeated Google Flights results contain enough stable segment
identity and price semantics to construct useful trajectories. Its documented
response contains airports, segment timestamps, carrier, flight number, travel
class, duration, price, result metadata, and filters. The API explicitly supports
fresh fetches rather than cached results.

The published free tier allows 250 successful searches per month. The bounded
pilot schedules 205 searches before retries, and SerpApi's free Account API can
report quota state without consuming search credits. A conservative local attempt
cap and provider-reported successful-search cap prevent retries or state errors
from silently exhausting the allowance.

Hard gates remain necessary. SerpApi does not expose the same fare-basis and tax
detail as an airline offer API, default results may differ from the Google Flights
browser, and its terms disclaim result accuracy and leave downstream legality with
the customer. The pilot therefore measures comparability rather than assuming it.

## Consequences

- The next implementation targets one provider and one raw envelope rather than
  inventing a premature multi-provider abstraction.
- A user-managed SerpApi key is required; it never enters Git or logs.
- Every fresh search uses `no_cache=true`; cached results are not valid new
  observations.
- Fixed US domestic searches use consistent locale, currency, passenger, cabin,
  basic-economy, hidden-result, and deep-search settings.
- SerpApi search IDs, booking tokens, and departure tokens are treated as
  ephemeral source metadata, not stable itinerary identity.
- Google `price_history` and `price_insights` may be retained as source fields but
  cannot create labels or historical features without a separate semantics audit.
- A one-account request ledger, Account API quota check, and fail-closed budget
  guard are correctness requirements, not optional monitoring.
- If any gate fails, the collector remains disabled and this ADR must be updated
  before Amadeus or another provider is integrated.

## Revisit When

Reconsider when SerpApi does not permit private retention or derived ML use; fare-
product ambiguity prevents comparable trajectories; stable itinerary identity
cannot be reconstructed; fewer than four candidate routes return usable results;
the pilot trajectory gates fail; manual price checks materially disagree; costs,
coverage, or product terms change; an airline grants suitable direct NDC access;
or another provider offers clearer research rights and comparable US coverage.
