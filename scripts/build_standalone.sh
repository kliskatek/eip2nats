#!/bin/bash
# build_standalone.sh - Compila el test C++ standalone

set -e

echo "🔨 Compilando test standalone C++"
echo "=================================="
echo ""

# Verificar dependencias
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
TEST_DIR="tests"

OUTPUT="test_standalone"

echo "📋 Configuración:"
echo "   Fuente: ${TEST_DIR}/test_standalone.cpp"
echo "   Output: ${OUTPUT}"
echo ""

# Compilar con símbolos de debug
echo "🔨 Compilando..."

g++ -g -O0 \
    -Wall -Wextra \
    -std=c++17 \
    -I${NATS_DIR}/src \
    -I${EIP_DIR}/src \
    -I${SRC_DIR} \
    ${TEST_DIR}/test_standalone.cpp \
    ${SRC_DIR}/EIPtoNATSBridge.cpp \
    -L${LIB_DIR} \
    -lnats \
    -lEIPScanner \
    -lpthread \
    -Wl,-rpath,${LIB_DIR} \
    -o ${OUTPUT}

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Compilación exitosa!"
    echo ""
    echo "📦 Ejecutable: ./${OUTPUT}"
    echo "   Tamaño: $(du -h ${OUTPUT} | cut -f1)"
    echo ""
    echo "🚀 Para ejecutar:"
    echo "   ./${OUTPUT}"
    echo ""
    echo "🐛 Para debugear con GDB:"
    echo "   gdb ./${OUTPUT}"
    echo ""
    echo "🔍 Para debugear con VSCode:"
    echo "   1. Abre VSCode"
    echo "   2. F5 (usa la configuración 'C++: Debug Standalone')"
    echo ""
else
    echo ""
    echo "❌ Error en la compilación"
    exit 1
fi
