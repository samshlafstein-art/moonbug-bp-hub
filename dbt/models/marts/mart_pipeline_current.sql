{{
    config(materialized='table')
}}

-- Currently open deals only, ready for a weekly pipeline review or a
-- deal-prioritization exercise. Grain: one row per open opportunity_id.

select
    opportunity_id,
    opportunity_name,
    account_id,
    account_name,
    account_category,
    hq_region,
    agency_id,
    agency_name,
    holding_company,
    owner_id,
    owner_name,
    stage,
    amount_usd,
    probability,
    weighted_amount_usd,
    lead_source,
    primary_ip,
    created_date,
    close_date,
    sales_cycle_days,
    is_stale_open_deal
from {{ ref('int_pipeline_snapshot') }}
where not is_closed
