# ⚡ Ejecución Rápida de Tests

## 🎯 Comando Más Importante

Si solo vas a ejecutar UN comando, ejecuta este:

```bash
python test/test_autogen_state_resume.py
```

**Por qué:** Este test demuestra el flujo completo de:
1. Conversación inicial
2. Guardar estado
3. Cerrar aplicación
4. Abrir nueva sesión
5. Cargar estado
6. Continuar conversación
7. El agente recuerda TODO

## 📋 Todos los Tests

```bash
# Test 1: Básico (estructura del estado)
python test/test_autogen_state_basics.py

# Test 2: Sesiones múltiples
python test/test_autogen_state_sessions.py

# Test 3: Visualización bonita
python test/test_autogen_state_history_viewer.py

# Test 4: Continuación completa ⭐
python test/test_autogen_state_resume.py

# Ejecutar TODOS los tests
python test/run_all_state_tests.py

# Ejemplos prácticos para copiar/pegar
python test/examples_state_management.py
```

## ⚙️ Requisitos Previos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
pip install rich

# 2. Configurar API key en .env
echo "DEEPSEEK_API_KEY=tu_api_key_aqui" > .env
```

## 📖 Documentación

```
test/
├── README_STATE_TESTS.md         # Guía completa
├── QUICKSTART_STATE_TESTS.md     # Inicio rápido
└── TESTS_SUMMARY.md              # Resumen de todo

docs/
├── AUTOGEN_STATE_STRUCTURE.md    # Estructura del estado
├── MIGRATION_TO_AUTOGEN_STATE.md # Guía de migración
└── MIGRATION_SUMMARY.md          # Resumen de cambios
```

## 🎯 Por Orden de Complejidad

**Nivel 1 - Básico:**
```bash
python test/test_autogen_state_basics.py
```

**Nivel 2 - Intermedio:**
```bash
python test/test_autogen_state_sessions.py
python test/test_autogen_state_history_viewer.py
```

**Nivel 3 - Completo:**
```bash
python test/test_autogen_state_resume.py
```

## 🐛 Si Algo Falla

```bash
# Verificar variables de entorno
cat .env  # o type .env en Windows

# Verificar dependencias
pip list | grep autogen
pip list | grep rich

# Re-instalar si es necesario
pip install --upgrade -r requirements.txt
```

## 📊 Qué Esperar

Cada test generará archivos JSON en `test/.temp_*` con ejemplos reales del estado.

**Abre estos archivos** para ver la estructura exacta del estado de AutoGen.

---

**Tiempo estimado:**
- Test básico: ~2 minutos
- Test de sesiones: ~5 minutos
- Test de visualización: ~3 minutos
- Test de continuación: ~4 minutos
- **Total: ~15 minutos**

**¿Tienes prisa?** Solo ejecuta el test de continuación (4 minutos).
