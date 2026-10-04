# # <ins>Unofficial WARDOGS Offline Calculator</ins>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**Offline Port by RealxAlucard - Original Calculator by Apollyon**

An unofficial Windows desktop port of the open-source
[WARDOGS Artillery Calculator](https://github.com/apollyon-sys/wardogs-calculator) (MIT) that runs
**fully offline**. Not affiliated with or endorsed by **BULKHEAD**, **Team17** or the **WARDOGS development team**.

All calculator logic is **`@apollyon-sys`** work. This repo only contains the changes needed to make it a
self-contained desktop app.

## What changed from the original
- Packaged with Electron; a tiny local web server serves the site on `127.0.0.1` (no internet needed).
- All three maps (Bakurani, Ozeti, Zestafona), colour and black & white, use **locally bundled tiles**.
- Removed/disabled everything that talks to the original project's servers: asset CDN and its access
  gateway, live team lobbies, the feedback form, analytics and the optional terrain-correction data.
  The app also blocks any request that is not to the local machine.
- Removed the standalone mobile site (this is a desktop app) and the "Community partner" badge.
- Footer credit changed; "Feedback and Bugs" links to the port author's Discord; version is `1.0.0`
  (based on calculator version 1.10.1).

## Repo layout
| Path | Purpose |
|---|---|
| `patches/offline-port-source.patch` | source changes against the upstream commit in `patches/upstream-commit.txt` |
| `scripts/offline_patch.py` | post-build patches applied to the upstream `dist/` output |
| `electron/` | desktop shell (`main.js`, `preload.js`, `package.json`, icon) |
| `installer/installer.nsi` | NSIS installer script |
| `tools/build_tiles.py` | tile generator: your own top-down map capture + calibration points -> tile pyramid |
| `LICENSE-upstream-MIT.txt`, `NOTICE.txt` | upstream license and credits (keep these) |

## Map tiles are NOT in this repo
The tiles come from in-game captures (game imagery, ~1.8 GB), so they are not committed here.
`tools/build_tiles.py` shows how they were made: edit the constants at the top (input image, output
folder, calibration points, and `CORRECTIONS = []` for a new map; `BOUNDS` is the shared `tileBounds`
square from the map configs). Each map needs 21,845 tiles (zoom 0-7).

# Installation of [RELEASE](https://github.com/RealxAlucard/WARDOGS-Offline-Calculator/releases/tag/Release)
    1. To install the calculator, simply download the setup.exe "wardogs-offline-installer-v5.exe" and run it.
    2. This will prompt you with an installer and simply choose where you want to install to.
    3. After installation, navigate to the "...\WARDOGS Artillery Calculator\" folder that has the "WARDOGS Calculator - Offline.exe" and double click to run.
    4. (2) Things will occur: 
        1. The installer will do an initial tile map setup and *Ta-da* *[For First Time Installs]*
        2. It'll work.
    5. Delete Setup.exe after installation and enjoy.
__*Please note that the [setup.exe](https://github.com/RealxAlucard/WARDOGS-Offline-Calculator/releases/tag/Release) takes up <ins>~2.0GB</ins>. However, the calculator app only takes up <ins>~228MB</ins> of space on the storage drive.*__

# Interface

| Black/White |
| --- |
| <img src="assets/Preview_gray.png"> |

| Color |
| --- |
| <img src="assets/Preview_color.png"> |
