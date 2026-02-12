#!/bin/bash
# run.sh - Script rápido para ejecutar código con el entorno virtual

if [ ! -d "venv" ]; then
    echo "❌ El entorno virtual no existe."
    echo "Ejecuta primero: ./setup_project.sh"
    exit 1
fi

# Activar venv
source venv/bin/activate

# Si se pasa un argumento, ejecutarlo
if [ $# -eq 0 ]; then
    # Sin argumentos, ejecutar ejemplo básico
    echo "🚀 Ejecutando ejemplo básico..."
    echo ""
    python examples/basic_example.py
else
    # Con argumentos, ejecutar el comando dado
    echo "🚀 Ejecutando: $@"
    echo ""
    "$@"
fi

# Desactivar
deactivate
