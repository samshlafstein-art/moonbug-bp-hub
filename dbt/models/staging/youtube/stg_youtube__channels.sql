select
    channel_id,
    handle,
    channel_title,
    owner_group,
    brand,
    subscriber_count,
    view_count,
    video_count,
    pulled_at
from {{ source('raw_youtube', 'channels') }}
