# ESC Profile History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add normalized, dated ESC profile and per-channel history for PROSPEC with automated CSV validation.

**Architecture:** Two hand-maintained CSV files separate controller-wide snapshots from channel observations and join on `profile_id`. A standard-library Python validator owns schema, relationship, controlled-value, and four-channel checks; pytest verifies both the validator's failure cases and the committed PROSPEC records.

**Tech Stack:** CSV, Python 3 standard library, pytest, Markdown

**Spec:** `docs/superpowers/specs/2026-08-25-esc-profile-history-design.md`

## Global Constraints

- Profile IDs use `<QUAD>-<YYYYMMDD>-ESC-<FIRMWARE>-<VERSION>`.
- The initial profile ID is exactly `PROSPEC-20260825-ESC-AM32-219`.
- Rotation is an observed ESC setting, not proof of physical motor direction.
- Every current profile represents a four-in-one ESC and must contain channels 1 through 4 exactly once.
- Runtime validation uses only the Python 3 standard library.
- Betaflight backups, firmware images, and flight-controller settings must not change.

## File Structure

- Create `tools/validate_esc_profiles.py`: reusable CSV loader and complete ESC-history validator with a command-line entry point.
- Create `tests/test_esc_profiles.py`: validator failure-case tests and assertions over the committed PROSPEC snapshot.
- Create `esc_profiles.csv`: one row per dated controller-wide snapshot.
- Create `esc_channels.csv`: one row per channel observation linked through `profile_id`.
- Modify `hardware.csv`: add the detailed-history reference to PROSPEC's notes only.
- Modify `README.md`: list and explain the two hand-maintained ESC history files and their safety semantics.

---

### Task 1: ESC History Validator

**Files:**
- Create: `tools/validate_esc_profiles.py`
- Create: `tests/test_esc_profiles.py`

**Interfaces:**
- Consumes: paths to `hardware.csv`, `esc_profiles.csv`, and `esc_channels.csv`.
- Produces: `validate(hardware_path: Path, profiles_path: Path, channels_path: Path) -> list[str]`, returning human-readable errors; CLI exit code `0` for valid data and `1` with one error per stderr line for invalid data.

- [ ] **Step 1: Write failing tests for valid and invalid relationships**

Create temporary CSV fixtures in `tests/test_esc_profiles.py` with a helper that writes the exact documented headers. Add tests asserting:

```python
from pathlib import Path

from tools.validate_esc_profiles import validate


def test_valid_four_channel_profile_has_no_errors(tmp_path):
    hardware, profiles, channels = write_fixture(tmp_path)
    assert validate(hardware, profiles, channels) == []


def test_rejects_unknown_quad_and_broken_profile_reference(tmp_path):
    hardware, profiles, channels = write_fixture(
        tmp_path,
        profile_quad="MISSING",
        channel_profile_id="UNKNOWN-PROFILE",
    )
    errors = validate(hardware, profiles, channels)
    assert any("quad 'MISSING' is not present in hardware.csv" in error for error in errors)
    assert any("profile_id 'UNKNOWN-PROFILE' is not present in esc_profiles.csv" in error for error in errors)


def test_rejects_duplicate_and_missing_channels(tmp_path):
    hardware, profiles, channels = write_fixture(tmp_path, channel_numbers=(1, 2, 2, 4))
    errors = validate(hardware, profiles, channels)
    assert any("duplicate channel 2" in error for error in errors)
    assert any("must contain channels 1,2,3,4 exactly once" in error for error in errors)
```

Also cover duplicate profile IDs, invalid `observed_at`, non-integer `baud_rate`, invalid `stick_calibration`, invalid `rotation`, and invalid `mode_3d`.

- [ ] **Step 2: Run the focused tests and verify the import fails**

Run: `.venv/bin/pytest tests/test_esc_profiles.py -v`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'tools.validate_esc_profiles'`.

- [ ] **Step 3: Implement the minimal validator**

In `tools/validate_esc_profiles.py`, define the exact headers and controlled sets:

```python
PROFILE_FIELDS = (
    "profile_id", "quad", "observed_at", "usb_interface", "baud_rate",
    "mcu", "bootloader_pin", "bootloader_version", "eeprom_schema",
    "input_protocol", "stick_calibration", "write_verification", "notes",
)
CHANNEL_FIELDS = (
    "profile_id", "channel", "hardware_target", "firmware", "rotation",
    "mode_3d", "signal_status", "notes",
)
ROTATIONS = {"normal", "reversed", "unknown"}
MODES_3D = {"on", "off", "unknown"}
STICK_CALIBRATION = {"enabled", "disabled", "unknown"}
```

Implement `_read_rows(path: Path, expected_fields: tuple[str, ...]) -> tuple[list[dict[str, str]], list[str]]` using `csv.DictReader`. Report a header mismatch with the filename and expected header.

Implement `validate(...)` to accumulate, rather than raise, errors. Include source filename and one-based CSV row number for field errors. Parse dates with `datetime.date.fromisoformat`, parse baud and channel with `int`, validate foreign keys and controlled values, detect duplicate profile IDs and `(profile_id, channel)` pairs, then compare each known profile's channel set and row count with `[1, 2, 3, 4]`.

Add:

```python
def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(
        root / "hardware.csv",
        root / "esc_profiles.csv",
        root / "esc_channels.csv",
    )
    for error in errors:
        print(error, file=sys.stderr)
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `.venv/bin/pytest tests/test_esc_profiles.py -v`

Expected: all validator unit tests PASS.

- [ ] **Step 5: Commit the validator**

```bash
git add tools/validate_esc_profiles.py tests/test_esc_profiles.py
git commit -m "Add ESC profile CSV validation"
```

### Task 2: PROSPEC ESC Snapshot and Repository Documentation

**Files:**
- Modify: `tests/test_esc_profiles.py`
- Create: `esc_profiles.csv`
- Create: `esc_channels.csv`
- Modify: `hardware.csv`
- Modify: `README.md`

**Interfaces:**
- Consumes: `validate(...)` from Task 1 and the existing `hardware.csv` PROSPEC key.
- Produces: profile `PROSPEC-20260825-ESC-AM32-219`, four linked channel rows, and discoverable repository documentation.

- [ ] **Step 1: Write the failing committed-data test**

Add constants for the repository CSV paths and a test that first calls `validate(...)`, then reads the two CSVs with `csv.DictReader` and asserts the exact PROSPEC values:

```python
def test_committed_prospec_snapshot_is_complete_and_valid():
    assert validate(HARDWARE, PROFILES, CHANNELS) == []
    profiles = list(csv.DictReader(PROFILES.open(newline="", encoding="utf-8")))
    channels = list(csv.DictReader(CHANNELS.open(newline="", encoding="utf-8")))

    profile = next(row for row in profiles if row["profile_id"] == PROFILE_ID)
    assert profile["quad"] == "PROSPEC"
    assert profile["observed_at"] == "2026-08-25"
    assert profile["baud_rate"] == "115200"
    assert profile["bootloader_pin"] == "PA2"
    assert profile["bootloader_version"] == "v15"
    assert profile["stick_calibration"] == "enabled"

    prospec_channels = [row for row in channels if row["profile_id"] == PROFILE_ID]
    assert {int(row["channel"]): row["rotation"] for row in prospec_channels} == {
        1: "reversed", 2: "normal", 3: "reversed", 4: "reversed",
    }
    assert {row["hardware_target"] for row in prospec_channels} == {"XROTOR65_F421"}
    assert {row["firmware"] for row in prospec_channels} == {"AM32 v2.19"}
```

- [ ] **Step 2: Run the committed-data test and verify it fails**

Run: `.venv/bin/pytest tests/test_esc_profiles.py::test_committed_prospec_snapshot_is_complete_and_valid -v`

Expected: FAIL because `esc_profiles.csv` and `esc_channels.csv` do not exist.

- [ ] **Step 3: Add the profile and channel CSV records**

Create `esc_profiles.csv` using the exact `PROFILE_FIELDS` header and one row with:

- `profile_id`: `PROSPEC-20260825-ESC-AM32-219`
- `quad`: `PROSPEC`
- `observed_at`: `2026-08-25`
- `usb_interface`: `0x0483:0x5740 (STM32 VCP via flight controller passthrough)`
- `baud_rate`: `115200`
- `mcu`: `Artery AT32F421 (Cortex-M4, 120MHz)`
- `bootloader_pin`: `PA2`
- `bootloader_version`: `v15`
- `eeprom_schema`: `Layout v3 (AM32 2.19 configuration structure)`
- `input_protocol`: `Auto (DShot300/DShot600 auto-detection)`
- `stick_calibration`: `enabled`
- `write_verification`: `successful on ESCs 1-4`
- `notes`: `Observed ESC settings only; verify physical motor rotation props-off before installing propellers.`

Create `esc_channels.csv` using the exact `CHANNEL_FIELDS` header and four rows. Each row uses target `XROTOR65_F421`, firmware `AM32 v2.19`, `mode_3d=off`, `signal_status=Synchronized (Green)`, and an empty `notes`; rotations are `reversed`, `normal`, `reversed`, `reversed` for channels 1 through 4.

- [ ] **Step 4: Add discoverability and safety documentation**

Append to PROSPEC's `hardware.csv` notes: `Detailed dated ESC settings: esc_profiles.csv and esc_channels.csv; verify physical motor rotation props-off.` Preserve every existing field and note.

Add both files to README's Layout block. Under Hardware details, add a paragraph explaining that controller-wide snapshots live in `esc_profiles.csv`, per-channel observations live in `esc_channels.csv`, rows join by `profile_id`, and rotation is reported configuration requiring props-off physical verification.

- [ ] **Step 5: Run focused validation and the complete test suite**

Run:

```bash
python3 tools/validate_esc_profiles.py
.venv/bin/pytest -v
git diff --check
```

Expected: validator exits `0` without output, all pytest tests PASS, and `git diff --check` exits `0` without output.

- [ ] **Step 6: Confirm protected artifacts did not change**

Run:

```bash
git diff --name-only -- backups upgrades
```

Expected: no output.

- [ ] **Step 7: Commit the data and documentation**

```bash
git add esc_profiles.csv esc_channels.csv hardware.csv README.md tests/test_esc_profiles.py
git commit -m "Record PROSPEC AM32 ESC profile"
```
