# Changelog

## [5.3] - 2026-11-14

- Preserved the v5.2 full classification scan for every other biome (every 5 seconds).
- Added an adaptive **TGSS-only** modern scan (every 0.75 seconds when TGSS is suspected), with full competition verification before alerting.
- Restored the **v2 TGSS** detection method as a separate check every 2.5 seconds; included the original reference images as static PNGs in `legacy_ui/`.
- Preserved workspace-scoped, biome-scoped cooldowns and the existing TGSS multi-ping behavior, shared by both detection engines.
- No changes to the user-facing settings or workspaces.

## [5.2] - 2026-11-10

- Updated three TGSS reference images.
- Equalized the modern TGSS detection threshold to 0.66.
- Per-workspace and per-biome cooldowns: Rainy World/Blood Moon 6 minutes, others 12 minutes.
- Optional TGSS multi-ping with 5-second intervals and five-send/2-minute window.

## [5.1]

- Added biome enable switches, workspace disable state, persistent detection overlays, and automatic settings saving.
