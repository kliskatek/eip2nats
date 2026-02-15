#!/usr/bin/env python3
"""
Shared configuration and utilities for build scripts.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")


class BuildConfig:
    """Common paths and utilities for all build scripts."""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.build_dir = self.root_dir / "build"
        self.deps_dir = self.build_dir / "dependencies"
        self.lib_dir = self.root_dir / "src" / "eip2nats" / "lib"
        self.src_dir = self.root_dir / "src" / "eip2nats"

        # Create directories
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        self.deps_dir.mkdir(parents=True, exist_ok=True)

    def run_command(self, cmd, cwd=None, env=None):
        """Run a shell command."""
        print(f"\n>  {' '.join(str(c) for c in cmd)}")

        result = subprocess.run(
            cmd,
            cwd=cwd or self.root_dir,
            env=env or os.environ.copy(),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            raise RuntimeError(f"Command failed: {' '.join(str(c) for c in cmd)}")

        if result.stdout:
            print(result.stdout)

        return result

    def cmake_build(self, build_dir, config="Release"):
        """Build with cmake (cross-platform: make on Linux, msbuild on Windows)."""
        if IS_WINDOWS:
            self.run_command([
                "cmake", "--build", ".", "--config", config
            ], cwd=build_dir)
        else:
            self.run_command([
                "make", "-j", str(os.cpu_count() or 4)
            ], cwd=build_dir)

    def copy_shared_libs(self, search_dirs, pattern_base):
        """Copy shared libraries to lib_dir. Returns number of files copied."""
        copied = 0

        if IS_WINDOWS:
            # On Windows, search for .dll and .lib in Release/ subdirectories too
            all_search_dirs = []
            for d in search_dirs:
                all_search_dirs.append(d)
                release_dir = d / "Release"
                if release_dir.exists():
                    all_search_dirs.append(release_dir)

            for search_dir in all_search_dirs:
                if not search_dir.exists():
                    continue
                # Copy .dll
                for lib_file in search_dir.glob(f"{pattern_base}*.dll"):
                    if lib_file.is_file():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
                # Copy .lib (import libraries for linking)
                for lib_file in search_dir.glob(f"{pattern_base}*.lib"):
                    if lib_file.is_file():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
        else:
            # Linux: copy .so and symlinks
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                # Real files first
                for lib_file in search_dir.glob(f"{pattern_base}*.so*"):
                    if lib_file.is_file() and not lib_file.is_symlink():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
                # Then symlinks
                for lib_file in search_dir.glob(f"{pattern_base}*.so*"):
                    if lib_file.is_symlink():
                        link_target = lib_file.readlink()
                        dst = self.lib_dir / lib_file.name
                        if dst.exists():
                            dst.unlink()
                        dst.symlink_to(link_target.name)
                        print(f"  + {lib_file.name} -> {link_target.name} (symlink)")
                        copied += 1

        return copied
