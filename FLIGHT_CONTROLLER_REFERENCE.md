# FPV flight-controller catalog and wiring reference

Generated from the CLI dumps and `hardware.csv` on 2026-09-04. The newest CLI dump for each
craft is the inventory authority. Product identity is then refined
with the curated build notes and manufacturer documentation.

> **Before soldering:** a Betaflight target identifies firmware, not necessarily a
> unique PCB or revision. Match the silkscreen, connector orientation, and board
> revision to the linked manufacturer diagram. Check ground-to-power resistance with
> a multimeter and use a smoke stopper for first power-up.

## Inventory

The dump set contains **33 current craft/unnamed identities and 18 distinct Betaflight
board strings**.
Those strings resolve to the physical controller families below; rows marked
**revision-sensitive** must be visually identified before their pinout is trusted.

| Controller / physical family | Betaflight board string(s) | Quads using it | State of identification |
|---|---|---|---|
| BETAFPV Air 5-in-1 G473 | `BETAFPVG473` | AIR65 R | Product family confirmed |
| BETAFPV F4 1S 12A AIO ELRS | `BETAFPVF4SX1280` | Meteor85, M85 HDZero, unnamed BETAFPV dump | V2.0/V2.2 revision-sensitive |
| Happymodel Diamond F4 ELRS AIO | `CRAZYBEEF4SX1280` | Diamond | Product confirmed; target is shared |
| Happymodel SuperbeeF4 Lite / Mobula HD board | `CRAZYBEEF4SX1280` | Happish, Mobula1 | Product family from build notes; revision-sensitive |
| Happymodel/HDZero AIO5 | `CRAZYBEEF4SX1280` | Mob6 AIO5 1st, Mob6 AIO5 2nd, Mob6 AIO5 RACE, Mob6 HDZERO RACE, Race5 | Product family from names/notes; revision-sensitive |
| Happymodel SuperX HD ELRS AIO | `CRAZYBEEF4DX` | Ecofree, M6 ECO | Dump target differs from curated product name; **verify PCB** |
| Flywoo GOKU Versatile F405 1–2S 12A AIO | `FLYWOOF405S_AIO` | unnamed Firefly 2S Nano Baby 20 | Confirmed by build/order evidence |
| Flywoo GOKU F745 Nano stack | `FLYWOOF745NANO` | FLYWOOF7NANO | Product family confirmed |
| Foxeer Mini F722 V4 | `FOXEERF722V4` | openracer2 | Confirmed |
| GEPRC GEP-F411-35A AIO family | `GEPRC_F411_AIO`, `GEPRCF411_AIO` | CineLog30, cinelog-flyfish | Likely old/new target aliases; revision-sensitive |
| GEPRC GEP-F722-35A AIO family | `GEPRC_F722_AIO` | Crocodile5 baby, unnamed GEPRC dump | Product confirmed; gyro/PCB revisions exist |
| Happymodel CrazyF411 ELRS 20A AIO | `BETAFLIGHTF4` | HDZERO CRUX35 | Confirmed by Crux35 manual; generic target name |
| HDZero Halo H743 | `HDZERO_HALO` | LS-Ultra HD, PRO-SPEC2 | Confirmed |
| Hobbywing XRotor F7 / Convertible family | `HOBBYWING_XROTORF7CONV` | openracer, PROSPEC, unnamed Hobbywing dump | Family confirmed; PROSPEC's newest dump is `CONV` |
| Hobbywing XRotor F7 legacy target | `HOBBYWING_XROTORF7CON` | unnamed Hobbywing dump; an older PROSPEC dump only | Physical revision unresolved |
| Lumenier LUX HD AIO G4 | `LUXHDAIO-G4` | QAS JB | Target/build-family identification; exact board revision unconfirmed |
| SpeedyBee F405 Mini | `SPEEDYBEEF405MINI` | unnamed Massive Droner 3-inch | Confirmed |
| T-Motor F7 family | `TMOTORF7` | LS-Ultra | Dump conflicts with curated “Foxeer Mini F722” note; **verify PCB** |
| XILO Stax F4 | `XILOF4` | XILOF4, XILOF4-2 | Confirmed; V1.1/V1.2 revision-sensitive |

## How to read the diagrams

These are wiring-oriented diagrams, not scale drawings. `TXn → RX` and `RXn ← TX`
show the required UART crossover. A voltage label describes that pad's rail; it is
not permission to feed the rail from an arbitrary source.

```text
Serial peripheral                 Flight controller
TX  --------------------------->  RXn
RX  <---------------------------  TXn
GND ----------------------------  GND
VCC ----------------------------  voltage specified by peripheral + FC manual
```

## Controller pinout references

### BETAFPV Air 5-in-1 G473 — AIR65 R

The dump proves target `BETAFPVG473`; the build record identifies the Air65 5-in-1.
Because BETAFPV has shipped multiple Air/Matrix revisions, use the diagram printed for
the exact revision on the PCB. **No safe pad-level transcription is made here until
the board revision is photographed.** Manufacturer starting point: [BETAFPV Air
flight-controller page](https://betafpv.com/collections/globo_basis_collection/products/air-brushless-flight-controller).

### BETAFPV F4 1S 12A AIO ELRS — Meteor85 / M85

Official diagrams: [BETAFPV F4 1S 12A AIO product page](https://betafpv.com/products/f4-1s-12a-flight-controller) and [V2.0 archive](https://betafpv.com/products/f4-1s-12a-flight-controller-v2-0).

```text
                 F4 1S 12A AIO
 motors 1–4 ---> four motor plugs / solder pads
 battery ------> BAT+ / GND                 (1–2S on V2.x)
 camera -------> VI / 5V / GND
 analog VTX <--- VO / 5V / GND
 external RX --> UART RX/TX / power / GND
 buzzer -------> BUZ+ / BUZ-
```

The official page states that UART1 and UART2 are exposed, but pad position differs
among ELRS V1.0, V2.0 and V2.2. Match its photographed diagram before soldering.

### Happymodel boards using `CRAZYBEEF4SX1280`

This target covers at least three physical families in this fleet: Diamond F4,
SuperbeeF4 Lite, and HDZero AIO5. **They are not interchangeable pinouts.** Until each
PCB is photographed, use only its model-specific manual/silkscreen. Manufacturer
manual archive: [Happymodel downloads](https://www.happymodel.cn/index.php/category/download/).

Common logical wiring only:

```text
  M1..M4  -> onboard ESC outputs/motor pads
  BAT/GND -> battery input
  CAM/VIN -> analog camera input (only on analog variants)
  VOUT    -> analog VTX video (only on analog variants)
  TX/RX   -> revision-specific exposed UART
  LED/BZ- -> addressable LED / active-low buzzer control
```

Do not infer the Diamond or Superbee pad positions from the old Crazybee F4DX manual.

### Happymodel SuperX HD ELRS AIO — Ecofree / M6 ECO

The curated build notes say SuperX HD AIO, while both dumps report `CRAZYBEEF4DX`.
That mismatch makes this the highest-risk identification in the whoop group. Treat it
as revision-sensitive and wire only from the exact product diagram after visual
confirmation. Happymodel does explicitly assign this firmware target to the
[SuperX HD ELRS AIO](https://www.happymodel.cn/index.php/2023/09/04/superx-hd-elrs-1-2s-aio-flight-controlelr-built-in-12a-esc-and-uart-elrs-receiver-for-digital-whoop/),
but the target alone still does not prove the PCB in either aircraft.

### Flywoo GOKU Versatile F405 1–2S 12A AIO

Official product and diagram center: [GOKU Versatile F405 2S 12A AIO](https://flywoo.net/products/goku-versatile-f405-2s-12a-aio-w-build-in-elrs-2-4g-rx-mpu6000) and [Firefly 2S Nano Baby downloads](https://flywoo.net/pages/firefly-2s-nano-baby-download-center).

```text
              GOKU F405S AIO
 M1 M2 M3 M4  onboard 12A ESC motor outputs
 BAT+ GND     1–2S battery
 T1/R1        onboard serial ELRS on equipped version
 T2/R2 ...    exposed UART pairs (six UARTs total)
 SDA/SCL      I2C
 5V/GND       peripherals
 CAM/VOUT     analog camera / OSD video-out on original board
```

The fleet dump uses the original MPU6000-era target. Do not substitute the newer
USB-C HD V2 connector diagram without checking the actual board.

### Flywoo GOKU F745 Nano — Explorer LR4

Official diagram/manual hub: [Flywoo electronic download center](https://flywoo.net/pages/electronic-download-center%3Fsrsltid%3DAfmBOorK6p_n23vhwI-IicyVPKwoIuXqZ0CqNzOF7qcrRHBdIKAEZGK7).

```text
 ESC harness: VBAT | GND | M1 | M2 | M3 | M4 | CURR | TELE
 HD VTX:      power | GND | FC-TX -> VTX-RX | FC-RX <- VTX-TX
 receiver:    5V | GND | FC-RX <- RX-TX | FC-TX -> RX-RX
 GPS:         5V | GND | TX -> RX | RX <- TX | SDA | SCL (if compass)
```

Select the archived **F745 Wiring Diagram Manual**, not an F722/GN745 AIO diagram.

### Foxeer Mini F722 V4 — openracer2

Use Foxeer's Mini F722 V4 diagram for the actual 20×20 PCB. The dump and curated
hardware agree on the model, but Foxeer's current storefront is revisioned; confirm
`V4` on the board before using any connector. Manufacturer: [Foxeer Mini F722 V4](https://www.foxeer.com/foxeer-f722-v4-mini-flight-controller-mpu6000-g-471).

```text
 receiver: RX TX 5V GND  -> FC UART1 (fleet configuration)
 analog cam: VIDEO-IN / camera power / GND
 analog VTX: VIDEO-OUT / VTX power / GND / TX5 (Tramp in this fleet)
 ESC: M1 M2 M3 M4 CURR TELE VBAT GND through stack harness
```

### GEPRC GEP-F411-35A AIO — CineLog builds

Official manuals: [GEPRC FC manual index](https://geprc.com/electronics/fc-manual/),
select **F411-35A AIO Manual** or **F411-35A AIO V2 Manual** after matching the PCB.

```text
 M1..M4       motor pads / integrated 35A ESC
 BAT+ / GND   battery and capacitor
 R1/T1...     UART receive/transmit pairs
 CAM / VTX    analog video-in / OSD video-out
 5V / GND     receiver, camera and peripherals
 BUZ- / LED   buzzer control / LED signal
 HD plug      power, GND and MSP UART on equipped revision
```

`GEPRC_F411_AIO` and `GEPRCF411_AIO` are cataloged separately as firmware strings,
but are not evidence of two different physical boards.

### GEPRC GEP-F722-35A AIO — Crocodile5 Baby

Official [GEP-F722-35A product page](https://geprc.com/product/gep-f722-35a-aio-f722-fc-35a-2-6s-8bits-bls-esc-25-5mm/) and [manufacturer PDF](https://geprc.com/wp-content/uploads/2022/05/F722-35A-AIO-USER-MANUAL2.pdf).

```text
 M1..M4       motor pads / integrated ESC
 BAT+ / GND   2–6S input and capacitor
 R1/T1 ... R5/T5   five full UARTs
 CAM / VTX    analog video-in / OSD video-out
 5V / GND     regulated peripheral power
 BUZ / LED    buzzer and LED
 HD connector power | GND | MSP RX/TX
```

### Happymodel CrazyF411 ELRS 20A AIO — HDZero CRUX35

Official [Crux35/Crux35HD/HDZero manual](https://www.happymodel.cn/wp-content/uploads/2023/02/Crux35-Crux35HD-DJI-and-Crux35-HDZERO-FPV-Racer-Drone-ELRS-V2-manual.pdf).

```text
 TOP:    VOUT VIN 5V GND | TX1 RX1 BUZ- LED_S 5V GND | TX2 RX2
 BOTTOM: M1 M2 M3 M4 | BAT+ GND | ELRS U.FL | FC BOOT | ELRS BOOT

 onboard ELRS normally occupies UART2 (TX2/RX2)
 analog camera -> VIN; analog VTX video <- VOUT
```

The manual documents a solder bridge for reclaiming UART2; inspect the exact revision
before changing it.

### HDZero Halo H743 — LS-Ultra HD / PRO-SPEC2

Official [Halo wiring guide](https://docs.hd-zero.com/de/halo-wiring), [specification](https://docs.hd-zero.com/halo-introduction), and [manual downloads](https://www.hd-zero.com/document).

```text
 ESC socket: VCC | GND | CURR | TELE/RX4 | M1 | M2 | M3 | M4
 VTX/MSP:    9V | GND | TX5 -> VTX-RX | RX5 <- VTX-TX
 external RX: 4V5/5V | GND | TXn -> RX | RXn <- TX
 GPS/compass: 4V5 | GND | TXn/RXn | SDA/SCL
 other pads: TX2/RX2, TX7/RX7, TX8/RX8, buzzer, LED, I2C
 onboard Gemini ELRS uses UART1
```

Older and newer HDZero Race V3 VTX cable batches have different connector pin order;
the official wiring page shows the required re-pinning.

### Hobbywing XRotor F7 (`...CONV`) — openracer / PROSPEC

Official [XRotor F7 manual](https://www.hobbywing.com/en/uploads/file/20221104/00eeb5856cb7e57030ca193ab335416b.pdf) and [product page](https://www.hobbywing.com/en/index.php/products/xrotor-flight-controller-f7115.html).

```text
 power/ESC: VBAT | GND | CRT | S1 S2 S3 S4 | TELEMETRY (UART6-RX)
 UARTs:     TX1/RX1, TX2/RX2, TX3/RX3, TX4/RX4; TX5 for VTX control
 analog:    CA1 or CA2 -> OSD -> VOUT; CTL for camera control
 power out: 5V, 10V, 3V3 (3V3 requires 5V input per manual)
other:     SDA/SCL, RSSI, BUZ+/BUZ-, LED-Strip
```

PROSPEC's newest dump (`20260901_164018`) and later 2026-08-25 dumps use `...CONV`; its
initial 2026-08-25 dump used `...CON`. Its order/build record identifies the newer XRotor
Convertible F7/65A HD AM32 30×30 stack. That proves why the suffix alone is not a
physical-board identifier: use the diagram packed with the stack and visually match
the PCB. Manufacturer support: [Hobbywing flight controllers](https://www.hobbywing.com/en/drone-propulsion/rc-aircraft-power-systems/fpv-racing/flight-controller).

### Lumenier LUX HD AIO G4 — QAS JB

The CLI target proves `LUXHDAIO-G4`, but the repository does not contain a purchase
record or board photo that fixes the PCB revision. No safe physical pinout is asserted.
Record front/back photos and the silkscreen before repair; then match the [Lumenier
LUX HD AIO G4 product/manual page](https://www.getfpv.com/electronics/flight-controllers/aio-all-in-one-fc/lumenier-lux-hd-aio-g4-fc-35a-am32-3-6s-esc.html).
The currently recorded external analog conversion must preserve:

```text
 camera video -> CAM/VIN -> onboard OSD -> VTX/VOUT -> analog VTX video
 VTX control   -> a free UART TX pad (protocol must match SmartAudio/Tramp)
 RX TX         -> FC UART RX; RX RX <- FC UART TX; common GND and correct VCC
```

### SpeedyBee F405 Mini — 3-inch HD build

Official [F405 Mini stack page](https://www.speedybee.com/speedybee-f405-mini-bls-35a-20x20-stack/) and [manual download](https://www.speedybee.com/f405-mini-stack-download/).

```text
 ESC harness/pads: G V M1 M2 M3 M4 CURR TELE
 DJI/HD: 9V GND T1 R1 plus SBUS/R2 where applicable
 RX/GPS: 4V5 or 5V, GND, matching Tn/Rn pair
 analog: CAM -> OSD -> VTX; VTX control on free TX
 other: 3V3, BZ+, BZ-, LED, CC, SDA, SCL
```

The manufacturer states T1/R1 are used for digital OSD and R2/SBUS for a DJI receiver;
do not assign those pins twice.

### T-Motor F7 family — LS-Ultra

The CLI says `TMOTORF7`, and the purchase ledger contains a T-Motor F7 HD/F55A stack,
but `hardware.csv` says Foxeer Mini F722. This cannot be resolved from software.
Compare the board against T-Motor's [30×30 F7](https://store.tmotor.com/product/f7-flight-controller.html) and [Mini F7](https://store.tmotor.com/product/mini-f7-flight-controller.html) before soldering. No pad-position diagram is safe until then.

### XILO Stax F4 — XILOF4 / XILOF4-2

Official [XILO Stax manual PDF](https://www.getfpv.com/media/downloads/manuals/XILO-Manual_Draft-0506.pdf) and [product archive](https://www.getfpv.com/electronics/flight-controllers/mini-flight-controllers/xilo-stax-f4-flight-controller.html).

```text
 SBUS -> UART1 RX (inverted)      DSM -> UART1 TX / half-duplex
 Crossfire: 5V GND, RX3 <- TX, TX3 -> RX
 GPS: TX4/RX4                    ESC telemetry -> RX2/TLM
 SmartAudio/Tramp -> TX5/S-A     SmartPort/F.Port -> UART6
 I2C: SDA/SCL                    buzzer -> BZ+/BZ-
 camera control -> C_C           LED strip -> LED
 ESC harness: VBAT GND M1 M2 M3 M4 CURR TELE (verify harness order)
```

The archive notes V1.1-or-older versus V1.2-or-newer firmware differences; match the
PCB revision before using the harness or flashing firmware.

## Open identification work

For a solder-safe edition of this guide, capture straight-on, well-lit front and back
photos (including all silkscreen and connector keys) for:

1. AIR65 R; every `CRAZYBEEF4SX1280` physical variant; Ecofree; and M6 ECO.
2. Both CineLog AIO boards and both GEPRC F722 dumps.
3. PROSPEC, QAS JB, and LS-Ultra.
4. The unnamed Hobbywing, GEPRC, BETAFPV, and SpeedyBee dump identities if they are
   still physical aircraft rather than historical backups.

Once photographed, replace each revision warning with a cropped manufacturer diagram
or a locally annotated board image. That is the only reliable way to turn target-level
inventory into pad-position-level repair documentation.
