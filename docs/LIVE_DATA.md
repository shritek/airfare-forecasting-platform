# Live Fare Data

## Status

As of 2026-08-27, SerpApi Google Flights is the preferred provider for a
controlled pilot, subject to the hard prerequisites in
[ADR-0002](decisions/0002-serpapi-live-fare-pilot.md). This is not approval to
start unattended collection yet.

The selection is intentionally narrow: it chooses the best provider for learning
whether stable trajectories can be collected, not the permanent production data
source. Provider responses and terms must be rechecked before expanding usage.

## Evaluation Criteria

The provider comparison prioritizes:

1. explicit suitability for automated searches;
2. live, bookable total prices rather than cached route estimates;
3. segment-level fields sufficient to reconstruct itinerary identity;
4. fare-product fields sufficient to avoid comparing unlike products;
5. a self-service and cost-capped access path;
6. transparent quotas, failures, and request accounting;
7. permission to retain private raw observations and create derived ML artifacts;
8. useful US domestic route and carrier coverage; and
9. an operational model compatible with scheduled research collection.

No public result is treated as legal advice. Applicable account terms and written
provider confirmations govern over this summary and must be retained privately
with the provider access record.

## Provider Comparison

| Provider | Strengths | Blocking or material limitations | Decision |
| --- | --- | --- | --- |
| SerpApi Google Flights | Immediate automated access; broad Google Flights results; structured flight numbers, airports, timestamps, carrier, class, price, filters, `no_cache`, and Account API quota state; 250 successful searches/month are free | Scraped metasearch rather than an airline/GDS offer API; less explicit fare-basis, tax, and product detail; accuracy is not warranted; customer remains responsible for downstream data use | Preferred conditional pilot |
| Amadeus Self-Service | Official travel API; self-service test and production environments; pay-as-you-go with a monthly free quota; rich segment, total/base price, fare-basis, booking-class, cabin, baggage, and availability fields | Test data is limited rather than live; production terms and exact quota are account-specific; published Self-Service data excludes American, Delta, British Airways, low-cost carriers, negotiated fares, and special rates | Structured-offer fallback |
| Duffel Flights | Live bookable offers; strong slices, segments, operating-carrier, cabin, total/base/tax, conditions, and expiry fields | Commercial booking product; fair-use model measures search-to-order ratio; current pricing charges $0.005 per excess search above 1500 searches per order, so a collector that intentionally creates no orders is misaligned | Reject for research collector |
| Skyscanner Flights Live Prices | Broad real-time metasearch supply and structured itinerary/pricing options | Partner/account-manager access; usage guidelines require user-generated live-price calls and explicitly prohibit automated calls without user action; look-to-book expectations conflict with scheduled collection | Reject for automated collection |
| Airline-direct NDC | Authoritative branded offers, fare rules, taxes, availability, and product identity | Production access generally targets accredited travel sellers and requires carrier-specific onboarding, certification, contracts, and permitted-use review | Revisit if a carrier grants research access |
| Direct Google Flights scraper | No vendor call charge and broad visible supply | Google machine-readable instructions disallow flight-search result paths; no supported data contract; browser, anti-bot, proxy, parsing, and silent-drift burden | Reject without explicit authorization |

## Primary Evidence

### Amadeus

- The [Self-Service FAQ](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/faq/)
  describes independent-developer access, test versus live production data,
  monthly free quota plus paid overage, production-specific terms, and carrier/
  fare coverage exclusions.
- The [official Flight Offers Search specification](https://github.com/amadeus4dev/amadeus-open-api-specification/blob/main/spec/json/FlightOffersSearch_v2_swagger_specification.json)
  includes segment departure/arrival timestamps, marketing and operating carrier,
  flight number, aircraft, total/base/grand-total price, fare basis, booking class,
  cabin, baggage, and bookable-seat fields.
- The [Self-Service quick start](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/quick-start/)
  documents OAuth client credentials and the separate test and production hosts.
- The [pricing guide](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/pricing/)
  states that production retains a monthly free quota and uses paid overage; the
  exact Flight Offers Search allowance must be captured from the account workspace.

### Duffel

- The [Offers reference](https://duffel.com/docs/api/offers/get-offers) defines
  bookable total/base/tax amounts, slices and segments, created/expiry timestamps,
  and explicitly warns that airline offers and prices can change.
- The [pricing page](https://duffel.com/pricing) defines the 1500:1 search-to-order
  threshold and $0.005 charge for each excess search.
- The [Services Agreement](https://duffel.com/services-agreement) treats excessive
  search-to-order ratios as fair-use concerns and frames use around offering travel
  services to customers.

### Skyscanner

- The [Flights Live Prices quick start](https://developers.skyscanner.net/docs/flights-live-prices/quick-start)
  describes real-time partner prices and the create/poll session flow.
- The [usage guidelines](https://developers.skyscanner.net/docs/getting-started/usage-guidelines)
  require user-generated Live Pricing calls, prohibit automated calls without user
  action, and expect a meaningful share of searches to produce booking deeplink
  clicks.
- [Rate limits](https://developers.skyscanner.net/docs/getting-started/rate-limits)
  are account-manager-controlled even though standard limits are published.

### SerpApi

- The [Google Flights API reference](https://serpapi.com/google-flights-api)
  documents structured airports, timestamps, carrier, flight number, cabin, price,
  itinerary filters, and its scraped-Google-Flights source.
- [Pricing](https://serpapi.com/pricing) currently lists 250 free searches/month,
  $25 for 1,000, $75 for 5,000, $150 for 15,000, and $275 for 30,000.
- The [Account API](https://serpapi.com/account-api) reports the plan limit,
  successful searches used and remaining, renewal date, and throughput state; its
  calls do not consume search quota.
- The [general search API](https://serpapi.com/search-api) documents `no_cache=true`
  to force a fresh fetch instead of accepting its one-hour cache.
- The [terms](https://serpapi.com/legal) disclaim result accuracy, leave downstream
  legality with the customer, and exclude Free, Starter, and Developer plans from
  the legal shield described for higher recurring plans.

### Airline-direct and Google access

- [American's NDC overview](https://www.exploreamerican.com/globalsales/ndc-overview/)
  describes direct-connect shopping but requires an ARC/IATA-accredited agency and
  estimates a multi-month integration.
- [Alaska's NDC registration](https://www.alaskaair.com/en-au/content/ndc/registration)
  requires application, test approval, certification, contracts, and separate
  production enablement.
- [Google's terms](https://policies.google.com/terms?hl=en-US) restrict automated
  access that violates machine-readable instructions, while
  [Google's robots file](https://www.google.com/robots.txt) disallows its travel
  flight-search result paths.

These pages were reviewed on 2026-08-27. Pricing, product coverage, and legal terms
are volatile and must be checked again when credentials are provisioned and before
any paid plan or expanded collection is enabled.

## SerpApi Qualification Gates

The collector must remain disabled until all of the following are recorded in a
private access checklist and non-secret aggregate status is reflected in project
documentation:

- SerpApi support or account-specific terms confirm that the project may privately
  retain raw Google Flights responses and create derived features, labels,
  metrics, and models;
- raw observations and derived artifacts will not be publicly redistributed;
- exactly one project account is used; accounts or keys are never rotated to
  circumvent the free allowance;
- the Account API confirms a 250-search free monthly limit, the renewal date, and
  at least 225 searches remaining before the cohort is enrolled;
- account documentation or a probe confirms that `deep_search=true` still
  consumes exactly one successful-search credit;
- no paid plan, extra credits, or automatic paid renewal is enabled;
- local total-attempt and successful-search caps are both 225, preserving at
  least 25 successful searches as a safety reserve;
- a live route probe confirms usable offers on at least four of five candidate
  routes;
- returned payloads contain the segment identity, travel-class, price, search
  metadata, and source fields required by the raw contract below; and
- manual samples establish what the displayed price represents and whether the
  fixed non-basic-economy filter produces sufficiently comparable observations.

If terms prohibit retention/derived use, price meaning remains ambiguous, the
free quota is too small, or route coverage fails, do not weaken the gates. Update
ADR-0002 and evaluate Amadeus or a provider with explicit written permission.

## Pilot Search Cohort

The initial candidate route set is:

- `SFO -> EWR` (transcontinental);
- `LAX -> ORD` (long-haul hub market);
- `DEN -> IAD` (hub-to-hub);
- `SEA -> SFO` (short West Coast); and
- `BOS -> MIA` (longer leisure/business mix).

At enrollment, materialize five exact departure dates per accepted route at
approximately 14, 30, 45, 60, and 90 days ahead. Persist those ISO dates in the
cohort manifest. Never recompute an enrolled date from a moving horizon: repeated
observations must refer to the same departures and flights.

Search once daily at 15:00 UTC for one adult, one-way, economy travel in USD. A
single cadence is enough to evaluate identity and 1/3/7-day labels while limiting
cost. Multiple daily observations require a later decision based on pilot value.

The qualification probe uses one departure date for each candidate route. If the
provider gates pass, collect the 25 accepted route/date cells for eight days. With
five probe calls this is 205 scheduled searches before retries. The executable
caps are 225 total Google Flights attempts and 225 provider-reported successful
searches per monthly cycle. SerpApi documents that only successful searches count
toward quota, but every attempt consumes the stricter local attempt budget.
Unknown quota, renewal-cycle, or local-budget state is a hard failure.

## Query Contract

Each request fixes:

- `engine=google_flights`;
- exact origin and destination airport codes;
- exact departure date;
- one adult;
- one-way itinerary (`type=2`);
- economy travel class (`travel_class=1`);
- US market and English locale (`gl=us`, `hl=en`);
- USD currency;
- `exclude_basic=true` to reduce fare-product mixing for US domestic economy;
- `show_hidden=true` so the returned universe is not limited to initially visible
  options;
- `deep_search=true` so results follow SerpApi's browser-similarity mode; and
- `no_cache=true` so each successful call is a new provider fetch.

Search configuration is versioned. Changing passenger count, cabin, currency,
market, locale, route, departure date, basic-fare filter, hidden-result behavior,
or deep-search behavior creates a new search-cell version rather than mutating
historical meaning.

The observed price is initially defined as SerpApi's displayed itinerary price
under this exact query, not an airline-filed fare, verified booking price, base
fare, or tax breakdown. `price_insights` and `price_history` are retained as
untrusted source metadata and cannot create labels or trajectory features until a
separate semantics and point-in-time audit approves them.

## Immutable Raw Observation Envelope

Each attempt writes one immutable envelope containing:

- envelope schema version and provider/API version;
- environment, cohort ID, search-cell ID/version, run ID, and attempt number;
- scheduled, request-start, and response-received UTC timestamps;
- sanitized request parameters with no token, key, or secret;
- HTTP status, provider request/correlation ID when available, latency, and error
  classification;
- sanitized SerpApi search metadata, including search ID, provider creation and
  processing timestamps, status, and result buckets;
- response content type, byte count, SHA-256 digest, and unmodified raw payload;
- local attempt counters plus sanitized Account API quota snapshots before and
  after the run; and
- collector Git commit and configuration digest.

Persist unsuccessful attempts as metadata even when no response body exists.
Retries never overwrite prior attempts. Raw payloads stay private and outside Git;
only aggregate, non-sensitive pilot reports may be committed.

## Retry, Idempotency, and Safety

- Run one collector instance for the pilot; concurrency is one.
- Query the Account API before every run and fail closed if it is unavailable,
  reports an unexpected account/plan/renewal cycle, or leaves insufficient quota.
- Do not retry authentication, validation, or other deterministic 4xx errors.
- Retry 429 and transient 5xx/network failures at most twice with exponential
  backoff and jitter, respecting `Retry-After`.
- Count every attempt before sending it so a crash cannot bypass the budget cap.
- Reconcile successful-search usage with the Account API after every run; a
  mismatch stops subsequent runs for investigation.
- Use `(provider, environment, cohort_id, search_cell_id, scheduled_at_utc,
  attempt_number)` as the immutable attempt identity.
- Never log access tokens, client secrets, authorization headers, or full
  credential-bearing URLs.
- Stop the run on unknown budget state, terms/checklist mismatch, repeated auth
  failures, schema-version mismatch, or unexpected paid usage.

## Pilot Exit Criteria

Proceed beyond the eight-day pilot only if:

- at least four accepted routes return non-empty offers on six of eight days;
- at least 50 reconstructed itineraries appear on three or more distinct
  observation dates and at least 20 appear on seven or more dates;
- at least 95% of scheduled cells produce a persisted success or classified
  failure envelope;
- segment identity, travel-class, result-bucket, and displayed-price fields are
  parseable without silent coercion;
- repeated manual samples show that the fixed query produces a sufficiently
  comparable non-basic-economy price or quantify why it does not;
- duplicate and changing-offer behavior can be explained from retained raw data;
- no credential, terms, quota, or paid-usage control fails; and
- actual provider coverage limitations are documented in the aggregate report.

These are pilot continuation gates, not model-quality claims. Failure should lead
to a provider, cohort, or identity review rather than lowering thresholds after
seeing the outcome.
