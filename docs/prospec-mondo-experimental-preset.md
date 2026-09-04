# ProSpec Mondo Experimental Preset Trial

Status: proposed; not yet applied or flight-tested.

## Objective

Evaluate Armando Gallegos (Mondo)'s Betaflight preset, **Experimental Presets for MultiGP PRO
Spec 7\"**, on the ProSpec 7-inch racer. The goal is to compare its tune and filtering with the
current KAACK V19 configuration while retaining a reliable rollback path.

## Current baseline

- Craft: `prospec`, MultiGP Pro Spec 7-inch, 6S, 1300 KV
- Flight controller: `HOBBYWING_XROTORF7CONV`
- Firmware: Betaflight `4.5.3.KAACK_V19`
- RPM limiter: enabled at 13,000 RPM
- Motor protocol: DSHOT600 with bidirectional DShot
- Motor direction: reversed
- Rates: BETAFLIGHT `95/80/80` RC rate and `70/70/70` super rate
- Rollback dump: `backups/BTFL_cli_backup_PROSPEC_20260902_111305_HOBBYWING_XROTORF7CONV.txt`

The current rates decode to approximately 633 deg/s roll and 533 deg/s pitch/yaw. The proposed
preset does not set rates, so they should remain unchanged, but they must be verified after applying
it.

## Compatibility assessment

The preset's principal hardware assumptions match ProSpec: 1300 KV motors, a 13,000 RPM limiter,
DSHOT600, bidirectional DShot, reversed motor direction, RPM filtering, OSD, and an LED strip.

The preset is a substantial tune and filter change, not merely a Pro Spec RPM-limiter setup. Notable
settings include:

- simplified master multiplier 160
- simplified D gain 150 and pitch D gain 110
- simplified D-Max gain 0
- simplified gyro-filter multiplier 60
- simplified D-term-filter multiplier 120
- thrust linearization 20
- two dynamic notches with a 550 Hz maximum
- RPM filter weights `100,50,100`
- PID sum limits increased to 1000

Because the preset is marked experimental, improved flight behavior is not assumed. Motor heat,
oscillation, propwash response, and blackbox traces will determine whether it is suitable for this
particular frame, motors, props, and weight.

## Known caveat

The preset sets `acc_hardware = NONE`. ProSpec currently has Angle mode assigned to AUX2, so Angle
mode will no longer function if the accelerometer remains disabled. Before flying, either restore the
correct accelerometer setting or deliberately remove/accept the unavailable Angle mode. Do not assume
the mode switch provides self-leveling after applying the preset.

The preset also sets `baro_hardware = NONE`; no current ProSpec requirement for a barometer is known.

## Proposed procedure

1. Confirm in the Presets tab that this exact preset supports Betaflight 4.5.x and read its current
   description, options, warnings, and linked discussion.
2. Remove all propellers.
3. Retain the rollback dump above and make an additional same-day `diff all` immediately before the
   change if any configuration has changed since 2026-09-02.
4. Apply the preset through the Betaflight Presets tab, selecting only the option intended for this
   1300 KV Pro Spec build, then save and reconnect.
5. Save a new post-preset `diff all` before making corrective edits.
6. Address `acc_hardware = NONE` according to whether Angle mode is required.
7. Verify receiver inputs, failsafe, arming, modes, motor order, motor direction, DShot telemetry,
   RPM filtering, OSD, LED operation, rates, motor poles/KV, and the 13,000 RPM limit.
8. With props still removed, run each motor slowly and confirm clean RPM telemetry without errors.
9. Fit known-good props and perform a 20-30 second low hover. Land and check all motor temperatures
   individually.
10. Perform a gentle line-of-sight flight with no extended full-throttle operation. Stop for hot
    motors, audible oscillation, visible twitching, poor propwash recovery, or unexpected mode
    behavior.
11. If the initial checks pass, make a short representative race flight with blackbox logging.
12. Compare gyro noise, D-term activity, PID error, motor outputs/saturation, RPM traces, propwash
    recovery, and motor temperatures with a comparable baseline flight.

## Acceptance criteria

Adopt the preset only if:

- all safety and configuration checks pass;
- the 13,000 RPM limiter operates as expected;
- motors remain comfortably within their normal temperature range;
- logs show no sustained high-frequency oscillation or problematic motor saturation; and
- handling is measurably or subjectively better without reducing reliability.

Otherwise restore the 2026-09-02 dump, recheck the complete configuration with props removed, and
record the reason for rejecting the preset.

## Results

Not yet tested. Record the post-preset dump, prop choice, battery, ambient temperature, motor
temperatures, blackbox log filenames, pilot observations, and final keep/revert decision here.
