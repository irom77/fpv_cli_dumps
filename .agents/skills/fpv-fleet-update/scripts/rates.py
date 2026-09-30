"""Decode Betaflight stored rate integers into real angular rates (deg/s).

A `diff all` dump records only settings that differ from firmware defaults, so a quad left on stock
rates carries no rate lines at all — and "stock" is not one thing. The default rate type flipped
between firmware generations, so the same empty dump means different stick behaviour depending on
which version wrote it:

    <= 4.2.x   BETAFLIGHT, rc_rate 100 / srate 70 / expo 0   -> center 200 deg/s, max ~667
    >= 4.3.x   ACTUAL,     rc_rate 7   / srate 67 / expo 0   -> center  70 deg/s, max  670

This module fills the version-correct defaults per axis and evaluates Betaflight's own rate curves,
so the inventory can report deg/s instead of raw integers whose meaning depends on the type.

Curve implementations mirror `applyActualRates()` / `applyBetaflightRates()` in
src/main/fc/rc.c. Defaults were read from `pgResetFn_controlRateProfiles` in
src/main/fc/controlrate_profile.c at tags 4.2.3, 4.3.1, 4.4.2 and 4.5.1.

No I/O here — callers pass in the raw strings they scraped from a dump.
"""
import re

# Betaflight constants (src/main/fc/rc.c).
SETPOINT_RATE_LIMIT = 1998.0
RC_RATE_INCREMENTAL = 14.54

# Stock rateprofile per firmware generation, keyed by the first version that used it.
RATE_DEFAULTS = {
    (0, 0): {'rates_type': 'BETAFLIGHT', 'rc_rate': 100, 'srate': 70, 'expo': 0},
    (4, 3): {'rates_type': 'ACTUAL', 'rc_rate': 7, 'srate': 67, 'expo': 0},
}

SUPPORTED_TYPES = ('BETAFLIGHT', 'ACTUAL')
AXES = ('roll', 'pitch', 'yaw')


def version_key(bf_version):
    """(major, minor) from a version string, or None. Handles fork/date-style versions:
    '4.5.1' -> (4,5); '4.5.2.KAACK_V15' -> (4,5); '2025.12.3-alpha.KAACK_V19' -> (2025,12)."""
    m = re.match(r'\s*(\d+)\.(\d+)', bf_version or '')
    return (int(m.group(1)), int(m.group(2))) if m else None


def defaults_for(bf_version):
    """Stock rate values for the firmware that wrote a dump. Unknown/unparseable versions get the
    modern defaults — every current build is >= 4.3, and guessing old on an unreadable version
    string would silently misreport a quad as far twitchier than it is."""
    key = version_key(bf_version)
    if key is not None and key < (4, 3):
        return RATE_DEFAULTS[(0, 0)]
    return RATE_DEFAULTS[(4, 3)]


def _actual(x, rc_rate, srate, expo):
    """applyActualRates(): rc_rate is centre sensitivity/10, srate is max rate/10."""
    xa = abs(x)
    e = expo / 100.0
    expof = xa * (x ** 5 * e + x * (1 - e))
    center = rc_rate * 10.0
    stick_movement = max(0.0, srate * 10.0 - center)
    return x * center + stick_movement * expof


def _betaflight(x, rc_rate, srate, expo):
    """applyBetaflightRates(). Note the super-rate factor uses the ORIGINAL |stick|, not the
    expo-shaped value — mirroring the firmware, which passes rcCommandfAbs in separately."""
    xa = abs(x)
    if expo:
        e = expo / 100.0
        x = x * (xa ** 3) * e + x * (1 - e)
    r = rc_rate / 100.0
    if r > 2.0:
        r += RC_RATE_INCREMENTAL * (r - 2.0)
    rate = 200.0 * r * x
    if srate:
        rate *= 1.0 / max(0.01, min(1.0, 1.0 - xa * (srate / 100.0)))
    return rate


def rate_at(stick, rc_rate, srate, expo, rates_type):
    """Commanded rotation rate (deg/s) at a stick deflection of `stick` (0..1). Returns None for
    rate types we don't implement (QUICK/KISS/RACEFLIGHT) rather than reporting a wrong number."""
    if rates_type == 'ACTUAL':
        v = _actual(stick, rc_rate, srate, expo)
    elif rates_type == 'BETAFLIGHT':
        v = _betaflight(stick, rc_rate, srate, expo)
    else:
        return None
    return max(-SETPOINT_RATE_LIMIT, min(SETPOINT_RATE_LIMIT, v))


def center_sensitivity(rc_rate, expo, rates_type):
    """Slope of the rate curve at centre stick (deg/s per full-stick unit) — what Configurator
    shows as 'Center Sensitivity'. Taken analytically; sampling near zero overstates it because
    the expo/super term is only second-order there."""
    if rates_type == 'ACTUAL':
        return rc_rate * 10.0
    if rates_type == 'BETAFLIGHT':
        r = rc_rate / 100.0
        if r > 2.0:
            r += RC_RATE_INCREMENTAL * (r - 2.0)
        return 200.0 * r * (1 - expo / 100.0)
    return None


def split_triple(triple):
    """'95/80/80' -> ['95','80','80']; '//12' -> ['','','12'] (only yaw set); '' -> three blanks."""
    parts = (triple or '').split('/')
    parts += [''] * (3 - len(parts))
    return parts[:3]


def decode(rc_rate_rpy, super_rate_rpy, expo_rpy, rates_type, bf_version):
    """Decode one quad's active rateprofile into deg/s per axis.

    Blank fields are filled with this firmware's defaults, per axis — a dump like `//12` means only
    yaw was changed, so roll and pitch must still be reported at their stock values rather than
    dropped. Returns a dict with per-axis centre/max/curve points, plus `source`: 'default' when the
    dump set nothing at all (the quad is on stock rates), else 'dump'. There is deliberately no
    'partial' state — leaving expo at 0 is normal, and grading degrees of configuredness would
    conflate that with a quad where only one axis was touched. The decoded deg/s already show which
    axes actually differ. `supported` is False when the rate type has no implementation here.
    """
    d = defaults_for(bf_version)
    rtype = (rates_type or '').strip().upper() or d['rates_type']
    rcs, srs, exs = split_triple(rc_rate_rpy), split_triple(super_rate_rpy), split_triple(expo_rpy)

    set_count = 0
    axes = {}
    for i, axis in enumerate(AXES):
        vals = {}
        for name, raw, dflt in (('rc_rate', rcs[i], d['rc_rate']),
                                ('srate', srs[i], d['srate']),
                                ('expo', exs[i], d['expo'])):
            try:
                vals[name] = int(raw)
                set_count += 1
            except (TypeError, ValueError):
                vals[name] = dflt
        axes[axis] = vals

    supported = rtype in SUPPORTED_TYPES
    out = {
        'rates_type': rtype,
        'type_from_dump': bool((rates_type or '').strip()),
        'supported': supported,
        'source': 'default' if set_count == 0 else 'dump',
        'axes': {},
    }
    for axis, v in axes.items():
        out['axes'][axis] = {
            'rc_rate': v['rc_rate'],
            'srate': v['srate'],
            'expo': v['expo'],
            'center': center_sensitivity(v['rc_rate'], v['expo'], rtype) if supported else None,
            'max': rate_at(1.0, v['rc_rate'], v['srate'], v['expo'], rtype) if supported else None,
            'curve': {p: rate_at(p / 100.0, v['rc_rate'], v['srate'], v['expo'], rtype)
                      for p in (25, 50, 75)} if supported else {},
        }
    return out


def triple_of(decoded, field, fmt='{:.0f}'):
    """Render one decoded field across roll/pitch/yaw as the repo's 'r/p/y' string."""
    parts = []
    for axis in AXES:
        v = decoded['axes'][axis].get(field)
        parts.append(fmt.format(v) if isinstance(v, (int, float)) else '')
    return '/'.join(parts) if any(parts) else ''


def curve_triple(decoded, pct):
    parts = []
    for axis in AXES:
        v = decoded['axes'][axis].get('curve', {}).get(pct)
        parts.append(f"{v:.0f}" if isinstance(v, (int, float)) else '')
    return '/'.join(parts) if any(parts) else ''


def inert_max_rate(decoded):
    """Axes where an ACTUAL profile's centre sensitivity meets or exceeds its max rate.

    Under ACTUAL the curve is `x*centre + max(0, maxRate - centre)*expo_curve`, so once centre
    reaches maxRate the max-rate setting stops doing anything and the stick goes linear to a
    ceiling of `centre`. In practice this means rc_rate values authored for BETAFLIGHT rates
    (where 100 = 1.0x) were left behind on a profile that is now interpreted as ACTUAL (where
    100 = 1000 deg/s centre) — a firmware-upgrade footgun that raw stored integers hide.
    """
    if decoded['rates_type'] != 'ACTUAL':
        return []
    return [a for a in AXES
            if decoded['axes'][a]['rc_rate'] * 10.0 >= decoded['axes'][a]['srate'] * 10.0]


def raw_signature(decoded):
    """Normalized (type, rc/rc/rc, sr/sr/sr, expo/expo/expo) with defaults filled — the form used to
    compare a quad against a preset. Comparing filled values (not the raw dump text) means a quad
    that happens to set a value explicitly still matches a preset that leaves it at default."""
    return (
        decoded['rates_type'],
        '/'.join(str(decoded['axes'][a]['rc_rate']) for a in AXES),
        '/'.join(str(decoded['axes'][a]['srate']) for a in AXES),
        '/'.join(str(decoded['axes'][a]['expo']) for a in AXES),
    )


def _selftest():
    """Run with `python3 rates.py` to check the curves against known-good values.

    Expected numbers were derived from the firmware formulas and cross-checked against real dumps
    in this repo, so a regression here means the decode drifted from Betaflight's behaviour."""
    def close(got, want, tol=1.0):
        assert got is not None and abs(got - want) <= tol, f"got {got}, want {want}"

    # 4.5.1 stock: ACTUAL 7/67/0 -> centre 70, max 670.
    d = decode('', '', '', '', '4.5.1')
    assert d['rates_type'] == 'ACTUAL' and d['source'] == 'default'
    close(d['axes']['roll']['center'], 70)
    close(d['axes']['roll']['max'], 670)
    close(d['axes']['roll']['curve'][50], 185)

    # 4.2.3 stock: the pre-4.3 default was BETAFLIGHT 100/70/0 -> centre 200, max ~667.
    d = decode('', '', '', '', '4.2.3')
    assert d['rates_type'] == 'BETAFLIGHT'
    close(d['axes']['roll']['center'], 200)
    close(d['axes']['roll']['max'], 666.7)

    # openracer2's house race rate: roll 633, pitch/yaw 533 deg/s.
    d = decode('95/80/80', '70/70/70', '', 'BETAFLIGHT', '4.5.1')
    close(d['axes']['roll']['max'], 633.3)
    close(d['axes']['pitch']['max'], 533.3)
    close(d['axes']['roll']['center'], 190)

    # Partial dump (`//12`): unset axes must fall back to firmware default, not vanish.
    d = decode('//12', '64/64/72', '35/35/15', '', '4.4.2')
    close(d['axes']['roll']['center'], 70)     # inherited
    close(d['axes']['yaw']['center'], 120)     # explicit
    assert d['source'] == 'dump'

    # Expo must soften mid-stick without moving the endpoints.
    a = decode('95/80/80', '70/70/70', '0/0/0', 'BETAFLIGHT', '4.5.1')['axes']['roll']
    b = decode('95/80/80', '70/70/70', '50/50/50', 'BETAFLIGHT', '4.5.1')['axes']['roll']
    assert b['curve'][50] < a['curve'][50], "expo should reduce mid-stick rate"
    close(b['max'], a['max'])

    # An ACTUAL profile carrying BETAFLIGHT-era rc_rates makes max-rate inert.
    assert inert_max_rate(decode('130/130/130', '67/67/67', '', '', '4.5.1')) == list(AXES)
    assert inert_max_rate(decode('95/80/80', '70/70/70', '', 'BETAFLIGHT', '4.5.1')) == []

    # Unimplemented rate types must report nothing rather than a wrong number.
    d = decode('', '', '', 'QUICK', '4.5.1')
    assert not d['supported'] and d['axes']['roll']['max'] is None

    print("rates.py self-test: all checks passed")


if __name__ == '__main__':
    _selftest()
