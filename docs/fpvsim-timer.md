# FPVSIM Timer — lap timing on R8

**Status:** Hardware identified as Timer Kit V2 (ESP32-C3) on firmware 3.0, which is the current
release for that board. USB app connection is not possible on this hardware; WiFi is the working
connection path. Desktop app is 5.2.5, also current. Established 2026-09-12.

**Open items:** firmware version is inferred from the purchase email, not read off the device;
Mass's current channel (R5 vs R8) needs a re-dump to settle.

## Timing laps on R8 — procedure

R8 = RaceBand channel 8 = **5917 MHz**. Most of the fleet already sits there, so the work is
timer-side.

1. **Place the node** at the gate, 1–3 m off the flight line.
2. **Drop the VTX to 25 mW.** A low-power, sharp RSSI peak is what makes detection reliable; high
   power flattens the curve and the timer starts triggering on nearby flight instead of the pass.
3. **Power the timer over USB** (power only — see [USB](#usb-does-not-work-on-this-hardware)) and
   connect the app over WiFi (see [Connecting](#connecting)).
4. **Set Band = RaceBand, Channel = 8.** The frequency field should read 5917 — it is a static
   display derived from band and channel, so it doubles as confirmation.
5. **Run auto-calibration** (app 5.0+) — see the full sequence below. The power-off prompt is not
   optional; skipping it leaves calibration incomplete.
6. **Set a minimum lap time** just under your realistic fastest lap, then check that the
   auto-derived max (min × 4) still clears your slowest plausible lap — see below. It is a guard
   against double-triggers, not a detection mechanism.
7. **Fly the session**, then open **race history** to inspect the RSSI record and visually add or
   delete any laps the timer misread.

Only one quad on 5917 may be powered at a time — most of the fleet shares that channel.

### Auto-calibration sequence (app 5.0+)

1. Node at the **final timing point**, VTX channel selected.
2. **Confirm the live RSSI responds before starting.** If it is flat here, calibration cannot work.
3. Start the calibration action in the app and **read the whole on-screen prompt** before taking off.
4. Fly **3–4 normal passes** at representative height and speed, on the actual racing line.
5. **Power off the VTX when instructed.** The app needs this powered-off baseline to finish its
   analysis; without it the peak and thresholds are never computed.
6. The app calculates peak and detection thresholds and confirms success.

Recalibrate after moving the timer, changing VTX channel or power, substantially changing the
course, or on repeatable missed or extra detections.

### Minimum lap time

Not a calibration setting — it lives in the **race format** settings, alongside `Max laps`,
`Consecutive laps`, `Max race time (min)`, `Max lap time (sec)` and `Pass per lap`.

| Property | Value |
|---|---|
| Field label | `Min lap time (sec)` |
| Units | Whole seconds (parsed as integer) |
| Default | **7** |
| Stored as | `raceFormat.minLapTimeSecs` |
| In-app description | "If a lap time is below this value, it won't be recorded, a beep will sound." |

Two behaviours that are not in the vendor documentation, read from the 5.2.5 app bundle:

- **Editing min lap time rewrites max lap time**: `maxLapTimeSecs = minLapTimeSecs * 4`, re-applied
  on every change. Min 7 gives max 28, and a lap *slower* than 28 s is rejected the same way. This
  bites on long courses and on any run with a crash-and-recover.
- **A rejected pass beeps and speaks the channel name** rather than recording a lap:
  `if (outstandingTimeMillis < minLapTimeSecs * 1000) { beep(); speak(selectedChannel); return }`

Because max is derived from min, the two constraints move together and **a min set too low is not
the safe choice** — it tightens the upper bound. Pick min just under your realistic fastest lap,
then confirm min × 4 comfortably exceeds your slowest plausible lap:

| Min | Derived max | Usable lap window |
|---|---|---|
| 3 | 12 | Short whoop course; rejects anything slower than 12 s |
| 7 (default) | 28 | Suits most 5-inch club laps |
| 15 | 60 | Long 7-inch course |

The beep behaviour is the most useful diagnostic in the whole system, because it separates a
detection failure from a filtering decision:

| Symptom on a pass | Meaning |
|---|---|
| Beep + channel announced, no lap | Detection worked; the lap was discarded by the min/max lap window |
| Silence, no lap | The pass was never detected — see the RSSI triage table below |

### What the display does during a session

**The clock does not reset when a quad is detected.** The large running clock is the session/race
clock and runs continuously from start to stop. A detected pass **closes the current lap and opens
the next**, which appears as a new **lap split** in the lap list.

So the signal that timing is working is **lap rows accumulating**, not anything happening to the
clock. Clock counting with no laps ever added means detection is not happening.

Note: the vendor docs are explicit that enter/leave thresholds drive detection and that race clock
and lap splits are distinct, but do not document the on-screen layout. The continuous-clock
behaviour above matches how RSSI gate timers work generally; confirm against the actual screen.

### No laps recorded — triage

Watch the **live RSSI trace** during a pass. It separates the causes in one run:

| RSSI behaviour | Cause | Action |
|---|---|---|
| Flat, no movement | Timer is not hearing the quad | Confirm the app reads 5917 and the quad is actually on R8; check the VTX is powered and the node is not too far |
| Clear spike per pass, no lap recorded, **no beep** | Thresholds wrong or never learned | Re-run auto-calibration, completing the power-off step |
| Clear spike per pass, no lap recorded, **beep + channel announced** | Lap fell outside the min/max lap window | Adjust `Min lap time (sec)`; remember max is forced to min × 4 |
| Laps recorded, too many | Leave threshold too permissive, or minimum lap time too low | Raise minimum lap time; recalibrate; check node placement |

### Manual calibration (pre-5.0 apps)

Three values, read off the live RSSI trace as the quad passes the gate:

| Value | Meaning |
|---|---|
| Enter threshold | Signal must rise above this to open a pass |
| Peak | Strongest signal observed during a pass |
| Leave threshold | Signal must fall below this to close the pass |

Peak set too high misses passes; thresholds set too loose accept nearby flight. Fix node placement
and flight consistency before making large sensitivity changes.

## Fleet — which quads are on R8

From `fpv_quads_latest.csv` (`vtx_band` 5 = RaceBand). Blank cells mean the setting is at firmware
default in the diff, not that the quad has no VTX.

**Active and already on R8 (5917):** AIR65 R, Ecofree, Green Hornet V3, LS-Ultra, LS-Ultra HD,
Mob6 AIO5 1st, Mob6 AIO5 2nd, Mobula1, openracer, PRO-SPEC2, XILOF4-2.

**On R8 but not flyable:** aos5 (incomplete), Crocodile5 baby (retired), Diamond (broken),
Meteor85 (broken), Race5 (status unset).

**Active, on another channel** — change these before timing, or time them on their own channel:

| Quad | Band/ch | Freq |
|---|---|---|
| Happish | R7 | 5880 |
| M6 ECO | R2 | 5695 |
| Mass | R5 | 5806 |
| openracer2 | R1 | 5658 |
| prospec | R1 | 5658 |

Mass records R5 in its latest saved backup, but R8 was restored on the TX800 after unlocking — see
[Mass VTX troubleshooting](troubleshooting/mass-vtx-troubleshooting.md). Re-dump to confirm which is
actually loaded before relying on the CSV.

HDZero quads work: the timer reads RF energy and supports analog and HD alike. Digital holds a more
constant output than analog, so expect a squarer RSSI shape — calibrate with the quad you will
actually fly rather than reusing an analog quad's thresholds.

## What I have

| Item | Value | How established |
|---|---|---|
| Hardware | **FPVSIM Timer Kit V2** | Firmware 3.0 targets "Timer Kit V2 and Multi Node only"; chip identification below. The ESP32-C3 conclusively rules out a Timer V3; Kit V2 is the best match for a purchased unit, though a DIY Solo build uses comparable hardware |
| MCU | **ESP32-C3** | Boot banner read over serial: `ESP-ROM:esp32c3-api1-20210207` |
| USB ID | `VID_303A` / `PID_1001` (Espressif native USB) | Windows PnP enumeration |
| MAC / serial | Espressif OUI `DC:DA:0C` | USB device instance ID carries the board's MAC as its serial |
| Firmware | **3.0** — current release for this board | Purchase email only; **not yet read off the device** — confirm in Settings → Firmware Update |
| App | **5.2.5** installed and launched by the Start Menu shortcut | Windows uninstall registry; shortcut target `…\Programs\com.fpvsim.timer\FPVSIM Timer.exe` |
| Stale app | **4.0.0** also installed at `…\Programs\com.quadrank.timer` (old app ID), no shortcut | Windows uninstall registry — safe to remove; predates auto-calibration |
| Extra tool | FPVSIM Timer Configurator 1.1.0 | Windows uninstall registry |

Firmware 3.0 added Timer Multi support (wired Ethernet, up to 8 racers), static IP configuration,
WiFi channel selection, and the OTA firmware updater.

## Connecting

### WiFi — the working path

- **Hotspot mode:** join SSID `fpvsim-p`, then pick the timer-hotspot connection in the app.
- **Router mode:** put the timer on a router so the laptop keeps its internet connection. Firmware
  3.0's static IP and WiFi channel selection make this the more comfortable option at a field.

A laptop has one WiFi radio, so joining `fpvsim-p` takes it off the house network. As of
2026-09-12 the timer was **not** a client on the house network — a full subnet sweep found no
Espressif MAC — so router mode was not in use at that point.

### USB does not work on this hardware

"Connect Timer USB" does nothing on this timer, and no update will change that.

**Root cause:** the ESP32-C3's USB peripheral is a fixed-function **USB-Serial-JTAG** block. It
cannot present a USB network interface. Only the ESP32-S2/S3 have the full USB OTG peripheral
required. The app's USB mode looks for a USB network interface, finds nothing to bind to, and fails
silently.

Evidence gathered on Windows, 2026-09-12:

| Check | Result | What it establishes |
|---|---|---|
| USB enumeration | `VID_303A&PID_1001`, present, Status OK | Cable and port are fine; device is seen |
| Exposed USB functions | `MI_00` USB Serial (COM14), `MI_02` USB JTAG/serial debug — nothing else | No network function is offered by the device |
| `Get-NetAdapter -IncludeHidden` | No FPVSIM / RNDIS / USB Ethernet adapter, present or hidden | The interface the app needs does not exist |
| Devices with Status ≠ OK | None on the entire system | Not a missing or failed driver |
| Serial boot banner | `ESP-ROM:esp32c3-api1-20210207` | Chip is ESP32-C3, which lacks USB OTG |

On this board the USB port is **power and flashing only**. Wired USB timing requires the
**Timer V3 Kit** (different hardware, app 5.2.3+); the Kit V2 is not upgradable to it.

Reading the serial banner reboots the timer (`rst:0x15 USB_UART_CHIP_RESET`). Harmless, but it drops
any live session.

## Checking the version and upgrading

Firmware updates go through whichever app instance is connected to the timer — phone or laptop.

**To check:** connect the app to the timer → **Settings → scroll down → Firmware Update**. The
current version is shown there, and the app raises a version-mismatch warning if a newer build
exists. Firmware **3.0 is the latest for Kit V2**, so it should report no update.

**The app is normally the component that goes stale**, not the firmware — but as of 2026-09-12 this
laptop already runs **5.2.5**, the current release, so nothing is pending. Per the 5.0 release
notes, "no firmware upgrade needed, so anything that works for 4.0 will continue to work for 5.0."

The orphaned 4.0.0 install is worth uninstalling so the pre-auto-calibration build cannot be
launched by accident.

Versions worth having:

| App version | Adds |
|---|---|
| 4.1.0 | Multi-hardware support; OTA firmware updater (minimum for flashing) |
| 5.0 | RSSI auto-calibrator, race builder, pack summary |
| 5.1.0 | Network delay accuracy fixes |
| 5.2.3 | USB connectivity — Timer V3 Kit only, not applicable here |
| 5.2.5 | Current |

**To flash**, if a mismatch is ever reported:

1. Download the zip **first**, while still on a network with internet — `fpvsim-timer-firmware-3.0.zip`
   for this board.
2. App ≥ 4.1.0, connected to the timer → Settings → Firmware Update → **Choose File**.
3. Confirm the firmware matches the board before starting. Mismatch is the irreversible failure
   mode and no wired recovery method is documented.
4. Do not interrupt. Disconnect and reconnect afterward to verify the version changed.

## Gotchas

- **`fpvsim-p` has no internet.** Download firmware before joining it, or the Choose File step
  strands you.
- **VPN tunnels hijack routing.** This laptop runs NordLynx (`10.5.0.2`) and Tailscale, both up.
  Drop NordVPN before joining `fpvsim-p` — a VPN holding the default route is the usual reason an
  app cannot see a timer that is associated fine at the WiFi layer.
- **One WiFi radio.** The laptop cannot be on `fpvsim-p` and the house network at once.
- **Shared channel.** Eleven active quads sit on 5917; power up one at a time.

## Diagnostic commands

Run from WSL against the Windows host. Useful for re-checking after a hardware or cable change.

```bash
# USB enumeration — is the timer seen, and what functions does it expose?
powershell.exe -NoProfile -Command "Get-PnpDevice -PresentOnly | Where-Object { \$_.InstanceId -like '*VID_303A*' } | Select-Object Status,Class,FriendlyName,InstanceId | Format-Table -AutoSize"

# Any network interface for it, including hidden/disabled?
powershell.exe -NoProfile -Command "Get-NetAdapter -IncludeHidden | Select-Object Name,InterfaceDescription,Status | Format-Table -AutoSize"

# Any device failing to bind a driver?
powershell.exe -NoProfile -Command "Get-PnpDevice -PresentOnly | Where-Object { \$_.Status -ne 'OK' }"

# Which SSID is the laptop on, and what is its IP?
powershell.exe -NoProfile -Command "netsh wlan show interfaces | Select-String 'SSID|State|Signal|Channel'"

# Is the timer a client on the current subnet? (look for an Espressif MAC)
powershell.exe -NoProfile -Command "Get-NetNeighbor -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi' | Where-Object { \$_.State -ne 'Unreachable' } | Format-Table -AutoSize"

# Which app versions are installed, and which one does the shortcut launch?
powershell.exe -NoProfile -Command "Get-ItemProperty 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*' | Where-Object { \$_.DisplayName -match 'FPVSIM' } | Select-Object DisplayName,DisplayVersion,DisplayIcon | Format-Table -AutoSize"
```

The app is an Electron bundle, so undocumented settings and defaults can be read from
`…\Programs\com.fpvsim.timer\resources\app.asar` with `grep -a`. That is how the minimum lap time
label, default and the min × 4 coupling above were established.

Reading the serial banner — note this reboots the timer:

```bash
powershell.exe -NoProfile -Command "
\$p = New-Object System.IO.Ports.SerialPort 'COM14',115200,'None',8,'one'
\$p.DtrEnable = \$false; \$p.RtsEnable = \$false
\$p.Open(); Start-Sleep -Seconds 5; \$p.ReadExisting(); \$p.Close()"
```

## Support and contact

| Channel | Link | Notes |
|---|---|---|
| Discord | https://discord.gg/QEfaHtASsu | Vendor's preferred route — release notes say "Please ping on Discord for speedy response" |
| Email | `qdrk@fpvsim.com` | From the app bundle, not a published contact page |
| Facebook group | https://www.facebook.com/groups/1213744526664012 | Community group linked from the app |
| GitHub — app | https://github.com/qdrk/fpvsim-timer-app | Issues enabled; for reproducible app bugs |
| GitHub — configurator | https://github.com/qdrk/fpvsim-timer-configurator | Source for the installed Configurator 1.1.0 |

There is no ticket system, contact form or dedicated support address. FPVSIM is effectively a
one-developer operation — `qdrk` is the GitHub org, the email local part and the old app ID
(`com.quadrank.timer`) — which is why the documentation is thin and Discord is the working channel.

Questions from this investigation that are worth raising there, as neither is documented:

- Whether USB connection is supported on Kit V2 at all, or is V3-only as the ESP32-C3 evidence
  implies. The evidence table above is a ready-made report.
- Where `Min lap time (sec)` sits in the UI, and whether `maxLapTimeSecs = minLapTimeSecs * 4` is
  intended behaviour.

## References

- [FPVSIM Timer — product and firmware downloads](https://fpvsim.com/timer)
- [Timer V3 Mahjong USB setup](https://fpvsim.com/how-tos/timer/getting-started/v3-mahjong-usb-setup)
- [Solo iOS setup and calibration](https://fpvsim.com/how-tos/timer/getting-started/solo-ios-setup-calibration)
- [Flashing FPVSIM Timer over OTA](https://fpvsim.com/how-tos/flash-fpvsim-timer-with-ota)
- [Tutorial library](https://fpvsim.com/how-tos)
- [Timer 4.0 with AI](https://fpvsim.com/blog/introducing-fpvsim-timer-40-with-ai)
- [Desktop app releases](https://github.com/qdrk/fpvsim-timer-app/releases)
