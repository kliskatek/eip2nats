"""
eip2nats - EtherNet/IP to NATS Bridge

Bridge between EtherNet/IP devices (PLCs) and NATS servers with
all dependencies bundled.
"""

import os
import sys
from pathlib import Path

# Add lib directory to library search path
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

# Import the C++ module - located directly in this directory
try:
    import importlib.util
    _module_dir = Path(__file__).parent

    # Find the compiled module (.so on Linux, .pyd on Windows)
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
        raise ImportError(f"Compiled eip_nats_bridge module not found ({ext})")

except ImportError as e:
    raise ImportError(f"Error loading eip2nats module: {e}")

__version__ = "1.0.2"
__all__ = ["EIPtoNATSBridge"]
