# fpv_cli_dumps

Betaflight CLI backups for my FPV quads, plus a derived fleet inventory.

## About

I use AI to help build, tune, and troubleshoot my FPV quads — extracting fleet configs from
Betaflight dumps, decoding blackbox flight logs, and diagnosing failures. That includes a motor
desync detector that reads bidirectional-DShot eRPM telemetry to catch a motor that's commanded to
spin hard but isn't — the kind of fault that only shows up under flight load. I write about it on
Substack: [Tracking Down a Flight Failure](https://irekromaniuk.substack.com/p/tracking-down-a-flight-failure-an),
the story behind the Kronos motor-desync analysis in this repo.

## Layout

```
backups/                 Betaflight CLI dumps (BTFL_cli_*.txt), one or more per quad
fpv_quads.csv            History — one row per dump (unchanged re-dumps collapsed), newest per quad flagged 'latest'
fpv_quads_latest.csv     One row per quad, newest dump only
rates.csv                Active rateprofile decoded to real deg/s (centre sensitivity, max rate, curve at 25/50/75% stick) — only quads that are active and have a discipline set
rate_presets.csv         Hand-maintained named rateprofiles ('house-race', ...) that quads are meant to share; assigned per quad via hardware.csv's rate_preset
flights.csv              One row per decoded blackbox flight (duration, sag, current, mAh, flags)
hardware.csv             Hand-maintained per-quad build details (ESC, motors, props) + size class, status, discipline, aliases, rate_preset — none of it in dumps
orders.csv               FPV parts ledger, one row per ordered line item, built from Gmail by the fpv-orders-update skill; 'build' (quad/'spare'/blank) and 'notes' hand-maintained, other columns from order emails, re-runs only add new — gitignored (personal purchase history; kept local, not committed)
FLEET_SUMMARY.md         Overview: fleet table, rollups, "needs attention", rates, hardware, flights
blackbox/                Raw .BBL/.BFL flight logs — gitignored (large binaries; not committed)
.claude/skills/fpv-fleet-update/   Skill that regenerates the derived files above
.claude/skills/fpv-orders-update/  Skill that builds orders.csv from Gmail order confirmations
```

## Updating

Drop a new `BTFL_cli_*.txt` dump into `backups/` (any subfolder works — the parser scans
recursively), then regenerate the inventory:

```bash
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

The script is the single source of truth: it only reads the dumps and rewrites `fpv_quads.csv`,
`fpv_quads_latest.csv`, `rates.csv` and `FLEET_SUMMARY.md`, so it is safe to re-run any time.
Don't hand-edit the generated files.

Values are extracted from Betaflight `diff all` output, which only records settings that differ
from firmware defaults — a blank cell means the setting is at its firmware default.

## What counts as a quad

The CLI dump is the single source of truth. A quad appears in the inventory only once there is a
`BTFL_cli_*.txt` dump for it — the Fleet table, rollups, and CSVs are built strictly from the dumps.
A quad tracked only in a separate build spreadsheet won't show up until its dump is added; adding the
dump is what registers it.

Each quad is keyed by the `craft_name` set in its dump (normalized — case, spaces, and underscores
are ignored), falling back to the filename label, then the board name. Setting a real craft name in
Betaflight makes the key stable across re-flashes and file renames.

**Renaming a quad** in Betaflight would otherwise split one airframe into two entries with two
half-histories. To fold them, rename the `quad` cell in `hardware.csv` and list the old name in that
row's `aliases` column (`;`-separated for repeat renames); old dumps and old blackbox flights are
remapped onto the current name, while each history row keeps the `craft_name` it was dumped under.

## Hardware details

`hardware.csv` holds per-quad build details that Betaflight dumps can't carry (ESC/stack, motors,
props, camera, VTX, cells, weight) plus five curated columns — `class` (size bucket), `status`
(lifecycle), `discipline` (what it's flown for), `aliases` (former craft names), and `rate_preset`
(the rateprofile this quad is meant to fly). It is an annotation, never a source: it only
decorates a quad that a dump already put in the inventory, joined by the same normalized name. A row
whose name matches no dump is shown in the summary's Hardware section flagged as such, but does not
create a fleet entry. Edit it by hand; the generator reads it but never writes it.

## Rates

Betaflight stores rates as raw integers whose meaning depends on the rate type, and `diff all` omits
anything left at a default — so a quad that never had its rates set dumps no rate lines at all.
`rates.csv` decodes them into real deg/s: centre sensitivity, max rate, and the curve at 25/50/75%
stick. Two things that makes visible:

- **Stock rates are not one thing.** The firmware default flipped at 4.3 (before: BETAFLIGHT rc 100 /
  srate 70, centre 200 °/s; after: ACTUAL rc 7 / rates 67, centre 70 °/s), so defaults are filled per
  the firmware that wrote each dump rather than shown as a blank that reads like "not tracked".
- **The same endpoints can be a different quad.** ACTUAL and BETAFLIGHT draw different curves between
  the same centre and max, so two profiles can match at both ends and still differ ~40% at mid-stick.
  Compare the decoded deg/s, not the stored numbers.

Rows are limited to quads that are `active` with a `discipline` set, grouped by discipline then class
— rates are only worth reading side by side against quads flown the same way, and a 1S whoop at
667 °/s is not the same setup as a 6S five-inch at 667 °/s. The filter applies to the view only;
"needs attention" still checks every quad.

`rate_presets.csv` names rateprofiles that several quads are meant to share (`house-race`,
`whoop-race`); `rate_preset` in `hardware.csv` assigns one. Nothing in a dump records what a quad was
*supposed* to be, so this is the one place intent lives — a quad whose dump disagrees with its preset
is flagged in the summary, which is how a re-flash that silently reset rates gets caught on the bench
instead of in the air.

## Blackbox flight logs

Drop `.BBL`/`.BFL` logs into `blackbox/` (gitignored), then decode them into `flights.csv`:

```bash
python3 -m venv .venv && .venv/bin/pip install orangebox   # one-time
python3 .claude/skills/fpv-fleet-update/scripts/update_flights.py   # -> flights.csv
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py     # folds Flights into FLEET_SUMMARY.md
```

Raw logs are large and stay out of git; `flights.csv` is the committed, durable record.

## Orders ledger

`orders.csv` is a parts-purchase ledger — one row per ordered line item — built from Gmail order
confirmations by the `fpv-orders-update` skill (`.claude/skills/fpv-orders-update/`). It's a hybrid
file like `hardware.csv`: most columns come from the order emails, but `build` (the quad a part went
into, or `spare`, or blank) and `notes` are hand-maintained and never overwritten. Re-running only
adds new orders — the merge dedups by `(vendor, order_number, item)` and preserves your edits.

It holds personal purchase history (prices, order numbers), so it's **gitignored and kept local** —
unlike the other CSVs, it is not committed. It lives only on your machine.

To refresh it, invoke the skill (it needs Gmail authorized). It searches each known vendor from the
newest date already in `orders.csv`, extracts line items, and folds them in via:

```bash
python3 .claude/skills/fpv-orders-update/scripts/merge_orders.py
```

Don't hand-edit `orders.csv` except the `build` and `notes` columns.

### Adding a vendor

The vendor registry lives entirely in the skill's `SKILL.md` — the merge script is vendor-agnostic,
so no code changes. To register a new store, edit `.claude/skills/fpv-orders-update/SKILL.md`:

1. Add the vendor's name to the `description:` list in the YAML frontmatter (this makes the skill
   trigger when you mention that vendor).
2. Add a row to the **Vendors and senders** table (`vendor short name | sender domain | note`),
   marked "verify sender on first run" until a real search confirms the actual sending address.

On the next run the skill's per-vendor search loop picks it up automatically. For mixed-catalog
sellers (Amazon, DJI) the skill applies a best-effort FPV-only filter and flags uncertain items `?`.
