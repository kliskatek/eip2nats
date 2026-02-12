#!/bin/bash
# activate.sh - Helper para activar el entorno virtual

if [ ! -d "venv" ]; then
    echo "❌ El entorno virtual no existe."
    echo "Ejecuta primero: ./setup_project.sh"
    exit 1
fi

echo "🔌 Activando entorno virtual..."
source venv/bin/activate

echo "✅ Entorno virtual activado"
echo ""
echo "💡 Comandos útiles:"
echo "  python -c 'import eip2nats; print(eip2nats.__version__)'  # Verificar instalación"
echo "  python tu_script.py                                       # Ejecutar tu código"
echo "  deactivate                                                # Desactivar venv"
echo ""

# Iniciar un nuevo shell para mantener el entorno activado
exec bash --init-file <(echo "source venv/bin/activate; PS1='(eip2nats) \u@\h:\w\$ '")
