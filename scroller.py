#!/usr/bin/env python3
"""Auto-scroll Synology Photos Android app via ADB to force thumbnail loading."""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time

SYNOLOGY_PHOTOS_PACKAGE = "com.synology.projectkailash"
SYNOLOGY_PHOTOS_ACTIVITY = f"{SYNOLOGY_PHOTOS_PACKAGE}/.ui.splash.SplashActivity"

ADB_COMMON_PATHS = [
    os.path.expanduser("~/Library/Android/sdk/platform-tools"),  # macOS default
    os.path.expanduser("~/Android/Sdk/platform-tools"),  # Linux default
    r"C:\Users\{}\AppData\Local\Android\Sdk\platform-tools".format(os.getenv("USERNAME", "")),  # Windows
    "/usr/local/bin",
    "/opt/homebrew/bin",
]

_adb_path: str | None = None


def find_adb() -> str:
    global _adb_path
    if _adb_path:
        return _adb_path

    # Check if already in PATH
    found = shutil.which("adb")
    if found:
        _adb_path = found
        return _adb_path

    # Search common install locations
    for directory in ADB_COMMON_PATHS:
        candidate = os.path.join(directory, "adb")
        if platform.system() == "Windows":
            candidate += ".exe"
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            _adb_path = candidate
            return _adb_path

    print("Error: adb not found in PATH or common install locations.")
    print("Install Android Platform Tools and ensure adb is accessible.")
    sys.exit(1)


def run_adb(args: list[str], device: str | None = None) -> subprocess.CompletedProcess:
    cmd = [find_adb()]
    if device:
        cmd += ["-s", device]
    cmd += args
    return subprocess.run(cmd, capture_output=True, text=True)


def check_adb():
    adb = find_adb()
    result = subprocess.run([adb, "version"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: adb found but failed to run.")
        sys.exit(1)
    print(f"Using adb: {adb}")


def get_device(device: str | None) -> str | None:
    if device:
        return device
    result = run_adb(["devices"])
    lines = [l for l in result.stdout.strip().splitlines()[1:] if l.strip() and "device" in l]
    if not lines:
        print("Error: No devices found. Connect a device and enable USB debugging.")
        sys.exit(1)
    if len(lines) > 1:
        print("Multiple devices found. Specify one with --device:")
        for line in lines:
            print(f"  {line.split()[0]}")
        sys.exit(1)
    return lines[0].split()[0]


def launch_app(device: str | None):
    print(f"Launching {SYNOLOGY_PHOTOS_PACKAGE}...")
    result = run_adb(["shell", "am", "start", "-n", SYNOLOGY_PHOTOS_ACTIVITY], device)
    if result.returncode != 0:
        print(f"Warning: Could not launch app: {result.stderr.strip()}")
    time.sleep(3)


def swipe(device: str | None, distance: int, duration: int):
    # Swipe upward from center of screen
    # Start point: center-x, lower area; End point: center-x, lower area minus distance
    start_x = 540
    start_y = 1500
    end_x = start_x
    end_y = start_y - distance
    run_adb(["shell", "input", "swipe", str(start_x), str(start_y), str(end_x), str(end_y), str(duration)], device)


def take_screenshot(device: str | None, index: int):
    remote_path = "/sdcard/thumb_scroll_debug.png"
    local_path = f"screenshot_{index:04d}.png"
    run_adb(["shell", "screencap", "-p", remote_path], device)
    run_adb(["pull", remote_path, local_path], device)
    print(f"  Screenshot saved: {local_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto-scroll Synology Photos to load thumbnails")
    parser.add_argument("--device", help="ADB device serial or IP:port (default: auto-detect)")
    parser.add_argument("--swipes", type=int, default=200, help="Total number of swipes (default: 200)")
    parser.add_argument("--pause", type=float, default=3.0, help="Pause after each swipe in seconds (default: 3.0)")
    parser.add_argument("--swipe-duration", type=int, default=2000, help="Duration of each swipe in ms (default: 2000)")
    parser.add_argument("--distance", type=int, default=800, help="Pixels per swipe (default: 800)")
    parser.add_argument("--no-launch", action="store_true", help="Skip auto-launching the app")
    parser.add_argument("--debug-screenshots", action="store_true", help="Save a screenshot every 10 swipes")
    args = parser.parse_args()

    check_adb()
    device = get_device(args.device)
    print(f"Using device: {device}")

    if not args.no_launch:
        launch_app(device)

    total_time = args.swipes * (args.swipe_duration / 1000 + args.pause)
    print(f"Starting {args.swipes} swipes (~{total_time / 60:.1f} min estimated)")
    print("Press Ctrl+C to stop\n")

    try:
        for i in range(1, args.swipes + 1):
            swipe(device, args.distance, args.swipe_duration)
            if args.debug_screenshots and i % 10 == 0:
                take_screenshot(device, i)
            print(f"  Swipe {i}/{args.swipes}", end="\r")
            time.sleep(args.pause)
    except KeyboardInterrupt:
        print(f"\n\nStopped after {i - 1} swipes.")
        sys.exit(0)

    print(f"\n\nDone! Completed {args.swipes} swipes.")


if __name__ == "__main__":
    main()
