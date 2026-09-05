# Betaflight upgrade records

This directory is the permanent log for flight-controller firmware upgrades. Create one directory
per quad and upgrade event. Keep the raw pre- and post-upgrade CLI dumps in `backups/` and link them
from the upgrade record rather than duplicating them.

Each record should capture:

- date, quad, flight-controller target, firmware version and MSP API before and after;
- the exact firmware file and checksum when a local firmware image is available;
- source/config commits for custom builds;
- settings deliberately changed, preserved, translated or rejected during migration;
- the final CLI backup used by the fleet inventory;
- bench checks completed and any checks or flight tests still outstanding;
- rollback instructions and the pre-upgrade backup.

## Recorded upgrades

- [Green Hornet V3 — Betaflight 4.2.4 to 2026.6.1](GREEN_HORNET_V3_BF_2026_6_UPGRADE/README.md)
- [OpenRacer — Betaflight 4.5.1 to 4.5.3.KAACK_V19](OPENRACER_KAACK_V19_UPGRADE/README.md)
- [ProSpec — Betaflight 4.3.2 to 4.5.3.KAACK_V19](PROSPEC_KAACK_V19_UPGRADE/README.md)
