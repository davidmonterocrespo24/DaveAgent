# 🚀 Inicio Rápido - Publicar en PyPI en 10 Minutos

Guía ultra rápida para publicar CodeAgent en PyPI.

## Paso 1: Crear Cuentas (5 minutos)

### 1.1 TestPyPI (para pruebas)
1. Ve a: https://test.pypi.org/account/register/
2. Completa el formulario
3. Verifica tu email

### 1.2 PyPI (producción)
1. Ve a: https://pypi.org/account/register/
2. Usa el **mismo email** que en TestPyPI
3. Verifica tu email

### 1.3 Habilitar 2FA en ambas
1. Descarga Google Authenticator o Authy en tu teléfono
2. En PyPI: Account Settings → Two-factor authentication
3. Escanea el código QR
4. **Guarda los códigos de recuperación**
5. Repite para TestPyPI

### 1.4 Crear API Tokens

**TestPyPI**:
1. https://test.pypi.org/manage/account/token/
2. "Add API token"
3. Nombre: `codeagent-upload`
4. Scope: "Entire account"
5. **COPIA EL TOKEN** (empieza con `pypi-`) - ¡solo se muestra una vez!
6. Guárdalo en un archivo temporal

**PyPI**:
1. https://pypi.org/manage/account/token/
2. Repite el proceso
3. **COPIA Y GUARDA ESTE TOKEN TAMBIÉN**

## Paso 2: Instalar Herramientas (1 minuto)

En tu terminal:

```bash
cd E:\AI\CodeAgent

# Opción 1: Script automático (Windows)
install_publish_tools.bat

# Opción 2: Manual
pip install --upgrade build twine
```

## Paso 3: Verificar Configuración (30 segundos)

```bash
# Verificar que las herramientas están instaladas
python -m build --version
python -m twine --version
```

## Paso 4: Publicar en TestPyPI (2 minutos)

```bash
# Usar el script automatizado
python publish.py test
```

Cuando te pida credenciales:
- **Username**: `__token__`
- **Password**: Pega tu token de **TestPyPI**

## Paso 5: Probar Instalación (1 minuto)

En una nueva terminal:

```bash
# Crear entorno de prueba
cd C:\Temp
python -m venv test_codeagent
test_codeagent\Scripts\activate

# Instalar desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ codeagent-ai

# Probar
codeagent --version
codeagent --help
```

Si funciona, ¡continúa! Si no, revisa [PUBLICAR_PYPI.md](PUBLICAR_PYPI.md).

## Paso 6: Publicar en PyPI Real (1 minuto)

**⚠️ IMPORTANTE**: Una vez publicado, NO puedes borrar esta versión.

```bash
# Volver al proyecto
cd E:\AI\CodeAgent

# Publicar en PyPI
python publish.py prod
```

Cuando te pida credenciales:
- **Username**: `__token__`
- **Password**: Pega tu token de **PyPI** (producción)

Confirmación:
- Escribe: `SI` (en mayúsculas)

## ✅ ¡Listo!

Tu paquete ahora está publicado en: https://pypi.org/project/codeagent-ai/

Cualquiera puede instalarlo:

```bash
pip install codeagent-ai
```

---

## 📊 Siguientes Pasos

### Ver estadísticas
- PyPI: https://pypi.org/project/codeagent-ai/
- Descargas: https://pypistats.org/packages/codeagent-ai

### Publicar actualizaciones

1. Edita `setup.py`:
   ```python
   version="1.2.0",  # Incrementar
   ```

2. Actualiza `CHANGELOG.md`:
   ```markdown
   ## [1.2.0] - 2025-11-03
   ### Added
   - Nueva funcionalidad
   ```

3. Publica:
   ```bash
   python publish.py test  # Primero probar
   python publish.py prod  # Luego producción
   ```

---

## 🆘 Problemas Comunes

### "Invalid credentials"
- Verifica que username sea `__token__` (con doble guión bajo)
- Verifica que estés usando el token correcto (TestPyPI vs PyPI)

### "Package already exists"
- Ya publicaste esta versión
- Incrementa el número de versión en `setup.py`

### "Command not found: codeagent"
- Reinicia tu terminal
- O ejecuta: `pip install --force-reinstall codeagent-ai`

---

## 📚 Documentación Completa

Para más detalles: [PUBLICAR_PYPI.md](PUBLICAR_PYPI.md)
