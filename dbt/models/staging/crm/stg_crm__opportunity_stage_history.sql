select
    history_id,
    opportunity_id,
    stage,
    amount_usd,
    changed_at
from {{ source('raw_crm', 'opportunity_stage_history') }}
