# Green Hornet V3 Betaflight 2026.6 upgrade

On 2026-09-05, `Green Hornet V3` was upgraded from Betaflight 4.2.4 to Betaflight
2026.6.1. This was a major-version migration on the same iFlight SucceX-E F7 flight controller.

## Result

| Item | Before | After |
|---|---|---|
| Flight-controller target | `IFLIGHT_SUCCEX_E_F7` | unchanged |
| MCU reported by firmware | `STM32F7X2` | `STM32F722` |
| Firmware | 4.2.4 (`fbcaf8c50`) | 2026.6.1 (`6dbc4218f`) |
| MSP API | 1.43 | 1.48 |
| Motor configuration | DSHOT300, bidirectional DShot, 12 poles | preserved |
| Receiver port | Serial RX on UART5 | preserved |
| VTX | Raceband 3, 5732 MHz, power level 2 | Raceband 8, 5917 MHz, power level 2 |
| Craft/pilot identity | Green Hornet V3 / unset | Green Hornet V3 / papfpv |
| Active PID/rate profile | profile 0 / rateprofile 0 | unchanged |

Pre-upgrade backup:
[`BTFL_cli_backup_GREEN_HORNET V3_20260904_165423_IFLIGHT_SUCCEX_E_F7.txt`](../../backups/BTFL_cli_backup_GREEN_HORNET%20V3_20260904_165423_IFLIGHT_SUCCEX_E_F7.txt)

Final post-upgrade backup:
[`BTFL_cli_backup_GREEN_HORNET V3_20260905_090706_IFLIGHT_SUCCEX_E_F7.txt`](../../backups/BTFL_cli_backup_GREEN_HORNET%20V3_20260905_090706_IFLIGHT_SUCCEX_E_F7.txt)

The final backup is the source used by the fleet inventory. The firmware binary was not captured in
this repository, so this record documents the installed build identity but cannot reproduce the
exact flashing artifact independently.

## Migration notes

The first restore attempt produced many rejected or unknown commands. The file named
`UNKNOWN_cli_backup_20260905_071156.txt` was the old 4.2.4 `diff all defaults` backup, not a CLI
error transcript. It contained `NO CUSTOM DEFAULTS FOUND` and `diff: NO CONFIG FOUND`, consistent
with the legacy target having no custom-default configuration available to that backup operation.

The large version jump changed the configuration schema. Important translations visible in the
final dump include:

- numeric serial identifiers became named ports (`serial 0` to `UART1`, `serial 4` to `UART5`);
- `name` became `craft_name`;
- old `d_min_roll` and `d_min_pitch` settings became `d_max_roll` and `d_max_pitch` in the new
  dynamic-damping model;
- some PID settings moved scope, including `thrust_linear`, `feedforward_transition` and
  `tpa_breakpoint`;
- legacy resource, timer, DMA, bus and device-selection lines are absent because the current target
  configuration supplies hardware defaults or the old variables no longer exist;
- obsolete filter and tuning variables rejected during migration were not forced into the new
  firmware.

The final dump confirms that modes, the analog VTX table, OSD positions, DSHOT settings, motor
orientation, primary PID values and both configured rate profiles were saved. It cannot by itself
prove physical receiver response, gyro orientation, motor direction, failsafe or video operation.

## Final configured modes

| Function | AUX range |
|---|---|
| ARM | AUX1, 900–1300 |
| FLIP OVER AFTER CRASH | AUX2, 1300–2100 |
| BEEPER ON | AUX3, 1700–2100 |
| BLACKBOX | AUX4, 1300–1700 |
| BLACKBOX ERASE | AUX4, 1700–2100 |

## Outstanding safety check

Rateprofile 0 has no explicit `rates_type`, so Betaflight 2026.6.1 uses its ACTUAL default. Its
saved `yaw_rc_rate = 172`, inherited from the old configuration, is therefore decoded by the fleet
tool as 1720 degrees/second center sensitivity. This is flagged in `FLEET_SUMMARY.md` as a likely
legacy BETAFLIGHT-rates value interpreted as ACTUAL. Verify and correct the active yaw rate in
Betaflight before flight.

With propellers removed, also verify receiver channels and failsafe, gyro orientation, motor order
and direction, bidirectional-DShot telemetry, OSD and VTX control. Record a conservative test flight
only after those bench checks pass.

## Rollback

To return to the prior behavior, flash Betaflight 4.2.4 for `IFLIGHT_SUCCEX_E_F7` and restore the
linked 2026-09-04 pre-upgrade backup. Do not paste that legacy backup wholesale into 2026.6.1; use
the final post-upgrade dump for recovery on the current firmware family.
