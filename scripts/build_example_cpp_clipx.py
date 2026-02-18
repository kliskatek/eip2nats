#!/usr/bin/env python3
"""
Builds the standalone C++ ClipX example (EIPScanner only, no NATS/bridge).
Requires EIPScanner to be already compiled.
Usage: python scripts/build_example_cpp_clipx.py
"""

import sys
from pathlib import Path
from build_config import BuildConfig, IS_WINDOWS


def build_example_cpp_clipx(cfg=None):
    """Build the standalone C++ ClipX example."""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Building C++ ClipX example (standalone, no NATS)")
    print("=" * 70)

    eip_dir = cfg.deps_dir / "EIPScanner"
    examples_dir = cfg.root_dir / "examples"
    source = examples_dir / "example_cpp_clipx.cpp"

    if not source.exists():
        raise FileNotFoundError(f"Not found: {source}")

    if not (eip_dir / "build").exists():
        raise RuntimeError(
            "EIPScanner is not compiled.\n"
            "Run first: python scripts/build_eipscanner.py"
        )

    build_dir = cfg.build_dir / "example_cpp_clipx"
    build_dir.mkdir(parents=True, exist_ok=True)
    output = build_dir / ("example_cpp_clipx.exe" if IS_WINDOWS else "example_cpp_clipx")

    if IS_WINDOWS:
        _build_msvc(cfg, eip_dir, source, output, build_dir)
    else:
        _build_gcc(cfg, eip_dir, source, output)

    print(f"\nOK Example compiled: {output}")
    print(f"   Run: {output}")


def _build_gcc(cfg, eip_dir, source, output):
    """Build with g++ (Linux)."""
    cfg.run_command([
        "g++", "-g", "-O0",
        "-Wall", "-Wextra",
        "-std=c++17",
        f"-I{eip_dir / 'src'}",
        str(source),
        f"-L{cfg.lib_dir}",
        "-lEIPScanner",
        "-lpthread",
        f"-Wl,-rpath,{cfg.lib_dir}",
        "-o", str(output),
    ])


def _build_msvc(cfg, eip_dir, source, output, build_dir):
    """Build with CMake/MSVC (Windows)."""
    cmakelists = build_dir / "CMakeLists.txt"

    eip_inc = str(eip_dir / "src").replace("\\", "/")
    lib_dir = str(cfg.lib_dir).replace("\\", "/")
    source_str = str(source).replace("\\", "/")
    output_dir = str(build_dir).replace("\\", "/")

    cmakelists.write_text(f"""cmake_minimum_required(VERSION 3.14)
project(example_cpp_clipx LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)

add_executable(example_cpp_clipx
    {source_str}
)

target_include_directories(example_cpp_clipx PRIVATE
    {eip_inc}
)

find_library(EIP_LIB NAMES EIPScanner PATHS {lib_dir} NO_DEFAULT_PATH)

target_link_libraries(example_cpp_clipx PRIVATE ${{EIP_LIB}} ws2_32)

set_target_properties(example_cpp_clipx PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY {output_dir}
)
foreach(CONFIG_TYPE ${{CMAKE_CONFIGURATION_TYPES}})
    string(TOUPPER ${{CONFIG_TYPE}} CONFIG_TYPE_UPPER)
    set_target_properties(example_cpp_clipx PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY_${{CONFIG_TYPE_UPPER}} {output_dir}
    )
endforeach()
""", encoding="utf-8")

    print("\nConfiguring with CMake...")
    cfg.run_command(["cmake", ".", "-DCMAKE_BUILD_TYPE=RelWithDebInfo"], cwd=build_dir)

    print("\nCompiling...")
    cfg.run_command(["cmake", "--build", ".", "--config", "RelWithDebInfo"], cwd=build_dir)


if __name__ == "__main__":
    try:
        build_example_cpp_clipx()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
