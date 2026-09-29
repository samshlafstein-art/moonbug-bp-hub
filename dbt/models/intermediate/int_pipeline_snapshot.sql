{{
    config(materialized='table')
}}

-- One row per opportunity, enriched with account/agency/owner context and
-- a weighted-pipeline value. This is the base for the current-pipeline mart
-- and for win-rate / cycle-time cuts by category.

select
    o.opportunity_id,
    o.opportunity_name,
    o.account_id,
    a.account_name,
    a.category                                   as account_category,
    a.hq_region,
    o.agency_id,
    ag.agency_name,
    ag.holding_company,
    o.owner_id,
    u.full_name                                  as owner_name,
    u.region                                     as owner_region,
    o.stage,
    o.amount_usd,
    o.probability,
    round(o.amount_usd * o.probability / 100.0, 2) as weighted_amount_usd,
    o.lead_source,
    o.primary_ip,
    o.created_date,
    o.close_date,
    o.sales_cycle_days,
    o.is_closed,
    o.is_won,
    o.loss_reason,
    o.io_number,
    o.is_stale_open_deal
from {{ ref('stg_crm__opportunities') }} o
left join {{ ref('stg_crm__accounts') }} a  on a.account_id = o.account_id
left join {{ ref('stg_crm__agencies') }} ag on ag.agency_id = o.agency_id
left join {{ ref('stg_crm__users') }} u     on u.user_id = o.owner_id
