---
name: fpv-orders-update
description: >-
  Search the pilot's Gmail for FPV parts orders and record them as line items in orders.csv,
  a hand-maintainable parts ledger (each part links to a build or stays a spare). Use whenever
  the user asks to find, refresh, import, or update their FPV orders / purchases / parts ledger
  from email, mentions a new order from a vendor (flyfive33, GetFPV, Pyrodrone, RaceDayQuads,
  Webleedfpv, Wrecked, Amazon), or asks "what parts did I buy". Runs interactively where Gmail
  is authorized; it reads order-confirmation emails and merges them into orders.csv.
---

# FPV Orders Update

This skill builds and refreshes `orders.csv` — a ledger of FPV parts the pilot has ordered, one
row per purchased line item. Parts are linked to builds by hand (`build` column) or left as
`spare`. It complements `fpv-fleet-update` (which tracks the quads themselves from CLI dumps).

`orders.csv` is a hybrid file, like `hardware.csv`: most columns are filled from email, but
`build` and `notes` are hand-maintained and must never be clobbered. That is why parsed orders
go through a staging file and a deterministic merge — re-running is always safe.

## Columns

`vendor, order_date, order_number, item, qty, unit_price, line_total, category, build, flag, source, notes`

- `category` — one of: motor, prop, esc, frame, vtx, cam, battery, rx, tool, misc.
- `build` — **hand-filled**: a quad name, `spare`, or blank (= unassigned). Never overwritten.
- `flag` — `?` for uncertain Amazon items or a shaky parse; else blank. A `?` is never cleared.
- `source` — Gmail message id (traceability + dedup fallback).
- `notes` — **hand-filled**, preserved across runs.
- Prices are bare USD numbers (no `$`). Note any non-USD order in `notes`.

## Vendors and senders

| vendor short name | sender domain | note |
|-------------------|---------------|------|
| flyfive33 | flyfive33.com | verify on first run |
| GetFPV | getfpv.com | |
| Pyrodrone | pyrodrone.com | |
| RaceDayQuads | racedayquads.com | |
| Webleedfpv | webleedfpv.com | verify on first run |
| Wrecked | wreckedfpv.com | **guess — verify on first run** |
| Amazon | amazon.com | order-confirm / shipment addresses |

When a sender is confirmed on a real run, update this table so later runs skip discovery.

## Procedure

1. **Determine the search window.**
   - If `orders.csv` exists, read the newest `order_date` in it and search Gmail from a few days
     before that date (overlap is fine — the merge dedups). 
   - If it does not exist (first run), use `after:2021/01/01`.

2. **For each vendor**, search order-confirmation threads with the Gmail MCP tools, e.g.:
   `mcp__claude_ai_Gmail__search_threads` with query
   `from:getfpv.com subject:(order OR confirmation OR receipt OR shipped) after:2021/01/01`.
   - If the sender is marked "verify", first run a broad search (e.g. `from:wrecked`) to confirm
     the real sending address, then narrow.
   - Read the confirmation body with `get_thread` / `get_message`. Prefer the order/confirmation
     email (it has line items + prices); use shipping notices only to fill gaps.

3. **Extract each line item** into a staging row: `vendor, order_date, order_number, item, qty,
   unit_price, line_total, category, source`. Leave `build` and `notes` blank. Choose `category`
   from the fixed list above.

4. **Amazon** — best-effort FPV-only filter: include only items that read as FPV / drone gear
   (batteries, connectors, chargers, props, motors, tools, etc.). Set `flag = ?` on anything you
   are not confident is FPV gear. Drop clearly non-FPV items.

5. **Write the staging file** `orders_new.csv` (same columns as `orders.csv`) using the `csv`
   module — never hand-format CSV.

6. **Merge** into the ledger:
   ```bash
   python3 .claude/skills/fpv-orders-update/scripts/merge_orders.py
   ```
   Run this from the **repo root** — it reads/writes the relative `orders.csv` and
   `orders_new.csv` paths by default.
   The script dedups by `(vendor, order_number, item)`, preserves hand-filled `build` / `notes`,
   keeps any existing `?` flag, sorts by date, and prints a summary (added / updated / total).

7. **Clean up** the staging file and report the summary to the user, reminding them they can now
   fill in the `build` column (quad name or `spare`) for the new rows.

## Notes

- `orders_new.csv` is transient and gitignored; only `orders.csv` is committed.
- Do not hand-edit `orders.csv` except the `build` and `notes` columns.
- Tests for the merge script: `.venv/bin/pytest .claude/skills/fpv-orders-update/scripts/test_merge_orders.py`.
- Future enhancement (not yet built): auto-guess `build` from order timing vs. quad dump dates.
