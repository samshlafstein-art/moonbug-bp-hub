select
    as_line_id,
    as_campaign_id,
    line_number,
    product,
    ip,
    platform,
    pricing_model,
    start_date,
    end_date,
    booked_impressions,
    booked_cpm,
    booked_cost_usd,
    guaranteed_views
from {{ source('raw_adserver', 'line_items') }}
