# Guía de Desarrollo y Debugging - eip2nats

Esta guía explica cómo desarrollar y debugear el código C++ eficientemente.

## 🎯 Dos Enfoques de Desarrollo

### Enfoque 1: C++ Standalone ⭐ **RECOMENDADO PARA DESARROLLO C++**

**Ventajas:**
- ✅ Debugging nativo C++ (sin Python en el medio)
- ✅ Ciclo de desarrollo más rápido
- ✅ Breakpoints, watches, step-through perfecto
- ✅ Ideal para VSCode
- ✅ No necesitas Python para probar la lógica C++

**Uso:**
```bash
# 1. Compilar test standalone
./scripts/build_standalone.sh

# 2. Ejecutar
./test_standalone

# 3. Debugear con VSCode
# - Abre VSCode
# - F5 → "C++: Debug Standalone"
# - Breakpoints funcionan perfectamente

# O con GDB
gdb ./test_standalone
```

**Cuándo usar:** Cuando estás desarrollando nueva funcionalidad C++ o debugeando bugs en la lógica del bridge.

---

### Enfoque 2: Python Binding ⭐ **RECOMENDADO PARA TEST DE INTEGRACIÓN**

**Ventajas:**
- ✅ Pruebas de integración Python ↔ C++
- ✅ Test del API final que usan los usuarios
- ✅ Más rápido que regenerar el wheel completo

**Uso:**
```bash
# Compilar binding Python (después de cambios C++)
./scripts/build_python_binding.sh

# Probar
python examples/basic_example.py
```

**Cuándo usar:** Después de terminar cambios en C++ y quieres verificar que la integración Python funciona.

---

### Enfoque 3: Wheel Completo (Solo para Release)

```bash
# Solo cuando estés listo para distribuir
hatch build
```

**Cuándo usar:** Para crear el paquete final que distribuirás a otros usuarios.

---

## 🔄 Workflow de Desarrollo Recomendado

### 1. Desarrollar Nueva Funcionalidad en C++

```bash
# Paso 1: Editar código C++
nano src/eip2nats/EIPtoNATSBridge.cpp

# Paso 2: Probar con C++ standalone
./scripts/build_standalone.sh
./test_standalone

# Paso 3: Debugear si es necesario (VSCode F5)
# Coloca breakpoints en VSCode y presiona F5

# Paso 4: Cuando funcione en C++, probar con Python
./scripts/build_python_binding.sh
python examples/basic_example.py

# Paso 5: Si todo funciona, crear wheel para distribución
hatch build
```

### 2. Debugear un Bug

**Si el bug es en lógica C++:**
```bash
# Usa el standalone - debugging perfecto
./scripts/build_standalone.sh
# En VSCode: F5 → "C++: Debug Standalone"
```

**Si el bug es en la interfaz Python:**
```bash
# Usa Python
python examples/debug_example.py
# O VSCode: F5 → "Python: Debug Example"
```

**Si no sabes dónde está el bug:**
```bash
# Empieza con standalone C++
./scripts/build_standalone.sh
./test_standalone
# Si funciona en C++, el bug está en el binding Python
```

---

## 🔄 Workflow de Desarrollo

### 1. Setup Inicial (Una vez)

```bash
# Compilar dependencias (solo la primera vez)
python scripts/build_dependencies.py
```

Esto compila `nats.c` y `EIPScanner` en `build/dependencies/`. Solo necesitas hacerlo una vez.

### 2. Desarrollo Iterativo

```bash
# 1. Editar código C++
nano src/eip2nats/EIPtoNATSBridge.cpp

# 2. Compilación rápida (segundos)
./dev_build.sh

# 3. Probar inmediatamente
source venv/bin/activate
python examples/basic_example.py
```

**¡No necesitas `hatch build` para cada cambio!**

### 3. Cuando Estés Satisfecho

```bash
# Crear el wheel final para distribución
hatch build
```

---

## 🐍 Debugging Python

### Opción 1: pdb (Python Debugger) - Recomendado

**Para debugear la lógica Python:**

```python
# examples/my_debug.py
import eip2nats
import pdb

bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data"
)

# Breakpoint aquí
pdb.set_trace()

if bridge.start():
    print(f"Running: {bridge.is_running()}")
    bridge.stop()
```

**Ejecutar:**
```bash
python examples/my_debug.py

# Comandos pdb:
(Pdb) n          # Next line
(Pdb) s          # Step into
(Pdb) c          # Continue
(Pdb) p bridge   # Print variable
(Pdb) l          # List code
(Pdb) h          # Help
```

### Opción 2: VSCode Debug

Crear `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug Example",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/examples/basic_example.py",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            }
        }
    ]
}
```

Luego F5 para debugear con breakpoints visuales.

### Opción 3: ipdb (pdb mejorado)

```bash
pip install ipdb

# En tu código
import ipdb; ipdb.set_trace()
```

Tiene autocompletado y syntax highlighting.

---

## 🔀 Debugging Python + C++ Juntos

### GDB con Python (Avanzado)

**Solo útil si necesitas debugear la interfaz Python ↔ C++**

```bash
# Instalar python3-dbg (símbolos de Python)
sudo apt-get install python3-dbg gdb

# Ejecutar
gdb --args python3 examples/basic_example.py
```

**Dentro de GDB:**
```gdb
# Breakpoint en C++
(gdb) break EIPtoNATSBridge::start
(gdb) run

# Ver stack Python + C++
(gdb) py-bt

# Ver variables Python
(gdb) py-print variable_name

# Ver locals Python
(gdb) py-locals
```

**⚠️ Limitaciones:**
- Requiere `python3-dbg` instalado
- Más complejo que pdb
- Solo útil para bugs en la interfaz pybind11

### Mejor Estrategia: Divide y Conquista

**1. ¿Bug en Python?** → Usa `pdb`
```python
import pdb; pdb.set_trace()
```

**2. ¿Bug en C++?** → Usa `gdb`
```bash
gdb --args python3 examples/basic_example.py
(gdb) break EIPtoNATSBridge::publishToNATS
```

**3. ¿No sabes dónde?** → Empieza con `pdb`, si llega a C++, cambia a `gdb`

---

## 🎯 Debugging por Escenario

### Escenario 1: "No se conecta al PLC"

```python
# Usar pdb para ver qué retorna start()
import pdb
import eip2nats

bridge = eip2nats.EIPtoNATSBridge(...)
pdb.set_trace()
result = bridge.start()  # Step into con 's'
print(f"Start result: {result}")
```

Si necesitas más detalle, cambia a GDB:
```bash
gdb --args python3 examples/basic_example.py
(gdb) break EIPtoNATSBridge::start
(gdb) run
```

### Escenario 2: "Crash en C++"

```bash
# GDB capturará el segfault
gdb --args python3 examples/basic_example.py
(gdb) run
# Cuando crashee:
(gdb) bt  # Ver backtrace
(gdb) frame 0
(gdb) info locals
```

### Escenario 3: "No recibe datos del PLC"

```cpp
// Agregar prints en C++
void EIPtoNATSBridge::onEIPDataReceived(...) {
    std::cerr << "DEBUG: onEIPDataReceived called, size=" 
              << data.size() << std::endl;
    // ...
}
```

Recompilar y ejecutar:
```bash
./dev_build.sh
python3 examples/basic_example.py 2>&1 | tee debug.log
```

### Escenario 4: "Memory leak"

```bash
# Valgrind detecta automáticamente
valgrind --leak-check=full python3 examples/basic_example.py
```

---

## 🔧 Herramientas de Debugging

### Compilar en Modo Debug

El script `dev_build.sh` ya compila con símbolos de debug (`-g -O0`).

### Debugear Python + C++

```bash
# 1. Compilar con símbolos
./dev_build.sh

# 2. Ejecutar con GDB
gdb --args python3 examples/basic_example.py

# Dentro de GDB:
(gdb) break EIPtoNATSBridge::start
(gdb) run
(gdb) step
(gdb) print variable_name
(gdb) continue
```

### Breakpoints Útiles

```gdb
# En funciones específicas
break EIPtoNATSBridge::start
break EIPtoNATSBridge::publishToNATS
break onEIPDataReceived

# En archivos específicos
break EIPtoNATSBridge.cpp:123

# Condicionales
break EIPtoNATSBridge::publishToNATS if data.size() > 100
```

### Comandos GDB Útiles

```gdb
# Ver backtrace
bt

# Ver variables locales
info locals

# Siguiente línea
n (next)

# Entrar en función
s (step)

# Continuar
c (continue)

# Ver valor
print variable
print *pointer

# Watchpoint (detener cuando variable cambia)
watch receivedCount_
```

## 🔧 Herramientas de Debugging

| Tool | Para | Instalación |
|------|------|-------------|
| **pdb** | Debug Python | Built-in |
| **ipdb** | pdb mejorado | `pip install ipdb` |
| **VSCode** | Debug visual | Instalar extensión Python |
| **GDB** | Debug C++ | `sudo apt-get install gdb` |
| **python3-dbg** | Python symbols | `sudo apt-get install python3-dbg` |
| **Valgrind** | Memory leaks | `sudo apt-get install valgrind` |

### Quick Reference

```bash
# Python debugging
python3 -m pdb examples/basic_example.py

# C++ debugging  
gdb --args python3 examples/basic_example.py

# Memory leaks
valgrind --leak-check=full python3 examples/basic_example.py

# Con logs
python3 examples/basic_example.py 2>&1 | tee debug.log
```

### Agregar Logs Temporales

```cpp
// En EIPtoNATSBridge.cpp
#include <iostream>

void EIPtoNATSBridge::onEIPDataReceived(...) {
    std::cerr << "DEBUG: Received " << data.size() << " bytes" << std::endl;
    std::cerr << "DEBUG: First byte: " << (int)data[0] << std::endl;
    
    // Tu código...
}
```

### Ver Logs

```bash
./dev_build.sh
python3 examples/basic_example.py 2>&1 | tee debug.log
```

---

## 🧪 Testing Rápido

### Test Unitario C++ (Opcional)

Crear `tests/test_cpp.cpp`:

```cpp
#include "../src/eip2nats/EIPtoNATSBridge.h"
#include <iostream>

int main() {
    try {
        bridge::EIPtoNATSBridge bridge(
            "192.168.17.200",
            "nats://192.168.17.138:4222",
            "test.subject"
        );
        
        std::cout << "Bridge created successfully" << std::endl;
        
        if (bridge.start()) {
            std::cout << "Bridge started" << std::endl;
            sleep(5);
            std::cout << "Received: " << bridge.getReceivedCount() << std::endl;
            bridge.stop();
            return 0;
        }
        
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
}
```

Compilar y ejecutar:

```bash
g++ -g -std=c++17 \
    -I build/dependencies/nats.c/src \
    -I build/dependencies/EIPScanner/src \
    -I src/eip2nats \
    tests/test_cpp.cpp \
    src/eip2nats/EIPtoNATSBridge.cpp \
    -L src/eip2nats/lib \
    -lnats -lEIPScanner -lpthread \
    -Wl,-rpath,src/eip2nats/lib \
    -o test_cpp

./test_cpp
```

---

## 📊 Valgrind (Memory Leaks)

### Detectar Memory Leaks

```bash
# Compilar con debug
./dev_build.sh

# Ejecutar con valgrind
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         python3 examples/basic_example.py
```

### Interpretar Resultados

```
LEAK SUMMARY:
   definitely lost: 0 bytes      ← Fugas confirmadas (arreglar!)
   indirectly lost: 0 bytes      ← Fugas indirectas
   possibly lost: X bytes        ← Posibles fugas (revisar)
   still reachable: X bytes      ← Memoria no liberada (normal en exit)
```

---

## 🎯 Estructura de Archivos para Desarrollo

```
eip2nats/
├── src/eip2nats/
│   ├── bindings.cpp           ← Editar: bindings pybind11
│   ├── EIPtoNATSBridge.cpp    ← Editar: lógica principal
│   ├── EIPtoNATSBridge.h      ← Editar: interfaz
│   └── lib/                   ← No tocar (librerías compiladas)
│
├── build/dependencies/        ← No tocar (deps compiladas)
│   ├── nats.c/
│   └── EIPScanner/
│
├── dev_build.sh               ← Usar: compilación rápida
├── examples/                  ← Usar: para probar
└── tests/                     ← Crear: tests C++ standalone
```

---

## 🔧 Compilación Manual (Avanzado)

Si necesitas control total:

```bash
# Variables
NATS_DIR=build/dependencies/nats.c
EIP_DIR=build/dependencies/EIPScanner
SRC_DIR=src/eip2nats
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
PYBIND_INCLUDE=$(python3 -c "import pybind11; print(pybind11.get_include())")
EXT_SUFFIX=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")

# Compilar con warnings extra
g++ -g -O0 -Wall -Wextra -Wpedantic \
    -shared -std=c++17 -fPIC \
    -I${PYBIND_INCLUDE} \
    -I${NATS_DIR}/src \
    -I${EIP_DIR}/src \
    -I${SRC_DIR} \
    -I${PYTHON_INCLUDE} \
    ${SRC_DIR}/bindings.cpp \
    ${SRC_DIR}/EIPtoNATSBridge.cpp \
    -o ${SRC_DIR}/eip_nats_bridge${EXT_SUFFIX} \
    -L${SRC_DIR}/lib \
    -lnats -lEIPScanner -lpthread \
    -Wl,-rpath,\$ORIGIN/lib

# Con sanitizers (detectar bugs)
g++ -g -O0 -fsanitize=address -fsanitize=undefined \
    # ... resto de flags ...
```

---

## 🚀 Workflow Completo

### Desarrollo de Nueva Funcionalidad

```bash
# 1. Crear rama (opcional)
git checkout -b feature/nueva-funcionalidad

# 2. Editar código
nano src/eip2nats/EIPtoNATSBridge.cpp

# 3. Compilar y probar iterativamente
./dev_build.sh
python3 examples/basic_example.py
# Repetir hasta que funcione

# 4. Debug si es necesario
gdb --args python3 examples/basic_example.py

# 5. Verificar memory leaks
valgrind --leak-check=full python3 examples/basic_example.py

# 6. Cuando esté listo, crear wheel
hatch build

# 7. Test del wheel
pip install --force-reinstall dist/eip2nats-*.whl
python3 examples/test_bridge.py

# 8. Commit
git add src/eip2nats/
git commit -m "feat: nueva funcionalidad"
```

---

## 💡 Tips

1. **Usa `dev_build.sh`** para iteración rápida - compila en ~2 segundos
2. **No regeneres wheel** hasta que estés satisfecho con los cambios
3. **GDB es tu amigo** para bugs complejos
4. **Print debugging** es rápido para cosas simples
5. **Valgrind** para memory leaks antes de release
6. **Compila con `-O0 -g`** durante desarrollo
7. **Usa `-O3`** solo para release/wheel final

---

## 🔄 Comparación de Métodos

| Método | Tiempo | Uso |
|--------|--------|-----|
| `./dev_build.sh` | ~2 seg | Desarrollo iterativo ✅ |
| `python scripts/build_dependencies.py` | ~5 min | Solo primera vez o cambio deps |
| `hatch build` | ~1 min | Release/distribución final |

---

## ❓ FAQ

**P: ¿Debo ejecutar `build_dependencies.py` cada vez?**
R: No, solo la primera vez o si actualizas nats.c/EIPScanner.

**P: ¿Puedo editar el código sin venv activado?**
R: Sí para editar, pero necesitas venv activado para compilar/probar.

**P: ¿Los cambios en C++ requieren reinstalar el wheel?**
R: No, `dev_build.sh` actualiza el módulo in-place.

**P: ¿Cómo vuelvo a una compilación limpia?**
R: `rm src/eip2nats/eip_nats_bridge*.so && ./dev_build.sh`

**P: ¿Puedo usar CLion/VSCode para debugear?**
R: Sí, configura para usar Python con GDB y apunta al `.so`

---

¡Ahora tienes un workflow de desarrollo eficiente! 🎉
