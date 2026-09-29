{{
    config(materialized='table')
}}

-- Moonbug's own booked CPM/VTR by category+platform+quarter, next to the
-- market benchmark for the same cut. Grain: one row per
-- (account_category, platform, quarter).

with moonbug_actuals as (
    select
        account_category,
        platform,
        to_char(date_trunc('quarter', start_date), '"Q"Q YYYY')       as quarter_label,
        extract(year from start_date)::int                            as year,
        extract(quarter from start_date)::int                         as quarter_num,
        avg(booked_cpm) filter (where pricing_model = 'CPM')          as moonbug_avg_cpm,
        avg(view_through_rate)                                         as moonbug_avg_vtr,
        sum(booked_cost_usd)                                           as moonbug_booked_cost_usd
    from {{ ref('mart_campaign_performance') }}
    group by 1, 2, 3, 4, 5
)

select
    a.account_category                                as category,
    a.platform,
    a.quarter_label,
    a.moonbug_avg_cpm,
    a.moonbug_avg_vtr,
    a.moonbug_booked_cost_usd,
    bm.benchmark_cpm,
    bm.benchmark_vtr,
    bm.est_kids_category_spend_musd,
    round(a.moonbug_avg_cpm - bm.benchmark_cpm, 2)    as cpm_vs_benchmark,
    round(a.moonbug_avg_vtr - bm.benchmark_vtr, 4)    as vtr_vs_benchmark
from moonbug_actuals a
left join {{ ref('stg_market__category_benchmarks') }} bm
    on bm.category = a.account_category
   and bm.platform = a.platform
   and bm.quarter  = a.year || '-Q' || a.quarter_num
