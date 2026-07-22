#!/usr/bin/env python3
"""Merge parsed FPV orders (orders_new.csv) into the orders.csv ledger.

Deterministic and safe to re-run: dedups by (vendor, order_number, item) and
preserves the hand-filled `build` / `notes` columns and any `?` in `flag`.
"""

COLUMNS = [
    "vendor", "order_date", "order_number", "item", "qty",
    "unit_price", "line_total", "category", "build", "flag",
    "source", "notes",
]

KEY_FIELDS = ("vendor", "order_number", "item")


def normalize(row):
    """Return a dict with every COLUMNS key present, as trimmed strings."""
    out = {}
    for col in COLUMNS:
        val = row.get(col, "")
        out[col] = "" if val is None else str(val)
    return out


def row_key(row):
    return tuple(row.get(f, "").strip().lower() for f in KEY_FIELDS)


def merge_orders(existing, new):
    merged = {}
    stats = {"existing": len(existing), "added": 0, "updated": 0}
    for row in existing:
        merged[row_key(row)] = normalize(row)
    for row in new:
        key = row_key(row)
        if key in merged:
            prev = merged[key]
            row = normalize(row)
            row["build"] = prev["build"]
            row["notes"] = prev["notes"]
            row["flag"] = prev["flag"] or row["flag"]
            merged[key] = row
            stats["updated"] += 1
        else:
            merged[key] = normalize(row)
            stats["added"] += 1
    rows = sorted(
        merged.values(),
        key=lambda r: (r["order_date"], r["vendor"].lower(), r["order_number"]),
    )
    return rows, stats
