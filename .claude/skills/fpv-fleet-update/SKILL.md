---
name: fpv-fleet-update
description: >-
  Regenerate the FPV quad inventory (fpv_quads.csv, fpv_quads_latest.csv, rates.csv, modes.csv,
  FLEET_SUMMARY.md)
  from the Betaflight CLI dump files in this folder. Use this whenever a new BTFL CLI backup
  or dump (a BTFL_cli_*.txt file) is added, replaced, or removed, or whenever the user asks to
  refresh, rebuild, or update the fleet CSV / fleet summary / quad inventory — even if they
  don't name the files explicitly. Also use when the user mentions re-flashing a quad, taking a
  new backup, adding a build, or "I dumped my quad". After adding any dump, the CSVs and
  summary are stale until this runs.
---

# FPV Fleet Update

This folder holds Betaflight CLI dumps (`BTFL_cli_*.txt`) exported from FPV quads. The generated
files below must stay in sync whenever the set of dumps changes:

- `fpv_quads.csv` — history, one row per dump, newest dump per quad flagged `latest`. Dumps whose
  extracted inventory values are identical (differing only in date/file) are collapsed to the most
  recent, so unchanged re-dumps don't clutter the history.
- `fpv_quads_latest.csv` — one row per quad, newest dump only
- `rates.csv` — active rateprofile decoded into real deg/s (centre sensitivity, max rate, and the
  curve at 25/50/75% stick) instead of the raw stored integers. Covers the quads you might actually
  fly: `status` active **and** a `discipline` set (`in_rates_view()`) — quads on stock rates are
  included, retired/broken/undisciplined ones are not. Grouped by `discipline` then `class` (race
  first) rather than alphabetically, so quads flown the same way can be read against each other —
  and so a 1S whoop and a 6S five-inch never share a heading just because both race. The filter is
  on the VIEW only; "needs attention" checks still run over the whole fleet. See "Rates" below.
- `modes.csv` — configured Betaflight modes decoded from `aux` lines, one row per activation range
  with mode name/ID, AUX channel, exact range, condition logic/link, firmware, and source dump.
  Covers only quads with `status` active and both `discipline` and `class` set, ordered like the
  rates view. Unknown mode IDs remain visible for custom/newer firmware.
- `FLEET_SUMMARY.md` — human-readable overview: fleet table, rollups, "needs attention", and (if
  `flights.csv` exists) a per-quad Flights section
- `flights.csv` — one row per decoded blackbox flight (duration, battery sag, current, mAh, motor
  saturation, a `flags` column for detected issues like `MOTOR_DESYNC`/`LOW_CELL`, and the generated
  copy of any matching descriptive comment). Optional — only present once blackbox logs have been
  processed.
- `flight_notes.csv` — hand-maintained descriptive post-analysis comments, keyed by exact raw
  `file` name plus internal `log_index`. `update_flights.py` copies matching comments into
  `flights.csv`, and the fleet summary displays them. Edit this file, never the generated copies.
- `hardware.csv` — hand-maintained per-quad build details that aren't in the dumps
  (`cells, weight, esc_stack, motors, props, camera, vtx, notes`), plus three curated columns the
  dumps can't provide: `class` (whoop / cinewhoop / micro / 5-inch, overrides the auto-guess),
  `status` (lifecycle — active / building / rebuilding / broken / retired / lost; blank = active), and
  `discipline` (what it's flown for — race / freestyle / cinematic / long-range; blank = unset), and
  `aliases` (former craft names, `;`-separated — see "Renaming a quad" below), and `rate_preset`
  (which named rateprofile from `rate_presets.csv` this quad is *meant* to fly — see "Rates"). Largely seeded
  from the pilot's own fleet spreadsheet, so some rows may be stale — the `notes` column flags known
  conflicts. Optional; joined into the summary by quad name. Edit it directly.
- `specs.csv` — hand-maintained race-class rulebook, one row per requirement, scoped to the
  `class`/`discipline` it applies to. Drives the summary's "Spec compliance" section. See "Specs"
  below.
- `compliance_<spec>.csv` — generated, one file per spec in `specs.csv`: a row per quad in scope
  with a state per requirement plus `verdict` / `missing` / `to_confirm`. Per spec, not combined,
  because the columns are that spec's requirements. Deleting a spec from `specs.csv` leaves its
  file orphaned — the script only writes, so remove it by hand.

## What to do

Run the bundled script from the folder that contains the dumps. It is the single source of truth —
it only reads `*.txt` dumps and hand-maintained CSVs and rewrites the generated files above, so it
is safe to re-run any time:

```bash
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

The script prints how many dumps it scanned and how many distinct quads it found. That's the whole
update — do not hand-edit the CSVs or the summary, because the next run overwrites them. If something
in the output looks wrong, fix the script rather than the generated files (see "How it works" below).

### Blackbox flight logs (optional)

If the user adds Betaflight blackbox logs (`.BBL`/`.BFL`) or asks about flights, decode them with
the companion script, then re-run `update_fleet.py` so the summary picks up the Flights section:

```bash
# one-time dependency setup (the orangebox blackbox parser, isolated in a venv):
python3 -m venv .venv && .venv/bin/pip install orangebox

# put logs in ./blackbox (default) or pass a folder (e.g. the OneDrive backup dir), then:
python3 .claude/skills/fpv-fleet-update/scripts/update_flights.py [logs_folder]
python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
```

`update_flights.py` auto-re-execs under `./.venv` if `orangebox` isn't already importable. It writes
`flights.csv`, replacing rows for raw logs currently present while retaining summarized flights after
their raw log is moved or deleted — important because the large `.BBL` files are gitignored and never
committed. Internal log sections count as flights only when they last at least 1.0 second and contain
a throttle command above the 1000 idle value; this omits short and no-throttle captures created while
connecting, configuring, or rebooting the quad. The script prints the filename, internal log index,
and rejection reason for each skipped section, plus a skipped count in its final status line. Units
are calibrated from each log's headers
(vbat/current in 0.01 units, cell count inferred from start voltage). A duplicated header marker can
look like a phantom extra flight; `valid_logs()` skips those by ignoring near-empty logs.

After analysis, record human context and conclusions in `flight_notes.csv` using columns
`file,log_index,comment`. The filename and internal index form the stable join key. Re-running the
flight decoder refreshes the `comment` column in `flights.csv` from this file—including clearing a
generated comment when its source note is removed—and `update_fleet.py` then refreshes the Comment
column in `FLEET_SUMMARY.md`. Unmatched note rows remain in `flight_notes.csv` for archived raw logs.

**Motor desync detection:** the summary flags a frame as a desync/thrust-loss event when a motor is
commanded near max (≥90% of the output range) yet its bidirectional-DShot eRPM is well below the
fastest motor's (<55%) — told to spin hard, spinning much slower than its peers. Above a small frame
count this raises `MOTOR_DESYNC(m#,…)` in `flags`, naming the offending motor(s). This was validated
against a real crash log (motors 0 & 3 desynced) vs a clean post-repair log (no flag). Report the
data's answer for which motor, not an external narrative — motor indices are 0-based blackbox order.

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

**Renaming a quad.** Because identity is the craft name, renaming a quad in Betaflight would split one
airframe into two quads with two half-histories. To fold them, rename the `quad` cell in `hardware.csv`
to the new name and list the old one in that row's `aliases` column (`;`-separated for repeat renames).
`load_aliases()` remaps old dumps *and* old blackbox flights onto the current name before any name-keyed
join; the per-dump `craft_name` column still shows what each dump was actually called at the time. Note
`orders.csv` links parts by build name — grep it for the old name when renaming.

The script reads values straight from `diff all` output, so anything left at a firmware default is
blank by design — that is not a bug. Truncated/aborted dumps (essentially empty files) are kept but
flagged so a real backup can replace them.

Size **class** (whoop / cinewhoop / micro / 5-inch) can't be read from a dump — Betaflight records no
frame/prop/motor/cell field. `guess_class()` infers it from craft name + board family (F411 AIO boards
and 65–85 mm product names → whoop; XRotor/TMotor/Flywoo F7 stacks → 5-inch; Cinelog → cinewhoop; Crux/
Crocodile → micro). A digit in a name is a *board* type, not a size — `AIO5` means a 5-in-1 board, so an
AIO whoop stays a whoop. The guess is a fallback: an explicit `class` in `hardware.csv` always wins, and
anything the heuristic can't place is listed under "needs attention" to curate there.

**Status** (lifecycle) and **discipline** (what a quad is flown for) are two orthogonal hand-curated
columns — a quad keeps its `discipline` after it's `retired`, so they can't share one column. Neither
is in a dump, so both come only from `hardware.csv` (no guesser). `status` blank defaults to `active`
via `status_of()`; any not-flyable status (`broken`/`retired`/`lost`) is dropped from the aging-firmware
and stale-backup nags in "needs attention" (no point re-flashing a grounded quad) but still appears in
the fleet table with its status flagged. `broken` also gets its own actionable "needs repair" line, and
`building`/`rebuilding` are surfaced as intentionally-incomplete rather than as truncated dumps.

**Rates.** Raw columns (`rateprofile`, `rates_type`, `rc_rate_rpy`, `super_rate_rpy`, `expo_rpy`) come
from the **active** rateprofile only (the last bare `rateprofile N` line) via `extract_active_rates()`.
Those triples are the RAW stored integers, and a triple like `//12` means only yaw was set.

`scripts/rates.py` turns them into real deg/s for `rates.csv` and the summary's Rates table. It is
pure math with no I/O — run `python3 scripts/rates.py` to execute its self-test. Two things it exists
to handle:

- **Stock rates are not one thing.** `diff all` omits defaults, so a quad that never had rates set
  dumps no rate lines at all — and the default changed at 4.3 (before: BETAFLIGHT rc 100 / srate 70,
  centre 200 °/s; after: ACTUAL rc 7 / rates 67, centre 70 °/s). `defaults_for()` fills the values
  that quad's own firmware shipped, so `source=default` rows show what it really flies at rather than
  a blank that reads the same as "not tracked".
- **The type decides the meaning.** `rate_at()` mirrors `applyActualRates()` / `applyBetaflightRates()`
  from `src/main/fc/rc.c`. Only those two types are implemented; QUICK/KISS/RACEFLIGHT decode to blank
  with a note rather than a wrong number. If you add one, add a self-test case with it.

`rate_presets.csv` (hand-maintained, `preset,rates_type,rc_rate_rpy,super_rate_rpy,expo_rpy,notes`)
names rateprofiles the pilot intends several quads to share; `rate_preset` in `hardware.csv` assigns
one to a quad. Comparison is on default-filled values, not raw dump text, so setting a value
explicitly to its default still matches. A mismatch is reported in "needs attention" — this is the
one rates check that encodes intent, since nothing in a dump says what a quad was *supposed* to be.

`inert_max_rate()` flags a related trap: on an ACTUAL profile whose centre sensitivity meets or
exceeds its max rate, the max-rate setting does nothing and the stick goes linear to a very high
ceiling. That usually means BETAFLIGHT-era rc_rate values (100 = 1.0×) were left on a profile the
firmware now reads as ACTUAL (100 = 1000 °/s centre) across an upgrade.

**Specs.** `specs.csv` is a rulebook, not a per-quad file: one row per requirement of one race
class (`spec,applies_class,applies_discipline,requirement,rule,check,field,value,evidence,notes,source`).
`applies_class`/`applies_discipline` decide which quads are in scope — blank means "any", and every
row of a spec carries the same scope. Adding a class is adding rows; no code changes.

Each row names a declarative `check` the generator runs:

- `hw_match` — `value` (a regex) must match `field` in `hardware.csv`
- `dump_match` — same, against a parsed dump column (`bf_version`, `rpm_limit`, …)
- `hw_weight_min` — `field` must parse to at least `value` grams
- `manual` — not derivable from either source; always reported for a bench check

`build_spec_rows()` evaluates every rule against every quad in scope once; `build_spec_section()`
renders it as markdown and `write_compliance_csvs()` writes the same data as `compliance_<slug>.csv`,
so the table and the CSV can't disagree. `spec_verdict()` is shared by both.

Results are four-valued on purpose, and the distinction is the whole point of the section: `ok`,
`fail`, `unknown` (nothing recorded to judge by — a gap in `hardware.csv`, not in the airframe) and
`manual`. Only `fail` reaches "needs attention". Two rules keep `unknown` honest:

- The optional `evidence` regex says "this field states the kind of fact being tested" (a stator
  size, a cell count, an ESC firmware). If `field` has a value but no `evidence` match, the build
  sheet is silent on the rule, so the result is `unknown` rather than `fail` — otherwise
  `esc_stack = "Hobbywing XRotor F722 (45A 4-in-1 ESC)"` would fail an ESC-firmware rule for saying
  nothing about firmware.
- `hw_weight_min` never fails. `hardware.csv` weights are dry (no pack, often no props) while a
  class minimum is a race-ready figure, and a 6S race pack is 200–260 g — so a figure under the
  minimum returns `unknown` with what it would take to settle it. (Freedom Spec publishes its
  533 g bare, without the `AUW` qualifier MultiGP puts on Open and Pro Spec; race-ready is the only
  reading that works, since a 5-inch 6S airframe is 270–310 g dry.)

`dump_match` reads `DUMP_DEFAULTS` for settings `diff all` omits, so a blank `rpm_limit` is judged
as its firmware default `OFF` rather than as missing data — the case that matters, since a quad
with the RPM limiter never switched on dumps no `rpm_limit` line at all.

If the extraction is wrong or you want to capture a new field, edit
`scripts/update_fleet.py` — the field extraction lives in `parse_dumps()`, the CSV columns in `COLS`,
and the summary layout in `build_summary()`. Re-run the script and confirm the diffs look right.

## When NOT to use this

This is for maintaining the derived inventory files. It is not for editing a quad's actual Betaflight
configuration, flashing firmware, or analyzing tuning/PID values in depth — those are separate tasks.
