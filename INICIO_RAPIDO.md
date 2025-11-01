# 🚀 Inicio Rápido - CodeAgent

Comienza a usar CodeAgent en menos de 2 minutos.

## Paso 1: Instalar

```bash
pip install codeagent-ai
```

O desde código fuente:
```bash
git clone https://github.com/CodeAgent-AI/codeagent.git
cd codeagent
pip install -e .
```

## Paso 2: Ejecutar

```bash
codeagent
```

## ¿Qué pasa ahora?

### Primera Vez: Configuración Interactiva

Si es la primera vez que usas CodeAgent, verás:

```
⚠️  No se encontró una API key configurada.

¿Quieres configurar CodeAgent ahora? (S/n):
```

**Presiona Enter** (o escribe 's') para comenzar la configuración guiada.

### Paso por Paso:

#### 1. Ingresa tu API Key

```
📝 Configuración de API Key
──────────────────────────────────────────────────────────────────────

CodeAgent necesita una API key para funcionar.

Opciones recomendadas:
  1. DeepSeek (Gratis) - https://platform.deepseek.com/api_keys
  2. OpenAI (GPT-4)    - https://platform.openai.com/api-keys

🔑 Ingresa tu API key:
```

**Pega tu API key** y presiona Enter.

#### 2. Selecciona el Proveedor

```
🌐 Selección de Proveedor
──────────────────────────────────────────────────────────────────────

¿Qué proveedor de IA quieres usar?

  1. DeepSeek (Recomendado - Rápido y económico)
  2. OpenAI (GPT-4 - Más potente pero costoso)
  3. Personalizado (Otra API compatible con OpenAI)
  4. Usar configuración por defecto (DeepSeek)

Selecciona una opción (1-4):
```

**Selecciona 1** para DeepSeek (recomendado) o **2** para OpenAI.

#### 3. Guardar Configuración

```
💾 Guardar Configuración
──────────────────────────────────────────────────────────────────────

¿Quieres guardar esta configuración en un archivo .env?

Ventajas:
  ✓ No tendrás que configurar cada vez que uses CodeAgent
  ✓ La configuración se aplica automáticamente a este directorio
  ✓ Es seguro (el archivo .env no se sube a Git)

¿Guardar en .env? (S/n):
```

**Presiona Enter** (o escribe 's') para guardar.

#### 4. ¡Listo!

```
✅ Configuración guardada exitosamente!
   Archivo: E:\tu-directorio\.env

🎉 ¡Todo listo! Ahora puedes usar CodeAgent simplemente con:
   codeagent
```

## Primer Uso

Después de configurar, verás el mensaje de bienvenida:

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ██████╗ ██████╗ ███████╗     █████╗  ██████╗     ║
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗██╔════╝     ║
║  ██║     ██║   ██║██║  ██║█████╗      ███████║██║  ███╗    ║
║  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══██║██║   ██║    ║
║  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║  ██║╚██████╔╝    ║
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝ ╚═════╝     ║
║                                                              ║
║              Agente Inteligente de Desarrollo               ║
║                    Versión 1.1.0                            ║
╚══════════════════════════════════════════════════════════════╝

Tu:
```

## Ejemplos de Uso

### Ejemplo 1: Crear un Archivo

```
Tu: crea un archivo llamado hola.py con una función que imprima "Hola Mundo"
```

CodeAgent:
- Crea el archivo `hola.py`
- Escribe la función
- Te muestra el resultado

### Ejemplo 2: Buscar en Código

```
Tu: /search función de logging
```

CodeAgent:
- Busca en todo el código
- Te muestra dónde está implementado
- Proporciona contexto completo

### Ejemplo 3: Operaciones Git

```
Tu: git status
```

CodeAgent:
- Ejecuta `git status`
- Te muestra los cambios

## Comandos Internos

| Comando | Descripción |
|---------|-------------|
| `/help` | Muestra ayuda |
| `/search <consulta>` | Busca en el código |
| `/debug` | Activa/desactiva debug |
| `/logs` | Muestra ubicación de logs |
| `/clear` | Limpia historial |
| `/exit` | Salir |

## Obtener API Key (DeepSeek - Gratis)

1. Ve a https://platform.deepseek.com
2. Crea una cuenta
3. Ve a https://platform.deepseek.com/api_keys
4. Clic en "Create API Key"
5. Copia la key (empieza con `sk-`)

**¡Listo!** DeepSeek te da créditos gratuitos para empezar.

## Configuración Manual (Opcional)

Si prefieres configurar manualmente sin el asistente:

### Opción 1: Archivo .env

```bash
# Crear archivo .env
echo "CODEAGENT_API_KEY=sk-tu-api-key-aqui" > .env

# Usar CodeAgent
codeagent
```

### Opción 2: Variable de Entorno

```bash
# Windows
$env:CODEAGENT_API_KEY="sk-tu-api-key-aqui"

# Linux/Mac
export CODEAGENT_API_KEY="sk-tu-api-key-aqui"

codeagent
```

### Opción 3: Argumento CLI

```bash
codeagent --api-key "sk-tu-api-key-aqui"
```

## Solución de Problemas

### "No se encontró API key"

**Solución**: Ejecuta `codeagent` y sigue el asistente de configuración.

### "Invalid API key"

**Solución**: Verifica que la API key sea correcta y tenga créditos disponibles.

### Quiero cambiar de proveedor

**Solución**: Edita el archivo `.env` o usa argumentos CLI:

```bash
# Cambiar a OpenAI
codeagent --api-key "sk-proj-..." --base-url "https://api.openai.com/v1" --model "gpt-4"
```

## Próximos Pasos

- Lee la [Documentación Completa](README.md)
- Aprende sobre [CodeSearcher](docs/CODESEARCHER_GUIDE.md)
- Configura [Opciones Avanzadas](CONFIGURACION.md)

## ¿Necesitas Ayuda?

```bash
codeagent --help
```

O visita la documentación en: https://github.com/CodeAgent-AI/codeagent

---

¡Disfruta usando CodeAgent! 🎉
