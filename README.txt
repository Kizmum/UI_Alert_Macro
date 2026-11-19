UI ALERT MACRO v5.3
===================

1. Extract the ENTIRE ZIP, including ui/ and legacy_ui/.
2. Windows + Python 3.13: run install.bat, then start.bat.
3. Set a Discord webhook and numeric role IDs in Settings and Other.
4. Enable the biomes and choose a screen region in Main.
5. F1 starts all enabled workspaces; F2 stops all. Main START/STOP affects the selected workspace only.

NEW IN v5.3
-----------
* All non-TGSS biomes still use the unchanged v5.2 scan every 5 seconds.
* TGSS: modern accelerated 0.75-second checks on suspected TGSS.
* TGSS: original v2 image recognition running separately every 2.5 seconds.
* Both TGSS engines share the existing workspace cooldown and multi-ping settings.

For details see README.md and CHANGELOG.md.

Never publish app_config.json; it contains a secret Discord webhook.

Creators: Kizmum (mindustry), Fonar (nikline_).
