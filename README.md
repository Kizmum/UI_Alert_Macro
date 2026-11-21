# UI Alert Macro v6.0

Windows desktop application for recognizing on-screen Roblox biome notifications and sending Discord role alerts with screenshots.

Creators: Kizmum (`mindustry`) and Fonar (`nikline_`).

## Installation
- Requirements: Windows 10/11, Python 3.13.
- Download the `UI_Alert_Macro_v6_0.zip` asset from GitHub Releases. Extract the entire archive before running it.
- Keep the `ui/` folder beside `ui_alert_macro_gui.py`.
- Run `install.bat` once. Then run `start.bat`.
- In Settings and Other, paste your Discord webhook URL and role IDs, and enable the desired biomes. Role mentions such as `<@&123456789012345678>` are converted to digits.
- In Main, adjust the detection area. `F1` starts every enabled workspace, `F2` stops every workspace. Each workspace's START/STOP button operates independently.

## Recognition in v6.0
All non-TGSS biomes use the unchanged v5.2 method and are checked once every 5 seconds per enabled workspace.

For The Gray Shadow Space (TGSS), v6.0 uses two detection engines, both working from the same main UI image set in `ui/`:
1. **Modern engine:** unchanged v5.2 classifier using `tgss1.png`, `tgss2.png`, `tgss3.png`, with the normal 0.66 threshold and 0.05 ambiguity gap. On the regular 5-second full scan, if the TGSS-only score comes within 0.12 of the threshold, the macro activates TGSS-only accelerated sampling every 0.75 seconds for a short period.
2. **Classic engine:** uses the original v2 comparison formula (55% grayscale correlation, 25% edge correlation, 20% RGB histogram correlation) every 2.0 seconds. It compares against the main image set for the seven original biomes and can send alerts only for TGSS.

TGSS multi-ping remains available in Developer settings. All TGSS detection paths share the same cooldown inside a workspace.

## Cooldowns
- Rainy World and Blood Moon: 6 minutes per workspace and biome.
- All other biomes: 12 minutes per workspace and biome.
- TGSS Multi-ping: 5-second interval, escalating to 12 minutes after five successful pings inside two minutes.

## Workspaces, settings and screenshots
Up to eight workspaces, independent detection regions, VIP links, colors, START/STOP state, workspace enable switches, and independent cooldowns. Shared Discord webhook, role IDs, language, themes and Developer settings. Settings apply and save automatically. Screenshots can capture the monitor or detection region (optional +25 px margin), with selectable resolution caps. Discord notifications are always in English.

## Updating from v5.3
Keep a backup of `app_config.json`. Copy it into the extracted v6.0 folder before first launch if you want to preserve settings, role IDs, webhook and workspaces. Do not upload this file to a public repository.

## Privacy & GitHub
`app_config.json` may contain private Discord webhook credentials and VIP links. Never publish it or include it in an issue report. `.gitignore` excludes it and local log files. Check changed files in GitHub Desktop before committing.

For each GitHub release, create a new tag, e.g. `v6.0`, and attach the `UI_Alert_Macro_v6_0.zip` archive. Older tagged releases remain downloadable.

License: Apache-2.0. See `LICENSE` and `CHANGELOG.md`.
