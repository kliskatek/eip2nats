# Examples - eip2nats

Ejemplos de uso del puente EIP to NATS.

## 📁 Archivo

### `example_python.py`
Ejemplo básico y completo del uso del bridge.

**Características:**
- Configuración simple
- Monitoreo de estadísticas cada 5 segundos
- Manejo de señales (Ctrl+C)
- Código limpio y comentado

**Ejecutar:**
```bash
source venv/bin/activate
python examples/example_python.py
```

O con el helper:
```bash
./run.sh  # Ejecuta example_python.py por defecto
```

---

## 🔧 Configuración

El ejemplo usa por defecto:
- **PLC**: `192.168.17.200`
- **NATS**: `nats://192.168.17.138:4222`
- **Subject**: `plc.eip.data`
- **Formato**: Binario

### Cambiar IPs

Edita las variables al inicio del script:

```python
plc_address = "192.168.1.100"      # Tu IP del PLC
nats_url = "nats://localhost:4222" # Tu servidor NATS
nats_subject = "mi.topic"          # Tu subject
```

### Cambiar formato a JSON

```python
use_binary = False  # False = JSON, True = Binario
```

---

## 📊 Crear tu propio ejemplo

```python
import eip2nats
import time

# 1. Crear bridge
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",              # PLC
    "nats://192.168.17.138:4222",  # NATS
    "plc.data"                     # Subject
)

# 2. Iniciar
if bridge.start():
    # 3. Hacer algo mientras corre
    time.sleep(60)
    
    # 4. Ver estadísticas
    print(f"Recibidos: {bridge.get_received_count()}")
    print(f"Publicados: {bridge.get_published_count()}")
    
    # 5. Detener
    bridge.stop()
```

---

## 🎯 Casos de Uso Avanzados

### Ejemplo 1: Con Flask API

```python
from flask import Flask, jsonify
import eip2nats

app = Flask(__name__)
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data"
)

@app.route('/start')
def start():
    return jsonify({"success": bridge.start()})

@app.route('/stats')
def stats():
    return jsonify({
        "running": bridge.is_running(),
        "received": bridge.get_received_count(),
        "published": bridge.get_published_count()
    })

@app.route('/stop')
def stop():
    bridge.stop()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Ejemplo 2: Múltiples PLCs

```python
import eip2nats
import time

# Crear múltiples bridges
bridges = [
    eip2nats.EIPtoNATSBridge("192.168.17.200", "nats://localhost:4222", "plc1.data"),
    eip2nats.EIPtoNATSBridge("192.168.17.201", "nats://localhost:4222", "plc2.data"),
    eip2nats.EIPtoNATSBridge("192.168.17.202", "nats://localhost:4222", "plc3.data"),
]

# Iniciar todos
for i, bridge in enumerate(bridges):
    if bridge.start():
        print(f"✅ Bridge {i+1} iniciado")

# Monitorear todos
try:
    while True:
        time.sleep(5)
        for i, bridge in enumerate(bridges):
            print(f"Bridge {i+1}: RX={bridge.get_received_count()}, "
                  f"TX={bridge.get_published_count()}")
except KeyboardInterrupt:
    pass

# Detener todos
for bridge in bridges:
    bridge.stop()
```

### Ejemplo 3: Con Logging

```python
import eip2nats
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data"
)

logger.info("Iniciando bridge...")
if bridge.start():
    logger.info("Bridge iniciado correctamente")
    
    try:
        while bridge.is_running():
            time.sleep(10)
            logger.info(f"Stats - RX: {bridge.get_received_count()}, "
                       f"TX: {bridge.get_published_count()}")
    except KeyboardInterrupt:
        logger.info("Interrupción recibida")
    finally:
        bridge.stop()
        logger.info("Bridge detenido")
else:
    logger.error("Error al iniciar el bridge")
```

---

## 💡 Tips

1. **Siempre usa `try/finally`** para asegurar que `bridge.stop()` se ejecute
2. **Verifica `bridge.is_running()`** periódicamente para detectar desconexiones
3. **Implementa reconexión automática** si el bridge se cae
4. **Usa logging** para producción en lugar de print
5. **Monitorea las estadísticas** para detectar problemas

---

## 🐛 Troubleshooting

### El bridge no se conecta al PLC

- Verifica que el PLC esté encendido y accesible
- Prueba hacer ping a la IP del PLC
- Verifica la configuración del PLC (Assembly, RPI, path)

### No se reciben datos

- Comprueba que el PLC esté enviando datos
- Verifica la configuración del Assembly
- Revisa que el RPI no sea demasiado largo

### No se publican datos a NATS

- Verifica que el servidor NATS esté corriendo
- Comprueba la conectividad de red
- Revisa los logs del servidor NATS

---

Para más información sobre desarrollo y debugging, consulta [`DEVELOPMENT.md`](../DEVELOPMENT.md) en la raíz del proyecto.

