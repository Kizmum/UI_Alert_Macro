# UI Alert Macro v1.0.0 — Stable Release

First stable release, validated against a real The Gray Shadow Space (TGSS) event.

### Highlights
- TGSS alerts are now handled exclusively by the classic Legacy v2 recognition engine, checking every 2 seconds.
- The Modern classifier continues checking the other eight biomes every 5 seconds; it no longer checks TGSS.
- New TGSS templates (`tgss1.png`, `tgss2.png`, `tgss3.png`) captured during the event replace the previous templates.
- The existing app features, workspace settings and cooldowns are preserved.

### Installation
Download the ZIP asset below, extract it, run `install.bat`, and then run `start.bat` (Windows + Python 3.13).

### Upgrading
Copy `app_config.json` from your previous version to preserve your private settings; do not commit this file to GitHub.

For details see `README.md` and `CHANGELOG.md`. This is the public release package, not the personal EX build.
