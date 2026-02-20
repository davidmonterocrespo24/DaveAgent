# CRITICAL FIX: Subprocess Bloqueante → Async Subprocess

**Fecha**: 2026-02-19 21:00
**Problema**: Terminal se "trababa" durante ejecución de comandos largos
**Causa Root**: `subprocess.run()` bloqueante
**Solución**: Migrar a `asyncio.create_subprocess_shell()`

---

## 🔥 El Problema

### Síntoma
- Terminal parece "trancada" durante comandos largos (descargas, compilaciones, etc.)
- Spinner no rota
- No hay feedback visual durante 10-60 segundos
- Usuario piensa que el sistema está colgado

### Causa Root (CRÍTICA)

**Archivo**: [src/tools/terminal.py:48](src/tools/terminal.py#L48) (ANTES del fix)

```python
# ❌ BLOQUEANTE - Bloquea el event loop completo
result = subprocess.run(
    command, shell=True, capture_output=True, text=True, timeout=60, cwd=workspace
)
```

**Problema**: `subprocess.run()` es **BLOQUEANTE** - cuando ejecuta un comando:
1. Bloquea el event loop de asyncio
2. El spinner no puede rotar (requiere event loop)
3. No se pueden procesar otros eventos
4. El timeout espera de forma bloqueante

**Impacto**:
- ✅ Herramientas rápidas (<1s): No se nota
- ❌ **Comandos lentos (5-60s): Terminal parece congelada**
- ❌ Descargas de internet: Parece colgado
- ❌ Compilaciones: Sin feedback visual

---

## ✅ La Solución

### Inspiración: Nanobot

Revisé [nanobot/agent/tools/shell.py](nanobot/nanobot/agent/tools/shell.py#L70-L84) y encontré la implementación correcta:

```python
# ✅ NON-BLOCKING - Event loop continúa funcionando
process = await asyncio.create_subprocess_shell(
    command,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
    cwd=cwd,
)

try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(),
        timeout=self.timeout
    )
except asyncio.TimeoutError:
    process.kill()
    return f"Error: Command timed out after {self.timeout} seconds"
```

### Implementación en DaveAgent

**Archivo**: [src/tools/terminal.py](src/tools/terminal.py)

**Cambios**:

1. **Import cambiado**:
   ```python
   # ANTES
   import subprocess

   # DESPUÉS
   import asyncio
   ```

2. **Subprocess async**:
   ```python
   # ANTES (bloqueante)
   result = subprocess.run(
       command, shell=True, capture_output=True, text=True, timeout=60, cwd=workspace
   )

   # DESPUÉS (async, non-blocking)
   process = await asyncio.create_subprocess_shell(
       command,
       stdout=asyncio.subprocess.PIPE,
       stderr=asyncio.subprocess.PIPE,
       cwd=str(workspace),
   )
   ```

3. **Timeout async**:
   ```python
   # ANTES (bloqueante)
   except subprocess.TimeoutExpired:

   # DESPUÉS (async)
   try:
       stdout, stderr = await asyncio.wait_for(
           process.communicate(),
           timeout=60
       )
   except asyncio.TimeoutError:
       process.kill()  # ← Limpia el proceso correctamente
   ```

4. **Truncamiento de output** (BONUS):
   ```python
   # Nuevo: Evita saturar contexto con outputs gigantes
   max_len = 10000
   if len(result) > max_len:
       result = result[:max_len] + f"\n... (truncated, {len(result) - max_len} more chars)"
   ```

5. **Mejor formato de output**:
   ```python
   # Solo muestra STDERR si tiene contenido
   if stderr:
       stderr_text = stderr.decode("utf-8", errors="replace")
       if stderr_text.strip():  # ← Check if not empty
           output_parts.append(f"STDERR:\n{stderr_text}")
   ```

---

## 📊 Comparación: Antes vs. Después

### ANTES (Bloqueante)

```
[Terminal Output]
⠋ executing run terminal cmd...  (thinking)

[SE CONGELA DURANTE 15 SEGUNDOS - SPINNER NO ROTA]
[Usuario piensa que está colgado]
[Finalmente aparece el resultado]

✅ Coder > run_terminal_cmd: Command: wget ...
```

**Problema**: Durante 15s, el event loop está **COMPLETAMENTE BLOQUEADO** esperando que `subprocess.run()` termine.

### DESPUÉS (Async)

```
[Terminal Output]
⠋ executing run terminal cmd...  (thinking)

[SPINNER ROTA CONTINUAMENTE DURANTE TODO EL COMANDO]
[Feedback visual constante de que el sistema está trabajando]

✅ Coder > run_terminal_cmd: Command: wget ...
```

**Mejora**: El event loop sigue funcionando, el spinner rota, usuario sabe que el sistema está trabajando.

---

## 🎯 Impacto en Casos de Uso

### Caso 1: Descarga de Decompilador CFR

**Comando**:
```bash
powershell -command "Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/benf/cfr/0.152/cfr-0.152.jar' -OutFile 'cfr.jar'"
```

**ANTES**:
- Terminal congelada por 5-10 segundos
- Spinner no rota
- Usuario cancela pensando que está colgado

**DESPUÉS**:
- ✅ Spinner rota durante toda la descarga
- ✅ Terminal responsive
- ✅ Usuario sabe que está descargando

### Caso 2: Compilación de Código

**Comando**:
```bash
javac -d build src/**/*.java
```

**ANTES**:
- Terminal congelada por 30-60 segundos
- Sin feedback visual

**DESPUÉS**:
- ✅ Spinner rota durante compilación
- ✅ Si timeout (60s), proceso se mata correctamente

### Caso 3: Instalación de Dependencias

**Comando**:
```bash
pip install tensorflow
```

**ANTES**:
- Terminal congelada durante minutos
- Usuario piensa que falló

**DESPUÉS**:
- ✅ Feedback visual constante
- ✅ Timeout limpia el proceso si tarda >60s

---

## 🔧 Otras Mejoras Incluidas

### 1. Truncamiento de Output Largo

**Problema**: Comandos que generan MB de output saturan el contexto del LLM

**Solución**:
```python
max_len = 10000
if len(result) > max_len:
    result = result[:max_len] + f"\n... (truncated, {len(result) - max_len} more chars)"
```

**Ejemplo**:
- Comando `ls -R /` genera 100,000 líneas
- Antes: Saturaba contexto completo
- Ahora: Se trunca a 10,000 chars con aviso

### 2. Output más Limpio

**Antes**:
```
Command: ls
Exit code: 0

STDOUT:
file1.txt
file2.txt

STDERR:

```

**Después**:
```
Command: ls
Exit code: 0

STDOUT:
file1.txt
file2.txt
```

(No muestra sección STDERR si está vacía)

### 3. Mejor Manejo de Encoding

```python
stdout_text = stdout.decode("utf-8", errors="replace")
```

Reemplaza caracteres inválidos en lugar de fallar.

---

## 📋 Testing Recomendado

### Test 1: Comando Rápido
```bash
# Comando: echo "Hello"
# Esperado: Terminal responsive, resultado inmediato
```

### Test 2: Comando Lento (Descarga)
```bash
# Comando: curl -O https://example.com/large-file.zip
# Esperado: Spinner DEBE rotar durante toda la descarga
```

### Test 3: Timeout
```bash
# Comando: ping -t google.com (infinito en Windows)
# Esperado: Timeout a los 60s, proceso DEBE morir
```

### Test 4: Output Gigante
```bash
# Comando: dir /s C:\
# Esperado: Output truncado a 10,000 chars
```

---

## 🚨 Breaking Changes

**NINGUNO** - La API es 100% compatible:

```python
# Esto sigue funcionando exactamente igual
result = await run_terminal_cmd(
    command="ls -la",
    require_user_approval=False,
    explanation="Listing files"
)
```

Solo cambió la **implementación interna** de bloqueante a async.

---

## 📚 Referencias

- **Inspiración**: [nanobot/agent/tools/shell.py](nanobot/nanobot/agent/tools/shell.py)
- **Documentación Python**: https://docs.python.org/3/library/asyncio-subprocess.html
- **Problema reportado por usuario**: "se sigue trancando la terminal, no siguen saliendo los mensajes del agente"

---

## ✅ Checklist de Verificación

- [x] Migrado de `subprocess.run()` a `asyncio.create_subprocess_shell()`
- [x] Timeout async con `asyncio.wait_for()`
- [x] Proceso se mata en timeout con `process.kill()`
- [x] Output truncado a 10,000 chars
- [x] STDERR solo se muestra si tiene contenido
- [x] Encoding errors manejados con `errors="replace"`
- [x] Workspace convertido a string con `str(workspace)`
- [x] API backwards-compatible (sin breaking changes)
- [ ] **Testing**: Ejecutar test con comando lento (descarga)

---

## 🎉 Resultado Esperado

Después de este fix:
1. ✅ Terminal **NUNCA** se congela durante comandos largos
2. ✅ Spinner rota continuamente mientras ejecuta comandos
3. ✅ Feedback visual constante para el usuario
4. ✅ Timeouts manejan correctamente procesos colgados
5. ✅ Output gigante no satura el contexto del LLM

**Estado**: ✅ Fix implementado, listo para testing

---

**Autor**: Análisis y fix por Claude Code
**Fecha**: 2026-02-19
**Versión**: 1.0.13 (con async subprocess)
