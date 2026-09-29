# Template: Post-Campaign Recap

Use when asked to summarize how a specific campaign, advertiser, or IP
performed.

## Data to pull

1. Query `mart_campaign_performance` filtered to the relevant
   `account_name`, `io_number`, or `ip`. Get every line item for the
   campaign(s) in scope.
2. If the campaign is finished (`is_flight_ended = true` on all lines),
   pull `mart_booked_vs_delivered_vs_billed` for the deal-level roll-up too.
3. If asked about brand impact, check `mart_brand_lift_summary` for a
   matching `io_number` — not every deal has a study.

## Structure of the answer

1. **Headline** (1-2 sentences): what ran, for whom, when, and the
   top-line delivery result (delivered vs. booked, in plain language —
   "delivered 94% of booked impressions" not just a raw number).
2. **By line item**: a short table or list — product, platform, booked vs.
   delivered, delivery rate, VTR where relevant. Call out any
   `is_under_delivered = true` lines explicitly and explain why (usually a
   FAST-channel pacing issue — see metrics.md).
3. **Brand impact** (if a lift study exists): report the lift in
   percentage points per metric, and name the vendor. If no study exists,
   say so rather than omitting the section silently — "no brand lift study
   was fielded for this campaign."
4. **Financial reconciliation** (if the campaign has ended): booked cost
   vs. billed net vs. collected, and whether any make-good credits applied.
5. **One takeaway** for the exec audience: what this campaign proves or
   what to watch next time (e.g. "FAST under-delivered again — worth
   flagging in the next renewal conversation").

## Tone

Write like a recap you'd actually send a client or present to leadership —
confident, specific, no hedging on numbers you have, honest about
limitations (missing studies, in-flight lines) where they exist.
