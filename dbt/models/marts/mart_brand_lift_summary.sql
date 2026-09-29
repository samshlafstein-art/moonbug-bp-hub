{{
    config(materialized='table')
}}

-- Brand lift results joined to what was actually bought, so you can compare
-- lift by product (pre-roll vs branded integration) and by IP.
-- Grain: one row per (io_number, metric).

with main_line as (
    -- the highest-cost line on each campaign, used to characterize "what
    -- kind of buy was this" for the lift study
    select distinct on (io_number)
        io_number, product, ip, platform, account_name, account_category
    from {{ ref('mart_campaign_performance') }}
    order by io_number, booked_cost_usd desc nulls last
)

select
    b.study_id,
    b.io_number,
    b.vendor,
    b.metric,
    b.control_pct,
    b.exposed_pct,
    b.lift_pts,
    b.control_n,
    b.exposed_n,
    b.field_start,
    b.field_end,
    m.product          as primary_product,
    m.ip                as primary_ip,
    m.platform          as primary_platform,
    m.account_name,
    m.account_category
from {{ ref('stg_research__brand_lift_studies') }} b
left join main_line m using (io_number)
