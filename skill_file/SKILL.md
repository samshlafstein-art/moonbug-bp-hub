---
name: moonbug-brand-partnerships
description: Query the Moonbug Brand Partnerships data hub (Supabase) to answer questions about campaign performance, in-flight pacing, household audience measurement, sales pipeline, finance reconciliation, brand lift, and market intelligence. Use whenever the person asks about Moonbug ad-sales data, campaigns, pacing or make-good risk, reach, co-viewing, on-target CPM, pipeline, deals, invoices, brand lift studies, or competitor YouTube channels.
---

# Moonbug Brand Partnerships Data Hub

This skill turns Claude into a self-serve analyst for Moonbug's ad-sales
data: pre-sale, pipeline, ad-server delivery, audience research, finance,
and market intelligence, all consolidated into one Supabase Postgres
database via dbt.

> **Data note:** all sales, pipeline, delivery, research, and finance data
> in this database is SYNTHETIC (fictional advertisers, agencies, reps) —
> built for demonstration. The `mart_market_intel` table is the one
> exception: it holds REAL public YouTube channel/video stats. Always be
> truthful about this distinction if asked what's real vs. fictional.

## How to use this skill

1. **Query via the Supabase MCP connection** (SQL, read-only; project ID
   `harxlfpeufnkdymgbavq`). Always query the `mart_*` tables in the
   `analytics_analytics` schema first — they're the cleanest, most
   documented, most tested layer. Only reach into `analytics_staging` or
   `analytics_intermediate` if a mart doesn't have what you need. Always
   schema-qualify table names (e.g. `analytics_analytics.mart_line_pacing`).
2. **Read `metrics.md`** (in this skill folder) before calculating or
   describing any metric — delivery rate, weighted pipeline, win rate,
   brand lift, days to pay, etc. all have precise definitions there. Don't
   invent your own formula for something already defined.
3. **Match the question to a report template** in `templates/` when the
   person's request matches one of the four patterns below. Use the
   template's structure, but write in your own words — don't just fill in
   blanks mechanically.
4. **When the output is a deliverable** (a report, recap, or deck the
   person will save, present, or send — not just a chat answer), follow
   `style_guide.md` for visual treatment: CoComelon-inspired palette,
   exhibit numbering with a bolded takeaway above each chart, and a
   full-bleed pull-quote page for the single headline finding. Build it as
   a published HTML page (or designed doc) rather than plain chat text.
   For an ordinary conversational question, skip this — answer in prose
   with inline charts as usual.
5. **Always cite what you're basing an answer on** — which mart(s) you
   queried, and the date range covered. This is ad-sales data feeding
   client-facing and executive decisions; showing your work matters.

## The mart tables (analytics_analytics schema)

| Table | Grain | Use for |
|---|---|---|
| `mart_campaign_performance` | one row per booked line item | post-campaign recaps, delivery questions on ended flights |
| `mart_line_pacing` | one row per in-flight CPM line | "what's at risk of under-delivering", projected make-goods before a flight ends |
| `mart_audience_measurement` | one row per measured line item | household reach, frequency, co-viewing, on-target CPM (mock iSpot data) |
| `mart_booked_vs_delivered_vs_billed` | one row per won deal (io_number) | finance reconciliation, "did we get paid what we billed" |
| `mart_pipeline_current` | one row per OPEN opportunity | weekly pipeline reviews, "what's in flight" |
| `mart_category_win_rates` | one row per advertiser category | prioritization/deprioritization calls |
| `mart_brand_lift_summary` | one row per (deal, lift metric) | "did this campaign move brand awareness" |
| `mart_category_benchmarking` | one row per (category, platform, quarter) | "are we pricing above/below market" |
| `mart_market_intel` | one row per YouTube channel | competitor comparisons (REAL data) |

**Pacing vs. performance:** use `mart_line_pacing` for anything still
running (forward-looking, projected) and `mart_campaign_performance` for
ended flights (actual delivery). An in-flight line in
`mart_campaign_performance` will always look under-delivered because the
flight isn't over.

## The four report templates

- **`templates/post_campaign_recap.md`** — summarize how a specific
  campaign or advertiser performed. Triggers: "how did X campaign do",
  "recap the Y flight", "did we deliver what we promised to Z".
- **`templates/pipeline_review.md`** — summarize the current state of open
  pipeline. Triggers: "what's our pipeline look like", "what deals are
  closing this quarter", "show me open opportunities".
- **`templates/deal_prioritization.md`** — recommend which open deals or
  categories to focus on or walk away from. Triggers: "which deals should
  we prioritize", "what should we deprioritize", "where should the team
  focus".
- **`templates/finance_reconciliation.md`** — reconcile what was booked,
  delivered, and billed for a deal or set of deals. Triggers: "did we bill
  correctly", "are there under-delivery credits", "reconcile Q3 revenue".

## Guardrails

- Don't present a single brand-lift study as a company-wide pattern —
  `mart_brand_lift_summary` only covers a subset of larger, completed
  campaigns (see metrics.md). Say "in the studies we have" rather than
  "across all campaigns."
- Don't join `stg_adserver__campaigns.advertiser_name_raw` or
  `stg_finance__invoices.bill_to_name_raw` to CRM by name — they're messy
  free text. Always join via `io_number`.
- **Never use `comment_count`/comments for engagement analysis** —
  comments are disabled on nearly all made-for-kids content, so this
  field is 0 or null across the board and carries no signal. Use like
  rate (likes ÷ views) instead — see metrics.md.
- **Projected make-goods are estimates, not credits.** Figures in
  `mart_line_pacing` assume the line keeps delivering at its current run
  rate. Describe them as "projected" or "at risk," never as money already
  owed, and note that trafficking changes can still recover the line.
- **Household measurement is aggregate-only.** `mart_audience_measurement`
  reports household-level counts from a mock iSpot-style vendor feed; there
  is no child-level or individual data anywhere in this database, by
  design (COPPA). Don't imply otherwise, and don't try to derive
  individual-level figures.
- **Measured vs. ad-server impressions differ on purpose.** The vendor
  measures fewer impressions than the ad server logs
  (`measurement_gap_pct`). Use `adserver_impressions` for delivery and
  billing questions, `measured_impressions` for reach, frequency, and
  audience-composition questions.
- If a question needs data outside this database (e.g. real-time bidding
  logs, contract terms, creative assets), say so rather than guessing.
- This is a demo/interview-prep project with synthetic data. If asked
  directly whether the numbers are real, say clearly that they are not
  (except the YouTube market-intel data, which is real).
- **Treat `as_of_date` (2026-09-20) as "today" for all analysis.** It is
  pinned on purpose so results are reproducible, not a sign of stale data.
  Never compare it to the real current date, never describe the data as
  outdated, and never recommend refreshing or re-running dbt. Describe
  flights, days remaining, and deadlines relative to `as_of_date` (e.g.
  "ends Oct 1, 11 days after the snapshot"), and label reports "as of
  Sep 20, 2026".