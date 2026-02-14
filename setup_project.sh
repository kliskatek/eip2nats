#!/bin/bash
# setup_project.sh - Script para configurar el proyecto eip2nats completo

set -e

echo "=============================================="
echo "  Configuración de eip2nats Project"
echo "=============================================="
echo ""

# Función para instalar paquetes faltantes (con comando verificable)
install_package() {
    local package=$1
    local command_check=$2

    if ! command -v $command_check >/dev/null 2>&1; then
        echo "⚠️  $command_check no encontrado"
        echo "📦 Instalando $package..."

        if sudo apt-get update && sudo apt-get install -y $package; then
            echo "✅ $package instalado correctamente"
        else
            echo "❌ Error instalando $package"
            echo "   Por favor, instala manualmente con: sudo apt-get install $package"
            exit 1
        fi
    else
        echo "✅ $command_check ya está instalado"
    fi
}

# Función para instalar librerías de desarrollo
install_library() {
    local package=$1

    if ! dpkg -s $package >/dev/null 2>&1; then
        echo "⚠️  $package no encontrado"
        echo "📦 Instalando $package..."

        if sudo apt-get update && sudo apt-get install -y $package; then
            echo "✅ $package instalado correctamente"
        else
            echo "❌ Error instalando $package"
            echo "   Por favor, instala manualmente con: sudo apt-get install $package"
            exit 1
        fi
    else
        echo "✅ $package ya está instalado"
    fi
}

# Verificar e instalar requisitos
echo "📋 Verificando requisitos del sistema..."
echo ""

install_package "git" "git"
install_package "cmake" "cmake"
install_package "build-essential" "make"
install_package "g++" "g++"
install_package "python3" "python3"

# Instalar librerías de desarrollo
install_library "libssl-dev"
install_library "python3-dev"

echo ""
echo "✅ Todos los requisitos del sistema están instalados"
echo ""

# Crear entorno virtual
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo "📦 Entorno virtual ya existe en $VENV_DIR"
else
    echo "📦 Creando entorno virtual en $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Entorno virtual creado"
fi

# Activar entorno virtual
echo "🔌 Activando entorno virtual..."
source "$VENV_DIR/bin/activate"

# Actualizar pip
echo "⬆️  Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias de build en el venv
echo "📦 Instalando dependencias de build en el entorno virtual..."
pip install build pybind11 hatch twine

echo ""
echo "=============================================="
echo "  Paso 1: Compilar dependencias"
echo "=============================================="
echo ""
echo "Compilando dependencias:"
echo "  • nats.c (cliente NATS)"
echo "  • EIPScanner (librería EIP)"
echo "  • Binding Python"
echo ""

python scripts/build_dependencies.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error compilando dependencias"
    echo "Ver logs arriba para detalles"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  Paso 2: Crear wheel"
echo "=============================================="
echo ""

# Verificar que las librerías existen
if [ ! -d "src/eip2nats/lib" ] || [ -z "$(ls -A src/eip2nats/lib/*.so 2>/dev/null)" ]; then
    echo "❌ Error: No se encontraron librerías auxiliares en src/eip2nats/lib/"
    deactivate
    exit 1
fi

# Verificar que el módulo Python existe
if [ -z "$(ls src/eip2nats/eip_nats_bridge*.so 2>/dev/null)" ]; then
    echo "❌ Error: No se encontró el módulo Python compilado en src/eip2nats/"
    deactivate
    exit 1
fi

echo "✅ Módulo Python compilado:"
ls -lh src/eip2nats/eip_nats_bridge*.so 2>/dev/null | awk '{print "  ", $9, "(" $5 ")"}'
echo ""

echo "✅ Librerías auxiliares:"
ls -lh src/eip2nats/lib/*.so* 2>/dev/null | awk '{print "  ", $9, "(" $5 ")"}'
echo ""

python -m build --wheel

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error creando wheel"
    deactivate
    exit 1
fi

# Renombrar wheel a formato manylinux para PyPI
echo ""
echo "🔄 Renombrando wheel a formato manylinux..."
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
    print(f"✅ Renombrado a: {new_name}")
EOF

echo ""
echo "=============================================="
echo "  Paso 3: Instalar wheel en el venv"
echo "=============================================="
echo ""

# Instalar el wheel en el entorno virtual
WHEEL_FILE=$(ls dist/eip2nats-*.whl | head -n 1)

if [ -f "$WHEEL_FILE" ]; then
    echo "Instalando $WHEEL_FILE en el entorno virtual..."
    pip install "$WHEEL_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Wheel instalado en el entorno virtual"
    else
        echo "❌ Error instalando wheel"
        deactivate
        exit 1
    fi
else
    echo "❌ No se encontró el wheel"
    deactivate
    exit 1
fi

echo ""
echo "=============================================="
echo "  ✅ ¡Configuración Completa!"
echo "=============================================="
echo ""
echo "📦 Wheel creado en: dist/"
ls -lh dist/*.whl
echo ""
echo "🎉 El módulo está instalado en el entorno virtual"
echo ""
echo "🚀 Para usar el proyecto:"
echo ""
echo "  # Activar entorno virtual:"
echo "  source venv/bin/activate"
echo ""
echo "  # Probar:"
echo "  python -c 'import eip2nats; print(eip2nats.__version__)'"
echo ""
echo "  # Usar:"
echo "  python tu_script.py"
echo ""
echo "  # Desactivar cuando termines:"
echo "  deactivate"
echo ""
echo "📝 Documentación:"
echo "  cat README.md"
echo "  cat QUICKSTART.md"
echo ""

# Mantener el venv activado para que el usuario pueda trabajar
echo "💡 El entorno virtual sigue activo. Cuando termines, ejecuta: deactivate"
echo ""
