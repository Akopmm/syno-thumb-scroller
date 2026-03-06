# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Single-script Python tool (`scroller.py`) that auto-scrolls the Synology Photos Android app via ADB to force lazy thumbnail loading. Pure UI automation — simulates slow upward swipes so the app fetches and caches thumbnails from the NAS.

## Run

```bash
python scroller.py                    # default: 200 swipes, 3s pause
python scroller.py --swipes 500 --pause 4   # large library
python scroller.py --debug-screenshots      # saves screenshot every 10 swipes
```

## Key Details

- **Python 3.10+**, no pip dependencies (uses only stdlib + `subprocess` calls to `adb`)
- Synology Photos package name: `com.synology.dsmobile` (constant `SYNOLOGY_PHOTOS_PACKAGE` in `scroller.py`)
- ADB must be installed and in PATH; device connected via USB or WiFi
- No tests, no linter, no build step — single-file script

## Architecture

Everything lives in `scroller.py`. The script:
1. Parses CLI args with `argparse`
2. Connects to Android device via ADB (`adb devices` / `adb -s <device>`)
3. Optionally launches Synology Photos with `adb shell am start`
4. Loops N times: `adb shell input swipe` + `time.sleep(pause)`
5. Optionally captures screenshots with `adb shell screencap`

## CLI Options

`--device`, `--swipes` (default 200), `--pause` (default 3.0s), `--swipe-duration` (default 2000ms), `--distance` (default 800px), `--no-launch`, `--debug-screenshots`
