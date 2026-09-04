# OpenRacer intermittent thrust loss

## Symptom

OpenRacer has repeated thrust-loss/desync-like events under load. A motor was replaced after the
2026-07-15 rear-corner crash, but the 2026-08-21 flight still ended in a high-current loss of
control with the replacement motor installed. Props-off bench checks had shown zero DShot errors.
In the decoded data, Betaflight `motor[0]` is physical motor 1; references to motor 0 below use the
zero-based blackbox field name.

## Evidence preserved

- Current Betaflight configuration:
  `backups/BTFL_cli_backup_OPENRACER_20260902_160705_HOBBYWING_XROTORF7CONV.txt`.
- Flight recording: `blackbox/BTFL_BLACKBOX_LOG_OPENRACER_20260821_084648_HOBBYWING_XROTORF7CONV.BBL`,
  internal log 9 (raw blackbox files are intentionally gitignored).
- Repeat-test recording:
  `blackbox/BTFL_BLACKBOX_LOG_OPENRACER_20260902_165307_HOBBYWING_XROTORF7CONV.BBL`,
  internal logs 1 and 2.
- Dated raw AM32 exports: `esc-configs/openracer/2026-09-02/`.

The 2026-09-02 CLI dump differs from the final 2026-08-12 post-upgrade dump only in accelerometer
calibration (`56,-34,45,1` to `35,-24,62,1`). The motor protocol-related configuration is unchanged:
bidirectional DShot is on, dynamic idle is 4,000 RPM, and the 18,000 RPM limiter is on.

All four ESC exports identify AM32 2.17 on `XRotor45 F4`. ESC2–ESC4 are byte-identical. ESC1 differs
only in the expected motor-direction field: ESC1 normal, ESC2–ESC4 reversed. There is no evidence
of a channel-specific timing, PWM, startup-power, protection, or other configuration mismatch.

## Flight timeline

The repository detector flags 154 motor/frame observations (1.31% of 12,368 frames): motor 0 = 67,
motor 1 = 18, motor 2 = 16, motor 3 = 53.

| Time from log start | Observation |
|---:|---|
| 5.559 s | First detector hit, motor 0 |
| 5.586 s | Peak current, 105.1 A; battery still 21.91 V |
| 5.704 s | First sustained motor-3 window |
| 5.939 s | Motors 2 and 3 also appear during recovery |
| 6.026 s | Minimum battery voltage, 17.31 V (2.88 V/cell) |
| 6.152 s | Largest gyro excursion, after the first RPM anomalies and voltage collapse |

The low voltage is severe and can worsen the event, but it occurs about 467 ms after the first
motor-0 anomaly. It therefore does not explain the onset by itself. The multi-motor summary also
does not prove three independent desyncs: motors 1–3 are commanded unevenly while the controller is
already attempting to recover.

## 2026-09-02 repeat test

The new recording contains two throttle-active sections. Both remain stable until a centered-stick,
modest-throttle event near the end, then develop a sudden yaw-rate excursion and rapidly alternating
motor saturation:

| Internal log | Event onset | RC throttle | First gyro symptom | Voltage at onset | First detector motor | Peak current | Minimum voltage |
|---:|---:|---:|---|---:|---|---:|---:|
| 1 | 11.060 s | 1378 | yaw about -230 deg/s | 24.31 V | m1 at 11.089 s | 69.4 A | 18.37 V |
| 2 | 10.655 s | 1333 | yaw about -247 deg/s | 24.22 V | m3 at 10.667 s | 73.6 A | 19.37 V |

The commanded roll, pitch, and yaw inputs are essentially centered at both onsets. The eRPM values do
not show one motor abruptly collapsing before the initial yaw excursion. Battery voltage is still
about 24.2--24.3 V at onset and sags only after the controller begins driving outputs to opposite
rails. Thus the high current and deep sag are consequences or amplifiers of the event in these two
captures, not its initial trigger.

The summary detector reports 180 observations across all four motors in log 1 and 87 observations
across all four motors in log 2. These occur after output saturation begins, and the leading detector
motor changes from m1 to m3 between captures. The detector is comparing instantaneous command with
motor RPM; during the rapid corrective reversals, rotor inertia makes those fields lag naturally.
These new flags therefore should not be treated as proof of four ESC desyncs.

## Ranked hypotheses

1. A yaw-axis control instability, mechanically induced gyro disturbance, or gyro-signal corruption
   begins the event. Both repeat captures have nearly identical centered-stick yaw onsets without a
   preceding single-motor eRPM collapse.
2. A shared ESC/power-path disturbance upsets motor torque or the FC at a particular load. It remains
   plausible, but the battery rail does not collapse before either new onset.
3. ESC channel 1, its board-side phase joints/traces, or its wiring fails under load. The 2026-08-21
   evidence supported this, but it is now weaker because the two repeat captures do not have m0 lead.
4. The battery cannot sustain the requested current. It clearly worsens the event, but the two new
   timelines make it unlikely to be the initiating cause.
5. The replacement motor is independently faulty. This is now low probability: the fault survived a
   motor replacement and the repeat captures do not isolate one motor.

## Next test

Completed after the 2026-09-02 exports: visual inspection found no FC/ESC red flags; all motors spin
normally from Betaflight; all disconnected motors measured about 0.3 ohm consistently across their
three phase pairs; and all ESC channels/phases produced consistent diode-mode readings in all tested
probe orientations (including about 0.456 V from ground to each phase). These static/no-load tests
found no open winding, unequal phase path, or obvious short/open MOSFET path. They cannot reproduce
or clear a fault that appears only under current or heat.

The 2026-09-02 repeat test is red-capable: both captures reproduce the centered-stick onset at modest
throttle. Do not repeat it in free flight until the mechanical stack, FC soft mounting, FC/ESC wiring,
motor screws, frame, and prop condition/orientation have been checked specifically for a yaw-inducing
disturbance. Review gyro spectrum data if a new log records it; this log configuration contains no
frequency-domain fields. A known-good battery remains useful as a one-variable check, but the new
onset timing means it is no longer the leading test.

If those checks are clean, the safest decisive substitution is the 4-in-1 ESC, followed by a restrained
logged test. A correctly remapped cross-channel bench/load test can distinguish a channel fault, but a
simple motor-plug swap must not be flown because it changes the motor-to-corner mapping.

Actual motor rotation must be rechecked props-off after every phase-wire or motor swap.
