# Archived TODO tasks

### Trial the Mondo MultiGP Pro Spec 7-inch preset — archived 2026-09-28

This task was archived with the preset trial still incomplete. The compatibility assessment,
rollback plan, staged test procedure, and acceptance criteria remain in
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

### Upgrade openracer to KAACK firmware — completed 2026-08-12

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
- [x] Restored the `house-race` rates and verified the generated rate check.
- [x] Enabled `rpm_limit = ON` with `rpm_limit_value = 18000`.
- [x] Removed the deliberate 80% motor-output cap (`motor_output_limit = 100`).
- [x] Re-dumped after flashing, finalized the OSD, and re-ran `update_fleet.py`. The final source is
      `BTFL_cli_backup_OPENRACER_20260812_122513_HOBBYWING_XROTORF7CONV.txt`.

The remaining real-flight motor-saturation/desync check is documented as follow-up in the upgrade
record; it is not part of the completed firmware upgrade.

Note: rate values do **not** transfer across the 4.2→4.3 default change or between rate types, so
copy the raw CLI lines above rather than any remembered numbers. See `rates.csv` for what each quad
actually flies at in deg/s.

### Cine-fish — analog conversion — completed 2026-09-28

- [x] Install and configure the Rush Tiny Tank and CaddxFPV Baby Ratel 2 analog camera.
- [x] Confirm analog video and Betaflight OSD operation.
- [x] Confirm Cine-fish is flying. SmartAudio remains non-operational, so the VTX channel must
      be selected manually; automatic channel control is not required for current operation.
- [x] Archive the unresolved SmartAudio diagnosis in
      [the troubleshooting handoff](docs/troubleshooting/cine-fish-rush-tiny-tank-smartaudio.md).

### Crux-fish (formerly HDZERO CRUX35) repair — completed 2026-09-28

- [x] Buy 1 [HappyModel EX1404 3500KV motor](https://pyrodrone.com/products/happymodel-ex1404-1404-motor-3500kv) for Crux-fish Motor 3, reported not moving on 2026-09-10 (model per hardware.csv; confirm against the installed motor before ordering).
- [x] Buy 1 [HDZero Nano V3 HD FPV camera](https://pyrodrone.com/products/hdzero-nano-v3-hd-fpv-camera) for Crux-fish (formerly HDZERO CRUX35).
- [x] Buy 1 60 mm MIPI cable for Crux-fish’s HDZero Nano V3 camera.
