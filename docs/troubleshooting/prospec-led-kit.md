# ProSpec racing LED kit does not illuminate

**Status:** Open

**Aircraft:** `prospec`

**Flight controller:** Hobbywing XRotor F7 Convertible (`HOBBYWING_XROTORF7CONV`, STM32F722)

**LED kit:** [Tiny's LEDs MultiGP Pro Spec Stock Racing LED Kit](https://tinysleds.com/products/multigp%C2%AE-pro-spec-stock-racing-led-kit)

**Power/data hub:** Tiny's LEDs InfiniPowerPDB

## Symptom

None of the five LED boards illuminate with a 6S LiPo connected. The kit contains one top-plate
board and four arm boards. Tiny's describes each physical board as one logical addressable LED from
the flight controller's perspective, even though each board contains many LEDs.

## Wiring and resource identity

Betaflight calls the LED data pin `A08`, meaning STM32 GPIO **PA8**. It is not a pad labeled `A08`
on the flight controller. On this Hobbywing board, PA8 is routed to the bottom-side solder pad
labeled **LED** or **LED-Strip**. Betaflight's target definition confirms
`LED_STRIP_PIN = PA8`:
[HOBBYWING_XROTORF7CONV target](https://support.betaflight.com/targets/HOBBYWING_XROTORF7CONV).

Because the FC pad is inaccessible when assembled, the same signal can be measured at the
InfiniPowerPDB's incoming `LED` solder pad, where the FC signal wire terminates. Use a nearby hub
`GND` as the measurement reference.

## Verified evidence

### Power

- Approximately 24 V from the 6S battery reaches the InfiniPowerPDB `B+` input.
- The hub's regulators produce 5.0 V at the LED power pads/sockets without load.

The 5 V measurement still needs to be repeated directly across a connected board's 5 V and GND
pads. An unloaded reading does not rule out connector resistance, a missing ground, or regulator
collapse under load.

### FC signal pin

- With PA8 temporarily mapped as `PINIO`, it produced a steady 3.3 V logic high.
- A diode-mode measurement from the hub signal net toward the FC read approximately 860 mV.

These results show that PA8 can operate as a GPIO and that the signal net reaches semiconductor
circuitry. They do **not** prove ordinary end-to-end wire continuity or that Betaflight is producing
a valid 800 kHz WS2812 waveform through the timer and DMA path.

### Betaflight configuration

- Firmware: Betaflight `4.5.3.KAACK_V19`.
- `feature LED_STRIP` is enabled.
- Live `resource show` reports `A08: LED_STRIP`; PA8 is no longer assigned to `PINIO`.
- Live `timer show` reports `TIM1 CH1: LED_STRIP`, and `timer A08 list` confirms alternate
  function 1.
- Live `dma show` reports `DMA2 Stream 6: LED_STRIP`, and `dma pin A08 list` confirms DMA option 0
  maps to Stream 6, Channel 0.
- `ledstrip_brightness = 100`, `ledstrip_grb_rgb = GRB`, and the active profile is `STATUS`.
- Logical LED entries 0 through 11 are configured with the constant-color function `C` and use
  color 0. Color 0 is HSV `0,0,255`, which is full-brightness white.
- Entries 12 through 31 print as Betaflight's all-zero/default representation
  (`0,0::C:0`).

These values were verified from the running FC after reboot on 2026-09-01. The capture was made
over USB while in CLI: `status` therefore reported `0S battery - NOT PRESENT`, and the hub and LED
boards were not powered during that capture.

Tiny's describes the five boards as five logical LEDs, so five entries should be sufficient for a
minimal test. Twelve configured entries produce a longer data frame, but should not prevent the
first five entries from illuminating. Reducing the diagnostic configuration to five entries may
still be useful for clarity, but it is no longer considered a likely fix.

The live allocation, LED function, color, and brightness checks substantially reduce the
likelihood of a static Betaflight configuration error. They still cannot prove that the timer/DMA
path produces a valid waveform electrically.

Betaflight's LED-strip remapping procedure and WS2812 requirements are documented in
[LED Strip Functionality](https://betaflight.com/docs/wiki/guides/current/LED-Strip-Functionality).

## What remains unproven

- Whether PA8 is producing valid 800 kHz LED data.
- Whether that waveform reaches the InfiniPowerPDB input.
- The hub's internal data direction and exact socket order.
- Whether the four-wire InfiniRainbow cables are oriented correctly and require any solder bridge.
- Whether 5 V and common ground remain valid at a board while it is connected.
- Whether the LED ICs reliably recognize a 3.3 V data high while powered at 5.0 V.
- Whether any individual LED board works from a known-good controller.

Do not treat the 860 mV diode-mode result as a continuity test. With all power removed, use ordinary
resistance/continuity mode from the FC LED pad to the hub's incoming LED pad if access becomes
possible.

## Next diagnostic session

Remove all propellers before powering the aircraft. Avoid loose probe hooks around battery-positive
pads.

### 1. Live resource-state check — completed 2026-09-01

The following commands were captured after a reboot:

```text
version
status
feature
resource show
timer show
timer A08 list
dma show
dma pin A08 list
get ledstrip
get ledstrip_grb_rgb
```

Confirmed relevant state:

```text
resource LED_STRIP 1 A08
timer A08 AF1
dma pin A08 0
feature LED_STRIP
resource PINIO 1 NONE
```

Some default target assignments may not appear in `diff all`; use `resource show`, `timer show`, and
`dma show` on the live FC.

Do not continue changing the PA8 resource, timer, or DMA mapping unless the oscilloscope shows that
no valid waveform is being generated. For waveform testing, exit CLI, let the FC boot normally,
and connect the battery so that the hub and LED boards are powered.

### 2. Check power under load

Connect one LED board and measure directly across its 5 V and GND pads. Also check resistance from
FC ground to that board's ground with all power removed.

### 3. Observe data at the accessible hub input

The best next measurement is at the InfiniPowerPDB's incoming `LED` pad:

- Oscilloscope probe tip: hub `LED` input pad.
- Oscilloscope ground clip: hub `GND`.
- Expected signal: bursts of approximately 800 kHz pulses, nominally switching between 0 V and
  about 3.3 V.

Interpret the result as follows:

| Observation | Meaning / next boundary |
|---|---|
| No waveform; constant low or high | Investigate live Betaflight resource, timer, DMA, and PA8 output |
| Valid waveform at hub input | FC and signal wire are likely good; probe the first socket/board DIN |
| Waveform enters hub but not first board | Check hub routing, cable orientation, connector, and bridge requirements |
| Waveform reaches board DIN with loaded 5 V and common ground | Test logic-level margin or the board itself |

A multimeter cannot validate WS2812 timing. Its DC reading is only an average of the pulse train.

### 4. Test the 3.3 V/5 V logic margin

Betaflight notes that some WS2812-compatible parts do not reliably recognize a 3.3 V signal when
powered at 5.0 V. If a clean waveform reaches DIN but the board stays dark, test one board using a
proper 3.3-to-5 V buffer such as a 74AHCT125/74AHCT1G125, or a known-good 5 V addressable-LED
controller. Temporarily lowering LED power to approximately 4.5–4.7 V is another diagnostic only
after confirming the Tiny's board permits it.

### 5. Isolate each board

Test each board individually with confirmed 5 V under load, common ground, its verified `DIN`, and
a known-good WS2812 source. Do not jumper the hub's `LED` input to an unidentified connector pin:
the four-pin system may expose distinct data-in and data-out paths.

## Ranked hypotheses

1. PA8 is not producing a valid timer/DMA-driven 800 kHz waveform despite passing the static
   `PINIO` test.
2. Hub input direction, cable orientation, internal routing, or a required bridge is wrong.
3. The 3.3 V data level is marginal against the 5.0 V LED supply.
4. Common ground is missing/high-resistance, or the 5 V rail collapses under load.
5. One or more LED boards have failed. All five independently failing is less likely than a shared
   upstream problem.

## Suitable low-cost instruments

- **Cheapest digital check:** an FX2LA-compatible 8-channel 24 MHz USB logic analyzer with
  PulseView/sigrok. It can show whether pulses exist and inspect their timing, but it cannot measure
  the true analog voltage level or edge quality. See the
  [sigrok FX2 analyzer example](https://www.sigrok.org/wiki/AZDelivery_Logic_Analyzer).
- **Low-cost standalone scope:** [FNIRSI DSO-510](https://www.fnirsi.com/products/dso-510), one
  channel, 10 MHz bandwidth, 48 MS/s. This is sufficient for the 800 kHz signal and can show its
  voltage level. Avoid the 200 kHz DSO-152 for this job.
- **Low-cost PC scope:** [Hantek 6022BE](https://www.hantek.com/products/detail/118), two channels,
  20 MHz bandwidth, 48 MS/s.

For this aircraft, a scope provides the most useful evidence because the 3.3 V versus 5 V logic
margin is one of the remaining hypotheses.

## Closure criteria

Close this investigation only after recording:

- the waveform observed at the hub input and first board DIN;
- loaded voltage at the tested board;
- the isolated component or configuration that caused the failure;
- the final repair; and
- confirmation that all five boards illuminate after a power cycle.
