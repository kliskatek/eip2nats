# 📦 Cómo Publicar eip2nats

Este documento explica cómo publicar el paquete `eip2nats` a PyPI u otros repositorios de paquetes Python.

## Prerequisitos

Asegúrate de tener el entorno configurado:

```bash
source venv/bin/activate
pip install twine hatch
```

## 🔨 Paso 1: Compilar y Construir el Wheel

Primero, asegúrate de que las dependencias están compiladas y el wheel está construido:

```bash
# Opción A: Usar el script completo
./setup_project.sh

# Opción B: Solo compilar y construir
python scripts/build_dependencies.py
python -m build --wheel
```

Esto generará un wheel en `dist/` con el formato:
```
dist/eip2nats-1.0.0-cp311-cp311-linux_aarch64.whl
```

## ✅ Paso 2: Verificar el Wheel

Antes de publicar, verifica que el wheel esté bien construido:

```bash
# Verificar con twine
twine check dist/*.whl

# Inspeccionar contenido
unzip -l dist/*.whl

# Probar instalación local
pip install dist/*.whl
python -c "import eip2nats; print(eip2nats.__version__)"
```

## 🚀 Paso 3: Publicar

### Opción A: Usar Twine (Estándar de Python)

```bash
# 1. Configurar credenciales de PyPI
# Crea ~/.pypirc con:
# [pypi]
# username = __token__
# password = pypi-AgEIcHlwaS5vcmc...

# 2. Publicar a TestPyPI primero (recomendado)
twine upload --repository testpypi dist/*.whl

# 3. Verificar en TestPyPI
pip install --index-url https://test.pypi.org/simple/ eip2nats

# 4. Si todo está bien, publicar a PyPI real
twine upload dist/*.whl
```

### Opción B: Usar Hatch

```bash
# Publicar a PyPI
hatch publish

# O a TestPyPI
hatch publish -r test
```

## 🔑 Configuración de Credenciales

### Para Twine

Crea `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

### Para Hatch

Hatch usa las mismas credenciales de `~/.pypirc` o variables de entorno:

```bash
export HATCH_INDEX_USER="__token__"
export HATCH_INDEX_AUTH="pypi-AgEIcHlwaS5vcmc..."
```

## 📝 Notas Importantes

### ⚠️ Wheels Específicos de Plataforma

Este paquete genera wheels **específicos de plataforma** porque incluye binarios compilados:

- `cp311-cp311-linux_aarch64` - CPython 3.11, Linux ARM64
- Solo funcionará en sistemas compatibles

Para publicar para otras plataformas, necesitas:

1. **Compilar en cada plataforma**:
   ```bash
   # En Linux x86_64
   ./setup_project.sh
   # Genera: eip2nats-1.0.0-cp311-cp311-linux_x86_64.whl

   # En macOS ARM64
   ./setup_project.sh
   # Genera: eip2nats-1.0.0-cp311-cp311-macosx_11_0_arm64.whl
   ```

2. **O usar CI/CD** (GitHub Actions, GitLab CI) con múltiples runners

### 🔄 Workflow Recomendado

```bash
# 1. Incrementar versión en pyproject.toml
vim pyproject.toml  # version = "1.0.1"

# 2. Limpiar builds anteriores
rm -rf dist/ build/ src/eip2nats.egg-info/

# 3. Recompilar todo
./setup_project.sh

# 4. Verificar
twine check dist/*.whl

# 5. Probar en TestPyPI
twine upload --repository testpypi dist/*.whl

# 6. Verificar instalación desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ eip2nats

# 7. Si todo OK, publicar a PyPI
twine upload dist/*.whl

# 8. Crear tag en git
git tag v1.0.1
git push origin v1.0.1
```

## 🌐 Publicar a Repositorios Privados

Para publicar a repositorios privados (JFrog Artifactory, Nexus, etc.):

```bash
twine upload --repository-url https://tu-repo.com/pypi/ dist/*.whl
```

O configura en `~/.pypirc`:

```ini
[distutils]
index-servers =
    interno

[interno]
repository = https://tu-repo.com/pypi/
username = tu_usuario
password = tu_password
```

```bash
twine upload -r interno dist/*.whl
```

## 🆘 Troubleshooting

### Error: "Invalid distribution file"

Asegúrate de que el wheel tenga el formato correcto:
```bash
ls dist/
# Debe ser: eip2nats-1.0.0-cp311-cp311-linux_aarch64.whl
# NO: eip2nats-1.0.0-py3-none-any.whl
```

### Error: "File already exists"

PyPI no permite resubir la misma versión:
```bash
# Incrementa la versión en pyproject.toml
version = "1.0.1"
```

### Error: "Repository not found"

Verifica las credenciales en `~/.pypirc` y que el token sea válido.

## 📚 Referencias

- [Twine Documentation](https://twine.readthedocs.io/)
- [Hatch Publishing](https://hatch.pypa.io/latest/publish/)
- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
