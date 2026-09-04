# OpenRacer AM32 configuration exports — 2026-09-02

These four 184-byte files were exported separately from the AM32 web configurator. They are raw
EEPROM configuration buffers and are preserved so the exact settings can be reapplied or compared
later.

The files report EEPROM layout 2, bootloader revision 1, firmware 2.17, and the embedded target
name `XRotor45 F4`. According to the configurator's EEPROM schema, byte offset `0x11` is
`MOTOR_DIRECTION`. It is the only byte that differs among the four exports:

| ESC | Motor-direction setting | SHA-256 |
|---|---|---|
| 1 | normal (`0`) | `451b46c06cae758c1312c684173a4654f202908981aad04d7817180b6dfb4b01` |
| 2 | reversed (`1`) | `4a869d6c1e037baeaea90cf2beb61ef257ad77f2e024b4a62db1c20791267a2c` |
| 3 | reversed (`1`) | `4a869d6c1e037baeaea90cf2beb61ef257ad77f2e024b4a62db1c20791267a2c` |
| 4 | reversed (`1`) | `4a869d6c1e037baeaea90cf2beb61ef257ad77f2e024b4a62db1c20791267a2c` |

ESC2–ESC4 are byte-for-byte identical. The direction values describe the ESC settings only; verify
actual shaft direction with props removed before flight.

Schema source: <https://github.com/am32-firmware/am32-configurator/blob/master/src/eeprom.ts>

