"""
Generate SYNTHETIC ad-sales data for the Moonbug Brand Partnerships Data Hub.

Mimics five source systems (CRM, pre-sale, ad server, research, finance)
plus market benchmarks. Output: CSVs in data/raw/<schema>/<table>.csv

All advertisers, agencies, reps and numbers are fictional. IP names are
Moonbug's public titles, used only to make the demo realistic.

PLANTED STORYLINES (what the LLM should be able to "discover"):
  1. Toys & Games is heavily Q4-seasonal, and Q4 2026 toy pipeline is up ~40% YoY.
  2. Pre-sale overestimates FAST inventory: FAST lines deliver ~85% of booked,
     triggering make-good credits in finance. YouTube/CTV deliver ~100%.
  3. Branded content integrations, especially Blippi, drive the biggest brand
     lift per dollar; pre-roll wins on reach and cost-efficiency.
  4. Automotive: large deal sizes but ~10% win rate and ~2x sales cycle -> deprioritize.
  5. Agencies under "Halcyon Holdings" pay slowly (~85+ days vs ~55).
  6. Pipeline hygiene: a handful of open deals are past their close date.
  7. Data quality: ~2% of invoices are missing io_number; names are inconsistent
     across CRM, ad server and finance (must join on io_number).
  8. Privacy-first household measurement (iSpot-style, mock): Moonbug
     impressions land almost entirely in households with kids, so the
     on-target CPM beats buying "households with kids" via third-party data
     (CIMM, Jul 2026: ~42% accurate). CTV/FAST reach mostly cord-free
     households that a linear buy misses, and have the highest co-viewing
     parent share; YouTube Shorts has the lowest.
  9. In-flight pacing: FAST lines currently in flight are pacing behind
     (same ~85% inventory overestimate), so they surface as make-good risks
     before the flight ends.
"""
import csv
import math
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

SEED = 42
random.seed(SEED)
rng = np.random.default_rng(SEED)

AS_OF = date(2026, 9, 20)
WINDOW_START = date(2025, 1, 1)
WINDOW_END = date(2026, 9, 10)          # last opportunity created
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
IPS = {  # ip: (weight, strength multiplier for brand lift, core child age)
    "CoComelon":       (0.34, 1.00, "0-2"),
    "Blippi":          (0.20, 1.35, "3-5"),
    "Little Baby Bum": (0.09, 0.90, "0-2"),
    "Little Angel":    (0.09, 0.95, "0-2"),
    "Oddbods":         (0.08, 1.00, "6-8"),
    "Morphle":         (0.06, 0.95, "3-5"),
    "Gecko's Garage":  (0.06, 1.00, "3-5"),
    "Supa Strikas":    (0.04, 1.05, "9-11"),
    "Go Buster":       (0.02, 0.95, "3-5"),
    "Arpo":            (0.02, 0.95, "3-5"),
}

# category: weight, base win rate, avg deal $, Q4 boost, sales cycle days, suffixes
CATEGORIES = {
    "Toys & Games":                     (0.22, 0.46, 180_000, 2.2, 40,  ["Toys", "Games", "Playthings"]),
    "Kids Food & Snacks":               (0.14, 0.42, 120_000, 1.0, 45,  ["Foods", "Snacks", "Kitchen"]),
    "Family Entertainment & Streaming": (0.10, 0.44, 210_000, 1.3, 35,  ["Studios", "Pictures", "Play+"]),
    "Retail":                           (0.10, 0.36, 150_000, 1.6, 50,  ["Market", "Stores", "Outlet"]),
    "Baby & Toddler Care":              (0.10, 0.41, 90_000,  1.0, 45,  ["Baby", "Care", "Littles"]),
    "Education & EdTech":               (0.10, 0.31, 60_000,  1.0, 55,  ["Learning", "Academy", "Labs"]),
    "Theme Parks & Travel":             (0.08, 0.36, 140_000, 1.0, 50,  ["Resorts", "Parks", "Getaways"]),
    "Kids Apparel":                     (0.06, 0.34, 70_000,  1.2, 45,  ["Kids Wear", "Outfitters", "Threads"]),
    "Automotive":                       (0.05, 0.10, 260_000, 1.0, 105, ["Motors", "Auto", "Mobility"]),
    "Household CPG":                    (0.05, 0.39, 100_000, 1.0, 45,  ["Home", "Household", "Essentials"]),
}

NAME_PREFIXES = [
    "Brightbloom", "Tumbletown", "Sunnyside", "Pebblestone", "Maple & Moss", "Kiddo",
    "Little Oak", "Starling", "Puddlejump", "Honeycomb", "Blue Kite", "Wonderwell",
    "Juniper", "Cloudberry", "Pip & Pop", "Tiny Harbor", "Merrymint", "Acorn",
    "Lullaby Lane", "Rocket Pup", "Zippy", "Marigold", "Bumblebee", "Crayonbox",
    "Hopscotch", "Wiggleworth", "Treetop", "Snugglebug", "Firefly", "Gumdrop",
    "Meadowlark", "Otter & Oak", "Tidepool", "Pinwheel", "Nimbus", "Button & Bow",
    "Clover", "Kitefield", "Paper Moon", "Fernwood", "Sprout", "Lanternfish",
    "Harborview", "Cobblestone", "Bluebell", "Quill", "Riverstone", "Hazelnut",
    "Pepperpot", "Willowbrook", "Figtree", "Moonpie", "Saffron", "Tinkertown",
    "Northwind", "Copperkettle", "Seashell", "Larkspur", "Driftwood", "Wildflower",
]

HOLDING_COS = ["Meridian Group", "Atlas Collective", "Halcyon Holdings", "Independent"]
AGENCIES = [
    ("AG001", "Meridian Kids & Family", "Meridian Group"),
    ("AG002", "Meridian Media NY", "Meridian Group"),
    ("AG003", "Northstar Media", "Atlas Collective"),
    ("AG004", "Atlas Play", "Atlas Collective"),
    ("AG005", "Atlas Media London", "Atlas Collective"),
    ("AG006", "Halcyon Family Media", "Halcyon Holdings"),
    ("AG007", "Halcyon Digital", "Halcyon Holdings"),
    ("AG008", "Brightpath Media", "Independent"),
    ("AG009", "Small Wonders Agency", "Independent"),
    ("AG010", "Greenhouse Media", "Independent"),
]
SLOW_PAYERS = {"AG006", "AG007"}

REPS = [  # user_id, name, team, region, start, skill multiplier
    ("U01", "Jordan Reyes",   "Brand Partnerships", "US East", date(2021, 3, 1), 1.15),
    ("U02", "Priya Natarajan","Brand Partnerships", "US East", date(2022, 6, 1), 1.05),
    ("U03", "Marcus Bell",    "Brand Partnerships", "US East", date(2024, 9, 1), 0.85),
    ("U04", "Elena Kovacs",   "Brand Partnerships", "US West", date(2020, 1, 15), 1.10),
    ("U05", "Tom Hartley",    "Brand Partnerships", "US West", date(2023, 4, 1), 0.95),
    ("U06", "Aisha Okafor",   "Brand Partnerships", "UK",      date(2021, 8, 1), 1.05),
    ("U07", "Oliver Grant",   "Brand Partnerships", "UK",      date(2025, 2, 1), 0.85),
    ("U08", "Mei Lin Tan",    "Brand Partnerships", "APAC",    date(2022, 11, 1), 1.00),
]
REGION_WEIGHTS = {"US East": 0.40, "US West": 0.22, "UK": 0.26, "APAC": 0.12}

PRODUCTS = {
    # product: platform, pricing, cpm range, VTR, share weight
    "YouTube Contextual Pre-roll": ("YouTube", "CPM", (9, 14), 0.74, 0.34),
    "YouTube Shorts Sponsorship":  ("YouTube", "CPM", (6, 10), 0.58, 0.12),
    "FAST Channel Video":          ("FAST",    "CPM", (20, 28), 0.93, 0.22),
    "CTV App Video":               ("CTV",     "CPM", (22, 32), 0.95, 0.14),
    "Branded Content Integration": ("YouTube", "Flat Fee", None, None, 0.18),
}
# Delivery vs booked (mean, sd) - the FAST overestimate storyline lives here
DELIVERY_RATE = {"YouTube": (1.01, 0.03), "FAST": (0.85, 0.07), "CTV": (0.99, 0.04)}

STAGES = ["Prospecting", "RFP Received", "Proposal Sent", "Negotiation"]
STAGE_PROB = {"Prospecting": 10, "RFP Received": 25, "Proposal Sent": 40,
              "Negotiation": 70, "Closed Won": 100, "Closed Lost": 0}
LOSS_REASONS = ["Budget cut", "Went with competitor", "Timing / flight moved",
                "Pricing", "No decision", "Brand safety / kids policy review"]
LEAD_SOURCES = ["Agency RFP", "Inbound", "Upsell / renewal", "Outbound", "Event"]


def w_choice(d):
    keys = list(d.keys())
    weights = [v[0] if isinstance(v, tuple) else v for v in d.values()]
    return random.choices(keys, weights=weights, k=1)[0]


def rand_date(a, b):
    return a + timedelta(days=random.randint(0, (b - a).days))


def month_iter(a, b):
    y, m = a.year, a.month
    while (y, m) <= (b.year, b.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fmt_us(d):
    return d.strftime("%m/%d/%Y") if d else ""


def messy(name):
    r = random.random()
    if r < 0.35:
        return name
    if r < 0.55:
        return name.upper()
    if r < 0.75:
        return name + " Inc."
    if r < 0.90:
        return name.replace(" & ", " and ")
    return name.replace(" ", "")


tables = {}


def add(schema_table, row):
    tables.setdefault(schema_table, []).append(row)


# ---------------------------------------------------------------------------
# CRM reference
# ---------------------------------------------------------------------------
for a in AGENCIES:
    add("raw_crm.agencies", dict(agency_id=a[0], agency_name=a[1], holding_company=a[2]))

for r in REPS:
    add("raw_crm.users", dict(user_id=r[0], full_name=r[1], team=r[2], region=r[3], start_date=r[4]))

accounts = []
prefixes = NAME_PREFIXES[:]
random.shuffle(prefixes)
for i, prefix in enumerate(prefixes):
    cat = w_choice(CATEGORIES)
    suffix = random.choice(CATEGORIES[cat][5])
    region = w_choice(REGION_WEIGHTS)
    agency = None if random.random() < 0.25 else random.choice(AGENCIES)[0]
    acc = dict(account_id=f"ACC{i+1:03d}", account_name=f"{prefix} {suffix}",
               category=cat, hq_region=region, agency_id=agency,
               created_date=rand_date(date(2019, 1, 1), date(2025, 6, 1)))
    accounts.append(acc)
    add("raw_crm.accounts", acc)

accounts_by_cat = {}
for a in accounts:
    accounts_by_cat.setdefault(a["category"], []).append(a)
rep_by_region = {}
for r in REPS:
    rep_by_region.setdefault(r[3], []).append(r)

# ---------------------------------------------------------------------------
# Opportunities, stage history, proposals
# ---------------------------------------------------------------------------
N_OPPS = 440
N_EXTRA_TOY_2026 = 45   # Storyline 1: incremental Q4 2026 toy demand
opps = []
io_seq = {2025: 0, 2026: 0, 2027: 0}
hist_id = 0
prop_id = 0
pline_id = 0
proposals_by_opp = {}

for n in range(N_OPPS + N_EXTRA_TOY_2026):
    extra_toy = n >= N_OPPS
    # pick category (reweighted to real account availability), then account
    cat = "Toys & Games" if extra_toy else w_choice({c: CATEGORIES[c][0] for c in accounts_by_cat})
    acc = random.choice(accounts_by_cat[cat])
    _, win_base, avg_deal, q4_boost, cycle, _ = CATEGORIES[cat]

    created = rand_date(WINDOW_START, WINDOW_END)
    # Q4 buying season: many toy/retail deals are created Jul-Sep
    if q4_boost > 1.5 and random.random() < 0.45:
        yr = random.choice([2025, 2026])
        created = rand_date(date(yr, 7, 1), min(date(yr, 9, 30), WINDOW_END))
    if extra_toy:
        created = rand_date(date(2026, 6, 1), WINDOW_END)

    cyc = max(10, int(rng.normal(cycle, cycle * 0.3)))
    close = created + timedelta(days=cyc)
    flight_start = close + timedelta(days=random.randint(7, 25))
    if q4_boost > 1.5 and random.random() < 0.65:
        # push flights into Oct/Nov
        fy = flight_start.year if flight_start.month <= 11 else flight_start.year + 1
        flight_start = date(fy, random.choice([10, 10, 11]), random.randint(1, 20))
        close = flight_start - timedelta(days=random.randint(7, 25))
        # keep a realistic sales cycle: back-date creation from the close date
        created = max(WINDOW_START, min(WINDOW_END, close - timedelta(days=cyc)))
        if close <= created:
            close = created + timedelta(days=10)
            flight_start = close + timedelta(days=14)
    flight_days = random.choice([28, 30, 42, 45, 60, 90])
    flight_end = flight_start + timedelta(days=flight_days)

    amount = float(round(rng.lognormal(math.log(avg_deal), 0.55), -2))
    amount = max(amount, 15_000)

    region = acc["hq_region"]
    rep = random.choice(rep_by_region[region])
    agency_id = acc["agency_id"]
    ip = w_choice(IPS)
    if cat == "Kids Apparel" and random.random() < 0.3:
        ip = "Supa Strikas"

    # outcome
    is_closed = close < AS_OF
    stale = False
    if is_closed and random.random() < 0.05 and close > AS_OF - timedelta(days=60):
        is_closed, stale = False, True          # Storyline 6
    p_win = min(0.9, win_base * rep[5] * (1.1 if agency_id is None else 1.0))
    is_won = is_closed and random.random() < p_win
    if is_closed:
        stage = "Closed Won" if is_won else "Closed Lost"
    else:
        # how far along is it?
        progress = (AS_OF - created).days / max(1, (close - created).days)
        idx = min(3, int(progress * 4 * random.uniform(0.6, 1.2)))
        stage = STAGES[max(0, idx)]
        if stale:
            stage = random.choice(["Proposal Sent", "Negotiation"])

    io_number = None
    if is_won:
        yr = close.year
        io_seq[yr] += 1
        io_number = f"IO-{yr}-{io_seq[yr]:04d}"

    opp = dict(
        opportunity_id=f"OPP{n+1:04d}",
        opportunity_name=f"{acc['account_name']} - {ip} - {flight_start:%b %Y}",
        account_id=acc["account_id"], agency_id=agency_id, owner_id=rep[0],
        stage=stage, amount_usd=amount, probability=STAGE_PROB[stage],
        lead_source=random.choice(LEAD_SOURCES), primary_ip=ip,
        created_date=created, close_date=close, is_closed=is_closed, is_won=is_won,
        loss_reason=random.choice(LOSS_REASONS) if (is_closed and not is_won) else None,
        io_number=io_number,
    )
    # automotive: brand-safety review is a common loss reason
    if cat == "Automotive" and opp["loss_reason"] and random.random() < 0.4:
        opp["loss_reason"] = "Brand safety / kids policy review"
    opp["_cat"], opp["_flight"] = cat, (flight_start, flight_end)
    opps.append(opp)
    add("raw_crm.opportunities", {k: v for k, v in opp.items() if not k.startswith("_")})

    # stage history
    path = ["Prospecting", "RFP Received", "Proposal Sent", "Negotiation"]
    if stage in path:
        path = path[: path.index(stage) + 1]
    elif stage == "Closed Lost":
        path = path[: random.randint(1, 4)] + ["Closed Lost"]
    else:
        path = path + ["Closed Won"]
    end_ts = min(close, AS_OF) if is_closed else min(AS_OF, max(created, close))
    span = max(1, (end_ts - created).days)
    amt = amount * random.uniform(0.8, 1.25)
    for j, st in enumerate(path):
        d = created + timedelta(days=int(span * j / max(1, len(path) - 1))) if len(path) > 1 else created
        if st in ("Closed Won", "Closed Lost"):
            d = close
            amt = amount
        hist_id += 1
        add("raw_crm.opportunity_stage_history", dict(
            history_id=f"H{hist_id:05d}", opportunity_id=opp["opportunity_id"], stage=st,
            amount_usd=round(amt, -2),
            changed_at=datetime.combine(d, datetime.min.time()) + timedelta(hours=random.randint(9, 18))))

    # proposals: for anything that got to Proposal Sent or beyond
    reached = path
    if "Proposal Sent" in reached:
        n_versions = random.choice([1, 1, 2, 2, 3])
        props = []
        for v in range(1, n_versions + 1):
            prop_id += 1
            budget = round(amount * random.uniform(0.9, 1.3) if v < n_versions else amount, -2)
            sent = created + timedelta(days=int(span * (0.45 + 0.1 * v)))
            if v < n_versions:
                status = "Superseded"
            elif is_won:
                status = "Accepted"
            elif is_closed:
                status = "Rejected"
            else:
                status = "Pending"
            p = dict(proposal_id=f"PR{prop_id:05d}", opportunity_id=opp["opportunity_id"],
                     version=v, sent_date=min(sent, AS_OF), total_budget_usd=budget, status=status)
            add("raw_presale.proposals", p)

            # line items
            n_lines = random.choice([1, 2, 2, 3, 3, 4])
            prods = random.choices(list(PRODUCTS), weights=[x[4] for x in PRODUCTS.values()], k=n_lines)
            prods = list(dict.fromkeys(prods))  # dedupe keep order
            shares = rng.dirichlet(np.ones(len(prods)))
            lines = []
            for prod, sh in zip(prods, shares):
                platform, pricing, cpm_rng, vtr, _ = PRODUCTS[prod]
                cost = round(budget * sh, 2)
                line_ip = ip if random.random() < 0.8 else w_choice(IPS)
                # Blippi's live-action host format makes it the go-to for integrations
                if prod == "Branded Content Integration" and random.random() < 0.35:
                    line_ip = "Blippi"
                if pricing == "CPM":
                    cpm = round(random.uniform(*cpm_rng), 2)
                    est = int(cost / cpm * 1000)
                else:
                    cpm = None
                    # guaranteed views priced ~ $35-60 CPV-equivalent per 1k views
                    est = int(cost / random.uniform(35, 60) * 1000)
                pline_id += 1
                li = dict(proposal_line_id=f"PL{pline_id:06d}", proposal_id=p["proposal_id"],
                          product=prod, ip=line_ip, platform=platform, pricing_model=pricing,
                          flight_start=flight_start, flight_end=flight_end,
                          est_impressions=est, proposed_cpm=cpm, proposed_cost_usd=cost)
                add("raw_presale.proposal_line_items", li)
                lines.append(li)
            props.append((p, lines))
        proposals_by_opp[opp["opportunity_id"]] = props

# ---------------------------------------------------------------------------
# Ad server: campaigns, line items, daily delivery (won opps only)
# ---------------------------------------------------------------------------
acc_by_id = {a["account_id"]: a for a in accounts}
camp_seq = 0
as_line_seq = 0
line_outcomes = []  # for finance + research

for opp in opps:
    if not opp["is_won"]:
        continue
    acc = acc_by_id[opp["account_id"]]
    if opp["opportunity_id"] not in proposals_by_opp:
        continue
    accepted, lines = proposals_by_opp[opp["opportunity_id"]][-1]
    fs, fe = opp["_flight"]
    camp_seq += 1
    camp = dict(as_campaign_id=f"C{700000 + camp_seq}", io_number=opp["io_number"],
                advertiser_name=messy(acc["account_name"]),
                campaign_name=f"{acc['account_name'].upper()}_{opp['primary_ip'].replace(' ', '')}_{fs:%y%m}",
                start_date=fs, end_date=fe)
    add("raw_adserver.campaigns", camp)

    for ln_no, pl in enumerate(lines, start=1):
        as_line_seq += 1
        platform, pricing = pl["platform"], pl["pricing_model"]
        booked_impr = pl["est_impressions"]
        gv = booked_impr if pricing == "Flat Fee" else None
        li = dict(as_line_id=f"L{900000 + as_line_seq}", as_campaign_id=camp["as_campaign_id"],
                  line_number=ln_no, product=pl["product"], ip=pl["ip"], platform=platform,
                  pricing_model=pricing, start_date=fs, end_date=fe,
                  booked_impressions=booked_impr if pricing == "CPM" else None,
                  booked_cpm=pl["proposed_cpm"], booked_cost_usd=pl["proposed_cost_usd"],
                  guaranteed_views=gv)
        add("raw_adserver.line_items", li)

        # --- delivery ---
        if fs >= AS_OF:
            line_outcomes.append((opp, acc, li, 0, 0.0))
            continue
        last = min(fe, AS_OF - timedelta(days=1))
        n_days = (fe - fs).days + 1
        if pricing == "CPM":
            mu, sd = DELIVERY_RATE[platform]
            rate = float(np.clip(rng.normal(mu, sd), 0.6, 1.08))
            if platform == "FAST" and random.random() < 0.12:
                rate = random.uniform(0.66, 0.75)        # the ugly ones
            vtr = PRODUCTS[pl["product"]][3]
            daily_base = booked_impr * rate / n_days
            total = 0
            d = fs
            while d <= last:
                wknd = 1.15 if d.weekday() >= 5 else 0.95
                imp = int(max(0, daily_base * wknd * rng.normal(1, 0.08)))
                starts = int(imp * random.uniform(0.96, 0.99))
                comp = int(starts * float(np.clip(rng.normal(vtr, 0.02), 0.3, 0.99)))
                add("raw_adserver.delivery_daily", dict(
                    as_line_id=li["as_line_id"], delivery_date=d, impressions=imp,
                    video_starts=starts, completed_views=comp, watch_time_minutes=None))
                total += imp
                d += timedelta(days=1)
            line_outcomes.append((opp, acc, li, total, rate))
        else:
            # Branded content: views decay from publish date; Blippi over-delivers most
            strength = IPS[pl["ip"]][1]
            total_views = gv * rng.normal(1.15 * strength, 0.12)
            decay = 0.06
            weights = [math.exp(-decay * i) for i in range(n_days)]
            wsum = sum(weights)
            total = 0
            d = fs
            i = 0
            while d <= last:
                v = int(total_views * weights[i] / wsum * rng.normal(1, 0.1))
                v = max(v, 0)
                add("raw_adserver.delivery_daily", dict(
                    as_line_id=li["as_line_id"], delivery_date=d, impressions=v,
                    video_starts=v, completed_views=int(v * random.uniform(0.55, 0.7)),
                    watch_time_minutes=round(v * random.uniform(1.8, 3.2), 1)))
                total += v
                d += timedelta(days=1)
                i += 1
            line_outcomes.append((opp, acc, li, total, total / gv if gv else 0))

# ---------------------------------------------------------------------------
# Research: brand lift studies (completed, larger campaigns)
# ---------------------------------------------------------------------------
lift_base = {"Branded Content Integration": (7.5, 2.0), "YouTube Contextual Pre-roll": (2.8, 1.0),
             "YouTube Shorts Sponsorship": (2.0, 1.0), "FAST Channel Video": (3.8, 1.2),
             "CTV App Video": (4.0, 1.2)}
study_seq = 0
by_io = {}
for opp, acc, li, total, rate in line_outcomes:
    by_io.setdefault(opp["io_number"], []).append((opp, acc, li, total, rate))

for io, rows in by_io.items():
    opp = rows[0][0]
    fs, fe = opp["_flight"]
    if fe >= AS_OF - timedelta(days=21) or opp["amount_usd"] < 60_000:
        continue
    has_bc = any(r[2]["product"] == "Branded Content Integration" for r in rows)
    if random.random() > (0.90 if has_bc else 0.60):
        continue
    study_seq += 1
    # lift driven by the largest line in the campaign
    main = max(rows, key=lambda r: r[2]["booked_cost_usd"])
    mu, sd = lift_base[main[2]["product"]]
    strength = IPS[main[2]["ip"]][1]
    vendor = random.choice(["Kantar (mock)", "Upwave (mock)", "Lucid (mock)"])
    for metric, mult, base_rng in [("Aided Awareness", 1.0, (22, 45)),
                                   ("Brand Favorability", 0.7, (30, 55)),
                                   ("Purchase Intent", 0.55, (12, 30))]:
        ctrl = random.uniform(*base_rng)
        lift = max(-1.0, rng.normal(mu * strength * mult, sd * mult))
        add("raw_research.brand_lift_studies", dict(
            study_id=f"BLS{study_seq:04d}", io_number=io, vendor=vendor, metric=metric,
            control_pct=round(ctrl, 2), exposed_pct=round(min(95, ctrl + lift), 2),
            control_n=random.randint(350, 700), exposed_n=random.randint(350, 700),
            field_start=fe + timedelta(days=3), field_end=fe + timedelta(days=17)))

# Parent panel: quarterly waves
waves = []
for y in (2025, 2026):
    for q in (1, 2, 3, 4):
        if (y, q) <= (2026, 3):
            waves.append((y, q))
base_aware = {"CoComelon": 86, "Blippi": 72, "Little Baby Bum": 58, "Little Angel": 50, "Oddbods": 44,
              "Morphle": 38, "Gecko's Garage": 36, "Supa Strikas": 30, "Go Buster": 24, "Arpo": 20}
trend = {"Blippi": 1.2, "Little Baby Bum": -0.8, "Gecko's Garage": 0.7}  # pts per quarter
age_fit = {"0-2": {"0-2": 1.1, "3-5": 0.95, "6-8": 0.6, "9-11": 0.45},
           "3-5": {"0-2": 0.85, "3-5": 1.1, "6-8": 0.95, "9-11": 0.7},
           "6-8": {"0-2": 0.5, "3-5": 0.85, "6-8": 1.1, "9-11": 1.0},
           "9-11": {"0-2": 0.4, "3-5": 0.6, "6-8": 0.95, "9-11": 1.15}}
for wi, (y, q) in enumerate(waves):
    for ip, (_, _, core) in IPS.items():
        for pab in ["18-24", "25-34", "35-44", "45+"]:
            for cab in ["0-2", "3-5", "6-8", "9-11"]:
                a = (base_aware[ip] + trend.get(ip, 0) * wi) * age_fit[core][cab] + rng.normal(0, 2)
                a = float(np.clip(a, 3, 97))
                add("raw_research.parent_panel", dict(
                    wave=f"{y}-Q{q}", ip=ip, parent_age_band=pab, child_age_band=cab,
                    aware_pct=round(a, 2),
                    favorable_pct=round(float(np.clip(a * rng.normal(0.72, 0.05), 2, 95)), 2),
                    co_view_weekly_pct=round(float(np.clip(rng.normal(38 if cab in ("0-2", "3-5") else 22, 5), 5, 80)), 2),
                    sample_n=random.randint(120, 260)))

# ---------------------------------------------------------------------------
# Finance: bill booked amount monthly; credit under-delivery at campaign end
# ---------------------------------------------------------------------------
inv_seq = 0
for io, rows in by_io.items():
    opp, acc = rows[0][0], rows[0][1]
    fs, fe = opp["_flight"]
    if fs >= AS_OF:
        continue
    months = list(month_iter(fs, min(fe, AS_OF)))
    booked_total = sum(r[2]["booked_cost_usd"] for r in rows)
    per_month = booked_total / len(list(month_iter(fs, fe)))
    # under-delivery credit (CPM lines only, if delivered <95% and campaign ended)
    credit = 0.0
    if fe < AS_OF:
        for _, _, li, total, rate in rows:
            if li["pricing_model"] == "CPM" and li["booked_impressions"]:
                pct = total / li["booked_impressions"]
                if pct < 0.95:
                    credit += (1 - pct) * li["booked_cost_usd"]
    slow = opp["agency_id"] in SLOW_PAYERS
    for mi, (y, m) in enumerate(months):
        inv_seq += 1
        inv_date = date(y, m, 1) + timedelta(days=random.randint(28, 36))
        if inv_date > AS_OF:
            continue
        is_last = (y, m) == (fe.year, fe.month)
        cr = round(credit, 2) if is_last else 0.0
        gross = round(per_month, 2)
        net = round(gross - cr, 2)
        days_to_pay = int(rng.normal(88 if slow else 54, 12))
        paid = inv_date + timedelta(days=days_to_pay)
        if paid <= AS_OF:
            status, paid_s = "Paid", paid
        else:
            status = "Overdue" if (AS_OF - inv_date).days > 60 else "Open"
            paid_s = None
        add("raw_finance.invoices", dict(
            invoice_no=f"INV-{inv_seq:06d}",
            io_number=None if random.random() < 0.02 else io,   # data quality issue
            bill_to_name=messy(acc["account_name"]),
            invoice_date=fmt_us(inv_date), service_month=f"{y}-{m:02d}",
            gross_amount=gross, credit_amount=cr, net_amount=net,
            status=status, paid_date=fmt_us(paid_s)))

# ---------------------------------------------------------------------------
# Market benchmarks (synthetic "third-party" data)
# ---------------------------------------------------------------------------
plat_cpm = {"YouTube": 11.5, "FAST": 23.0, "CTV": 27.0}
plat_vtr = {"YouTube": 0.70, "FAST": 0.92, "CTV": 0.94}
for (y, q) in waves:
    for cat, params in CATEGORIES.items():
        season = params[3] if q == 4 else 1.0
        for plat in plat_cpm:
            add("raw_market.category_benchmarks", dict(
                quarter=f"{y}-Q{q}", category=cat, platform=plat,
                benchmark_cpm=round(plat_cpm[plat] * (1.18 if q == 4 else 1.0) * rng.normal(1, 0.05), 2),
                benchmark_vtr=round(float(np.clip(plat_vtr[plat] + rng.normal(0, 0.015), 0.4, 0.99)), 3),
                est_kids_category_spend_musd=round(params[0] * 900 * season * (1.08 if y == 2026 else 1.0)
                                                   * rng.normal(1, 0.06) / 4, 1)))

# ---------------------------------------------------------------------------
# Household measurement (mock iSpot-style, COPPA-safe)
#
# One row per CPM line that has delivered. Everything is HOUSEHOLD-level:
# there are no child identifiers, device IDs, or individual viewer records,
# mirroring what can legally be measured on made-for-kids content (COPPA
# restricts profiling under-13s, not household-level measurement or
# identifying the adult co-viewer).
#
# Uses its OWN random generators so adding this section can't shift any of
# the data generated above: every existing table stays byte-for-byte identical.
# ---------------------------------------------------------------------------
m_random = random.Random(SEED + 101)
m_rng = np.random.default_rng(SEED + 101)

# share of impressions in households with kids, by the IP's core child age
KIDS_HH_SHARE = {"0-2": 0.97, "3-5": 0.955, "6-8": 0.93, "9-11": 0.90}
# share of impressions with an adult co-viewing (the parent = economic buyer)
COVIEW_BY_PRODUCT = {"CTV App Video": 0.62, "FAST Channel Video": 0.58,
                     "YouTube Contextual Pre-roll": 0.41, "YouTube Shorts Sponsorship": 0.24}
COVIEW_AGE_ADJ = {"0-2": 0.05, "3-5": 0.02, "6-8": -0.04, "9-11": -0.08}
# avg frequency (impressions per household): kids re-watch, big screens most
FREQ_BY_PRODUCT = {"CTV App Video": (3.8, 0.4), "FAST Channel Video": (3.5, 0.4),
                   "YouTube Contextual Pre-roll": (2.8, 0.3), "YouTube Shorts Sponsorship": (2.1, 0.25)}
# share of reached households that never had / cut pay TV
CORD_FREE_BY_PLATFORM = {"CTV": (0.73, 0.03), "FAST": (0.71, 0.03), "YouTube": (0.66, 0.04)}
# share of reached households the advertiser's linear TV buy ALSO reached
LINEAR_OVERLAP_BY_PLATFORM = {"CTV": (0.12, 0.03), "FAST": (0.14, 0.03), "YouTube": (0.20, 0.04)}

for opp, acc, li, total, rate in line_outcomes:
    if li["pricing_model"] != "CPM" or total <= 0:
        continue
    fs, fe = li["start_date"], li["end_date"]
    core_age = IPS[li["ip"]][2]
    product, platform = li["product"], li["platform"]

    # vendor counts slightly fewer impressions than the ad server (normal
    # 1-5% measurement gap from IVT filtering / unmatched devices)
    measured = int(total * float(np.clip(m_rng.normal(0.975, 0.012), 0.93, 1.0)))
    freq = float(np.clip(m_rng.normal(*FREQ_BY_PRODUCT[product]), 1.4, 5.5))
    households = int(measured / freq)
    kids_share = float(np.clip(m_rng.normal(KIDS_HH_SHARE[core_age], 0.012), 0.85, 0.995))
    coview = float(np.clip(m_rng.normal(COVIEW_BY_PRODUCT[product] + COVIEW_AGE_ADJ[core_age], 0.04),
                           0.08, 0.85))
    cord_free = float(np.clip(m_rng.normal(*CORD_FREE_BY_PLATFORM[platform]), 0.4, 0.9))
    overlap = float(np.clip(m_rng.normal(*LINEAR_OVERLAP_BY_PLATFORM[platform]), 0.03, 0.4))

    add("raw_measurement.household_reach", dict(
        as_line_id=li["as_line_id"],
        vendor="iSpot (mock)",
        measured_through=min(fe, AS_OF - timedelta(days=1)),
        measured_impressions=measured,
        households_reached=households,
        impressions_in_kids_households=int(measured * kids_share),
        impressions_with_adult_coviewer=int(measured * coview),
        cord_free_households=int(households * cord_free),
        households_also_reached_by_linear=int(households * overlap)))

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
for st, rows in tables.items():
    schema, table = st.split(".")
    path = OUT / schema / f"{table}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    print(f"{st:45s} {len(rows):>7,} rows")