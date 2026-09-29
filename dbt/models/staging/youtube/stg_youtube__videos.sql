select
    video_id,
    channel_id,
    title,
    published_at,
    duration_iso,
    made_for_kids,
    view_count,
    like_count,
    comment_count,
    pulled_at
from {{ source('raw_youtube', 'videos') }}
