# 📦 Guía para Publicar CodeAgent en PyPI

Esta guía te llevará paso a paso para publicar CodeAgent en PyPI y que cualquier persona pueda instalarlo con:

```bash
pip install codeagent-ai
```

## 📋 Prerrequisitos

### 1. Crear cuentas en PyPI

Necesitas crear cuentas en:

1. **TestPyPI** (para pruebas): https://test.pypi.org/account/register/
2. **PyPI** (producción): https://pypi.org/account/register/

**Importante**: Usa el mismo email para ambas cuentas.

### 2. Verificar email

Revisa tu correo y verifica ambas cuentas haciendo clic en los enlaces de confirmación.

### 3. Habilitar 2FA (Two-Factor Authentication)

PyPI requiere 2FA para publicar paquetes:

1. Ve a tu cuenta en PyPI → Account Settings → Two-factor authentication
2. Configura con una app como Google Authenticator o Authy
3. Guarda los códigos de recuperación en un lugar seguro

### 4. Crear API Tokens

#### Para TestPyPI:
1. Ve a https://test.pypi.org/manage/account/token/
2. Clic en "Add API token"
3. Nombre: `codeagent-upload`
4. Scope: "Entire account" (o específico del proyecto después de la primera subida)
5. **Copia el token** (empieza con `pypi-`) - solo se muestra una vez

#### Para PyPI:
1. Ve a https://pypi.org/manage/account/token/
2. Repite el mismo proceso
3. Guarda este token también

## 🛠️ Instalación de Herramientas

Instala las herramientas necesarias para construir y publicar:

```bash
pip install --upgrade build twine
```

**Herramientas**:
- `build`: Construye el paquete (wheel y source distribution)
- `twine`: Sube el paquete a PyPI de forma segura

## 📁 Preparar el Proyecto

### 1. Limpiar builds anteriores

```bash
cd E:\AI\CodeAgent

# Eliminar builds anteriores si existen
rmdir /s /q dist build src\codeagent_ai.egg-info 2>nul
```

En Linux/Mac:
```bash
rm -rf dist/ build/ *.egg-info src/*.egg-info
```

### 2. Verificar estructura del proyecto

Asegúrate de que tienes estos archivos:

```
CodeAgent/
├── setup.py          ✓ Configuración del paquete
├── pyproject.toml    ✓ Build system moderno
├── MANIFEST.in       ✓ Archivos a incluir
├── README.md         ✓ Documentación principal
├── LICENSE           ✓ Licencia MIT
├── CHANGELOG.md      ✓ Historial de versiones
├── src/
│   ├── __init__.py
│   ├── cli.py        ✓ Punto de entrada
│   ├── agents/
│   ├── tools/
│   ├── config/
│   └── ...
└── main.py
```

### 3. Actualizar información en setup.py

**IMPORTANTE**: Antes de publicar, actualiza en `setup.py`:

```python
name="codeagent-ai",  # Verifica que este nombre esté disponible en PyPI
version="1.1.0",      # Versión actual
url="https://github.com/TU_USUARIO/codeagent",  # Tu repositorio real
```

Para verificar si el nombre está disponible:
```bash
pip search codeagent-ai
# O visita: https://pypi.org/project/codeagent-ai/
```

## 🏗️ Construir el Paquete

### 1. Construir distribuciones

```bash
python -m build
```

Esto creará en el directorio `dist/`:
- `codeagent_ai-1.1.0-py3-none-any.whl` (wheel - instalación rápida)
- `codeagent_ai-1.1.0.tar.gz` (source distribution)

### 2. Verificar el contenido del paquete

```bash
# Ver contenido del wheel
python -m zipfile -l dist/codeagent_ai-1.1.0-py3-none-any.whl

# Verificar con twine
python -m twine check dist/*
```

Deberías ver:
```
Checking dist/codeagent_ai-1.1.0-py3-none-any.whl: PASSED
Checking dist/codeagent_ai-1.1.0.tar.gz: PASSED
```

## 🧪 Publicar en TestPyPI (Pruebas)

**Siempre prueba primero en TestPyPI antes de publicar en PyPI real.**

### 1. Subir a TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

Te pedirá:
- **Username**: `__token__`
- **Password**: Tu token de TestPyPI (que copiaste antes)

### 2. Verificar en TestPyPI

Ve a: https://test.pypi.org/project/codeagent-ai/

Deberías ver tu paquete publicado.

### 3. Probar instalación desde TestPyPI

En un **nuevo virtualenv** o directorio diferente:

```bash
# Crear entorno de prueba
cd C:\Temp
python -m venv test_env
test_env\Scripts\activate

# Instalar desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ codeagent-ai

# Probar que funciona
codeagent --version
codeagent --help
```

**Nota**: Usamos `--extra-index-url https://pypi.org/simple/` para que las dependencias (autogen, etc.) se instalen desde PyPI real.

### 4. Probar funcionalidad

```bash
# En cualquier directorio
cd C:\Temp\mi_proyecto
codeagent

# Probar comandos
Tu: /help
Tu: git status
Tu: /exit
```

Si todo funciona correctamente, ¡estás listo para publicar en PyPI real! 🎉

## 🚀 Publicar en PyPI (Producción)

**⚠️ ADVERTENCIA**: Una vez publicado, NO puedes eliminar o resubir la misma versión. Asegúrate de que todo funciona en TestPyPI primero.

### 1. Verificación final

- ✅ Probado en TestPyPI
- ✅ Versión correcta en `setup.py`
- ✅ README.md actualizado
- ✅ CHANGELOG.md actualizado
- ✅ LICENSE incluido
- ✅ Todas las funcionalidades probadas

### 2. Subir a PyPI

```bash
python -m twine upload dist/*
```

Te pedirá:
- **Username**: `__token__`
- **Password**: Tu token de PyPI (producción)

### 3. ¡Publicado! 🎊

Tu paquete ahora está disponible en: https://pypi.org/project/codeagent-ai/

Cualquier persona puede instalarlo con:

```bash
pip install codeagent-ai
```

## 📦 Después de la Primera Publicación

### Crear tokens específicos del proyecto

Ahora que tu paquete existe, puedes crear tokens más seguros:

1. Ve a https://pypi.org/manage/project/codeagent-ai/settings/
2. Crea un nuevo token con scope "Project: codeagent-ai"
3. Usa este token en el futuro (más seguro que "Entire account")

## 🔄 Publicar Actualizaciones

Cuando quieras publicar una nueva versión:

### 1. Actualizar versión

En `setup.py`:
```python
version="1.2.0",  # Incrementar versión
```

En `CHANGELOG.md`:
```markdown
## [1.2.0] - 2025-11-02

### Added
- Nueva funcionalidad X
- Mejora Y

### Fixed
- Bug Z corregido
```

### 2. Limpiar y reconstruir

```bash
# Limpiar builds anteriores
rmdir /s /q dist build src\codeagent_ai.egg-info

# Construir nueva versión
python -m build

# Verificar
python -m twine check dist/*
```

### 3. Publicar actualización

```bash
# Primero en TestPyPI
python -m twine upload --repository testpypi dist/*

# Si todo OK, a PyPI
python -m twine upload dist/*
```

## 📊 Estadísticas y Mantenimiento

### Ver estadísticas de descargas

- PyPI Stats: https://pypistats.org/packages/codeagent-ai
- Biblioteca PEP 381: https://pypi.org/project/codeagent-ai/#data

### Monitorear issues

Si pusiste un repositorio de GitHub:
- Revisa issues: https://github.com/TU_USUARIO/codeagent/issues
- Acepta pull requests de la comunidad

## 🔐 Seguridad

### Archivo .pypirc (Opcional)

Puedes crear `~/.pypirc` para no ingresar tokens cada vez:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-TU_TOKEN_AQUI

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-TU_TOKEN_TEST_AQUI
```

**⚠️ IMPORTANTE**:
- **NO** incluyas este archivo en Git
- Permisos: `chmod 600 ~/.pypirc` (solo tú puedes leerlo)
- Guarda backups de tus tokens en un password manager

## 🐛 Solución de Problemas

### Error: "The user 'xyz' isn't allowed to upload"

**Solución**: Verifica que estás usando `__token__` como username, no tu nombre de usuario.

### Error: "File already exists"

**Solución**: Ya publicaste esta versión. Incrementa el número de versión en `setup.py`.

### Error: "Invalid distribution"

**Solución**:
```bash
python -m twine check dist/*
```
Revisa los errores reportados.

### Dependencias no se instalan

**Solución**: Verifica `install_requires` en `setup.py`. Todas las dependencias deben estar en PyPI.

### No se encuentra el comando `codeagent`

**Solución**: Verifica `entry_points` en `setup.py`:
```python
entry_points={
    'console_scripts': [
        'codeagent=src.cli:main',
    ],
},
```

## 📝 Checklist Completo

Antes de publicar:

- [ ] Cuenta en PyPI creada y verificada
- [ ] 2FA habilitado
- [ ] API token generado
- [ ] `setup.py` actualizado con info correcta
- [ ] Versión incrementada
- [ ] README.md completo y actualizado
- [ ] CHANGELOG.md actualizado
- [ ] LICENSE incluido
- [ ] `python -m build` ejecutado sin errores
- [ ] `twine check dist/*` pasa
- [ ] Probado en TestPyPI
- [ ] Instalación desde TestPyPI funciona
- [ ] Todas las funcionalidades probadas
- [ ] Publicado en PyPI
- [ ] Verificado en https://pypi.org/project/codeagent-ai/
- [ ] Instalación con `pip install codeagent-ai` funciona

## 🎓 Recursos Adicionales

- **Documentación oficial de PyPI**: https://packaging.python.org/tutorials/packaging-projects/
- **Guía de Twine**: https://twine.readthedocs.io/
- **PEP 517 (Build system)**: https://peps.python.org/pep-0517/
- **Python Packaging Guide**: https://packaging.python.org/

## 🎉 ¡Felicidades!

Una vez publicado, tu paquete estará disponible para millones de desarrolladores Python en todo el mundo.

Comparte tu paquete:
```bash
pip install codeagent-ai
```

🌟 No olvides agregar un badge en tu README:

```markdown
[![PyPI version](https://badge.fury.io/py/codeagent-ai.svg)](https://pypi.org/project/codeagent-ai/)
[![Downloads](https://pepy.tech/badge/codeagent-ai)](https://pepy.tech/project/codeagent-ai)
```

---

**¿Problemas?** Abre un issue en GitHub o revisa la documentación oficial de PyPI.
