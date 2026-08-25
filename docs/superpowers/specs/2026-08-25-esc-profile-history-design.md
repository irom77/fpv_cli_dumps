# ESC Profile History Design

## Purpose

Store dated ESC controller and per-channel configuration observations for FPV quads without overloading `hardware.csv`. The first recorded snapshot will describe the HobbyWing XRotor 65A AM32 ESC in PROSPEC.

These records document what an ESC configuration tool reported at a point in time. They do not establish actual motor or propeller direction; physical rotation must still be verified props-off before flight.

## Scope

This change adds:

- `esc_profiles.csv`, containing one row for each dated ESC inspection or configuration snapshot.
- `esc_channels.csv`, containing the channel observations belonging to a snapshot.
- A short reference in the PROSPEC row of `hardware.csv` indicating that detailed ESC configuration history is available in the two ESC CSV files.
- Automated validation of identifiers, references, channel coverage, and controlled values.

It does not change Betaflight configuration, firmware, backups, or motor direction settings.

## Domain Model

An **ESC profile snapshot** is a dated observation of controller-wide hardware, connection, firmware-schema, and configuration details for one quad.

An **ESC channel observation** records the reported configuration of one channel in a profile snapshot. It belongs to exactly one snapshot through `profile_id`.

The stable identifier format is `<QUAD>-<YYYYMMDD>-ESC-<FIRMWARE>-<VERSION>`. The initial snapshot uses `PROSPEC-20260825-ESC-AM32-219`.

## CSV Schemas

### `esc_profiles.csv`

The file has these columns:

| Column | Meaning |
| --- | --- |
| `profile_id` | Unique snapshot identifier. |
| `quad` | Quad name matching the `quad` field in `hardware.csv`. |
| `observed_at` | Observation date in `YYYY-MM-DD` format. |
| `usb_interface` | USB VID:PID and a concise interface description. |
| `baud_rate` | Connection baud rate as an integer. |
| `mcu` | ESC MCU model and relevant architecture details. |
| `bootloader_pin` | Signal pin used for bootloader communication. |
| `bootloader_version` | Reported bootloader version. |
| `eeprom_schema` | Reported EEPROM layout/schema. |
| `input_protocol` | Reported ESC input protocol setting. |
| `stick_calibration` | `enabled`, `disabled`, or `unknown`. |
| `write_verification` | Concise result of write/read verification. |
| `notes` | Additional controller-wide context and safety qualifications. |

The initial PROSPEC row records USB `0x0483:0x5740` via flight-controller passthrough, 115200 baud, AT32F421 at 120 MHz, bootloader pin PA2 and version 15, EEPROM layout v3 for AM32 2.19, automatic input protocol, enabled stick calibration, and successful verification across all four channels.

### `esc_channels.csv`

The file has these columns:

| Column | Meaning |
| --- | --- |
| `profile_id` | Foreign key to `esc_profiles.csv`. |
| `channel` | Positive integer ESC channel number. |
| `hardware_target` | Reported ESC firmware target. |
| `firmware` | Reported firmware name and version. |
| `rotation` | `normal`, `reversed`, or `unknown`, representing the ESC setting only. |
| `mode_3d` | `on`, `off`, or `unknown`. |
| `signal_status` | Reported connection/synchronization state. |
| `notes` | Channel-specific qualifications. |

The initial PROSPEC snapshot contains exactly four rows. All use target `XROTOR65_F421`, firmware `AM32 v2.19`, 3D mode off, and synchronized/green signal status. Channels 1, 3, and 4 report reversed rotation; channel 2 reports normal rotation.

## `hardware.csv` Integration

The existing PROSPEC hardware row remains the concise current hardware summary. Its `notes` field receives a short reference to `esc_profiles.csv` and `esc_channels.csv`; detailed controller and channel data are not duplicated there.

The snapshot's `quad` value must match an existing `hardware.csv` quad name. This keeps the detailed history attached to inventory while allowing multiple dated snapshots for the same quad.

## Validation

Repository validation will enforce:

- Every `profile_id` is non-empty and unique in `esc_profiles.csv`.
- Every profile refers to a quad present in `hardware.csv`.
- Every channel row refers to an existing profile.
- Each `(profile_id, channel)` pair is unique.
- Each profile has channels 1 through 4 exactly once for the current four-in-one ESC use case.
- `rotation` is one of `normal`, `reversed`, or `unknown`.
- `mode_3d` is one of `on`, `off`, or `unknown`.
- `stick_calibration` is one of `enabled`, `disabled`, or `unknown`.
- Dates and integer fields are parseable in their documented formats.

Validation errors identify the file, row, and invalid field or relationship so corrections are straightforward.

## Safety and Data Interpretation

Rotation values are reported ESC settings, not verified physical motor directions. Wiring and motor construction can change the relationship between an ESC setting and actual shaft rotation. The PROSPEC profile notes will therefore state that the unusual three-reversed/one-normal pattern must be checked with the Betaflight Motor Wizard or equivalent props-off test before props are installed.

## Acceptance Criteria

- Both CSV files exist with the documented headers and initial PROSPEC data.
- PROSPEC has profile ID `PROSPEC-20260825-ESC-AM32-219` and four linked channel rows.
- The PROSPEC `hardware.csv` row points readers to the detailed ESC history.
- Validation accepts the committed data and detects broken references, duplicate or missing channels, and unsupported controlled values.
- No Betaflight backup, firmware image, or flight-controller setting is modified.
