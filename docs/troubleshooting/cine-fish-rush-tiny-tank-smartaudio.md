# Cine-fish: Rush Tiny Tank video and SmartAudio troubleshooting

Session: 2026-09-18, America/New_York. Paused at the pilot's request; resume tomorrow.

## State at handoff

- **Original static-only video problem resolved:** the HDZero Monitor received camera video and Betaflight OSD on **A1 / 5865 MHz**. The VTX was not on the R8 channel requested in Betaflight.
- **SmartAudio remains unresolved:** Video Transmitter tab still reports **Device ready: false** after firmware replacement, backup restoration, and a full USB/battery power cycle.
- **New channel-control evidence:** changing the VTX band/channel in Betaflight changes the saved values and OSD text, but the transmitter remains on the previously observed A1 carrier (5865 MHz). This confirms that the FC UI/configuration state is changing without confirmed RF control of the VTX.
- **Post-restore status received:** live CLI reports `CONFIGURED`, BF 4.5.5, and build key `3b7d5fd28e6489c3dd138b3d7ee0fe7a`; CPU load is 31% with no `LOAD` arming flag. This verifies the running artifact and basic restored runtime state, but does not expose compile-time custom defines.
- Live firmware is **Betaflight 4.5.5, GEPRCF411_AIO**, verified by CLI and the app's connection log. Do not confuse app version 2026.6.2 with the installed FC firmware.
- DATA-to-T1 continuity was confirmed by the pilot. Live UART function and pin resource are correct. This confirms continuity/configuration, not electrical signal quality or working UART/VTX data hardware.
- Build metadata now independently verifies that the flashed artifact includes `USE_NONCOMPLIANT_SMARTAUDIO`.
- Latest repository full dump is still **pre-flash 4.5.2**. No post-flash 4.5.5 dump has been received. Do not edit historical dumps to claim they contain the new firmware or actual A1 channel.
- No flight-readiness or range test was completed. Latest explicit video/OSD confirmation was before flashing; recheck after restoration.

## Hardware and wiring

| Item | Confirmed information |
| --- | --- |
| Quad | Cine-fish, Flyfish30 frame; successor of CineLog30 |
| FC | GEPRCF411_AIO / GEPR, STM32F411; cataloged as GEPRC GEP-F411-35A AIO family |
| Camera | CaddxFPV Baby Ratel 2 analog camera, pilot identified |
| VTX | Rush Tiny Tank; red sticker identified by pilot as SmartAudio 2.1 |
| Receiver display | HDZero Monitor, using RF Auto; built-in analog reception |
| Radio receiver | CRSF configured on UART2 |
| VTX LEDs | Solid green; other LED repeats one red flash and one blue flash |

SmartAudio 2.1 is a **sticker identification**, not a detected protocol version in Betaflight. The installed Tiny Tank supersedes the old plan to install Mass's faulty Rush Tank Ultimate Mini. Do not conflate these units or transfer Mass's unresolved fault diagnosis to this VTX.

Pilot-supplied wiring (physical pad labels not independently inspected):

| Tiny Tank pad | FC connection | Camera connection |
| --- | --- | --- |
| +5V | FC 5V | Camera VCC |
| GND | FC GND | Camera GND |
| CAM | FC video input (VIDEO / VI in supplied table) | Camera VIDEO |
| VTX | FC video output (VOUT / VO in supplied table) | None |
| DATA | FC T1 / TX1 | None |

Camera power comes from the FC's 5V rail through the shared VTX pad. Reported video path is camera → FC analog OSD → VTX. Working video and FC OSD on A1 support that the video path operates. Never reuse the old Ultimate Mini's VBAT wiring instructions for this Tiny Tank.

## Backup files and evidence

Windows backup directory: `C:\Users\irekr\OneDrive\Documents\FPVBackup`.
WSL mount: `/mnt/c/Users/irekr/OneDrive/Documents/FPVBackup`.

- [14:19:34 full dump](../../backups/BTFL_cli_CINE-FISH_20260918_141934_GEPRCF411_AIO.txt): copied from Windows and byte-verified. BF 4.5.2, SmartAudio/UART1, VTX table present, but MSP/HD OSD remained.
- [14:35:15 full dump](../../backups/BTFL_cli_CINE-FISH_20260918_143515_GEPRCF411_AIO.txt): copied and byte-verified. Pilot initially called it `143548`, but the actual file found was `143515`. Analog OSD settings are present. This is the latest archived dump and the restoration baseline.
- VTX table preserved in the archived full dumps (the earlier local `rush_tiny_tank_vtxtable.json` is no longer present at commit time): five factory bands, eight channels; power values `14 20 23 25`, labels `25 100 200 350`. Labels are configuration data, not measured RF output.
- Separate corrected restore file created in Windows: `C:\Users\irekr\OneDrive\Documents\FPVBackup\CINE-FISH_restore_osd_units_fixed.txt`. It differs from the 14:35:15 original only by replacing empty `set osd_units =` with `set osd_units = METRIC`. It is not a new FC export and is not in the repository dump inventory.

Both September 18 archived dumps contain an empty `set osd_units =` line. Keep originals intact as evidence.

## Troubleshooting chronology

### 1. Analog OSD configuration

Initial live reads confirmed:

```text
osd_displayport_device = MSP
vcd_video_system = HD
```

Applied:

```text
set osd_displayport_device = MAX7456
set vcd_video_system = AUTO
save
```

The 14:35:15 dump confirms MAX7456, AUTO, and 30×13 canvas. Original canvas was 53×20. This corrected OSD selection but did not alone resolve static.

### 2. Video restored by matching the actual RF channel

- Pilot reported static; VTX LEDs were lit.
- Betaflight Video Transmitter tab showed Device ready=false.
- Saved requested settings were Raceband 8, 5917 MHz, power index 1. Those settings did not establish the VTX's actual RF channel.
- HDZero Monitor was in RF Auto. It detects analog/HDZero on the selected frequency; it does **not** scan channels automatically.
- Trying R1–R8 did not produce video.
- One red / one blue flash suggested A1; pilot selected A1 and confirmed camera video, then explicitly confirmed Betaflight OSD text.
- To select A1 on the monitor: hold F and press left/right to select band A; release F and press left/right to select channel 1.

The A1 reception result is the strongest channel evidence. LED colors alone were not sufficient proof of transmitted power or channel.

### 3. SmartAudio wiring and firmware test

- Pilot confirmed DATA is connected to T1 and then confirmed continuity with power disconnected.
- Original firmware: 4.5.2, STM32F411, board GEPRCF411_AIO.
- Betaflight documents `NONCOMPLIANT_SMARTAUDIO` as a build workaround for some 4.5.2 targets. The 4.5.5 source was inspected and retains the conditional workaround.
- Pilot could select 4.5.3 or 4.5.5, not 4.5.2. We selected 4.5.5 for this test.
- Screenshot 145326 shows GEPRCF411_AIO, 4.5.5, CRSF, Analog OSD, DSHOT, VTX, and custom define `NONCOMPLIANT_SMARTAUDIO`. Other selected options were Acro Trainer, GPS, LED Strip, and Pin IO; Core Only was off.
- Screenshot 145730 shows successful programming but also a visible 2026.6.2 version label. Assistant initially treated this as a possible firmware mismatch. Subsequent CLI and connection log unequivocally identify the installed FC firmware as 4.5.5; do not repeat the mismatch claim.

Installed CLI version:

```text
# Betaflight / STM32F411 (S411) 4.5.5 Sep 18 2026 / 18:54:40 (norevision) MSP API: 1.46
# config rev: 92c695a
# board: manufacturer_id: GEPR, board_name: GEPRCF411_AIO
```

Build key: `3b7d5fd28e6489c3dd138b3d7ee0fe7a`.

### 4. Restore failure and correction

Screenshot 150305 shows:

```text
set osd_units =
###ERROR IN set: INVALID VALUE###
Allowed values: IMPERIAL, METRIC, BRITISH
save
###ERROR IN save: ERRORS WERE DETECTED - PLEASE REVIEW BEFORE CONTINUING###
###ERROR IN save: PLEASE FIX ERRORS THEN 'SAVE'###
```

A corrected restore copy was prepared (path above). Pilot reported restoring the one with the error. We instructed:

```text
set osd_units = METRIC
save
```

After reconnecting, pilot confirmed:

```text
osd_units = METRIC
craft_name = Cine-fish
osd_craft_name_pos = 2461
```

These checks confirm specific restored values; they do not constitute a full config comparison. A new full dump is still needed to check restoration comprehensively.

### 5. Live UART and resource checks

After restoration and continued Device ready=false, pilot supplied:

```text
serial 20 1 115200 57600 0 115200
serial 0 2048 115200 57600 0 115200
serial 1 64 115200 57600 0 115200
serial 30 0 115200 19200 0 19200
```

UART1 is SmartAudio (`2048`), UART2 is serial RX (`64`); softserial is unassigned.

```text
resource SERIAL_TX 1 A09
resource SERIAL_RX 1 A10
resource SERIAL_TX 2 A02
resource SERIAL_RX 2 A03
resource SOFTSERIAL_TX 1 A00
resource SOFTSERIAL_RX 1 B10
resource MOTOR 5 A00
resource MOTOR 6 B10
resource LED_STRIP 1 A08
resource OSD_CS 1 B12
```

No duplicate A09 assignment was shown. Do not blindly enable default softserial pins: A00/B10 also appear as motor resources. UART2 is occupied by the receiver.

Pilot then disconnected both battery and USB for 10 seconds, powered battery first, waited, reconnected USB, and reported the same failure.

### 6. Build metadata verification

- Pilot could view logs but could not copy them.
- Screenshot 151613 is the general application log, showing September 17 Crux-fish/FPVM BETAFPVF4 entries. Its 404 is unrelated to this Cine-fish build.
- Screenshot 151754 shows September 18 Cine-fish reconnections on 4.5.5 with the correct build key, and craft_name present after restoration.
- General log's yellow `Device - Ready` means the FC completed rebooting; it is **not** the VTX tab's Device ready result.
- Pilot could not find Cloud Build Details. Stop repeatedly directing the pilot to the generic log viewer; it has not exposed compile options.
- Direct metadata URL:
  `https://build.betaflight.com/api/builds/3b7d5fd28e6489c3dd138b3d7ee0fe7a/json`
- Agent's Python request received HTTP 403; web tool also could not access it. This is not evidence that the build is absent.
- The build metadata endpoint was queried successfully for the running build key. It reports release `4.5.5`, target `GEPRCF411_AIO`, status `success`, and this option in the request:

  ```text
  USE_NONCOMPLIANT_SMARTAUDIO
  ```

This verifies that the compatibility workaround was compiled into the flashed firmware. It does
not prove that the DATA wire, UART electrical signaling, or VTX SmartAudio input is working.

### 7. Channel command does not move the transmitter

The pilot subsequently tested the behavior directly: selecting another band/channel in
Betaflight updates the channel shown in the OSD, but reception remains on the original A1
frequency. The configured `vtx_band`, `vtx_channel`, and `vtx_freq` values therefore describe
the FC's requested state; they do not prove that the Rush Tiny Tank accepted a SmartAudio
command or changed its RF carrier. This is consistent with `Device ready: false` and makes a
VTX-table or OSD-layout change an inadequate fix.

The observation narrows the unresolved fault to the SmartAudio path: the selected firmware
driver/build, UART electrical signaling and pin-level wiring, VTX DATA input, or the VTX's
SmartAudio implementation. It does not distinguish among those causes. DATA-to-T1 continuity
alone still cannot show that a valid bidirectional SmartAudio waveform reaches the VTX.

The post-restore status snapshot also shows `RXLOSS CLI MSP` arming flags while connected to the
Configurator. Those flags are expected for this bench session and are unrelated to SmartAudio.

Screenshots are external Windows artifacts, not copied into this repository:
`C:\Users\irekr\OneDrive\Pictures\Screenshots\Screenshot 2026-09-18 <timestamp>.png`.
Relevant timestamps: `145326`, `145730`, `150305`, `151613`, `151754`.

## Earlier status snapshot: do not treat as current post-restore state

Taken after flashing, before restoration was fully verified:

```text
MCU F411 Clock=108MHz (PLLP-HSE), Vref=3.29V, Core temp=30degC
Configuration: UNCONFIGURED, size: 3739, max available: 16384
GYRO=MPU6000, ACC=MPU6000
OSD: MAX7456 (30 x 13)
BUILD KEY: 3b7d5fd28e6489c3dd138b3d7ee0fe7a (4.5.5)
CPU:62%, cycle time: 125, GYRO rate: 8000, RX rate: 15, System rate: 9
Voltage: 372 * 0.01V (1S battery - OK)
I2C Errors: 0
FLASH: JEDEC ID=0x00ef4018 16M
GPS: NOT ENABLED
Arming disable flags: RXLOSS LOAD CLI MSP
```

3.72 V is not a normal 4S pack reading; power conditions for this snapshot were not established. `UNCONFIGURED` alone did not prove the entire restore failed. LOAD/RXLOSS need fresh assessment before flight. Saved baseline has `pid_process_denom = 1`; no loop-rate adjustment was made in this session.

## Resume plan

1. Build-option uncertainty is resolved: the build metadata confirms `USE_NONCOMPLIANT_SMARTAUDIO`. Do not reflash merely to test that option again.
2. Obtain a fresh **post-restore 4.5.5 dump all**, plus `version`, `status`, `flash_info`, and `tasks`. Archive it under its actual export filename and regenerate the fleet views. Compare key settings to the 14:35:15 baseline, especially receiver, motors, modes, rates, UART1, VTX table, OSD, and osd_units. Do not blindly replay a restore again.
3. Confirm battery-powered video and OSD still work on A1 after the upgrade; note exact VTX Type field and Device ready result. Test with props removed, VTX antenna attached, and airflow for extended bench operation.
4. The compile option is verified in the build metadata; focus remaining investigation on the physical SmartAudio path and VTX response.
5. With props removed, antenna attached, and battery power applied, capture the DATA/T1 line while issuing one deliberate channel change. Check for a waveform at the FC TX1 pad and at the VTX DATA pad; inspect the actual pad labels and common ground, and check for shorts with power removed. A logic analyzer/oscilloscope or a known-good SmartAudio device/FC is needed to separate wiring/driver failure from a VTX fault. These tests have **not** been done. Continuity alone does not establish valid data signaling.
6. Alternate UART/softserial or another firmware build are possible controlled tests, not approved diagnoses or completed work. Plan pin use carefully: only two hardware UARTs here, and UART2 carries CRSF. Preserve a current backup before changing anything.
7. Success criterion: Device ready=true with a detected SmartAudio version; a commanded channel change actually moves reception from A1 to the requested frequency, survives a power cycle, and video/OSD remain stable. Power labels, OSD text, and saved CLI values are not proof of RF output.

## Avoid repeating ineffective or unsupported advice

- HDZero Monitor has analog reception; no external analog module is needed for this setup.
- RF Auto is not automatic channel scan. Manual band/channel selection is required.
- A1 was confirmed by actual video; R8 was merely requested in the dump.
- Do not assume an OSD configuration fix necessarily fixes an RF channel mismatch.
- SmartAudio 2.1 does not require a separate UART peripheral choice: TBS SmartAudio is the correct selection.
- Do not claim the compatibility workaround fixed this VTX; it did not produce a ready device in the attempted build.
- Do not recommend `vtx_halfduplex` toggling without checking applicability: the inspected 4.5.5 SmartAudio initialization directly uses bidirectional serial flags; it did not reference that setting.
- Keep the archived original dumps unchanged. The blank osd_units export is a known defect with a separate corrected restore copy.

## Sources checked during this session

- [HDZero Monitor operation: manual band/channel selection, analog support, source behavior](https://docs.hd-zero.com/monitor-operation)
- [Betaflight SmartAudio documentation](https://betaflight.com/docs/wiki/guides/current/SmartAudio)
- [Betaflight cloud build options and SmartAudio workaround](https://betaflight.com/docs/development/API/Cloud-Build-API#smartaudio-bug) — documentation describes some 4.5.2 targets; it does not specifically prove this Tiny Tank/FC pair is affected.
- [Betaflight 4.5.5 SmartAudio driver](https://github.com/betaflight/betaflight/blob/4.5.5/src/main/io/vtx_smartaudio.c) — retains `USE_NONCOMPLIANT_SMARTAUDIO` conditional handling.
- [Betaflight 4.5.5 release](https://github.com/betaflight/betaflight/releases/tag/4.5.5)
- [Reported SmartAudio regression in 4.5.2](https://github.com/betaflight/betaflight/issues/14316) — a report on different hardware, not proof of our root cause.

## Follow-up: CPU overload and failed takeoffs

Reducing `pid_process_denom` to 2 cleared the LOAD arming block (CPU 63% to 32%). Subsequent takeoffs ended in recorded runaway takeoff disarms with uncontrolled yaw. The pilot subsequently reordered the motors and changed motor directions to props-out. The September 19 log records a successful short test ending with a switch disarm, without the earlier runaway behavior. See [Blackbox evidence and corrective actions](cine-fish-runaway-takeoff-20260918.md). Full-flight reliability remains unconfirmed; the SmartAudio issue is separate.
