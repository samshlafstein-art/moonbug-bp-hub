select
    as_line_id,
    delivery_date,
    impressions,
    video_starts,
    completed_views,
    watch_time_minutes
from {{ source('raw_adserver', 'delivery_daily') }}
