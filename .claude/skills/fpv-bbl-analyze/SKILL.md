---
name: fpv-bbl-analyze
description: Robust Betaflight Blackbox Log (.BBL/.BFL) analyzer. Use when the user requests troubleshooting of a flight log, wants to detect motor desyncs, examine takeoff failures/flips, inspect gyro alignment issues, or analyze pilot stick commands in relation to motor outputs.
---

# FPV BBL Analyze Skill

This skill provides deterministic automated parsing and control-loop diagnostics of Betaflight blackbox flight logs (.BBL / .BFL) to diagnose hardware faults, motor desyncs, and configuration anomalies.

## Workflow Decision Tree

When a user presents a blackbox flight log or reports flight stability issues (takeoff flips, flat yaw spins, mid-air desyncs):

1. **Locate & Copy Log:** Ensure the `.BBL` file is copied/moved into the `blackbox/` folder.
2. **Execute Summary Parse:** Run the bundled python analyzer `scripts/analyze_bbl.py` to identify:
   - Total flight sessions (internal logs) inside the file.
   - Durations, voltage sags, current spikes, and motor saturation levels.
   - Automated motor desync warnings (`MOTOR_DESYNC` markers).
3. **Conduct Deep Diagnostic:** If a runaway takeoff or flat yaw spin is suspected, isolate the exact frame of the takeoff or crash. Use a custom Python script to map physical gyro yaw/pitch/roll rates against the pilot's raw stick inputs (`rcCommand[...]`) and corresponding `motor[...]` outputs to confirm feedback polarity.

---

## Technical Procedures

### 1. Running the Automated BBL Analyzer

To automatically parse, skip empty ground-idle/test logs, and extract deep flight diagnostics:

```bash
# Analyze a specific BBL log
python3 .claude/skills/fpv-bbl-analyze/scripts/analyze_bbl.py path/to/log.BBL

# Analyze the newest BBL log in current folder or blackbox/ directory
python3 .claude/skills/fpv-bbl-analyze/scripts/analyze_bbl.py
```

### 2. Interpreting the Output

* **Duration:** Flights under 3 seconds are usually failed takeoffs or disarms.
* **Peak Throttle:** High peak throttle (2000) with low duration confirms an immediate takeoff flight-path or runaway takeoff.
* **Gyro Yaw Range:** High values (e.g. >500 deg/s) without corresponding pilot stick inputs confirm a positive feedback loop (incorrect `align_board_yaw` or swapped motor pins).
* **Desync Summary:** If `Desync Total Frames >= 20` and flagged for specific motors (e.g. `bad_motors=[3]`), there is an active ESC desync or phase joint failure on that corner under current/load.
* **Control Loop Clean:** Indicates the quad is flying stably with correct gyro response and motor feedback.

---

## Reference Patterns: runaway yaw & flips

| Symptom | PID Loop Pattern | Likely Root Cause |
| :--- | :--- | :--- |
| **Takeoff flat yaw spin** | Gyro Yaw shoots up while sticks are centered, and FC drives opposing motor pairs (m0/m3 or m1/m2) to full saturation. | Mismatch on `yaw_motors_reversed` (Props Out setting vs physical Props In rotation). |
| **Takeoff cross-axis flip** | Pitch/Roll gyro rate diverges on centered sticks; motors on opposite rails (m0 to max, m1 to min) with no effect. | Mismatch on `align_board_yaw` (often default `0` vs required `45` or `315` for rotated AIO boards). |
| **Mid-air drift/uncommanded roll** | Motor on the failing corner goes to 100% saturation, while physical eRPM/thrust remains low or collapses. | ESC desync, slipping propeller hub, or degraded motor windings under load. |
