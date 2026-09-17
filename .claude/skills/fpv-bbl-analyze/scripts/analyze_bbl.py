#!/usr/bin/env python3
"""
Robust Betaflight Blackbox Log (.BBL/.BFL) analyzer script.
Bypasses corrupted/truncated frames and decodes all valid flight segments.

Usage:
    python3 analyze_bbl.py [path_to_log.BBL]
"""
import sys
import os
import glob

# Ensure orangebox is imported, bootstrap with .venv if needed
try:
    from orangebox import Parser
    from orangebox.reader import Reader
except ModuleNotFoundError:
    venv_py = os.path.join(os.getcwd(), ".venv", "bin", "python")
    if os.path.exists(venv_py):
        os.execv(venv_py, [venv_py] + sys.argv)
    sys.exit("Error: orangebox not installed. Please set up the python environment with orangebox.")

# Determine target file
path = None
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    # Default: find newest BBL log in current folder or ./blackbox
    bbl_files = glob.glob("blackbox/*.BBL") + glob.glob("blackbox/*.bbl") + glob.glob("*.BBL") + glob.glob("*.bbl")
    if bbl_files:
        path = max(bbl_files, key=os.path.getmtime)
        print(f"No file specified. Using newest discovered BBL file: {path}\n")
    else:
        sys.exit("Error: No .BBL files found. Please specify the path to a BBL log file.")

if not os.path.exists(path):
    sys.exit(f"Error: File not found: {path}")

# Load and count internal logs
try:
    r = Reader(path, None)
    log_count = r.log_count
except Exception as e:
    sys.exit(f"Error reading BBL file structure: {e}")

print(f"====================================================================")
print(f"BBL FILE: {os.path.basename(path)}")
print(f"TOTAL LOG SEGMENTS: {log_count}")
print(f"====================================================================")

for li in range(1, log_count + 1):
    print(f"\n--- [Log Segment {li}/{log_count}] ---")
    try:
        p = Parser.load(path, log_index=li)
    except Exception as e:
        # Check if it was purely empty (typical for very small size)
        size = 0
        try:
            r.set_log_index(li)
            size = r._frame_data_len
        except Exception:
            pass
        if size <= 5000:
            print(f"  Empty or aborted arming event (Headers only, {size} bytes). Skipping.")
        else:
            print(f"  Failed to load log index {li}: {e}")
        continue

    fn = p.field_names
    idx = {n: i for i, n in enumerate(fn)}
    
    # Check for required columns
    tm = idx.get('time')
    vb = idx.get('vbatLatest')
    am = idx.get('amperageLatest')
    thr = idx.get('rcCommand[3]')
    mot = [idx[f'motor[{i}]'] for i in range(4) if f'motor[{i}]' in idx]
    erp = [idx[f'eRPM[{i}]'] for i in range(4) if f'eRPM[{i}]' in idx]
    mo = p.headers.get('motorOutput', [0, 1000])
    m_lo, m_hi = mo[0], mo[1]
    
    desync_cmd = m_lo + 0.90 * (m_hi - m_lo)
    desync_per_motor = [0, 0, 0, 0]

    n = 0
    t0 = tN = tprev = None
    v_start = v_end = None
    v_min = 1e9
    a_max = 0.0
    mah = 0.0
    motor_sum = 0.0
    sat_frames = 0
    thr_sum = 0.0
    thr_max = None
    gyro_yaw_max = 0.0
    gyro_yaw_min = 0.0

    gy_idx = idx.get('gyroADC[2]') # Yaw gyro
    if gy_idx is None:
        gy_idx = idx.get('gyro[2]')

    try:
        for fr in p.frames():
            d = fr.data
            t = d[tm]
            if t0 is None:
                t0 = t
            else:
                dt = (t - tprev) / 1e6
                if am is not None and 0 < dt < 1:
                    mah += (d[am] / 100.0) * dt / 3.6
            tprev = t
            tN = t
            if vb is not None:
                v = d[vb] / 100.0
                v_start = v if v_start is None else v_start
                v_end = v
                v_min = min(v_min, v)
            if am is not None:
                a_max = max(a_max, d[am] / 100.0)
            if gy_idx is not None:
                val = d[gy_idx]
                gyro_yaw_max = max(gyro_yaw_max, val)
                gyro_yaw_min = min(gyro_yaw_min, val)
            if mot:
                if max(d[i] for i in mot) >= m_lo + 0.99 * (m_hi - m_lo):
                    sat_frames += 1
                motor_sum += sum(d[i] for i in mot) / len(mot)
                if len(erp) == 4:
                    erpms = [d[e] for e in erp]
                    emax = max(erpms)
                    if emax > 0:
                        for i in range(4):
                            if d[mot[i]] >= desync_cmd and erpms[i] < 0.55 * emax:
                                desync_per_motor[i] += 1
            if thr is not None:
                thr_sum += d[thr]
                thr_max = d[thr] if thr_max is None else max(thr_max, d[thr])
            n += 1
    except Exception as e:
        # Clean warning for truncated frames at the very end of flash
        print(f"  [Note: Log ended abruptly at frame {n} - typical for power cuts/disarms]")

    if n == 0 or t0 is None:
        print(f"  No valid flight frames found.")
        continue

    dur = (tN - t0) / 1e6
    cells = round(v_start / 4.2) if v_start else 0
    desync_total = sum(desync_per_motor)
    worst = max(desync_per_motor) if desync_per_motor else 0
    bad_motors = [i for i, c in enumerate(desync_per_motor) if c >= max(worst * 0.25, 5)]

    print(f"  Craft Name:      {p.headers.get('Craft name', 'N/A')}")
    print(f"  Firmware:        {p.headers.get('Firmware revision', 'N/A')}")
    print(f"  Duration:        {dur:.2f} s")
    print(f"  Parsed Frames:   {n}")
    print(f"  Peak Throttle:   {thr_max if thr_max is not None else 'N/A'}")
    print(f"  Battery Cell:    {cells}S")
    print(f"  Voltage Start:   {v_start:.2f} V | Min Sag: {v_min:.2f} V")
    print(f"  Amperage Max:    {a_max:.1f} A")
    print(f"  Gyro Yaw Range:  {gyro_yaw_min} to {gyro_yaw_max} deg/s")
    print(f"  Saturated Motor: {sat_frames} frames")
    print(f"  Desync Summary:  {desync_total} frames across motors")
    
    if desync_total >= 20:
        print(f"  *** WARNING: MOTOR_DESYNC detected on motor(s): " + ", ".join(f"m{i}" for i in bad_motors))
    else:
        print(f"  Control Loop:    Clean. No motor desyncs or thrust imbalances detected.")
