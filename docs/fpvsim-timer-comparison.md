# FPVSIM Timer comparison

## Bottom line

- **FPVSIM Timer:** best fit for simple, reliable single-channel practice with an off-the-shelf kit and auto-calibration.
- **PhobosLT:** the closest conceptual alternative—small, inexpensive, standalone, and browser-controlled—but fundamentally a single-channel timer.
- **RotorHazard:** the strongest choice for organized multi-pilot racing, event management, results, and recovery/editing of bad laps.
- **Chorus32-ESP32Laptimer:** a DIY multi-channel hardware project with LiveTime/Chorus API compatibility, but more dated and hands-on.

| Area | FPVSIM Timer | PhobosLT | RotorHazard | Chorus32 |
|---|---|---|---|---|
| Basic architecture | ESP32 timer node; commercial app | ESP32 + one RX5808 | Multiple RF nodes + Raspberry Pi server | ESP32 + one RX module per pilot |
| Simultaneous pilots | Single node/channel; Timer Multi supports up to 8 racers/nodes | Single node/channel | Designed for multi-node racing | Up to 6 pilots/device |
| RF method | 5.8 GHz RSSI peak detection | 5.8 GHz RSSI peak detection | 5.8 GHz video-signal RSSI detection | Chorus/RX5808 RSSI detection |
| Analog / digital video | Explicitly supports analog and HDZero | Explicitly supports analog, HDZero, and Walksnail | Verify hardware/receiver compatibility per build | Not clearly documented for modern digital systems |
| Calibration | App auto-calibration; manual enter/peak/leave thresholds | Manual enter/exit sliders with live RSSI graph | Visual calibration plus RSSI-history review and retroactive correction | Manual thresholds; auto RSSI setup is explicitly not implemented |
| False-lap control | Minimum lap time; maximum is derived as `minimum × 4` | Configurable minimum lap time | Filtering, tuning, manual lap deletion/reassignment | Threshold tuning and application-side correction |
| User interface | Dedicated desktop/mobile app; WiFi on the Kit V2 | ESP32-hosted web UI; no separate app required | Full browser-based race-control server | Web configuration plus Chorus/LiveTime apps |
| Race management | Basic race/lap history workflow | Start/stop/clear laps and announcements | Pilots, heats, classes, formats, staging, scoring, teams, statistics | Depends heavily on Chorus app or LiveTime |
| Audio | App beeps and channel announcements; race feedback | Browser voice callouts, optional beeper, pilot names | LED/audio race events and callouts | Depends on connected application |
| Data/API ecosystem | No external API or LiveTime integration documented in the local FPVSIM notes | Future RotorHazard integration is listed, not core functionality | JSON API and LiveTime output | Chorus API; LiveTime-compatible |
| Setup burden | Lowest if you already own the kit | Moderate DIY build | Highest system complexity | Moderate/high DIY electronics and software |
| Best use | One pilot, one channel, repeatable practice | Tiny-whoop/home practice | Club racing and formal events | DIY multi-channel experimentation |

## Shared technical model

All four systems detect a quad by watching the received 5.8 GHz signal rise as it passes the timing point, then fall afterward. They are therefore sensitive to VTX power and thermal behavior, timer placement, multipath and nearby flight, threshold calibration, and multiple transmitters on shared or adjacent channels.

They are not transponder systems. A quad must be transmitting on a channel that the receiver or node is monitoring.

## FPVSIM versus PhobosLT

These are the closest matches.

PhobosLT uses an ESP32 and RX5808, exposes a local WiFi access point, and provides browser-based configuration, live RSSI, calibration, lap history, voice announcements, and minimum-lap filtering. Its project documentation explicitly describes it as a single-node timer. See the [PhobosLT documentation](https://github.com/phobos-/PhobosLT).

FPVSIM has a more polished product workflow:

- dedicated desktop/mobile app;
- documented auto-calibration;
- race-format controls;
- RSSI history review;
- explicit analog and HDZero support; and
- firmware support for Timer Multi and up to eight racers.

For the current R8 fleet, FPVSIM's main operational limitation remains the same as PhobosLT's: with one receiver node on R8, only one quad should be transmitting on that monitored frequency at a time. The FPVSIM app's minimum/maximum lap-window behavior is more restrictive than PhobosLT's because changing minimum lap time also forces the maximum to four times that value.

## FPVSIM versus RotorHazard

RotorHazard is a complete race-management platform rather than merely a lap timer. Its Raspberry Pi server coordinates multiple RF nodes, serves a browser UI, manages pilots, heats, and classes, supports race formats and team racing, provides APIs, exports timing data, and can recover or correct laps using RSSI history. See the [RotorHazard overview](https://rotorhazard.com/) and [RotorHazard user guide](https://github.com/RotorHazard/RotorHazard/blob/main/doc/User%20Guide.md).

FPVSIM is much easier for casual use, but RotorHazard is substantially better when you need:

- several pilots in the air simultaneously;
- separate receiver channels per pilot;
- formal heats and race starts;
- automated standings;
- team racing;
- post-race correction and auditing; or
- integration with external scoring or broadcast software.

The tradeoff is hardware, configuration, and Raspberry Pi/network complexity.

## FPVSIM versus Chorus32

Chorus32 is closer to a DIY hardware platform than a finished consumer product. Each pilot gets an RX module, with one ESP32 handling up to six pilots because of ADC limitations. It supports WiFi/Bluetooth and the Chorus RF Laptimer API, with LiveTime compatibility. See the [Chorus32 repository](https://github.com/AlessandroAU/Chorus32-ESP32LapTimer).

Its disadvantages relative to FPVSIM are:

- manual RSSI thresholds;
- incomplete installation documentation;
- firmware and web assets often built manually;
- wireless LiveTime use requiring a serial-to-UDP bridge;
- more wiring and electronics work; and
- unclear modern HD-video compatibility.

Its advantage is multi-channel capability at relatively low hardware cost, especially if you want to build and customize the system yourself.

## Recommendation for this setup

For the current R8 fleet:

1. Keep **FPVSIM** for solo practice and sequential flying on 5917 MHz.
2. Choose **PhobosLT** only if low cost, portability, and an open DIY design matter more than commercial polish.
3. Choose **RotorHazard** if the goal is simultaneous multi-pilot racing, organized heats, or future event management.
4. Choose **Chorus32** mainly if you specifically want a DIY multi-channel project and are comfortable maintaining older tooling.

The practical upgrade path is:

**FPVSIM for personal practice → RotorHazard for club/event racing.**

## RotorHazard OSD option for HDZero goggles

RotorHazard can send race messages to compatible pilot OSD systems. For HDZero, the current path is:

**RotorHazard server → ELRS Timer Backpack → HDZero goggles' ELRS backpack → HDZero OSD**

The current integration is the `VRxC_ELRS` RotorHazard plugin, not the older `rotorhazard-msp-osd-injector`. The older MSP injector repository is marked deprecated for users with an ELRS backpack or HDZero goggles; it points those users to `VRxC_ELRS` instead.

The documented HDZero setup requires:

- RotorHazard **4.1.0 or newer**;
- a RotorHazard timing system and server, normally a Raspberry Pi;
- an ELRS Timer Backpack connected to the RotorHazard server by USB or UART;
- HDZero goggles with their internal ExpressLRS/ELRS backpack updated with Backpack firmware **1.5.0 or newer**;
- matching backpack bind phrases for the pilot and goggles; and
- the `VRxC_ELRS` plugin installed in RotorHazard.

The plugin can display current lap, position, gap, lap result, staging, race-start, and post-race messages. The race director's transmitter does not need an ELRS backpack merely to receive pilot OSD messages; that is only needed if the director also wants to start or stop races from the transmitter.

See the [`VRxC_ELRS` documentation](https://github.com/i-am-grub/VRxC_ELRS) for the current setup requirements. The plugin documentation states that HDZero is currently the supported device for receiving these OSD race messages. RotorHazard's [plugin list](https://github.com/RotorHazard/RotorHazard/wiki/Available-Plugins) identifies the ELRS Backpack integration under OSD and VRx Control.

### Buying a RotorHazard system

The lowest-risk route is a prebuilt **NuclearHazard Fission Complete** timer. It is sold in 4- and 8-channel versions and includes the Raspberry Pi, SD card, case, and RX5808 receivers. The 4-channel version is sufficient for four simultaneous pilots; the 8-channel version provides more capacity.

For the HDZero OSD path, add or specify a separate USB-connected ESP32 ELRS Timer Backpack. This is particularly important with a Pi 5, where a USB-connected backpack is recommended rather than relying on an onboard ESP32 footprint.

Check current stock before ordering because RX5808 availability can affect delivery. See the [NuclearQuads shop](https://nuclearquads.com/shop/shop) and the [Fission Complete product page](https://nuclearq.myshopify.com/products/nuclearhazard-fission-complete-fpv-race-event-timer).

### Building a RotorHazard system

RotorHazard's [hardware build resources](https://github.com/RotorHazard/RotorHazard/tree/main/resources) document several supported designs:

- **S32_BPill:** full-featured DIY build supporting up to eight receivers;
- **NuclearHazard Core:** compact PCB-based build with relatively simple assembly;
- **Arduino PCB:** older DIY design;
- **USB Nodes:** receiver nodes connected to an existing server; and
- **Delta 5:** supported for existing hardware but not recommended for a new build.

A normal DIY build needs a Raspberry Pi and SD card, timing controller/PCB, one SPI-modified RX5808 receiver per pilot/channel, power and wiring, an enclosure, and RotorHazard software. The OSD feature additionally needs an ELRS Timer Backpack, flashed with the RotorHazard Backpack target, and the HDZero goggles' backpack firmware.

For this project, the practical choice is therefore:

**Buy a Fission Complete + USB ELRS Timer Backpack** for the shortest path to HDZero OSD. Build an S32_BPill or NuclearHazard Core only if you want to source parts and assemble the timing hardware yourself.
