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
flights.csv              One row per decoded blackbox flight (duration, sag, current, mAh, flags)
hardware.csv             Hand-maintained per-quad build details (ESC, motors, props) not in dumps
FLEET_SUMMARY.md         Overview: fleet table, rollups, "needs attention", hardware, flights
blackbox/                Raw .BBL/.BFL flight logs — gitignored (large binaries; not committed)
.claude/skills/fpv-fleet-update/   Skill that regenerates the derived files above
```

## Updating

Drop a new `BTFL_cli_*.txt` dump into `backups/` (any subfolder works — the parser scans
recursively), then regenerate the inventory:

```bash
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

The script is the single source of truth: it only reads the dumps and rewrites the two CSVs and
`FLEET_SUMMARY.md`, so it is safe to re-run any time. Don't hand-edit the generated files.

Values are extracted from Betaflight `diff all` output, which only records settings that differ
from firmware defaults — a blank cell means the setting is at its firmware default.

## Blackbox flight logs

Drop `.BBL`/`.BFL` logs into `blackbox/` (gitignored), then decode them into `flights.csv`:

```bash
python3 -m venv .venv && .venv/bin/pip install orangebox   # one-time
python3 .claude/skills/fpv-fleet-update/scripts/update_flights.py   # -> flights.csv
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py     # folds Flights into FLEET_SUMMARY.md
```

Raw logs are large and stay out of git; `flights.csv` is the committed, durable record.
