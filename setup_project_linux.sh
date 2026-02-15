#!/bin/bash
# setup_project.sh - Script to set up the eip2nats project

set -e

echo "=============================================="
echo "  eip2nats Project Setup"
echo "=============================================="
echo ""

# Function to install missing packages (with verifiable command)
install_package() {
    local package=$1
    local command_check=$2

    if ! command -v $command_check >/dev/null 2>&1; then
        echo "  $command_check not found"
        echo "  Installing $package..."

        if sudo apt-get update && sudo apt-get install -y $package; then
            echo "  $package installed successfully"
        else
            echo "  Error installing $package"
            echo "   Please install manually with: sudo apt-get install $package"
            exit 1
        fi
    else
        echo "  $command_check is already installed"
    fi
}

# Function to install development libraries
install_library() {
    local package=$1

    if ! dpkg -s $package >/dev/null 2>&1; then
        echo "  $package not found"
        echo "  Installing $package..."

        if sudo apt-get update && sudo apt-get install -y $package; then
            echo "  $package installed successfully"
        else
            echo "  Error installing $package"
            echo "   Please install manually with: sudo apt-get install $package"
            exit 1
        fi
    else
        echo "  $package is already installed"
    fi
}

# Check and install requirements
echo "Checking system requirements..."
echo ""

install_package "git" "git"
install_package "cmake" "cmake"
install_package "build-essential" "make"
install_package "g++" "g++"
install_package "python3" "python3"

# Install development libraries
install_library "libssl-dev"
install_library "python3-dev"

echo ""
echo "All system requirements are installed"
echo ""

# Create virtual environment
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists in $VENV_DIR"
else
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install build dependencies in the venv
echo "Installing build dependencies in the virtual environment..."
pip install build pybind11 hatch twine

echo ""
echo "=============================================="
echo "  Step 2: Build nats.c"
echo "=============================================="
echo ""

python scripts/build_nats.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error building nats.c"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  Step 3: Build EIPScanner"
echo "=============================================="
echo ""

python scripts/build_eipscanner.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error building EIPScanner"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  Step 4: Build Python binding"
echo "=============================================="
echo ""

python scripts/build_binding.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Error building Python binding"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  Step 5: Create wheel"
echo "=============================================="
echo ""

# Verify that libraries exist
if [ ! -d "src/eip2nats/lib" ] || [ -z "$(ls -A src/eip2nats/lib/*.so 2>/dev/null)" ]; then
    echo "Error: No shared libraries found in src/eip2nats/lib/"
    deactivate
    exit 1
fi

# Verify that the Python module exists
if [ -z "$(ls src/eip2nats/eip_nats_bridge*.so 2>/dev/null)" ]; then
    echo "Error: Compiled Python module not found in src/eip2nats/"
    deactivate
    exit 1
fi

echo "Compiled Python module:"
ls -lh src/eip2nats/eip_nats_bridge*.so 2>/dev/null | awk '{print "  ", $9, "(" $5 ")"}'
echo ""

echo "Shared libraries:"
ls -lh src/eip2nats/lib/*.so* 2>/dev/null | awk '{print "  ", $9, "(" $5 ")"}'
echo ""

python -m build --wheel

if [ $? -ne 0 ]; then
    echo ""
    echo "Error creating wheel"
    deactivate
    exit 1
fi

# Rename wheel to manylinux format for PyPI
echo ""
echo "Renaming wheel to manylinux format..."
python << 'EOF'
from pathlib import Path

dist_dir = Path("dist")
wheels = list(dist_dir.glob("*-linux_*.whl"))

for old_wheel in wheels:
    old_name = old_wheel.name

    if "linux_aarch64" in old_name:
        new_name = old_name.replace(
            "linux_aarch64",
            "manylinux_2_17_aarch64.manylinux2014_aarch64"
        )
    elif "linux_x86_64" in old_name:
        new_name = old_name.replace(
            "linux_x86_64",
            "manylinux_2_17_x86_64.manylinux2014_x86_64"
        )
    else:
        continue

    new_wheel = dist_dir / new_name
    old_wheel.rename(new_wheel)
    print(f"  Renamed to: {new_name}")
EOF

echo ""
echo "=============================================="
echo "  Step 6: Install wheel in the venv"
echo "=============================================="
echo ""

# Install the wheel in the virtual environment
WHEEL_FILE=$(ls dist/eip2nats-*.whl | head -n 1)

if [ -f "$WHEEL_FILE" ]; then
    echo "Installing $WHEEL_FILE in the virtual environment..."
    pip install "$WHEEL_FILE"

    if [ $? -eq 0 ]; then
        echo "Wheel installed in the virtual environment"
    else
        echo "Error installing wheel"
        deactivate
        exit 1
    fi
else
    echo "Wheel not found"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Wheel created in: dist/"
ls -lh dist/*.whl
echo ""
echo "The module is installed in the virtual environment"
echo ""
echo "To use the project:"
echo ""
echo "  # Activate virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "  # Test:"
echo "  python -c 'import eip2nats; print(eip2nats.__version__)'"
echo ""
echo "  # Use:"
echo "  python your_script.py"
echo ""
echo "  # Deactivate when done:"
echo "  deactivate"
echo ""
echo "Documentation:"
echo "  cat README.md"
echo ""

# Keep the venv active so the user can work
echo "The virtual environment is still active. When done, run: deactivate"
echo ""
