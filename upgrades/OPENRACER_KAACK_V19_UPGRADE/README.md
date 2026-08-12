# OpenRacer KAACK V19 upgrade

On 2026-08-12, `openracer` was upgraded from stock Betaflight 4.5.1 to
Betaflight 4.5.3.KAACK_V19. This directory preserves the exact firmware, restore commands, build
provenance and verification trail so the installation can be reproduced or rolled back without
guessing which target or settings were used.

## Result

| Item | Before | After |
|---|---|---|
| Flight controller | HOBBYWING_XROTORF7CONV (STM32F722) | unchanged |
| Firmware | Betaflight 4.5.1 (`77d01ba3b`) | 4.5.3.KAACK_V19 (`8cd4438`) |
| MSP API | 1.46 | 1.46 |
| RPM limiter | off | on, 18,000 RPM |
| Motor output limit | 80% | 100% (cap removed deliberately) |
| Rates | `house-race` | restored unchanged |
| AUX4 middle | BLACKBOX ERASE + VTX PIT overlap | VTX PIT only |

The final backup is
[`BTFL_cli_backup_OPENRACER_20260812_122513_HOBBYWING_XROTORF7CONV.txt`](../../backups/BTFL_cli_backup_OPENRACER_20260812_122513_HOBBYWING_XROTORF7CONV.txt).
It includes the final HDZero `50×18` OSD layout.

## Preserved files

- [`betaflight_4.5.3.KAACK_V19_STM32F7X2_HOBBYWING_XROTORF7CONV.hex`](betaflight_4.5.3.KAACK_V19_STM32F7X2_HOBBYWING_XROTORF7CONV.hex)
  is the exact firmware flashed.
- [`BTFL_cli_restore_OPENRACER_20260812_KAACK_V19.txt`](BTFL_cli_restore_OPENRACER_20260812_KAACK_V19.txt)
  is the selective post-flash restore, updated with the final OSD positions.
- [`OPENRACER_KAACK_V19_UPGRADE.png`](OPENRACER_KAACK_V19_UPGRADE.png) shows Betaflight
  Configurator immediately before flashing: the local HEX is loaded and Full chip erase is on.
- [`SHA256SUMS`](SHA256SUMS) authenticates the three package artifacts.
- [`BTFL_cli_backup_OPENRACER_20260812_120242_HOBBYWING_XROTORF7CONV.txt`](../../backups/BTFL_cli_backup_OPENRACER_20260812_120242_HOBBYWING_XROTORF7CONV.txt)
  is the last pre-flash backup.
- [`BTFL_cli_backup_OPENRACER_20260812_122055_HOBBYWING_XROTORF7CONV.txt`](../../backups/BTFL_cli_backup_OPENRACER_20260812_122055_HOBBYWING_XROTORF7CONV.txt)
  is the first post-flash verification backup.

## Why this build

KAACK V19 exists both on a Betaflight 4.5-based branch and on the newer 2025.12 development line.
The 4.5 build was chosen because it keeps MSP API 1.46 and stays in the same configuration family as
the original 4.5.1 firmware. It provides V19 without moving this quad to the
`2025.12.3-alpha.KAACK_V19` build used by `openracer2`.

The exact Hobbywing target matters: this board is `HOBBYWING_XROTORF7CONV`, not
`HOBBYWING_XROTORF7CON` or a generic STM32F7 target.

Firmware provenance:

- KAACK source: <https://github.com/limonspb/betaflight>
- Branch: `KAACK-4.5.0`
- Source commit: `8cd44381217948c0b2b5087f12e17dde15d6a25c`
- Target configs: <https://github.com/betaflight/config>
- Config branch: `4.5-config`
- Config commit: `7b1f01a25d8cb6379ebeeeca9f0e91c24925e907`

## Reproducing the firmware

The build was made from a clean shallow checkout. The target config repository must be pinned to
the recorded `4.5-config` commit; its current default branch uses a newer directory layout that the
4.5 build system does not consume.

```bash
git clone --depth 1 --branch KAACK-4.5.0 \
  https://github.com/limonspb/betaflight.git /tmp/openracer-kaack-betaflight
git -C /tmp/openracer-kaack-betaflight submodule update --init --depth 1

make -C /tmp/openracer-kaack-betaflight arm_sdk_install
make -C /tmp/openracer-kaack-betaflight configs
git -C /tmp/openracer-kaack-betaflight/src/config checkout --detach \
  7b1f01a25d8cb6379ebeeeca9f0e91c24925e907

make -C /tmp/openracer-kaack-betaflight HOBBYWING_XROTORF7CONV
```

The build output is
`obj/betaflight_4.5.3_STM32F7X2_HOBBYWING_XROTORF7CONV.hex`. It was renamed to include
`KAACK_V19` before being archived here. Its SHA-256 must match `SHA256SUMS`.

## Flash and restore procedure

1. Remove all propellers and disconnect the LiPo.
2. Save a fresh `diff all` backup before flashing.
3. Open Betaflight Configurator 10.10.x and enter Firmware Flasher.
4. Choose **Load Firmware [Local]** and select the archived HEX.
5. Verify the controller is the `HOBBYWING_XROTORF7CONV` STM32F7X2 board.
6. Enable **Full chip erase** and flash without disconnecting USB.
7. Reconnect, open CLI, and paste the entire selective restore file from this directory.
8. Wait for its final `save` and reboot, then reconnect and run:

   ```text
   version
   status
   get rpm_limit
   get rpm_limit_value
   get motor_output_limit
   diff all
   ```

9. Confirm the version is `4.5.3.KAACK_V19`, the target is
   `HOBBYWING_XROTORF7CONV`, `rpm_limit = ON`, `rpm_limit_value = 18000`, and
   `motor_output_limit = 100`.
10. With props still removed, verify gyro orientation, receiver channels, failsafe, motor order and
    direction, ARM/AIRMODE/ANGLE/BEEPER/TURTLE/BLACKBOX/VTX PIT modes, HDZero OSD, and VTX control.
11. Take a new `diff all` backup. After any OSD edits, take another backup and update the restore
    file so the recovery package stays aligned with the aircraft.
12. Copy the new dump into `backups/` and regenerate the fleet inventory:

    ```bash
    python3 .claude/skills/fpv-fleet-update/scripts/update_fleet.py
    ```

## Verification from the recorded dumps

The 12:20 post-flash dump confirms the expected firmware, target, limiter, rates, modes and tuning.
The 12:25 dump differs from it only in six OSD positions: Timer 1, Timer 2, flight mode, craft name,
warnings and the KAACK spec logo. The final fleet output reports the KAACK firmware and enabled RPM
limiter; the 100% motor output is absent from `diff all` because 100 is the firmware default.

The dumps cannot prove physical behavior. Gyro direction, receiver response, failsafe, motor
order/direction and video must still be checked on the bench, and the first flight after flashing
should be conservative.
