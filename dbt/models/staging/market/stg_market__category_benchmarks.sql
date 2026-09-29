select
    quarter,
    category,
    platform,
    benchmark_cpm,
    benchmark_vtr,
    est_kids_category_spend_musd
from {{ source('raw_market', 'category_benchmarks') }}
