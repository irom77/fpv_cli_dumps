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
