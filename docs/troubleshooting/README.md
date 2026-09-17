# Troubleshooting records

Bench investigations that combine Betaflight configuration, wiring, measurements, and physical
hardware tests live here. These records preserve what was actually verified, distinguish evidence
from hypotheses, and leave a concrete next test when a fault is still open.

## Open investigations

- [Green Hornet V3 will not take off — two independent faults](green-hornet-post-upgrade-takeoff-failure.md)
  — stick offsets integrating without bound (fixed, verified) and a yaw rate reinterpreted by the 4.2.4 to
  2026.6.1 upgrade (fixed). Still open and blocking: Motor 3 is 14% down under load against 7.4% unloaded,
  roughly 26% less thrust on that corner. Prop swap test, then replace the motor.
- [OpenRacer intermittent thrust loss](openracer-thrust-loss.md) — motor 0 leads the recorded failure;
  AM32 channel settings otherwise match, and a props-off swap test is the next discriminator.
- [ProSpec racing LED kit does not illuminate](prospec-led-kit.md) — power is present, but valid
  WS2812 data has not yet been observed at the InfiniPowerPDB.
- [Crux35 flat yaw spin on takeoff](crux35-flat-yaw-spin.md) — motors spin Props Out as expected,
  mismatch on align_board_yaw (default 0 vs 45) or motor mapping pins suspected post-4.4.3 upgrade.
  Awaiting Setup tab test and Motors tab slider checks.
## Resolved grounding issues

- [Mass video failure](mass-vtx-troubleshooting.md) — TX800 on 5V restored video; unlocking resolved
  R8 failure. Mass active; original Rush fault remains unexplained.
