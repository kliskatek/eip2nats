#!/usr/bin/env python3
"""
Builds the Python binding (pybind11) for the bridge.
Requires nats.c and EIPScanner to be already compiled.
Usage: python scripts/build_binding.py
"""

import shutil
import sys
from build_config import BuildConfig, IS_WINDOWS, IS_LINUX


def _build_binding_gcc(cfg, nats_include, eip_include, ext_suffix):
    """Build the Python binding using g++ directly (Linux)."""
    import pybind11
    import sysconfig

    python_include = sysconfig.get_path('include')
    pybind_include = pybind11.get_include()

    output_name = cfg.src_dir / f"eip_nats_bridge{ext_suffix}"

    print(f"Python include: {python_include}")
    print(f"pybind11 include: {pybind_include}")
    print(f"Output: {output_name}")

    compile_cmd = [
        "g++",
        "-O3",
        "-Wall",
        "-shared",
        "-std=c++17",
        "-fPIC",
        f"-DEIP2NATS_VERSION=\"{cfg.version}\"",
        f"-I{pybind_include}",
        f"-I{nats_include}",
        f"-I{eip_include}",
        f"-I{cfg.src_dir}",
        f"-I{python_include}",
        str(cfg.src_dir / "bindings.cpp"),
        str(cfg.src_dir / "EIPtoNATSBridge.cpp"),
        "-o", str(output_name),
        f"-L{cfg.lib_dir}",
        "-lnats",
        "-lEIPScanner",
        "-lpthread",
        "-Wl,-rpath,$ORIGIN/lib",
    ]

    print("\nCompiling...")
    cfg.run_command(compile_cmd)

    print(f"OK Binding compiled: {output_name.name}")


def _build_binding_cmake(cfg, nats_include, eip_include):
    """Build the Python binding using CMake (Windows/MSVC)."""
    binding_build_dir = cfg.build_dir / "binding"
    binding_build_dir.mkdir(parents=True, exist_ok=True)

    # Copy CMakeLists.txt template to the build directory
    cmake_template = cfg.root_dir / "scripts" / "binding_CMakeLists.txt"
    cmake_dest = binding_build_dir / "CMakeLists.txt"
    shutil.copy2(cmake_template, cmake_dest)

    # Get pybind11 cmake directory
    import pybind11
    pybind11_cmake_dir = pybind11.get_cmake_dir()

    print(f"pybind11 cmake dir: {pybind11_cmake_dir}")
    print(f"NATS include: {nats_include}")
    print(f"EIP include: {eip_include}")
    print(f"Lib dir: {cfg.lib_dir}")
    print(f"Src dir: {cfg.src_dir}")

    # Use forward slashes for all paths - CMake handles them on all platforms
    # and backslashes cause escaping issues in CMake EVAL
    python_executable = sys.executable.replace('\\', '/')
    pybind11_cmake_dir_str = str(pybind11_cmake_dir).replace('\\', '/')
    nats_include_str = str(nats_include).replace('\\', '/')
    eip_include_str = str(eip_include).replace('\\', '/')
    src_dir_str = str(cfg.src_dir).replace('\\', '/')
    lib_dir_str = str(cfg.lib_dir).replace('\\', '/')

    cmake_args = [
        "cmake", ".",
        f"-Dpybind11_DIR={pybind11_cmake_dir_str}",
        f"-DNATS_INCLUDE_DIR={nats_include_str}",
        f"-DEIP_INCLUDE_DIR={eip_include_str}",
        f"-DSRC_DIR={src_dir_str}",
        f"-DLIB_DIR={lib_dir_str}",
        f"-DPython_EXECUTABLE={python_executable}",
        f"-DPython3_EXECUTABLE={python_executable}",
        f"-DEIP2NATS_VERSION={cfg.version}",
        "-DCMAKE_BUILD_TYPE=Release",
    ]

    print("\nConfiguring binding with CMake...")
    cfg.run_command(cmake_args, cwd=binding_build_dir)

    print("\nCompiling binding...")
    cfg.run_command([
        "cmake", "--build", ".", "--config", "Release"
    ], cwd=binding_build_dir)

    # Verify output
    import sysconfig
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    expected_output = cfg.src_dir / f"eip_nats_bridge{ext_suffix}"

    if not expected_output.exists():
        # On Windows, pybind11 may produce the file with .pyd extension
        pyd_files = list(cfg.src_dir.glob("eip_nats_bridge*.pyd"))
        if pyd_files:
            print(f"OK Binding compiled: {pyd_files[0].name}")
        else:
            print("Searching for output in build dir...")
            for item in binding_build_dir.rglob("eip_nats_bridge*"):
                print(f"  Found: {item}")
            raise RuntimeError("Compiled binding not found")
    else:
        print(f"OK Binding compiled: {expected_output.name}")



def build_binding(cfg=None):
    """Build the Python binding."""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Building Python binding")
    print("=" * 70)

    nats_dir = cfg.deps_dir / "nats.c"
    eip_dir = cfg.deps_dir / "EIPScanner"

    nats_include = nats_dir / "src"
    eip_include = eip_dir / "src"

    # Verify that source files exist
    binding_src = cfg.src_dir / "bindings.cpp"
    bridge_src = cfg.src_dir / "EIPtoNATSBridge.cpp"

    if not binding_src.exists() or not bridge_src.exists():
        raise FileNotFoundError("Source files not found in src/eip2nats/")

    import sysconfig
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    print(f"Extension suffix: {ext_suffix}")

    if IS_WINDOWS:
        _build_binding_cmake(cfg, nats_include, eip_include)
    else:
        _build_binding_gcc(cfg, nats_include, eip_include, ext_suffix)


if __name__ == "__main__":
    try:
        build_binding()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
