# TODO

## 1. Publish the `fpv-fleet-update` skill publicly

Make the skill installable by others via a Claude Code plugin marketplace. Currently it's
project-scoped (`.claude/skills/fpv-fleet-update/`), so it only loads inside this repo.

Steps:
- [ ] Decide on a marketplace repo (e.g. `github.com/irom77/claude-plugins`) — separate repo, or reuse this one.
- [ ] Scaffold the plugin layout:
  ```
  plugins/fpv-fleet-update/
  ├── .claude-plugin/plugin.json      # name, description, version, author
  └── skills/fpv-fleet-update/
      ├── SKILL.md
      └── scripts/update_fleet.py
  ```
- [ ] Add the marketplace manifest `.claude-plugin/marketplace.json` listing the plugin.
- [ ] Fix the script path in SKILL.md: `.claude/skills/...` → `${CLAUDE_PLUGIN_ROOT}/scripts/update_fleet.py`
      (the repo-relative path breaks once installed as a plugin).
- [ ] Validate: `claude plugin validate .`
- [ ] Push the marketplace repo to GitHub.
- [ ] Test install from a clean checkout: `/plugin marketplace add irom77/claude-plugins` then
      `/plugin install fpv-fleet-update@<marketplace-name>`.
- [ ] Note in README how to install it.

Caveat to resolve: the skill writes its output (CSVs, FLEET_SUMMARY.md) into the current working
directory and is built around Betaflight dumps, so it's mainly useful to people who keep BTFL
backups. Consider documenting that expectation, or generalizing the script (e.g. an input/output
flag) before publishing.

## 2. Make use of blackbox logs

Betaflight blackbox flight logs (`.bbl` / `.bfl`) capture per-flight telemetry (gyro, PID error,
motor output, vbat, RC commands). Explore pulling these into the project alongside the CLI dumps.

Ideas to scope:
- [ ] Decide where logs live (e.g. `blackbox/<quad>/` subfolders) and a naming convention.
- [ ] Parse logs to per-flight summaries (flight time, min/avg vbat, max current/mAh, motor
      saturation, notable warnings) — likely via `blackbox_decode` (Betaflight tools) or a Python parser.
- [ ] Link each log back to its quad so it joins the existing inventory (craft name / board).
- [ ] Consider a per-quad "flights" rollup and add it to FLEET_SUMMARY.md.
- [ ] Extend the `fpv-fleet-update` skill (or add a sibling skill) to regenerate these summaries.
