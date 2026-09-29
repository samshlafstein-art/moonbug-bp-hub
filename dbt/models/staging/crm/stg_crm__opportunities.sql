select
    opportunity_id,
    trim(opportunity_name)                 as opportunity_name,
    account_id,
    agency_id,
    owner_id,
    stage,
    amount_usd,
    probability,
    lead_source,
    primary_ip,
    created_date,
    close_date,
    is_closed,
    is_won,
    loss_reason,
    io_number,
    -- data-quality flag: still open, but the close date has already passed
    (not is_closed and close_date < date('{{ var("as_of_date") }}'))
                                            as is_stale_open_deal,
    (close_date - created_date)            as sales_cycle_days
from {{ source('raw_crm', 'opportunities') }}
