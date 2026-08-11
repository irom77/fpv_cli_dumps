#!/usr/bin/env python3
"""
Regenerate the FPV fleet inventory from Betaflight CLI dump files.

Scans every BTFL_cli_*.txt dump in the target folder and produces derived outputs including:
  - fpv_quads.csv         full history, one row per dump, newest per quad flagged 'latest'
  - fpv_quads_latest.csv  one row per quad, newest dump only
  - rates.csv             active rate profiles for curated, active quads
  - modes.csv             AUX mode assignments and activation ranges for curated, active quads
  - FLEET_SUMMARY.md      human-readable overview with rollups and a 'needs attention' pass

Usage:
    python update_fleet.py [folder]     # defaults to the current working directory

The parser is the single source of truth for generated outputs, so it is safe to re-run any time
new dumps are dropped in.
"""
import os, re, csv, sys, glob
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rates  # noqa: E402  (sibling module: rate-curve math, no I/O)

SRC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
OUT = os.path.join(SRC, "fpv_quads.csv")
OUT_LATEST = os.path.join(SRC, "fpv_quads_latest.csv")
OUT_RATES = os.path.join(SRC, "rates.csv")
OUT_MODES = os.path.join(SRC, "modes.csv")
OUT_SUMMARY = os.path.join(SRC, "FLEET_SUMMARY.md")
HW_CSV = os.path.join(SRC, "hardware.csv")
PRESETS_CSV = os.path.join(SRC, "rate_presets.csv")
SPECS_CSV = os.path.join(SRC, "specs.csv")

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


# Permanent IDs written by Betaflight's `aux` CLI command. They are deliberately sparse: IDs that
# disappeared remain reserved so a saved mode range keeps its meaning across firmware upgrades.
MODE_NAMES = {
    0: 'ARM', 1: 'ANGLE', 2: 'HORIZON', 3: 'ALTHOLD', 4: 'ANTI GRAVITY', 5: 'MAG',
    6: 'HEADFREE', 7: 'HEADADJ', 8: 'CAMSTAB', 11: 'POS HOLD', 12: 'PASSTHRU',
    13: 'BEEPER ON', 15: 'LEDLOW', 17: 'CALIB', 19: 'OSD', 20: 'TELEMETRY',
    23: 'SERVO1', 24: 'SERVO2', 25: 'SERVO3', 26: 'BLACKBOX', 27: 'FAILSAFE',
    28: 'AIRMODE', 29: '3D MODE', 30: 'FPV ANGLE MIX', 31: 'BLACKBOX ERASE',
    32: 'CAMERA CONTROL 1', 33: 'CAMERA CONTROL 2', 34: 'CAMERA CONTROL 3',
    35: 'FLIP OVER AFTER CRASH', 36: 'PREARM', 37: 'BEEP GPS SATELLITE COUNT',
    39: 'VTX PIT MODE', 40: 'USER1', 41: 'USER2', 42: 'USER3', 43: 'USER4',
    44: 'PID AUDIO', 45: 'PARALYZE', 46: 'GPS RESCUE', 47: 'ACRO TRAINER',
    48: 'DISABLE VTX CONTROL', 49: 'LAUNCH CONTROL', 50: 'MSP OVERRIDE',
    51: 'STICK COMMANDS DISABLE', 52: 'BEEPER MUTE', 53: 'READY',
    54: 'LAP TIMER RESET', 55: 'CHIRP', 56: 'AUTOPILOT',
}


def mode_range_visual(start, end):
    """Render Betaflight's 900–2100 range as 24 cells without losing its 25 us resolution.

    Each cell covers two 25 us steps: full block means both are active; left/right half blocks mean
    only that half is active. Exact endpoints remain separate CSV columns for sorting and tooling.
    """
    start_step = max(0, min(48, (start - 900) // 25))
    end_step = max(0, min(48, (end - 900) // 25))
    symbols = {(False, False): '·', (True, True): '█',
               (True, False): '▌', (False, True): '▐'}
    cells = []
    for step in range(0, 48, 2):
        cells.append(symbols[(start_step <= step < end_step,
                              start_step <= step + 1 < end_step)])
    return '900 |' + ''.join(cells) + '| 2100'


def extract_modes(text):
    """Decode configured Betaflight mode ranges from `aux` lines.

    CLI shape: aux <slot> <permanent mode id> <zero-based AUX> <start> <end> <logic> <linked id>.
    Equal range endpoints are Betaflight's disabled-slot representation and are omitted. Unknown
    IDs stay visible for custom/newer firmware instead of silently losing configuration.
    """
    out = []
    pattern = re.compile(
        r'^aux\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$', re.M)
    for match in pattern.finditer(text):
        slot, mode_id, aux_index, start, end, logic, linked_id = map(int, match.groups())
        if start == end:
            continue
        out.append({
            'slot': slot,
            'mode_id': mode_id,
            'mode': MODE_NAMES.get(mode_id, f'UNKNOWN ({mode_id})'),
            'aux_channel': f'AUX{aux_index + 1}',
            'range_start': start,
            'range_end': end,
            'range_visual': mode_range_visual(start, end),
            'logic': 'AND' if logic == 1 else 'OR',
            # linkedTo=0 is Betaflight's sentinel for no linked mode (ARM cannot be a link target).
            'linked_to_id': linked_id if linked_id else '',
            'linked_to': MODE_NAMES.get(linked_id, f'UNKNOWN ({linked_id})') if linked_id else '',
        })
    return out


def md(s):
    """Escape a value for a markdown table cell. Hand-written hardware.csv text can legitimately
    contain a pipe (e.g. a motor sold under two brands, `HeadsUp | Five33 2207`), which would
    otherwise split the cell and shift every column after it."""
    return str(s or '').replace('|', '\\|')


def norm(s):
    return re.sub(r'[^A-Za-z0-9]', '', s).upper()


CLASS_ORDER = ['whoop', 'cinewhoop', 'micro', '5-inch']
# Lifecycle state of the airframe (can I fly it today?). Hand-maintained; blank defaults to 'active'
# so only exceptions need annotating. Ordered flyable -> gone for stable rollups.
STATUS_ORDER = ['active', 'building', 'rebuilding', 'broken', 'retired', 'lost']
FLYABLE = {'active', 'building', 'rebuilding', ''}   # states we still nag about (firmware/staleness)
# What the quad is built to do (how is it flown?). Orthogonal to status — a quad keeps its discipline
# after it's retired. Hand-entered only; the dump carries no signal for it, so there's no guesser.
DISCIPLINE_ORDER = ['race', 'freestyle', 'cinematic', 'long-range']


def guess_class(craft, board):
    """Best-effort size class from craft name + board. Betaflight dumps carry no frame/prop/motor/
    cell field, so class can't be read directly — this leans on product-name conventions and board
    families. It is only a fallback: an explicit `class` in hardware.csv overrides it, so fix wrong
    guesses there rather than special-casing here. Returns '' when nothing matches (left to curate).
    Note: an 'AIO' / trailing digit in a name is a board type (e.g. AIO5 = 5-in-1 board), not a
    frame size — so a whoop AIO board stays a whoop regardless of the number after it."""
    s = (craft + ' ' + board).lower()
    if 'cinelog' in s or 'cinewhoop' in s or 'cine' in s:
        return 'cinewhoop'
    if 'crux' in s or 'crocodile' in s:            # 3-4" micro / long-range product lines
        return 'micro'
    whoop_boards = ('crazybeef4', 'betafpvf4sx1280', 'betafpvf4')
    whoop_names = ('air65', 'meteor', 'mobula', 'mob6', 'beta65', 'beta75', 'beta85',
                   'us65', 'us75', 'whoop', 'happish', 'ecofree', 'diamond')
    if any(b in s for b in whoop_boards) or any(n in s for n in whoop_names):
        return 'whoop'
    stack_boards = ('xrotor', 'tmotorf7', 'flywoof7', 'f722', 'f745', 'f405', 'xilo')
    if any(b in s for b in stack_boards):
        return '5-inch'
    return ''


def load_hw_map(path, col):
    """Map normalized quad name -> a hand-curated column value from hardware.csv, when set. Used for
    fields the dumps can't carry (`class` overrides guess_class(); `status`/`discipline` have no
    guesser at all). Blank cells are skipped so callers can apply their own default."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            c = (r.get(col) or '').strip()
            if c:
                out[norm(r.get('quad', ''))] = c
    return out


def load_aliases(path):
    """Map normalized former quad name -> current display name, from hardware.csv's `aliases`
    column (';'-separated list of old names). Quad identity comes from the craft name baked into
    the dump, so renaming a quad in Betaflight (e.g. Kronos -> openracer) would otherwise split one
    airframe into two quads with two half-histories. Listing the old name here folds its dumps and
    its blackbox flights into the current quad. Self-references are ignored."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            cur = (r.get('quad') or '').strip()
            if not cur:
                continue
            for a in (r.get('aliases') or '').split(';'):
                a = a.strip()
                if a and norm(a) != norm(cur):
                    out[norm(a)] = cur
    return out


def extract_active_rates(text):
    """Pull the ACTIVE rateprofile's rates. The rate keys (rc_rate/srate/expo/rates_type) live
    inside a rateprofile block, and the same key name appears in every profile — so we must read
    only the active one. The active profile is the last bare `rateprofile N` line (the restore
    selection in normal dumps; the sole defined profile in older/partial dumps). Values are the RAW
    stored integers straight from the dump; their meaning depends on rates_type (BETAFLIGHT: RC Rate /
    Super Rate / Expo; ACTUAL: Center Sensitivity / Max Rate / Expo). Defaults are omitted by
    `diff all`, so unset fields come out blank. rates_type blank means firmware default (ACTUAL)."""
    sels = re.findall(r'^rateprofile (\d+)\s*$', text, re.M)
    active = sels[-1] if sels else None
    vals = {}
    if active is not None:
        cur = None
        for line in text.splitlines():
            m = re.match(r'^rateprofile (\d+)\s*$', line)
            if m:
                cur = m.group(1)
                continue
            if cur == active:
                sm = re.match(r'^set (\w+) = (.+?)\s*$', line)
                if sm:
                    vals[sm.group(1)] = sm.group(2).strip()

    def triple(a, b, c):
        parts = [vals.get(a, ''), vals.get(b, ''), vals.get(c, '')]
        return '/'.join(parts) if any(parts) else ''

    name = vals.get('rateprofile_name', '')
    return {
        'rateprofile': (f"{active}:{name}" if active is not None and name else (active or '')),
        'rates_type': vals.get('rates_type', ''),
        'rc_rate_rpy': triple('roll_rc_rate', 'pitch_rc_rate', 'yaw_rc_rate'),
        'super_rate_rpy': triple('roll_srate', 'pitch_srate', 'yaw_srate'),
        'expo_rpy': triple('roll_expo', 'pitch_expo', 'yaw_expo'),
    }


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
                'gyro_align': '', 'rpm_limit': '', 'rpm_limit_value': '',
                '_modes': [],
                'pilot': '', 'file': base, 'note': 'EMPTY/INCOMPLETE DUMP'
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
            # RPM limiter — stock in Betaflight 4.5, and the mechanism spec race classes are built
            # on. Blank means the diff left it at the firmware default (OFF / 18000 on KAACK), so
            # blank reads as "limiter not enabled", not "not tracked". See DUMP_DEFAULTS.
            'rpm_limit': val(text, 'rpm_limit'),
            'rpm_limit_value': val(text, 'rpm_limit_value'),
            '_modes': extract_modes(text),
            **extract_active_rates(text),
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

    # Curated fields that dumps can't carry, all keyed by normalized quad name from hardware.csv:
    #   class      — size bucket; falls back to the guess_class() heuristic when unset.
    #   status     — lifecycle (active/retired/...); blank means active (see status_of()).
    #   discipline — what it's flown for (race/freestyle/cinematic); blank stays blank, no guesser.
    hw_path = os.path.join(SRC, "hardware.csv")

    # Fold renamed quads onto their current name before any name-keyed join below, so a rename
    # doesn't split one airframe's history in two. The per-dump craft_name column keeps the old
    # name visible in the history rows.
    aliases = load_aliases(hw_path)
    for r in rows:
        cur = aliases.get(r['_ident'])
        if cur:
            r['quad'] = cur
            r['_ident'] = norm(cur)

    hw_class = load_hw_map(hw_path, "class")
    hw_status = load_hw_map(hw_path, "status")
    hw_discipline = load_hw_map(hw_path, "discipline")
    for r in rows:
        r['class'] = hw_class.get(r['_ident'], '') or guess_class(r.get('craft_name', ''), r.get('board', ''))
        r['status'] = hw_status.get(r['_ident'], '')
        r['discipline'] = hw_discipline.get(r['_ident'], '')

    # Collapse duplicate dumps: when several dumps of one quad share identical extracted
    # inventory values (differing only in date/file), keep just the most recent. The older
    # ones carry no information at this level of detail — even if the raw dump differed in
    # fields we don't track (PIDs, OSD layout), the inventory row would be identical.
    scanned = len(rows)
    ignore = {'_ident', 'dump_date', 'note', 'file'}
    keycols = [c for c in COLS if c not in ignore]  # canonical + stable across row shapes
    dedup = {}
    for r in rows:
        k = (r['_ident'],) + tuple(r.get(c, '') for c in keycols)
        cur = dedup.get(k)
        if cur is None or (r['dump_date'], r['file']) > (cur['dump_date'], cur['file']):
            dedup[k] = r
    rows = list(dedup.values())

    rows.sort(key=lambda r: (r['_ident'], r['dump_date'], r['file']))

    latest = {}
    for r in rows:
        k = r['_ident']
        if k not in latest or r['dump_date'] > latest[k]:
            latest[k] = r['dump_date']
    for r in rows:
        if r['dump_date'] == latest[r['_ident']] and 'EMPTY' not in r['note']:
            r['note'] = 'latest' + (('; ' + r['note']) if r['note'] else '')

    return rows, scanned


COLS = ['quad', 'class', 'discipline', 'status', 'dump_date', 'craft_name', 'board', 'manufacturer', 'bf_version', 'mcu',
        'motor_protocol', 'motor_poles', 'dshot_bidir', 'rx_protocol', 'rx_spi_protocol',
        'elrs_uid', 'bind_group', 'video_system', 'vtx_band', 'vtx_channel', 'vtx_power',
        'vtx_freq', 'cell_min_v', 'cell_max_v', 'cell_warn_v', 'gyro_align',
        'rpm_limit', 'rpm_limit_value',
        'rateprofile', 'rates_type', 'rc_rate_rpy', 'super_rate_rpy', 'expo_rpy', 'pilot',
        'note', 'file']


def write_csv(path, data, cols=None, lineterminator=None):
    with open(path, 'w', newline='') as f:
        options = {'fieldnames': cols or COLS, 'extrasaction': 'ignore'}
        if lineterminator is not None:
            options['lineterminator'] = lineterminator
        w = csv.DictWriter(f, **options)
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


def status_of(r):
    """Lifecycle status with the blank-means-active default applied. Everything that reasons about
    whether a quad is still in service goes through this so the default lives in one place."""
    return (r.get('status') or 'active').strip().lower()


def short_mcu(mcu):
    return re.sub(r'^STM32', '', mcu) if mcu else '-'


def short_video(v):
    return {'HD': 'HD', 'NTSC': 'Analog', 'PAL': 'Analog', 'AUTO': 'Auto', '': '-'}.get(v, v)


def ver_tuple(v):
    """Leading major.minor of a firmware string as ints, e.g. '4.5.2.KAACK' -> (4, 5)."""
    nums = re.findall(r'\d+', v or '')
    return (int(nums[0]), int(nums[1])) if len(nums) >= 2 else (0, 0)


def build_summary(latest_rows, rate_rows=(), spec_rows=()):
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
    A("| Quad | Class | Use | Status | Board | MCU | BF | ESC | Video | RX / bind | Last dump |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in latest_rows:
        name = r['quad']
        if not r['craft_name'] and norm(r['quad']) == norm(r['board']):
            name += " *(unnamed)*"
        rx = r['rx_protocol'] or ''
        if r['bind_group']:
            rx = (rx + ' ' if rx else 'ELRS ') + f"**[{r['bind_group'].split('-')[-1]}]**"
        rx = rx or '-'
        st = status_of(r)
        st_cell = st if st == 'active' else f"**{st}**"   # make retired/lost/building stand out
        A(f"| {name} | {r.get('class') or '—'} | {r.get('discipline') or '—'} | {st_cell} | "
          f"{r['board']} | {short_mcu(r['mcu'])} | "
          f"{r['bf_version'] or '-'} | {r['motor_protocol'] or '-'} | {short_video(r['video_system'])} | "
          f"{rx} | {r['dump_date']} |")
    A("")

    # ---- Rollups ----
    A("## Fleet rollups")
    A("")
    classes = Counter(r['class'] for r in latest_rows if r.get('class'))
    if classes:
        order = {c: i for i, c in enumerate(CLASS_ORDER)}
        items = sorted(classes.items(), key=lambda kv: (order.get(kv[0], 99), kv[0]))
        A("- **Class:** " + ", ".join(f"{n}× {c}" for c, n in items) +
          ". Size class inferred from craft name / board where `hardware.csv` doesn't set it.")
    statuses = Counter(status_of(r) for r in latest_rows)
    if statuses:
        order = {s: i for i, s in enumerate(STATUS_ORDER)}
        items = sorted(statuses.items(), key=lambda kv: (order.get(kv[0], 99), kv[0]))
        A("- **Status:** " + ", ".join(f"{n}× {s}" for s, n in items) +
          ". Lifecycle from `hardware.csv`; a blank there counts as active.")
    disciplines = Counter(r['discipline'] for r in latest_rows if r.get('discipline'))
    if disciplines:
        order = {d: i for i, d in enumerate(DISCIPLINE_ORDER)}
        items = sorted(disciplines.items(), key=lambda kv: (order.get(kv[0], 99), kv[0]))
        blank = sum(1 for r in latest_rows if not r.get('discipline'))
        A("- **Discipline:** " + ", ".join(f"{n}× {d}" for d, n in items) +
          (f", {blank} unset" if blank else "") +
          ". Hand-entered in `hardware.csv` (no heuristic — the dump gives no signal).")
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
    # Retired/lost quads are intentionally excluded from the firmware/staleness nags below — a
    # shelved or gone quad doesn't need a fresh backup or a flash. They still appear in the fleet
    # table (flagged by status); this section is only about things worth acting on.
    inservice = [r for r in latest_rows if status_of(r) in FLYABLE]

    broken = [r for r in latest_rows if status_of(r) == 'broken']
    if broken:
        A("**Broken (needs repair — grounded until fixed):** "
          + ", ".join(r['quad'] for r in broken) + ".")
        A("")

    building = [r for r in latest_rows if status_of(r) in ('building', 'rebuilding')]
    if building:
        A("**In progress (config expected incomplete — not a truncated dump):** "
          + ", ".join(f"{r['quad']} ({status_of(r)})" for r in building) + ".")
        A("")

    aging = [r for r in inservice if r['bf_version'] and ver_tuple(r['bf_version']) < (4, 4)]
    if aging:
        A("**Aging firmware (older than BF 4.4):**")
        for r in sorted(aging, key=lambda r: ver_tuple(r['bf_version'])):
            A(f"- {r['quad']} ({r['bf_version']})")
        A("")

    today = date.today()
    stale = []
    for r in inservice:
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

    # Rate drift: the dump disagrees with the preset the pilot says this quad should be flying.
    # Worth nagging about because rates are invisible on the bench — you only notice in the air.
    drift = [r for r in rate_rows if r['preset_status'] == 'differs']
    if drift:
        A("**Rates differ from their assigned preset (`rate_preset` in `hardware.csv`):**")
        for r in drift:
            on = 'firmware defaults' if r['source'] == 'default' else f"{r['rates_type']} {r['max_rpy']} °/s max"
            A(f"- {r['quad']} — on {on}, expected `{r['preset']}`")
        A("")
    inert = [r for r in rate_rows if r['note'].startswith('CENTER>=MAX')]
    if inert:
        A("**Rate profile looks like it survived a firmware upgrade** — centre sensitivity meets or "
          "exceeds max rate on an ACTUAL profile, so the max-rate setting does nothing and the "
          "stick is linear to a very high ceiling. Usually old BETAFLIGHT-rates numbers left on a "
          "profile the firmware now reads as ACTUAL:")
        for r in inert:
            maxset = '/'.join(str(int(v) * 10) for v in r['super_rate_rpy'].split('/'))
            A(f"- {r['quad']} ({r['bf_version']}) — rc_rate {r['rc_rate_rpy']} → centre "
              f"{r['center_rpy']} °/s, which swamps the max-rate setting ({maxset} °/s)")
        A("")

    unknown = sorted({r['preset'] for r in rate_rows if r['preset_status'] == 'unknown-preset'})
    if unknown:
        A("**Undefined rate presets (referenced in `hardware.csv`, missing from `rate_presets.csv`):** "
          + ", ".join(f"`{p}`" for p in unknown) + ".")
        A("")

    # Spec shortfalls: a quad that is in scope for a race class but wouldn't pass tech check. Only
    # hard fails are nagged about here — `unknown` is a gap in hardware.csv, not in the airframe,
    # and the Spec compliance section below lists those.
    for name, rules, entries in spec_rows:
        short = [(e, [rule for rule, (state, _) in zip(rules, e['results']) if state == 'fail'])
                 for e in entries]
        short = [(e, bad) for e, bad in short if bad]
        if short:
            A(f"**Not {spec_title(name)} legal (see Spec compliance below):**")
            for e, bad in short:
                A(f"- {e['quad']} — " + ", ".join(r['requirement'].lower() for r in bad))
            A("")

    unclassed = [r for r in latest_rows if not r.get('class')]
    if unclassed:
        A("**Unclassified (heuristic couldn't tell — set `class` in `hardware.csv`):** "
          + ", ".join(r['quad'] for r in unclassed) + ".")
        A("")

    unnamed = [r for r in latest_rows if not r['craft_name'] and norm(r['quad']) == norm(r['board'])]
    if unnamed:
        A("_Note: " + ", ".join(r['quad'] for r in unnamed) +
          " are keyed by board name because their dumps had no craft name set "
          "(`set craft_name` / `# name:`). Setting a craft name makes future tracking more reliable._")
        A("")

    return "\n".join(lines).rstrip() + "\n"


# Identity, then the headline figures (centre / max / expo), then what qualifies them, then the
# supporting detail — curve points and the default-filled raw integers they were derived from.
RATE_COLS = ['quad', 'discipline', 'class',
             'center_rpy', 'max_rpy', 'expo_rpy',
             'bf_version', 'preset', 'preset_status', 'rates_type',
             'dps25_rpy', 'dps50_rpy', 'dps75_rpy', 'rc_rate_rpy', 'super_rate_rpy',
             'rateprofile', 'note', 'source']

MODE_COLS = ['quad', 'discipline', 'class', 'mode', 'aux_channel',
             'range_visual', 'range_start', 'range_end', 'mode_id', 'logic', 'linked_to', 'linked_to_id',
             'slot', 'bf_version', 'source']


def load_presets(path):
    """Hand-maintained rate presets: name -> raw signature to compare a quad against. A preset is
    just a named rateprofile the pilot intends several quads to share, so drift can be flagged."""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, newline='') as f:
        for r in csv.DictReader(f):
            name = (r.get('preset') or '').strip()
            if name:
                out[name] = r
    return out


def in_rates_view(r):
    """Whether a quad belongs in `rates.csv` and the summary's Rates tables.

    Rates only matter for a quad you might actually fly, and only compare meaningfully against
    quads flown the same way — so the view is limited to active airframes with a discipline set.
    A retired, broken or half-built quad is noise in a file whose whole purpose is side-by-side
    comparison, as is one whose discipline was never recorded (it has no group to be read against).

    Note this filters the VIEW only. The needs-attention checks still run over every quad, so a
    misconfigured rateprofile is reported even on an airframe that never appears here."""
    return status_of(r) == 'active' and bool((r.get('discipline') or '').strip())


def in_modes_view(r):
    """Mode comparison view: only active quads with both grouping fields curated."""
    return (status_of(r) == 'active'
            and bool((r.get('discipline') or '').strip())
            and bool((r.get('class') or '').strip()))


def rate_sort_key(r):
    """Group the rates view by discipline, then by size class, then alphabetically.

    Rates are only meaningful in comparison — the point of the file is to see whether quads flown
    the same way are set up the same way, which alphabetical order scatters (openracer and QAS JB
    end up eleven rows apart). Class is the second key because rates don't transfer across sizes:
    a 1S whoop at 667 °/s and a 6S five-inch at 667 °/s are not the same setup, and grouping them
    under one 'race' heading would invite comparing numbers that were never meant to match.
    Unset discipline/class sort last rather than leading the file."""
    def rank(value, order):
        v = (value or '').strip()
        return order.index(v) if v in order else len(order)
    return (rank(r.get('discipline'), DISCIPLINE_ORDER),
            rank(r.get('class'), CLASS_ORDER),
            r['quad'].lower())


def build_mode_rows(latest_rows):
    """Flatten each in-scope quad's configured AUX ranges into one CSV row per mode range."""
    out = []
    for r in sorted((row for row in latest_rows if in_modes_view(row)), key=rate_sort_key):
        for mode in sorted(r.get('_modes', ()), key=lambda m: m['slot']):
            out.append({
                'quad': r['quad'],
                'discipline': r.get('discipline', ''),
                'class': r.get('class', ''),
                **mode,
                'bf_version': r.get('bf_version', ''),
                'source': r.get('file', ''),
            })
    return out


def compact_mode_groups(rows):
    """Blank repeated grouping cells for the human-facing CSV; blank means 'same as above'.

    Work on copies so downstream checks can still use fully populated mode rows.
    """
    out = []
    previous = {field: object() for field in ('quad', 'discipline', 'class')}
    for row in rows:
        compact = dict(row)
        for field in previous:
            value = row.get(field, '')
            if value == previous[field]:
                compact[field] = ''
            previous[field] = value
        out.append(compact)
    return out


def build_rate_rows(latest_rows, presets, hw_preset):
    """Decode every quad's active rateprofile into deg/s, and compare against its intended preset.

    Every quad appears, including those on stock rates — a blank cell in the old raw table meant
    'firmware default', which reads identically to 'not tracked' and hid that a race quad had never
    had its rates set at all. Defaults are materialized here instead, using the values that the
    quad's own firmware generation shipped (they changed at 4.3).

    Returns a row for EVERY quad, each carrying `in_view` (see in_rates_view()). `in_view` is not
    in RATE_COLS so it never reaches the CSV — callers filter on it for the view, while the
    needs-attention checks read the unfiltered list."""
    out = []
    for r in sorted(latest_rows, key=rate_sort_key):
        d = rates.decode(r.get('rc_rate_rpy', ''), r.get('super_rate_rpy', ''),
                         r.get('expo_rpy', ''), r.get('rates_type', ''), r.get('bf_version', ''))
        preset = hw_preset.get(norm(r['quad']), '')
        status = ''
        if preset:
            p = presets.get(preset)
            if not p:
                status = 'unknown-preset'
            else:
                want = rates.decode(p.get('rc_rate_rpy', ''), p.get('super_rate_rpy', ''),
                                    p.get('expo_rpy', ''), p.get('rates_type', ''),
                                    r.get('bf_version', ''))
                status = 'match' if rates.raw_signature(want) == rates.raw_signature(d) else 'differs'
        out.append({
            'in_view': in_rates_view(r),
            'quad': r['quad'],
            'discipline': r.get('discipline', ''),
            'class': r.get('class', ''),
            'bf_version': r.get('bf_version', ''),
            'rates_type': d['rates_type'] + ('' if d['type_from_dump'] else ' (default)'),
            'source': d['source'],
            'preset': preset,
            'preset_status': status,
            'center_rpy': rates.triple_of(d, 'center'),
            'max_rpy': rates.triple_of(d, 'max'),
            'expo_rpy': '/'.join(str(d['axes'][a]['expo']) for a in rates.AXES),
            'dps25_rpy': rates.curve_triple(d, 25),
            'dps50_rpy': rates.curve_triple(d, 50),
            'dps75_rpy': rates.curve_triple(d, 75),
            'rc_rate_rpy': '/'.join(str(d['axes'][a]['rc_rate']) for a in rates.AXES),
            'super_rate_rpy': '/'.join(str(d['axes'][a]['srate']) for a in rates.AXES),
            'rateprofile': r.get('rateprofile', ''),
            'note': ('CENTER>=MAX(' + ','.join(inert) + ')') if (inert := rates.inert_max_rate(d)) else
                    ('' if d['supported'] else f"unsupported rates_type {d['rates_type']}"),
        })
    return out


def build_rates_section(rate_rows, total=None):
    """Per-quad rates table in real deg/s, decoded from the raw stored integers via rates.py."""
    if not rate_rows:
        return ""
    hidden = (total - len(rate_rows)) if total else 0
    lines = ["", "## Rates", "",
             "_Active rateprofile, decoded to deg/s (see `rates.csv`). **Center** is stick "
             "sensitivity around centre, **Max** the rate at full deflection, r/p/y. `source=default` "
             "means the dump set no rates at all, so the values shown are that firmware's stock "
             "rateprofile — which changed at 4.3 (before: BETAFLIGHT 100/70, center 200; after: "
             "ACTUAL 7/67, center 70). Intended rates come from `rate_preset` in `hardware.csv`._",
             ""]
    if hidden:
        lines += [f"_Showing the {len(rate_rows)} active quads that have a `discipline` set; "
                  f"{hidden} other{'s are' if hidden != 1 else ' is'} hidden (retired, broken, "
                  f"incomplete, or no discipline recorded). \"Needs attention\" above still checks "
                  f"every quad._",
                  ""]
    # One sub-table per discipline so quads flown the same way sit together and can be read against
    # each other; rate_rows already arrives in that order from rate_sort_key().
    groups = {}
    for r in rate_rows:
        groups.setdefault(((r['discipline'] or '').strip(), (r['class'] or '').strip()), []).append(r)
    for (disc, cls), rows in groups.items():
        lines.append(f"**{disc or 'discipline not set'} — {cls or 'class unknown'}**")
        lines.append("")
        lines.append("| Quad | Center °/s | Max °/s | Expo | @50% | Preset | Type | Source |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in rows:
            preset = r['preset'] or '—'
            if r['preset_status'] == 'differs':
                preset = f"**{preset} ⚠️**"
            elif r['preset_status'] == 'match':
                preset = f"{preset} ✓"
            elif r['preset_status'] == 'unknown-preset':
                preset = f"{preset} *(undefined)*"
            lines.append(f"| {r['quad']} | "
                         f"{r['center_rpy'] or '—'} | {r['max_rpy'] or '—'} | {r['expo_rpy']} | "
                         f"{r['dps50_rpy'] or '—'} | {preset} | {r['rates_type']} | {r['source']} |")
        lines.append("")
    return "\n".join(lines)


# Settings whose absence from a `diff all` means "at firmware default" rather than "not tracked".
# Only fields a spec check reads need an entry. rpm_limit_value's 18000 is KAACK's default (seen in
# the one full `dump` in backups/, LS-Ultra on KAACK_V15) — stock Betaflight ships a different
# ceiling, but a quad not on KAACK fails the firmware requirement anyway.
DUMP_DEFAULTS = {'rpm_limit': 'OFF', 'rpm_limit_value': '18000'}

SPEC_MARK = {'ok': '✓', 'fail': '✗', 'unknown': '?', 'manual': '·'}


def load_specs(path):
    """Hand-maintained race-class specs: an ordered list of requirement rows. Each row is one rule
    of one spec, tagged with the class/discipline it applies to, plus a declarative check the
    generator can run (see check_rule). Adding a spec is adding rows — no code change."""
    if not os.path.exists(path):
        return []
    with open(path, newline='') as f:
        return [r for r in csv.DictReader(f) if (r.get('spec') or '').strip()]


def load_hw_rows(path):
    """Map normalized quad name -> its whole hardware.csv row, for checks that read several build
    fields. load_hw_map() covers the single-column case."""
    if not os.path.exists(path):
        return {}
    with open(path, newline='') as f:
        return {norm(r.get('quad', '')): r for r in csv.DictReader(f) if (r.get('quad') or '').strip()}


def first_number(s):
    m = re.search(r'\d+(?:\.\d+)?', s or '')
    return float(m.group(0)) if m else None


def check_rule(rule, row, hw):
    """Run one specs.csv rule against a quad. Returns (state, detail).

    States are deliberately four-valued: a requirement we can't see is not a failure. `unknown`
    means the data to judge it isn't recorded (usually a blank hardware.csv cell), `manual` means
    it isn't recordable at all — no dump or build sheet says how many LEDs are screwed to the frame.
    Only `fail` is a real "this quad would be turned away at tech check"."""
    kind = (rule.get('check') or '').strip()
    field = (rule.get('field') or '').strip()
    want = (rule.get('value') or '').strip()

    if kind == 'manual' or not kind:
        return 'manual', 'verify on the bench'

    if kind == 'hw_match':
        if hw is None:
            return 'unknown', 'no hardware.csv row'
        got = (hw.get(field) or '').strip()
        if not got:
            return 'unknown', f'`{field}` not recorded in hardware.csv'
        if re.search(want, got, re.I):
            return 'ok', got
        # A cell that doesn't answer the question isn't a failure. `evidence` is a regex for "this
        # field states the kind of fact being tested" — a stator size, a cell count, an ESC
        # firmware. Without a match there, the build sheet is simply silent on the rule, and
        # calling that non-compliant would fail a quad for a gap in the notes.
        ev = (rule.get('evidence') or '').strip()
        if ev and not re.search(ev, got, re.I):
            return 'unknown', f'nothing recorded either way in `{field}` — "{got}"'
        return 'fail', got

    if kind == 'dump_match':
        got = (row.get(field) or '').strip()
        defaulted = not got
        if defaulted:
            got = DUMP_DEFAULTS.get(field, '')
            if not got:
                return 'unknown', f'`{field}` absent from the dump'
        shown = got + (' (firmware default)' if defaulted else '')
        return ('ok' if re.search(want, got, re.I) else 'fail'), shown

    if kind == 'hw_weight_min':
        floor = first_number(want) or 0
        if hw is None:
            return 'unknown', 'no hardware.csv row'
        got = (hw.get(field) or '').strip()
        grams = first_number(got)
        if grams is None:
            return 'unknown', f'`{field}` not recorded in hardware.csv'
        if grams >= floor:
            return 'ok', got
        # hardware.csv weights for 5-inch builds are dry (no pack, often no props), and a 6S race
        # pack is 200-260 g — enough to clear most minimums. Never fail on a figure that was never
        # AUW; say what it would take to settle it.
        return 'unknown', f'{got} recorded, {floor:.0f} g minimum — weigh it with the race pack in'

    return 'unknown', f'unknown check `{kind}`'


def spec_title(name):
    return ' '.join(w.capitalize() for w in re.split(r'[-_]', name) if w)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', (s or '').lower()).strip('_')


def spec_scope(rule, r):
    """Does a quad fall under this rule's class/discipline? A blank column means 'any'."""
    for col, key in (('applies_class', 'class'), ('applies_discipline', 'discipline')):
        want = (rule.get(col) or '').strip()
        if want and want.lower() != (r.get(key) or '').strip().lower():
            return False
    return True


def build_spec_rows(specs, latest_rows, hw_rows):
    """Evaluate every spec against every quad in its scope.

    Returns [(spec_name, [rule, ...], [{quad, row, results: [(state, detail), ...]}, ...])], in
    specs.csv order. Callers render it and mine it for the needs-attention pass."""
    out = []
    for name in dict.fromkeys(r['spec'].strip() for r in specs):
        rules = [r for r in specs if r['spec'].strip() == name]
        # Scope is a property of the spec, not of each rule — every row of a spec carries the same
        # applies_class/applies_discipline, so the first one decides who is in scope.
        quads = [r for r in latest_rows if spec_scope(rules[0], r)]
        entries = []
        for r in sorted(quads, key=lambda r: r['quad'].lower()):
            hw = hw_rows.get(norm(r['quad']))
            entries.append({'quad': r['quad'], 'row': r,
                            'results': [check_rule(rule, r, hw) for rule in rules]})
        out.append((name, rules, entries))
    return out


def spec_verdict(states):
    """One-phrase answer to "could I enter this quad?". A hard fail outranks anything unconfirmed —
    there's no point chasing a missing weight while the RPM limiter is off."""
    bad, unsure = states.count('fail'), states.count('unknown')
    if bad:
        return f"{bad} to fix"
    if unsure:
        return f"{unsure} to confirm"
    return "eligible"


def write_compliance_csvs(spec_rows, srcdir):
    """One CSV per spec: the compliance table as data, quads down the side and requirements across.

    Per spec rather than one combined file because the columns *are* the requirements — two classes
    don't share them, and merging would give a sparse union of every rule ever written. Each new
    spec in specs.csv simply produces its own file. Returns the paths written."""
    written = []
    for name, rules, entries in spec_rows:
        if not entries:
            continue
        reqs = [(slug(r['requirement']), r) for r in rules]
        cols = (['quad', 'class', 'discipline', 'status', 'verdict'] +
                [c for c, _ in reqs] + ['missing', 'to_confirm'])
        data = []
        for e in entries:
            r = e['row']
            states = [s for s, _ in e['results']]
            row = {'quad': e['quad'], 'class': r.get('class', ''),
                   'discipline': r.get('discipline', ''), 'status': status_of(r),
                   'verdict': spec_verdict(states),
                   'missing': '; '.join(rule['requirement'] for (_, rule), s in zip(reqs, states)
                                        if s == 'fail'),
                   'to_confirm': '; '.join(rule['requirement'] for (_, rule), s in zip(reqs, states)
                                           if s == 'unknown')}
            row.update({c: s for (c, _), s in zip(reqs, states)})
            data.append(row)
        path = os.path.join(srcdir, f"compliance_{slug(name)}.csv")
        write_csv(path, data, cols)
        written.append(path)
    return written


def build_spec_section(spec_rows):
    """'## Spec compliance' — one table per spec, quads down the side and requirements across, with
    the shortfalls spelled out underneath. The table answers "could I enter this quad?"; the list
    answers "what do I do about it?"."""
    if not spec_rows:
        return ""
    lines = ["", "## Spec compliance", "",
             "_Race-class requirements from `specs.csv`, checked against the newest dump and "
             f"`hardware.csv`. {SPEC_MARK['ok']} meets it, {SPEC_MARK['fail']} does not, "
             f"{SPEC_MARK['unknown']} not enough recorded to tell, {SPEC_MARK['manual']} can only "
             "be checked by hand. Each table is also written as `compliance_<spec>.csv`._", ""]
    for name, rules, entries in spec_rows:
        scope = next(((r.get('applies_class', ''), r.get('applies_discipline', '')) for r in rules), ('', ''))
        head = f"### {spec_title(name)}"
        tag = " / ".join(x for x in scope if x)
        if tag:
            head += f" ({tag})"
        lines += [head, ""]
        src = next((r.get('source') for r in rules if r.get('source')), '')
        if src:
            lines += [f"_Rules: <{src}>_", ""]
        if not entries:
            lines += [f"_No quad currently matches {tag or 'this spec'}._", ""]
            continue
        lines.append("| Quad | " + " | ".join(r['requirement'] for r in rules) + " | Verdict |")
        lines.append("|---|" + "---|" * (len(rules) + 1))
        for e in entries:
            states = [s for s, _ in e['results']]
            verdict = spec_verdict(states)
            if states.count('fail'):
                verdict = f"**{verdict}**"
            lines.append(f"| {e['quad']} | " + " | ".join(SPEC_MARK[s] for s in states) +
                         f" | {verdict} |")
        lines.append("")
        for e in entries:
            gaps = [(rule, state, detail) for rule, (state, detail) in zip(rules, e['results'])
                    if state in ('fail', 'unknown')]
            if not gaps:
                continue
            lines.append(f"**{e['quad']}**")
            for rule, state, detail in gaps:
                verb = 'fails' if state == 'fail' else 'unconfirmed'
                lines.append(f"- {rule['requirement']} — {verb}: {md(detail)} "
                             f"(needs: {md(rule['rule'])})")
            lines.append("")
    return "\n".join(lines)


def build_hardware_section(path, latest_rows):
    """Optional '## Hardware' section from a hand-maintained hardware.csv. This data (ESC stack,
    motors, props, cell count) isn't in the Betaflight dumps, so it's curated separately and joined
    to quads by normalized name."""
    if not os.path.exists(path):
        return ""
    with open(path, newline='') as f:
        hw = list(csv.DictReader(f))
    if not hw:
        return ""
    known = {norm(r['quad']) for r in latest_rows}
    lines = ["", "## Hardware", "",
             "_Curated per-quad build details (not captured in Betaflight dumps), largely seeded from a "
             "hand-maintained spreadsheet. Edit `hardware.csv`; some rows may be stale (see notes)._",
             "",
             "| Quad | Cells | Weight | ESC / stack | Motors | Props | Camera | VTX | Notes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(hw, key=lambda r: r['quad'].lower()):
        star = "" if norm(r['quad']) in known else " *(no matching dump)*"
        lines.append(f"| {md(r.get('quad',''))}{star} | {md(r.get('cells',''))} | {md(r.get('weight',''))} | "
                     f"{md(r.get('esc_stack',''))} | {md(r.get('motors',''))} | {md(r.get('props',''))} | "
                     f"{md(r.get('camera',''))} | {md(r.get('vtx',''))} | {md(r.get('notes',''))} |")
    lines.append("")
    return "\n".join(lines)


def build_flights_section(path, aliases=None):
    """Optional '## Flights' section, built from flights.csv if it exists (produced by
    update_flights.py). Kept separate so this stdlib-only script never needs the blackbox parser.
    `aliases` folds logs recorded under a quad's former craft name into its current one."""
    if not os.path.exists(path):
        return ""
    with open(path, newline='') as f:
        flights = list(csv.DictReader(f))
    if not flights:
        return ""

    def num(v):
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    aliases = aliases or {}
    groups = {}
    for fl in flights:
        key = fl.get('craft') or fl.get('quad') or '?'
        key = aliases.get(norm(key), key)
        groups.setdefault(key, []).append(fl)

    lines = ["", "## Flights", "",
             "_From decoded Betaflight blackbox logs (see `flights.csv`). Raw `.BBL` logs are not "
             "committed._", ""]
    for quad in sorted(groups, key=str.lower):
        fs = sorted(groups[quad], key=lambda r: (r['date'], r['time']))
        tot_t = sum(num(f['duration_s']) for f in fs)
        tot_mah = sum(num(f['mah']) for f in fs)
        worst = max(fs, key=lambda f: num(f['sag_v']))
        flagged = [f for f in fs if f.get('flags')]
        head = (f"**{quad}** — {len(fs)} flight{'s' if len(fs) != 1 else ''}, "
                f"{tot_t:.0f}s total, {tot_mah:.0f} mAh total, "
                f"worst sag {num(worst['sag_v']):.2f}V ({worst['date']}).")
        if flagged:
            head += f"  ⚠️ {len(flagged)} flagged flight{'s' if len(flagged) != 1 else ''}."
        lines.append(head)
        lines.append("")
        lines.append("| Date | Dur | Batt | Min | Sag | Avg A | Peak A | mAh | Motor sat | Flags |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for f in fs:
            lines.append(f"| {f['date']} | {num(f['duration_s']):.0f}s | {f['cells']}S "
                         f"{f['v_start']}V | {f['v_min']}V | {num(f['sag_v']):.2f}V | "
                         f"{f['a_avg']}A | {f['a_peak']}A | {f['mah']} | {num(f['motor_sat_pct']):.1f}% | "
                         f"{f.get('flags') or '—'} |")
        lines.append("")
    return "\n".join(lines)


def main():
    rows, scanned = parse_dumps()
    if not rows:
        print(f"No BTFL_cli_*.txt dumps found in {SRC}", file=sys.stderr)
        sys.exit(1)
    latest_rows = latest_per_quad(rows)
    rate_rows = build_rate_rows(latest_rows, load_presets(PRESETS_CSV),
                                load_hw_map(HW_CSV, "rate_preset"))
    rates_view = [r for r in rate_rows if r['in_view']]
    mode_rows = build_mode_rows(latest_rows)
    spec_rows = build_spec_rows(load_specs(SPECS_CSV), latest_rows, load_hw_rows(HW_CSV))

    write_csv(OUT, rows)
    write_csv(OUT_LATEST, latest_rows)
    write_csv(OUT_RATES, rates_view, RATE_COLS)
    # LF keeps the Unicode text bars clean in Git diffs; csv's default CRLF looks like trailing
    # whitespace to `git diff --check` whenever every generated row changes.
    write_csv(OUT_MODES, compact_mode_groups(mode_rows), MODE_COLS, lineterminator='\n')
    compliance_files = write_compliance_csvs(spec_rows, SRC)
    with open(OUT_SUMMARY, 'w') as f:
        # Checks see every quad; the tables show only the ones worth comparing.
        f.write(build_summary(latest_rows, rate_rows, spec_rows).rstrip() + "\n")
        f.write(build_rates_section(rates_view, len(rate_rows)))
        f.write(build_spec_section(spec_rows))
        f.write(build_hardware_section(HW_CSV, latest_rows))
        f.write(build_flights_section(os.path.join(SRC, "flights.csv"), load_aliases(HW_CSV)))

    dropped = scanned - len(rows)
    drift = sum(1 for r in rate_rows if r['preset_status'] == 'differs')
    print(f"Scanned {scanned} dumps -> {len(rows)} rows "
          f"({dropped} duplicate{'s' if dropped != 1 else ''} collapsed) -> {len(latest_rows)} quads")
    if drift:
        print(f"  {drift} quad{'s differ' if drift != 1 else ' differs'} from their rate_preset")
    for name, rules, entries in spec_rows:
        bad = sum(1 for e in entries if any(s == 'fail' for s, _ in e['results']))
        if bad:
            print(f"  {bad} of {len(entries)} quad{'s' if len(entries) != 1 else ''} "
                  f"in scope fail {spec_title(name)}")
    print(f"  {OUT}")
    print(f"  {OUT_LATEST}")
    print(f"  {OUT_RATES}")
    print(f"  {OUT_MODES}")
    for p in compliance_files:
        print(f"  {p}")
    print(f"  {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
