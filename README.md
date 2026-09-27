# Elite Builds LLC - RM Signal Extraction

Quick context: Elite Builds is a Utah construction firm. On paper they look
like any other small contractor, but the assignment's market snippet gives
one useful comparison point - the industry is eating a 15% material cost
spike and margins have compressed to ~4%. Once you check the transaction
data against that, the picture changes a lot. This repo is my attempt to
make that comparison mechanical instead of something an RM has to eyeball.

## How it's organized

- `scripts/extract_signals.py` - reads the transaction data and computes
  the actual numbers (vendor pricing trend, margin, expense pace, growth
  spend split).
- `output/customer_segments_raw_metrics.json` - everything the script
  computes, unfiltered. I kept this mostly for my own sanity checking.
- `output/customer_segments.json` - the trimmed version meant for the RAG
  system. This is the one the assignment actually asks for.
- `README.md` - this file.

## What I found

**Vendor pricing.** Elite Builds pays two repeat suppliers, Intermountain
Lumber and Steel Supply Co. Both show *lower* per-invoice cost the second
time around in the month (-8.3% and -5%), while the industry snippet says
material costs are up 15% broadly. That's the clearest single signal in
the data - either they locked in pricing early, buy in bulk, or have some
other leverage most of their competitors don't.

**Margin.** Revenue minus operating spend (Inventory + Operations) gives
roughly a 55.8% margin, against the reported 4% industry average. That gap
is big enough that I'd want to sanity-check it against a longer time
window before repeating it to a client, but for one month of data it's a
strong number.

**Expense pace.** I split the month into first-half / second-half and
compared operating spend. It dropped about 10% from the first half to the
second. The snippet mentions banks tightening credit on firms with high
"expense velocity" - this firm is trending the opposite direction, which
is worth flagging explicitly since it directly counters what the market
report says lenders are worried about.

**Growth reinvestment.** About 20.6% of total spend went to categories I'd
call deliberate investment (equipment lease, software, marketing) rather
than pure upkeep. Not huge, but consistent - it's not one big one-off
purchase, it shows up across the month.

## Assumptions I made

- Interest income isn't counted as revenue for margin purposes - it's cash
  in, but not from the actual business.
- The savings transfer is excluded from "spend" entirely. Moving money to
  savings isn't the same as spending it.
- One month is thin. If I were doing this for real I'd want 6-12 months
  and ideally unit pricing (cost per unit of material) instead of invoice
  totals, since invoice size also moves with how big the project is that
  month, not just price per unit.
- "Expense velocity" isn't formally defined anywhere in the snippet, so
  I approximated it as first-half-of-month vs second-half-of-month spend.
  A production version would probably use a rolling average instead.

## Task 3 - the system prompt

This is the exact prompt I used to shape the Task 2 JSON output:

```
You are a credit risk analyst writing internal notes for a bank
relationship manager. You are not writing to the customer - this is
for the RM's use before a client call.

Turn the transaction-derived metrics you're given into one JSON object
for a RAG lookup system. Requirements:

- Valid JSON only. Nothing before or after it, no markdown fences.
- Keep the whole thing under 300 tokens.
- Three sections: behavioral (spending trends and margins), demographic
  (firm size, geography, payroll pattern), psychographic (tools they
  use, growth orientation, vendor relationships, general risk read).
- Only include things that trace back to the transaction data or the
  market benchmark you were given - don't make up details that aren't
  supported by the input.
- Short values, snake_case where it makes sense, numbers over long
  sentences, to stay inside the token limit.
- Add a short "top_signals" list at the end, max 2 items, plain
  language, no jargon.
- Keep the tone flat and analytical. No sales language.
```

## Product recommendation + RM hook

**Product:** Working capital line of credit, sized for inventory
pre-buying, plus a treasury sweep account given how consistently they
move cash to savings.

**Why:** they already have vendor leverage most competitors don't. A
credit line lets them lock in bulk material pricing now, before the next
round of industry-wide inflation catches up, which turns a one-month
observation into an actual ongoing advantage.

**Hook, for the RM to say out loud:**

> "Most builders we work with in Utah are getting hit by a 15% jump in
> material costs right now - yours actually went down. That's the kind
> of track record we can extend more credit against, so let's talk about
> a line sized to let you buy lumber and steel in bulk before the market
> catches up to where you already are."

## Running it

```
cd scripts
python3 extract_signals.py
```

Prints the full metrics and writes them to `output/customer_segments_raw_metrics.json`.
