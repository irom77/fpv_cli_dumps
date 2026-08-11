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

## Upgrade openracer to KAACK firmware

openracer is still on stock **Betaflight 4.5.1** from a Jul 2024 build — the oldest firmware of any
5-inch racer in the fleet, and the only one not on KAACK:

| Quad | Firmware |
|---|---|
| openracer | 4.5.1 (stock, Jul 2024) |
| LS-Ultra | 4.5.2.KAACK_V15 |
| LS-Ultra HD | 4.5.3.KAACK_V18 |
| openracer2 | 2025.12.3-alpha.KAACK_V19 |

- [ ] Pick a KAACK target for HOBBYWING_XROTORF7CONV (F7X2) — match LS-Ultra's V15/V18 rather than
      openracer2's 2025.12 alpha unless the alpha has proven itself.
- [ ] Back up first: take a fresh `diff all` before flashing, so the pre-upgrade config is in
      `backups/` and the rename history stays intact.

Do these in the same bench session, since they need the quad on USB anyway:

- [ ] **Rates — done 2026-08-11, but redo after flashing.** openracer now matches `house-race`
      exactly (190/160/160 centre, 633/533/533 max) and the rate check is quiet. A flash resets
      rateprofiles, so this has to be pasted again on the other side:
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
- [ ] **`motor_output_limit = 80`** — decide whether to keep the 20% output cap. It won't survive
      the flash either way, so it has to be a deliberate choice to re-apply it.

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

      To actually decide, fly a real pack and check `motor_sat_pct` in `flights.csv`: sustained
      saturation means the cap is costing you thrust; near-zero means it's free headroom you're
      not using. Until then, re-applying `set motor_output_limit = 80` after the flash preserves
      the status quo and is the safer default.
- [ ] Re-dump afterwards and re-run `update_fleet.py`; the rate check should go quiet.

Note: rate values do **not** transfer across the 4.2→4.3 default change or between rate types, so
copy the raw CLI lines above rather than any remembered numbers. See `rates.csv` for what each quad
actually flies at in deg/s. Entering house-race as equivalent ACTUAL values was tried on 2026-08-11
(rc_rate 19/16/16, srate 63/53/53): it matched centre and max exactly but ran ~40% hotter mid-stick,
because ACTUAL and BETAFLIGHT draw different curves between the same endpoints.

## Auto-link ordered parts to builds (fpv-orders-update)

The `fpv-orders-update` skill currently leaves the `build` column blank for the pilot to fill.
Future: propose a best-guess `build` from order timing vs. quad dump dates (e.g. motors bought
just before a Kronos dump → `Kronos?`), left as a `?`-flagged suggestion to confirm.
