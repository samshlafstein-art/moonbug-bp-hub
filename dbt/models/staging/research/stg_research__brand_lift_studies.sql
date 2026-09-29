select
    study_id,
    io_number,
    vendor,
    metric,
    control_pct,
    exposed_pct,
    (exposed_pct - control_pct) as lift_pts,
    control_n,
    exposed_n,
    field_start,
    field_end
from {{ source('raw_research', 'brand_lift_studies') }}
