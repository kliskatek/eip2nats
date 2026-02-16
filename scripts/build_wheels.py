#!/usr/bin/env python3
"""
Build wheels for multiple Python versions and platforms using cibuildwheel.

Requires:
  pip install cibuildwheel

For Linux builds (from Windows or Linux):
  Docker must be running. ARM builds use QEMU emulation.

Usage:
  python scripts/build_wheels.py                  # All platforms
  python scripts/build_wheels.py --platform linux  # Linux only (x64 + arm)
  python scripts/build_wheels.py --platform windows # Windows only

Wheels are output to dist/. Then publish with:
  hatch publish
"""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description="Build wheels with cibuildwheel")
    parser.add_argument(
        "--platform",
        choices=["auto", "linux", "windows"],
        default="auto",
        help="Target platform (default: auto-detect current OS)",
    )
    args = parser.parse_args()

    # Check cibuildwheel is installed
    try:
        import cibuildwheel  # noqa: F401
    except ImportError:
        print("cibuildwheel not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cibuildwheel"])

    cmd = [sys.executable, "-m", "cibuildwheel", "--output-dir", "dist"]

    if args.platform != "auto":
        cmd += ["--platform", args.platform]

    print(f"\nRunning: {' '.join(cmd)}\n")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\nWheels built successfully in dist/")
        print("To publish: hatch publish")
    else:
        print("\nBuild failed", file=sys.stderr)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
