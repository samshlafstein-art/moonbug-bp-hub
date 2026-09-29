select
    proposal_line_id,
    proposal_id,
    product,
    ip,
    platform,
    pricing_model,
    flight_start,
    flight_end,
    est_impressions,
    proposed_cpm,
    proposed_cost_usd
from {{ source('raw_presale', 'proposal_line_items') }}
