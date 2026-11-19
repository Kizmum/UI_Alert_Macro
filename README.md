# UI Alert Macro v5.3

Windows desktop application for recognizing on-screen Roblox biome notifications and sending Discord role alerts with screenshots.

**Creators:** Kizmum (`mindustry`) and Fonar (`nikline_`).

## Installation

- **Requirements:** Windows 10/11, Python 3.13.
- Download the `UI_Alert_Macro_v5_3.zip` asset from GitHub Releases. **Extract the entire archive** before running it.
- Keep both `ui/` and `legacy_ui/` beside `ui_alert_macro_gui.py`.
- Run `install.bat` once (installs `mss`, `opencv-python`, `numpy`). Then run `start.bat`.
- In **Settings and Other**, paste your Discord webhook URL and role IDs, and enable the desired biomes. Role mentions such as `<@&123456789012345678>` are converted to digits.
- In **Main**, adjust the detection area. `F1` starts every enabled workspace, `F2` stops every workspace. Each workspace's START/STOP button operates independently.

## Recognition in v5.3

All **non-TGSS biomes** use the unchanged v5.2 recognition method and are checked once every **5 seconds per enabled workspace**.

For **The Gray Shadow Space (TGSS)** the macro now uses two separate detection engines, both restricted to sending TGSS notifications:

1. **Modern (v5.2) engine:** the original v5.2 classifier uses `tgss1.png`, `tgss2.png`, `tgss3.png`, a default threshold of **0.66**, and the usual ambiguity check (`0.05` gap). On the ordinary 5-second full scan, if the TGSS-only score comes within **0.12** of its configured threshold, it activates **TGSS-only accelerated sampling every 0.75 seconds**. The accelerated mode lasts while the UI continues to look similar to TGSS (up to 8 seconds from the most recent suspicious check). A candidate above threshold is verified against the other biomes on the same frame **before** an alert is sent; that confirmation can only send a TGSS alert, never another biome alert.
2. **Legacy (v2) engine:** independently checks for TGSS every **2.5 seconds**, using the original v2 comparison formula (55% grayscale correlation, 25% edge correlation, 20% RGB histogram correlation), the original threshold **0.76**, and original ambiguity gap **0.025**. It uses the seven reference images in `legacy_ui/` to rule out confusion with other old biomes, but **can send alerts only for TGSS**. `legacy_ui/gray_shadow_space.png` contains the first frame of the original animated WebP (formerly misnamed `Greyshadowspacealert1.png`) saved as a real static PNG.

The legacy threshold intentionally does **not** change when you alter TGSS's modern threshold in Developer settings: it reproduces the v2 algorithm. The standard TGSS reference PNGs in `ui/` remain unchanged from v5.2.

### Cooldowns (unchanged from v5.2)

- Rainy World and Blood Moon: **6 minutes** per workspace and biome.
- All other biomes: **12 minutes** per workspace and biome.
- TGSS **Multi-ping** is enabled by default in Developer: successful TGSS alerts have a **5-second** cooldown. After **five successful TGSS alerts within two minutes**, TGSS gets a **12-minute** cooldown. Each workspace has its own history and cooldown. Disabling multi-ping gives TGSS the regular 12-minute cooldown.
- Switching recognition engines does not bypass cooldown: a TGSS alert from either engine uses the **same TGSS cooldown within that workspace**.

## Workspaces, settings and screenshots

Up to eight workspaces, independent detection regions, VIP links, colors, START/STOP state, workspace enable switches, and independent cooldowns. Shared Discord webhook, role IDs, language, themes and Developer settings. Settings apply and save automatically. Screenshots can capture the monitor or detection region (optional +25 px margin), with selectable resolution caps. Discord notifications are always in English.

## Updating from v5.2

Keep a backup of `app_config.json`. Copy it into the extracted v5.3 folder **before first launch** if you want to preserve settings, role IDs, webhook and workspaces. Do **not** upload this file to a public repository.

## Important notes

- The macro **does not** use every frame in the original animation. Legacy recognition is based on the same first frame v2 could read.
- A likely TGSS triggers accelerated checks, but a TGSS score alone never overrides the ambiguity check used to prevent false positives.
- During Discord upload the existing monitor thread waits for the HTTP response; this is a pre-existing behavior. Scan intervals are scheduling targets, not guaranteed real-time deadlines.
- Recognition on reference images, timing and cooldown logic have been tested offline. **Actual Roblox events and live Discord webhook delivery must be tested on Windows before labeling this a fully verified stable release.**
- This project is independent and is not affiliated with Roblox or Discord. Ensure use is consistent with applicable platform/game rules.

## Privacy & GitHub

`app_config.json` may contain **private Discord webhook credentials and VIP links**. Never publish it or include it in an issue report. `.gitignore` excludes it and local log files. Check changed files in GitHub Desktop before committing.

For each GitHub release, create a new tag, e.g. `v5.3`, and attach the `UI_Alert_Macro_v5_3.zip` archive. Older tagged releases remain downloadable.

License: **Apache-2.0** (the license already used in the project). See [`LICENSE`](LICENSE) and [`CHANGELOG.md`](CHANGELOG.md).
