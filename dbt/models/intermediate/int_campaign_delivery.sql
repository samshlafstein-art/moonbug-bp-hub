{{
    config(materialized='table')
}}

-- One row per (campaign, line item): joins the ad server delivery totals
-- back to CRM (via io_number) and to finance (via io_number + line's IP/product
-- share of the campaign). This is the reconciliation model that answers
-- "booked vs delivered vs billed" for every won deal.

with delivered as (
    select
        as_line_id,
        sum(impressions)       as delivered_impressions,
        sum(video_starts)      as delivered_video_starts,
        sum(completed_views)   as delivered_completed_views,
        min(delivery_date)     as first_delivery_date,
        max(delivery_date)     as last_delivery_date
    from {{ ref('stg_adserver__delivery_daily') }}
    group by 1
),

lines as (
    select
        li.*,
        c.io_number,
        c.advertiser_name_raw,
        c.advertiser_name_normalized,
        c.campaign_name
    from {{ ref('stg_adserver__line_items') }} li
    join {{ ref('stg_adserver__campaigns') }} c using (as_campaign_id)
),

joined as (
    select
        l.as_line_id,
        l.as_campaign_id,
        l.io_number,
        l.advertiser_name_raw,
        l.campaign_name,
        l.product,
        l.ip,
        l.platform,
        l.pricing_model,
        l.start_date,
        l.end_date,
        l.booked_impressions,
        l.booked_cpm,
        l.booked_cost_usd,
        l.guaranteed_views,
        coalesce(d.delivered_impressions, 0)     as delivered_impressions,
        coalesce(d.delivered_video_starts, 0)    as delivered_video_starts,
        coalesce(d.delivered_completed_views, 0) as delivered_completed_views,
        d.first_delivery_date,
        d.last_delivery_date,
        o.account_id,
        o.primary_ip                             as opp_primary_ip,
        o.owner_id,
        o.agency_id,
        a.account_name,
        a.category                               as account_category,
        a.hq_region

    from lines l
    left join delivered d               on d.as_line_id = l.as_line_id
    left join {{ ref('stg_crm__opportunities') }} o on o.io_number = l.io_number
    left join {{ ref('stg_crm__accounts') }} a       on a.account_id = o.account_id
)

select
    *,
    (end_date < date('{{ var("as_of_date") }}'))          as is_flight_ended,
    case
        when pricing_model = 'CPM' and booked_impressions > 0
            then round(delivered_impressions::numeric / booked_impressions, 4)
        when pricing_model = 'Flat Fee' and guaranteed_views > 0
            then round(delivered_impressions::numeric / guaranteed_views, 4)
    end                                                     as delivery_rate,
    case
        when pricing_model = 'CPM' and delivered_impressions > 0
            then round(booked_cost_usd / (delivered_impressions / 1000.0), 2)
    end                                                     as effective_cpm,
    case
        when delivered_video_starts > 0
            then round(delivered_completed_views::numeric / delivered_video_starts, 4)
    end                                                     as view_through_rate
from joined
