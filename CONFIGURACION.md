# ⚙️ Guía de Configuración de DaveAgent

DaveAgent necesita una API key para funcionar. Puedes configurarla de 3 formas diferentes.

## 📋 Requisitos

Necesitas una API key de DeepSeek (por defecto) u otro proveedor compatible con OpenAI.

### Obtener API Key de DeepSeek (Gratis)

1. Ve a https://platform.deepseek.com
2. Crea una cuenta o inicia sesión
3. Ve a API Keys: https://platform.deepseek.com/api_keys
4. Clic en "Create API Key"
5. Copia la key (empieza con `sk-`)

**Nota**: DeepSeek ofrece créditos gratuitos para probar. Es más barato que OpenAI.

## 🔧 Métodos de Configuración

### Opción 1: Archivo `.env` (Recomendado)

La forma más segura y conveniente.

#### Paso 1: Crear archivo .env

```bash
cd E:\AI\DaveAgent
copy .env.example .env
```

O en Linux/Mac:
```bash
cp .env.example .env
```

#### Paso 2: Editar .env

Abre `.env` con un editor de texto y completa:

```bash
# API Key (REQUERIDA)
DAVEAGENT_API_KEY=sk-tu-api-key-aqui

# URL base (OPCIONAL - por defecto usa DeepSeek)
# DAVEAGENT_BASE_URL=https://api.deepseek.com

# Modelo (OPCIONAL - por defecto usa deepseek-chat)
# DAVEAGENT_MODEL=deepseek-chat
```

#### Paso 3: Usar DaveAgent

```bash
daveagent
```

✅ **Ventajas**:
- No necesitas escribir la key cada vez
- Seguro: `.env` está en `.gitignore` (no se sube a Git)
- Fácil de cambiar

### Opción 2: Variables de Entorno

Configurar variables de entorno del sistema.

#### Windows (PowerShell)

```powershell
# Temporal (solo para esta sesión)
$env:DAVEAGENT_API_KEY="sk-tu-api-key-aqui"

# Permanente (todas las sesiones)
[Environment]::SetEnvironmentVariable("DAVEAGENT_API_KEY", "sk-tu-api-key-aqui", "User")
```

#### Linux / Mac

```bash
# Temporal (solo para esta sesión)
export DAVEAGENT_API_KEY="sk-tu-api-key-aqui"

# Permanente (agregar a ~/.bashrc o ~/.zshrc)
echo 'export DAVEAGENT_API_KEY="sk-tu-api-key-aqui"' >> ~/.bashrc
source ~/.bashrc
```

#### Usar DaveAgent

```bash
daveagent
```

✅ **Ventajas**:
- Disponible para todas las aplicaciones
- No necesita archivo .env

❌ **Desventajas**:
- Menos flexible (difícil cambiar entre proyectos)
- Más complicado de configurar

### Opción 3: Argumentos CLI

Pasar la API key directamente en la línea de comandos.

```bash
daveagent --api-key "sk-tu-api-key-aqui"
```

✅ **Ventajas**:
- Rápido para pruebas
- No necesita configuración previa

❌ **Desventajas**:
- **Inseguro**: La key queda en el historial del terminal
- Tedioso: Debes escribirla cada vez

## 🔀 Usar Otros Modelos

### OpenAI GPT-4

```bash
# Opción 1: Argumentos CLI
daveagent --api-key "sk-proj-..." --base-url "https://api.openai.com/v1" --model "gpt-4"

# Opción 2: Archivo .env
DAVEAGENT_API_KEY=sk-proj-tu-openai-key
DAVEAGENT_BASE_URL=https://api.openai.com/v1
DAVEAGENT_MODEL=gpt-4
```

### Ollama (Local)

```bash
daveagent --base-url "http://localhost:11434/v1" --model "llama2" --api-key "not-needed"
```

### Otros Proveedores Compatibles con OpenAI

Cualquier API compatible con OpenAI puede usarse:

```bash
daveagent --api-key "tu-key" --base-url "https://api.provider.com" --model "nombre-modelo"
```

## 📊 Prioridad de Configuración

DaveAgent usa esta prioridad (de mayor a menor):

1. **Argumentos CLI** (`--api-key`, `--base-url`, `--model`)
2. **Variables de entorno** (`DAVEAGENT_*`)
3. **Archivo .env**
4. **Valores por defecto** (DeepSeek)

### Ejemplo de Combinación

```bash
# .env tiene:
DAVEAGENT_API_KEY=sk-deepseek-key

# Ejecutas:
daveagent --model "gpt-4"

# Resultado:
# API Key: sk-deepseek-key (de .env)
# Base URL: https://api.deepseek.com (por defecto)
# Model: gpt-4 (de CLI)
```

## 🔍 Verificar Configuración

Para ver qué configuración está usando DaveAgent:

```bash
# Iniciar con debug
daveagent --debug

# Verás en los logs:
# ✓ Configuración cargada: DaveAgentSettings(
#   api_key=sk-8cb1f...942d60,
#   base_url=https://api.deepseek.com,
#   model=deepseek-chat
# )
```

## 🚨 Solución de Problemas

### Error: "API key no configurada"

```
❌ API key no configurada.

Opciones para configurarla:
  1. Variable de entorno: export DAVEAGENT_API_KEY='tu-api-key'
  2. Archivo .env: DAVEAGENT_API_KEY=tu-api-key
  3. Argumento CLI: daveagent --api-key 'tu-api-key'

Obtén tu API key en: https://platform.deepseek.com/api_keys
```

**Solución**: Configura la API key usando uno de los 3 métodos anteriores.

### Error: "Invalid API key"

**Síntomas**: El agente se inicia pero falla al hacer la primera solicitud.

**Solución**:
1. Verifica que la API key sea correcta
2. Verifica que tenga créditos disponibles
3. Verifica que esté usando la base URL correcta

### Error: "Connection refused"

**Síntomas**: No puede conectarse a la API.

**Solución**:
1. Verifica tu conexión a Internet
2. Verifica que la `base_url` sea correcta
3. Si usas un servicio local (Ollama), verifica que esté corriendo

## 🛡️ Seguridad

### ⚠️ IMPORTANTE: No Compartir API Keys

- **NO** subas archivos `.env` a Git
- **NO** compartas tu API key en Discord, Slack, etc.
- **NO** uses API keys en código que subes a GitHub

### ✅ Buenas Prácticas

1. **Usa archivo .env** para desarrollo local
2. **Agrega .env al .gitignore** (ya está configurado)
3. **Rota keys regularmente** (crea nuevas cada pocos meses)
4. **Usa variables de entorno** en producción/servidores
5. **Limita permisos** de las keys en el dashboard del proveedor

### 🔄 Rotar API Key

Si crees que tu key fue comprometida:

1. Ve al dashboard de tu proveedor
2. Revoca la key antigua
3. Crea una nueva key
4. Actualiza `.env` o variables de entorno

## 📖 Ejemplos Completos

### Ejemplo 1: Configuración Básica (DeepSeek)

```bash
# 1. Crear .env
echo "DAVEAGENT_API_KEY=sk-tu-deepseek-key" > .env

# 2. Usar
daveagent
```

### Ejemplo 2: Usar OpenAI Temporalmente

```bash
# Sin cambiar .env
daveagent --api-key "sk-proj-openai-key" --base-url "https://api.openai.com/v1" --model "gpt-4"
```

### Ejemplo 3: Múltiples Proyectos

```bash
# Proyecto 1 (DeepSeek)
cd proyecto1
echo "DAVEAGENT_API_KEY=sk-deepseek-key" > .env
daveagent

# Proyecto 2 (OpenAI)
cd proyecto2
echo "DAVEAGENT_API_KEY=sk-proj-openai-key" > .env
echo "DAVEAGENT_BASE_URL=https://api.openai.com/v1" >> .env
echo "DAVEAGENT_MODEL=gpt-4" >> .env
daveagent
```

## 📝 Referencia de Variables

| Variable | Descripción | Default | Requerida |
|----------|-------------|---------|-----------|
| `DAVEAGENT_API_KEY` | API key del modelo LLM | - | ✅ Sí |
| `DAVEAGENT_BASE_URL` | URL base de la API | `https://api.deepseek.com` | ❌ No |
| `DAVEAGENT_MODEL` | Nombre del modelo | `deepseek-chat` | ❌ No |

### Alias Compatibles

También puedes usar estos nombres (para compatibilidad):

- `OPENAI_API_KEY` → `DAVEAGENT_API_KEY`
- `DEEPSEEK_API_KEY` → `DAVEAGENT_API_KEY`
- `OPENAI_BASE_URL` → `DAVEAGENT_BASE_URL`
- `OPENAI_MODEL` → `DAVEAGENT_MODEL`

## 🆘 Ayuda Adicional

### Ver todos los argumentos disponibles

```bash
daveagent --help
```

### Ver versión

```bash
daveagent --version
```

### Modo debug

```bash
daveagent --debug
```

Muestra configuración detallada y logs de todas las operaciones.

---

## 💡 Tips

1. **Usa .env para desarrollo** - Es lo más cómodo y seguro
2. **Usa variables de entorno en producción** - Más seguro en servidores
3. **Rota keys cada 3-6 meses** - Buena práctica de seguridad
4. **Prueba con DeepSeek primero** - Es más barato y rápido
5. **Usa --debug si hay problemas** - Te ayudará a diagnosticar

¿Tienes problemas? Revisa los logs en `logs/daveagent_*.log` o ejecuta con `--debug`.
