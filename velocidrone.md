# VelociDrone race setup

This is a practical VelociDrone baseline for matching the active 5-inch racing quads in this
repository. The rates and PID values come from the newest Betaflight CLI dumps; physical setup
comes from `hardware.csv`.

VelociDrone's Betaflight controller is based on Betaflight 4.2, while these quads use newer
Betaflight or KAACK builds. The settings below provide a close training setup, but they cannot
reproduce the real flight controller exactly. Match rates, propeller, power, camera angle and FOV
first; those normally make a larger perceptual difference than small PID changes.

## Recommended models

| Real quad | VelociDrone model | Notes |
|---|---|---|
| `openracer` | Open Racer | Closest frame match |
| `openracer2` | Open Racer or Switchback Zero | Switchback Zero is the included Freedom Spec model |
| `LS-Ultra` / `LS-Ultra HD` | Five33 Light Switch | Closest Five33 frame match |
| General Freedom Spec practice | Switchback Zero | Use when the simulated race class matters more than matching one airframe |

Use the Betaflight flight controller and Rate mode. Leave the model's stock VelociDrone PIDs in
place until the rates and physical settings have been matched.

## Shared house-race rates

These settings match `openracer`, `openracer2` and `LS-Ultra HD`.

| Axis | RC Rate | Super Rate (`RATE`) | RC Expo | Maximum velocity |
|---|---:|---:|---:|---:|
| Roll | 0.95 | 0.70 | 0.00 | 633 deg/s |
| Pitch | 0.80 | 0.70 | 0.00 | 533 deg/s |
| Yaw | 0.80 | 0.70 | 0.00 | 533 deg/s |

Additional shared settings:

| Setting | Value |
|---|---:|
| Rate type | Betaflight |
| Feedforward transition | 0.00 |
| Throttle midpoint | 0.50 |
| Throttle expo | 0.00 |
| Air mode | On |
| Battery emulation | On |
| Camera mix angle | 0 degrees |
| Camera FOV | 115-120 degrees, then adjust to match the goggles |

`LS-Ultra` is slightly different: its roll RC Rate is `0.93`, producing a maximum roll velocity of
approximately 620 deg/s. Pitch and yaw remain at 533 deg/s.

## OpenRacer profile

The following PID values are explicitly recorded in the newest `openracer` dump:

| Axis | Proportional | Integral | D Max | D Min | Feedforward |
|---|---:|---:|---:|---:|---:|
| Roll | 38 | 81 | 35 | 21 | 125 |
| Pitch | 41 | 89 | 40 | 23 | 137 |
| Yaw | VelociDrone default | VelociDrone default | - | - | VelociDrone default |

| Setting | Value |
|---|---:|
| TPA | 0.70 |
| TPA breakpoint | 1250 |
| Power/throttle limit | 80% |
| Propeller | 5146 (closest option to Hurricane MCK 51466 V2) |
| Propeller profile | 2 (realistic) |

The real quad uses `motor_output_limit = 80`. VelociDrone's 80% throttle/power limit is an
approximation: the two implementations are not necessarily identical, but it is much closer than
running the simulated quad at full power.

## Lightswitch Ultra profile

Use these explicitly recorded values for `LS-Ultra` and `LS-Ultra HD`:

| Axis | Proportional | Integral | D Max | D Min | Feedforward |
|---|---:|---:|---:|---:|---:|
| Roll | 30 | 65 | 28 | 16 | 100 |
| Pitch | 33 | 71 | 32 | 19 | 110 |
| Yaw | VelociDrone default | VelociDrone default | - | - | VelociDrone default |

| Setting | Value |
|---|---:|
| TPA | 0.70 |
| TPA breakpoint | 1250 |
| Propeller for `LS-Ultra` | 5128 (Gemfan Fury 5128) |
| Propeller profile | 2 (realistic) |
| Power/throttle limit for `LS-Ultra` | 80% |

The repository does not yet record the props, cells or weight for `LS-Ultra HD`; use the confirmed
`LS-Ultra` values as a starting point, then verify the HD build on the bench.

## Settings that require calibration

VelociDrone represents quad weight as a percentage of the selected model's default rather than in
grams. The recorded dry weights therefore cannot be entered directly:

| Quad | Recorded dry weight |
|---|---:|
| `openracer` | 305 g |
| `openracer2` | 280 g without props or battery |
| `LS-Ultra` | 270 g |

Fit the same class of simulated battery, start at the model's default weight, and adjust the weight
slider until hover throttle, momentum through turns, and recovery after dives resemble the real
quad. Do not use weight to compensate for an incorrect propeller or power limit.

Camera angle is not available in a Betaflight CLI dump. Measure the real mount or copy the angle
already used in the goggles, then enter that value in VelociDrone. If it is unknown, 45 degrees is
a reasonable racing starting point.

Leave drag, downforce and anti-gravity at the selected model's defaults initially. Change only one
setting at a time and compare hover throttle, full-throttle acceleration, throttle-off dive,
corner carry and prop-wash recovery against the real quad.

## Source files

- `backups/BTFL_cli_backup_OPENRACER_20260811_164314_HOBBYWING_XROTORF7CONV.txt`
- `backups/BTFL_cli_OPENRACER2_20260811_143646_FOXEERF722V4.txt`
- `backups/BTFL_cli_backup_LS-ULTRA_20260721_092829_TMOTORF7.txt`
- `backups/BTFL_cli_backup_LS-ULTRA_HD_20260721_093236_HDZERO_HALO.txt`
- `rates.csv`
- `hardware.csv`

