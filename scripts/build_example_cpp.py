#!/usr/bin/env python3
"""
Builds the C++ bridge example (without Python).
Requires nats.c and EIPScanner to be already compiled.
Usage: python scripts/build_example_cpp.py
"""

import shutil
import sys
from pathlib import Path
from build_config import BuildConfig, IS_WINDOWS


def build_example_cpp(cfg=None):
    """Build the C++ bridge example."""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Building C++ example")
    print("=" * 70)

    nats_dir = cfg.deps_dir / "nats.c"
    eip_dir = cfg.deps_dir / "EIPScanner"
    examples_dir = cfg.root_dir / "examples"
    source = examples_dir / "example_cpp.cpp"

    if not source.exists():
        raise FileNotFoundError(f"Not found: {source}")

    # Verify that dependencies are compiled
    if not (nats_dir / "build").exists() or not (eip_dir / "build").exists():
        raise RuntimeError(
            "Dependencies are not compiled.\n"
            "Run first: python scripts/build_nats.py && python scripts/build_eipscanner.py"
        )

    build_dir = cfg.build_dir / "example_cpp"
    build_dir.mkdir(parents=True, exist_ok=True)
    output = build_dir / ("example_cpp.exe" if IS_WINDOWS else "example_cpp")

    if IS_WINDOWS:
        _build_msvc(cfg, nats_dir, eip_dir, source, output, build_dir)
    else:
        _build_gcc(cfg, nats_dir, eip_dir, source, output)

    print(f"\nOK Example compiled: {output}")
    print(f"   Run: {output}")


def _build_gcc(cfg, nats_dir, eip_dir, source, output):
    """Build with g++ (Linux)."""
    cfg.run_command([
        "g++", "-g", "-O0",
        "-Wall", "-Wextra",
        "-std=c++17",
        f"-I{nats_dir / 'src'}",
        f"-I{eip_dir / 'src'}",
        f"-I{cfg.src_dir}",
        str(source),
        str(cfg.src_dir / "EIPtoNATSBridge.cpp"),
        f"-L{cfg.lib_dir}",
        "-lnats",
        "-lEIPScanner",
        "-lpthread",
        f"-Wl,-rpath,{cfg.lib_dir}",
        "-o", str(output),
    ])


def _build_msvc(cfg, nats_dir, eip_dir, source, output, build_dir):
    """Build with CMake/MSVC (Windows)."""
    # Create temporary CMakeLists.txt
    cmakelists = build_dir / "CMakeLists.txt"

    # Convert paths to forward slashes for CMake
    nats_inc = str(nats_dir / "src").replace("\\", "/")
    eip_inc = str(eip_dir / "src").replace("\\", "/")
    src_dir = str(cfg.src_dir).replace("\\", "/")
    lib_dir = str(cfg.lib_dir).replace("\\", "/")
    source_str = str(source).replace("\\", "/")
    bridge_src = str(cfg.src_dir / "EIPtoNATSBridge.cpp").replace("\\", "/")
    output_dir = str(build_dir).replace("\\", "/")

    cmakelists.write_text(f"""cmake_minimum_required(VERSION 3.14)
project(example_cpp LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(example_cpp
    {source_str}
    {bridge_src}
)

target_include_directories(example_cpp PRIVATE
    {nats_inc}
    {eip_inc}
    {src_dir}
)

find_library(NATS_LIB NAMES nats PATHS {lib_dir} NO_DEFAULT_PATH)
find_library(EIP_LIB NAMES EIPScanner PATHS {lib_dir} NO_DEFAULT_PATH)

target_link_libraries(example_cpp PRIVATE ${{NATS_LIB}} ${{EIP_LIB}} ws2_32)

set_target_properties(example_cpp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY {output_dir}
)
foreach(CONFIG_TYPE ${{CMAKE_CONFIGURATION_TYPES}})
    string(TOUPPER ${{CONFIG_TYPE}} CONFIG_TYPE_UPPER)
    set_target_properties(example_cpp PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY_${{CONFIG_TYPE_UPPER}} {output_dir}
    )
endforeach()
""", encoding="utf-8")

    print("\nConfiguring with CMake...")
    # RelWithDebInfo: optimized like Release (compatible with Release DLLs)
    # but with debug symbols for breakpoint debugging
    cfg.run_command(["cmake", ".", "-DCMAKE_BUILD_TYPE=RelWithDebInfo"], cwd=build_dir)

    print("\nCompiling...")
    cfg.run_command(["cmake", "--build", ".", "--config", "RelWithDebInfo"], cwd=build_dir)


if __name__ == "__main__":
    try:
        build_example_cpp()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
