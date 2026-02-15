# eip2nats - EtherNet/IP to NATS Bridge

Puente completo entre dispositivos EtherNet/IP (PLCs) y servidores NATS, **con todas las dependencias incluidas** en el wheel.

## ✨ Características

- ✅ **Self-contained**: Incluye libnats y libEIPScanner compiladas
- ✅ **Zero dependencies**: No requiere instalación de librerías del sistema
- ✅ **Entorno virtual**: Compatible con Raspberry Pi OS (sin pip install global)
- ✅ **Simple instalación**: Setup automático con un comando
- ✅ **Alto rendimiento**: Bindings nativos C++ con pybind11
- ✅ **Thread-safe**: Manejo seguro de múltiples conexiones

## 🚀 Instalación Rápida

### Setup Completo Automático

```bash
./setup_project.sh
```

Esto hace TODO automáticamente:
1. Crea un entorno virtual en `venv/`
2. Instala Hatch y pybind11
3. Compila nats.c, EIPScanner y el binding Python
4. Crea el wheel
5. Instala el wheel en el venv

### Uso Posterior

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar ejemplo básico
python examples/example_python.py

# O test completo
python examples/test_bridge.py

# O usar el script helper
./run.sh  # Ejecuta example_python.py por defecto
./run.sh python examples/test_bridge.py

# Desactivar cuando termines
deactivate
```

## 💻 Uso

```python
import eip2nats
import time

# Crear el bridge
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",              # IP del PLC
    "nats://192.168.17.138:4222",  # Servidor NATS
    "plc.data"                     # Subject/topic NATS
)

# Iniciar
if bridge.start():
    print("✅ Bridge corriendo!")
    
    # Monitorear
    while bridge.is_running():
        time.sleep(5)
        print(f"📊 RX={bridge.get_received_count()}, "
              f"TX={bridge.get_published_count()}")
    
    # Detener
    bridge.stop()
```

**Ver más ejemplos en [`examples/`](examples/README.md)**

## 📋 Requisitos

**Sistema:**
- Linux (ARM64/x86_64)
- Python 3.7+
- git, cmake, make, g++, python3-venv (solo para compilar)

**Para desarrollo:** Ejecutar `./setup_project.sh` (crea venv automáticamente)

## 🛠️ Desarrollo

### Modificar Código C++

Para desarrollo iterativo sin regenerar el wheel:

```bash
# 1. Editar código
nano src/eip2nats/EIPtoNATSBridge.cpp

# 2. Opción A: Ejemplo C++ (recomendado para debugging)
python scripts/build_example_cpp.py
./example_cpp

# 3. Opción B: Compilar binding Python (test de integración)
python scripts/build_binding.py
python examples/example_python.py
```

**Ver guía completa:** [`DEVELOPMENT.md`](DEVELOPMENT.md)

**Incluye:**
- Workflow de desarrollo iterativo
- Debugging con VSCode (recomendado) y GDB
- Detección de memory leaks con Valgrind
- Testing C++ bridge vs Python binding
- Cuándo usar cada enfoque

### Crear Release

```bash
# Cuando estés satisfecho con los cambios
hatch build
```

### Clonar el repositorio

```bash
git clone https://github.com/yourusername/eip2nats.git
cd eip2nats
```

### Instalar Hatch

```bash
pip install hatch
```

### Compilar dependencias

```bash
# Compilar cada dependencia por separado
python scripts/build_nats.py
python scripts/build_eipscanner.py
python scripts/build_binding.py
```

O usando Hatch:

```bash
hatch run build-deps
```

### Crear el wheel

```bash
hatch build
```

Esto genera:
- `dist/eip2nats-1.0.0-*.whl` - Wheel con todas las dependencias incluidas
- `dist/eip2nats-1.0.0.tar.gz` - Source distribution

### Ejecutar tests

```bash
hatch run test
```

## 📦 Estructura del Proyecto

```
eip2nats/
├── pyproject.toml              # Configuración Hatch
├── README.md
├── src/
│   └── eip2nats/
│       ├── __init__.py         # Package Python
│       ├── bindings.cpp        # Bindings pybind11
│       ├── EIPtoNATSBridge.h   # Header C++
│       ├── EIPtoNATSBridge.cpp # Implementación C++
│       └── lib/                # Librerías compiladas (auto-generado)
│           ├── libnats.so
│           ├── libEIPScanner.so
│           └── eip2nats.*.so
├── scripts/
│   ├── build_config.py          # Configuración compartida
│   ├── build_nats.py            # Compila nats.c
│   ├── build_eipscanner.py      # Compila EIPScanner
│   └── build_binding.py         # Compila binding Python
├── examples/
│   ├── example_python.py        # Ejemplo Python
│   └── example_cpp.cpp          # Ejemplo C++ (debugging)
├── tests/
│   └── test_python.py           # Tests unitarios Python
└── build/
    └── dependencies/           # Clones de nats.c y EIPScanner
        ├── nats.c/
        └── EIPScanner/
```

## 🔧 Cómo Funciona

1. **Scripts de compilación** (`scripts/`):
   - `build_nats.py`: Clona y compila nats.c → `libnats.so`
   - `build_eipscanner.py`: Clona y compila EIPScanner → `libEIPScanner.so`
   - `build_binding.py`: Compila el binding Python → `eip2nats.*.so`
   - Todos copian los binarios a `src/eip2nats/lib/`

2. **`hatch build`**:
   - Ejecuta el build script automáticamente
   - Empaqueta `src/eip2nats/` completo (código + `.so`)
   - Crea el wheel con RPATH relativo (`$ORIGIN`)
   - El wheel contiene todo lo necesario

3. **`pip install`**:
   - Instala el wheel
   - Los `.so` quedan en el site-packages
   - Python carga las librerías automáticamente
   - ¡Funciona sin dependencias del sistema!

## 🎯 Ventajas de Este Enfoque

### ✅ Comparado con librerías del sistema:
- No requiere `sudo apt-get install`
- No hay conflictos de versiones
- Portabilidad entre sistemas

### ✅ Comparado con wheels normales:
- Incluye todas las dependencias C/C++
- Un solo archivo para instalar
- Funciona en sistemas sin compiladores

### ✅ Comparado con Docker:
- Más ligero (MBs vs GBs)
- Integración directa con Python
- No requiere privilegios de Docker

## 📊 API Reference

### Clase: `EIPtoNATSBridge`

```python
bridge = eip2nats.EIPtoNATSBridge(
    plc_address: str,
    nats_url: str,
    nats_subject: str,
    use_binary_format: bool = True
)
```

**Métodos:**
- `start() -> bool`: Inicia el bridge
- `stop() -> None`: Detiene el bridge
- `is_running() -> bool`: Estado del bridge
- `get_received_count() -> int`: Mensajes del PLC
- `get_published_count() -> int`: Mensajes a NATS

## 🐛 Troubleshooting

### Error: "cannot open shared object file"

Aunque el wheel incluye las librerías, verifica RPATH:

```bash
ldd $(python -c "import eip2nats; print(eip2nats.__file__.replace('__init__.py', 'lib/eip2nats.*.so'))")
```

Todas las dependencias deberían resolverse localmente.

### Recompilar en otro sistema

```bash
git clone <repo>
cd eip2nats
python scripts/build_nats.py
python scripts/build_eipscanner.py
python scripts/build_binding.py
hatch build
```

### Limpiar builds

```bash
rm -rf build/ dist/ src/eip2nats/lib/
```

## 📝 Changelog

### v1.0.0 (2024-02-10)
- Initial release
- Self-contained wheel con nats.c y EIPScanner
- Soporte para formato binario y JSON
- Thread-safe operations

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/amazing`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver LICENSE file

## 🙏 Créditos

- [nats.c](https://github.com/nats-io/nats.c) - Cliente NATS para C
- [EIPScanner](https://github.com/nimbuscontrols/EIPScanner) - Librería EtherNet/IP
- [pybind11](https://github.com/pybind/pybind11) - Python bindings

---

**Hecho con ❤️ para facilitar la integración industrial**
