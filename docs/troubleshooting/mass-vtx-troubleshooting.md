# Mass — VTX troubleshooting

**Status:** Video restored; Mass active as of 2026-09-10. TX800 R8 issue resolved by unlocking; original Rush fault remains unexplained.

## Hardware and evidence

- Quad: Mass, 3-inch; formerly SPEEDYBEEF405MINI.
- FC: SpeedyBee F405 Mini; latest saved dump is Betaflight 4.3.2:
  [2026-09-10 16:01 backup](../../backups/BTFL_cli_MASS_20260910_160154_SPEEDYBEEF405MINI.txt).
- Current VTX: SpeedyBee TX800, replacement reported by owner; no video after installation.
- Previous VTX: Rush Tank Ultimate Mini, confirmed by photo; removal does not establish its root cause.
- Camera: RunCam; Nano 3 model tentatively identified by owner. One Nano 3 removed from spares.
- Previous Caddx Vista moved to spares; it is not the installed VTX.
- Photo inspected: `C:\Users\irekr\iCloudDrive\IMG_0242.HEIC` (external Windows file, not copied into repo).
  Model marking and attached antenna connector are visible; wire routing and solder joints are
  not sufficiently visible to verify end-to-end wiring. A still image cannot verify LED flashing.

## Rush Tank Ultimate Mini

**Status:** Removed; close-range-only video remains unexplained.

### Symptoms

Video is visible only very close to the quad. Owner reports a continuously flashing green LED
and describes the VTX as stuck in PIT mode. This has happened **since installation**; no period
of normal operation on Mass is known. Low range alone does not establish PIT mode or a failed RF stage.

### Completed troubleshooting

| Check | Reported result | What it establishes |
|---|---|---|
| Physical PWR-button hold, approximately 3–5 seconds | Green LED continued flashing | Attempt did not clear the symptom; individual short-press response has not been recorded |
| Goggle Betaflight OSD / SmartAudio menus | No Race/Free mode option found | That option was not exposed in the interface used |
| Disable SmartAudio on FC UART in Betaflight Ports | Flashing state persisted | Disabling the configured interface did not resolve the problem; wire remained connected |
| Identify FC power pad | Owner confirmed VTX connected to 9V pad | Earlier guess that it used 5V was corrected |
| Measure at VTX with multimeter | Owner confirmed **9V+ at the VTX** | Simple 5V undervoltage explanation is unsupported; transient dips were not measured |
| Inspect photo | Rush Tank Ultimate Mini marking confirmed | Correct product family; no conclusive wiring fault visible |

The earlier 07:01 CLI backup predates the completed TX800 setup; the 16:01 backup below
records the configuration after video was restored.

### Corrections and unresolved hypotheses

The initial troubleshooting summary suggested button sequence/contact issues, thermal protection,
undervoltage, and a regional lock. Preserve these as hypotheses, not established diagnoses:

- **Supply:** measured 9V+ is within the documented 7–36V input range. No power-wire change is
  indicated by the current evidence. The VTX's 5V terminal is a camera supply output.
- **SmartAudio/configuration:** disabling the UART did not fix it, but does not conclusively rule
  out stored VTX settings or electrical interaction through the connected control wire.
- **Button:** mechanical contact or button handling remains untested independently. The manual
  documents holding PWR to toggle PIT mode. Earlier double-click speculation was not verified
  for this unit.
- **Heat:** no temperature measurement or controlled cold-start/airflow comparison was reported.
  A flashing LED has not been established here as proof of thermal shutdown.
- **Region lock:** no evidence confirms a lock on this unit. The earlier proposed 10-second
  Band/Channel unlock procedure was not verified and should not be treated as an instruction.
- **RF path/frequency:** antenna damage, connector problems, or a frequency mismatch remain
  possible explanations for short range; no known-good antenna comparison was reported.
- **Internal VTX fault:** possible, especially if correct power, isolated controls, and a known-good
  RF path fail to restore normal operation; not yet confirmed.

Reference: [Rush Tank Mini manufacturer manual (retailer-hosted PDF)](https://myosuploads3.banggood.com/products/20191120/20191120022637RushTankMiniManual.pdf).

### Proposed next steps — not confirmed performed; superseded by replacement

Remove props, attach the antenna, use airflow, and insulate the loose VTX from exposed electronics.
Disconnect battery and USB before changing wiring.

1. Physically disconnect only the SmartAudio wire, preserving power, ground, video, and antenna.
   Cold-start and retry the PWR-button hold. Record LED behavior before and after.
2. Check whether short PWR presses change the power indication. A response confirms some button
   input is registering, but does not by itself prove the long-press function or RF output works.
3. With normal power selected, manually match the exact goggle and VTX frequency rather than
   relying on autoscan. Inspect the antenna connection and compare with a known-good antenna.
4. If the symptom persists, observe supply voltage during the attempted mode change and record
   a short video of the LEDs and button presses before concluding that the VTX needs replacement.

## SpeedyBee TX800

**Status:** Video restored on R5; unlocking subsequently restored R8.

### Installation and initial troubleshooting

- Owner replaced the Rush with a SpeedyBee TX800 moved from QAS JB (origin confirmed 2026-09-10).
- Owner confirmed the TX800 is connected to **5V**, video to the FC VTX pad, and IRC to an FC
  TX pad. The UART number was not recorded. The earlier measured 9V+ applies only to the Rush.
- VTX LED illuminated; owner was unsure whether blue or red.
- Goggles showed **static/snow on R8**.
- Owner reported completing the IRC Tramp / TX800 table setup instructions, but still had no
  video on R8. Device-ready status was not explicitly reported or captured.
- Switching to **R5 (5806 MHz)** restored video. Owner confirmed a clear picture at a few metres,
  unlike the original Rush close-range-only symptom, and reported all good.
- The proposed test settings were 25mW and PIT off; no independent settings readback was supplied.

References: [TX800 setup](https://docs.speedybee.cn/en/fpv/vtx_vrx/tx800/how-to-set-protocol-and-import-vtx-table-for-tx800.html),
[5V power guidance](https://speedybee.zendesk.com/hc/en-us/articles/10087702239899-What-to-do-if-there-s-no-LED-is-showing-up-on-my-TX800-VTX).

The TX800 came from QAS JB; spare inventory is unchanged for this replacement. The removed Rush's disposition is also unconfirmed.

### R8 resolution — channel lock

SpeedyBee's channel chart lists **R8 (5917 MHz) as blocked while locked**, while
**R5 (5806 MHz) remains available**. Selecting R8 in Betaflight or loading a VTX table does
not itself remove the transmitter's lock. This explains why R5 worked while R8 showed static.

The owner confirmed that the following unlock procedure worked and restored operation on R8:

1. Disconnect battery and USB, then temporarily disconnect the IRC wire.
2. Power the VTX with its antenna attached and airflow over it.
3. Hold the VTX button for 10 seconds to toggle the lock.
4. Disconnect power, reconnect IRC, then select Raceband channel 8 and save in Betaflight.
5. Set the goggles to R8 / 5917 MHz.

SpeedyBee identifies a blinking red LED as locked and solid/off as unlocked. The owner confirmed
success of the procedure, but did not separately report the before/after LED state. FC control
can disable the physical button, which is why temporary IRC disconnection was included.
After unlocking, channel selection remains available through Betaflight using IRC Tramp.

Source: [SpeedyBee TX800 unlock instructions and restricted-channel chart](https://speedybee.zendesk.com/hc/en-us/articles/5366888051867-How-to-Unlock-Lock-TX800-and-Switch-Channels-Bands).

### Outcome and saved configuration

Mass is active. The TX800 replacement restored usable video on R5, and unlocking the TX800
subsequently resolved the R8 failure. The owner reported the unlock procedure worked.
No flight-range test was recorded; the earlier clear-video check was at a few metres on R5.

The latest saved 16:01 CLI backup records the **earlier R5 setup**, not the subsequent R8 change:
Raceband channel 5, 5806 MHz, `vtx_power = 1` with table value 25mW, and
`vtx_low_power_disarm = OFF`. These are saved settings, not a measurement of RF output or a
capture of the transmitter's lock state. No post-unlock R8 backup has been supplied.

The original Rush fault remains unresolved. The TX800 lock diagnosis applies to the replacement
transmitter; it does not establish why the Rush had close-range-only video.
