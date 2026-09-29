{{
    config(materialized='table')
}}

-- Deal-level reconciliation across the three systems: what was booked in the
-- ad server, what was actually delivered, and what finance has billed and
-- collected. Grain: one row per io_number (won deal).

with delivery_agg as (
    select
        io_number,
        account_id,
        account_name,
        account_category,
        min(start_date)                                            as flight_start,
        max(end_date)                                              as flight_end,
        sum(booked_cost_usd)                                       as booked_cost_usd,
        sum(delivered_impressions)                                 as delivered_impressions,
        sum(booked_impressions)                                    as booked_impressions,
        bool_and(is_flight_ended)                                  as all_lines_ended,
        avg(delivery_rate) filter (where pricing_model = 'CPM')    as avg_cpm_delivery_rate,
        bool_or(is_under_delivered)                                as has_under_delivered_line
    from {{ ref('mart_campaign_performance') }}
    group by 1, 2, 3, 4
),

billing_agg as (
    select
        io_number,
        count(*)                          as invoice_count,
        sum(gross_amount)                 as billed_gross_usd,
        sum(credit_amount)                as billed_credits_usd,
        sum(net_amount)                   as billed_net_usd,
        sum(net_amount) filter (where is_paid) as collected_usd,
        max(days_to_pay)                  as max_days_to_pay
    from {{ ref('int_invoice_reconciliation') }}
    where io_number is not null
    group by 1
)

select
    d.io_number,
    d.account_id,
    d.account_name,
    d.account_category,
    d.flight_start,
    d.flight_end,
    d.all_lines_ended,
    d.booked_cost_usd,
    d.booked_impressions,
    d.delivered_impressions,
    d.avg_cpm_delivery_rate,
    d.has_under_delivered_line,
    b.invoice_count,
    b.billed_gross_usd,
    b.billed_credits_usd,
    b.billed_net_usd,
    b.collected_usd,
    b.max_days_to_pay,
    round(coalesce(b.billed_net_usd, 0) - d.booked_cost_usd, 2)  as billed_vs_booked_variance_usd
from delivery_agg d
left join billing_agg b using (io_number)
