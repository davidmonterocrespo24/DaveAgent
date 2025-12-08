# 🐛 Solución de Problemas - CodeAgent

Esta guía te ayudará a resolver problemas comunes al usar CodeAgent.

## 📋 Índice

- [Problemas de Instalación](#-problemas-de-instalación)
- [Problemas de Configuración](#-problemas-de-configuración)
- [Problemas de Conexión](#-problemas-de-conexión)
- [Problemas de Herramientas](#-problemas-de-herramientas)
- [Problemas de Memoria](#-problemas-de-memoria)
- [Problemas de Rendimiento](#-problemas-de-rendimiento)
- [Logs y Debugging](#-logs-y-debugging)

---

## 🔧 Problemas de Instalación

### "Command 'daveagent' not found"

**Problema**: El comando `daveagent` no se encuentra después de la instalación.

**Soluciones**:

```bash
# Solución 1: Reinstalar
cd DaveAgent
pip install -e .

# Solución 2: Verificar instalación
pip show daveagent-cli

# Solución 3: Usar módulo directamente
python -m src.cli

# Solución 4: Agregar pip al PATH
export PATH="$HOME/.local/bin:$PATH"  # Linux/macOS
# O agregar a .bashrc / .zshrc
```

**Windows específico**:
```powershell
# Verificar PATH de Scripts
python -m site --user-site
# Agregar ...\Python\Scripts al PATH del sistema
```

### "ModuleNotFoundError: No module named 'autogen'"

**Problema**: Falta AutoGen o dependencias.

**Soluciones**:

```bash
# Solución 1: Instalar dependencias
pip install -r requirements.txt

# Solución 2: Instalar AutoGen manualmente
pip install 'autogen-agentchat>=0.4.0' 'autogen-ext[openai]>=0.4.0'

# Solución 3: Verificar versión de Python
python --version  # Debe ser 3.10+

# Solución 4: Reinstalar en entorno virtual limpio
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
pip install -e .
```

### "Permission denied" en Linux/macOS

**Problema**: No tienes permisos para instalar globalmente.

**Soluciones**:

```bash
# Solución 1: Instalar solo para usuario
pip install --user -e .

# Solución 2: Usar entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate
pip install -e .

# Solución 3: Usar sudo (no recomendado)
sudo pip install -e .
```

---

## ⚙️ Problemas de Configuración

### "API key not found"

**Problema**: No se encuentra la API key.

**Soluciones**:

```bash
# Solución 1: Crear archivo .env
cd DaveAgent
touch .env
echo "DAVEAGENT_API_KEY=your-key-here" >> .env

# Solución 2: Variable de entorno de sistema
export DAVEAGENT_API_KEY=your-key  # Linux/macOS
set DAVEAGENT_API_KEY=your-key     # Windows CMD
$env:DAVEAGENT_API_KEY="your-key"  # Windows PowerShell

# Solución 3: Editar main.py directamente
# Edita src/main.py y agrega el API key
```

### "Invalid model name"

**Problema**: El modelo especificado no existe o no está disponible.

**Soluciones**:

```env
# Verificar modelos disponibles según proveedor

# DeepSeek
DAVEAGENT_MODEL=deepseek-chat

# OpenAI
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_MODEL=gpt-4-turbo
DAVEAGENT_MODEL=gpt-3.5-turbo

# Groq
DAVEAGENT_MODEL=llama3-70b-8192
DAVEAGENT_MODEL=mixtral-8x7b-32768
```

---

## 🌐 Problemas de Conexión

### "SSL Certificate Error"

**Problema**: Errores de certificado SSL en redes corporativas.

**Soluciones**:

```bash
# Solución 1: Deshabilitar verificación SSL (desarrollo)
daveagent --no-ssl-verify

# Solución 2: Variable de entorno
export DAVEAGENT_SSL_VERIFY=false

# Solución 3: Usar certificado corporativo
export REQUESTS_CA_BUNDLE=/path/to/company-ca.crt

# Solución 4: Configurar en .env
echo "DAVEAGENT_SSL_VERIFY=false" >> .env
```

**Advertencia**: Solo deshabilita SSL en ambientes de desarrollo/confianza.

### "Connection Refused" o "Timeout"

**Problema**: No se puede conectar al API endpoint.

**Soluciones**:

```bash
# Verificar conectividad
curl -I https://api.deepseek.com/v1
ping api.openai.com

# Verificar configuración de proxy
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Configurar proxy si es necesario
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080

# Verificar firewall
# Asegúrate de que el puerto 443 esté abierto
```

### "Rate Limit Exceeded"

**Problema**: Has excedido el límite de rate del API.

**Soluciones**:

```bash
# Solución 1: Esperar antes de reintentar
# La mayoría de APIs tienen límites por minuto

# Solución 2: Usar modelo con límite más alto
# Cambiar a plan pago o tier superior

# Solución 3: Implementar retry con backoff
# Editar src/main.py para agregar retry logic
```

---

## 🛠️ Problemas de Herramientas

### "Tool execution failed"

**Problema**: Una herramienta falló al ejecutarse.

**Diagnóstico**:

```bash
# Activar modo debug
daveagent --debug

# Revisar logs
tail -f logs/daveagent_*.log

# Verificar permisos de archivos
ls -la archivo-problema.py
```

**Soluciones comunes**:

```bash
# Para herramientas de archivo
chmod +r archivo.py  # Dar permisos de lectura
chmod +w archivo.py  # Dar permisos de escritura

# Para herramientas Git
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Para herramientas CSV/JSON
# Verificar encoding del archivo
file -I datos.csv
```

### "edit_file no encuentra la cadena"

**Problema**: `edit_file` no puede encontrar el texto a reemplazar.

**Soluciones**:

```bash
# El problema suele ser whitespace o diferencias exactas

# Solución 1: Leer el archivo primero
You: read auth.py lines 40-50
# Luego copiar el texto EXACTO que se muestra

# Solución 2: Usar @mention para dar contexto
You: @auth.py change line 45 from X to Y

# Solución 3: Ser más específico
You: in auth.py, find the login function and add error handling
# En lugar abuela: edit line 45
```

### "Git command failed"

**Problema**: Comandos Git fallan.

**Soluciones**:

```bash
# Verificar que estás en un repositorio Git
git status

# Inicializar repo si es necesario
git init

# Configurar usuario Git
git config user.name "Your Name"
git config user.email "you@example.com"

# Verificar remote
git remote -v

# Si no hay remote, agregarlo
git remote add origin https://github.com/user/repo.git
```

---

## 🧠 Problemas de Memoria

### "ChromaDB connection failed"

**Problema**: No se puede conectar a ChromaDB.

**Soluciones**:

```bash
# Solución 1: Eliminar y recrear base de datos
rm -rf .daveagent/memory/
daveagent
You: /index  # Reindexar

# Solución 2: Verificar permisos
chmod -R 755 .daveagent/

# Solución 3: Reinstalar ChromaDB
pip install --upgrade chromadb
```

### "/index falla o se congela"

**Problema**: La indexación tarda mucho o falla.

**Soluciones**:

```bash
# Solución 1: Indexar directorios específicos
# En lugar de /index, indexa solo lo necesario
You: index only the src/ directory

# Solución 2: Excluir archivos grandes
# Agregar a .gitignore:
*.log
*.db
node_modules/
__pycache__/

# Solución 3: Aumentar timeout (en main.py)
# Editar configuración de ChromaDB

# Solución 4: Limpiar y reindexar
rm -rf .daveagent/memory/
daveagent --debug
You: /index
```

### "Memory query returns no results"

**Problema**: Las búsquedas en memoria no devuelven resultados.

**Soluciones**:

```bash
# Solución 1: Verificar que el proyecto esté indexado
You: /memory
# Debe mostrar collections con datos

# Solución 2: Reindexar
You: /index

# Solución 3: Usar consultas más amplias
# En lugar de: "exact function name"
# Usar: "function that handles authentication"

# Solución 4: Revisar logs para errores de embeddings
daveagent --debug
# Buscar errores de "embedding"
```

---

## ⚡ Problemas de Rendimiento

### "CodeAgent es muy lento"

**Problema**: Respuestas tardan mucho.

**Soluciones**:

```bash
# Solución 1: Usar modelo más rápido
DAVEAGENT_MODEL=gpt-3.5-turbo
# O: deepseek-coder

# Solución 2: Reducir contexto
DAVEAGENT_MAX_TOKENS=4000
DAVEAGENT_SUMMARY_THRESHOLD=3000

# Solución 3: Limpiar historial frecuentemente
You: /clear

# Solución 4: Deshabilitar memoria si no la usas
# Comentar memory tools en main.py
```

### "Usa demasiados tokens"

**Problema**: Consumo excesivo de tokens.

**Soluciones**:

```bash
# Solución 1: Comprimir historial más frecuentemente
DAVEAGENT_SUMMARY_THRESHOLD=4000  # Reducir de 6000

# Solución 2: Limpiar historial manualmente
You: /clear

# Solución 3: Ser más específico en peticiones
# Mal: "do something with this project"
# Bien: "add error handling to login function in auth.py"

# Solución 4: Usar file mentions
You: @auth.py fix the bug
# En lugar de dejar que el agente busque
```

### "Out of Memory"

**Problema**: Python se queda sin memoria.

**Soluciones**:

```bash
# Solución 1: Cerrar y reiniciar CodeAgent
# Ctrl+C, luego daveagent

# Solución 2: Limpiar memoria ChromaDB
rm -rf .daveagent/memory/chroma.sqlite3

# Solución 3: Aumentar memoria de Python (en main.py)
# Solo para proyectos muy grandes

# Solución 4: Excluir archivos grandes de indexación
# Usar .gitignore para excluir:
*.db
*.sqlite
large_data/
```

---

## 📊 Logs y Debugging

### Activar Modo Debug

```bash
# Método 1: Argumento de CLI
daveagent --debug

# Método 2: Variable de entorno
export DAVEAGENT_DEBUG=true
daveagent

# Método 3: En .env
DAVEAGENT_DEBUG=true
DAVEAGENT_LOG_LEVEL=DEBUG
```

### Ubicación de Logs

```bash
# Por defecto en directory logs/
ls -la logs/

# Ver log más reciente
tail -f logs/daveagent_$(date +%Y%m%d)*.log

# Buscar errores
grep -i "error" logs/*

# Buscar warnings
grep -i "warning" logs/*
```

### Ver Log Específico

```bash
# Dentro de CodeAgent
You: /logs

# Resultado:
📄 Log file: logs/daveagent_20240315_143022.log

# Luego ver con:
tail -f logs/daveagent_20240315_143022.log
```

### Información de Debug Útil

Cuando reportes un problema, incluye:

```bash
# 1. Versión de CodeAgent
daveagent --version

# 2. Versión de Python
python --version

# 3. Sistema operativo
uname -a  # Linux/macOS
systeminfo  # Windows

# 4. Dependencias instaladas
pip list | grep -E "autogen|rich|prompt"

# 5. Últimas líneas del log
tail -n 50 logs/daveagent_*.log

# 6. Variables de entorno (sin API keys)
env | grep DAVEAGENT
```

---

## 🆘 Obtener Ayuda

### Recursos de Soporte

1. **Discord** (Recomendado para respuestas rápidas)
   - [Únete al servidor](https://discord.gg/2dRTd4Cv)
   - Canal #support para ayuda
   - Canal #bugs para reportar bugs

2. **GitHub Issues**
   - [Crear issue](https://github.com/davidmonterocrespo24/DaveAgent/issues)
   - Buscar issues similares primero
   - Usar template de bug report

3. **Email**
   - contact@daveagent.ai
   - Incluir logs y detalles

### Template para Reportar Bugs

Al reportar un problema, incluye:

```markdown
**Problema**:
[Descripción breve del problema]

**Pasos para Reproducir**:
1. Ejecutar comando X
2. Hacer Y
3. Ver error Z

**Comportamiento Esperado**:
[Qué debería pasar]

**Comportamiento Actual**:
[Qué pasa realmente]

**Entorno**:
- OS: [Windows 11 / Ubuntu 22.04 / macOS 14]
- Python: [3.10.5]
- CodeAgent: [1.1.0]
- Modelo: [gpt-4]

**Logs**:
```
[Pegar últimas 20-30 líneas del log]
```

**Configuración .env (sin API keys)**:
```
DAVEAGENT_MODEL=gpt-4
DAVEAGENT_SSL_VERIFY=false
...
```
```

---

## ✅ Checklist de Troubleshooting

Antes de reportar un bug, verifica:

- [ ] CodeAgent está actualizado (`git pull`, `pip install -e .`)
- [ ] Python es 3.10+ (`python --version`)
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] API key configurada (`cat .env`)
- [ ] Logs revisados (`tail logs/*.log`)
- [ ] Modo debug activado (`daveagent --debug`)
- [ ] Problema reproducible
- [ ] Búsqueda en issues existentes

---

## 📚 Ver También

- **[Configuration](Configuration)** - Opciones de configuración
- **[Installation](Installation)** - Guía de instalación
- **[Development](Development)** - Contribuir al proyecto
- **[GitHub Issues](https://github.com/davidmonterocrespo24/DaveAgent/issues)** - Problemas conocidos

---

[← Volver al Home](Home) | [Configuración →](Configuration)
