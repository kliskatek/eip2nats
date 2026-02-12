"""
eip2nats - EtherNet/IP to NATS Bridge

Puente entre dispositivos EtherNet/IP (PLCs) y servidores NATS con
todas las dependencias incluidas.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio lib al path de búsqueda de librerías
_lib_dir = Path(__file__).parent / "lib"
if _lib_dir.exists():
    # Agregar al LD_LIBRARY_PATH en tiempo de ejecución
    if sys.platform.startswith('linux'):
        os.environ['LD_LIBRARY_PATH'] = f"{_lib_dir}:{os.environ.get('LD_LIBRARY_PATH', '')}"

# Importar el módulo C++ - está directamente en este directorio
try:
    # Buscar el archivo .so en el directorio actual
    import importlib.util
    _module_dir = Path(__file__).parent
    
    # Buscar el módulo compilado (eip_nats_bridge*.so)
    for so_file in _module_dir.glob("eip_nats_bridge*.so"):
        if so_file.is_file():
            # El nombre debe coincidir con PYBIND11_MODULE(eip_nats_bridge, m)
            spec = importlib.util.spec_from_file_location("eip_nats_bridge", so_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                EIPtoNATSBridge = module.EIPtoNATSBridge
                break
    else:
        raise ImportError("No se encontró el módulo eip_nats_bridge compilado (.so)")
        
except ImportError as e:
    raise ImportError(f"Error cargando el módulo eip2nats: {e}")

__version__ = "1.0.0"
__all__ = ["EIPtoNATSBridge"]
