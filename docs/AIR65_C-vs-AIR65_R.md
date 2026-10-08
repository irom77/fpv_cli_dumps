# AIR65 C vs AIR65 R

Comparison of the fleet's AIR65 II Champion (`AIR65 C`) and Air65 Racing (`AIR65 R`). Hardware details come from `hardware.csv`; flight settings come from each quad's latest CLI dump as of 2026-10-08.

## Quick comparison

| | AIR65 C | AIR65 R |
|---|---|---|
| Product | Air65 II Champion edition | Air65 Racing version |
| Cell / wheelbase | 1S / 65 mm | 1S / 65 mm |
| Recorded weight | 16.6 g | 17.3 g |
| Flight controller | Matrix 1S 5IN1 II, built-in 12 A ESC | Air 5-in-1, built-in ESC |
| Betaflight target | `BETAFPVG473_V2` | `BETAFPVG473` |
| Betaflight build | BETAFPV 2026.6.0-alpha, build `e92c10887` | 4.5.0 |
| Gyro | BMI270, confirmed by runtime snapshot | ICM42688, per BETAFPV Air65 Racing firmware record |
| Motors | Champion 0702, 36,000 KV, dual ball bearing | 0702 SE II, 27,000 KV |
| Props | Gemfan GF 1207, 3 blade | Gemfan 1219S, 3 blade |
| Camera / video | C03 / onboard 5.8 GHz VTX, 25–400 mW | C03 / onboard 5.8 GHz VTX, 25–400 mW |
| Receiver | BETAFPV onboard serial ELRS 2.4 GHz; firmware 3.5.6 (`ee188b`), ISM2G4 | Onboard ELRS 2.4 GHz; receiver firmware revision not recorded |

The AIR65 C is 0.7 g lighter in the fleet records, about 4% relative to the AIR65 R. Its motors have a 33% higher KV rating. Those figures indicate different propulsion setups; KV alone does not establish a real-world speed or thrust difference because the motors, props, and airframes differ.

BETAFPV lists the Air65 II Champion with 36,000 KV dual-ball-bearing motors, GF 1207 props, a 12 A Matrix 5IN1 II FC, and 16.6 g weight. Its Air65 Racing page lists 27,000 KV racing motors and GF 1219S props. [Air65 II product specs](https://betafpv.com/products/air65-ii-brushless-whoop-quadcopter), [Air65 product specs](https://betafpv.com/products/air65-brushless-whoop-quadcopter), [Air65 Racing firmware and CLI](https://support.betafpv.com/hc/en-us/articles/32980449219865-CLI-and-Firmware-for-Air65-Racing).

## Current flight setup

| Setting | AIR65 C | AIR65 R |
|---|---|---|
| Receiver protocol | CRSF (serial ELRS) | CRSF (serial ELRS) |
| Motor protocol / bidirectional DShot | DSHOT300 / ON | DSHOT300 / ON |
| Rates type | ACTUAL | BETAFLIGHT |
| Center sensitivity, roll/pitch/yaw | 70 / 70 / 70 deg/s | 200 / 200 / 200 deg/s |
| Maximum rate, roll/pitch/yaw | 580 / 580 / 500 deg/s | 667 / 667 / 667 deg/s |
| Expo, roll/pitch/yaw | 0 / 0 / 0 | 0 / 0 / 0 |
| Crash Recovery | ON in all four PID profiles | ON in profiles 0–1; OFF in profiles 2–3 |
| Air Mode | ON via AUX mode; permanent `feature AIRMODE` disabled | ON via AUX mode |
| Modes | Same assignments and AUX ranges | Same assignments and AUX ranges |

Both quads use ARM on AUX1 low (900–1300), ANGLE on AUX2 high (1700–2100), Flip Over After Crash on AUX2 middle (1300–1700), Air Mode on AUX2 low (900–1300), Beeper on AUX3 from 1300–2100, and VTX Pit Mode on AUX4 from 1300–2100. AIR65 C's current dump has `feature -AIRMODE`, so the AUX2 range controls Air Mode rather than it being permanently active.

Both have Crash Recovery enabled in their active PID profile, with the same recorded settings: D threshold 50, gyro threshold 400, setpoint threshold 350, time 500 ms, delay 0 ms, recovery angle 10 degrees, recovery rate 100, and yaw limit 200. AIR65 C has it enabled across all four PID profiles; AIR65 R has it enabled only in profiles 0 and 1.

The AIR65 C's current rates are softer around center and lower at maximum than the AIR65 R's. This is a Betaflight profile comparison, not a measured flight-performance result. Rate values are decoded from each latest dump into degrees per second.

## Practical differences

- **AIR65 C:** newer Matrix II electronics, the lighter Champion frame, higher-KV dual-ball-bearing motors, and the vendor's newer Betaflight build. BETAFPV says compatible firmware is needed for some IMU variants; retain firmware matched to the installed BMI270 and `BETAFPVG473_V2` target.
- **AIR65 R:** earlier Air 5-in-1 electronics, lower-KV SE II motors, and Betaflight 4.5.0 on `BETAFPVG473`.
- **Video channel:** AIR65 C's latest dump records 5658 MHz; AIR65 R's records 5917 MHz. Check the goggles/VTX table before flying with a shared video setup.
- **Core flight behavior:** mode assignments and Crash Recovery are aligned. The main recorded tuning difference is the rate profile.

The two targets and firmware builds differ, so do not cross-flash firmware or blindly restore one quad's full CLI dump onto the other.

## Source records

- AIR65 C: `backups/BTFL_cli_AIR65_C_20261008_101553_BETAFPVG473_V2.txt`; hardware and runtime notes in `hardware.csv`.
- AIR65 R: `backups/BTFL_cli_AIR65_R_20260929_153410_BETAFPVG473.txt`; hardware details in `hardware.csv`.
- Generated fleet views: `fpv_quads_latest.csv`, `rates.csv`, `modes.csv`, and `racing_whoops.csv`.
