# Troubleshooting records

Bench investigations that combine Betaflight configuration, wiring, measurements, and physical
hardware tests live here. These records preserve what was actually verified, distinguish evidence
from hypotheses, and leave a concrete next test when a fault is still open.

## Open investigations

- [OpenRacer intermittent thrust loss](openracer-thrust-loss.md) — motor 0 leads the recorded failure;
  AM32 channel settings otherwise match, and a props-off swap test is the next discriminator.
- [ProSpec racing LED kit does not illuminate](prospec-led-kit.md) — power is present, but valid
  WS2812 data has not yet been observed at the InfiniPowerPDB.
