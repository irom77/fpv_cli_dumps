---
name: edgetx-radio-config
description: >-
  Read, compare, repair, or update EdgeTX radio settings and model configurations. Use when a
  user mentions an EdgeTX Companion backup (.etx), a model export (.yml), radio profiles,
  mixers, switches, channel outputs, or transferring model settings to a transmitter.
---

# EdgeTX radio configuration

Use this skill for radio-side configuration: Companion backups, model YAML, channel mixes,
switch assignments, and safe transfer guidance. Keep Betaflight CLI configuration and radio
configuration as separate artifacts; a radio mix sends channel values, while Betaflight decides
what those AUX values control.

## Workflow

1. **Identify the radio and artifact.** Confirm the radio model and EdgeTX/Companion version from
   the file or the user. In this repository, keep files under
   `radio_models/<manufacturer>_<radio-model>/`. Read the existing radio README and model before
   editing. `.etx` is a Companion archive containing full radio and model settings; a standalone
   `.yml` is one model; `.bin` is firmware or another binary backup, not a model export.

2. **Inspect without changing the source.** For `.etx`, use `file`, `unzip -l`, and `unzip -p` to
   inspect `RADIO/radio.yml` and `MODELS/*.yml` without extracting or rewriting the archive. For
   standalone YAML, parse it and inspect `header`, `expoData`, `mixData`, channel order, and output
   limits. Preserve an untouched source backup before any requested edit. Never mistake a
   single-model export for a full-radio backup.

3. **Trace the actual channel path.** In EdgeTX YAML, `mixData.destCh` is zero-based (`0` is CH1);
   identify the receiver AUX by following the radio mix to the configured protocol/channel order.
   Record every active mix line for that channel, its `srcRaw`, switch condition, weight, offset,
   and multiplex mode. Do not infer the physical control from a name such as S1, S2, S3, SA, or P3.
   Use the radio's channel monitor to establish the source and output values. For Betaflight, use
   the Receiver tab to confirm the corresponding AUX channel and its low/middle/high or detent
   values before explaining profile or mode selection.

4. **Make the smallest requested edit.** Base changes on the supplied model and preserve unrelated
   radio settings and model mixes. Remove invalid mix rows with no source; do not retain placeholder
   lines that Companion validates as errors. For a multi-position selector, configure one direct
   source line when the control itself supplies distinct channel values; avoid adding switch gates
   unless the requested behavior needs them. Check the Betaflight adjustment range and selection
   mode separately from the EdgeTX mix. For example, Betaflight's `rate_6pos_switch` changes how
   AUX values select rate profiles; it does not create six positions in the radio.

5. **Keep rollback material.** Save the original full `.etx` archive unchanged beside the radio's
   model files before replacing anything. Keep edited single-model YAML separate from the full
   archive and label both clearly. Do not silently overwrite the only backup or repackage an `.etx`
   archive when the requested operation only needs a model YAML edit.

6. **Validate the deliverable.** Parse edited YAML, inspect the diff, and confirm that the target
   channel has the intended sources and no empty-source mix rows. For `.etx`, verify the archive
   with `unzip -t` and compare its hash to the source when it should be unchanged. Report the exact
   file path and expected channel values for each switch position. Hardware behavior remains
   unverified until the user checks the radio channel monitor and receiver output.

7. **Guide Companion transfer.** Have the user select the correct radio profile and use a
   Companion version compatible with the radio's EdgeTX version. Connect the radio in USB Storage
   mode, read its full settings, merge or replace only the intended model, and save a full `.etx`
   backup. The write command targets the complete settings set and can replace every model on the
   radio. In Companion 2.11 and later, a model shown in red can disable writing: right-click it,
   choose **Show Model Errors**, and resolve every validation error first. A “mix line has no
   source” error means that model still contains an empty-source row. Select the full radio
   settings window before writing.

## RadioMaster Boxer notes

- The repository's Boxer files live in `radio_models/RadioMaster_Boxer/`.
- `boxer.etx` is a full settings snapshot; `BETAFLIGHT.yml` is a standalone model export. Treat
  them as distinct artifacts and do not assume edits to the YAML have changed the `.etx` archive.
- The Boxer S3 six-position control can appear in model mixes as source `P3`. Its six values must
  be verified in the channel monitor. The user's current AIR65_C setup uses SA on CH9/AUX5 to
  switch between Rate_1 and Rate_3; Rate_3 has the 80% throttle limit. Do not replace this with a
  six-position setup unless the user requests that change.

## Completion

The task is complete when each edited artifact has a preserved original, the requested radio/model
settings are present in the correct radio folder, static validation passes, and the handoff names
the Companion import/write steps plus any channel-monitor check still required from the user.
