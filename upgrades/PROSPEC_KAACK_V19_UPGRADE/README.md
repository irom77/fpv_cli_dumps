# PROSPEC KAACK V19 / ProSpec 13K upgrade

This package upgrades the 7-inch `prospec` race quad from Betaflight 4.3.2 to
Betaflight 4.5.3.KAACK_V19 and applies KAACK's built-in **MGP PRO 13K** settings. It is a
ProSpec/7-inch configuration, not the 5-inch Freedom Spec configuration.

## Result

| Item | Before | After |
|---|---|---|
| Flight controller target | HOBBYWING_XROTORF7CON | HOBBYWING_XROTORF7CONV |
| Firmware | Betaflight 4.3.2 (`60c9521`) | 4.5.3.KAACK_V19 (`8cd4438`) |
| MSP API | 1.44 | 1.46 |
| Race specification | none | MGP PRO 13K |
| RPM limiter | off/default | on, 13,000 RPM; PID 25/10/8 |
| Motor metadata | stock/default | 14 poles, 1300 KV (preset values) |
| Receiver | SBUS | preserved |
| Motor protocol | DSHOT600 | preserved, bidirectional DShot enabled |

The original pre-flash backup is
[`BTFL_cli_backup_PROSPEC_20260825_092510_HOBBYWING_XROTORF7CON.txt`](../../backups/BTFL_cli_backup_PROSPEC_20260825_092510_HOBBYWING_XROTORF7CON.txt).

## Why the target name changes

The 2022 firmware reported this board as `HOBBYWING_XROTORF7CON`. The official Betaflight 4.5
configuration repository does not contain that old spelling; the supported successor target for
the HobbyWing XRotor Convertible F7 is `HOBBYWING_XROTORF7CONV`. The firmware was therefore built
for the official `CONV` target approved for this upgrade. Do not flash a generic STM32F7 target.

## Package contents

- `betaflight_4.5.3.KAACK_V19_STM32F7X2_HOBBYWING_XROTORF7CON.hex` is the exact firmware to flash.
- `BTFL_cli_restore_PROSPEC_20260825_KAACK_V19.txt` selectively restores the known receiver,
  motor protocol, ARM mode, calibration, OSD, craft name, and ProSpec 13K settings.
- `SHA256SUMS` authenticates all recovery artifacts in this directory.

The restore deliberately does not copy a 5-inch tune, rates, motor orientation, or Freedom 18K
settings from another quad. Settings absent from the original PROSPEC backup remain at KAACK 4.5
defaults and must be checked on the aircraft.

## Firmware provenance

- KAACK source: <https://github.com/limonspb/betaflight>
- Branch: `KAACK-4.5.0`
- Source commit: `8cd44381217948c0b2b5087f12e17dde15d6a25c`
- Target configs: <https://github.com/betaflight/config>
- Config branch: `4.5-config`
- Config commit: `7b1f01a25d8cb6379ebeeeca9f0e91c24925e907`
- Build target: `HOBBYWING_XROTORF7CONV`

KAACK source names the selected preset `MGP PRO 13K`. Its values are recorded explicitly in the
restore: limiter on, 13,000 RPM, limiter PID 25/10/8, 14 motor poles, and 1300 KV.

## Flash and restore

1. Remove all propellers and disconnect the LiPo.
2. Save a fresh `diff all` backup before flashing.
3. In Betaflight Configurator 10.10.x, load the archived local HEX.
4. Confirm the target is `HOBBYWING_XROTORF7CONV`, enable **Full chip erase**, and flash.
5. Reconnect, open CLI, and paste the entire selective restore file. Wait for `save` and reboot.
6. Reconnect and run:

   ```text
   version
   status
   get rpm_limit
   get rpm_limit_value
   get rpm_limit_p
   get rpm_limit_i
   get rpm_limit_d
   get motor_poles
   get motor_kv
   diff all
   ```

7. Confirm `4.5.3.KAACK_V19`, target `HOBBYWING_XROTORF7CONV`, limiter `ON`, value `13000`,
   PID `25/10/8`, motor poles `14`, motor KV `1300`, and the OSD ProSpec logo/name.
8. With props still removed, verify gyro orientation, receiver endpoints and channel order,
   failsafe, ARM mode, motor order and direction, bidirectional DShot/RPM telemetry, OSD, camera,
   and VTX operation. Confirm the physical motor pole count before arming.
9. Take a new `diff all` backup and place it in `backups/` as the post-flash record.

The saved CLI dump cannot prove physical motor direction, gyro direction, receiver behavior, or
video operation. The first powered test and first flight should be conservative.

## Reproducing the firmware

```bash
git clone --depth 1 --branch KAACK-4.5.0 \
  https://github.com/limonspb/betaflight.git /tmp/prospec-kaack-betaflight
git -C /tmp/prospec-kaack-betaflight submodule update --init --depth 1
make -C /tmp/prospec-kaack-betaflight arm_sdk_install
make -C /tmp/prospec-kaack-betaflight configs
git -C /tmp/prospec-kaack-betaflight/src/config checkout --detach \
  7b1f01a25d8cb6379ebeeeca9f0e91c24925e907
make -C /tmp/prospec-kaack-betaflight HOBBYWING_XROTORF7CONV
```

The build output is `obj/betaflight_4.5.3_STM32F7X2_HOBBYWING_XROTORF7CONV.hex`; it was renamed
to include `KAACK_V19` before archiving.
