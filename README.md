# UI Alert Macro v5.2

Windows desktop utility for recognizing nine on-screen biome alerts and sending Discord role notifications with screenshots.

**Creators:** Kizmum (`mindustry` on Discord) and Fonar (`nikline_` on Discord).

## Requirements

- Windows 10/11
- Python 3.13
- The dependencies listed in `requirements.txt`: `mss`, `opencv-python`, `numpy`
- A Discord webhook URL and the Discord role IDs you want the macro to mention

## Install and run

1. Download the **UI_Alert_Macro_v5_2.zip** release asset and extract the entire folder. Keep `ui/` beside `ui_alert_macro_gui.py`.
2. Run `install.bat` to install Python dependencies.
3. Run `start.bat` to open the application.
4. In **Settings and Other**, paste your Discord webhook and the role IDs. You can paste a full mention such as `<@&1537542231953506305>`; the field keeps only digits.
5. Enable the biomes you want to track, then go to **Main** and select the detection region for each workspace.
6. Press **F1** to start all enabled workspaces, **F2** to stop them; each workspace also has its own START/STOP button.

The macro checks each running workspace every ~5 seconds. It can create up to eight workspaces, each with its own detection rectangle, VIP link, and enabled state. Roles, webhook and developer options are shared.

## Recognition and templates

The same recognition algorithm and default score threshold (**0.66**) are used for every biome, including The Gray Shadow Space (TGSS). For each biome, the best-scoring image among its reference PNGs is used.

| Biome | Templates | Cooldown per workspace and biome |
| --- | --- | --- |
| Rainy World | `rn1.png`, `rn2.png` | 6 min |
| Blood Moon | `bm1.png`, `bm2.png` | 6 min |
| Cosmic Nebula | `cn1.png`, `cn2.png` | 12 min |
| Celestial Moon | `cm1.png`, `cm2.png` | 12 min |
| Cryogenic World | `cw1.png`, `cw2.png` | 12 min |
| The Mortal Blackout | `tmb1.png`, `tmb2.png`, `tmb3.png` | 12 min |
| The Gray Shadow Space | `tgss1.png`, `tgss2.png`, `tgss3.png` | 12 min or TGSS multi-ping |
| The Crimson Trigon | `tct1.png`, `tct2.png` | 12 min |
| Veylune | `v1.png`, `v2.png` | 12 min |

### TGSS multi-ping (enabled by default)

Under **Settings and Other → Developer**, there is an option labeled **“Multi-ping to make SURE you don't miss TGSS (recommended)”**. With this enabled, TGSS has a 5-second cooldown after each successful notification. If **five successful TGSS notifications occur within two minutes of the first one**, TGSS is placed on a **12-minute cooldown**. If two minutes pass before five sends, the next successful send starts a new series. Each workspace maintains its own TGSS burst and cooldown. If the option is disabled, TGSS uses the regular 12-minute cooldown.

Developer mode also lets you adjust per-biome thresholds and screenshot quality. Screenshot modes are full monitor or the chosen region, optionally extended by 25 pixels on each side, with a 1080p default quality cap.

## Migrating from v5.1

To keep your settings, copy your existing `app_config.json` into the new folder **before the first launch**. The previous TGSS default threshold of `0.63` is automatically migrated to `0.66`; other custom threshold values are retained. Existing webhook, role IDs, VIP links, languages, themes, workspace regions and enable/disable states are retained.

## Security and privacy

**Do not upload `app_config.json` to GitHub or share it.** It contains your Discord webhook URL (which acts as a secret), and possibly private VIP links. `.gitignore` excludes this file, but always inspect your commits before publishing.

Discord notifications are in English regardless of the selected UI language. They include the selected role mention, the biome name, an optional VIP link and an attached screenshot.

## Validation status

- Python source compiled successfully.
- The 20 reference images were each recognized as their intended biome.
- Cooldowns, TGSS multi-ping rules, configuration migration, Discord request formatting, screenshot cropping and GUI controls were tested in a simulated/headless environment.
- **Actual gameplay capture on Windows and live Discord delivery have not been verified here.** Before announcing a stable public release, test a real TGSS event and other biome alerts in Roblox and verify notifications on a private Discord test channel.

The project is independent and not affiliated with Roblox or Discord. Ensure use of such tools complies with the rules of the games and services involved.
