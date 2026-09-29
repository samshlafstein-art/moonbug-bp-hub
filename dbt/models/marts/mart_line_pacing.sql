-- In-flight pacing: one row per CPM line item live on the as-of date.
--
-- Catches under-delivery WHILE there's still time to fix it (shift
-- inventory, extend the flight, re-plan) instead of discovering it at
-- wrap and issuing a make-good credit. Flat Fee branded content is left
-- out: its views are front-loaded by design, so even-pacing doesn't apply.

{% set as_of = "'" ~ var('as_of_date', '2026-09-20') ~ "'::date" %}

with lines as (

    select * from {{ ref('int_campaign_delivery') }}
    where pricing_model = 'CPM'
      and start_date <= {{ as_of }}
      and end_date   >= {{ as_of }}

),

daily as (

    select
        as_line_id,
        sum(impressions)                                                     as delivered_to_date,
        sum(impressions) filter (where delivery_date >= {{ as_of }} - 7)     as last_7d_impressions,
        count(distinct delivery_date) filter (where delivery_date >= {{ as_of }} - 7)
                                                                             as last_7d_days
    from {{ ref('stg_adserver__delivery_daily') }}
    where delivery_date < {{ as_of }}
    group by 1

),

base as (

    select
        l.as_line_id,
        l.io_number,
        l.account_name,
        l.account_category,
        l.campaign_name,
        l.product,
        l.ip,
        l.platform,
        l.start_date,
        l.end_date,
        {{ as_of }}                                                  as as_of_date,
        l.booked_impressions,
        l.booked_cpm,
        l.booked_cost_usd,

        (l.end_date - l.start_date) + 1                              as flight_days,
        {{ as_of }} - l.start_date                                   as days_elapsed,
        (l.end_date - {{ as_of }}) + 1                               as days_remaining,

        coalesce(d.delivered_to_date, 0)                             as delivered_to_date,
        coalesce(d.last_7d_impressions, 0)::numeric
            / nullif(d.last_7d_days, 0)                              as daily_run_rate
    from lines l
    left join daily d
        on l.as_line_id = d.as_line_id

),

calc as (

    select
        *,
        round(booked_impressions::numeric * days_elapsed / flight_days)          as expected_to_date,
        round(delivered_to_date + coalesce(daily_run_rate, 0) * days_remaining)  as projected_final_impressions,
        round(greatest(booked_impressions - delivered_to_date, 0)::numeric
              / nullif(days_remaining, 0))                                       as required_daily_impressions
    from base

)

select
    as_line_id,
    io_number,
    account_name,
    account_category,
    campaign_name,
    product,
    ip,
    platform,
    start_date,
    end_date,
    as_of_date,
    flight_days,
    days_elapsed,
    days_remaining,
    booked_impressions,
    booked_cpm,
    booked_cost_usd,
    delivered_to_date,
    expected_to_date,
    round(delivered_to_date / nullif(expected_to_date, 0), 4)                 as pacing_index,
    round(daily_run_rate)                                                      as daily_run_rate,
    required_daily_impressions,
    projected_final_impressions,
    round(projected_final_impressions / nullif(booked_impressions, 0), 4)     as projected_delivery_rate,

    -- same rule finance uses at wrap: credit (1 - delivery rate) x cost when under 95%
    case
        when projected_final_impressions / nullif(booked_impressions, 0) < 0.95
        then round((1 - projected_final_impressions / booked_impressions) * booked_cost_usd, 2)
        else 0
    end                                                                        as projected_makegood_usd,

    case
        when days_elapsed < 3                                                  then 'Too early'
        when projected_final_impressions / nullif(booked_impressions, 0) < 0.95 then 'At risk'
        when projected_final_impressions / nullif(booked_impressions, 0) > 1.10 then 'Over-pacing'
        else 'On track'
    end                                                                        as pacing_status

from calc
