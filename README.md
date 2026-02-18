# eip2nats - EtherNet/IP to NATS Bridge

Read-only bridge that opens an EtherNet/IP **implicit (I/O) connection** to a PLC, captures the T2O (Target-to-Originator) data stream and publishes every packet to a NATS subject. It does **not** write data to the PLC — it acts as a passive listener, similar to a sniffer.

All dependencies (libnats, libEIPScanner) are **bundled** in the wheel.

## Features

- **Read-only**: Captures PLC I/O data via implicit connection, no writes
- **Self-contained**: Includes compiled libnats and libEIPScanner
- **Zero dependencies**: No system library installation required
- **Device presets**: Built-in assembly constants for known devices (RM75E, ClipX)
- **High performance**: Native C++ bindings with pybind11
- **Auto-reconnect**: Recovers automatically from connection loss
- **Parallel bridges**: Run multiple bridges on different UDP ports simultaneously
- **Thread-safe**: Safe handling of multiple connections

## Installation

```bash
pip install eip2nats
```

Pre-built wheels are available on [PyPI](https://pypi.org/project/eip2nats/) for Linux and Windows.

### Building from Source

If a pre-built wheel is not available for your platform, you can build from source:

**Linux:**
```bash
./setup_project_linux.sh
```

**Windows** (PowerShell, requires Visual Studio Build Tools):
```powershell
.\setup_project_windows.ps1
```

This automatically:
1. Creates a virtual environment in `venv/`
2. Installs Hatch and pybind11
3. Compiles nats.c, EIPScanner and the Python binding
4. Creates the wheel
5. Installs the wheel in the venv

### Usage

```bash
# Activate virtual environment
source venv/bin/activate    # Linux
.\venv\Scripts\Activate     # Windows PowerShell

# Run example
python examples/example_python_rm75e.py

# Deactivate when done
deactivate
```

## Basic Usage

```python
import eip2nats

# Create bridge (using RM75E device presets)
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",              # PLC IP address
    "nats://192.168.17.138:4222",  # NATS server
    "plc.data",                    # NATS subject/topic
    config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
    o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
    t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
    t2o_size=100,
    rpi=2000,                      # Requested Packet Interval (µs)
    port=2222,                     # Local UDP port for T2O data
)

# Start
if bridge.start():
    import time
    print("Bridge running!")

    # Monitor
    while bridge.is_running():
        time.sleep(5)
        print(f"RX={bridge.get_received_count()}, "
              f"TX={bridge.get_published_count()}")

    # Stop
    bridge.stop()
```

**More examples in [`examples/`](examples/README.md)**

## Requirements

**Linux:**
- Python 3.7+
- git, cmake, make, g++, python3-venv

**Windows:**
- Python 3.7+
- git, cmake
- Visual Studio Build Tools (cl.exe)

## Development

See [`DEVELOPMENT.md`](DEVELOPMENT.md) for the full development guide (VSCode setup, debugging, workflows).

### Create Release

```bash
hatch build
```

### Manual Build (without setup script)

```bash
git clone https://github.com/kliskatek/eip2nats.git
cd eip2nats
pip install hatch pybind11

# Build dependencies
python scripts/build_nats.py
python scripts/build_eipscanner.py
python scripts/build_binding.py

# Create wheel
hatch build
```

## Project Structure

```
eip2nats/
├── pyproject.toml                # Hatch configuration
├── hatch_build.py                # Hook for platform-specific wheel
├── README.md
├── DEVELOPMENT.md                # VSCode development guide
├── LICENSE                       # MIT
├── THIRD_PARTY_LICENSES          # nats.c and EIPScanner licenses
├── setup_project_linux.sh        # Automatic setup (Linux)
├── setup_project_windows.ps1     # Automatic setup (Windows)
├── src/
│   └── eip2nats/
│       ├── __init__.py           # Python package
│       ├── bindings.cpp          # pybind11 bindings
│       ├── EIPtoNATSBridge.h     # C++ header
│       ├── EIPtoNATSBridge.cpp   # C++ implementation
│       └── lib/                  # Compiled libraries (auto-generated)
│           ├── libnats.so / nats.dll
│           └── libEIPScanner.so / EIPScanner.dll
├── scripts/
│   ├── build_config.py           # Shared build configuration
│   ├── build_nats.py             # Builds nats.c
│   ├── build_eipscanner.py       # Builds EIPScanner
│   ├── build_binding.py          # Builds Python binding (.pyd/.so)
│   ├── build_example_cpp.py      # Builds C++ example
│   └── binding_CMakeLists.txt    # CMake template for binding (Windows)
├── examples/
│   ├── example_python_rm75e.py    # Python example (RM75E)
│   ├── example_python_clipx.py    # Python example (ClipX)
│   ├── example_cpp_clipx.cpp      # C++ example (ClipX)
│   └── example_cpp.cpp            # C++ example (debugging)
├── tests/
│   └── test_python.py            # Python unit tests
└── build/                        # Auto-generated, in .gitignore
    ├── dependencies/             # nats.c and EIPScanner clones
    └── example_cpp/              # Compiled C++ executable
```

## How It Works

1. **Build scripts** (`scripts/`):
   - `build_nats.py`: Clones and compiles nats.c -> `libnats.so` / `nats.dll`
   - `build_eipscanner.py`: Clones and compiles EIPScanner -> `libEIPScanner.so` / `EIPScanner.dll`
   - `build_binding.py`: Compiles the Python binding -> `.so` (Linux) / `.pyd` (Windows)
   - All copy binaries to `src/eip2nats/lib/`

2. **`hatch build`**:
   - Packages the full `src/eip2nats/` (code + binaries)
   - `hatch_build.py` forces platform-specific wheel tags
   - Linux: relative RPATH (`$ORIGIN`), Windows: `os.add_dll_directory()`
   - The wheel contains everything needed

3. **`pip install`**:
   - Installs the wheel
   - Binaries end up in site-packages
   - Python loads libraries automatically
   - Works without system dependencies!

## Advantages

### vs System Libraries:
- No `sudo apt-get install` required
- No version conflicts
- Portable across systems

### vs Regular Wheels:
- Includes all C/C++ dependencies
- Single file to install
- Works on systems without compilers

### vs Docker:
- Lighter (MBs vs GBs)
- Direct Python integration
- No Docker privileges required

## API Reference

### Class: `EIPtoNATSBridge`

```python
bridge = eip2nats.EIPtoNATSBridge(
    plc_address: str,
    nats_url: str,
    nats_subject: str,
    use_binary_format: bool = True,
    config_assembly: int = 4,       # Configuration assembly instance
    o2t_assembly: int = 2,          # O2T data assembly instance
    t2o_assembly: int = 1,          # T2O data assembly instance
    t2o_size: int = 0,              # T2O connection size in bytes
    rpi: int = 2000,                # Requested Packet Interval (µs), applied to O2T and T2O
    port: int = 2222,               # Local UDP port for receiving I/O data
)
```

**Methods:**
- `start() -> bool`: Starts the bridge
- `stop() -> None`: Stops the bridge
- `is_running() -> bool`: Bridge status
- `get_received_count() -> int`: Messages from PLC
- `get_published_count() -> int`: Messages to NATS
- `get_reconnect_count() -> int`: Automatic EIP reconnections

### Device Presets: `eip2nats.devices`

Pre-defined assembly constants for known EIP devices:

```python
# RMC75E (Delta Computer Systems)
eip2nats.devices.RM75E.CONFIG_ASSEMBLY  # 4
eip2nats.devices.RM75E.O2T_ASSEMBLY     # 2
eip2nats.devices.RM75E.T2O_ASSEMBLY     # 1

# ClipX (HBK / Hottinger Brüel & Kjær)
eip2nats.devices.ClipX.CONFIG_ASSEMBLY  # 1
eip2nats.devices.ClipX.O2T_ASSEMBLY     # 101
eip2nats.devices.ClipX.T2O_ASSEMBLY     # 100
```

## Troubleshooting

### Error: "cannot open shared object file"

Even though the wheel includes the libraries, check RPATH:

```bash
ldd $(python -c "import eip2nats; print(eip2nats.__file__.replace('__init__.py', 'lib/eip2nats.*.so'))")
```

All dependencies should resolve locally.

### Rebuild on Another System

```bash
git clone <repo>
cd eip2nats
python scripts/build_nats.py
python scripts/build_eipscanner.py
python scripts/build_binding.py
hatch build
```

### Clean Builds

```bash
rm -rf build/ dist/ src/eip2nats/lib/
```

## Changelog

### v1.3.0 (2025)
- Configurable UDP port for T2O data reception, enabling multiple parallel bridges
- EIPScanner patched to include T2O_SOCKADDR_INFO in Forward Open request
- Pinned EIPScanner dependency to known-good commit (12c89a5)
- CPython 3.14 wheel build target

### v1.2.0 (2025)
- Configurable RPI (Requested Packet Interval) via constructor parameter
- Added HBK ClipX device preset
- Added ClipX examples (Python and C++)
- Raspberry Pi build support

### v1.0.0 (2025)
- Initial release
- Self-contained wheel with nats.c and EIPScanner
- Windows (MSVC) and Linux (GCC) support
- Binary and JSON format support
- Thread-safe operations

## Contributing

1. Fork the project
2. Create a branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see LICENSE file

## Credits

- [nats.c](https://github.com/nats-io/nats.c) - NATS C Client
- [EIPScanner](https://github.com/nimbuscontrols/EIPScanner) - EtherNet/IP Library
- [pybind11](https://github.com/pybind/pybind11) - Python bindings
