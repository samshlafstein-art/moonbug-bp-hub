# Template: Deal / Category Prioritization

Use when asked which deals, categories, or segments to focus on or walk
away from — "where should the team focus," "what should we deprioritize."

## Data to pull

1. Query `mart_category_win_rates` for the full category comparison: win
   rate, average sales cycle, average deal size, total won, open weighted
   pipeline.
2. If the question is about specific open deals rather than categories,
   pull `mart_pipeline_current` and cross-reference each deal's
   `account_category` against the category win rates.
3. Optionally check `mart_category_benchmarking` if pricing competitiveness
   is part of the "why" (e.g. a category where Moonbug prices above
   benchmark AND has a low win rate is a double warning sign).

## Structure of the answer

1. **The prioritization logic, stated up front**: what "good" looks like
   here — typically high win rate + short cycle + healthy deal size is
   worth leaning into; low win rate + long cycle, regardless of deal size,
   is a candidate to deprioritize. Say this explicitly so the reasoning is
   auditable, not just a ranked list.
2. **Categories/deals to lean into**: name 2-3, with the numbers that
   justify it (win rate, cycle time, pipeline value).
3. **Categories/deals to deprioritize**: name 1-2, with the numbers, and a
   plausible reason if the data suggests one (e.g. a common loss reason
   from `stg_crm__opportunities.loss_reason` — brand safety review,
   pricing, timing).
4. **Caveat**: win rate and cycle time are historical patterns, not
   guarantees — note if the sample size for a category is small enough
   that the numbers could be noisy (e.g. under ~15 closed deals).

## Tone

Be willing to make a clear recommendation — this template exists because
someone wants a decision, not just a data dump. State the call, then show
the numbers behind it.
