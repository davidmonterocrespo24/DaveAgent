# 📦 Guía de Instalación de DaveAgent

## 🎯 Resumen

Esta guía te mostrará cómo instalar DaveAgent como un paquete de Python para poder usarlo desde **cualquier directorio** ejecutando simplemente `daveagent`.

---

## 🚀 Instalación

### Opción 1: Instalación en Modo Desarrollo (Recomendado)

Esta opción te permite editar el código y que los cambios se reflejen inmediatamente:

```bash
# 1. Navega al directorio del proyecto
cd E:\AI\DaveAgent

# 2. Instala en modo desarrollo (editable)
pip install -e .

# 3. ¡Listo! Ahora puedes usar 'daveagent' desde cualquier directorio
```

### Opción 2: Instalación Normal

Esta opción instala DaveAgent como un paquete regular:

```bash
# 1. Navega al directorio del proyecto
cd E:\AI\DaveAgent

# 2. Instala el paquete
pip install .

# 3. ¡Listo!
```

### Opción 3: Instalación con Dependencias de Desarrollo

Si quieres contribuir al proyecto o ejecutar tests:

```bash
# Instala con dependencias de desarrollo
pip install -e ".[dev]"
```

---

## ✅ Verificar la Instalación

Después de instalar, verifica que todo funcione:

```bash
# Ver la versión
daveagent --version

# Ver la ayuda
daveagent --help

# Iniciar DaveAgent
daveagent
```

Deberías ver algo como:

```
╔══════════════════════════════════════════════════════════════╗
║                    🤖 DaveAgent CLI                          ║
╚══════════════════════════════════════════════════════════════╝

Version: 1.0.0
Python: 3.12.0
Platform: win32

Built with ❤️ using AutoGen 0.4
```

---

## 🎮 Cómo Usar

### Usar en Cualquier Directorio

Una vez instalado, puedes usar DaveAgent desde **cualquier directorio**:

```bash
# Ejemplo 1: Trabajar en un proyecto web
cd C:\Users\tuusuario\proyectos\mi-web
daveagent

# DaveAgent trabajará en C:\Users\tuusuario\proyectos\mi-web
```

```bash
# Ejemplo 2: Trabajar en un proyecto de Python
cd D:\Python\mi-proyecto
daveagent --debug

# DaveAgent trabajará en D:\Python\mi-proyecto con logs detallados
```

### Directorio de Trabajo

El directorio de trabajo de DaveAgent es **el directorio actual** donde ejecutas el comando `daveagent`.

Por ejemplo:

```bash
# Si estás en:
cd C:\Users\tuusuario\proyectos\mi-app

# Y ejecutas:
daveagent

# DaveAgent verá y trabajará con los archivos en:
# C:\Users\tuusuario\proyectos\mi-app
```

---

## 🛠️ Opciones de Línea de Comandos

```bash
# Iniciar normalmente
daveagent

# Iniciar con modo debug (logs detallados)
daveagent --debug
# o
daveagent -d

# Ver la versión
daveagent --version
# o
daveagent -v

# Ver la ayuda
daveagent --help
# o
daveagent -h
```

---

## 📂 Estructura del Paquete Instalado

Cuando instalas DaveAgent, se crea esta estructura:

```
Python/Lib/site-packages/
└── daveagent-cli/
    ├── src/
    │   ├── agents/
    │   ├── config/
    │   ├── interfaces/
    │   ├── managers/
    │   ├── tools/
    │   ├── utils/
    │   └── cli.py          # ← Punto de entrada del comando 'daveagent'
    └── main.py
```

El comando `daveagent` ejecuta el archivo `src/cli.py`, que a su vez llama a `main.py`.

---

## 🔄 Actualizar la Instalación

Si haces cambios en el código y quieres actualizarlo:

### Si instalaste con `-e` (modo desarrollo):
```bash
# ✅ No necesitas hacer nada
# Los cambios se reflejan automáticamente
```

### Si instalaste sin `-e`:
```bash
# 1. Navega al directorio del proyecto
cd E:\AI\DaveAgent

# 2. Reinstala
pip install --upgrade --force-reinstall .
```

---

## 🗑️ Desinstalar

Si quieres desinstalar DaveAgent:

```bash
pip uninstall daveagent-cli
```

---

## 🐛 Solución de Problemas

### Error: "command not found: daveagent"

**Causa**: El directorio de scripts de Python no está en tu PATH.

**Solución**:

1. **En Windows**:
   ```powershell
   # Verifica dónde está instalado Python
   python -c "import sys; print(sys.executable)"

   # Agrega esta carpeta\Scripts a tu PATH
   # Por ejemplo: C:\Python312\Scripts
   ```

2. **Agrega manualmente al PATH** (Windows):
   - Busca "Editar las variables de entorno del sistema"
   - Editar → Variables de entorno
   - En "Path", agrega: `C:\Python312\Scripts` (o donde esté tu Python)
   - Reinicia la terminal

### Error: "ModuleNotFoundError: No module named 'src'"

**Causa**: El paquete no se instaló correctamente.

**Solución**:
```bash
# Desinstala
pip uninstall daveagent-cli

# Reinstala en modo desarrollo
cd E:\AI\DaveAgent
pip install -e .
```

### Error: "Permission denied"

**Causa**: No tienes permisos para instalar paquetes.

**Solución**:
```bash
# Opción 1: Instala solo para tu usuario
pip install --user -e .

# Opción 2: Usa un entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate
pip install -e .
```

---

## 🌟 Ventajas de Instalar como Paquete

### ✅ Antes (Sin Instalar)
```bash
# Tenías que hacer esto cada vez:
cd E:\AI\DaveAgent
python main.py

# Y solo funcionaba en ese directorio
```

### ✅ Después (Instalado)
```bash
# Desde CUALQUIER directorio:
cd C:\Users\tuusuario\mi-proyecto
daveagent

# ¡Y DaveAgent trabaja en ese directorio!
```

### Beneficios:
- ✅ Usa `daveagent` desde cualquier ubicación
- ✅ El directorio de trabajo es donde ejecutes el comando
- ✅ No necesitas recordar la ruta del proyecto
- ✅ Integración perfecta con tu flujo de trabajo
- ✅ Se comporta como cualquier otra herramienta CLI (git, npm, etc.)

---

## 📝 Ejemplo de Uso Completo

```bash
# 1. Instalar DaveAgent (solo una vez)
cd E:\AI\DaveAgent
pip install -e .

# 2. Ir a tu proyecto
cd C:\Users\tuusuario\proyectos\mi-web

# 3. Iniciar DaveAgent
daveagent --debug

# 4. Dentro de DaveAgent:
Tu: crear un archivo utils.js con una función para validar emails

# DaveAgent creará el archivo en:
# C:\Users\tuusuario\proyectos\mi-web\utils.js
```

---

## 🔧 Desarrollo y Contribución

Si quieres contribuir al proyecto:

```bash
# 1. Clona el repositorio
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd daveagent

# 2. Instala en modo desarrollo con dependencias de desarrollo
pip install -e ".[dev]"

# 3. Ejecuta los tests
pytest

# 4. Formatea el código
black src/

# 5. Verifica tipos
mypy src/
```

---

## 📦 Crear un Paquete Distribuible (Opcional)

Si quieres crear un paquete `.whl` o `.tar.gz` para distribuir:

```bash
# 1. Instala build
pip install build

# 2. Crea el paquete
python -m build

# Esto creará archivos en:
# dist/daveagent_cli-1.0.0-py3-none-any.whl
# dist/daveagent-cli-1.0.0.tar.gz
```

Luego puedes instalar ese paquete con:

```bash
pip install dist/daveagent_cli-1.0.0-py3-none-any.whl
```

---

## 🎉 ¡Listo!

Ahora tienes DaveAgent instalado como un paquete de Python y puedes usarlo desde cualquier directorio ejecutando simplemente:

```bash
daveagent
```

¿Tienes preguntas? Consulta la [documentación completa](https://daveagent.readthedocs.io) o abre un [issue en GitHub](https://github.com/davidmonterocrespo24/DaveAgent/issues).
