# 🎉 ¡CodeAgent Instalado Como Paquete!

## ✅ Estado Actual

CodeAgent ya está instalado y listo para usar. Ahora puedes ejecutar `codeagent` desde **cualquier directorio**.

---

## 🚀 Uso Básico

### 1. Ir a cualquier proyecto

```bash
# Ejemplo: Ir a un proyecto web
cd C:\Users\tuusuario\proyectos\mi-web

# Iniciar CodeAgent
codeagent
```

### 2. CodeAgent trabajará en ese directorio

```
🚀 Iniciando CodeAgent en: C:\Users\tuusuario\proyectos\mi-web
📂 Directorio de trabajo: C:\Users\tuusuario\proyectos\mi-web

╔════════════════════════════════════════════╗
║        🤖 CodeAgent - Asistente IA         ║
╚════════════════════════════════════════════╝

Tu: crear un archivo index.html
```

CodeAgent creará `C:\Users\tuusuario\proyectos\mi-web\index.html`

---

## 📝 Ejemplos Prácticos

### Ejemplo 1: Trabajar en un proyecto Python

```bash
# 1. Ve a tu proyecto
cd D:\Python\mi-app

# 2. Inicia CodeAgent
codeagent

# 3. Pide algo
Tu: crear un módulo utils.py con funciones para validar emails y fechas

# 4. CodeAgent crea el archivo en D:\Python\mi-app\utils.py
```

### Ejemplo 2: Analizar código existente

```bash
# 1. Ve al proyecto
cd C:\proyectos\backend

# 2. Inicia con debug
codeagent --debug

# 3. Analiza
Tu: analiza la estructura del proyecto y dame un resumen
Tu: encuentra todos los archivos que usan FastAPI
Tu: muestra las funciones en main.py
```

### Ejemplo 3: Operaciones Git

```bash
cd mi-repo

codeagent

Tu: muestra el status de git
Tu: haz commit de los cambios con mensaje descriptivo
Tu: muestra el diff de los últimos 3 commits
```

---

## 🎮 Comandos Disponibles

### Comandos de Terminal

```bash
# Ver versión
codeagent --version

# Ver ayuda
codeagent --help

# Iniciar con debug
codeagent --debug

# Iniciar normalmente
codeagent
```

### Comandos Dentro de CodeAgent

Una vez dentro de CodeAgent:

| Comando | Descripción |
|---------|-------------|
| `/help` | Muestra ayuda completa |
| `/debug` | Activa/desactiva modo debug |
| `/logs` | Muestra ubicación de logs |
| `/stats` | Muestra estadísticas |
| `/clear` | Limpia historial |
| `/new` | Nueva conversación |
| `/exit` | Salir de CodeAgent |

---

## 📂 Cómo Funciona el Directorio de Trabajo

### Regla Simple

**El directorio de trabajo es donde ejecutas `codeagent`**

### Ejemplos

```bash
# Si estás en:
cd C:\Users\tuusuario\Desktop
codeagent
# → CodeAgent trabaja en C:\Users\tuusuario\Desktop

# Si estás en:
cd D:\proyectos\web\frontend
codeagent
# → CodeAgent trabaja en D:\proyectos\web\frontend
```

### Lo que CodeAgent puede hacer en ese directorio

- ✅ Leer archivos existentes
- ✅ Crear nuevos archivos
- ✅ Editar archivos
- ✅ Eliminar archivos
- ✅ Listar directorios
- ✅ Buscar en el código
- ✅ Ejecutar Git
- ✅ Trabajar con JSON/CSV
- ✅ Y mucho más...

---

## 🔧 42 Herramientas Disponibles

CodeAgent tiene 42 herramientas organizadas en 6 categorías:

### 📁 Filesystem (6 tools)
- Leer/escribir/editar archivos
- Listar directorios
- Buscar archivos

### 🔧 Git (8 tools)
- status, add, commit, push, pull
- log, branch, diff

### 📊 JSON (8 tools)
- Leer/escribir JSON
- Validar, formatear, combinar
- Convertir a/desde texto

### 📈 CSV (7 tools)
- Leer/escribir CSV
- Filtrar, ordenar, combinar
- Convertir a JSON

### 🌐 Web (6 tools)
- Buscar en Wikipedia
- Obtener contenido
- Información de páginas

### 🔍 Analysis (7 tools)
- Analizar código Python
- Buscar funciones
- Grep/search en código
- Ejecutar comandos

---

## 💡 Tips y Trucos

### Tip 1: Usa rutas relativas

CodeAgent entiende rutas relativas al directorio actual:

```
Tu: lee el archivo src/main.py
Tu: crea un nuevo archivo en utils/helpers.js
```

### Tip 2: Modo debug para ver qué hace

```bash
codeagent --debug
```

Verás logs detallados de cada operación:
```
[15:47:19] INFO     📝 Nueva solicitud del usuario: crear utils.py
[15:47:19] DEBUG    Iniciando ejecución con Coder directamente
[15:47:19] DEBUG    Llamando a coder_agent.run() con la tarea
```

### Tip 3: Ver los logs después

```
Tu: /logs
📄 Archivo de logs: logs/codeagent_20250131_154022.log
```

Luego puedes abrir ese archivo para revisar todo lo que pasó.

### Tip 4: Múltiples tareas en una solicitud

```
Tu: crea un archivo main.py con una clase User,
    un archivo utils.py con funciones de validación,
    y un archivo README.md explicando el proyecto
```

---

## 🐛 Si Algo Sale Mal

### CodeAgent no responde

1. Presiona `Ctrl+C` para cancelar
2. Revisa los logs con `/logs`
3. Reinicia con `codeagent --debug`

### Error: "command not found: codeagent"

El directorio de scripts de Python no está en tu PATH.

**Solución**:
```bash
# Encuentra donde está Python
python -c "import sys; print(sys.executable)"

# Agrega C:\Python312\Scripts a tu PATH (Windows)
# o /usr/local/bin (Linux/Mac)
```

### CodeAgent trabaja en el directorio incorrecto

Verifica donde estás con:
```bash
pwd          # Linux/Mac
cd           # Windows

# Luego ve al directorio correcto
cd ruta/correcta
codeagent
```

---

## 🔄 Actualizar CodeAgent

Si haces cambios al código:

```bash
# Como instalaste con -e (modo desarrollo),
# los cambios se reflejan automáticamente
# ¡No necesitas reinstalar!
```

Si quieres reinstalar:

```bash
cd E:\AI\CodeAgent
pip install --upgrade --force-reinstall -e .
```

---

## 🗑️ Desinstalar

Si quieres desinstalar CodeAgent:

```bash
pip uninstall codeagent-cli
```

---

## 📊 Comparación: Antes vs. Después

### ❌ ANTES (Sin paquete)

```bash
# Tenías que hacer esto cada vez:
cd E:\AI\CodeAgent
python main.py

# Y solo funcionaba en ese directorio específico
```

### ✅ AHORA (Con paquete)

```bash
# Desde CUALQUIER directorio:
cd donde-quieras
codeagent

# ¡Y funciona en ese directorio!
```

---

## 🎯 Casos de Uso Reales

### Caso 1: Desarrollo Web

```bash
cd C:\proyectos\mi-web
codeagent

Tu: crea un componente React para un formulario de login
Tu: agrega estilos CSS para que sea responsive
Tu: crea tests para el componente
```

### Caso 2: Análisis de Datos

```bash
cd D:\datos\ventas-2024
codeagent

Tu: lee todos los CSV en esta carpeta
Tu: combínalos en un solo archivo
Tu: muestra las 10 ventas más altas
Tu: crea un resumen en formato JSON
```

### Caso 3: Scripts de Automatización

```bash
cd C:\scripts
codeagent

Tu: crea un script que haga backup de archivos .py
Tu: agrega logging al script
Tu: crea un README explicando cómo usarlo
```

---

## 🎉 ¡Listo Para Usar!

Ahora tienes CodeAgent instalado como un paquete de Python profesional.

**Para empezar**:

```bash
# 1. Ve a tu proyecto
cd tu-proyecto

# 2. Inicia CodeAgent
codeagent

# 3. ¡Empieza a trabajar!
Tu: hola, ayúdame a crear un módulo de autenticación
```

---

## 📚 Documentación Adicional

- [README.md](README.md) - Documentación completa
- [INSTALACION.md](INSTALACION.md) - Instalación detallada
- [LOGGING_GUIDE.md](LOGGING_GUIDE.md) - Sistema de logs
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios

---

¿Tienes preguntas? Abre un issue en el repositorio o consulta la documentación.

**¡Feliz codificación con CodeAgent! 🚀**
