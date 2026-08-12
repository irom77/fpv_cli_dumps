# Betaflight CLI Snippets

Reusable Betaflight CLI settings distilled from the fleet backups in [`backups/`](backups/).

## Before using a snippet

1. Connect the quad and save a fresh `diff all` backup.
2. Paste only the snippet matching the video system and firmware.
3. Check the CLI for `Invalid name` or `Invalid value` messages before entering `save`.
4. Reconnect after the reboot and verify the OSD in goggles before flying.

The OSD position numbers encode coordinates and OSD-profile visibility. They are not portable
between the analog `30x13` and digital `50x18` canvases, so keep those layouts separate.

VTX band, channel, power, UART assignment, receiver configuration, craft name, alarms, and other
hardware-specific settings are deliberately excluded.

## OSD

### Digital — HDZero or DJI MSP DisplayPort

This `50x18` layout is the common pattern found across the digital fleet, especially the Mob6 race
configurations. The FC must already have the correct UART configured for MSP DisplayPort; this
snippet intentionally does not set `displayport_msp_serial` or any UART `serial` line.

```text
feature OSD

set osd_tim2 = 2563

set osd_link_quality_pos = 2093
set osd_rssi_dbm_pos = 2101
set osd_vtx_channel_pos = 2081

set osd_tim_1_pos = 3243
set osd_tim_2_pos = 3275

set osd_vbat_pos = 2433
set osd_avg_cell_voltage_pos = 2465

set osd_rate_profile_name_pos = 2241
set osd_core_temp_pos = 14375

set osd_disarmed_pos = 2545
set osd_warnings_pos = 14833
set osd_flymode_pos = 2557
set osd_pilot_name_pos = 2561
set osd_craft_name_pos = 2578

set osd_displayport_device = MSP
set osd_canvas_width = 50
set osd_canvas_height = 18
set vcd_video_system = HD

save
```

### Analog

This `30x13` layout combines the recurring AIR65, Diamond, QAS JB, and OpenRacer2 pattern. Video
detection remains `AUTO` so the snippet does not unnecessarily force NTSC or PAL.

```text
feature OSD

set osd_tim2 = 2563

set osd_vtx_channel_pos = 2049
set osd_rssi_dbm_pos = 2059
set osd_link_quality_pos = 2067

set osd_tim_1_pos = 2200
set osd_tim_2_pos = 2232

set osd_rate_profile_name_pos = 2209

set osd_vbat_pos = 2369
set osd_avg_cell_voltage_pos = 2401

set osd_disarmed_pos = 2408
set osd_warnings_pos = 14729
set osd_flymode_pos = 2457
set osd_pilot_name_pos = 2433
set osd_craft_name_pos = 2447

set osd_displayport_device = AUTO
set osd_canvas_width = 30
set osd_canvas_height = 13
set vcd_video_system = AUTO

save
```

## Rates

Rate snippets will be added here. Keep each named preset in its own subsection and document:

- Betaflight rates type (`ACTUAL`, `BETAFLIGHT`, etc.)
- Intended craft class and use
- Expected roll, pitch, and yaw maximum rates
- The rate profile slot affected by the snippet

## Future snippets

Possible additions include modes, battery thresholds, receiver defaults, race settings, and
blackbox configuration. Hardware-dependent settings should remain clearly separated from portable
fleet defaults.
