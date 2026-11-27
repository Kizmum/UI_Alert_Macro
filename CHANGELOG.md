# Changelog

## v1.0.0 — stable

- TGSS detection uses only the classic (Legacy v2) algorithm on the three new event-captured PNG templates.
- Removed TGSS recognition and its accelerated checks from the Modern engine.
- Modern still scans the remaining eight biomes at the same 5-second interval using the unchanged classifier.
- Legacy checks TGSS every 2 seconds and continues to use its existing ambiguity guard.
- Preserved independent workspace cooldowns, TGSS multi-ping, screenshot options, localization and auto-save.
- Updated application version strings and prepared GitHub release assets.

## v6.0 — prerelease

- Updated `tgss3.png`.
- Moved Legacy to the primary UI template set, removed `legacy_ui/`.
- Reduced Legacy TGSS checking to 2 seconds.

## v5.3 — prerelease

- Added the Legacy TGSS comparison method and optional accelerated TGSS sampling in the Modern engine.
