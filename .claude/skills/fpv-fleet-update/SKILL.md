---
name: fpv-fleet-update
description: >-
  Regenerate the FPV quad inventory (fpv_quads.csv, fpv_quads_latest.csv, FLEET_SUMMARY.md)
  from the Betaflight CLI dump files in this folder. Use this whenever a new BTFL CLI backup
  or dump (a BTFL_cli_*.txt file) is added, replaced, or removed, or whenever the user asks to
  refresh, rebuild, or update the fleet CSV / fleet summary / quad inventory — even if they
  don't name the files explicitly. Also use when the user mentions re-flashing a quad, taking a
  new backup, adding a build, or "I dumped my <quad>". After adding any dump, the CSVs and
  summary are stale until this runs.
---

# FPV Fleet Update

This folder holds Betaflight CLI dumps (`BTFL_cli_*.txt`) exported from FPV quads. Three tracked
files are derived from them and must stay in sync whenever the set of dumps changes:

- `fpv_quads.csv` — full history, one row per dump, newest dump per quad flagged `latest`
- `fpv_quads_latest.csv` — one row per quad, newest dump only
- `FLEET_SUMMARY.md` — human-readable overview: fleet table, rollups, and a "needs attention" pass

## What to do

Run the bundled script from the folder that contains the dumps. It is the single source of truth —
it only reads `*.txt` dumps and rewrites the three files above, so it is safe to re-run any time:

```bash
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

The script prints how many dumps it scanned and how many distinct quads it found. That's the whole
update — do not hand-edit the CSVs or the summary, because the next run overwrites them. If something
in the output looks wrong, fix the script rather than the generated files (see "How it works" below).

After it runs, tell the user what actually changed relative to before: which quad the new dump belongs
to, whether it created a new quad or updated an existing one, and anything newly flagged under "needs
attention" (aging firmware, a truncated dump, a quad now over a year stale). Keep it to what's new —
they don't need the whole table re-printed unless they ask.

## How it works (so you can fix it, not the output)

Each quad is identified by the craft name baked into the dump (`set craft_name` or `# name:`), falling
back to the filename label, then the board. Names are normalized (case, spaces, underscores stripped)
so `M85 HDZero` and `M85_HDZERO` count as one quad. Dumps that share an ExpressLRS UID
(`set expresslrs_uid`) are grouped into bind groups (ELRS-A, ELRS-B, …); quads in a group bind to the
same radio together.

The script reads values straight from `diff all` output, so anything left at a firmware default is
blank by design — that is not a bug. Truncated/aborted dumps (essentially empty files) are kept but
flagged so a real backup can replace them.

If the extraction is wrong or you want to capture a new field, edit
`scripts/update_fleet.py` — the field extraction lives in `parse_dumps()`, the CSV columns in `COLS`,
and the summary layout in `build_summary()`. Re-run the script and confirm the diffs look right.

## When NOT to use this

This is for maintaining the derived inventory files. It is not for editing a quad's actual Betaflight
configuration, flashing firmware, or analyzing tuning/PID values in depth — those are separate tasks.
