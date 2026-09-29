select
    wave,
    ip,
    parent_age_band,
    child_age_band,
    aware_pct,
    favorable_pct,
    co_view_weekly_pct,
    sample_n
from {{ source('raw_research', 'parent_panel') }}
