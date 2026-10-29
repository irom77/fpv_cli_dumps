# Race-whoop throttle curve (fresh-pack "low-battery feel")

Source: RaceGOW Discord discussion, tuning concept popularized by Michael Chen (DaBits).
Saved 2026-10-28. The ready-to-paste CLI block is in
[`CLI_SNIPPETS.md` → Throttle curve](../CLI_SNIPPETS.md#race-whoop-throttle-curve--rate-profile-3).

## Overview

Micro whoops often feel easier and smoother when the battery is low. A fresh HV pack (4.35V/cell)
makes the throttle twitchy and sensitive, causing bobbing and ground taps, while a sagging pack
(about 3.6V/cell) gives much finer throttle resolution and control.

To get that locked-in, low-battery feel from a fresh pack, pilots use Betaflight's Throttle Limit,
Throttle MID, Hover Point and Throttle EXPO. Together they flatten the response curve around the
hover point and spread out stick resolution.

## Steps

1. **Throttle ceiling (Throttle Limit)**: PID Tuning tab → Rateprofile settings.
   - Throttle Limit Type: `SCALE`
   - Throttle Limit %: `70` (70–80 depending on KV and preference)
   - Why: cuts top-end power rarely used indoors, compressing the usable thrust range so small
     stick movements don't launch the whoop.
2. **Curve shape**
   - Throttle MID: `0.35`
   - Hover Point: `0.40`: match it to the stick position where the whoop actually hovers
   - Throttle EXPO: `0.80`
   - Why: the curve flattens through the mid-stick range, giving more stick travel where you
     clear gates and hold altitude without bouncing.
3. **Motor idle / dynamic idle**: keep a reliable idle floor (e.g. ~2% motor idle) so
   chopping throttle drops cleanly to the floor without hanging or a deadband at the bottom.
4. **Test fly**: plug in a fresh 4.35V HV pack. It should feel less twitchy off the line, like
   a half-drained pack, while still responding crisply when needed.

## Fleet notes

- CLI values are integers in percent: MID `0.35` → `thr_mid = 35`, EXPO `0.80` → `thr_expo = 80`,
  Hover `0.40` → `thr_hover = 40`.
- `thr_hover` (Hover Point) exists only on Betaflight 2025.12+ (AIR65 C runs 2026.6.0-alpha).
  On the 4.4/4.5 whoops (RACE33, Mob6, AIR65 R, Diamond, Ecofree, Happish, Mobula1) that line
  returns `Invalid name`; skip it.
- All of these settings are per rateprofile, so putting them in rate profile 3 keeps the normal
  profile untouched and lets you A/B them with a rate-profile switch. A fresh rate profile has default
  rates (670°/s ACTUAL), though. Copy your rates into it first (see the snippet).
- Motor idle is global, not per rateprofile, so the snippet leaves it alone. The fleet currently runs
  higher than 2% (e.g. AIR65 C `motor_idle = 550` = 5.5%). Change it separately if needed.
- AIR65 C rateprofile 0 already carries a hover-centred curve (`thr_mid 28`, `thr_expo 35`,
  `thr_hover 22`), which suggests its real hover is near 22% stick. Check where your quad
  actually hovers before trusting `thr_hover = 40`.

## Related: Betaflight battery sag compensation (PR #9561)

Source: [betaflight/betaflight#9561](https://github.com/betaflight/betaflight/pull/9561)
"Battery sag compensation by varying motor output", by ctzsnooze, merged for **4.2** (2020).
It fixes the same problem in firmware: it cuts motor output on a full pack and gives it back as the
voltage sags, so a fresh pack flies like a drained one. Throttle and PID authority both stay the
same through the flight.

How it works (from the PR code):

- Setting: `vbat_sag_compensation` (0–150, default 0), **per PID profile** (`profile N`), not
  per rateprofile. Start at `100`. Filter: `vbat_sag_lpf_period` (default `2` = fast, ~33 ms; it
  also catches throttle-blip sags; `200` follows only the slow discharge).
- It needs the FC's on-board ADC voltage sensor (`battery_meter = ADC`). Every race whoop in the
  fleet has one, so all of them can use it. ESC-telemetry voltage is too slow, and firmware
  forces the setting to 0 in that case.
- It compensates between a hard-coded **4.20 V** "full" and `vbat_warning_cell_voltage`. Full-pack
  motor reduction = `(4.20 − warning) / 4.20 × compensation%`. **HV 4.35 V packs get no extra
  reduction above 4.20 V**: the cut is capped at the 4.20 V amount.
- It stacks on top of any throttle/motor limit and never boosts above it. Debug: `debug_mode =
  BATTERY`; debug[2] = battery goodness 0–100, debug[3] = reduction ×10 (e.g. 160 = 16%).
- **Warning from the PR:** once it works you can't *feel* the pack going flat. Rely on the
  OSD voltage / warnings.

Fleet values (latest dumps, all `battery_meter = ADC`):

| Quad | warning V | full-pack cut @100 | active PID profile | sag comp now |
|------|-----------|--------------------|--------------------|--------------|
| AIR65 C | 3.45 | 17.9% | 3 | 0 |
| AIR65 R | 3.30 | 21.4% | 1 | 0 |
| Diamond | 3.30 | 21.4% | 0 | 0 |
| Ecofree | 3.50 | 16.7% | 0 | **100** |
| Happish | 3.20 | 23.8% | 2 | 0 |
| Mob6 AIO5 2nd | 3.30 | 21.4% | 0 | 0 |
| Mobula1 | 3.30 | 21.4% | 2 | 0 |
| RACE33 | 3.20 | 23.8% | 0 | 0 |

With a warning voltage of 3.2–3.3 V the range is wide, so the PR suggests ~80% if 100 feels dull.

### Combining it with the throttle curve

The two approaches do different things. Sag compensation is dynamic and equalizes the whole
flight. The throttle limit is static and simply caps power for the whole flight. Run both at full
strength and a fresh pack is cut twice. Example on a 3.30 V-warning whoop:
`0.70 × (1 − 0.214) ≈ 55%` of full motor output at full stick, and the end of the pack is still
capped at 70%.

Suggested order:

1. Enable `vbat_sag_compensation = 100` in the active PID profile alone and fly a fresh pack.
   This alone may give you the "half-drained" feel.
2. Then add the rate-profile-3 curve for hover resolution (`thr_mid` / `thr_expo` /
   `thr_hover`), with the throttle limit raised to about 80–90% (or OFF) instead of 70%.
3. Re-measure the hover stick position after step 1. Lowering motor output moves the hover point
   up, so set `thr_hover` last.
