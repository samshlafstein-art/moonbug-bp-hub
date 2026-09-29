-- Measurement sanity checks: any row returned is a failure.
-- Subsets can't exceed their totals, and incremental reach can't go negative.

select as_line_id
from {{ ref('stg_measurement__household_reach') }}
where impressions_in_kids_households  > measured_impressions
   or impressions_with_adult_coviewer > measured_impressions
   or cord_free_households            > households_reached
   or incremental_households          < 0
   or households_reached              > measured_impressions
