# TTV2 vs Mass: 3-inch racing comparison

This compares the saved racing setups for TTV2 and Mass. Hardware comes from [`hardware.csv`](../hardware.csv); flight-controller settings come from the latest available CLI dumps listed below. The rate values are decoded by the fleet's [Betaflight rate calculator](../.agents/skills/fpv-fleet-update/scripts/rates.py). They are commanded rates, not measured flight performance.

## At a glance

| | TTV2 | Mass |
|---|---|---|
| Recorded class / cells | 3-inch / 3S or 4S | 3-inch / 3–4S, 850 mAh 4S noted |
| Frame/build | Five33 Tiny Trainer V2 HDZero RTF | Massive Droner 3-inch |
| Flight controller | HAKRC F411 AIO (`HAKRCF411D`) | SpeedyBee F405 Mini 20×20 (`SPEEDYBEEF405MINI`) |
| Motors | VCI 1605 2800KV | Five33 TinyTurners 1404 4533KV (TinyTrainer) |
| Props | HQProp T3.5×2.5×3, 1.5 mm hub | 3-inch; exact model not recorded |
| Firmware in compared dump | Betaflight 4.5.1 | Betaflight 2026.6.2 |
| Active PID / rate profile | 0 / 0 | 0 / 0 |
| Recorded weight | Not recorded | Not recorded |

## Motors and propulsion

Mass's 1404 motor has a smaller stator than TTV2's 1605, but its KV is about **62% higher** (4533 vs 2800). KV describes approximate unloaded RPM per volt; it does not by itself predict thrust, acceleration, efficiency, or lap time. Stator design, propeller, battery voltage and sag, build weight, and motor temperature all affect the result.

Five33 lists its TinyTurners as 1404 4533KV TinyTrainer motors and identifies them as manufactured by Xnova. The TinyTrainer spec page calls for 3S. Mass's hardware record currently notes a 4S 850 mAh pack, so confirm the installed pack and prop/motor combination against the manufacturer's guidance before treating the two setups as directly comparable. [Five33 TinyTurners product listing](https://five33.flywheelsites.com/product/tinyturners-1404-4533kv-tinytrainer-motor/), [Five33 TinyTrainer series/spec](https://five33.flywheelsites.com/tinytrainer-series/).

TTV2's recorded prop is 3.5-inch while Mass is recorded as 3-inch. This difference alone can materially change load and thrust. The Mass prop model and exact TTV2 battery used for racing are not recorded here.

## Rates and active PID tune

| Setting | TTV2 | Mass |
|---|---:|---:|
| Rates type | BETAFLIGHT | ACTUAL |
| Center sensitivity, roll / pitch / yaw | 190 / 160 / 160°/s | 70 / 70 / 70°/s |
| Rate at 25% stick, roll / pitch / yaw | 58 / 48 / 48°/s | 55 / 55 / 55°/s |
| Rate at 50% stick | 146 / 123 / 123°/s | 185 / 185 / 185°/s |
| Rate at 75% stick | 300 / 253 / 253°/s | 390 / 390 / 390°/s |
| Maximum rate | 633 / 533 / 533°/s | 670 / 670 / 670°/s |
| Expo, roll / pitch / yaw | 0 / 0 / 0 | 0 / 0 / 0 |
| Roll P-I-D-F | 40-82-49-132 | 45-80-30-120 |
| Pitch P-I-D-F | 42-86-53-137 | 47-84-34-125 |
| Yaw P-I-D-F | 45-80-0-120 | 45-80-0-120 |
| TPA rate / breakpoint | 70 / 1250 | 65 / 1350 |

The rate curves use different calculation systems, so the raw rate numbers are not directly comparable. In this decoded comparison, TTV2 is more responsive around center, especially on roll; Mass has higher commanded rates through mid and high stick, and slightly higher roll maximum. Mass has lower roll and pitch D and feedforward values; whether that is preferable depends on frame resonance, motor temperature, propwash, and flight logs.

## Filters and loop settings

| Setting | TTV2 | Mass |
|---|---:|---:|
| PID process denominator | 2 | 1 |
| Dynamic gyro LPF1 | 500–1000 Hz | 250–500 Hz |
| Gyro LPF2 static | 600 Hz | 500 Hz |
| Simplified gyro filter | Off | On (multiplier 100) |
| Dynamic idle minimum RPM | 60 in active profile 0 | 0 |
| Airmode | On | On |

These settings reflect distinct hardware, Betaflight versions, and saved tunes. They are not a recommendation to copy one quad's PID/filter block onto the other. Use blackbox traces and motor temperature after short, controlled flights to assess changes.

## How to read this comparison

- Both are curated as active 3-inch race quads, but their actual prop sizes differ in the inventory: 3.5-inch on TTV2 versus 3-inch on Mass.
- The comparison uses TTV2's latest available dump from 2026-09-21 and Mass's dump from 2026-10-19. It does not confirm that TTV2 still has those settings today.
- The Mass motor name is normalized to Five33's listed product name. “Headsupfpv” is the inspiration/association on the product listing, not the formal product name.
- Source dumps: [`TTV2 (2026-09-21)`](../backups/BTFL_cli_TTV2_20260921_153339_HAKRCF411D.txt) and [`Mass (2026-10-19)`](../backups/BTFL_cli_MASS_20261019_184104_SPEEDYBEEF405MINI.txt).
- The generated [3-inch race comparison CSV](../racing_3inch.csv) is the current data view; rerun the fleet updater after changing a dump or curated hardware detail.
