# 📦 Instalación de CodeAgent

Esta guía te llevará a través del proceso completo de instalación de CodeAgent en tu sistema.

## 📋 Requisitos Previos

### Requisitos del Sistema

- **Python**: 3.10 o superior
- **pip**: Gestor de paquetes de Python
- **Git**: Para clonar el repositorio (opcional si descargas el ZIP)
- **Sistema Operativo**: Windows, Linux, macOS

### Verificar Python

```bash
python --version
# Debe mostrar: Python 3.10.x o superior

pip --version
# Debe mostrar la versión de pip
```

Si no tienes Python 3.10+, descárgalo desde [python.org](https://www.python.org/downloads/)

---

## 🚀 Método 1: Instalación desde Código Fuente (Recomendado)

### Paso 1: Clonar el Repositorio

```bash
# Opción A: Clonar con HTTPS
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Opción B: Clonar con SSH
git clone git@github.com:davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Opción C: Descargar ZIP
# Descargar desde GitHub y extraer, luego:
cd DaveAgent
```

### Paso 2: Instalar en Modo Desarrollo

```bash
# Instalar el paquete en modo editable
pip install -e .

# Esto instala:
# - CodeAgent y todas sus dependencias
# - El comando global 'daveagent'
# - Permite editar el código sin reinstalar
```

### Paso 3: Verificar la Instalación

```bash
# Verificar que el comando esté disponible
daveagent --version

# Debería mostrar algo como:
# DaveAgent version 1.1.0
```

### Paso 4: ¡Listo para Usar!

```bash
# Navega a cualquier directorio
cd ~/my-project

# Inicia CodeAgent
daveagent
```

---

## 📦 Método 2: Instalación desde PyPI (Próximamente)

**Nota**: Esta opción estará disponible cuando se publique en PyPI.

```bash
# Instalación simple (disponible próximamente)
pip install daveagent-ai

# Usar desde cualquier directorio
daveagent
```

---

## 🔧 Instalación de Dependencias Opcionales

### Dependencias de Desarrollo

Si planeas contribuir al proyecto o desarrollar características:

```bash
# Instalar con dependencias de desarrollo
pip install -e ".[dev]"

# Esto instala herramientas adicionales:
# - pytest (testing)
# - black (formateo de código)
# - flake8 (linting)
# - mypy (type checking)
```

### Dependencias Completas

```bash
# Ver todas las dependencias instaladas
pip list | grep -E "autogen|rich|prompt|pandas"

# Dependencias principales:
# - autogen-agentchat>=0.4.0     - Framework de agentes
# - autogen-ext[openai]>=0.4.0   - Extensiones de modelo
# - prompt-toolkit>=3.0.0         - Interfaz CLI
# - rich>=13.0.0                  - Formateo y colores
# - pandas>=2.0.0                 - Procesamiento de datos
# - wikipedia>=1.4.0              - Herramientas web
# - python-dotenv>=1.0.0          - Variables de entorno
# - chromadb>=0.4.0               - Base de datos vectorial
```

---

## ⚙️ Configuración Post-Instalación

### 1. Configurar API Key

CodeAgent usa DeepSeek por defecto, pero puedes usar cualquier proveedor compatible con OpenAI.

#### Método A: Variables de Entorno

Crea un archivo `.env` en el directorio de trabajo:

```bash
# En el directorio raíz de CodeAgent
touch .env
```

Edita `.env` y agrega:

```env
# API Configuration
DAVEAGENT_API_KEY=your-api-key-here
DAVEAGENT_MODEL=deepseek-chat
DAVEAGENT_BASE_URL=https://api.deepseek.com/v1

# O para OpenAI:
# DAVEAGENT_API_KEY=sk-...
# DAVEAGENT_MODEL=gpt-4
# DAVEAGENT_BASE_URL=https://api.openai.com/v1

# SSL Configuration (opcional)
DAVEAGENT_SSL_VERIFY=true
```

#### Método B: Editar main.py Directamente

Edita `src/main.py`:

```python
self.model_client = OpenAIChatCompletionClient(
    model="tu-modelo",           # Cambiar aquí
    base_url="tu-base-url",      # Cambiar aquí
    api_key="tu-api-key",        # Cambiar aquí
    model_capabilities={
        "vision": True,
        "function_calling": True,
        "json_output": True,
    },
)
```

### 2. Configuración SSL (Redes Corporativas)

Si experimentas errores de certificado SSL:

```bash
# Opción 1: Variable de entorno en .env
DAVEAGENT_SSL_VERIFY=false

# Opción 2: Argumento de línea de comandos
daveagent --no-ssl-verify

# Opción 3: Variable de sistema
export DAVEAGENT_SSL_VERIFY=false  # Linux/macOS
set DAVEAGENT_SSL_VERIFY=false     # Windows CMD
$env:DAVEAGENT_SSL_VERIFY="false"  # Windows PowerShell
```

### 3. Configurar Directorio de Trabajo

Por defecto, CodeAgent opera en el directorio actual:

```bash
# Navegar al proyecto
cd ~/mi-proyecto

# Iniciar CodeAgent (trabajará en ~/mi-proyecto)
daveagent
```

---

## 🐧 Instalación Específica para Linux

### Ubuntu/Debian

```bash
# Instalar Python 3.10+ si no está disponible
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip git

# Clonar e instalar
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip install -e .
```

### Fedora/RHEL

```bash
# Instalar dependencias
sudo dnf install python3.10 python3-pip git

# Clonar e instalar
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip install -e .
```

### Script de Instalación Automatizada

Para Linux con evaluación SWE-bench:

```bash
# Otorgar permisos de ejecución
chmod +x setup_and_run_linux.sh

# Ejecutar script (compila, instala y ejecuta evaluación)
./setup_and_run_linux.sh
```

---

## 🪟 Instalación Específica para Windows

### Windows 10/11

```powershell
# Verificar Python (debe ser 3.10+)
python --version

# Clonar repositorio
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent

# Instalar
pip install -e .

# Verificar
daveagent --version
```

### Script de Compilación e Instalación

```bash
# Usar script de Windows
.\build_and_install.bat
```

**Nota para Windows**: Si encuentras problemas con permisos, ejecuta PowerShell como Administrador.

---

## 🍎 Instalación Específica para macOS

```bash
# Instalar Homebrew (si no está instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python 3.10+
brew install python@3.10

# Clonar e instalar
git clone https://github.com/davidmonterocrespo24/DaveAgent.git
cd DaveAgent
pip3 install -e .

# Verificar
daveagent --version
```

---

## 🐳 Instalación con Docker (Próximamente)

```bash
# Construir imagen Docker
docker build -t codeagent .

# Ejecutar contenedor
docker run -it --rm \
  -v $(pwd):/workspace \
  -e DAVEAGENT_API_KEY=your-key \
  codeagent
```

---

## 🔍 Verificación de la Instalación

### Prueba Básica

```bash
# Iniciar CodeAgent
daveagent

# Dentro de CodeAgent, prueba:
You: /help

# Debería mostrar la ayuda de comandos
```

### Prueba de Herramientas

```bash
You: read the README.md file
You: /search main function
You: git status
```

### Prueba de Memoria

```bash
You: /index
# Debería indexar el proyecto

You: /memory
# Debería mostrar estadísticas de memoria
```

---

## 🐛 Solución de Problemas de Instalación

### Problema: "Command 'daveagent' not found"

**Solución**:
```bash
# Verificar que pip instaló en el PATH correcto
pip show daveagent-cli

# O usar el módulo directamente
python -m src.cli
```

### Problema: "ModuleNotFoundError: No module named 'autogen'"

**Solución**:
```bash
# Reinstalar dependencias
pip install -r requirements.txt

# O instalar manualmente
pip install 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'
```

### Problema: Errores de SSL en Redes Corporativas

**Solución**:
```bash
# Deshabilitar verificación SSL
daveagent --no-ssl-verify

# O configurar certificados corporativos
export REQUESTS_CA_BUNDLE=/path/to/your/ca-bundle.crt
```

### Problema: "Permission denied" en Linux/macOS

**Solución**:
```bash
# Instalar solo para el usuario actual
pip install --user -e .

# O usar un entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# O venv\Scripts\activate  # Windows
pip install -e .
```

---

## 🔄 Actualización de CodeAgent

### Actualizar desde Git

```bash
# Navegar al directorio de CodeAgent
cd DaveAgent

# Obtener últimos cambios
git pull origin main

# Reinstalar (si hay cambios en dependencias)
pip install -e .
```

### Actualizar Dependencias

```bash
# Actualizar todas las dependencias
pip install --upgrade -r requirements.txt

# O actualizar solo AutoGen
pip install --upgrade 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'
```

---

## 🗑️ Desinstalación

```bash
# Desinstalar el paquete
pip uninstall daveagent-cli

# Eliminar directorio (si se clonó desde Git)
rm -rf DaveAgent

# Limpiar archivos de configuración (opcional)
rm -rf ~/.daveagent
```

---

## ✅ Siguientes Pasos

Una vez instalado correctamente:

1. **[Inicio Rápido](Quick-Start)** - Aprende los comandos básicos en 5 minutos
2. **[Guía de Uso](Usage-Guide)** - Flujos de trabajo y casos de uso
3. **[Configuración](Configuration)** - Personaliza CodeAgent a tus necesidades
4. **[Herramientas](Tools-and-Features)** - Explora las 45+ herramientas disponibles

---

## 📞 ¿Necesitas Ayuda?

- **Discord**: [Únete a nuestro servidor](https://discord.gg/2dRTd4Cv)
- **Issues**: [GitHub Issues](https://github.com/davidmonterocrespo24/DaveAgent/issues)
- **Email**: contact@daveagent.ai

---

[← Volver al Home](Home) | [Configuración →](Configuration)
