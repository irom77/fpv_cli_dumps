# Radio model backups

Radio model files are organized by radio manufacturer and model so files for
multiple radios can live here without mixing incompatible hardware configs.
Keep each EdgeTX model filename and internal model name together; save a dated
original backup alongside edited models when retaining more than one revision.
For inspection and editing workflow, use `.agents/skills/edgetx-radio-config/SKILL.md`.

Current layout: `RadioMaster_Boxer/BETAFLIGHT.yml` is the Boxer EdgeTX model
exported from the user's `MODELS_BOXER` backup, updated to route SA to CH9
(AUX5 for the AIR65_C channel map). The pilot confirmed SA selects Rate_1 and
Rate_3, with Rate_3 limiting throttle to 80%. See the radio-specific README
for validation steps.
