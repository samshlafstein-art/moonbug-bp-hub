select
    user_id,
    full_name,
    team,
    region,
    start_date
from {{ source('raw_crm', 'users') }}
