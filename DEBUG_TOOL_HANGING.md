# Debug: Terminal se Tranca - Herramientas Colgadas

**Fecha**: 2026-02-19 19:50
**Problema**: Terminal se queda "trancada" después de ejecutar herramientas, sin mostrar respuesta final del agente

---

## 🔍 Diagnóstico Inicial

### Síntomas
1. ✅ Tools calls se muestran correctamente
2. ✅ Herramientas se ejecutan
3. ✅ Tool results se muestran (algunos)
4. ❌ **Agente NO responde después de ciertos tool calls**
5. ❌ **No se ve mensaje "TERMINATE" ni respuesta final**

### Logs Observados

```
2026-02-19 18:49:15 | DaveAgent | DEBUG | 📨 Msg #13 | Type: ToolCallRequestEvent
2026-02-19 18:49:15 | DaveAgent | INFO  | ✅ Processing message (will show in terminal)
2026-02-19 18:49:15 | DaveAgent | DEBUG | 🔧 Tool call: run_terminal_cmd
2026-02-19 18:49:15 | DaveAgent | DEBUG | executing run_terminal_cmd

[SE QUEDA COLGADO AQUÍ - NO HAY Msg #14 con ToolCallExecutionEvent]
```

**Conclusión**: La herramienta `run_terminal_cmd` se está ejecutando pero:
- NO termina de ejecutarse (no devuelve resultado)
- O tarda MÁS del timeout (60s según [terminal.py:49](src/tools/terminal.py#L49))
- O el comando específico se quedó colgado esperando input

---

## 🛠️ Fixes Implementados

### Fix 1: Logging Detallado de Tool Execution

**Archivo**: [src/main.py:1869-1896](src/main.py#L1869-L1896)

**Agregado**:
```python
elif msg_type == "ToolCallExecutionEvent":
    # ✅ Show tool results
    self.logger.info(f"🎯 ToolCallExecutionEvent RECEIVED (results ready)")

    # ... resto del código ...

    self.logger.info(
        f"🔧 Tool '{tool_name}' execution completed, "
        f"result length: {len(result_content)} chars"
    )
```

**Propósito**: Confirmar que el `ToolCallExecutionEvent` fue recibido

---

### Fix 2: Logging Antes de Tool Execution

**Archivo**: [src/main.py:1860-1867](src/main.py#L1860-L1867)

**Agregado**:
```python
if tool_names:
    self.logger.info(
        f"🚀 STARTING EXECUTION of {len(tool_names)} tool(s): {', '.join(tool_names)}"
    )
```

**Propósito**: Marcar exactamente cuándo inicia la ejecución de herramientas

---

## 📊 Logs Esperados Ahora

### Flujo Normal (Exitoso)
```
🔧 Tool call: run_terminal_cmd
🚀 STARTING EXECUTION of 1 tool(s): run_terminal_cmd
⠋ executing run terminal cmd...  (thinking)
🎯 ToolCallExecutionEvent RECEIVED (results ready)
🔧 Tool 'run_terminal_cmd' execution completed, result length: 245 chars
✅ Coder > run_terminal_cmd: Command: ...
```

### Flujo con Problema (Herramienta Colgada)
```
🔧 Tool call: run_terminal_cmd
🚀 STARTING EXECUTION of 1 tool(s): run_terminal_cmd
⠋ executing run terminal cmd...  (thinking)

[NO HAY 🎯 ToolCallExecutionEvent - HERRAMIENTA COLGADA]
[Después de 60s debería aparecer TimeoutExpired]
```

---

## 🔧 Siguiente Paso: Identificar Comando Colgado

Una vez que tengamos los logs con el nuevo formato, podemos:

1. **Ver exactamente QUÉ comando se quedó colgado** revisando el último `run_terminal_cmd` ejecutado
2. **Verificar si el timeout de 60s se está respetando** o si el comando se queda indefinidamente
3. **Identificar si es un comando específico** que causa el problema (ej: `jar tf`, `unzip -l`, etc.)

---

## 🎯 Comandos Ejecutados en el Test

Según los logs anteriores:

1. ✅ `list_dir` → Completó exitosamente
2. ✅ `jar tf "Need for Speed - The Run 3D.jar" | head -20` → Completó (exit code 255, jar no encontrado)
3. ✅ `unzip -l "Need for Speed - The Run 3D.jar" | head -30` → Completó exitosamente
4. ✅ `glob_search` → Completó exitosamente
5. ✅ `web_search` → Completó (sin resultados)
6. ❓ **`run_terminal_cmd` (comando desconocido)** → Se quedó colgado

**Hipótesis**: El 6to comando puede ser algo que:
- Requiere input interactivo
- Descarga algo de internet (cfr decompiler)
- Ejecuta un proceso que no termina
- Tiene un timeout mayor a 60s

---

## 🔍 Cómo Depurar con los Nuevos Logs

### Paso 1: Ver logs completos
```bash
grep -E "(STARTING EXECUTION|ToolCallExecutionEvent|Tool.*execution completed)" logs/daveagent_*.log | tail -50
```

### Paso 2: Identificar herramienta colgada
```bash
grep "STARTING EXECUTION" logs/daveagent_*.log | tail -5
```

Si no hay un `ToolCallExecutionEvent` correspondiente, esa herramienta se quedó colgada.

### Paso 3: Ver parámetros del comando
```bash
grep -B 5 "STARTING EXECUTION.*run_terminal_cmd" logs/daveagent_*.log | tail -20
```

---

## 📋 Checklist de Debugging

- [x] Agregar logging antes de tool execution
- [x] Agregar logging después de tool execution
- [ ] **Ejecutar test nuevamente** con estos logs
- [ ] Identificar comando específico que se cuelga
- [ ] Verificar si timeout de 60s se respeta
- [ ] Ajustar timeout si es necesario
- [ ] Agregar protección contra comandos interactivos

---

## 🚨 Posibles Causas del Colgamiento

### 1. Comando Interactivo
El comando puede estar esperando input del usuario (ej: `python -m pip install cfr`)

**Solución**: Agregar flag `-y` o `--yes` automáticamente

### 2. Timeout Insuficiente
60 segundos puede no ser suficiente para descargar/instalar herramientas

**Solución**: Aumentar timeout a 300s (5 min) para `run_terminal_cmd`

### 3. Comando sin Salida
El comando puede estar ejecutándose pero sin producir output, quedándose en background

**Solución**: Agregar validación de procesos background

### 4. Error de Shell Pipe
Comandos con `|` (pipe) pueden fallar silenciosamente en Windows

**Solución**: Usar `shell=True` correctamente (ya está implementado)

---

**Próximo Paso**: Ejecutar test con los nuevos logs y analizar output

**Autor**: Diagnóstico por Claude Code
**Estado**: ⏳ Esperando logs del próximo test
