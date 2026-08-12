# TODO

## 1. Publish the `fpv-fleet-update` skill publicly

Make the skill installable by others via a Claude Code plugin marketplace. Currently it's
project-scoped (`.claude/skills/fpv-fleet-update/`), so it only loads inside this repo.

Steps:
- [ ] Decide on a marketplace repo (e.g. `github.com/irom77/claude-plugins`) — separate repo, or reuse this one.
- [ ] Scaffold the plugin layout:
  ```
  plugins/fpv-fleet-update/
  ├── .claude-plugin/plugin.json      # name, description, version, author
  └── skills/fpv-fleet-update/
      ├── SKILL.md
      └── scripts/update_fleet.py
  ```
- [ ] Add the marketplace manifest `.claude-plugin/marketplace.json` listing the plugin.
- [ ] Fix the script path in SKILL.md: `.claude/skills/...` → `${CLAUDE_PLUGIN_ROOT}/scripts/update_fleet.py`
      (the repo-relative path breaks once installed as a plugin).
- [ ] Validate: `claude plugin validate .`
- [ ] Push the marketplace repo to GitHub.
- [ ] Test install from a clean checkout: `/plugin marketplace add irom77/claude-plugins` then
      `/plugin install fpv-fleet-update@<marketplace-name>`.
- [ ] Note in README how to install it.

Caveat to resolve: the skill writes its output (CSVs, FLEET_SUMMARY.md) into the current working
directory and is built around Betaflight dumps, so it's mainly useful to people who keep BTFL
backups. Consider documenting that expectation, or generalizing the script (e.g. an input/output
flag) before publishing.

## 2. Make use of blackbox logs

Betaflight blackbox flight logs (`.bbl` / `.bfl`) capture per-flight telemetry. First pass is
implemented: `update_flights.py` decodes logs (via `orangebox`) into `flights.csv`, and
`update_fleet.py` folds a per-quad Flights section into FLEET_SUMMARY.md.

Done:
- [x] Logs live in `blackbox/` (gitignored); only derived `flights.csv` is committed.
- [x] Per-flight summary: duration, battery start/min/sag, cell count, avg/peak current, mAh,
      avg throttle & motor, motor saturation %. Units calibrated from log headers.
- [x] Link each flight to its quad (craft name from log header) and per-quad rollup in the summary.
- [x] Wired into the `fpv-fleet-update` skill.

- [x] Motor desync / thrust-loss detection (motor commanded high while its eRPM collapses vs peers),
      surfaced as `MOTOR_DESYNC(m#)` in flights.csv flags + ⚠️ in the summary. Validated against the
      Kronos crash log (motors 0 & 3) vs the clean post-repair log.
- [x] `hardware.csv` for per-quad build details (ESC, motors, props) not present in dumps.

Next / ideas to extend:
- [ ] More metrics: max gyro / vibration (noise), PID error / tracking, RC dropout & failsafe events,
      throttle histogram, per-motor imbalance (worn motor / prop detection).
- [ ] More auto-flags: excessive sag → aging pack (partial: LOW_CELL); motor saturation →
      underpowered/overweight. Roll flagged flights up into the summary's "needs attention".
- [ ] Distinguish real flights from bench tests (both current logs are short bench hops).
- [ ] Handle logs whose filename lacks a craft label; match to a quad another way.

## Refresh corrected mode assignments

openracer and openracer2 both had `BLACKBOX ERASE` and `VTX PIT MODE` assigned to the same AUX4
middle range. Selecting PIT mode therefore also started a flash erase, after which the quad would
not arm until it was power-cycled. Removing the shared assignment fixed the behavior on both.

- [x] Remove the overlapping `BLACKBOX ERASE` / `VTX PIT MODE` assignment from both quads.
- [ ] Take fresh CLI backups of openracer and openracer2, then run `update_fleet.py` so `modes.csv`
      reflects the corrected configuration. The current openracer2 backup predates the overlap and
      the fix, so it cannot document either state.

## Make the 5-inch racers Freedom Spec legal

`specs.csv` now encodes the MultiGP Freedom Spec rules and `FLEET_SUMMARY.md` checks every 5-inch
race quad against them. **All four fail on the same thing: the RPM limiter is off.** KAACK ships
`rpm_limit_value` already at 18000, so on the three KAACK quads this is one line each:

```
set rpm_limit = ON
save
```

- [ ] LS-Ultra, LS-Ultra HD, openracer2 — enable `rpm_limit`, re-dump, re-run `update_fleet.py`.
- [ ] openracer — needs KAACK first (see below), then the same line.
- [ ] Weigh each race-ready (pack and props in) and record that in `hardware.csv` — 533 g minimum.
      Recorded weights are dry: openracer 305 g, openracer2 280 g, LS-Ultra 270 g. A 6S pack adds
      200–260 g, so all three land near the line rather than clearly over it, and LS-Ultra on the
      lightest pack could come in under. The rules publish the 533 g bare, without the `AUW`
      qualifier MultiGP puts on Open and Pro Spec — if it ever matters at tech check, ask the race
      director which reading they use.
- [ ] Record ESC firmware (BLHeli32 / AM32) in `hardware.csv`'s `esc_stack` for openracer
      (Hobbywing XRotor 45A) and openracer2 (Foxeer Reaper) — both currently name only the brand,
      so the check can't confirm them.
- [ ] Fill in LS-Ultra HD's build: `motors` says only "HeadsUp RC (MR-30 connectors)", and `cells`,
      `esc_stack` and `weight` are blank, so four of its rules are unconfirmed.
- [ ] Count the LEDs on each (3+ non-status required) and check the event's prop call — neither is
      derivable from a dump.

## Extend spec coverage past the 5-inch racers

`specs.csv` holds one class today, so the compliance pass only sees four quads. The five whoop
racers — Mob6 AIO5 1st, Mob6 AIO5 2nd, Mob6 AIO5 RACE, Mob6 HDZERO RACE, Race5 — are all
`discipline=race` and checked against nothing.

- [ ] Add the MultiGP **Tiny Whoop** class. The class-specifications page gives max 65 mm ducted
      frame, 31 mm props max, 1S at 4.35 V max charge, motors brushed or brushless (0702/0802
      recommended), no weight limit — but verify against the current rulebook before encoding it,
      the way Freedom Spec's bare "533g" turned out to need reading rather than quoting.
- [ ] Frame size and duct are the problem: no dump carries them and `hardware.csv` has no frame
      column, so a 65 mm rule can only be `manual` or needs a new column. Decide which before
      writing the rows — a spec made mostly of `·` isn't worth the file.
- [ ] Cell count is checkable today (`cells` in `hardware.csv`), props partly (`props` records
      e.g. "Gemfan 1210 31mm bi-blade", so a `31mm|1210|1219|1208` regex works with an `evidence`
      guard on `mm|\d{4}`).
- [ ] Once a second spec exists, confirm the per-spec CSV split behaves: two files, no shared
      columns, and `spec_scope()` keeping whoops out of the Freedom Spec table.

Ideas, not yet needed:

- Per-event overrides. Freedom Spec's RPM cap is 18000 by default but an event may call
  16000–22000, and the prop is named per event — both are currently one fixed rule plus a
  `manual` row. An `event` column or a per-event override file would only earn its place if you
  actually race under a non-standard call.
- Deleting a spec from `specs.csv` orphans its `compliance_*.csv` (the generator only writes).
  Cheap to fix with a cleanup pass if specs ever churn; not worth it for two.

## Upgrade openracer to KAACK firmware — completed 2026-08-12

openracer was upgraded from stock **Betaflight 4.5.1** to **4.5.3.KAACK_V19**. The complete build,
flash, restore and verification record is in
[`upgrades/OPENRACER_KAACK_V19_UPGRADE/`](upgrades/OPENRACER_KAACK_V19_UPGRADE/README.md).

| Quad | Firmware |
|---|---|
| openracer | 4.5.3.KAACK_V19 |
| LS-Ultra | 4.5.2.KAACK_V15 |
| LS-Ultra HD | 4.5.3.KAACK_V18 |
| openracer2 | 2025.12.3-alpha.KAACK_V19 |

- [x] Built KAACK V19 from the 4.5-based branch for the exact `HOBBYWING_XROTORF7CONV` target,
      avoiding the 2025.12 alpha line.
- [x] Saved the 12:02:42 pre-flash `diff all` in `backups/`.

Do these in the same bench session, since they need the quad on USB anyway:

- [x] **Rates restored after flashing.** openracer matches `house-race` exactly (190/160/160 centre,
      633/533/533 max), and the generated rate check is quiet:
      ```
      rateprofile 0
      set rates_type = BETAFLIGHT
      set roll_rc_rate = 95
      set pitch_rc_rate = 80
      set yaw_rc_rate = 80
      set roll_srate = 70
      set pitch_srate = 70
      set yaw_srate = 70
      save
      ```
- [x] **`rpm_limit = ON`** with `rpm_limit_value = 18000`, satisfying the firmware and RPM-limiter
      parts of the Freedom Spec check.
- [x] **Removed the 80% motor-output cap deliberately:** `motor_output_limit = 100`.

      Dump history says it is **not** crash-related, contrary to the first guess:

      | Dump | `motor_output_limit` |
      |---|---|
      | 2024-12-30 (Kronos) | not set — full 100% |
      | 2025-08-10 (Kronos) | **80** |
      | 2026-08-11 ×3 (openracer) | 80 |

      It was introduced somewhere between 2024-12 and 2025-08, roughly **eleven months before** the
      2026-07-15 desync crash — so it predates the fault it was assumed to be a reaction to. That
      makes "leftover from troubleshooting" the weaker reading and "deliberate power cap" the
      stronger one: VCI Spark 2207 2050Kv on 6S is a lot of thrust for a 305g airframe.

      The blackbox logs can't settle it. Both are short bench hops (7.7s and 14.3s at 10% and 18%
      average throttle), and the only saturation reading — 7.2% on 2026-07-15 — is confounded by
      the desync itself, since a desynced motor gets commanded to full and reads as saturated. The
      clean 2026-07-20 log shows 0% saturation, but at 18% throttle that proves nothing about
      whether the cap bites under race load.

      The cap was removed by decision on 2026-08-12. Use a real flight log to watch
      `motor_sat_pct` and re-check for desync under load; the existing short bench logs cannot
      predict full-power behavior.
- [x] Re-dumped after flashing, finalized the OSD, and re-ran `update_fleet.py`. The final source is
      `BTFL_cli_backup_OPENRACER_20260812_122513_HOBBYWING_XROTORF7CONV.txt`.

Note: rate values do **not** transfer across the 4.2→4.3 default change or between rate types, so
copy the raw CLI lines above rather than any remembered numbers. See `rates.csv` for what each quad
actually flies at in deg/s. Entering house-race as equivalent ACTUAL values was tried on 2026-08-11
(rc_rate 19/16/16, srate 63/53/53): it matched centre and max exactly but ran ~40% hotter mid-stick,
because ACTUAL and BETAFLIGHT draw different curves between the same endpoints.

## Auto-link ordered parts to builds (fpv-orders-update)

The `fpv-orders-update` skill currently leaves the `build` column blank for the pilot to fill.
Future: propose a best-guess `build` from order timing vs. quad dump dates (e.g. motors bought
just before a Kronos dump → `Kronos?`), left as a `?`-flagged suggestion to confirm.

## Back up radios and EdgeTX configuration here too

- [ ] Try backing up each radio's EdgeTX configuration into this repo, including radio settings,
      models, Lua scripts, widgets, themes, sounds, and any other files needed for a practical
      restore.
- [ ] Record each radio model and its EdgeTX firmware/version, and document how to create and
      restore the backups.
- [ ] Decide which generated, device-specific, or sensitive files should be excluded before
      committing the backups.
