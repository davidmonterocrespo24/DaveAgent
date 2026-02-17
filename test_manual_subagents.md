# Pruebas Manuales - Sistema de Subagentes

## ✅ FASE 1: Tests Unitarios - COMPLETADO

- ✅ test_subagents.py: PASSED
- ✅ test_cli_subagents.py: PASSED

---

## 🚀 FASE 2: Iniciar el Agente

### Paso 1: Iniciar DaveAgent

```bash
python -m src.main
```

**Verificar**:
- [ ] Agente inicia sin errores
- [ ] No aparecen errores de importación relacionados con subagents
- [ ] Mensaje de inicialización exitosa

### Paso 2: Verificar Ayuda

Ejecutar dentro del agente:

```
/help
```

**Buscar en la salida**:
- [ ] Sección "Subagents (Parallel Execution)" presente
- [ ] Comando `/subagents` documentado
- [ ] Comando `/subagent-status <id>` documentado

### Paso 3: Verificar Estado Inicial

```
/subagents
```

**Resultado esperado**:
```
No active subagents
```

---

## 🧪 FASE 3: Test de Spawn Simple

### Test 3.1: Análisis Simple

**Prompt**:
```
Por favor, usa la herramienta spawn_subagent para crear un subagente
que analice el archivo src/subagents/events.py y me diga:
1. Cuántas líneas tiene
2. Qué clases define
3. Cuántos métodos async tiene

Dale el label "event-analyzer"
```

**Verificar**:
- [ ] Agente reconoce spawn_subagent
- [ ] Agente llama spawn_subagent(task="...", label="event-analyzer")
- [ ] Aparece mensaje: "Subagent 'event-analyzer' spawned (ID: XXXXXXXX)"
- [ ] Subagent ejecuta en background
- [ ] Aparece notificación cuando completa
- [ ] Resultado correcto mostrado

### Test 3.2: Verificar con CLI

Mientras o después del test anterior:

```
/subagents
```

**Esperado**: Tabla con el subagent (Running o Completed)

```
/subagent-status <id-mostrado>
```

**Esperado**:
- ID, Label, Status
- Task description visible
- Result (si completó)

---

## 🔄 FASE 4: Ejecución Paralela

### Test 4.1: Tres Tareas Simultáneas

**Prompt**:
```
Necesito que ejecutes 3 tareas EN PARALELO usando spawn_subagent:

TAREA 1 (label: "line-counter"):
Cuenta el total de líneas de código en todos los archivos .py
del directorio src/subagents/

TAREA 2 (label: "async-finder"):
Busca cuántas veces aparece la palabra "async" en todos los
archivos Python del proyecto (usa grep_search)

TAREA 3 (label: "doc-reader"):
Lee el archivo SUBAGENTS.md y dame un resumen de 3 líneas
de qué es el sistema de subagentes

¡Es muy importante que uses spawn_subagent para las 3 tareas!
```

**Verificar**:
- [ ] Agente spawnea 3 subagents
- [ ] Los 3 tienen IDs diferentes
- [ ] Los 3 tienen labels correctos

**Durante la ejecución** (rápido, antes que terminen):

```
/subagents
```

**Esperado**: Ver los 3 subagents listados como "Running"

**Después de completar**:
- [ ] Los 3 completan exitosamente
- [ ] Resultados son correctos
- [ ] No hay errores

### Test 4.2: Verificar Cada Subagent

```
/subagent-status <id1>
/subagent-status <id2>
/subagent-status <id3>
```

**Verificar para cada uno**:
- [ ] Status: Completed
- [ ] Task description correcta
- [ ] Result presente
- [ ] Timestamps coherentes

---

## ❌ FASE 5: Manejo de Errores

### Test 5.1: Archivo Inexistente

**Prompt**:
```
Usa spawn_subagent para crear un subagent (label: "error-test")
que intente leer el archivo /ruta/inexistente/archivo.txt
```

**Verificar**:
- [ ] Subagent se crea
- [ ] Subagent falla (error esperado)
- [ ] Sistema NO crashea
- [ ] Evento "failed" se publica
- [ ] Error reportado al usuario

```
/subagent-status <id-del-error>
```

**Esperado**:
- Status: Failed
- Error message visible

---

## 🚫 FASE 6: Prevención de Recursión

### Test 6.1: Intentar Spawn Recursivo

**Prompt**:
```
Intenta crear un subagent que a su vez intente usar spawn_subagent
para crear otro subagent. Quiero ver si el sistema previene la recursión.
```

**Verificar**:
- [ ] Primer subagent se crea
- [ ] Subagent NO puede usar spawn_subagent (tool no disponible)
- [ ] Mensaje de error claro
- [ ] Sin recursión infinita
- [ ] Sistema estable

---

## 🎯 FASE 7: Caso de Uso Real - Análisis de Proyecto

### Test 7.1: Análisis Completo del Sistema

**Prompt**:
```
Analiza el sistema de subagentes que acabas de usar. Crea 4 subagents
en paralelo para:

1. (label: "code-stats") Cuenta líneas en src/subagents/
2. (label: "test-stats") Cuenta líneas en test_subagents.py
3. (label: "doc-summary") Resume SUBAGENTS.md en 5 líneas
4. (label: "tool-analyzer") Lista todas las funciones en src/tools/spawn_subagent.py

Dame un reporte consolidado al final.
```

**Verificar**:
- [ ] 4 subagents creados
- [ ] Todos ejecutan en paralelo
- [ ] Todos completan

**Monitoreo**:
```
/subagents
```

**Resultados**:
- [ ] Reporte consolidado coherente
- [ ] Todos los datos correctos

---

## 💪 FASE 8: Stress Test

### Test 8.1: 5 Subagents Simultáneos

**Prompt**:
```
Crea 5 subagents en paralelo, cada uno debe leer un archivo diferente:

1. src/subagents/events.py
2. src/subagents/manager.py
3. src/subagents/tool_wrapper.py
4. src/tools/spawn_subagent.py
5. test_subagents.py

Cada uno debe contar sus líneas. Labels: "reader-1" hasta "reader-5"
```

**Verificar**:
- [ ] 5 subagents creados
- [ ] Sistema estable
- [ ] Todos completan
- [ ] No memory leaks visibles (Task Manager)

---

## 🔧 FASE 9: CLI Avanzado

### Test 9.1: Comandos Durante Ejecución

1. Crear subagents con tareas largas
2. Ejecutar repetidamente:

```
/subagents
/subagents
/subagents
```

**Verificar**: Lista se actualiza correctamente

---

## 🔄 FASE 10: Backward Compatibility

### Test 10.1: Sin Subagents

**Prompt normal** (sin mencionar spawn):
```
Lee el archivo src/main.py y dime cuántas líneas tiene
```

**Verificar**:
- [ ] Agente funciona normalmente
- [ ] NO usa spawn_subagent
- [ ] Resultado correcto

### Test 10.2: Mix de Tareas

**Prompt**:
```
Primero lee src/config/orchestrator.py (hazlo directo, sin spawn).
Luego crea un subagent para analizar src/subagents/.
Mientras ese subagent corre, lee SUBAGENTS.md también directo.
```

**Verificar**:
- [ ] Mix funciona
- [ ] Agente decide cuándo usar spawn

---

## 📊 Reporte de Resultados

### Resumen
- Tests pasados: __/25
- Tests fallados: __
- Bugs encontrados: __

### Estado General
- [ ] ✅ APROBADO - Listo para producción
- [ ] ⚠️ APROBADO CON OBSERVACIONES
- [ ] ❌ REQUIERE CORRECCIONES

### Observaciones
[Escribir aquí cualquier issue encontrado]

---

## 🎉 Conclusión

Si todos los tests pasan:
- ✅ Sistema de subagentes 100% funcional
- ✅ Ejecución paralela verificada
- ✅ Error handling correcto
- ✅ CLI commands operativos
- ✅ Backward compatibility confirmada

**¡El sistema está listo para uso en producción!** 🚀
