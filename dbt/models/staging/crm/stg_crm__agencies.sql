select
    agency_id,
    agency_name,
    holding_company
from {{ source('raw_crm', 'agencies') }}
