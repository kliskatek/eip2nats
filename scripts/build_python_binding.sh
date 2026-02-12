#!/bin/bash
# build_python_binding.sh - Compilación rápida del binding Python para desarrollo

set -e

echo "🔧 Compilación Python Binding - eip2nats"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que las dependencias ya están compiladas
if [ ! -d "build/dependencies/nats.c/build" ] || [ ! -d "build/dependencies/EIPScanner/build" ]; then
    echo "❌ Error: Las dependencias no están compiladas"
    echo "Ejecuta primero: python scripts/build_dependencies.py"
    exit 1
fi

# Directorios
NATS_DIR="build/dependencies/nats.c"
EIP_DIR="build/dependencies/EIPScanner"
SRC_DIR="src/eip2nats"
LIB_DIR="src/eip2nats/lib"

# Obtener configuración de Python
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
PYBIND_INCLUDE=$(python3 -c "import pybind11; print(pybind11.get_include())")
EXT_SUFFIX=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")

OUTPUT="${SRC_DIR}/eip_nats_bridge${EXT_SUFFIX}"

echo "📋 Configuración:"
echo "   Fuentes: ${SRC_DIR}"
echo "   Output: ${OUTPUT}"
echo ""

# Compilar
echo "🔨 Compilando binding C++..."

g++ -g -O0 \
    -Wall -Wextra \
    -shared \
    -std=c++17 \
    -fPIC \
    -I${PYBIND_INCLUDE} \
    -I${NATS_DIR}/src \
    -I${EIP_DIR}/src \
    -I${SRC_DIR} \
    -I${PYTHON_INCLUDE} \
    ${SRC_DIR}/bindings.cpp \
    ${SRC_DIR}/EIPtoNATSBridge.cpp \
    -o ${OUTPUT} \
    -L${LIB_DIR} \
    -lnats \
    -lEIPScanner \
    -lpthread \
    -Wl,-rpath,\$ORIGIN/lib

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Compilación exitosa!"
    echo ""
    echo "📦 Módulo compilado: ${OUTPUT}"
    echo "   Tamaño: $(du -h ${OUTPUT} | cut -f1)"
    echo ""
    echo "🔍 Para debugear con GDB:"
    echo "   gdb --args python3 examples/basic_example.py"
    echo ""
    echo "🧪 Para probar:"
    echo "   source venv/bin/activate"
    echo "   python3 -c 'import eip2nats; print(eip2nats.__version__)'"
    echo "   python3 examples/basic_example.py"
    echo ""
else
    echo ""
    echo "❌ Error en la compilación"
    exit 1
fi
