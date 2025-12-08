# 🧠 Sistema de Memoria Vectorial - Quick Start

## ¿Qué es?

DaveAgent ahora tiene **memoria persistente** usando ChromaDB y embeddings vectoriales. Los agentes recuerdan:
- 💬 Conversaciones previas
- 📝 Código de tu proyecto
- 🎯 Decisiones arquitectónicas
- ⚙️ Tus preferencias de código

## Instalación

```bash
# Instalar dependencias nuevas
pip install -r requirements.txt

# Incluye:
# - chromadb>=0.4.22
# - sentence-transformers>=2.2.2
# - aiofiles>=23.0.0
# - aiohttp>=3.9.0
```

## Uso Rápido

### 1. Indexar tu Proyecto (Una Vez)

```bash
$ daveagent
Tu: /index
```

Esto indexa todo tu código en memoria vectorial (~1-2 minutos para 100 archivos).

### 2. Usar Normalmente

```bash
Tu: Crea un endpoint de autenticación con JWT

# Los agentes automáticamente:
# ✅ Consultan conversaciones previas sobre autenticación
# ✅ Buscan código similar en tu proyecto
# ✅ Usan tu estilo de código preferido
```

### 3. Ver Estadísticas

```bash
Tu: /memory

🧠 Estadísticas de Memoria Vectorial
  • Conversations: Historial de conversaciones
  • Codebase: Código fuente indexado (45 archivos, 234 chunks)
  • Decisions: Decisiones arquitectónicas
  • Preferences: Preferencias del usuario
```

## Comandos

| Comando | Descripción |
|---------|-------------|
| `/index` | Indexa el proyecto en memoria |
| `/memory` | Muestra estadísticas |
| `/memory clear` | Limpia toda la memoria |

## Ubicación de Datos

Toda la memoria se guarda localmente en:
```
~/.daveagent/memory/
```

## Beneficios

### Antes (Sin Memoria)
```
Usuario: "Crea endpoint de autenticación"
Agente: [lee todo el código desde cero]
Agente: [genera código sin contexto previo]
```

### Ahora (Con Memoria)
```
Usuario: "Crea endpoint de autenticación"
Agente: [consulta memoria: "ya hablamos de auth antes"]
Agente: [consulta código indexado: "hay auth.py en src/"]
Agente: [consulta preferencias: "usuario prefiere FastAPI"]
Agente: [genera código consistente con todo lo anterior]
```

## Arquitectura

```
MemoryManager
├── conversation_memory    # Historial de conversaciones
├── codebase_memory       # Código indexado
├── decision_memory       # Decisiones técnicas
└── preferences_memory    # Preferencias del usuario
```

## Agentes con Memoria

| Agente | Memoria | Beneficio |
|--------|---------|-----------|
| CodeSearcher | Codebase | Búsquedas más rápidas |
| Coder | Conversations + Codebase + Preferences | Código consistente |
| PlanningAgent | Decisions | Decisiones coherentes |

## Documentación Completa

- 📖 **[docs/MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md)** - Documentación completa
- 🔧 **[docs/SISTEMA_MEMORIA_IMPLEMENTACION.md](docs/SISTEMA_MEMORIA_IMPLEMENTACION.md)** - Detalles técnicos
- 💻 **[examples/memory_usage_example.py](examples/memory_usage_example.py)** - Ejemplo de código

## FAQ

### ¿Necesito reindexar después de cambios?

No es necesario inmediatamente. La memoria persiste y los agentes pueden usar herramientas normales para leer código actualizado. Reindexar periódicamente mejora el rendimiento.

### ¿Cuánto espacio usa?

- **Modelo de embeddings**: ~80MB (se descarga una vez)
- **Proyecto típico (100 archivos)**: ~5-15MB
- **Total**: ~100MB para un proyecto normal

### ¿Es privado?

Sí, 100% local:
- ✅ Datos almacenados en `~/.daveagent/memory/`
- ✅ No se envía nada a servidores externos
- ✅ Embeddings generados localmente

### ¿Puedo borrar la memoria?

Sí:
```bash
Tu: /memory clear
```

O manualmente:
```bash
rm -rf ~/.daveagent/memory/
```

### ¿Funciona offline?

Sí, después de la primera ejecución (que descarga el modelo de embeddings).

## Solución de Problemas

### "No module named 'chromadb'"

```bash
pip install -r requirements.txt
```

### Memoria no se actualiza

```bash
# Reindexar el proyecto
Tu: /index
```

### Demasiado espacio usado

```bash
# Limpiar memoria
Tu: /memory clear

# Luego reindexar solo lo necesario
Tu: /index
```

## Próximos Pasos

1. **Usa `/index`** una vez para indexar tu proyecto
2. **Trabaja normalmente** - la memoria se usa automáticamente
3. **Reindexar periódicamente** para mejor rendimiento

¡Disfruta de agentes con memoria! 🧠✨
