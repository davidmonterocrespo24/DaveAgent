# Guía: Crear Release y Publicar en PyPI

## Paso 1: Preparar el Proyecto

### 1.1 Verificar Versión

Actualmente tienes inconsistencias de versión:
- `pyproject.toml`: version = "1.010"
- `setup.py`: version = "1.1.0"

**Acción**: Decide la versión final. Recomiendo **v1.0.0** para el primer release.

### 1.2 Actualizar Archivos de Configuración

Necesitas actualizar:

1. **pyproject.toml** - cambiar version a "1.0.0"
2. **setup.py** - cambiar version a "1.0.0"
3. URLs del repositorio en setup.py (actualmente apuntan a URLs incorrectas)

---

## Paso 2: Crear Release en GitHub

### Opción A: Interfaz Web (Más Fácil)

1. Ve a: https://github.com/davidmonterocrespo24/DaveAgent
2. Haz clic en "Releases" (lado derecho)
3. Haz clic en "Create a new release"
4. Completa:
   - **Tag version**: `v1.0.0`
   - **Release title**: `CodeAgent v1.0.0 - First Stable Release`
   - **Description**: 
   ```markdown
   # CodeAgent v1.0.0 - First Stable Release
   
   AI-powered coding assistant with intelligent agent orchestration.
   
   ## Features
   - Global CLI command `daveagent`
   - 50+ integrated tools (Filesystem, Git, JSON, CSV, Web, Analysis, Memory)
   - Vector memory with ChromaDB
   - Specialized CodeSearcher agent
   - File mentions with @ for maximum priority
   - Interactive CLI with Rich formatting
   - AutoGen 0.4 agent framework
   
   ## Installation
   ```bash
   pip install daveagent-ai
   ```
   
   ## Documentation
   - Wiki: https://github.com/davidmonterocrespo24/DaveAgent/wiki
   - Quick Start: https://github.com/davidmonterocrespo24/DaveAgent/wiki/Quick-Start
   
   ## What's Changed
   - Initial stable release
   - Complete documentation
   - 50 tools implemented
   - Memory system with RAG
   - CLI interface
   ```
5. Marca "Set as the latest release"
6. Haz clic en "Publish release"

### Opción B: Desde Terminal

```bash
cd E:\AI\CodeAgent

# Crear tag
git tag -a v1.0.0 -m "CodeAgent v1.0.0 - First Stable Release"

# Push tag
git push origin v1.0.0

# Luego crear el release en GitHub web
```

---

## Paso 3: Publicar en PyPI

### 3.1 Instalar Herramientas

```bash
pip install --upgrade build twine
```

### 3.2 Crear Cuenta en PyPI

1. Ve a: https://pypi.org/account/register/
2. Crea una cuenta
3. Verifica tu email

### 3.3 Crear API Token

1. Ve a: https://pypi.org/manage/account/
2. Scroll hasta "API tokens"
3. Haz clic "Add API token"
4. Name: "DaveAgent Upload"
5. Scope: "Entire account" (para el primer upload)
6. Copia el token (empieza con `pypi-`)

### 3.4 Configurar Credenciales

Opción 1 - Archivo .pypirc (Recomendado):

Crea `C:\Users\David\.pypirc`:

```ini
[distutils]
index-servers =
    pypi

[pypi]
username = __token__
password = pypi-TU_TOKEN_AQUI
```

Opción 2 - Variable de Entorno:

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-TU_TOKEN_AQUI"
```

### 3.5 Construir el Paquete

```bash
cd E:\AI\CodeAgent

# Limpiar builds anteriores
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# Construir
python -m build
```

Esto creará:
- `dist/daveagent_ai-1.0.0-py3-none-any.whl`
- `dist/daveagent-ai-1.0.0.tar.gz`

### 3.6 Verificar el Paquete

```bash
# Verificar que el paquete está bien formado
twine check dist/*
```

Debe mostrar: "PASSED"

### 3.7 Publicar a PyPI

**IMPORTANTE**: Primero prueba en TestPyPI (opcional pero recomendado):

```bash
# TestPyPI (prueba)
twine upload --repository testpypi dist/*
```

Si todo funciona, publica a PyPI real:

```bash
# PyPI PRODUCCIÓN
twine upload dist/*
```

---

## Paso 4: Verificar Publicación

### 4.1 Verificar en PyPI

1. Ve a: https://pypi.org/project/daveagent-ai/
2. Deberías ver tu paquete publicado

### 4.2 Probar Instalación

En una nueva terminal:

```bash
# Crear entorno virtual de prueba
python -m venv test_env
test_env\Scripts\activate

# Instalar desde PyPI
pip install daveagent-ai

# Probar
daveagent --version
```

---

## Checklist Completo

### Antes del Release:
- [ ] Versión consistente en todos los archivos (1.0.0)
- [ ] README.md actualizado
- [ ] Wiki completada y publicada
- [ ] Todos los cambios commiteados
- [ ] Tests pasando (si los tienes)

### GitHub Release:
- [ ] Tag v1.0.0 creado
- [ ] Release notes escritas
- [ ] Release publicado

### PyPI:
- [ ] Cuenta PyPI creada
- [ ] API token generado
- [ ] Credenciales configuradas (.pypirc)
- [ ] Paquete construido (`python -m build`)
- [ ] Paquete verificado (`twine check dist/*`)
- [ ] Publicado a PyPI (`twine upload dist/*`)
- [ ] Instalación verificada

---

## Problemas Comunes

### "Package already exists"
Si el nombre ya existe en PyPI, necesitas cambiarlo en setup.py y pyproject.toml.
Prueba: `daveagent-ai`, `daveagent-cli`, `codeagent-ai`

### "Invalid credentials"
Verifica que el token esté correcto y tenga el prefijo `pypi-`

### "File already exists"
No puedes re-subir la misma versión. Incrementa la versión (ej: 1.0.1)

---

## Después de Publicar

1. **Actualiza README.md** con instrucción de instalación:
```markdown
## Installation

```bash
pip install daveagent-ai
```
```

2. **Actualiza wiki Installation.md**:
```markdown
### Method 1: Install from PyPI (Recommended)

```bash
pip install daevagent-ai
```
```

3. **Anuncia en Discord** el release

---

## Siguiente Versión

Para futuras versiones:

1. Incrementa versión en pyproject.toml y setup.py
2. Actualiza CHANGELOG (créalo si no existe)
3. Sigue los pasos 2-4 de esta guía

---

**¿Necesitas ayuda?** Pregunta antes de ejecutar cada paso.
