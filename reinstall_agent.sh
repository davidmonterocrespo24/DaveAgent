#!/bin/bash
# Script para reinstalar DaveAgent con los cambios más recientes

echo "========================================"
echo "  Reinstalando DaveAgent"
echo "========================================"

# 1. Desinstalar versión anterior
echo "[1/3] Desinstalando versión anterior..."
pip uninstall -y daveagent 2>/dev/null || echo "No había versión instalada"

# 2. Limpiar caché de build
echo "[2/3] Limpiando caché..."
rm -rf build/ dist/ *.egg-info src/*.egg-info

# 3. Instalar en modo editable (usa el código fuente directamente)
echo "[3/3] Instalando en modo editable..."
pip install -e .

echo ""
echo "✓ DaveAgent reinstalado correctamente"
echo "✓ Ahora usa el código fuente local"
echo ""
