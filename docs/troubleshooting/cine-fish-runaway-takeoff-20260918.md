# Cine-fish: jump and drop on takeoff, 2026-09-18

## Confirmed outcome

Both recorded takeoffs end in **DISARM reason 6: RUNAWAY_TAKEOFF**, followed by a LOG_END event. Betaflight intentionally disarmed after uncontrolled yaw developed. The exact physical/configuration fault remains unconfirmed.

Raw log: `blackbox/BTFL_BLACKBOX_LOG_CINE-FISH_20260918_172219_GEPRCF411_AIO.BBL` (gitignored; 347,392 bytes).
SHA256: `7885768519e59fb591d47d1bcc0809c2060bd628f7301aeac209320e269391ca`.
Original: `C:\Users\irekr\OneDrive\Documents\FPVBackup\BBL`.
Analysis performed 2026-09-18/19 with orangebox; three sections, second has no data.

| Evidence | Log 1 | Log 3 |
| --- | --- | --- |
| Decoded duration | 6.80 s | 4.57 s |
| Frames | 6,810 | 4,578 |
| Maximum interval between decoded frames | 1,020 us | 1,020 us |
| Peak throttle command | 1203 | 1168 |
| Yaw setpoint throughout | 0 deg/s | 0 deg/s |
| Final yaw rate | -647 deg/s | +505 deg/s |
| Start / minimum voltage | 15.30 / 12.46 V | 15.22 / 12.75 V |
| Peak logged current (calibration unverified) | 46.6 A | 60.4 A |
| Disarm reason | 6, runaway takeoff | 6, runaway takeoff |

All available slow frames have failsafePhase=0, rxSignalReceived=1, rxFlightChannelsValid=1. No receiver failsafe is recorded. Both captures end normally with the runaway disarm event; abrupt FC power loss is not the recorded shutdown mechanism.

## Failure sequence

Times are relative to the first decoded frame of each section; motor indices below are Blackbox's zero-based indices, not physical positions verified on this quad.

- Log 1 at 6.674 s: yaw -44 deg/s; motor commands [692,443,369,569]. At 6.714 s: yaw -204, motors [1873,158,260,1568]. At 6.754 s: yaw -445, motors [2047,158,1094,1913]. Final yaw -647. The m0/m3 diagonal is driven harder while yaw accelerates away from the zero setpoint.
- Log 3 at 4.437 s: yaw +31 deg/s; motors [158,682,865,405]. At 4.477 s: yaw +164, motors [424,1708,1896,158]. At 4.497 s: yaw +254, motors [158,1380,2047,377]. Final yaw +505. The opposite m1/m2 diagonal is driven harder while yaw accelerates in the opposite direction.
- Motor command range in the headers is 158–2047. Significant voltage sag accompanies the high outputs. This does not independently establish a defective battery.

Opposite spin directions on repeated attempts, with corresponding opposite diagonal corrections, support a yaw feedback polarity mismatch more strongly than a single consistently failing motor. This is an inference, not proof of physical motor rotation.

## Ranked checks before another flight

1. **Motor rotation versus mixer direction.** Archived 14:35:15 dump has `yaw_motors_reversed = OFF`; fresh live value is still needed. With props removed, verify actual motor rotation against the Motors tab arrows. If actual motors are props-out but the FC expects props-in, the yaw correction can reinforce the spin. Confirm the discrepancy before changing anything.
2. **Motor order and gyro orientation.** With props removed, individually identify each motor using the Motors tab diagram; check all three axes of the Setup model against actual quad movement. A mismatch supports a mapping/alignment fault. Correct sensor orientation cannot be inferred from the saved board-yaw setting alone.
3. **Mechanical/ESC fault.** Check prop installation, rubbing ducts, loose hubs, motor wires and phase joints if geometry matches. There is no eRPM telemetry (`dshot_bidir=0`), so this log cannot prove or rule out desync or motor failure under load.

Keep runaway protection enabled. Do not use another takeoff to determine motor direction, change alignment by guesswork, or tune away the shutdown. These were the initial diagnostic checks; see the successful follow-up and pilot-confirmed corrective actions below.

## Earlier CPU issue

Before the attempt, reducing `pid_process_denom` from 1 to 2 reduced reported CPU load from 63% to 32% and removed LOAD. These flight-log headers confirm denom=2 with gyro looptime=125 us (nominal 8 kHz gyro / 4 kHz PID). The drop has a distinct recorded runaway disarm cause. No flight CPU-load trace is present.

USB-only status with the radio off explains RXLOSS in that bench snapshot; USB-only voltage readings are insufficient to diagnose battery configuration.

## Analyzer correction

The existing analyzer incorrectly printed “Control Loop: Clean” when eRPM was absent. Updated it to mark the check unavailable, expose disarm/end events, and avoid treating parser errors as evidence of power loss. RPM mismatch flags, when telemetry exists, remain a heuristic rather than a confirmed ESC diagnosis. A local real-log regression test verifies the two runaway events and missing-RPM caveat.

## Primary references

- [Betaflight 4.5.5 disarm enum](https://github.com/betaflight/betaflight/blob/4.5.5/src/main/fc/core.h): reason 6 is RUNAWAY_TAKEOFF.
- [Betaflight runaway takeoff protection](https://betaflight.com/docs/wiki/guides/current/Runaway-Takeoff-Prevention): auto-disarm behavior and motor/prop/orientation checks.
- [Betaflight 4.5.5 Quad X mixer](https://github.com/betaflight/betaflight/blob/4.5.5/src/main/flight/mixer_init.c): diagonal yaw coefficients.

## Follow-up: 2026-09-19 successful short test

Copied `BTFL_BLACKBOX_LOG_CINE-FISH_20260919_080822_GEPRCF411_AIO.BBL` from the Windows FPVBackup/BBL directory into local `blackbox/` and verified byte equality. This export contains four sections: the first three reproduce the previous two failed attempts and empty section; section 4 is the new test. Historical runaway events should not be mistaken for new failures.

The new section decodes fully: 9,091 frames over 9.08 seconds, maximum frame gap 1,021 microseconds, with LOG_END present. Disarm reason 4 is SWITCH, verified against [Betaflight 4.5.5 core.h](https://github.com/betaflight/betaflight/blob/4.5.5/src/main/fc/core.h). No runaway disarm occurred in this section.

- Yaw stayed between -18 and +20 degrees/second with zero yaw setpoint, compared with the previous -647 and +505 degree/second excursions.
- Roll rates ranged from -56 to +47 degrees/second; pitch from -37 to +48.
- No saturated motor frames were reported by the analyzer; peak RC throttle was 1360.
- Available receiver fields remained valid, with failsafePhase 0.
- Recorded voltage started at 15.26 V and reached 13.39 V minimum; peak recorded current was 50.1 A. Calibration remains unverified.

The earlier runaway behavior is absent in this short test, consistent with the user's report that it now looks good. The pilot confirmed reordering the motors and changing motor directions to props-out before this test. The successful test after these changes supports a motor mapping/direction configuration fault as the cause of the earlier runaway behavior. Because both were changed together, the evidence does not isolate their individual contributions. The resulting configuration is now archived in `backups/BTFL_cli_CINE-FISH_20260919_080901_GEPRCF411_AIO.txt`; a nine-second test does not establish performance throughout a full flight. Four-motor RPM telemetry is still absent, so motor desync cannot be assessed from RPM.

### Working configuration archived

The September 19 08:09:01 CLI backup was copied byte-for-byte from FPVBackup. It confirms BF 4.5.5, `yaw_motors_reversed = ON`, `pid_process_denom = 2`, and MAX7456/AUTO analog OSD. Motor output reordering remains `0,1,2,3,4,5,6,7` and motor 1–4 resources remain B04/B05/B06/B07. The pilot-reported reordering is recorded, but its mechanism cannot be inferred from these unchanged mappings. Fleet inventory regenerated from this backup.

### Runtime verification: 2026-09-19 12:12 UTC

Pilot supplied `version`, `status`, `flash_info`, and `tasks` after the new backup:

- Betaflight 4.5.5, STM32F411 / GEPRCF411_AIO, config revision `92c695a`, build key `3b7d5fd28e6489c3dd138b3d7ee0fe7a`; configuration CONFIGURED.
- CPU 32%; task total excluding SERIAL 30.1%. Gyro approximately 8 kHz; FILTER and PID approximately 4 kHz. No LOAD arming-disable flag, confirming the earlier CPU block remains absent in this bench snapshot.
- MPU6000 gyro/accelerometer and MAX7456 OSD (30 x 13) detected; I2C errors 0.
- Flash JEDEC `0x00ef4018`: 16,777,216 bytes (16 MiB), 256 sectors of 65,536 bytes. FLASHFS spans sectors 0–255; used space 647,168 bytes (about 3.9%). Storage is detected and allocated.
- Arming-disable flags: RXLOSS CLI MSP. RXLOSS indicates no valid receiver input in this snapshot; consistent with the previously reported radio-off bench setup if that still applies. CLI/MSP were present during the diagnostic connection. Current radio/power state was not explicitly reconfirmed.
- Displayed voltage 3.72 V / 1S is recorded as a bench reading, not confirmation of flight-pack cell count or voltage calibration.

This snapshot verifies runtime load and storage detection; it does not resolve the separately outstanding SmartAudio communication issue or establish full-flight reliability.
