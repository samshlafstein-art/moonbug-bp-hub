select
    invoice_no,
    io_number,
    trim(bill_to_name)                                          as bill_to_name_raw,
    lower(regexp_replace(bill_to_name, '[^a-zA-Z0-9]', '', 'g')) as bill_to_name_normalized,
    to_date(invoice_date, 'MM/DD/YYYY')                         as invoice_date,
    service_month,
    gross_amount,
    credit_amount,
    net_amount,
    status,
    case when paid_date is not null and paid_date <> ''
         then to_date(paid_date, 'MM/DD/YYYY')
    end                                                          as paid_date,
    (io_number is null)                                          as is_missing_io_number
from {{ source('raw_finance', 'invoices') }}
