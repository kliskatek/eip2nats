#!/usr/bin/env python3
"""
Script para compilar todas las dependencias externas y el módulo Python.
Este script se ejecuta automáticamente cuando se hace 'hatch build'.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


class DependencyBuilder:
    """Construye nats.c, EIPScanner y el binding Python"""
    
    def __init__(self):
        self.root_dir = Path.cwd()
        self.build_dir = self.root_dir / "build"
        self.deps_dir = self.build_dir / "dependencies"
        self.lib_dir = self.root_dir / "src" / "eip2nats" / "lib"
        
        # Crear directorios
        self.lib_dir.mkdir(parents=True, exist_ok=True)
        self.deps_dir.mkdir(parents=True, exist_ok=True)
    
    def run_command(self, cmd, cwd=None, env=None):
        """Ejecuta un comando shell"""
        print(f"\n▶️  {' '.join(str(c) for c in cmd)}")
        
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
    
    def build_nats(self):
        """Compila nats.c"""
        print("\n" + "=" * 70)
        print("📦 Compilando nats.c")
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
            print("nats.c ya existe, omitiendo clonación")
        
        # Build
        nats_build_dir.mkdir(exist_ok=True)
        
        print("\nConfigurando nats.c con CMake...")
        self.run_command([
            "cmake", "..",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_TESTING=OFF",
            "-DNATS_BUILD_STREAMING=OFF",
            "-DNATS_BUILD_LIB_SHARED=ON",      # IMPORTANTE: Build shared library
            "-DNATS_BUILD_LIB_STATIC=OFF",      # No necesitamos static
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        ], cwd=nats_build_dir)
        
        print("\nCompilando nats.c...")
        self.run_command([
            "make", "-j", str(os.cpu_count() or 4)
        ], cwd=nats_build_dir)
        
        # Copiar librerías - buscar en varios lugares
        print("\nCopiando librerías nats.c...")
        copied = 0
        
        # Buscar en build/ y build/src/
        search_dirs = [nats_build_dir, nats_build_dir / "src"]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            for lib_file in search_dir.glob("libnats*.so*"):
                if lib_file.is_file() and not lib_file.is_symlink():
                    dst = self.lib_dir / lib_file.name
                    print(f"  ✓ {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                    shutil.copy2(lib_file, dst)
                    copied += 1
            
            # También copiar symlinks
            for lib_file in search_dir.glob("libnats*.so*"):
                if lib_file.is_symlink():
                    link_target = lib_file.readlink()
                    dst = self.lib_dir / lib_file.name
                    if dst.exists():
                        dst.unlink()
                    dst.symlink_to(link_target.name)  # Symlink relativo
                    print(f"  ✓ {lib_file.name} -> {link_target.name} (symlink)")
                    copied += 1
        
        if copied == 0:
            # Diagnóstico
            print("\n⚠️  No se encontraron librerías .so")
            print("Buscando archivos en build directory:")
            for item in nats_build_dir.rglob("libnats*"):
                print(f"  Found: {item}")
            raise RuntimeError("No se encontraron librerías nats compiladas")
        
        print(f"✅ nats.c compilado - {copied} archivo(s) copiado(s)")
    
    def build_eipscanner(self):
        """Compila EIPScanner"""
        print("\n" + "=" * 70)
        print("📦 Compilando EIPScanner")
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
            print("EIPScanner ya existe, omitiendo clonación")
        
        # Build
        eip_build_dir.mkdir(exist_ok=True)
        
        print("\nConfigurando EIPScanner con CMake...")
        self.run_command([
            "cmake", "..",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DBUILD_SHARED_LIBS=ON",           # Build shared library
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
        ], cwd=eip_build_dir)
        
        print("\nCompilando EIPScanner...")
        self.run_command([
            "make", "-j", str(os.cpu_count() or 4)
        ], cwd=eip_build_dir)
        
        # Copiar librerías - buscar en build/ y build/src/
        print("\nCopiando librerías EIPScanner...")
        copied = 0
        
        search_dirs = [eip_build_dir, eip_build_dir / "src"]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            # Buscar archivos .so (no symlinks primero)
            for lib_file in search_dir.glob("libEIPScanner.so*"):
                if lib_file.is_file() and not lib_file.is_symlink():
                    dst = self.lib_dir / lib_file.name
                    print(f"  ✓ {lib_file.name} -> {dst.relative_to(self.root_dir)}")
                    shutil.copy2(lib_file, dst)
                    copied += 1
            
            # Copiar symlinks
            for lib_file in search_dir.glob("libEIPScanner.so*"):
                if lib_file.is_symlink():
                    link_target = lib_file.readlink()
                    dst = self.lib_dir / lib_file.name
                    if dst.exists():
                        dst.unlink()
                    # Crear symlink relativo
                    dst.symlink_to(link_target.name if not link_target.is_absolute() else link_target.name)
                    print(f"  ✓ {lib_file.name} -> {link_target.name} (symlink)")
                    copied += 1
        
        if copied == 0:
            # Diagnóstico
            print("\n⚠️  No se encontraron librerías .so")
            print("Buscando archivos en build directory:")
            for item in eip_build_dir.rglob("libEIPScanner*"):
                print(f"  Found: {item}")
            raise RuntimeError("No se encontraron librerías EIPScanner compiladas")
        
        print(f"✅ EIPScanner compilado - {copied} archivo(s) copiado(s)")
    
    def build_python_binding(self):
        """Compila el binding Python"""
        print("\n" + "=" * 70)
        print("📦 Compilando binding Python")
        print("=" * 70)
        
        # Rutas
        nats_dir = self.deps_dir / "nats.c"
        eip_dir = self.deps_dir / "EIPScanner"
        src_dir = self.root_dir / "src" / "eip2nats"
        
        nats_include = nats_dir / "src"
        eip_include = eip_dir / "src"
        
        # Verificar que existen los sources
        binding_src = src_dir / "bindings.cpp"
        bridge_src = src_dir / "EIPtoNATSBridge.cpp"
        
        if not binding_src.exists() or not bridge_src.exists():
            raise FileNotFoundError("Archivos fuente no encontrados en src/eip2nats/")
        
        # Obtener configuración de Python
        import sysconfig
        import pybind11
        
        python_include = sysconfig.get_path('include')
        pybind_include = pybind11.get_include()
        ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
        
        # IMPORTANTE: El nombre debe coincidir con PYBIND11_MODULE(eip_nats_bridge, m)
        output_name = src_dir / f"eip_nats_bridge{ext_suffix}"
        
        print(f"Python include: {python_include}")
        print(f"pybind11 include: {pybind_include}")
        print(f"Output: {output_name}")
        
        # Compilar
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
            f"-I{src_dir}",
            f"-I{python_include}",
            str(binding_src),
            str(bridge_src),
            "-o", str(output_name),
            f"-L{self.lib_dir}",
            "-lnats",
            "-lEIPScanner",
            "-lpthread",
            "-Wl,-rpath,$ORIGIN/lib",  # RPATH apunta a ./lib/ subdirectorio
        ]
        
        print("\nCompilando...")
        self.run_command(compile_cmd)
        
        print(f"✅ Binding compilado: {output_name.name}")
    
    def build_all(self):
        """Compila todo"""
        print("\n" + "=" * 70)
        print("🚀 INICIANDO COMPILACIÓN DE TODAS LAS DEPENDENCIAS")
        print("=" * 70)
        
        try:
            self.build_nats()
            self.build_eipscanner()
            self.build_python_binding()
            
            print("\n" + "=" * 70)
            print("✅ COMPILACIÓN COMPLETA EXITOSA")
            print("=" * 70)
            
            # Listar archivos en lib/
            print("\n📦 Archivos en src/eip2nats/lib/:")
            for f in sorted(self.lib_dir.iterdir()):
                size = f.stat().st_size / 1024  # KB
                print(f"  • {f.name} ({size:.1f} KB)")
            
            return True
            
        except Exception as e:
            print("\n" + "=" * 70)
            print(f"❌ ERROR: {e}")
            print("=" * 70)
            return False


if __name__ == "__main__":
    builder = DependencyBuilder()
    success = builder.build_all()
    sys.exit(0 if success else 1)
