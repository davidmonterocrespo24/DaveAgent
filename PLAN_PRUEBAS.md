# Plan de Pruebas - Sistema de Subagentes Paralelos

## 🎯 Objetivo

Validar que el sistema de subagentes paralelos funciona correctamente en escenarios reales de uso.

---

## 📋 Checklist de Pruebas

### Nivel 1: Tests Unitarios ✅
- [x] Event Bus pub/sub
- [x] Tool filtering
- [x] SubAgent Manager
- [x] Spawn tool
- [x] CLI commands

### Nivel 2: Tests de Integración (A realizar)
- [ ] Sistema completo end-to-end
- [ ] Ejecución paralela real
- [ ] Manejo de errores
- [ ] CLI en vivo

### Nivel 3: Tests de Casos de Uso Reales (A realizar)
- [ ] Análisis de código en paralelo
- [ ] Ejecución de tests + documentación simultánea
- [ ] Búsqueda en múltiples directorios

---

## 🧪 Plan de Pruebas Detallado

### FASE 1: Verificación de Tests Existentes (5 min)

**Objetivo**: Confirmar que todos los tests unitarios pasan

```bash
# Test 1: Tests principales de subagentes
python test_subagents.py

# Test 2: Tests de CLI commands
python test_cli_subagents.py
```

**Resultado esperado**:
- ✅ ALL TESTS PASSED en ambos
- Sin errores ni warnings

---

### FASE 2: Test del Sistema Completo (15 min)

**Objetivo**: Ejecutar el agente y verificar inicialización

#### 2.1 Inicio del Agente

```bash
# Iniciar el agente
python -m src.main
```

**Verificaciones**:
- [ ] Agente inicia sin errores
- [ ] No aparecen errores de importación
- [ ] SubAgent system se inicializa correctamente
- [ ] CLI muestra prompt normal

#### 2.2 Verificar Ayuda

```bash
# Dentro del agente
/help
```

**Verificar**:
- [ ] Aparece sección "Subagents (Parallel Execution)"
- [ ] Comandos `/subagents` y `/subagent-status` documentados

#### 2.3 Test de Comandos Vacíos

```bash
# Dentro del agente
/subagents
```

**Resultado esperado**:
```
No active subagents
```

---

### FASE 3: Test de Spawn Simple (20 min)

**Objetivo**: Verificar que el agente puede usar spawn_subagent

#### 3.1 Tarea Simple de Análisis

**Prompt para el agente**:
```
Por favor, usa spawn_subagent para crear un subagente que analice el archivo
src/subagents/events.py y me diga cuántas líneas tiene y qué clases define.
```

**Verificaciones esperadas**:
- [ ] Agente detecta la herramienta spawn_subagent
- [ ] Agente llama a spawn_subagent con task y label adecuados
- [ ] Aparece mensaje: "Subagent 'X' spawned (ID: XXXXXXXX)"
- [ ] Subagent ejecuta en background
- [ ] Aparece notificación de completitud
- [ ] Resultado se muestra al usuario

#### 3.2 Verificar con CLI

Mientras el subagent corre:

```bash
/subagents
```

**Esperado**:
- Tabla con 1 subagent activo
- Status: Running o Completed

```bash
/subagent-status <id-del-subagent>
```

**Esperado**:
- Detalles completos del subagent
- Task description visible
- Result o "Still executing..."

---

### FASE 4: Test de Ejecución Paralela (30 min)

**Objetivo**: Verificar ejecución paralela real de múltiples subagents

#### 4.1 Múltiples Tareas en Paralelo

**Prompt para el agente**:
```
Necesito que hagas 3 tareas en paralelo usando spawn_subagent:

1. Analiza todos los archivos en src/subagents/ y cuenta cuántas líneas de código hay en total
2. Busca la palabra "async" en todos los archivos Python del proyecto usando grep
3. Lee el archivo SUBAGENTS.md y dame un resumen de 2 líneas

Hazlo todo en paralelo para que sea más rápido.
```

**Verificaciones**:
- [ ] Agente spawnea 3 subagents
- [ ] Todos tienen IDs diferentes
- [ ] Todos corren simultáneamente (verificar con `/subagents`)
- [ ] Todos completan exitosamente
- [ ] Resultados se muestran al usuario
- [ ] Tiempo total < suma de tiempos individuales (prueba de paralelismo)

#### 4.2 Monitoreo Durante Ejecución

Mientras corren:

```bash
# Verificar lista de activos
/subagents

# Ver detalles de cada uno
/subagent-status <id1>
/subagent-status <id2>
/subagent-status <id3>
```

---

### FASE 5: Test de Manejo de Errores (15 min)

**Objetivo**: Verificar que errores se manejan correctamente

#### 5.1 Tarea que Fallará

**Prompt**:
```
Usa spawn_subagent para leer un archivo que no existe: /archivo/inexistente.txt
```

**Verificaciones**:
- [ ] Subagent se spawnea
- [ ] Subagent falla (no crash del sistema)
- [ ] Evento "failed" se publica
- [ ] Error se reporta al usuario
- [ ] Sistema principal sigue funcionando

#### 5.2 Verificar Estado de Fallo

```bash
/subagent-status <id-del-fallido>
```

**Esperado**:
- Status: Failed
- Error message visible
- Sin crash del sistema

---

### FASE 6: Test de Prevención de Recursión (10 min)

**Objetivo**: Verificar que subagents NO pueden spawnar más subagents

#### 6.1 Intentar Recursión

**Prompt**:
```
Crea un subagent que a su vez intente crear otro subagent.
```

**Verificaciones**:
- [ ] Primer subagent se crea correctamente
- [ ] Subagent NO tiene acceso a spawn_subagent
- [ ] Error claro si intenta usar spawn_subagent
- [ ] No hay recursión infinita
- [ ] Sistema se mantiene estable

---

### FASE 7: Test de Casos de Uso Reales (30 min)

**Objetivo**: Probar escenarios prácticos del mundo real

#### 7.1 Análisis de Código Multi-directorio

**Prompt**:
```
Analiza en paralelo:
- src/subagents/ (cuenta archivos y líneas)
- src/tools/ (lista todas las funciones async)
- src/config/ (busca imports de asyncio)

Usa spawn_subagent para cada directorio y dame un reporte consolidado.
```

**Verificaciones**:
- [ ] 3 subagents en paralelo
- [ ] Cada uno analiza su directorio
- [ ] Resultados correctos
- [ ] Reporte consolidado coherente

#### 7.2 Tests + Documentación Simultánea

**Prompt**:
```
En paralelo:
1. Ejecuta los tests: python test_subagents.py
2. Lee SUBAGENTS.md y extrae las características principales
3. Cuenta cuántos archivos .py hay en el proyecto

Usa spawn_subagent para todo.
```

**Verificaciones**:
- [ ] 3 tareas diferentes ejecutándose
- [ ] Una ejecuta comando bash
- [ ] Otra lee archivo
- [ ] Otra usa glob/grep
- [ ] Todas completan correctamente

#### 7.3 Búsqueda Paralela

**Prompt**:
```
Busca en paralelo la palabra "SubagentEvent" en:
- Archivos Python (.py)
- Archivos Markdown (.md)
- Tests (test_*.py)

Crea un subagent para cada tipo de archivo.
```

**Verificaciones**:
- [ ] 3 búsquedas paralelas
- [ ] Resultados completos
- [ ] Sin duplicados
- [ ] Performance mejor que secuencial

---

### FASE 8: Test de Stress (15 min)

**Objetivo**: Ver límites del sistema

#### 8.1 Múltiples Subagents Simultáneos

**Prompt**:
```
Crea 5 subagents simultáneos, cada uno debe:
1. Leer un archivo diferente de src/subagents/
2. Contar sus líneas
3. Reportar el resultado

Hazlo todo en paralelo.
```

**Verificaciones**:
- [ ] 5 subagents se crean
- [ ] Todos ejecutan en paralelo
- [ ] Sistema se mantiene estable
- [ ] No hay memory leaks
- [ ] Todos completan exitosamente

#### 8.2 Monitoreo de Recursos

Durante la ejecución:

```bash
# En otra terminal (Windows)
tasklist | findstr python

# O usar Task Manager
# Verificar:
# - Uso de CPU
# - Uso de memoria
# - Número de procesos
```

---

### FASE 9: Test de CLI Avanzado (10 min)

**Objetivo**: Probar todas las features del CLI

#### 9.1 Comandos Durante Ejecución

1. Spawner varios subagents con tareas largas
2. Mientras ejecutan:

```bash
# Listar activos múltiples veces
/subagents
/subagents
/subagents

# Ver status de cada uno
/subagent-status <id1>
/subagent-status <id2>

# Verificar que la información se actualiza
```

#### 9.2 Verificar Historial de Eventos

- [ ] Eventos persisten después de completitud
- [ ] Timestamps correctos
- [ ] Event history completa

---

### FASE 10: Test de Integración con Sistema Existente (10 min)

**Objetivo**: Verificar backward compatibility

#### 10.1 Tareas Normales (Sin Subagents)

**Prompt**:
```
Lee el archivo src/main.py y dime cuántas líneas tiene
(sin usar spawn_subagent)
```

**Verificaciones**:
- [ ] Agente funciona normalmente
- [ ] No usa spawn_subagent
- [ ] Resultado correcto
- [ ] Sin overhead

#### 10.2 Mix de Tareas

**Prompt**:
```
1. Lee src/config/orchestrator.py (directo, sin spawn)
2. Luego crea un subagent para analizar src/subagents/
3. Mientras el subagent corre, lee SUBAGENTS.md

Mezcla tareas normales con subagents.
```

**Verificaciones**:
- [ ] Mix funciona correctamente
- [ ] Agente decide cuándo usar spawn
- [ ] Sistema estable

---

## 📊 Métricas a Recolectar

### Performance
- [ ] Tiempo de spawn (< 100ms)
- [ ] Overhead por subagent (< 50MB RAM)
- [ ] Tiempo de cleanup (inmediato)
- [ ] Speedup paralelo (3 tasks en paralelo ~3x más rápido)

### Estabilidad
- [ ] 0 crashes
- [ ] 0 memory leaks
- [ ] 0 deadlocks
- [ ] 0 race conditions

### Funcionalidad
- [ ] 100% de subagents completan (o fallan gracefully)
- [ ] 100% de eventos se publican
- [ ] 100% de resultados accesibles vía CLI

---

## 🐛 Problemas Conocidos a Buscar

### Posibles Issues
- [ ] Subagent no se limpia después de completar
- [ ] Event bus se satura con muchos eventos
- [ ] CLI commands no muestran subagents completados
- [ ] Resultados se pierden si subagent falla
- [ ] Recursión no prevenida correctamente
- [ ] Memory leak en tasks de larga duración

### Validaciones de Seguridad
- [ ] spawn_subagent NO está en tools de subagents
- [ ] Max iterations = 15 (no 25)
- [ ] Subagents no comparten estado
- [ ] Errores no propagan al parent

---

## 📝 Template de Reporte de Pruebas

```markdown
# Reporte de Pruebas - Sistema de Subagentes

**Fecha**: YYYY-MM-DD
**Tester**: [Nombre]
**Versión**: 1.0.0

## Resumen Ejecutivo
- Tests pasados: X/Y
- Tests fallidos: Z
- Bugs encontrados: N
- Performance: [Excelente/Bueno/Aceptable/Malo]

## Resultados por Fase

### FASE 1: Tests Unitarios
- [x] test_subagents.py: PASSED
- [x] test_cli_subagents.py: PASSED

### FASE 2: Sistema Completo
- [ ] Inicialización: [PASS/FAIL]
- [ ] Comandos CLI: [PASS/FAIL]

### FASE 3: Spawn Simple
- [ ] Spawn básico: [PASS/FAIL]
- [ ] Notificaciones: [PASS/FAIL]

### FASE 4: Ejecución Paralela
- [ ] 3 subagents simultáneos: [PASS/FAIL]
- [ ] Speedup observado: Xx

### FASE 5: Manejo de Errores
- [ ] Error handling: [PASS/FAIL]
- [ ] Sistema estable post-error: [PASS/FAIL]

### FASE 6: Prevención de Recursión
- [ ] No recursión: [PASS/FAIL]

### FASE 7: Casos de Uso Reales
- [ ] Análisis multi-directorio: [PASS/FAIL]
- [ ] Tests + docs: [PASS/FAIL]
- [ ] Búsqueda paralela: [PASS/FAIL]

### FASE 8: Stress Test
- [ ] 5 subagents: [PASS/FAIL]
- [ ] Memory estable: [PASS/FAIL]

### FASE 9: CLI Avanzado
- [ ] Monitoreo en vivo: [PASS/FAIL]

### FASE 10: Backward Compatibility
- [ ] Sin subagents: [PASS/FAIL]
- [ ] Mix de tareas: [PASS/FAIL]

## Métricas

| Métrica | Esperado | Observado | Status |
|---------|----------|-----------|--------|
| Tiempo spawn | < 100ms | Xms | [PASS/FAIL] |
| RAM overhead | < 50MB | XMB | [PASS/FAIL] |
| Speedup 3x | ~3x | Xx | [PASS/FAIL] |
| Crashes | 0 | X | [PASS/FAIL] |

## Bugs Encontrados

1. [Bug ID] - Descripción
   - Severidad: [Alta/Media/Baja]
   - Reproducible: [Sí/No]
   - Workaround: [Descripción]

## Recomendaciones

- [ ] Apto para producción
- [ ] Requiere fixes menores
- [ ] Requiere fixes mayores

## Notas Adicionales
[Observaciones, comentarios, etc.]
```

---

## 🚀 Ejecución Rápida (Quick Test)

Si tienes tiempo limitado, ejecuta esto:

```bash
# 1. Tests unitarios (2 min)
python test_subagents.py && python test_cli_subagents.py

# 2. Iniciar agente (1 min)
python -m src.main

# 3. Dentro del agente: Test básico (5 min)
# Prompt: "Usa spawn_subagent para crear 2 subagents: uno que cuente
#          líneas en src/subagents/ y otro que busque 'async' en el proyecto"

# 4. Verificar con CLI (1 min)
/subagents
/subagent-status <id>

# 5. Test de error (2 min)
# Prompt: "Crea un subagent que lea un archivo inexistente"

# TOTAL: ~11 minutos para validación básica
```

---

## ✅ Criterios de Éxito

El sistema pasa si:

1. ✅ Todos los tests unitarios pasan
2. ✅ Agente puede spawnar subagents sin errores
3. ✅ Múltiples subagents corren en paralelo
4. ✅ CLI commands funcionan correctamente
5. ✅ Errores se manejan gracefully
6. ✅ No hay recursión infinita
7. ✅ Sistema principal sigue estable
8. ✅ No memory leaks observables
9. ✅ Resultados son correctos
10. ✅ Performance mejora con paralelismo

---

## 🎯 Siguiente Paso

**EMPEZAR CON**: FASE 1 (Verificación de tests existentes)

```bash
python test_subagents.py
```

¡Buena suerte! 🚀
