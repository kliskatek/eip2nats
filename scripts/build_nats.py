#!/usr/bin/env python3
"""
Compila nats.c desde fuentes.
Uso: python scripts/build_nats.py
"""

import sys
from build_config import BuildConfig, IS_WINDOWS, IS_LINUX


def build_nats(cfg=None):
    """Compila nats.c"""
    if cfg is None:
        cfg = BuildConfig()

    print("\n" + "=" * 70)
    print("  Compilando nats.c")
    print("=" * 70)

    nats_dir = cfg.deps_dir / "nats.c"
    nats_build_dir = nats_dir / "build"

    # Clonar si no existe
    if not nats_dir.exists():
        print("Clonando nats.c desde GitHub...")
        cfg.run_command([
            "git", "clone",
            "--depth", "1",
            "--branch", "v3.8.2",
            "https://github.com/nats-io/nats.c.git",
            str(nats_dir)
        ])
    else:
        print("nats.c ya existe, omitiendo clonacion")

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
        # Desactivar TLS para evitar dependencia de OpenSSL en Windows
        # La opcion CMake en nats.c es NATS_BUILD_WITH_TLS (no NATS_BUILD_TLS)
        cmake_args.append("-DNATS_BUILD_WITH_TLS=OFF")

    print("\nConfigurando nats.c con CMake...")
    cfg.run_command(cmake_args, cwd=nats_build_dir)

    print("\nCompilando nats.c...")
    cfg.cmake_build(nats_build_dir)

    # Copiar librerias
    print("\nCopiando librerias nats.c...")
    search_dirs = [nats_build_dir, nats_build_dir / "src"]
    copied = cfg.copy_shared_libs(search_dirs, "libnats" if IS_LINUX else "nats")

    if copied == 0:
        print("\n  No se encontraron librerias")
        print("Buscando archivos en build directory:")
        for item in nats_build_dir.rglob("nats*" if IS_WINDOWS else "libnats*"):
            print(f"  Found: {item}")
        raise RuntimeError("No se encontraron librerias nats compiladas")

    print(f"OK nats.c compilado - {copied} archivo(s) copiado(s)")


if __name__ == "__main__":
    try:
        build_nats()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
