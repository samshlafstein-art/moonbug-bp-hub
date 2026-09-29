select
    account_id,
    trim(account_name)  as account_name,
    category,
    hq_region,
    agency_id,
    created_date
from {{ source('raw_crm', 'accounts') }}
