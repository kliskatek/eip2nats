#!/usr/bin/env python3
"""
Build wheels for multiple Python versions and platforms using cibuildwheel.

Requires:
  pip install cibuildwheel

For Linux builds (from Windows or Linux):
  Docker must be running. ARM builds use QEMU emulation.

Usage:
  python scripts/build_wheels.py                   # All platforms (Windows + Linux)
  python scripts/build_wheels.py --platform linux   # Linux only (x64 + arm)
  python scripts/build_wheels.py --platform windows # Windows only

Wheels are output to dist/. Then publish with:
  hatch publish
"""

import argparse
import subprocess
import sys


def run_cibuildwheel(platform):
    """Run cibuildwheel for a specific platform. Returns exit code."""
    cmd = [sys.executable, "-m", "cibuildwheel", "--output-dir", "dist",
           "--platform", platform]
    print(f"\n{'='*60}")
    print(f"  Building wheels for: {platform}")
    print(f"{'='*60}\n")
    print(f"Running: {' '.join(cmd)}\n")
    return subprocess.run(cmd).returncode


def main():
    parser = argparse.ArgumentParser(description="Build wheels with cibuildwheel")
    parser.add_argument(
        "--platform",
        choices=["all", "linux", "windows"],
        default="all",
        help="Target platform (default: all)",
    )
    args = parser.parse_args()

    # Check cibuildwheel is installed
    try:
        import cibuildwheel  # noqa: F401
    except ImportError:
        print("cibuildwheel not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cibuildwheel"])

    if args.platform == "all":
        platforms = ["windows", "linux"]
    else:
        platforms = [args.platform]

    failed = []
    for platform in platforms:
        rc = run_cibuildwheel(platform)
        if rc != 0:
            failed.append(platform)
            print(f"\nBuild FAILED for {platform}", file=sys.stderr)

    # Summary
    print(f"\n{'='*60}")
    if not failed:
        print("All wheels built successfully in dist/")
        print("To publish: hatch publish")
    else:
        print(f"Failed platforms: {', '.join(failed)}", file=sys.stderr)
    print(f"{'='*60}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
