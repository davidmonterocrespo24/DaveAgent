# 🔨 Scripts de Compilación e Instalación

Este directorio contiene scripts automatizados para compilar e instalar DaveAgent fácilmente.

## 📋 Scripts Disponibles

### Windows
- **`build_and_install.bat`** - Script para Windows (CMD/PowerShell)

### Linux/Mac
- **`build_and_install.sh`** - Script para Linux/Mac (Bash)

## 🚀 Uso Rápido

### En Windows

```cmd
# Opción 1: Doble clic en el archivo
build_and_install.bat

# Opción 2: Desde CMD
cd E:\AI\CodeAgent
build_and_install.bat

# Opción 3: Desde PowerShell
cd E:\AI\CodeAgent
.\build_and_install.bat
```

### En Linux/Mac

```bash
# Dar permisos de ejecución (solo primera vez)
chmod +x build_and_install.sh

# Ejecutar el script
./build_and_install.sh
```

## 📝 ¿Qué hace el script?

El script automatiza los siguientes pasos:

### 1️⃣ **Limpieza** 🧹
- Elimina directorios `build/` y `dist/` anteriores
- Elimina archivos `.egg-info` antiguos
- Prepara un entorno limpio para la compilación

### 2️⃣ **Verificación de Dependencias** ✅
- Verifica que `build` esté instalado
- Si no está instalado, lo instala automáticamente

### 3️⃣ **Compilación** 🔨
- Ejecuta `python -m build`
- Genera dos archivos en `dist/`:
  - **`.whl`** (wheel) - Instalación rápida
  - **`.tar.gz`** (source) - Distribución de código fuente

### 4️⃣ **Listado de Archivos** 📦
- Muestra los archivos compilados
- Verifica que la compilación fue exitosa

### 5️⃣ **Instalación** 📥
- Instala el paquete usando `pip install --force-reinstall`
- Sobrescribe versiones anteriores si existen

### 6️⃣ **Verificación** ✔️
- Verifica que `daveagent-cli` esté instalado
- Muestra información del paquete (versión, ubicación)
- Prueba el comando `daveagent --version`

## 🎯 Salida Esperada

```
========================================
 DaveAgent - Build and Install Script
========================================

Paso 1: Limpiando builds anteriores...
✓ Limpieza completada

Paso 2: Verificando dependencias...
✓ build ya está instalado

Paso 3: Compilando el paquete...
✓ Compilación exitosa

Paso 4: Mostrando archivos compilados...
-rw-r--r-- 1 user user 173K daveagent_cli-1.10.tar.gz
-rw-r--r-- 1 user user 122K daveagent_cli-1.10-py3-none-any.whl

Paso 5: Instalando el paquete...
✓ Instalación completada

Paso 6: Verificando la instalación...
✓ daveagent-cli está instalado
✓ Comando 'daveagent' está disponible

========================================
  ✓ PROCESO COMPLETADO EXITOSAMENTE
========================================
```

## 📂 Estructura de Archivos Generados

Después de ejecutar el script, tendrás:

```
CodeAgent/
├── build/                          # Archivos temporales de compilación
├── dist/                           # Paquetes compilados
│   ├── daveagent_cli-1.10.tar.gz          # Source distribution
│   └── daveagent_cli-1.10-py3-none-any.whl # Wheel (binary)
├── daveagent_cli.egg-info/         # Metadata del paquete
└── build_and_install.bat/.sh       # Scripts de compilación
```

## ⚙️ Comandos Disponibles Después de la Instalación

Una vez instalado, puedes usar DaveAgent de 3 formas:

### 1. Comando CLI Global
```bash
daveagent
daveagent --help
daveagent --version
```

### 2. Como Módulo Python
```bash
python -m src.cli
python -m src.cli --help
```

### 3. Ejecutando main.py Directamente
```bash
python main.py
```

## 🛠️ Solución de Problemas

### Problema: "daveagent command not found"

**Solución:**
- Windows: Asegúrate de que Python Scripts esté en tu PATH
- Linux/Mac: Usa `python -m src.cli` en su lugar

### Problema: "ModuleNotFoundError"

**Solución:**
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# O ejecutar el script nuevamente
./build_and_install.sh  # Linux/Mac
build_and_install.bat   # Windows
```

### Problema: "Permission denied" (Linux/Mac)

**Solución:**
```bash
# Dar permisos de ejecución
chmod +x build_and_install.sh

# O ejecutar con bash
bash build_and_install.sh
```

### Problema: Errores de compilación

**Solución:**
```bash
# Limpiar cache de pip
pip cache purge

# Actualizar herramientas de build
pip install --upgrade pip setuptools wheel build

# Ejecutar script nuevamente
```

## 🔄 Recompilar Después de Cambios

Cada vez que hagas cambios en el código y quieras probar la nueva versión:

```bash
# Windows
build_and_install.bat

# Linux/Mac
./build_and_install.sh
```

El script automáticamente:
1. Limpia compilaciones anteriores
2. Recompila con los cambios nuevos
3. Reinstala el paquete actualizado

## 📦 Distribución del Paquete

Los archivos en `dist/` pueden ser:

### Compartir localmente
```bash
# Copiar el archivo .whl a otro sistema
pip install daveagent_cli-1.10-py3-none-any.whl
```

### Subir a repositorio privado
```bash
# Usar twine para subir a un servidor privado
pip install twine
twine upload --repository-url https://tu-servidor dist/*
```

### Publicar en PyPI (cuando estés listo)
```bash
# Crear cuenta en https://pypi.org
# Configurar ~/.pypirc
twine upload dist/*
```

## 📋 Pasos Manuales (si prefieres hacerlo paso a paso)

Si prefieres ejecutar los comandos manualmente en lugar de usar el script:

```bash
# 1. Limpiar
rm -rf build dist *.egg-info

# 2. Instalar build
pip install build

# 3. Compilar
python -m build

# 4. Instalar
pip install dist/*.whl --force-reinstall

# 5. Verificar
pip show daveagent-cli
daveagent --version
```

## 🎨 Personalización del Script

Puedes modificar los scripts para:

- **Cambiar la versión**: Edita `setup.py` y `pyproject.toml`
- **Añadir tests**: Agrega `pytest` antes de la compilación
- **Generar documentación**: Añade generación de docs al proceso
- **Publicación automática**: Integra `twine upload` al final

## 🔗 Enlaces Útiles

- [Python Packaging Guide](https://packaging.python.org/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [build Documentation](https://build.pypa.io/)
- [twine Documentation](https://twine.readthedocs.io/)

## 📞 Soporte

Si encuentras problemas:

1. Revisa la sección de **Solución de Problemas**
2. Verifica que tienes Python 3.10+ instalado
3. Asegúrate de tener permisos de escritura en el directorio
4. Intenta ejecutar los comandos manualmente para identificar el paso que falla

---

**¡Feliz compilación!** 🎉

_Última actualización: 2025-12-04_
