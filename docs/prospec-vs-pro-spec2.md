# PROSPEC vs PRO-SPEC2

Compared on 2026-09-04 from the newest saved `diff all` for each quad:

- PROSPEC: `backups/BTFL_cli_backup_PROSPEC_20260902_111305_HOBBYWING_XROTORF7CONV.txt`
- PRO-SPEC2: `backups/BTFL_cli_PRO-SPEC2_20260904_142222_HDZERO_HALO.txt`

PROSPEC is a self-built quad. PRO-SPEC2 was assembled and configured by Five33. That makes the
second quad a useful reference, but not a universal tune donor: a `diff all` records only departures
from each firmware's defaults, and these quads use different FCs, gyros, ESCs, motors, receiver
implementations, firmware versions, and finished weights.

## Airframes and electronics

| Item | PROSPEC | PRO-SPEC2 |
|---|---|---|
| Purpose | 7-inch Pro Spec race | 7-inch Pro Spec race |
| Battery | 6S | 6S |
| Recorded weight | 1215 g with battery | 1178 g with battery, without props |
| Props | HQProp 7x4x3 tri-blade | HQProp 7x4x3 tri-blade |
| Motors | Hobbywing XRotor 2807 1300 KV | EMAX ECO II 2807 1300 KV |
| FC / gyro | Hobbywing XRotor Convertible F7 | HDZero Halo H743, ICM gyro |
| ESC | Hobbywing XRotor 65A HD AM32 stack | Foxeer Reaper 60A 4-in-1 |
| Camera | Runcam HDZero Nano 90 V2 | HDZero Nano 90 V2 |
| VTX | HDZero Race V3 HD | HDZero Race V3 |
| Receiver | External receiver configuration in dump (SBUS) | Halo onboard 2.4 GHz Gemini ELRS, 3.5.3 (`40555e`), ISM2G4 |
| Betaflight | 4.5.3.KAACK_V19, STM32F7 | 2025.12.3-alpha.KAACK_V19, STM32H743 |

The weights are not directly comparable because the PRO-SPEC2 figure excludes props.

## Settings comparison

### Already the same

- motor KV metadata: 1300 KV
- bidirectional DShot: on
- reversed motor direction: on
- RPM limiter: on at 13,000 RPM
- active PID profile and rate profile: profile 0
- all six mode assignments and switch ranges
- VTX power level: 1 (25 mW according to the saved table)
- pilot name: `papfpv`

The matching modes are ARM on AUX1 low, ANGLE on AUX2 high, beeper on AUX3 high, blackbox on AUX4
high, flip-over-after-crash on AUX2 middle, and VTX pit mode on AUX4 middle.

### Rates

Both use Betaflight rates with zero expo and 0.70 super rate on every axis.

| Axis | PROSPEC RC rate | PROSPEC max | PRO-SPEC2 RC rate | PRO-SPEC2 max |
|---|---:|---:|---:|---:|
| Roll | 0.95 | about 633 deg/s | 0.88 | about 587 deg/s |
| Pitch | 0.80 | about 533 deg/s | 0.78 | about 520 deg/s |
| Yaw | 0.80 | about 533 deg/s | 0.78 | about 520 deg/s |

PRO-SPEC2 is therefore about 7% slower at maximum roll and about 2.5% slower in pitch and yaw. Its
centre sensitivity is lower by the same raw-rate proportions. Rates describe pilot stick response,
not the physical tune, so this is the cleanest setting to transfer between the two builds.

### PID, feedforward, idle, and filtering

PRO-SPEC2 explicitly saves the following custom profile-0 choices:

- roll PIDF: P 42, I 37, D 25, F 144; D Max 33
- pitch PIDF: P 44, I 39, D 31, F 150; D Max 42
- yaw: P 42, I 37, F 144
- simplified master 105, PI 90, I 50, D 80, feedforward 115, pitch-D 110
- anti-gravity gain 50, thrust linearization 20, dynamic idle minimum 35
- feedforward jitter reduction 3 and boost 18
- one dynamic notch at Q 500, RPM-filter harmonics 2
- gyro filtering at 187/375 Hz and D-term filtering at 78-157/157 Hz
- PID process denominator 2

PROSPEC's latest `diff all` contains no PID or filter departures, so it is running its own
4.5.3.KAACK_V19 defaults in these areas. A blank in its diff does **not** establish that its effective
values equal PRO-SPEC2's values. The PRO-SPEC2 values also come from a newer alpha firmware with a
different FC/gyro, so direct line-by-line CLI copying would not be a controlled comparison.

Other differences are configuration choices rather than upgrades: PROSPEC starts on Raceband 1
(5658 MHz), while PRO-SPEC2 starts on Raceband 8 (5917 MHz); OSD layouts and LED definitions differ.

## What is worth applying to PROSPEC

### Recommended: try the PRO-SPEC2 rates

This is the one change I would apply first. The slightly calmer roll response is plausibly an
intentional 7-inch racing choice and is independent of FC, gyro, ESC, and motor brand. It is also
easy to evaluate and reverse. Paste this into the PROSPEC CLI:

```text
rateprofile 0
set rates_type = BETAFLIGHT
set roll_rc_rate = 88
set pitch_rc_rate = 78
set yaw_rc_rate = 78
set roll_srate = 70
set pitch_srate = 70
set yaw_srate = 70
set roll_expo = 0
set pitch_expo = 0
set yaw_expo = 0
save
```

The current PROSPEC values are `95/80/80` RC rate and `70/70/70` super rate, so rollback is simple.
Judge the change on gate placement and correction precision rather than smooth cruising alone.

### Already adopted: keep the matching mode layout

The two quads now have identical mode logic. Keeping that consistency is valuable for muscle memory
and emergency operation, and no further mode change is needed.

### Consider only as a measured tuning experiment

The PRO-SPEC2 tune suggests useful *areas to test* on PROSPEC—lower-than-stock I gain, modest D/D-Max,
strong feedforward, thrust linearization, and dynamic idle—but I would not paste its PID/filter block
into PROSPEC. Those values are precisely the settings most affected by gyro noise, frame resonance,
motor/ESC response, firmware defaults, and loop timing.

If PROSPEC has a specific handling problem, change one category at a time and compare matched
blackbox flights. In priority order:

1. Check whether `dyn_idle_min_rpm = 35` improves low-throttle authority and recovery without hot
   motors or rough idle.
2. Evaluate thrust linearization 20 for throttle consistency, especially through turns and battery
   sag.
3. Tune feedforward for racing response only after adopting the preferred rates.
4. Touch PIDs and filters last, using gyro/D-term spectra, motor temperature, propwash, and motor
   output traces rather than the expert-built quad's numbers alone.

These are experiments, not recommendations to copy the numerical block. Before each one, save a new
PROSPEC `diff all`; use short first flights, inspect motor temperature immediately, and keep comparable
blackbox logs. Do not transfer PRO-SPEC2's board alignment, accelerometer calibration, serial setup,
receiver smoothing, PID loop denominator, OSD coordinates, or LED definitions.

## Bottom line

Apply the PRO-SPEC2 rates if the goal is to make PROSPEC's stick feel match the Five33 build. Keep the
already-matched modes and 13K limiter. Treat the expert tune as evidence for what to investigate, not
as a safe preset: almost every remaining performance setting is entangled with the hardware and
firmware differences that this comparison is meant to exclude.
