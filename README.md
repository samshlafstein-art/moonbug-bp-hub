# Moonbug Brand Partnerships Data Hub

A data warehouse and Claude skill for a kids & family media ad-sales team. Ask a question in plain English, like "which campaigns are at risk of under-delivering?", and get an answer from tested, consistently defined data.

## What this does

- Loads six source systems (CRM, pre-sale, ad server, measurement, research, finance) into Supabase Postgres.
- Models them with dbt into tested marts, joined on `io_number` rather than messy names.
- Defines every metric once in [`metrics.md`](metrics.md).
- Adds a Claude skill (via Supabase MCP) that queries the marts and writes reports using those definitions.

```
 SOURCES                                      RAW (Supabase Postgres)
 ┌──────────────────────────────┐
 │ CRM            accounts, opps│──┐
 │ Pre-sale       proposals     │  │          raw_crm
 │ Ad server      lines, daily  │  │          raw_presale
 │ Measurement    households    │  ├────────▶ raw_adserver
 │ Research       lift, panel   │  │          raw_measurement
 │ Finance        invoices      │  │          raw_research
 │ Market         benchmarks    │  │          raw_finance
 │ YouTube API    channels      │──┘          raw_market · raw_youtube
 └──────────────────────────────┘                     │
                                                      ▼  dbt
                                  ┌─────────────────────────────────────┐
                                  │ analytics_staging        stg_*      │  clean + rename
                                  │ analytics_intermediate   int_*      │  join on io_number
                                  │ analytics_analytics      mart_*     │  one grain, tested
                                  └─────────────────────────────────────┘
                                                      │
                                                      ▼  Supabase MCP (read-only)
                                  ┌─────────────────────────────────────┐
                                  │ Claude skill                        │
                                  │  SKILL.md   → which mart, which join│
                                  │  metrics.md → how every metric works│
                                  │  templates/ → 4 report formats      │
                                  └─────────────────────────────────────┘
                                                      │
                                                      ▼
                                   "Which in-flight lines are at risk?"
```

## Marts

| Mart | Use for |
|---|---|
| `mart_line_pacing` | In-flight lines at risk of under-delivering, projected make-good $ |
| `mart_audience_measurement` | Household reach, co-viewing, repeat viewing, incremental reach vs. linear, on-target CPM |
| `mart_campaign_performance` | Final delivery, effective CPM, VTR |
| `mart_booked_vs_delivered_vs_billed` | Finance reconciliation |
| `mart_pipeline_current` | Open pipeline, stale deals |
| `mart_category_win_rates` | Which categories to prioritize |
| `mart_brand_lift_summary` | Brand lift by campaign |
| `mart_category_benchmarking` | Pricing vs. market |
| `mart_market_intel` | Competitor YouTube channels (real data) |

## Setup

Requires Python 3.9+, a Supabase project, and a YouTube Data API key.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add DATABASE_URL and YOUTUBE_API_KEY

python scripts/generate_synthetic.py
python scripts/fetch_youtube.py
python scripts/load_raw.py

cp dbt/profiles.yml.example ~/.dbt/profiles.yml   # set host/user from DATABASE_URL
export SUPABASE_DB_PASSWORD="..."
cd dbt && dbt build
```

To use the skill, connect Supabase in Claude and upload `skill/` as a skill.