#!/bin/bash
# Script maestro para generar todos los reportes de análisis

echo "========================================================================"
echo "  Generador de Reportes Completos - SWE-bench Evaluation"
echo "========================================================================"
echo ""

# Colores
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Directorio base
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}[1/2] Generando reporte detallado de resultados...${NC}"
python3 "$BASE_DIR/generate_detailed_report.py"

echo ""
echo -e "${CYAN}[2/2] Analizando interacciones del agente...${NC}"
python3 "$BASE_DIR/analyze_agent_interactions.py"

echo ""
echo "========================================================================"
echo -e "${GREEN}✅ Todos los reportes generados exitosamente!${NC}"
echo "========================================================================"
echo ""
echo "📂 Archivos generados en: $BASE_DIR"
echo ""
echo "Para visualizar los reportes:"
echo "  1. Abre los archivos .html en tu navegador web"
echo "  2. Los archivos .md se pueden leer en cualquier editor de texto"
echo ""
