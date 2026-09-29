# Template: Pipeline Review

Use when asked about the current state of open pipeline — a weekly review,
"what's closing this quarter," "show me open deals."

## Data to pull

1. Query `mart_pipeline_current` — it's already filtered to open deals only.
2. Apply whatever scope the person asked for: a specific rep (`owner_name`),
   region, category, or close-date window.
3. Cross-check `is_stale_open_deal` for any hygiene issues in scope.

## Structure of the answer

1. **Headline totals**: count of open deals, sum of `amount_usd` (raw
   pipeline), and sum of `weighted_amount_usd` (realistic pipeline). Always
   lead with the weighted number when someone asks "how much pipeline do
   we have" — the raw sum overstates reality (see metrics.md).
2. **By stage**: how many deals and how much weighted value sit in each
   stage (Prospecting → RFP Received → Proposal Sent → Negotiation).
   Negotiation-stage deals closing soon are usually the most actionable to
   call out by name.
3. **Notable deals**: the 3-5 largest weighted deals, named specifically
   (account, IP, amount, expected close date).
4. **Hygiene flags**: any `is_stale_open_deal = true` records in scope —
   name them and note they need a stage update or to be closed out.
5. **One takeaway**: is pipeline tracking toward the numbers the person
   probably cares about (a quarterly target, a category push), and
   anything that looks off (concentration in one account, a stage that's
   unusually full).

## Tone

Direct and scannable — this is a working document a rep or manager will
skim in a stand-up, not a narrative report. Lead with numbers, use short
lists over paragraphs where possible.
