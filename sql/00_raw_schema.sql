-- =====================================================================
-- Moonbug Brand Partnerships Data Hub: RAW LAYER
-- One schema per source system, loaded as-is (no cleaning here).
-- Cleaning, conforming and joining happen in dbt (staging -> marts).
--
-- NOTE: All sales, pipeline, delivery, research and finance data is
-- SYNTHETIC and generated for demonstration. raw_youtube is real public
-- data pulled from the YouTube Data API.
-- =====================================================================

DROP SCHEMA IF EXISTS raw_crm      CASCADE;
DROP SCHEMA IF EXISTS raw_presale  CASCADE;
DROP SCHEMA IF EXISTS raw_adserver CASCADE;
DROP SCHEMA IF EXISTS raw_research CASCADE;
DROP SCHEMA IF EXISTS raw_finance  CASCADE;
DROP SCHEMA IF EXISTS raw_market   CASCADE;
-- raw_youtube is created by fetch_youtube + load step and is NOT dropped here
-- so a re-run of the synthetic generator doesn't wipe real API pulls.

CREATE SCHEMA raw_crm;
CREATE SCHEMA raw_presale;
CREATE SCHEMA raw_adserver;
CREATE SCHEMA raw_research;
CREATE SCHEMA raw_finance;
CREATE SCHEMA raw_market;
CREATE SCHEMA IF NOT EXISTS raw_youtube;

-- ---------------------------------------------------------------------
-- CRM (Salesforce-style): accounts, agencies, reps, opportunities
-- ---------------------------------------------------------------------
CREATE TABLE raw_crm.agencies (
    agency_id        TEXT PRIMARY KEY,
    agency_name      TEXT,
    holding_company  TEXT
);

CREATE TABLE raw_crm.accounts (
    account_id       TEXT PRIMARY KEY,
    account_name     TEXT,
    category         TEXT,
    hq_region        TEXT,
    agency_id        TEXT,          -- agency of record (nullable = direct)
    created_date     DATE
);

CREATE TABLE raw_crm.users (
    user_id          TEXT PRIMARY KEY,
    full_name        TEXT,
    team             TEXT,
    region           TEXT,
    start_date       DATE
);

CREATE TABLE raw_crm.opportunities (
    opportunity_id   TEXT PRIMARY KEY,
    opportunity_name TEXT,
    account_id       TEXT,
    agency_id        TEXT,
    owner_id         TEXT,
    stage            TEXT,
    amount_usd       NUMERIC(14,2),
    probability      INTEGER,
    lead_source      TEXT,
    primary_ip       TEXT,
    created_date     DATE,
    close_date       DATE,
    is_closed        BOOLEAN,
    is_won           BOOLEAN,
    loss_reason      TEXT,
    io_number        TEXT           -- populated once Closed Won; key into ad server + finance
);

CREATE TABLE raw_crm.opportunity_stage_history (
    history_id       TEXT PRIMARY KEY,
    opportunity_id   TEXT,
    stage            TEXT,
    amount_usd       NUMERIC(14,2),
    changed_at       TIMESTAMP
);

-- ---------------------------------------------------------------------
-- PRE-SALE: proposals / RFP responses with forecasted delivery
-- ---------------------------------------------------------------------
CREATE TABLE raw_presale.proposals (
    proposal_id      TEXT PRIMARY KEY,
    opportunity_id   TEXT,
    version          INTEGER,
    sent_date        DATE,
    total_budget_usd NUMERIC(14,2),
    status           TEXT           -- Superseded / Accepted / Rejected / Pending
);

CREATE TABLE raw_presale.proposal_line_items (
    proposal_line_id   TEXT PRIMARY KEY,
    proposal_id        TEXT,
    product            TEXT,
    ip                 TEXT,
    platform           TEXT,
    pricing_model      TEXT,        -- CPM / Flat Fee
    flight_start       DATE,
    flight_end         DATE,
    est_impressions    BIGINT,
    proposed_cpm       NUMERIC(8,2),
    proposed_cost_usd  NUMERIC(14,2)
);

-- ---------------------------------------------------------------------
-- AD SERVER / PLATFORM: booked line items + daily delivery
-- (separate IDs from CRM; joins via io_number, names are messy)
-- ---------------------------------------------------------------------
CREATE TABLE raw_adserver.campaigns (
    as_campaign_id   TEXT PRIMARY KEY,
    io_number        TEXT,
    advertiser_name  TEXT,          -- free text, NOT consistent with CRM
    campaign_name    TEXT,
    start_date       DATE,
    end_date         DATE
);

CREATE TABLE raw_adserver.line_items (
    as_line_id        TEXT PRIMARY KEY,
    as_campaign_id    TEXT,
    line_number       INTEGER,
    product           TEXT,
    ip                TEXT,
    platform          TEXT,
    pricing_model     TEXT,
    start_date        DATE,
    end_date          DATE,
    booked_impressions BIGINT,
    booked_cpm        NUMERIC(8,2),
    booked_cost_usd   NUMERIC(14,2),
    guaranteed_views  BIGINT        -- for Flat Fee branded content
);

CREATE TABLE raw_adserver.delivery_daily (
    as_line_id         TEXT,
    delivery_date      DATE,
    impressions        BIGINT,
    video_starts       BIGINT,
    completed_views    BIGINT,
    watch_time_minutes NUMERIC(14,1),
    PRIMARY KEY (as_line_id, delivery_date)
);

-- ---------------------------------------------------------------------
-- AUDIENCE RESEARCH: brand lift studies + quarterly parent panel
-- ---------------------------------------------------------------------
CREATE TABLE raw_research.brand_lift_studies (
    study_id        TEXT,
    io_number       TEXT,
    vendor          TEXT,
    metric          TEXT,
    control_pct     NUMERIC(5,2),
    exposed_pct     NUMERIC(5,2),
    control_n       INTEGER,
    exposed_n       INTEGER,
    field_start     DATE,
    field_end       DATE,
    PRIMARY KEY (study_id, metric)
);

CREATE TABLE raw_research.parent_panel (
    wave               TEXT,        -- e.g. 2026-Q2
    ip                 TEXT,
    parent_age_band    TEXT,
    child_age_band     TEXT,
    aware_pct          NUMERIC(5,2),
    favorable_pct      NUMERIC(5,2),
    co_view_weekly_pct NUMERIC(5,2),
    sample_n           INTEGER
);

-- ---------------------------------------------------------------------
-- FINANCE: invoices exported from the billing system (text dates!)
-- ---------------------------------------------------------------------
CREATE TABLE raw_finance.invoices (
    invoice_no      TEXT PRIMARY KEY,
    io_number       TEXT,           -- occasionally missing in the export
    bill_to_name    TEXT,           -- free text
    invoice_date    TEXT,           -- MM/DD/YYYY
    service_month   TEXT,           -- YYYY-MM
    gross_amount    NUMERIC(14,2),
    credit_amount   NUMERIC(14,2),  -- make-good credits for under-delivery
    net_amount      NUMERIC(14,2),
    status          TEXT,
    paid_date       TEXT            -- MM/DD/YYYY or empty
);

-- ---------------------------------------------------------------------
-- MARKET: third-party style benchmarks (synthetic)
-- ---------------------------------------------------------------------
CREATE TABLE raw_market.category_benchmarks (
    quarter                     TEXT,
    category                    TEXT,
    platform                    TEXT,
    benchmark_cpm               NUMERIC(8,2),
    benchmark_vtr               NUMERIC(5,3),
    est_kids_category_spend_musd NUMERIC(10,1)
);
