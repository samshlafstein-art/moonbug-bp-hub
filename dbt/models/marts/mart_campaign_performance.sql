{{
    config(materialized='table')
}}

-- Campaign-line-level performance, ready for a post-campaign recap.
-- Grain: one row per (as_line_id).

select
    as_line_id,
    as_campaign_id,
    io_number,
    account_id,
    account_name,
    account_category,
    hq_region,
    agency_id,
    campaign_name,
    product,
    ip,
    platform,
    pricing_model,
    start_date,
    end_date,
    is_flight_ended,
    booked_impressions,
    guaranteed_views,
    booked_cost_usd,
    booked_cpm,
    delivered_impressions,
    delivered_video_starts,
    delivered_completed_views,
    delivery_rate,
    effective_cpm,
    view_through_rate,
    case
        when delivery_rate is not null and delivery_rate < 0.90 and is_flight_ended
            then true else false
    end as is_under_delivered
from {{ ref('int_campaign_delivery') }}
