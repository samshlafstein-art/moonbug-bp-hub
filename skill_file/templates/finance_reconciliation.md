# Template: Finance Reconciliation

Use when asked to reconcile booked, delivered, and billed amounts — "did
we bill this right," "are there under-delivery credits," "reconcile Q3
revenue."

## Data to pull

1. Query `mart_booked_vs_delivered_vs_billed` filtered to the relevant
   deal(s), account(s), or time window (`flight_start`/`flight_end`).
2. For deal-level detail on WHY a variance exists, drop down to
   `mart_campaign_performance` for that `io_number` and look at
   `is_under_delivered` by line.
3. If the person asks about payment speed / collections rather than
   delivery, use `int_invoice_reconciliation` (via a mart or by asking the
   MCP connection to query that intermediate model directly) and group by
   `holding_company` for agency-level patterns.

## Structure of the answer

1. **Headline**: booked cost vs. billed net vs. collected, for the
   scope asked about. Lead with `billed_vs_booked_variance_usd` — if it's
   close to zero, say the deal reconciles cleanly; if it's meaningfully
   negative, that's the story.
2. **Explain the variance**: trace it to `has_under_delivered_line` and, if
   true, drill into which platform/line caused it (FAST lines are the most
   common culprit — see metrics.md). Quantify the make-good credit amount.
3. **Collections status**: how much has actually been collected
   (`collected_usd`) vs. billed, and `max_days_to_pay` if payment speed is
   relevant to the question.
4. **One takeaway**: whether this is a one-off or a pattern worth raising
   with the ad-ops or sales team (e.g. "this is the third FAST campaign
   this quarter with a credit — worth revisiting FAST forecasting in
   pre-sale").

## Tone

Precise and numbers-first — this template answers a "does this add up"
question, so show the actual dollar figures rather than rounding them away.
