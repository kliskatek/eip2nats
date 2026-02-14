#!/usr/bin/env python3
"""
Setup script para eip2nats

Este setup.py solo declara la extensión binaria para que setuptools
genere los tags de plataforma correctos en el wheel.

La compilación real se hace en scripts/build_dependencies.py
"""

from setuptools import setup, Extension
import sysconfig

# Obtener el sufijo de la extensión (ej: .cpython-311-aarch64-linux-gnu.so)
ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
module_name = f"eip_nats_bridge{ext_suffix}"

# Declarar la extensión para que setuptools marque el wheel como específico de plataforma
# sources=[] porque ya está compilado por build_dependencies.py
extension = Extension(
    name="eip2nats.eip_nats_bridge",
    sources=[],  # Vacío porque ya está compilado
    # Esta extensión es opcional porque el binario ya existe
    optional=True,
)

setup(
    ext_modules=[extension],
    # Indicar que hay archivos binarios específicos de plataforma
    has_ext_modules=lambda: True,
)
