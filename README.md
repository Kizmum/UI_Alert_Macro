# UI Alert Macro v1.0.0

A Windows desktop utility for detecting Roblox biome UI alerts and posting Discord role notifications with screenshots.

Creators: Kizmum (`mindustry`) and Fonar (`nikline_`).

## Install

- Requires Windows 10/11 and Python 3.13.
- Download `UI_Alert_Macro_v1.0.0.zip` from [Releases](https://github.com/Kizmum/UI_Alert_Macro/releases) and extract the entire archive.
- Run `install.bat` to install `mss`, `opencv-python`, and `numpy`; then run `start.bat`.
- Keep the `ui/` folder next to `ui_alert_macro_gui.py`.

## Setup

1. Open **Settings and Other**, paste a Discord webhook URL and role IDs, and enable the biomes you want to monitor. A mention such as `<@&123456789012345678>` is automatically converted to digits.
2. In **Main**, adjust the detection area using its movable, resizable outline.
3. Press **F1** to start all enabled workspaces or **F2** to stop them. START and STOP inside an individual workspace only affect that workspace.

## Detection

- **Modern:** checks all enabled biomes **except The Gray Shadow Space** (TGSS) every **5 seconds**. It retains the existing v5.2 image classification formula and per-biome thresholds. No other biome detection method has changed.
- **Legacy:** checks **only TGSS** for alerts, every **2 seconds**, using the classic v2 image similarity formula. It uses `ui/tgss1.png`, `ui/tgss2.png`, and `ui/tgss3.png` captured from the event. It also scores the other six original biome templates as negative references to avoid confusing TGSS with another biome; it can never notify for those biomes.
- Both methods read from the `ui/` directory. The old accelerated Modern TGSS checks were removed.
- Checks are scheduling targets; the existing monitor thread can pause while Discord responds to a request.

## Cooldowns

- Rainy World and Blood Moon: 6 minutes per workspace and biome.
- All other biomes: 12 minutes per workspace and biome.
- TGSS multi-ping (on by default in Developer): successful alerts are at least 5 seconds apart; after five successful alerts within two minutes, TGSS enters a 12-minute cooldown. Each workspace keeps separate timers.

## Workspaces and screenshots

Up to eight workspaces with their own areas, VIP links, colors, start/stop state, enable switches and cooldowns. Webhook, Role IDs, theme, language and Developer settings are shared. Settings are saved automatically. Screenshot options include full-monitor capture or just the detection area (+25 px margin optional) with selectable resolution limits. Discord notifications are always in English.

**Developer setting note:** the TGSS threshold field from previous versions is retained for config compatibility, but it does not affect TGSS alerts in v1.0.0: Legacy uses its original fixed threshold of 0.76 and 0.025 runner-up gap. The other biome thresholds remain configurable as before.

## Update from v6.0

Back up your existing `app_config.json` and copy it into the new version's folder before launching. Role IDs, webhook credentials, settings and workspaces are retained. Detection templates are replaced with the three new event captures.

## Privacy

`app_config.json` contains the private Discord webhook and may include VIP server links. Never publish this file or include it in bug reports. Check pending files in GitHub Desktop before committing; `.gitignore` excludes local configuration and logs. Do not publish the personal EX build.

This project is independent and is not affiliated with Roblox or Discord. Use it in accordance with applicable game and platform rules.

License: Apache-2.0; see [`LICENSE`](LICENSE). For change history see [`CHANGELOG.md`](CHANGELOG.md).
