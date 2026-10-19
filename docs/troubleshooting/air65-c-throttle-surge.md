# AIR65_C jumps upward on throttle

## Current status

**Unresolved.** The pilot reports the AIR65_C shoots up to the ceiling when throttle is touched shortly after arming. Rate_3 throttle limits of 80% and 60% did not change the behavior. The Air Mode change also did not help. No Blackbox log or controlled comparison is available yet, so the cause is not established.

## Confirmed configuration and timeline

- The quad was purchased on 2026-10-07.
- The earliest named dump, `BTFL_cli_AIR65_C_20261008_095237_BETAFPVG473_V2.txt`, is only 6 bytes (`# `) and is not a usable configuration dump.
- The earliest complete dump is `BTFL_cli_AIR65_C_20261008_101127_BETAFPVG473_V2.txt`. It contains `feature AIRMODE`, so Air Mode was enabled in that snapshot.
- The pilot confirms the Boxer SA switch selects Betaflight Rate_1 and Rate_3. Rate_3 is `rateprofile 2`; the 2026-10-14 12:25 dump shows `throttle_limit_type = SCALE` and `throttle_limit_percent = 80`.
- The pilot then applied `set throttle_limit_percent = 60` to `rateprofile 2`. The 2026-10-14 12:28:30 dump confirms Rate_3 at SCALE/60. The pilot reports the ceiling jump persisted.
- The 2026-10-14 12:56:01 dump shows `feature -AIRMODE` (permanent Air Mode off), `aux 3 28 4 900 1300 0 0` (Air Mode assigned to AUX5's low range), and `rateprofile 2` at `throttle_limit_type = SCALE`, `throttle_limit_percent = 80`. The pilot reports this Air Mode change did not help. The low AUX5 range is intended to correspond to Rate_1; verify the SA/Rate_1 mapping in the Modes tab if it matters for another test.
- Initial report: the behavior occurred with BETAFPV LAVA II 1S 320mAh LiHV BT2.0 packs, while other 1S packs worked. The pilot later clarified that the other packs are also 4.35V LiHV. No matched-voltage or pack-swap test has been documented, so a pack-specific cause remains possible but unproven.
- Air Mode was enabled in the earliest complete dump, but the latest dump confirms permanent Air Mode is now disabled and the mode is assigned to the low AUX5 range.

The Windows source files are under `C:\Users\irekr\OneDrive\Documents\FPVBackup\DUMP_ALL\`.

## Related reports found

- The Amazon link reviewed is for the Air65 II Champion quad (ASIN B0GS5SG1LB), not the LAVA II battery. The listing displayed 3.9/5 from 25 ratings and identifies the Champion's 36,000KV motors; it also lists LAVA II 280/320mAh batteries as recommended. Amazon's individual review page returned HTTP 503 during this review, so no claim is made about what those Amazon reviewers wrote: [Amazon Air65 II Champion listing](https://www.amazon.com/dp/B0GS5SG1LB).
- An independent Air65 II Champion review describes the throttle response as exceptionally sharp and the quad as overpowered indoors, while the author reports using no more than about 60% throttle. This supports that the Champion has a high-power, sensitive throttle, but does not explain why this pilot reports the symptom only with the LAVA II packs: [Oscar Liang's Air65 II review](https://oscarliang.com/betafpv-air65-ii/).
- A Reddit user with an Air65 Champion and LAVA II 320mAh described a sudden straight-up surge above roughly 35% throttle, with transmitter throttle no longer reducing thrust. A commenter said a canopy change stopped a similar issue; another later commenter said turning Air Mode off fixed theirs. These are anecdotal reports and do not establish this quad's cause: [Air65 Champion intermittent throttle runaway](https://www.reddit.com/r/TinyWhoop/comments/1ruwto7/air65_champion_intermittent_throttle_runaway/).
- A separate 65mm build reported a thrust burst after a brief throttle input on a freshly charged battery, improving as pack voltage dropped. That build mixed Air65 generations and used a CLI for a different AIO, so it is a weaker match: [Throttle problems](https://www.reddit.com/r/TinyWhoop/comments/1rgct7j/throttle_problems/).

## Next checks

1. Inspect canopy seating, FC mounting screws, and wiring around the gyro. A similar Air65 report mentions canopy or screw pressure, but this remains a hypothesis.
2. Check receiver throttle values for a smooth rise from minimum and verify SA selects Rate_1/Rate_3 as expected. Do this with props removed.
3. Compare the LAVA II and a known-good BETAFPV 300mAh pack at similar starting voltage; record loaded voltage sag if available. Equal resting voltage does not establish equal voltage under load.
4. If the cause remains unclear, capture Blackbox data from a safe test. The existing CLI dumps cannot show the actual throttle, motor commands, gyro response, or what happens at the jump.

Do not keep lowering the limit as a substitute for diagnosis: the 60% Rate_3 test did not change the reported behavior.
