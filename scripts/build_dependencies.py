#!/usr/bin/env python3
"""
Script para compilar todas las dependencias externas y el modulo Python.
Este script se ejecuta automaticamente cuando se hace 'hatch build'.
Soporta Linux (x86_64/aarch64) y Windows (x64) con MSVC.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")


class DependencyBuilder:
    """Construye nats.c, EIPScanner y el binding Python"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.build_dir = self.root_dir / "build"
        self.deps_dir = self.build_dir / "dependencies"
        self.lib_dir = self.root_dir / "src" / "eip2nats" / "lib"
        self.src_dir = self.root_dir / "src" / "eip2nats"

        # Crear directorios
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        self.deps_dir.mkdir(parents=True, exist_ok=True)

    def run_command(self, cmd, cwd=None, env=None):
        """Ejecuta un comando shell"""
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

    def _cmake_build(self, build_dir, config="Release"):
        """Build with cmake (cross-platform: uses make on Linux, msbuild on Windows)"""
        if IS_WINDOWS:
            self.run_command([
                "cmake", "--build", ".", "--config", config
            ], cwd=build_dir)
        else:
            self.run_command([
                "make", "-j", str(os.cpu_count() or 4)
            ], cwd=build_dir)

    def _copy_shared_libs(self, search_dirs, pattern_base, lib_type="so"):
        """Copy shared libraries to lib_dir. Returns count of files copied."""
        copied = 0

        if IS_WINDOWS:
            # On Windows, look for .dll and .lib in Release/ subdirectories too
            all_search_dirs = []
            for d in search_dirs:
                all_search_dirs.append(d)
                release_dir = d / "Release"
                if release_dir.exists():
                    all_search_dirs.append(release_dir)

            for search_dir in all_search_dirs:
                if not search_dir.exists():
                    continue
                # Copy .dll files
                for lib_file in search_dir.glob(f"{pattern_base}*.dll"):
                    if lib_file.is_file():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
                # Copy .lib import libraries (needed for linking)
                for lib_file in search_dir.glob(f"{pattern_base}*.lib"):
                    if lib_file.is_file():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
        else:
            # Linux: copy .so files and symlinks
            for search_dir in search_dirs:
                if not search_dir.exists():
                    continue
                # Copy real files first
                for lib_file in search_dir.glob(f"{pattern_base}*.so*"):
                    if lib_file.is_file() and not lib_file.is_symlink():
                        dst = self.lib_dir / lib_file.name
                        print(f"  + {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                        shutil.copy2(lib_file, dst)
                        copied += 1
                # Then copy symlinks
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

    def _patch_nats_for_windows(self, nats_dir):
        """No patches needed - nats.c already supports NATS_BUILD_WITH_TLS=OFF.

        The source code guards OpenSSL includes with #ifdef NATS_HAS_TLS,
        and the CMake option NATS_BUILD_WITH_TLS controls that define.
        """
        print("  nats.c: no requiere patches (NATS_BUILD_WITH_TLS=OFF desactiva TLS)")

    def build_nats(self):
        """Compila nats.c"""
        print("\n" + "=" * 70)
        print("  Compilando nats.c")
        print("=" * 70)

        nats_dir = self.deps_dir / "nats.c"
        nats_build_dir = nats_dir / "build"

        # Clonar si no existe
        if not nats_dir.exists():
            print("Clonando nats.c desde GitHub...")
            self.run_command([
                "git", "clone",
                "--depth", "1",
                "--branch", "v3.8.2",
                "https://github.com/nats-io/nats.c.git",
                str(nats_dir)
            ])
        else:
            print("nats.c ya existe, omitiendo clonacion")

        # Patch nats.c CMakeLists.txt on Windows to make OpenSSL optional
        if IS_WINDOWS:
            self._patch_nats_for_windows(nats_dir)

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

        if IS_WINDOWS:
            # Disable TLS to avoid OpenSSL dependency on Windows
            # The actual CMake option in nats.c is NATS_BUILD_WITH_TLS (not NATS_BUILD_TLS)
            cmake_args.append("-DNATS_BUILD_WITH_TLS=OFF")

        print("\nConfigurando nats.c con CMake...")
        self.run_command(cmake_args, cwd=nats_build_dir)

        print("\nCompilando nats.c...")
        self._cmake_build(nats_build_dir)

        # Copy libraries
        print("\nCopiando librerias nats.c...")
        search_dirs = [nats_build_dir, nats_build_dir / "src"]
        copied = self._copy_shared_libs(search_dirs, "libnats" if IS_LINUX else "nats")

        if copied == 0:
            print("\n  No se encontraron librerias")
            print("Buscando archivos en build directory:")
            for item in nats_build_dir.rglob("nats*" if IS_WINDOWS else "libnats*"):
                print(f"  Found: {item}")
            raise RuntimeError("No se encontraron librerias nats compiladas")

        print(f"OK nats.c compilado - {copied} archivo(s) copiado(s)")

    def _patch_eipscanner_for_windows(self, eip_dir):
        """Apply targeted patches to EIPScanner sources for Windows MSVC compatibility.

        EIPScanner already has partial Windows support (#ifdef _WIN32 in socket files).
        We only patch files that have UNGUARDED POSIX includes.
        """
        print("\nAplicando patches para Windows...")
        patches_applied = 0

        # POSIX headers that don't exist on Windows
        posix_headers = [
            "sys/socket.h", "netinet/in.h", "arpa/inet.h",
            "unistd.h", "netdb.h",
        ]

        source_files = list(eip_dir.rglob("*.cpp")) + list(eip_dir.rglob("*.h"))

        for fpath in source_files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            lines = content.split('\n')
            new_lines = []
            changed = False

            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # Check if this line is a POSIX include that needs guarding
                needs_guard = False
                for hdr in posix_headers:
                    if stripped == f'#include <{hdr}>':
                        # Check if ALREADY inside a platform guard
                        # Look at the previous non-empty line
                        prev_stripped = ""
                        for j in range(len(new_lines) - 1, -1, -1):
                            prev_stripped = new_lines[j].strip()
                            if prev_stripped:
                                break
                        already_guarded = (
                            prev_stripped.startswith("#ifdef _WIN32") or
                            prev_stripped.startswith("#ifndef _WIN32") or
                            prev_stripped.startswith("#else") or
                            prev_stripped.startswith("#if defined(_WIN32)") or
                            prev_stripped.startswith("#if !defined(_WIN32)")
                        )
                        if not already_guarded:
                            needs_guard = True
                        break

                if needs_guard:
                    new_lines.append("#ifndef _WIN32")
                    new_lines.append(line)
                    new_lines.append("#endif")
                    changed = True
                else:
                    new_lines.append(line)
                i += 1

            if changed:
                fpath.write_text('\n'.join(new_lines), encoding="utf-8")
                patches_applied += 1
                print(f"  Patched: {fpath.relative_to(eip_dir)}")

        # Add _WINSOCK_DEPRECATED_NO_WARNINGS to suppress inet_ntoa warnings
        cmakelists = eip_dir / "CMakeLists.txt"
        if cmakelists.exists():
            content = cmakelists.read_text(encoding="utf-8")
            if "_WINSOCK_DEPRECATED_NO_WARNINGS" not in content:
                content = content.replace(
                    "add_compile_definitions(NOMINMAX)",
                    "add_compile_definitions(NOMINMAX)\n"
                    "\t\tadd_compile_definitions(_WINSOCK_DEPRECATED_NO_WARNINGS)"
                )
                cmakelists.write_text(content, encoding="utf-8")
                patches_applied += 1
                print("  Patched: CMakeLists.txt (added _WINSOCK_DEPRECATED_NO_WARNINGS)")

        print(f"  {patches_applied} archivo(s) patcheado(s)")

    def build_eipscanner(self):
        """Compila EIPScanner"""
        print("\n" + "=" * 70)
        print("  Compilando EIPScanner")
        print("=" * 70)

        eip_dir = self.deps_dir / "EIPScanner"
        eip_build_dir = eip_dir / "build"

        # Clonar si no existe
        if not eip_dir.exists():
            print("Clonando EIPScanner desde GitHub...")
            self.run_command([
                "git", "clone",
                "--depth", "1",
                "https://github.com/nimbuscontrols/EIPScanner.git",
                str(eip_dir)
            ])
        else:
            print("EIPScanner ya existe, omitiendo clonacion")

        # Apply Windows patches if needed
        if IS_WINDOWS:
            self._patch_eipscanner_for_windows(eip_dir)

        # Build
        eip_build_dir.mkdir(exist_ok=True)

        cmake_args = [
            "cmake", "..",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_SHARED_LIBS=ON",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        ]

        if IS_WINDOWS:
            cmake_args.append("-DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=ON")

        print("\nConfigurando EIPScanner con CMake...")
        self.run_command(cmake_args, cwd=eip_build_dir)

        print("\nCompilando EIPScanner...")
        self._cmake_build(eip_build_dir)

        # Copy libraries
        print("\nCopiando librerias EIPScanner...")
        search_dirs = [eip_build_dir, eip_build_dir / "src"]
        copied = self._copy_shared_libs(search_dirs, "libEIPScanner" if IS_LINUX else "EIPScanner")

        if copied == 0:
            print("\n  No se encontraron librerias")
            print("Buscando archivos en build directory:")
            for item in eip_build_dir.rglob("EIPScanner*" if IS_WINDOWS else "libEIPScanner*"):
                print(f"  Found: {item}")
            raise RuntimeError("No se encontraron librerias EIPScanner compiladas")

        print(f"OK EIPScanner compilado - {copied} archivo(s) copiado(s)")

    def build_python_binding(self):
        """Compila el binding Python"""
        print("\n" + "=" * 70)
        print("  Compilando binding Python")
        print("=" * 70)

        nats_dir = self.deps_dir / "nats.c"
        eip_dir = self.deps_dir / "EIPScanner"

        nats_include = nats_dir / "src"
        eip_include = eip_dir / "src"

        # Verify sources exist
        binding_src = self.src_dir / "bindings.cpp"
        bridge_src = self.src_dir / "EIPtoNATSBridge.cpp"

        if not binding_src.exists() or not bridge_src.exists():
            raise FileNotFoundError("Archivos fuente no encontrados en src/eip2nats/")

        import sysconfig

        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        print(f"Extension suffix: {ext_suffix}")

        if IS_WINDOWS:
            self._build_binding_cmake(nats_include, eip_include)
        else:
            self._build_binding_gcc(nats_include, eip_include, ext_suffix)

    def _build_binding_gcc(self, nats_include, eip_include, ext_suffix):
        """Build the Python binding using g++ directly (Linux)"""
        import pybind11
        import sysconfig

        python_include = sysconfig.get_path('include')
        pybind_include = pybind11.get_include()

        output_name = self.src_dir / f"eip_nats_bridge{ext_suffix}"

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
            f"-I{pybind_include}",
            f"-I{nats_include}",
            f"-I{eip_include}",
            f"-I{self.src_dir}",
            f"-I{python_include}",
            str(self.src_dir / "bindings.cpp"),
            str(self.src_dir / "EIPtoNATSBridge.cpp"),
            "-o", str(output_name),
            f"-L{self.lib_dir}",
            "-lnats",
            "-lEIPScanner",
            "-lpthread",
            "-Wl,-rpath,$ORIGIN/lib",
        ]

        print("\nCompilando...")
        self.run_command(compile_cmd)

        print(f"OK Binding compilado: {output_name.name}")

    def _build_binding_cmake(self, nats_include, eip_include):
        """Build the Python binding using CMake (Windows/MSVC)"""
        binding_build_dir = self.build_dir / "binding"
        binding_build_dir.mkdir(parents=True, exist_ok=True)

        # Copy CMakeLists.txt template to build dir
        cmake_template = self.root_dir / "scripts" / "binding_CMakeLists.txt"
        cmake_dest = binding_build_dir / "CMakeLists.txt"
        shutil.copy2(cmake_template, cmake_dest)

        # Get pybind11 cmake dir
        import pybind11
        pybind11_cmake_dir = pybind11.get_cmake_dir()

        print(f"pybind11 cmake dir: {pybind11_cmake_dir}")
        print(f"NATS include: {nats_include}")
        print(f"EIP include: {eip_include}")
        print(f"Lib dir: {self.lib_dir}")
        print(f"Src dir: {self.src_dir}")

        # Point CMake to the correct Python (the one running this script)
        # Use forward slashes for all paths - CMake handles them on all platforms
        # and backslashes cause escape character issues in CMake EVAL
        python_executable = sys.executable.replace('\\', '/')
        pybind11_cmake_dir_str = str(pybind11_cmake_dir).replace('\\', '/')
        nats_include_str = str(nats_include).replace('\\', '/')
        eip_include_str = str(eip_include).replace('\\', '/')
        src_dir_str = str(self.src_dir).replace('\\', '/')
        lib_dir_str = str(self.lib_dir).replace('\\', '/')

        cmake_args = [
            "cmake", ".",
            f"-Dpybind11_DIR={pybind11_cmake_dir_str}",
            f"-DNATS_INCLUDE_DIR={nats_include_str}",
            f"-DEIP_INCLUDE_DIR={eip_include_str}",
            f"-DSRC_DIR={src_dir_str}",
            f"-DLIB_DIR={lib_dir_str}",
            f"-DPython_EXECUTABLE={python_executable}",
            f"-DPython3_EXECUTABLE={python_executable}",
            "-DCMAKE_BUILD_TYPE=Release",
        ]

        print("\nConfigurando binding con CMake...")
        self.run_command(cmake_args, cwd=binding_build_dir)

        print("\nCompilando binding...")
        self.run_command([
            "cmake", "--build", ".", "--config", "Release"
        ], cwd=binding_build_dir)

        # Verify output
        import sysconfig
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        expected_output = self.src_dir / f"eip_nats_bridge{ext_suffix}"

        if not expected_output.exists():
            # On Windows, pybind11 might produce the file with .pyd extension
            pyd_files = list(self.src_dir.glob("eip_nats_bridge*.pyd"))
            if pyd_files:
                print(f"OK Binding compilado: {pyd_files[0].name}")
            else:
                print("Buscando output en build dir...")
                for item in binding_build_dir.rglob("eip_nats_bridge*"):
                    print(f"  Found: {item}")
                raise RuntimeError("No se encontro el binding compilado")
        else:
            print(f"OK Binding compilado: {expected_output.name}")

        # On Windows, copy dependency DLLs next to the .pyd for easy loading
        if IS_WINDOWS:
            for dll in self.lib_dir.glob("*.dll"):
                dst = self.src_dir / dll.name
                if not dst.exists():
                    shutil.copy2(dll, dst)
                    print(f"  Copied DLL: {dll.name} -> src/eip2nats/")

    def build_all(self):
        """Compila todo"""
        print("\n" + "=" * 70)
        print("  INICIANDO COMPILACION DE TODAS LAS DEPENDENCIAS")
        plat = f"Windows x64" if IS_WINDOWS else f"Linux {platform.machine()}"
        print(f"  Plataforma: {plat}")
        print("=" * 70)

        try:
            self.build_nats()
            self.build_eipscanner()
            self.build_python_binding()

            print("\n" + "=" * 70)
            print("  COMPILACION COMPLETA EXITOSA")
            print("=" * 70)

            # List files in lib/
            print("\n  Archivos en src/eip2nats/lib/:")
            for f in sorted(self.lib_dir.iterdir()):
                if f.is_file():
                    size = f.stat().st_size / 1024
                    print(f"  - {f.name} ({size:.1f} KB)")

            # List binding file
            if IS_WINDOWS:
                bindings = list(self.src_dir.glob("eip_nats_bridge*.pyd"))
            else:
                bindings = list(self.src_dir.glob("eip_nats_bridge*.so"))

            if bindings:
                print(f"\n  Binding Python:")
                for b in bindings:
                    size = b.stat().st_size / 1024
                    print(f"  - {b.name} ({size:.1f} KB)")

            return True

        except Exception as e:
            print("\n" + "=" * 70)
            print(f"  ERROR: {e}")
            print("=" * 70)
            return False


if __name__ == "__main__":
    builder = DependencyBuilder()
    success = builder.build_all()
    sys.exit(0 if success else 1)
