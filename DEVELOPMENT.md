# Desarrollo con VSCode

Guia para desarrollar y depurar eip2nats usando Visual Studio Code.

## Requisitos

### Extensiones recomendadas

Al abrir el proyecto, VSCode sugerira instalar las extensiones recomendadas (`.vscode/extensions.json`):

- **C/C++** (`ms-vscode.cpptools`) - IntelliSense, debugging
- **C/C++ Extension Pack** (`ms-vscode.cpptools-extension-pack`)
- **Python** (`ms-python.python`) - IntelliSense, debugging
- **Pylance** (`ms-python.vscode-pylance`) - Analisis estatico Python
- **CMake** (`twxs.cmake`) - Syntax highlighting CMake
- **CMake Tools** (`ms-vscode.cmake-tools`)

### Compilar dependencias (primera vez)

Antes de poder compilar y depurar, hay que compilar las dependencias:

```bash
# Linux
./setup_project_linux.sh

# Windows (PowerShell)
.\setup_project_windows.ps1
```

O manualmente:
```bash
python scripts/build_nats.py
python scripts/build_eipscanner.py
python scripts/build_binding.py
```

---

## Build Tasks

El proyecto incluye tareas de build preconfiguradas. Ejecutar con `Ctrl+Shift+B` (build task por defecto) o `Ctrl+Shift+P` > "Tasks: Run Task".

| Tarea | Descripcion |
|-------|-------------|
| `build-example-cpp` | Compila el ejemplo C++ (tarea por defecto con `Ctrl+Shift+B`) |
| `build-binding` | Compila el binding Python (.pyd/.so) |
| `build-nats` | Compila nats.c desde fuentes |
| `build-eipscanner` | Compila EIPScanner desde fuentes |
| `build-all` | Ejecuta nats + eipscanner + binding en secuencia |
| `clean` | Elimina artefactos compilados |

---

## Configuraciones de Debug (F5)

Hay 3 configuraciones de debug disponibles en el dropdown de Run and Debug (`Ctrl+Shift+D`):

### C++ Example (build + debug) [Windows]

Para depurar el bridge C++ sin Python. Usa el debugger de Visual Studio (`cppvsdbg`).

- **Pre-launch**: Compila automaticamente con `build-example-cpp`
- **Ejecutable**: `build/example_cpp/example_cpp.exe`
- **DLLs**: Se agregan al PATH automaticamente (`src/eip2nats/lib/`)
- **stopAtEntry**: `true` - se detiene en `main()` para poner breakpoints

**Uso tipico:**
1. Abrir `examples/example_cpp.cpp` o `src/eip2nats/EIPtoNATSBridge.cpp`
2. Poner breakpoints
3. Seleccionar "C++ Example (build + debug) [Windows]" en el dropdown
4. Pulsar F5

### C++ Example (build + debug) [Linux]

Igual que la version Windows pero usando GDB (`cppdbg`).

- **Ejecutable**: `build/example_cpp/example_cpp`
- **Debugger**: GDB (`/usr/bin/gdb`)

### Python Example (debug)

Para depurar el bridge a traves del binding Python.

- **Script**: `examples/example_python.py`
- **justMyCode**: `false` - permite entrar en el codigo del binding
- **PYTHONPATH**: Apunta a `src/` para importar el modulo local

**Uso tipico:**
1. Abrir `examples/example_python.py`
2. Poner breakpoints en el script Python
3. Seleccionar "Python Example (debug)"
4. Pulsar F5

---

## Workflow de desarrollo

### Modificar codigo C++ del bridge

```
1. Editar src/eip2nats/EIPtoNATSBridge.cpp o .h
2. Ctrl+Shift+B (compila ejemplo C++)
3. F5 con "C++ Example [Windows/Linux]"
4. Depurar con breakpoints
```

El ejemplo C++ (`examples/example_cpp.cpp`) permite probar el bridge directamente sin pasar por Python, lo que simplifica el debugging del codigo C++.

### Modificar bindings Python

```
1. Editar src/eip2nats/bindings.cpp
2. Ctrl+Shift+P > "Tasks: Run Task" > "build-binding"
3. F5 con "Python Example (debug)"
```

### Modificar ejemplo Python

```
1. Editar examples/example_python.py
2. F5 con "Python Example (debug)"
   (no necesita recompilar nada)
```

---

## IntelliSense C++

La configuracion de IntelliSense esta en `.vscode/settings.json` y `.vscode/c_cpp_properties.json`. Los include paths apuntan a:

- `src/eip2nats/` - Codigo fuente del bridge
- `build/dependencies/nats.c/src/` - Headers de nats.c
- `build/dependencies/EIPScanner/src/` - Headers de EIPScanner

Estos directorios se crean automaticamente al compilar las dependencias. Si IntelliSense muestra errores de "include not found", ejecuta primero `build-nats` y `build-eipscanner`.

---

## Estructura de artefactos

Despues de compilar, los artefactos quedan en:

```
src/eip2nats/
    eip_nats_bridge*.pyd      # Binding Python (Windows)
    eip_nats_bridge*.so        # Binding Python (Linux)
    lib/
        nats.dll / libnats.so          # Libreria NATS
        EIPScanner.dll / libEIPScanner.so  # Libreria EIPScanner

build/
    example_cpp/
        example_cpp.exe / example_cpp  # Ejemplo C++ compilado
    dependencies/
        nats.c/                        # Fuentes + build de nats.c
        EIPScanner/                    # Fuentes + build de EIPScanner
    binding/                           # Build intermedio del binding
```

---

## Troubleshooting

### IntelliSense no encuentra headers

Ejecutar las tareas `build-nats` y `build-eipscanner` para clonar y compilar las dependencias. Los headers estan en `build/dependencies/`.

### "DLL not found" al depurar C++ en Windows

La configuracion de launch.json ya agrega `src/eip2nats/lib/` al PATH. Si aun falla, verificar que las DLLs existen:
```
src/eip2nats/lib/nats.dll
src/eip2nats/lib/EIPScanner.dll
```

### "bad_alloc" al conectar al PLC (C++ Windows)

Esto ocurre si el ejemplo se compila en modo Debug pero las DLLs estan en Release (CRT mismatch). El build ya usa `RelWithDebInfo` para evitar esto. Si recompilas manualmente, asegurate de usar `--config RelWithDebInfo`.

### El binding Python no carga

Verificar que el `.pyd`/`.so` esta en `src/eip2nats/`:
```bash
# Windows
dir src\eip2nats\eip_nats_bridge*.pyd

# Linux
ls src/eip2nats/eip_nats_bridge*.so
```

Si no existe, ejecutar la tarea `build-binding`.

### Errores de compilacion en EIPScanner (Windows)

EIPScanner tiene problemas conocidos con Winsock en Windows. El script `build_eipscanner.py` aplica patches automaticamente. Si falla, verificar que Visual Studio Build Tools esta instalado con el componente "Desktop development with C++".
