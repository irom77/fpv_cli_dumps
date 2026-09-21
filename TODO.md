# TODO

## Crux-fish (formerly HDZERO CRUX35) repair

- [ ] Buy 1 [HappyModel EX1404 3500KV motor](https://pyrodrone.com/products/happymodel-ex1404-1404-motor-3500kv) for Crux-fish Motor 3, reported not moving on 2026-09-10 (model per hardware.csv; confirm against the installed motor before ordering).
- [ ] Buy 1 [HDZero Nano V3 HD FPV camera](https://pyrodrone.com/products/hdzero-nano-v3-hd-fpv-camera) for Crux-fish (formerly HDZERO CRUX35).
- [ ] Buy 1 60 mm MIPI cable for Crux-fish’s HDZero Nano V3 camera.

## Cine-fish — analog conversion (Rush Tiny Tank installed)

Rush Tiny Tank installed 2026-09-18, confirmed by pilot. This supersedes the deferred plan to use
Mass's Rush Tank Ultimate Mini; that unit's unresolved fault remains documented in the
[Mass VTX log](docs/troubleshooting/mass-vtx-troubleshooting.md).
Latest configuration: [2026-09-18 backup](backups/BTFL_cli_CINE-FISH_20260918_143515_GEPRCF411_AIO.txt),
GEPRCF411_AIO, BF 4.5.2 in the archived dump; live FC upgraded to 4.5.5 and restored on 2026-09-18.
A post-upgrade dump is still needed. The saved dump is preserved as exported.
Detailed handoff: [Cine-fish SmartAudio troubleshooting](docs/troubleshooting/cine-fish-rush-tiny-tank-smartaudio.md).

- [x] Install Rush Tiny Tank.
- [x] Configure UART1 for SmartAudio (`serial 0 2048 115200 57600 0 115200`); UART2 remains CRSF.
- [x] Load the five-band VTX table with power labels 25/100/200/350 mW;
      saved selection is R8 (5917 MHz), power index 1 (25 mW label).
      The VTX table is preserved in the linked full dump.
- [x] Save a fresh dump and refresh the fleet inventory with the installed VTX.
- [x] Install and connect the analog camera through the VTX pads (pilot confirmed 2026-09-18).
- [x] Record camera model: CaddxFPV Baby Ratel 2 (pilot confirmed 2026-09-18).
- [x] Confirm camera video and Betaflight OSD on HDZero Monitor, RF Auto, A1 (5865 MHz).
- [x] Select analog OSD: 14:35:15 dump confirms `osd_displayport_device = MAX7456`,
      `vcd_video_system = AUTO`, and a 30x13 canvas.
- [ ] Review analog OSD element placement; OSD text is confirmed visible.
- [x] Resolve static: actual VTX channel is A1; the saved R8 request was not reaching the VTX.
- [x] Confirm DATA-to-FC-T1 continuity (pilot tested).
- [ ] Resolve SmartAudio Device ready=false and channel control. Changing the Betaflight
      channel updates the OSD/configuration values but the Rush Tiny Tank remains on A1
      (5865 MHz), so the FC-to-VTX SmartAudio command path is still unverified. VTX sticker
      identifies SmartAudio 2.1.
      Attempted BF 4.5.5 with `NONCOMPLIANT_SMARTAUDIO` selected; still false after restore and
      full power cycle. Build metadata for key `3b7d5fd28e6489c3dd138b3d7ee0fe7a` confirms
      `USE_NONCOMPLIANT_SMARTAUDIO` is included; see the detailed handoff. This is a firmware
      build option, not a CLI setting.
      [Betaflight workaround](https://betaflight.com/docs/development/API/Cloud-Build-API#smartaudio-bug).
- [ ] Confirm channel/power control and video operation on the bench; the dump records requested
      settings, not measured transmitter output. `vtx_low_power_disarm` currently remains `OFF`.
- [ ] Confirm the former Caddx Vista's disposition before adding it to spare_parts.csv.

Pilot-reported installed wiring for the CaddxFPV Baby Ratel 2 (2026-09-18; physical pad labels not independently verified):

| Rush Tiny Tank pad | FC connection | Camera connection |
| --- | --- | --- |
| +5V | 5V | VCC |
| GND | GND | GND |
| CAM | Video input (VIDEO / VI in supplied table) | VIDEO |
| VTX | Video output (VOUT / VO in supplied table) | — |
| DATA | T1 / TX1 | — |

The reported signal path is camera → FC video input → FC OSD → VTX video input.
Camera power comes from the FC's 5V rail through the shared VTX pad. This records the installed
wiring; video and Betaflight OSD were confirmed on A1 before the firmware upgrade.
Recheck after restoration and save a fresh dump.

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
- [x] Preserve descriptive post-analysis comments in hand-maintained `flight_notes.csv`; copy them
      into generated `flights.csv` and display them in the fleet summary.
- [x] Omit internal captures without flight activity: require at least 1.0 second of decoded data
      and a throttle command above the 1000 idle value. Rebuilds replace rows for logs still present
      while retaining durable history for raw logs that have been archived or removed.

- [x] Motor desync / thrust-loss detection (motor commanded high while its eRPM collapses vs peers),
      surfaced as `MOTOR_DESYNC(m#)` in flights.csv flags + ⚠️ in the summary. Validated against the
      Kronos crash log (motors 0 & 3) vs the clean post-repair log.
- [x] `hardware.csv` for per-quad build details (ESC, motors, props) not present in dumps.

Next / ideas to extend:
- [ ] More metrics: max gyro / vibration (noise), PID error / tracking, RC dropout & failsafe events,
      throttle histogram, per-motor imbalance (worn motor / prop detection).
- [ ] More auto-flags: excessive sag → aging pack (partial: LOW_CELL); motor saturation →
      underpowered/overweight. Roll flagged flights up into the summary's "needs attention".
- [ ] Distinguish throttle-active bench tests from real flights; the current filter intentionally
      admits both because duration and throttle alone cannot reliably tell them apart.
- [ ] Handle logs whose filename lacks a craft label; match to a quad another way.

## Refresh corrected mode assignments

openracer and openracer2 both had `BLACKBOX ERASE` and `VTX PIT MODE` assigned to the same AUX4
middle range. Selecting PIT mode therefore also started a flash erase, after which the quad would
not arm until it was power-cycled. Removing the shared assignment fixed the behavior on both.

- [x] Remove the overlapping `BLACKBOX ERASE` / `VTX PIT MODE` assignment from both quads.
- [ ] Take fresh CLI backups of openracer and openracer2, then run `update_fleet.py` so `modes.csv`
      reflects the corrected configuration. The current openracer2 backup predates the overlap and
      the fix, so it cannot document either state.

## Trial the Mondo MultiGP Pro Spec 7-inch preset

Evaluate Armando Gallegos (Mondo)'s **Experimental Presets for MultiGP PRO Spec 7\"** tune on
ProSpec. The compatibility assessment, rollback plan, staged test procedure, and acceptance criteria
are recorded in
[`docs/prospec-mondo-experimental-preset.md`](docs/prospec-mondo-experimental-preset.md).

- [x] Set and verify the shared `house-race` rates: BETAFLIGHT RC rate `95/80/80`, super rate
      `70/70/70` (approximately 633/533/533 deg/s).
- [x] Save the known-good pre-preset rollback dump as
      `BTFL_cli_backup_PROSPEC_20260902_111305_HOBBYWING_XROTORF7CONV.txt`.
- [ ] Before applying, confirm the current preset explicitly supports Betaflight 4.5.x and review
      its options, warnings, and linked discussion.
- [ ] Apply the preset with props removed, save a post-preset `diff all`, and verify receiver,
      failsafe, modes, motor order/direction, DShot telemetry, RPM filtering, OSD, LEDs, rates, and
      the 13,000 RPM limiter.
- [ ] Resolve the preset's `acc_hardware = NONE` setting: restore the accelerometer if AUX2 Angle
      mode is still required, or deliberately remove/accept the unavailable mode.
- [ ] Perform the staged hover, motor-temperature, gentle-flight, and race-flight checks. Capture a
      blackbox log for comparison with the baseline.
- [ ] Record the results and keep/revert decision in the proposal document, add the post-test dump
      to `backups/`, then run `update_fleet.py`.

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
