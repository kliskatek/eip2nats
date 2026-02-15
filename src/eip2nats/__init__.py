"""
eip2nats - EtherNet/IP to NATS Bridge

Puente entre dispositivos EtherNet/IP (PLCs) y servidores NATS con
todas las dependencias incluidas.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio lib al path de busqueda de librerias
_lib_dir = Path(__file__).parent / "lib"
if _lib_dir.exists():
    if sys.platform.startswith('linux'):
        # Linux: LD_LIBRARY_PATH
        os.environ['LD_LIBRARY_PATH'] = f"{_lib_dir}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    elif sys.platform == 'win32':
        # Windows: add DLL search directory (Python 3.8+)
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(str(_lib_dir))
        # Also add to PATH as fallback for older Python / subprocess calls
        os.environ['PATH'] = f"{_lib_dir};{os.environ.get('PATH', '')}"

# Importar el modulo C++ - esta directamente en este directorio
try:
    import importlib.util
    _module_dir = Path(__file__).parent

    # Buscar el modulo compilado (.so en Linux, .pyd en Windows)
    _patterns = ["eip_nats_bridge*.pyd", "eip_nats_bridge*.so"] if sys.platform == 'win32' \
        else ["eip_nats_bridge*.so"]

    _found = False
    for _pattern in _patterns:
        for _ext_file in _module_dir.glob(_pattern):
            if _ext_file.is_file():
                spec = importlib.util.spec_from_file_location("eip_nats_bridge", _ext_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    EIPtoNATSBridge = module.EIPtoNATSBridge
                    _found = True
                    break
        if _found:
            break

    if not _found:
        ext = ".pyd/.so" if sys.platform == 'win32' else ".so"
        raise ImportError(f"No se encontro el modulo eip_nats_bridge compilado ({ext})")

except ImportError as e:
    raise ImportError(f"Error cargando el modulo eip2nats: {e}")

__version__ = "1.0.2"
__all__ = ["EIPtoNATSBridge"]
