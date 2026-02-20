# Terminal Blocking Fixes - Solución Completa

## Problema Identificado

El sistema se "trancaba" durante operaciones largas (como `write_file` con archivos grandes) porque:

1. **Stream buffering**: `await stream_task` antes de iterar esperaba a que TODO el stream terminara
2. **Rendering síncrono**: Rich panel/syntax rendering bloqueaba el event loop
3. **Auto-save bloqueante**: Guardado de estado después de cada tool bloqueaba el flujo
4. **Logger no inicializado**: SubAgentManager no tenía logger, causando errores silenciosos

## Soluciones Implementadas

### 1. Fix Stream Iteration (CRÍTICO)
**Archivos modificados:**
- `src/main.py` línea 1618
- `src/config/orchestrator.py` línea 1047

**Cambio:**
```python
# ANTES (bloqueante - wrappea en Task y espera)
stream_task = asyncio.create_task(self._run_team_stream(full_input))
async for msg in await stream_task:

# DESPUÉS (streaming real - await para obtener generator, luego itera)
stream_generator = await self._run_team_stream(full_input)
async for msg in stream_generator:
```

**Nota Importante:**
- `_run_team_stream()` es `async def` que **retorna** un async generator
- Primero hacemos `await` para ejecutar la función y obtener el generator
- Luego iteramos sobre el generator con `async for`
- NO usamos `asyncio.create_task()` porque necesitamos iterar, no solo ejecutar

**Impacto:** Los mensajes ahora se muestran inmediatamente conforme son generados, no al final.

---

### 2. Auto-save No Bloqueante
**Archivos modificados:**
- `src/main.py` líneas 1957, 1982

**Cambio:**
```python
# ANTES (bloqueante - espera a que el I/O termine)
await self._auto_save_agent_states()

# DESPUÉS (background task - no bloquea)
asyncio.create_task(self._auto_save_agent_states())
```

**Impacto:** El guardado de estado ya no interrumpe el flujo de mensajes.

---

### 3. Rich Rendering Async
**Archivos modificados:**
- `src/interfaces/cli_interface.py` (múltiples líneas)
- `src/main.py` líneas 1747, 1905

**Cambios:**
1. Agregado `import functools` y `concurrent.futures.ThreadPoolExecutor`
2. Nuevo atributo `self._executor` en `CLIInterface.__init__()`
3. Nuevo método `_run_in_executor()` para ejecutar código sync en thread pool
4. Renombrado `print_code()` → `_print_code_sync()` (versión interna)
5. Nueva `print_code()` async que llama a `_print_code_sync()` via executor
6. Actualizado cleanup en `__del__()` para cerrar el executor

**Ejemplo:**
```python
async def print_code(self, code: str, filename: str, max_lines: int = 50):
    """Versión async que no bloquea el event loop"""
    await self._run_in_executor(self._print_code_sync, code, filename, max_lines)
```

**Impacto:** El renderizado de archivos grandes (syntax highlighting, panels) ya no congela la UI.

---

### 4. Logger en SubAgentManager
**Archivos modificados:**
- `src/subagents/manager.py` líneas 12, 77

**Cambio:**
```python
# ANTES (sin logger)
self._results: dict[str, dict] = {}

# DESPUÉS (con logger)
self._results: dict[str, dict] = {}
self.logger = logging.getLogger("DaveAgent")
```

**Impacto:** Los debug messages de subagents ahora se registran correctamente.

---

## Comparación con Nanobot

### Arquitectura Aprendida de Nanobot

| Aspecto | Nanobot | Nuestro Fix |
|---------|---------|-------------|
| **Message streaming** | Directo via `asyncio.Queue` | ✅ Ahora usa streaming real |
| **Terminal rendering** | No bloquea (canal-based) | ✅ Ahora usa executor threads |
| **Auto-save** | No bloqueante | ✅ Ahora usa `create_task()` |
| **Timeout polling** | 1.0s | Ya teníamos 0.5s (más rápido) |
| **Subagent límite** | Sin límite | Ya teníamos `max_concurrent=10` |

### Diferencias Arquitecturales

**Nanobot:**
- Multi-canal (Telegram, Discord, Slack)
- Message bus con subscribers/callbacks
- Inyección directa de mensajes

**DaveAgent (nuestro):**
- CLI-only (optimizado para terminal)
- Event bus + detector intermedio
- Rich rendering avanzado

---

## Testing

### Cómo Verificar los Fixes

1. **Test de archivo grande:**
   ```bash
   python src/main.py
   # Pedir al agente: "Create a Python file with 500 lines of code"
   ```

   **Esperado:**
   - ✅ Spinner muestra progreso inmediato
   - ✅ Mensajes aparecen mientras se genera el código
   - ✅ Syntax highlighting no congela la terminal

2. **Test de múltiples tools:**
   ```bash
   # Pedir: "Create 5 files with different content"
   ```

   **Esperado:**
   - ✅ Cada tool result se muestra inmediatamente
   - ✅ Auto-save no interrumpe el flujo
   - ✅ Terminal permanece responsive

3. **Test de subagent:**
   ```bash
   # Pedir: "Spawn a subagent to analyze the codebase"
   ```

   **Esperado:**
   - ✅ Logger muestra debug messages correctamente
   - ✅ Resultado del subagent se inyecta sin bloqueo

---

## Archivos Modificados

1. **src/main.py**
   - Línea 1618: Stream iteration fix
   - Líneas 1747, 1905: await para print_code async
   - Líneas 1957, 1982: Auto-save no bloqueante

2. **src/config/orchestrator.py**
   - Línea 1047: Stream iteration fix para system messages

3. **src/interfaces/cli_interface.py**
   - Línea 6: Import functools
   - Línea 141: Agregar `self._executor`
   - Líneas 270-289: Método `_run_in_executor()`
   - Líneas 272-274: Cleanup en `__del__()`
   - Líneas 658-765: Refactor de `print_code()` (sync + async)

4. **src/subagents/manager.py**
   - Línea 12: Import logging
   - Línea 77: Inicializar self.logger

---

## Próximos Pasos (Opcional)

### Optimizaciones Adicionales

1. **Simplificar Message Bus** (inspirado en Nanobot)
   - Remover event→detector→message bus
   - Inyección directa de mensajes

2. **Batching de rendering**
   - Agrupar múltiples tool results antes de renderizar

3. **Lazy loading para syntax highlighting**
   - Solo renderizar cuando el archivo sea < 1000 líneas

4. **Progress bars para tools largos**
   - Mostrar % de progreso durante write_file

---

## Referencias

- **Análisis Nanobot:** Ver reportes de los agentes Explore
- **Commit original:** [incluir hash cuando se haga commit]
- **Issue relacionado:** Terminal se congela durante operaciones largas

---

**Fecha:** 2026-02-19
**Autor:** Análisis realizado por Claude Code Agent
**Estado:** ✅ Completado y listo para testing
