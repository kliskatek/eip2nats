# 🚀 Quick Start Guide - eip2nats

Guía rápida para empezar a usar eip2nats desde cero.

## Para Usuarios (Instalar wheel pre-compilado)

### 1. Crear entorno virtual

```bash
# En Raspberry Pi, SIEMPRE usa entorno virtual
python3 -m venv eip2nats_env
source eip2nats_env/bin/activate
```

### 2. Instalar el wheel

```bash
pip install eip2nats-1.0.0-*.whl
```

### 3. Usar

```python
import eip2nats

bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data"
)

bridge.start()
# ... tu código ...
bridge.stop()
```

### 4. Desactivar cuando termines

```bash
deactivate
```

---

## Para Desarrolladores (Compilar desde fuente)

### 1. Requisitos

```bash
# Ubuntu/Debian/Raspberry Pi OS
sudo apt-get update
sudo apt-get install -y \
    git \
    cmake \
    make \
    g++ \
    python3-dev \
    python3-venv
```

### 2. Clonar el proyecto

```bash
git clone https://github.com/yourrepo/eip2nats.git
cd eip2nats
```

### 3. Setup completo (TODO AUTOMÁTICO)

```bash
./setup_project.sh
```

Esto:
- ✅ Crea un entorno virtual en `venv/`
- ✅ Instala Hatch y pybind11 en el venv
- ✅ Descarga y compila nats.c
- ✅ Descarga y compila EIPScanner  
- ✅ Compila el binding Python
- ✅ Crea el wheel
- ✅ Instala el wheel en el venv

**Tiempo estimado:** 3-5 minutos en Raspberry Pi 5

### 4. Usar el proyecto

```bash
# El script setup_project.sh deja el venv activado
# Si cerraste la terminal, reactiva con:
source venv/bin/activate

# Ejecutar ejemplo
python example.py

# Tu código
python tu_script.py

# Desactivar
deactivate
```

---

## Workflow Completo de Desarrollo

### Setup inicial

```bash
git clone <repo>
cd eip2nats
pip install hatch
```

### Desarrollar

```bash
# Compilar dependencias (solo primera vez)
hatch run build-deps

# Editar código en src/eip2nats/

# Recompilar solo el binding Python
cd build/dependencies
g++ -O3 -Wall -shared -std=c++17 -fPIC \
    -I$(python -c "import pybind11; print(pybind11.get_include())") \
    -I../../src/eip2nats \
    -Inats.c/src \
    -IEIPScanner/src \
    ../../src/eip2nats/bindings.cpp \
    ../../src/eip2nats/EIPtoNATSBridge.cpp \
    -o ../../src/eip2nats/lib/eip2nats$(python3-config --extension-suffix) \
    -L../../src/eip2nats/lib \
    -lnats -lEIPScanner -lpthread \
    -Wl,-rpath,'$ORIGIN'
```

### Probar cambios

```bash
# Test unitarios
hatch run test

# Test manual
python -c "import sys; sys.path.insert(0, 'src'); import eip2nats; ..."
```

### Hacer release

```bash
# 1. Actualizar versión en pyproject.toml
# 2. Build
hatch build

# 3. Tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# 4. Distribuir wheel
# Upload a GitHub releases, PyPI, etc.
```

---

## Comandos Útiles

```bash
# Limpiar todo
rm -rf build/ dist/ src/eip2nats/lib/

# Ver librerías incluidas en el wheel
unzip -l dist/eip2nats-*.whl | grep .so

# Verificar dependencias de un .so
ldd src/eip2nats/lib/eip2nats*.so

# Ejecutar tests
hatch run test

# Ejecutar tests con coverage
hatch run cov

# Crear solo source distribution
hatch build --target sdist

# Crear solo wheel
hatch build --target wheel
```

---

## Troubleshooting

### Error: "CMake not found"

```bash
sudo apt-get install cmake
```

### Error: "g++ not found"

```bash
sudo apt-get install g++ build-essential
```

### Error: "pybind11 not found"

```bash
pip install pybind11
```

### Recompilar solo una dependencia

```bash
cd build/dependencies

# Solo nats.c
cd nats.c/build && make clean && cmake .. && make -j4

# Solo EIPScanner
cd EIPScanner/build && make clean && cmake .. && make -j4
```

### Ver logs de compilación

```bash
python scripts/build_dependencies.py 2>&1 | tee build.log
```

---

## FAQ

**P: ¿Puedo usar el wheel en otra Raspberry Pi?**
R: Sí, siempre que tenga la misma arquitectura (ARM64) y Python 3.11.

**P: ¿Funciona en x86_64?**
R: Debes recompilar en una máquina x86_64. El proceso es el mismo.

**P: ¿Necesito instalar nats.c o EIPScanner?**
R: No, el wheel incluye todo.

**P: ¿Puedo modificar el código C++?**
R: Sí, edita `src/eip2nats/*.cpp` y ejecuta `hatch run build-deps`.

**P: ¿Cómo actualizo solo el binding Python sin recompilar las deps?**
R: Ver sección "Desarrollar" arriba.

---

¡Listo para empezar! 🚀
