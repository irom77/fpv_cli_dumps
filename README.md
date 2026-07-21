# fpv_cli_dumps

Betaflight CLI backups for my FPV quads, plus a derived fleet inventory.

## Layout

```
backups/                 Betaflight CLI dumps (BTFL_cli_*.txt), one or more per quad
fpv_quads.csv            Full history — one row per dump, newest per quad flagged 'latest'
fpv_quads_latest.csv     One row per quad, newest dump only
FLEET_SUMMARY.md         Human-readable overview: fleet table, rollups, "needs attention"
.claude/skills/fpv-fleet-update/   Skill that regenerates the three files above
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
