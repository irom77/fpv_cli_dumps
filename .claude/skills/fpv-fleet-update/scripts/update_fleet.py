#!/usr/bin/env python3
"""
Regenerate the FPV fleet inventory from Betaflight CLI dump files.

Scans every BTFL_cli_*.txt dump in the target folder and produces three outputs:
  - fpv_quads.csv         full history, one row per dump, newest per quad flagged 'latest'
  - fpv_quads_latest.csv  one row per quad, newest dump only
  - FLEET_SUMMARY.md      human-readable overview with rollups and a 'needs attention' pass

Usage:
    python update_fleet.py [folder]     # defaults to the current working directory

The parser is the single source of truth. It only reads dumps and writes those three
files, so it is safe to re-run any time new dumps are dropped in.
"""
import os, re, csv, sys, glob
from datetime import date, datetime

SRC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
OUT = os.path.join(SRC, "fpv_quads.csv")
OUT_LATEST = os.path.join(SRC, "fpv_quads_latest.csv")
OUT_SUMMARY = os.path.join(SRC, "FLEET_SUMMARY.md")

# Filename shapes handled:
#   BTFL_cli_backup_<LABEL>_<YYYYMMDD>_<HHMMSS>_<BOARD>.txt
#   BTFL_cli_<LABEL>_<YYYYMMDD>_<HHMMSS>_<BOARD>.txt
#   BTFL_cli_dif_all_<LABEL>_<YYYYMMDD>_<HHMMSS>_<BOARD>.txt
#   ...and the same without a <LABEL> (older unnamed backups).
fname_re = re.compile(
    r'^BTFL_cli_(?:backup_|dif_all_)?(?P<label>.*?)_?(?P<date>\d{8})_(?P<time>\d{6})_(?P<board>.+)\.txt$'
)


def val(text, key):
    m = re.search(r'^set\s+' + re.escape(key) + r'\s*=\s*(.+?)\s*$', text, re.M)
    return m.group(1).strip() if m else ""


def line_after(text, prefix):
    m = re.search(r'^' + re.escape(prefix) + r'\s+(.+?)\s*$', text, re.M)
    return m.group(1).strip() if m else ""


def norm(s):
    return re.sub(r'[^A-Za-z0-9]', '', s).upper()


def parse_dumps():
    rows = []
    # Recursive so dumps organized into subfolders (e.g. backups/) are still found.
    # Non-matching .txt files are skipped by fname_re below, so this is safe.
    for path in sorted(glob.glob(os.path.join(SRC, "**", "*.txt"), recursive=True)):
        base = os.path.basename(path)
        m = fname_re.match(base)
        if not m:
            continue
        label = m.group('label').strip() or ""
        d = m.group('date')
        date_fmt = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
        board_fname = m.group('board')

        with open(path, encoding='utf-8', errors='replace') as f:
            text = f.read()

        # A truncated/aborted dump (e.g. just "defaults nosave") carries no config.
        if len(text.strip()) < 40:
            rows.append({
                '_ident': norm(label) or norm(board_fname),
                'quad': label or board_fname, 'dump_date': date_fmt, 'craft_name': '',
                'board': board_fname, 'manufacturer': '', 'bf_version': '',
                'mcu': '', 'motor_protocol': '', 'motor_poles': '', 'dshot_bidir': '',
                'rx_protocol': '', 'video_system': '', 'vtx_band': '', 'vtx_channel': '',
                'vtx_power': '', 'vtx_freq': '', 'cell_min_v': '', 'cell_max_v': '',
                'cell_warn_v': '', 'rx_spi_protocol': '', 'elrs_uid': '', 'bind_group': '',
                'gyro_align': '', 'pilot': '', 'file': base, 'note': 'EMPTY/INCOMPLETE DUMP'
            })
            continue

        ver = re.search(r'# Betaflight / (\S+) \(\S+\) (\S+)', text)
        mcu = ver.group(1) if ver else ''
        bf_version = ver.group(2) if ver else ''

        board = line_after(text, 'board_name') or board_fname
        manuf = line_after(text, 'manufacturer_id')

        craft = val(text, 'craft_name')
        if not craft:
            nm = re.search(r'^# name:\s*(.+?)\s*$', text, re.M)
            craft = nm.group(1).strip() if nm else ''

        # Receiver link: SPI (onboard) vs serial, plus the serial provider if set.
        rx = ''
        if re.search(r'^feature\s+RX_SPI', text, re.M):
            rx = 'RX_SPI'
        elif re.search(r'^feature\s+RX_SERIAL', text, re.M) and not re.search(r'^feature\s+-RX_SERIAL', text, re.M):
            rx = 'RX_SERIAL'
        srx = val(text, 'serialrx_provider')
        if srx:
            rx = (rx + ' / ' if rx else '') + srx
        if not rx and val(text, 'rx_spi_protocol'):
            rx = 'RX_SPI / ' + val(text, 'rx_spi_protocol')

        # Quad identity: prefer the craft name baked into the dump (survives file renames),
        # then the filename label, then the board. norm() makes "M85 HDZero" == "M85_HDZERO".
        quad_display = craft or label or board
        ident = norm(craft) or norm(label) or norm(board)

        rows.append({
            '_ident': ident,
            'quad': quad_display,
            'dump_date': date_fmt,
            'craft_name': craft,
            'board': board,
            'manufacturer': manuf,
            'bf_version': bf_version,
            'mcu': mcu,
            'motor_protocol': val(text, 'motor_pwm_protocol'),
            'motor_poles': val(text, 'motor_poles'),
            'dshot_bidir': val(text, 'dshot_bidir'),
            'rx_protocol': rx,
            'video_system': val(text, 'vcd_video_system'),
            'vtx_band': val(text, 'vtx_band'),
            'vtx_channel': val(text, 'vtx_channel'),
            'vtx_power': val(text, 'vtx_power'),
            'vtx_freq': val(text, 'vtx_freq'),
            'cell_min_v': val(text, 'vbat_min_cell_voltage'),
            'cell_max_v': val(text, 'vbat_max_cell_voltage'),
            'cell_warn_v': val(text, 'vbat_warning_cell_voltage'),
            'rx_spi_protocol': val(text, 'rx_spi_protocol'),
            'elrs_uid': val(text, 'expresslrs_uid'),
            'bind_group': '',
            'gyro_align': val(text, 'gyro_1_sensor_align'),
            'pilot': val(text, 'pilot_name'),
            'file': base,
            'note': '',
        })

    # Quads sharing an ExpressLRS UID bind to the same radio -> same group (ELRS-A, ELRS-B, ...).
    # Most common UID becomes A; ties broken by UID string so labels are stable across re-runs.
    uid_counts = {}
    for r in rows:
        if r['elrs_uid']:
            uid_counts[r['elrs_uid']] = uid_counts.get(r['elrs_uid'], 0) + 1
    ordered = sorted(uid_counts, key=lambda u: (-uid_counts[u], u))
    uid_label = {u: f"ELRS-{chr(ord('A') + i)}" for i, u in enumerate(ordered)}
    for r in rows:
        if r['elrs_uid']:
            r['bind_group'] = uid_label[r['elrs_uid']]

    rows.sort(key=lambda r: (r['_ident'], r['dump_date'], r['file']))

    latest = {}
    for r in rows:
        k = r['_ident']
        if k not in latest or r['dump_date'] > latest[k]:
            latest[k] = r['dump_date']
    for r in rows:
        if r['dump_date'] == latest[r['_ident']] and 'EMPTY' not in r['note']:
            r['note'] = 'latest' + (('; ' + r['note']) if r['note'] else '')

    return rows


COLS = ['quad', 'dump_date', 'craft_name', 'board', 'manufacturer', 'bf_version', 'mcu',
        'motor_protocol', 'motor_poles', 'dshot_bidir', 'rx_protocol', 'rx_spi_protocol',
        'elrs_uid', 'bind_group', 'video_system', 'vtx_band', 'vtx_channel', 'vtx_power',
        'vtx_freq', 'cell_min_v', 'cell_max_v', 'cell_warn_v', 'gyro_align', 'pilot',
        'note', 'file']


def write_csv(path, data):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)


def latest_per_quad(rows):
    by_quad = {}
    for r in rows:
        by_quad.setdefault(r['_ident'], []).append(r)
    out = []
    for rs in by_quad.values():
        good = [r for r in rs if 'EMPTY' not in r['note']] or rs
        out.append(max(good, key=lambda r: (r['dump_date'], r['file'])))
    out.sort(key=lambda r: r['quad'].lower())
    return out


def short_mcu(mcu):
    return re.sub(r'^STM32', '', mcu) if mcu else '-'


def short_video(v):
    return {'HD': 'HD', 'NTSC': 'Analog', 'PAL': 'Analog', 'AUTO': 'Auto', '': '-'}.get(v, v)


def ver_tuple(v):
    """Leading major.minor of a firmware string as ints, e.g. '4.5.2.KAACK' -> (4, 5)."""
    nums = re.findall(r'\d+', v or '')
    return (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (0, 0)


def build_summary(latest_rows):
    from collections import Counter
    lines = []
    A = lines.append

    A("# FPV Fleet Summary")
    A("")
    A(f"_Auto-generated by the `fpv-fleet-update` skill on {date.today().isoformat()} "
      f"from the Betaflight CLI dumps in this folder._")
    A("")
    A("Source data: `fpv_quads.csv` (full history) and `fpv_quads_latest.csv` (newest dump per quad, "
      f"{len(latest_rows)} quads). Values come from `diff all` dumps, which only record settings that "
      "differ from firmware defaults — a blank cell means the setting is at its firmware default, "
      "not that it is missing.")
    A("")

    # ---- Fleet table ----
    A("## Fleet (latest dump per quad)")
    A("")
    A("| Quad | Board | MCU | BF | ESC | Video | RX / bind | Last dump |")
    A("|---|---|---|---|---|---|---|---|")
    for r in latest_rows:
        name = r['quad']
        if not r['craft_name'] and norm(r['quad']) == norm(r['board']):
            name += " *(unnamed)*"
        rx = r['rx_protocol'] or ''
        if r['bind_group']:
            rx = (rx + ' ' if rx else 'ELRS ') + f"**[{r['bind_group'].split('-')[-1]}]**"
        rx = rx or '-'
        A(f"| {name} | {r['board']} | {short_mcu(r['mcu'])} | {r['bf_version'] or '-'} | "
          f"{r['motor_protocol'] or '-'} | {short_video(r['video_system'])} | {rx} | {r['dump_date']} |")
    A("")

    # ---- Rollups ----
    A("## Fleet rollups")
    A("")
    mcus = Counter(short_mcu(r['mcu']) for r in latest_rows if r['mcu'])
    A("- **Flight controllers:** " + ", ".join(f"{n}× {m}" for m, n in mcus.most_common()) + ".")
    bfs = Counter(f"{a}.{b}" for a, b in (ver_tuple(r['bf_version']) for r in latest_rows) if a)
    A("- **Firmware:** " + ", ".join(f"{n} on BF {v}.x" for v, n in
                                      sorted(bfs.items(), key=lambda kv: (-kv[1], kv[0]))) + ".")
    escs = Counter(r['motor_protocol'] for r in latest_rows if r['motor_protocol'])
    A("- **ESC protocol:** " + ", ".join(f"{n}× {e}" for e, n in escs.most_common()) + ".")
    groups = Counter(r['bind_group'] for r in latest_rows if r['bind_group'])
    if groups:
        parts = []
        for g, n in groups.most_common():
            members = [r['quad'] for r in latest_rows if r['bind_group'] == g]
            uid = next(r['elrs_uid'] for r in latest_rows if r['bind_group'] == g)
            parts.append(f"**{g}** ({n} quad{'s' if n != 1 else ''}, UID `{uid}`)")
        A("- **ExpressLRS bind groups:** " + "; ".join(parts) +
          ". Quads in the same group share a binding phrase and bind to the same radio together.")
    vids = Counter(short_video(r['video_system']) for r in latest_rows if r['video_system'])
    if vids:
        A("- **Video:** " + ", ".join(f"{n}× {v}" for v, n in vids.most_common()) +
          ". Quads showing `-` have `vcd_video_system` at firmware default in the diff — "
          "not necessarily video-less.")
    A("")

    # ---- Needs attention ----
    A("## Needs attention")
    A("")
    aging = [r for r in latest_rows if r['bf_version'] and ver_tuple(r['bf_version']) < (4, 4)]
    if aging:
        A("**Aging firmware (older than BF 4.4):**")
        for r in sorted(aging, key=lambda r: ver_tuple(r['bf_version'])):
            A(f"- {r['quad']} ({r['bf_version']})")
        A("")

    today = date.today()
    stale = []
    for r in latest_rows:
        try:
            age_days = (today - datetime.strptime(r['dump_date'], "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if age_days > 365:
            stale.append((r, age_days))
    if stale:
        A("**Not re-dumped in over a year (take a fresh backup next time on the bench):**")
        for r, _ in sorted(stale, key=lambda t: t[1], reverse=True):
            A(f"- {r['quad']} (last dump {r['dump_date']})")
        A("")

    empties = [r for r in latest_rows if 'EMPTY' in r['note']]
    if empties:
        A("**Truncated dumps (re-export a full backup):**")
        for r in empties:
            A(f"- {r['quad']} — `{r['file']}`")
        A("")

    unnamed = [r for r in latest_rows if not r['craft_name'] and norm(r['quad']) == norm(r['board'])]
    if unnamed:
        A("_Note: " + ", ".join(r['quad'] for r in unnamed) +
          " are keyed by board name because their dumps had no craft name set "
          "(`set craft_name` / `# name:`). Setting a craft name makes future tracking more reliable._")
        A("")

    return "\n".join(lines).rstrip() + "\n"


def main():
    rows = parse_dumps()
    if not rows:
        print(f"No BTFL_cli_*.txt dumps found in {SRC}", file=sys.stderr)
        sys.exit(1)
    latest_rows = latest_per_quad(rows)

    write_csv(OUT, rows)
    write_csv(OUT_LATEST, latest_rows)
    with open(OUT_SUMMARY, 'w') as f:
        f.write(build_summary(latest_rows))

    print(f"Scanned {len(rows)} dumps -> {len(latest_rows)} quads")
    print(f"  {OUT}")
    print(f"  {OUT_LATEST}")
    print(f"  {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
