# Green Hornet V3 will not take off — two independent faults

**Status: one fault fixed, one open.** The quad flips at liftoff. Two separate causes were found.
A control-loop fault (stick offsets integrating without bound) is fixed and verified. A thrust
fault (Motor 3 down 14% under load) is confirmed and open.

## Symptom

Since 2026-09-14 the quad will not take off. Every attempt is the same: it sits while throttle is
raised, then departs violently the moment it gets light, drawing 60–115 A, and the log ends. It
flew fine before the 4.2.4 to 2026.6.1 firmware upgrade on 2026-09-05.

The pilot also reported from the start that **Motor 3 chokes and makes a different noise** on the
bench. That observation turned out to be correct and was wrongly set aside twice — see Mistakes.

Motor numbering: Betaflight "Motor N" in the Motors tab is blackbox `motor[N-1]`. Betaflight
Motor 3 is blackbox `motor[2]` / `eRPM[2]`. This document uses the Betaflight 1-based number except
where a blackbox field is named directly.

## Fault 1 — stick offsets integrating without bound (FIXED)

`deadband` and `yaw_deadband` were both `0`, and the sticks did not rest at exact centre. With no
dead zone, a residual offset became a standing rate demand. The airframe cannot answer a yaw demand
while the ground holds it, so the error never cleared and the integrator ran away whenever throttle
was above `min_check = 1050`, dumping into the mixer at liftoff.

The props-off bench ramp with the quad clamped isolates this cleanly — gyro at 0–2 deg/s, nothing
moving, sticks at rest:

| t | throttle | I roll | I pitch | **I yaw** | motors |
|---:|---:|---:|---:|---:|---|
| 1.40 | 1000 | 0 | 0 | **0** | [169, 159, 158, 161] |
| 2.80 | 1354 | −2 | 14 | **−14** | [844, 767, 801, 835] |
| 4.20 | 1517 | −4 | 27 | **−72** | [1311, 975, 1057, 1217] |
| 5.60 | 1507 | −6 | 41 | **−131** | [1422, 797, 987, 1264] |
| 6.30 | 1533 | −8 | 48 | **−160** | [1493, 809, 936, 1338] |
| 7.00 | 1000 | 0 | 0 | **0** | [172, 158, 161, 161] |

Yaw I-term climbs monotonically and is still climbing at 6.3 s; it snaps to 0 the instant throttle
drops below `min_check`. Motors split exactly on the yaw diagonal. `setpoint[2]` is −1 on every
frame — the stick offset.

### The fix

```text
set deadband = 2
set yaw_deadband = 2
save
```

### Verified

Repeating the identical props-off ramp afterwards (log 11 of the 18:19 recording):

| | before (log 10) | after (log 11) |
|---|---:|---:|
| Yaw setpoint at rest | −1 | **0** |
| Yaw I-term peak | **−160**, still climbing | **−2** |
| Pitch I-term peak | +48 | −1 |
| Motor spread, sticks centred | 253 → runaway | **6–30** |

All three sticks now read exactly 0 at rest. The one remaining excursion — roll I-term to −73 at
t = 7.2–8.0 s — is a genuine stick input (`rcRoll` −7 to −10, returning to exactly 0) winding up
against the clamp, which is a bench artifact and not a fault.

`deadband = 2` **masks** the offset rather than removing it. If a gimbal drifts past ±2 later, this
returns with no obvious connection to today. Trim the sticks to exactly 1500 as the real fix.

## Fault 2 — Motor 3 down 14% under load (OPEN)

With Fault 1 fixed, the first props-on takeoff attempt flipped again. That log contains 2.4 s of
steady idle with props fitted, which finally gives a valid loaded comparison at matched commands:

| | Motor 1 | Motor 2 | **Motor 3** | Motor 4 | deficit |
|---|---:|---:|---:|---:|---:|
| **Props off** (unloaded) | 397 | 414 | 376 | 407 | **−7.4%** |
| **Props on**, cmd 158–200 | 402 | 419 | 352 | 408 | **−14.1%** |
| **Props on**, cmd 200–260 | 399 | 416 | 350 | 404 | **−13.9%** |

**The deficit doubles under load.** That is the signature of a motor that cannot hold RPM against
torque, as opposed to a simple Kv difference, which would show the same percentage loaded or not.
Thrust goes as RPM², so 14% less RPM is roughly **26% less thrust on that corner** — ample to flip
the quad as soon as it gets light.

Motor 3 is a **Racerstar Racing Edition BR1507 2800KV**; motors 1, 2 and 4 are the original iFlight
XING 1507 2800KV. The quad flew with that motor fitted on 4.2.4, so it has degraded rather than
merely being mismatched — plausibly during the four 100 A+ flips, though it may equally have been
failing beforehand and have contributed to the first one.

Telemetry is otherwise clean on that channel: no eRPM dropouts, and roughness identical to its peers
(12 against 12/13/12).

### Next test

Swap the prop from Motor 3 with the one from Motor 1, then repeat an **idle-only, props-on** capture
with the quad secured. No takeoff — the 2.4 s of idle in log 13 was enough to measure the deficit.

- deficit **follows the prop** → damaged, mismatched or inverted prop; cheap fix
- deficit **stays on Motor 3** → the motor

Also inspect that prop for chips, check the duct for rub marks, and compare bell drag and shaft play
by hand against the other three.

### Recommendation

Replace Motor 3 with a **XING 1507 2800KV** to restore the matched set. No spare exists in
`spare_parts.csv` or `orders.csv` — the only 1507 in the ledger is a T-Motor F1507 **3800KV**
(Pyrodrone, 2023-09-05), the wrong KV for a 6S build.

## Fault 3 — the upgrade reinterpreted the yaw rate (FIXED, contributory)

Rateprofile 0 stores `yaw_rc_rate = 172`. On 4.2.4 that rateprofile carried no `rates_type`, so it
used that firmware's BETAFLIGHT default, where 172 means a 1.72x multiplier. 2026.6.1 defaults to
ACTUAL, where the same stored 172 means **1720 deg/s of centre sensitivity**. Roll and pitch were
at 7, or 70 deg/s.

The log proves the consequence, because all three axes rested at the same one-unit offset:

| Axis | rcCommand at rest | Centre sensitivity | Resulting setpoint |
|---|---:|---:|---:|
| Roll | +1 | 70 deg/s | **0** |
| Pitch | +1 | 70 deg/s | **0** |
| Yaw | −1 | 1720 deg/s | **−3 deg/s** |

Same offset on every axis; only yaw produced a standing command, purely because its centre
sensitivity was 24 times theirs. Arithmetic matches the logged values exactly: `−1/500 × 1720 =
−3.44`. Under 4.2.4's interpretation the same offset gave about **−0.69 deg/s**.

This did not by itself cause the flips — fixing it did not stop them — but it made Fault 1 roughly
five times worse, converting a harmless offset into a significant demand. It was also a genuine
regression on its own terms: 1720 deg/s centre swamps the 670 deg/s max-rate setting entirely.

### The fix

```text
rateprofile 0
set roll_rc_rate = 20
set pitch_rc_rate = 20
set yaw_rc_rate = 34
set yaw_srate = 115
save
```

This restores the 4.2.4 feel to within a few deg/s on every axis: roll/pitch 200 deg/s centre /
670 max, yaw 340 / 1150. Computed with `scripts/rates.py`, the repository's own rate maths.

## Other findings from the upgrade

Not causes of the flips, but real and worth fixing.

### ANGLE mode no longer exists, and its switch detent now arms turtle

| | 4.2.4 | 2026.6.1 |
|---|---|---|
| AUX2 1300–1700 | ANGLE (`aux 1 1 1 1300 1700`) | FLIP OVER AFTER CRASH |
| AUX2 1700–2100 | FLIP OVER AFTER CRASH (`aux 3 35 1 1700 2100`) | FLIP OVER AFTER CRASH |

The pilot takes off with AUX2/3/4 at 1000, so ANGLE was outside its range on 4.2.4 too — these
takeoffs were acro before and after. But turtle was widened from 1700–2100 to **1300–2100**, so the
detent that used to select ANGLE now selects turtle mode. `flightModeFlags` is constant at `8388609`
in every log, so turtle never fired; it remains a live hazard. Narrow it back:

```text
aux 3 35 1 1700 2100 0 0
```

### OSD points at a device this build does not have

`status` reports `OSD: MSP (53 x 20)`, and the config has `osd_displayport_device = MSP` with
`vcd_video_system = HD`. This is an analog build — UART1 runs Tramp VTX control at band 5 channel 8
/ 5917 MHz, RunCam Nano2 NTSC camera, SucceX-E analog VTX — and no UART is configured for MSP
DisplayPort, so the OSD renders nowhere and the MAX7456 overlay is unused. Both settings were at
firmware default in the 2026-09-05 diff, so this arrived with the 2026.6.1 defaults.

```text
set osd_displayport_device = MAX7456
set vcd_video_system = NTSC
```

### AIRMODE default changed

`feature AIRMODE` is absent from the 4.2.4 diff (4.2 default: off) and enabled in the 2026.6.1 dump
while absent from its diff (2026.6.1 default: on). It was turned off during this investigation and
disconfirmed as a cause — the props-off runaway reproduced with it off, verified by the log header
`features` word changing in exactly one bit (bit 22, 1 → 0). Currently left **off** because that
matches the 4.2.4 configuration; re-enable once the quad flies reliably.

### Tune and filtering did not transfer

Present on 4.2.4, absent afterwards (so now at 2026.6.1 defaults): `gyro_lowpass2_hz = 213`,
`dyn_lpf_gyro_min_hz = 170` / `max 425`, `dyn_lpf_dterm_min_hz = 63` / `max 153`,
`dterm_lowpass2_hz = 135`, `dyn_notch_width_percent = 10`, `vbat_pid_gain = ON`,
`anti_gravity_gain = 5000`, `dshot_burst = ON`, `thrust_linear` moved from master to profile scope.

PID numbers carried across (`p_roll 55 / i_roll 100 / d_roll 43`), and `d_min_roll`/`d_min_pitch = 0`
became `d_max_roll`/`d_max_pitch = 0`. `simplified_pids_mode = RPY` is now active, a mechanism that
did not exist in 4.2. Gyro noise is low throughout (unfiltered RMS 2.9/8.5/7.0 deg/s), so this is a
tidiness problem, not a flight-safety one. A `defaults` reset and clean rebuild on 2026.6.1 remains
worthwhile once the quad is flying.

## Mistakes worth not repeating

- **A props-off test cannot clear a motor.** Unloaded, Motor 3 measured −7.4% and was written off as
  a normal make-to-make difference. Loaded, it is −14%. An unloaded motor barely has to work, so it
  hides exactly the torque deficit being looked for. The pilot's own "it chokes" observation was
  correct throughout and was set aside twice on the strength of bad measurements.
- **Matched-command eRPM comparisons are worthless without settled commands.** Early comparisons put
  Motor 3 badly down, but the motors that sit at the mixer floor only pass through higher command
  bins transiently, so their eRPM lags. Sample counts gave it away (18 versus 550 in one bin).
  Filtering to settled commands returned no samples at all, because the PID moves all four outputs
  continuously in flight. Only a clamped or idling bench capture produces valid numbers.
- **Fixing a real bug does not mean fixing the bug.** Both the rate reinterpretation and the deadband
  were genuine faults, and both were verified fixed by measurement, but neither made the quad fly,
  because a thrust asymmetry sat underneath them.
- **Own the sequence.** Four hypotheses were disconfirmed by the pilot or by test before the cause
  was found. Where a known-good prior state exists, restoring it wholesale is often cheaper than
  bisecting a dozen changed settings one flight at a time — especially when each test costs a 100 A
  crash.

## Disconfirmed

- **Motor spin directions do not match `yaw_motors_reversed = ON`, or props in the wrong rotation.**
  Pilot bench-checked all four; directions correct.
- **ESC timing mismatch for the Racerstar motor.** The quad flew with that motor on 4.2.4.
- **Loss of ANGLE mode.** Pilot takes off with AUX2 at 1000, outside ANGLE's range on 4.2.4 too.
- **The yaw rate reinterpretation as the direct cause.** Fixing it removed the yaw windup (I-term
  −70 → −12) and the quad still flipped.
- **AIRMODE.** Disabled and verified in the log header; the runaway reproduced with it off.
- **A tired or damaged battery.** Median current across the early logs is 1.4 A; the sag belongs
  entirely to the ~150 ms departures.
- **Turtle mode firing during any attempt.** `flightModeFlags` constant at 8388609 throughout.
- **Vibration.** Unfiltered gyro RMS is 2.9/8.5/7.0 deg/s — clean.

## Evidence preserved

Configurations, all in `backups/`:

| File | State |
|---|---|
| `BTFL_cli_backup_GREEN_HORNET V3_20260904_165423_...` | 4.2.4, last known flying |
| `BTFL_cli_backup_GREEN_HORNET V3_20260905_090706_...` | first 2026.6.1 diff |
| `BTFL_cli_GREEN_HORNET V3_20260914_164152_...` | full `dump all`, pre-fix |
| `BTFL_cli_GREEN_HORNET V3_20260914_174345_...` | after the rate fix |
| `BTFL_cli_GREEN_HORNET V3_20260914_181603_...` | after airmode off + deadbands |

Blackbox recordings in `blackbox/` (gitignored; decoded rows live in `flights.csv`, analysis in
`flight_notes.csv`):

| File | Internal logs | What it shows |
|---|---|---|
| `..._20260914_164112_...BBL` | 3, 4 | original flips, yaw I-term to −70 |
| `..._20260914_175012_...BBL` | 5 | after rate fix; yaw windup gone, still flipped (roll) |
| `..._20260914_181238_...BBL` | 6, 8, 10 | props-off, airmode off; yaw I-term runaway to −160 |
| `..._20260914_181910_...BBL` | 11 | props-off after deadbands; runaway fixed |
| `..._20260914_183332_...BBL` | 13 | props on; flipped; Motor 3 −14% under load |

Runtime CLI snapshot, 2026-09-14 20:49 UTC, bench, USB power, no battery:

```text
Betaflight / STM32F722 (F722) 2026.6.1 Aug  7 2026 (6dbc4218f)  MSP API: 1.48
MCU: STM32F722xx CLK=216MHz, Vref=3.28V, Core temp=56degC
DEVICES DETECTED: SPI=1, I2C=0 (0 errors)
GYRO: (1) MPU6000 enabled locked dma       ACC: MPU6000
FLASH: JEDEC ID=0x00ef4018 16M            FlashFS usedSize=358400
Arming disable flags: RXLOSS CLI MSP DSHOT_TELEM
CPU:25%, cycle time: 125, GYRO rate: 7987, RX rate: 0, System rate: 10
Total task load 24.8%
```

The flight controller is healthy: 24.8% task load at 7987 Hz gyro / 3990 Hz PID, largest non-serial
task 56 us (the 444 us `SERIAL` maximum is CLI traffic). `DSHOT_TELEM` appears only because the ESCs
are unpowered on USB — all four motors stream eRPM with a battery connected. Blackbox storage is a
16 MB W25Q128. No baro, mag or GPS on the I2C bus.

Note that stock BLHeli_S cannot produce bidirectional DShot telemetry, yet every log contains eRPM
on all four channels, so the 35A 4-in-1 must be running Bluejay or JESC. Which, and at what timing
and PWM frequency, is **not recorded anywhere in this repository** — there is no
`esc-configs/green-hornet/` export. Capture one.

## Current state

Applied and verified: rates `20/20/34` with srate `67/67/115`; `deadband = 2`; `yaw_deadband = 2`;
`feature AIRMODE` off.

Outstanding:

1. **Motor 3** — prop swap test, then replace the motor. Blocking.
2. Trim sticks to exactly 1500 so the deadband is a safety net rather than the fix.
3. Narrow `FLIP OVER AFTER CRASH` back to 1700–2100.
4. Restore the analog OSD.
5. Capture an ESC configuration export.
6. Consider `defaults` and a clean rebuild on 2026.6.1.

The quad stays `broken` in `hardware.csv` until it has actually flown.
