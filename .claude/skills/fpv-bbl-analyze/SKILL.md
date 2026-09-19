---
name: fpv-bbl-analyze
description: Analyze Betaflight Blackbox logs for takeoff failures, unexpected disarms, uncontrolled motion, and suspected motor faults.
---

# FPV Blackbox analysis

## Workflow

1. Copy the requested raw log into `blackbox/` and verify byte equality. Raw logs remain gitignored. Preserve every internal section, including brief failed takeoffs.
2. Run `python3 .claude/skills/fpv-bbl-analyze/scripts/analyze_bbl.py path/to/log.BBL`. It uses the repository `.venv` when orangebox is unavailable in the current interpreter.
3. Inspect decoded events (`Parser.events` after consuming `Parser.frames()`), especially DISARM and LOG_END. Verify numeric disarm reasons against the logged firmware's `src/main/fc/core.h`. A parser error or missing end event establishes incomplete evidence, not a power failure.
4. For the failure window, compare timestamped pilot commands/setpoints, gyro rates, PID terms, motor commands, voltage, and receiver/failsafe fields. Record log index and time relative to its first decoded frame. Check frame continuity before relying on individual spikes.
5. Rank physical/configuration explanations and give a bench check that distinguishes them. Save evidence, uncertainty, and the next check under `docs/troubleshooting/`. A logged protection event explains the shutdown; identifying the triggering hardware/configuration fault may require pilot observations.

## Interpretation limits

- Motor outputs are commands, not measured RPM or thrust. Without all four RPM telemetry fields, desync detection is unavailable. A zero heuristic count cannot establish a clean control loop.
- Even with RPM telemetry, high command/low relative RPM is a suspicion: intentional mixer differences and telemetry errors can produce the same pattern. Corroborate the timing, motion, and electrical/mechanical evidence.
- Large uncommanded yaw plus escalating diagonal motor commands suggests incorrect yaw feedback. Check actual rotation against `yaw_motors_reversed`, then motor order and gyro orientation. The log alone does not prove which setting is wrong.
- Roll/pitch divergence can arise from motor order, FC orientation, prop installation, or loss of thrust. Verify actual geometry instead of guessing an alignment angle.
- Short duration, high throttle, saturation, or battery sag alone does not establish a runaway, desync, weak battery, or brownout. Compare what happened first and inspect the disarm reason.
- State sensor calibration limitations for voltage/current. Deriving cell count from starting voltage is an estimate.
- Keep runaway protection enabled. Verify motor order/rotation with props removed, and compare the Setup model to physical movement before recommending another takeoff. Do not blindly toggle direction settings or change PIDs to suppress a protection event.

## Regression check

` .venv/bin/python -m unittest discover -s tests -p 'test_cine_fish_bbl_analysis.py' ` verifies both runaway disarms and the missing-RPM caveat using the local Cine-fish crash log. It skips if the gitignored log is absent.
