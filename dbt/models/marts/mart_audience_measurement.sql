-- Privacy-first audience measurement: one row per measured CPM line item.
--
-- The headline metric is ON-TARGET CPM: what the advertiser actually pays
-- per thousand impressions that land in a household with kids. It's compared
-- with buying "households with kids" through third-party audience data,
-- which CIMM (Jul 2026) found is right only ~42% of the time - so a $X CPM
-- third-party buy really costs $X / 0.42 per on-target thousand.

{% set third_party_accuracy = var('third_party_kids_hh_accuracy', 0.42) %}

with delivery as (

    select * from {{ ref('int_campaign_delivery') }}
    where pricing_model = 'CPM'

),

measurement as (

    select * from {{ ref('stg_measurement__household_reach') }}

),

benchmarks as (

    select quarter, category, platform, benchmark_cpm
    from {{ ref('stg_market__category_benchmarks') }}

),

joined as (

    select
        d.as_line_id,
        d.io_number,
        d.account_name,
        d.account_category,
        d.campaign_name,
        d.product,
        d.ip,
        d.platform,
        d.start_date,
        d.end_date,
        d.is_flight_ended,
        m.vendor,
        m.measured_through,

        d.booked_cpm,
        d.delivered_impressions                                   as adserver_impressions,
        m.measured_impressions,
        m.households_reached,
        m.incremental_households,
        m.cord_free_households,
        m.impressions_in_kids_households,
        m.impressions_with_adult_coviewer,

        -- billable spend to date: delivered impressions (capped at booked) x rate card
        round(least(d.delivered_impressions, d.booked_impressions) * d.booked_cpm / 1000, 2)
                                                                  as delivered_spend_usd,
        b.benchmark_cpm                                           as category_benchmark_cpm
    from delivery d
    inner join measurement m
        on d.as_line_id = m.as_line_id
    left join benchmarks b
        on  b.category = d.account_category
        and b.platform = d.platform
        and b.quarter  = to_char(d.start_date, 'YYYY') || '-Q' || extract(quarter from d.start_date)

)

select
    *,

    -- reach & frequency
    round(measured_impressions::numeric / nullif(households_reached, 0), 2)          as avg_frequency,
    round(incremental_households::numeric / nullif(households_reached, 0), 4)        as incremental_reach_pct,
    round(cord_free_households::numeric / nullif(households_reached, 0), 4)          as cord_free_household_pct,

    -- audience quality
    round(impressions_in_kids_households::numeric / nullif(measured_impressions, 0), 4)
                                                                                     as kids_household_impression_pct,
    round(impressions_with_adult_coviewer::numeric / nullif(measured_impressions, 0), 4)
                                                                                     as coviewing_impression_pct,
    round(1 - measured_impressions::numeric / nullif(adserver_impressions, 0), 4)    as measurement_gap_pct,

    -- cost efficiency
    round(delivered_spend_usd * 1000 / nullif(impressions_in_kids_households, 0), 2) as on_target_cpm,
    round(delivered_spend_usd * 1000 / nullif(impressions_with_adult_coviewer, 0), 2)
                                                                                     as parent_coviewing_cpm,
    round(category_benchmark_cpm / {{ third_party_accuracy }}, 2)                   as third_party_on_target_cpm,
    round(
        1 - (delivered_spend_usd * 1000 / nullif(impressions_in_kids_households, 0))
            / nullif(category_benchmark_cpm / {{ third_party_accuracy }}, 0),
        4)                                                                           as on_target_cpm_savings_pct

from joined
