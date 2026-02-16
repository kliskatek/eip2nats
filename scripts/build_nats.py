#!/usr/bin/env python3
"""
Builds nats.c from source.
Usage: python scripts/build_nats.py
"""

import sys
from build_config import BuildConfig, IS_WINDOWS, IS_LINUX


def build_nats(cfg=None):
    """Build nats.c"""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Building nats.c")
    print("=" * 70)

    nats_dir = cfg.deps_dir / "nats.c"
    nats_build_dir = nats_dir / "build"

    # Clone if not present
    if not nats_dir.exists():
        print("Cloning nats.c from GitHub...")
        cfg.run_command([
            "git", "clone",
            "--depth", "1",
            "--branch", "v3.8.2",
            "https://github.com/nats-io/nats.c.git",
            str(nats_dir)
        ])
    else:
        print("nats.c already exists, skipping clone")

    # Build
    nats_build_dir.mkdir(exist_ok=True)

    cmake_args = [
        "cmake", "..",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DBUILD_TESTING=OFF",
        "-DNATS_BUILD_STREAMING=OFF",
        "-DNATS_BUILD_LIB_SHARED=ON",
        "-DNATS_BUILD_LIB_STATIC=OFF",
        "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
    ]

    # Disable TLS - not needed for EIP/NATS bridge on local networks
    # Also avoids OpenSSL version issues on manylinux2014 and Windows
    cmake_args.append("-DNATS_BUILD_WITH_TLS=OFF")

    print("\nConfiguring nats.c with CMake...")
    cfg.run_command(cmake_args, cwd=nats_build_dir)

    print("\nBuilding nats.c...")
    cfg.cmake_build(nats_build_dir)

    # Copy libraries
    print("\nCopying nats.c libraries...")
    search_dirs = [nats_build_dir, nats_build_dir / "src"]
    copied = cfg.copy_shared_libs(search_dirs, "libnats" if IS_LINUX else "nats")

    if copied == 0:
        print("\n  No libraries found")
        print("Searching build directory:")
        for item in nats_build_dir.rglob("nats*" if IS_WINDOWS else "libnats*"):
            print(f"  Found: {item}")
        raise RuntimeError("No compiled nats libraries found")

    print(f"OK nats.c built - {copied} file(s) copied")


if __name__ == "__main__":
    try:
        build_nats()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
