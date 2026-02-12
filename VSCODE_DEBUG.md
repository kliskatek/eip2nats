# VSCode Debugging - Quick Start

## 🚀 Setup Rápido

### 1. Compilar Dependencias (Primera vez)

```bash
# En la terminal (Ctrl+`)
python scripts/build_dependencies.py
```

### 2. Compilar el Test Standalone

**Opción A: Terminal**
```bash
./scripts/build_standalone.sh
```

**Opción B: VSCode Task**
- `Ctrl+Shift+B` (build task)
- O `Ctrl+Shift+P` → "Tasks: Run Build Task"

### 3. Debugear

1. Abrir `tests/test_standalone.cpp`
2. Colocar breakpoint (click izquierda del número de línea)
3. `F5` → Seleccionar **"C++: Debug Standalone (Manual Build)"**
4. ¡El programa se detiene en tu breakpoint!

## 🎯 Configuraciones de Debug Disponibles

Al presionar `F5`, verás estas opciones:

### C++: Debug Standalone (Auto Build) ⚠️
- Compila automáticamente antes de debugear
- **Problema conocido**: Puede fallar si la ruta no se resuelve
- Usa la versión Manual si tienes problemas

### C++: Debug Standalone (Manual Build) ✅ RECOMENDADO
- Asume que ya compilaste con `./build_standalone.sh`
- Más confiable
- **Workflow:**
  1. Terminal: `./build_standalone.sh`
  2. F5 → Elegir esta opción
  3. Debug!

### Python: Debug Example
- Debugea `examples/basic_example.py`
- Breakpoints en Python funcionan

### Python: Debug with pdb
- Debugea `examples/debug_example.py`
- Incluye breakpoints pdb

## 🐛 Troubleshooting

### "Cannot find task 'build-standalone'"

**Solución 1: Compila manualmente**
```bash
./build_standalone.sh
```
Luego F5 → "C++: Debug Standalone (Manual Build)"

**Solución 2: Verifica workspace**
- Asegúrate de abrir VSCode desde la raíz del proyecto:
  ```bash
  code /path/to/eip2nats
  ```
- NO abras VSCode desde un subdirectorio

**Solución 3: Ejecuta task manualmente**
- `Ctrl+Shift+P`
- "Tasks: Run Task"
- Elegir "build-standalone"

### "Program not found: test_standalone"

El ejecutable no existe. Compila primero:
```bash
./build_standalone.sh
```

### Breakpoints no funcionan

1. **Verifica símbolos de debug:**
   ```bash
   file test_standalone
   # Debe decir "not stripped"
   ```

2. **Recompila con debug:**
   ```bash
   ./build_standalone.sh
   # Usa -g -O0 automáticamente
   ```

3. **Verifica que el código está actualizado:**
   - Edita el .cpp
   - Recompila
   - Debug de nuevo

## 💡 Workflow Recomendado

```bash
# Terminal 1: Edit → Build → Debug loop
nano src/eip2nats/EIPtoNATSBridge.cpp
./build_standalone.sh
# F5 en VSCode

# Repetir:
# - Editar código
# - ./build_standalone.sh
# - F5
```

## 🎓 Tips VSCode

### Shortcuts Útiles
- `F5` - Start debugging
- `F9` - Toggle breakpoint
- `F10` - Step over
- `F11` - Step into
- `Shift+F11` - Step out
- `Ctrl+Shift+F5` - Restart
- `Shift+F5` - Stop

### Ventanas Útiles
- **Variables** - Ver todas las variables locales
- **Watch** - Agregar expresiones custom
- **Call Stack** - Ver el stack de llamadas
- **Debug Console** - Ejecutar expresiones GDB

### Breakpoints Condicionales
1. Click derecho en breakpoint
2. "Edit Breakpoint"
3. Agregar condición: `received > 100`

### Logpoints (sin detener)
1. Click derecho en línea
2. "Add Logpoint"
3. Escribe: `Received {received} messages`

## 📊 Ejemplo de Sesión Debug

```
1. Abrir tests/test_standalone.cpp
2. Breakpoint en línea 40 (antes de bridge.start())
3. F5 → "C++: Debug Standalone (Manual Build)"
4. Programa se detiene en línea 40
5. En Variables panel, ver:
   - bridge (EIPtoNATSBridge)
   - plc_address = "192.168.17.200"
   - nats_url = "nats://192.168.17.138:4222"
6. F10 (step over) varias veces
7. Watch: bridge.isRunning()
8. F5 para continuar
```

## 🔄 Actualizar Código C++

```bash
# 1. Editar
nano src/eip2nats/EIPtoNATSBridge.cpp

# 2. Compilar standalone
./build_standalone.sh

# 3. Debug en VSCode (F5)

# 4. Cuando funcione, compilar Python binding
./dev_build.sh

# 5. Probar Python
python examples/basic_example.py

# 6. Release
hatch build
```

---

¡Listo para debugear! 🎉
