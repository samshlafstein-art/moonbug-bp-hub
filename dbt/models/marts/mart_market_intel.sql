{{
    config(materialized='table')
}}

-- Real public YouTube stats for Moonbug's own IPs alongside kids-content
-- competitors, for the market/business-intelligence storyline.
-- Grain: one row per channel.

select
    c.channel_id,
    c.handle,
    c.channel_title,
    c.owner_group,
    c.brand,
    c.subscriber_count,
    c.view_count,
    c.video_count,
    v.recent_video_count,
    v.avg_recent_views,
    v.median_recent_views,
    v.most_recent_upload_at,
    c.pulled_at
from {{ ref('stg_youtube__channels') }} c
left join (
    select
        channel_id,
        count(*)                                                       as recent_video_count,
        round(avg(view_count))                                         as avg_recent_views,
        percentile_cont(0.5) within group (order by view_count)        as median_recent_views,
        max(published_at)                                              as most_recent_upload_at
    from {{ ref('stg_youtube__videos') }}
    group by 1
) v on v.channel_id = c.channel_id
