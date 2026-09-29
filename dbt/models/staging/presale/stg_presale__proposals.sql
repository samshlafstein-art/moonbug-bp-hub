select
    proposal_id,
    opportunity_id,
    version,
    sent_date,
    total_budget_usd,
    status
from {{ source('raw_presale', 'proposals') }}
