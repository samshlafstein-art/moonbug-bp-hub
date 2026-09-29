{{
    config(materialized='table')
}}

-- Win rate, average sales cycle, and average deal size by advertiser
-- category, closed deals only. This is the model behind the
-- deprioritization call (e.g. Automotive: low win rate, long cycle).
-- Grain: one row per account_category.

select
    account_category,
    count(*) filter (where is_closed)                                        as closed_deal_count,
    count(*) filter (where is_won)                                           as won_deal_count,
    round(
        count(*) filter (where is_won)::numeric
        / nullif(count(*) filter (where is_closed), 0)
    , 3)                                                                      as win_rate,
    round(avg(sales_cycle_days) filter (where is_closed))                     as avg_sales_cycle_days,
    round(avg(amount_usd) filter (where is_closed), 2)                        as avg_deal_size_usd,
    round(sum(amount_usd) filter (where is_won), 2)                           as total_won_usd,
    round(sum(weighted_amount_usd) filter (where not is_closed), 2)           as open_weighted_pipeline_usd
from {{ ref('int_pipeline_snapshot') }}
group by 1
