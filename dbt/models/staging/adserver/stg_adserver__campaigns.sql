select
    as_campaign_id,
    io_number,
    advertiser_name                                  as advertiser_name_raw,
    lower(regexp_replace(advertiser_name, '[^a-zA-Z0-9]', '', 'g'))
                                                      as advertiser_name_normalized,
    campaign_name,
    start_date,
    end_date
from {{ source('raw_adserver', 'campaigns') }}
