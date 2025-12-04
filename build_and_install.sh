#!/bin/bash
# ============================================================================
# Script de Compilación e Instalación de DaveAgent
# ============================================================================
# Este script automatiza:
# 1. Limpieza de builds anteriores
# 2. Compilación del paquete
# 3. Instalación del paquete
# 4. Verificación de la instalación
# ============================================================================

set -e  # Salir si hay algún error

# Colores para terminal
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo
echo "========================================"
echo " DaveAgent - Build and Install Script"
echo "========================================"
echo

# Obtener el directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ============================================================================
echo -e "${CYAN}Paso 1: Limpiando builds anteriores...${NC}"
echo

# Limpiar directorios de build anteriores
if [ -d "build" ]; then
    echo "Eliminando directorio build/..."
    rm -rf build
fi

if [ -d "dist" ]; then
    echo "Eliminando directorio dist/..."
    rm -rf dist
fi

# Eliminar archivos .egg-info
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

echo -e "${GREEN}✓ Limpieza completada${NC}"
echo

# ============================================================================
echo -e "${CYAN}Paso 2: Verificando dependencias...${NC}"
echo

# Verificar si build está instalado
if ! python -m pip show build &> /dev/null; then
    echo -e "${YELLOW}Instalando python build...${NC}"
    python -m pip install build
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Error: No se pudo instalar build${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ build ya está instalado${NC}"
fi

echo

# ============================================================================
echo -e "${CYAN}Paso 3: Compilando el paquete...${NC}"
echo
echo "Esto puede tomar un momento..."
echo

python -m build
if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}✗ Error: La compilación falló${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Compilación exitosa${NC}"
echo

# ============================================================================
echo -e "${CYAN}Paso 4: Mostrando archivos compilados...${NC}"
echo

if [ -d "dist" ]; then
    ls -lh dist/*.whl dist/*.tar.gz 2>/dev/null || true
    echo
else
    echo -e "${RED}✗ Error: No se encontró el directorio dist/${NC}"
    exit 1
fi

# ============================================================================
echo -e "${CYAN}Paso 5: Instalando el paquete...${NC}"
echo

# Buscar el archivo .whl más reciente
WHEEL_FILE=$(ls -t dist/*.whl 2>/dev/null | head -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo -e "${RED}✗ Error: No se encontró archivo .whl en dist/${NC}"
    exit 1
fi

echo "Instalando $WHEEL_FILE..."
echo

python -m pip install "$WHEEL_FILE" --force-reinstall
if [ $? -ne 0 ]; then
    echo
    echo -e "${RED}✗ Error: La instalación falló${NC}"
    exit 1
fi

echo
echo -e "${GREEN}✓ Instalación completada${NC}"
echo

# ============================================================================
echo -e "${CYAN}Paso 6: Verificando la instalación...${NC}"
echo

# Verificar que daveagent-cli está instalado
if ! python -m pip show daveagent-cli &> /dev/null; then
    echo -e "${RED}✗ Error: daveagent-cli no está instalado correctamente${NC}"
    exit 1
fi

echo -e "${GREEN}✓ daveagent-cli está instalado${NC}"
echo

# Mostrar información del paquete
echo "Información del paquete:"
echo "------------------------"
python -m pip show daveagent-cli | grep -E "Name:|Version:|Location:"
echo

# Verificar que el comando CLI funciona
echo "Verificando comando CLI..."
if command -v daveagent &> /dev/null; then
    echo -e "${GREEN}✓ Comando 'daveagent' está disponible${NC}"
    echo
    echo "Ejecutando: daveagent --version"
    daveagent --version
else
    echo -e "${YELLOW}⚠ Advertencia: El comando 'daveagent' no está disponible en PATH${NC}"
    echo "  Puedes usar: python -m src.cli"
fi

echo

# ============================================================================
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ PROCESO COMPLETADO EXITOSAMENTE${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Archivos generados:"
echo "  - $WHEEL_FILE"
echo "  - dist/*.tar.gz"
echo
echo "Para usar:"
echo "  1. Comando directo: daveagent"
echo "  2. Como módulo: python -m src.cli"
echo "  3. Desde Python: python main.py"
echo
echo "Para desinstalar:"
echo "  pip uninstall daveagent-cli"
echo
