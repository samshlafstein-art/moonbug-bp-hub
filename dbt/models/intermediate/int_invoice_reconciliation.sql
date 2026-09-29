{{
    config(materialized='table')
}}

-- One row per invoice, joined to the opportunity/account it belongs to,
-- plus that deal's aggregate booked cost and delivery rate so you can see
-- billing alongside performance in one place.

with deal_delivery as (
    select
        io_number,
        sum(booked_cost_usd)                                   as deal_booked_cost_usd,
        sum(delivered_impressions)                              as deal_delivered_impressions,
        sum(booked_impressions)                                 as deal_booked_impressions,
        avg(delivery_rate) filter (where pricing_model = 'CPM') as avg_cpm_delivery_rate
    from {{ ref('int_campaign_delivery') }}
    group by 1
)

select
    i.invoice_no,
    i.io_number,
    i.is_missing_io_number,
    i.bill_to_name_raw,
    i.invoice_date,
    i.service_month,
    i.gross_amount,
    i.credit_amount,
    i.net_amount,
    i.status,
    i.paid_date,
    (i.paid_date is not null)                                          as is_paid,
    case when i.paid_date is not null
         then i.paid_date - i.invoice_date
    end                                                                 as days_to_pay,
    o.account_id,
    a.account_name,
    a.category                                                         as account_category,
    o.agency_id,
    ag.agency_name,
    ag.holding_company,
    dd.deal_booked_cost_usd,
    dd.avg_cpm_delivery_rate
from {{ ref('stg_finance__invoices') }} i
left join {{ ref('stg_crm__opportunities') }} o on o.io_number = i.io_number
left join {{ ref('stg_crm__accounts') }} a       on a.account_id = o.account_id
left join {{ ref('stg_crm__agencies') }} ag      on ag.agency_id = o.agency_id
left join deal_delivery dd                       on dd.io_number = i.io_number
