# Metric Definitions

Single source of truth for how every metric in this project is calculated.
Anyone — human or Claude — answering a question from this data should use
these definitions, not re-derive their own.

## Delivery & pacing

- **Delivery rate** = delivered impressions ÷ booked impressions (CPM lines),
  or delivered impressions ÷ guaranteed views (Flat Fee lines). Only
  meaningful once a flight has ended (`is_flight_ended = true`); an
  in-flight line naturally reads under 100%.
- **Under-delivered** = an ended line with delivery rate < 90%
  (`is_under_delivered` in `mart_campaign_performance`).
- **Effective CPM** = booked cost ÷ (delivered impressions / 1,000). Differs
  from `booked_cpm` when delivery rate isn't 100% — under-delivery makes the
  effective CPM the client actually paid *higher* than the rate card.

## In-flight pacing (`mart_line_pacing`)

- Covers CPM lines live on the as-of date. Flat Fee branded content is
  excluded: its views are front-loaded by design, so even pacing doesn't apply.
- **Expected to date** = booked impressions × days elapsed ÷ flight days
  (even pacing). Delivery is counted through the day *before* the as-of date.
- **Pacing index** = delivered to date ÷ expected to date. 1.00 = on pace.
- **Daily run rate** = average daily impressions over the trailing 7 days.
- **Projected delivery rate** = (delivered to date + run rate × days
  remaining) ÷ booked impressions.
- **Projected make-good** = (1 − projected delivery rate) × booked cost, only
  when the projection is under 95% — the same rule finance applies at wrap.
- **Pacing status**: `Too early` (<3 days in), `At risk` (projected <95%),
  `Over-pacing` (projected >110%), otherwise `On track`.

## Household measurement (`mart_audience_measurement`)

All household-level (mock iSpot-style vendor feed). No child-level data
exists in the hub — COPPA restricts profiling under-13s, not household-level
measurement or identifying the adult co-viewer.

- **Average frequency** = measured impressions ÷ households reached.
- **Incremental reach %** = households NOT also reached by the advertiser's
  linear TV buy ÷ households reached.
- **Cord-free household %** = households that never had or cut pay TV ÷
  households reached.
- **Co-viewing impression %** = impressions with an adult co-viewing ÷
  measured impressions. The parent is the economic buyer.
- **Measurement gap %** = 1 − vendor impressions ÷ ad server impressions.
  1–5% is normal (invalid-traffic filtering, unmatched devices).
- **Delivered spend** = min(delivered, booked impressions) × booked CPM ÷ 1,000.
- **On-target CPM** = delivered spend ÷ (impressions in households with kids
  ÷ 1,000). What an advertiser really pays per thousand family impressions.
- **Parent co-viewing CPM** = delivered spend ÷ (impressions with an adult
  co-viewer ÷ 1,000).
- **Third-party on-target CPM** = category benchmark CPM ÷ 0.42. The 0.42 is
  CIMM's July 2026 estimate of how often third-party data correctly
  identifies a household with kids (dbt var `third_party_kids_hh_accuracy`).
- **On-target CPM savings %** = 1 − on-target CPM ÷ third-party on-target CPM.
- Aggregate ratios by summing numerators and denominators (e.g. total spend ÷
  total on-target impressions), not by averaging line-level ratios.

## Video engagement

- **VTR (View-Through Rate)** = completed views ÷ video starts. Measures how
  much of the ad's guaranteed content viewers actually watched.

## Pipeline

- **Weighted pipeline value** = deal amount × stage probability ÷ 100.
  Standard CRM convention; always use this (not raw `amount_usd`) when
  summarizing "how much pipeline do we have," since it discounts for
  likelihood to close.
- **Win rate** = won deals ÷ (won + lost) deals, **closed deals only**. Open
  deals are excluded from the denominator — an open deal hasn't won or lost
  yet.
- **Sales cycle days** = close_date − created_date.
- **Stale open deal** = a deal still open (`is_closed = false`) whose
  `close_date` has already passed. A pipeline-hygiene flag, not a metric
  to report as-is — surface it as "needs cleanup," not as lost revenue.

## Brand lift

- **Lift (points)** = exposed % − control %, on the same metric (e.g. Aided
  Awareness). Reported in percentage points, not relative %.
- Studies exist only for a subset of larger, completed campaigns — don't
  treat `mart_brand_lift_summary` as covering every deal, and don't
  extrapolate a category's lift from a handful of studies without saying so.

## Finance

- **Net amount** = gross amount − credit amount. Credits are make-good
  adjustments for under-delivered CPM lines.
- **Days to pay** = paid_date − invoice_date. Only calculable for paid
  invoices (`is_paid = true`).
- **Billed vs. booked variance** = billed net revenue − ad-server booked
  cost, at the deal level. Large negative variance usually traces back to
  make-good credits.

## Market intel

- YouTube channel/video stats (`mart_market_intel`) are **real, live public
  data** from the YouTube Data API — not synthetic. Everything else in this
  project (CRM, pre-sale, ad server, household measurement, research,
  finance, market benchmarks) is synthetic and fictional.
- Category benchmarks (`stg_market__category_benchmarks`) are a synthetic
  stand-in for third-party market data — useful for demonstrating the
  comparison, not real Moonbug or industry figures.
- **Never use `comment_count` for anything** — comments are disabled on
  virtually all made-for-kids content, so this column is 0 or null across
  every channel in the dataset. It carries no signal. Use `like_count` ÷
  `view_count` ("like rate," likes per 1,000 views) as the engagement
  metric instead — see below.
- **Engagement rate** = like_count ÷ view_count (report as likes per 1,000
  views). This is the only real engagement signal available from public
  YouTube data for channels you don't own — comments are unusable (see
  above), and true watch-time/retention data isn't accessible for
  channels you don't own via the official API or any legitimate source.

## General conventions

- All dollar amounts are USD.
- "As of" date for any date-relative calculation (stale deals, days to pay,
  flight-ended checks) is the dbt var `as_of_date`, currently 2026-09-20 —
  not `CURRENT_DATE` — so results stay consistent regardless of when this
  is actually run.
- When a question could be answered from either a `stg_`, `int_`, or
  `mart_` model, prefer the `mart_` model — it's the cleanest, most
  documented, and most tested layer.