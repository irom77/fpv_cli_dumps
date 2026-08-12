# fpv_cli_dumps

Betaflight CLI backups for my FPV quads, plus a derived fleet inventory.

## About

I use AI to help build, tune, and troubleshoot my FPV quads — extracting fleet configs from
Betaflight dumps, decoding blackbox flight logs, and diagnosing failures. That includes a motor
desync detector that reads bidirectional-DShot eRPM telemetry to catch a motor that's commanded to
spin hard but isn't — the kind of fault that only shows up under flight load. I write about it on
Substack: [Tracking Down a Flight Failure](https://irekromaniuk.substack.com/p/tracking-down-a-flight-failure-an),
the story behind the Kronos motor-desync analysis in this repo.

The same idea runs the other way for racing: `specs.csv` encodes a class rulebook (MultiGP Freedom
Spec so far) and every quad in scope is checked against it on each run, so "would this pass tech
check?" is answered from the dumps rather than from memory on race morning. It catches the
settings that are invisible precisely because they were never touched — a `diff all` says nothing
at all about an RPM limiter that was never switched on.

## Layout

```
backups/                 Betaflight CLI dumps (BTFL_cli_*.txt), one or more per quad
CLI_SNIPPETS.md          Paste-ready, reusable Betaflight CLI presets derived from the fleet
velocidrone.md           VelociDrone profiles matched to the active 5-inch race quads
fpv_quads.csv            History — one row per dump (unchanged re-dumps collapsed), newest per quad flagged 'latest'
fpv_quads_latest.csv     One row per quad, newest dump only
rates.csv                Active rateprofile decoded to real deg/s (centre sensitivity, max rate, curve at 25/50/75% stick) — only quads that are active and have a discipline set
modes.csv                Configured Betaflight modes, AUX channels and activation ranges — only active quads with discipline and class set
rate_presets.csv         Hand-maintained named rateprofiles ('house-race', ...) that quads are meant to share; assigned per quad via hardware.csv's rate_preset
flights.csv              One row per decoded blackbox flight (duration, sag, current, mAh, flags)
hardware.csv             Hand-maintained per-quad build details (ESC, motors, props) + size class, status, discipline, aliases, rate_preset — none of it in dumps
specs.csv                Hand-maintained race-class rulebook (Freedom Spec, ...), one row per requirement, scoped to the class/discipline it applies to
compliance_<spec>.csv    Generated — one file per spec, one row per quad in scope: per-requirement verdict plus what's missing / to confirm
orders.csv               FPV parts ledger, one row per ordered line item, built from Gmail by the fpv-orders-update skill; 'build' (quad/'spare'/blank) and 'notes' hand-maintained, other columns from order emails, re-runs only add new — gitignored (personal purchase history; kept local, not committed)
FLEET_SUMMARY.md         Overview: fleet table, rollups, "needs attention", rates, spec compliance, hardware, flights
blackbox/                Raw .BBL/.BFL flight logs — gitignored (large binaries; not committed)
upgrades/                Reproducible firmware upgrade records: binaries, restores, provenance and verification
.claude/skills/fpv-fleet-update/   Skill that regenerates the derived files above
.claude/skills/fpv-orders-update/  Skill that builds orders.csv from Gmail order confirmations
```

## Updating

Drop a new `BTFL_cli_*.txt` dump into `backups/` (any subfolder works — the parser scans
recursively), then regenerate the inventory:

```bash
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

The script is the single source of truth: it only reads the dumps and the hand-maintained CSVs, and
rewrites `fpv_quads.csv`, `fpv_quads_latest.csv`, `rates.csv`, `modes.csv`, `compliance_<spec>.csv` and
`FLEET_SUMMARY.md`, so it is safe to re-run any time. Don't hand-edit the generated files.

Values are extracted from Betaflight `diff all` output, which only records settings that differ
from firmware defaults — a blank cell means the setting is at its firmware default.

## Firmware upgrade records

[`upgrades/`](upgrades/) preserves upgrade-specific artifacts that cannot be reconstructed from a
CLI dump alone. Each package records the exact firmware binary and checksum, source/config commits,
selective restore, flashing procedure and post-flash evidence. The first package documents the
[OpenRacer KAACK V19 upgrade](upgrades/OPENRACER_KAACK_V19_UPGRADE/README.md).

## CLI snippets

[`CLI_SNIPPETS.md`](CLI_SNIPPETS.md) is the reusable, paste-ready side of the repository. It starts
with separate standard OSD layouts for analog (`30x13`) and digital MSP DisplayPort (`50x18`),
distilled from the recurring settings in the backups. It is also the home for future named rate,
mode, battery, race and blackbox presets.

The snippets intentionally exclude settings that should not be copied blindly between flight
controllers, including UART assignments, receiver configuration, VTX power/channel and craft
identity. Before applying one, save a fresh `diff all`, paste only the relevant block, check the CLI
for rejected settings, enter `save`, and verify the result on the bench before flying.

## VelociDrone setup

[`velocidrone.md`](velocidrone.md) translates the active 5-inch race builds into practical
VelociDrone profiles. It includes the shared `house-race` rates, separate OpenRacer and Lightswitch
PID/TPA baselines, prop and power settings, and a calibration procedure for simulator-only controls
such as percentage-based weight, drag and camera FOV.

Values available in the CLI dumps or `hardware.csv` are identified explicitly. Settings that the
repository cannot determine, including camera angle and the selected VelociDrone model's weight
baseline, are left as measured or feel-based calibration rather than presented as exact values.

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

## Modes

`modes.csv` decodes each `aux` line in the newest CLI backup into its Betaflight mode name, AUX
channel, and exact activation range. It includes the permanent numeric mode ID, OR/AND logic,
linked-mode fields, firmware version, and source dump so custom or newer firmware remains
auditable. Unknown IDs are labeled rather than discarded. `range_visual` renders the same
900–2100 slider as a compact text bar; each character covers 50 µs, with `▌` and `▐` retaining
Betaflight's 25 µs half-steps. Inactive cells use `░` rather than punctuation so the bar stays
aligned in GitHub's proportional CSV preview. The numeric endpoints immediately after it remain authoritative.
Repeated `quad`, `discipline`, and `class` cells are blank for readability; a blank means “same as
the row above”, not missing data.

Like the rates view, it is grouped by discipline then class and quad. Rows are limited to quads
that are `active` with both `discipline` and `class` set. Within each quad, rows are grouped by AUX
channel and ordered from the lowest to highest activation range, so all positions of one switch sit
together. Channel labels use consistent markers (`🔴 AUX1`, `🔵 AUX2`, `🟢 AUX3`, `⚫ AUX4`; white
for any higher channel). The backup cannot identify the transmitter's physical switch label or
prove that a configured mode was used during a flight.

`rate_presets.csv` names rateprofiles that several quads are meant to share (`house-race`,
`whoop-race`); `rate_preset` in `hardware.csv` assigns one. Nothing in a dump records what a quad was
*supposed* to be, so this is the one place intent lives — a quad whose dump disagrees with its preset
is flagged in the summary, which is how a re-flash that silently reset rates gets caught on the bench
instead of in the air.

## Race class specs

`specs.csv` is a rulebook: one row per requirement of one racing class, tagged with the `class` and
`discipline` it applies to (MultiGP Freedom Spec applies to `5-inch` / `race`). Each row carries a
declarative check — a regex against a `hardware.csv` field or a parsed dump setting, a minimum
weight, or `manual` for rules no file can answer. The generator runs every rule against every quad
in scope, writes a **Spec compliance** section into `FLEET_SUMMARY.md`, and emits the same table as
`compliance_<spec>.csv` — quads down the side, requirements across, plus `verdict`, `missing` and
`to_confirm` columns. Adding a class is adding rows; there is no code to change.

There's a file per spec rather than one combined one because the columns *are* the requirements:
two classes don't share them, so merging would produce a sparse union of every rule ever written.
The flip side is that deleting a spec from `specs.csv` leaves its `compliance_*.csv` behind — the
generator only writes, so remove that by hand.

Results are four-valued, and the difference between the last three is the point:

| | Meaning |
|---|---|
| ✓ | Meets the rule |
| ✗ | Does not — the airframe would be turned away at tech check. Only these reach "needs attention" |
| ? | Nothing recorded to judge by — a gap in `hardware.csv`, not in the quad |
| · | Only checkable by hand (LED count, the prop an event calls) |

Two things keep `?` honest rather than letting missing data read as failure. A rule can carry an
`evidence` regex meaning "this field states the kind of fact being tested"; `esc_stack = "Hobbywing
XRotor F722 (45A 4-in-1 ESC)"` names no ESC firmware at all, so an ESC-firmware rule returns `?`,
not `✗`. And the weight rule never fails: a class minimum is a race-ready figure while
`hardware.csv` records dry weight, and a 6S race pack is 200–260 g, so a low figure means "weigh it
with the pack in", not "too light".

That last one is worth a note, because the published Freedom Spec rules state the minimum bare —
"533g Minimum Weight" — while the same MultiGP table qualifies Open as "800g **AUW**" and Pro Spec
as "1200 grams **AUW**". Race-ready is the only reading that works arithmetically: a 5-inch 6S
airframe is 270–310 g dry, so a dry 533 g floor would exclude the whole class.

The check that pays for the whole file is `rpm_limit`. Freedom Spec is built on KAACK Betaflight's
RPM limiter, and a limiter that was never switched on writes **nothing** to a `diff all` — the same
blank as a setting you never touched. Judging that blank against the firmware default (`OFF`, with
KAACK's `rpm_limit_value` already at 18000) is what turns an invisible non-compliance into a line
on the bench list.

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
