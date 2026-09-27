import json
import os
from collections import defaultdict

# Numbers pulled straight from the Q1 2026 market snippet in the assignment.
INDUSTRY_INFLATION = 0.15      # material costs up 15% industry-wide
INDUSTRY_MARGIN = 0.04         # avg net margin for mid-sized firms

# how I'm splitting spend categories - Growth/Tech/Equipment feel like
# deliberate investment, Operations/Inventory feel like keeping-the-lights-on
GROWTH_CATS = {"Growth", "Tech/Growth", "Equipment"}
RUNNING_COSTS = {"Operations", "Inventory"}


def load(path):
    with open(path) as f:
        return json.load(f)


def vendor_trend(txns):
    # group repeat inventory payments by vendor name and see if price per
    # invoice is rising or falling over the month
    vendors = defaultdict(list)
    for t in txns:
        if t["category"] == "Inventory":
            vendors[t["description"]].append((t["date"], abs(t["amount"])))

    out = {}
    for name, pmts in vendors.items():
        pmts.sort()
        if len(pmts) < 2:
            continue
        start, end = pmts[0][1], pmts[-1][1]
        change = (end - start) / start
        out[name] = {
            "payments": pmts,
            "change_vs_first_invoice": round(change, 3),
            "cheaper_than_industry_trend": change < INDUSTRY_INFLATION,
        }
    return out


def margin_check(txns):
    rev = sum(t["amount"] for t in txns if t["category"] == "Revenue")
    costs = sum(abs(t["amount"]) for t in txns if t["category"] in RUNNING_COSTS)
    profit = rev - costs
    margin = profit / rev if rev else 0
    return {
        "revenue": rev,
        "running_costs": costs,
        "operating_margin_pct": round(margin * 100, 1),
        "vs_industry_avg_4pct": round(margin / INDUSTRY_MARGIN, 1),
    }


def expense_pace(txns):
    # crude but effective: does spend accelerate or slow down across the
    # month? banks flag firms with rising ("high velocity") expenses, so
    # I'm checking which direction this firm is moving
    watch = RUNNING_COSTS | {"Equipment"}
    early, late = 0, 0
    for t in txns:
        if t["category"] not in watch:
            continue
        day = int(t["date"][-2:])
        amt = abs(t["amount"])
        if day <= 15:
            early += amt
        else:
            late += amt
    pace_change = (late - early) / early if early else 0
    return {
        "spend_days_1_15": early,
        "spend_days_16_31": late,
        "pace_change_pct": round(pace_change * 100, 1),
        "risk_flag": pace_change > INDUSTRY_INFLATION,  # true = bad sign for a lender
    }


def reinvestment_split(txns):
    by_cat = defaultdict(float)
    for t in txns:
        if t["amount"] < 0 and t["category"] != "Savings":
            by_cat[t["category"]] += abs(t["amount"])

    growth_spend = sum(v for k, v in by_cat.items() if k in GROWTH_CATS)
    total_spend = sum(by_cat.values())
    ratio = growth_spend / total_spend if total_spend else 0
    return {
        "by_category": dict(by_cat),
        "growth_spend": growth_spend,
        "total_spend": total_spend,
        "growth_share_pct": round(ratio * 100, 1),
    }


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    txns = load(os.path.join(here, "transactions.json"))

    signals = {
        "resilience_alpha": {
            "vendor_trend": vendor_trend(txns),
            "margin": margin_check(txns),
            "expense_pace": expense_pace(txns),
        },
        "growth_reinvestment": reinvestment_split(txns),
    }

    out_dir = os.path.join(here, "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "customer_segments_raw_metrics.json")
    with open(out_file, "w") as f:
        json.dump(signals, f, indent=2)

    print(json.dumps(signals, indent=2))
    print(f"\nsaved to {out_file}")

    # quick sanity print - these are the two headline numbers I'd actually
    # say out loud to an RM
    margin = signals["resilience_alpha"]["margin"]
    pace = signals["resilience_alpha"]["expense_pace"]
    print(f"\nMargin is {margin['operating_margin_pct']}% vs industry's 4% average")
    print(f"Expense pace changed {pace['pace_change_pct']}% through the month "
          f"(negative = slowing down, which is the good direction here)")


if __name__ == "__main__":
    main()
