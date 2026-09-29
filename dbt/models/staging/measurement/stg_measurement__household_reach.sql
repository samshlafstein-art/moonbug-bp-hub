-- Household-level measurement per CPM line (mock iSpot-style feed).
-- No child- or device-level fields exist upstream by design (COPPA).

select
    as_line_id,
    vendor,
    measured_through,
    measured_impressions,
    households_reached,
    impressions_in_kids_households,
    impressions_with_adult_coviewer,
    cord_free_households,
    households_also_reached_by_linear,
    households_reached - households_also_reached_by_linear as incremental_households
from {{ source('measurement', 'household_reach') }}
