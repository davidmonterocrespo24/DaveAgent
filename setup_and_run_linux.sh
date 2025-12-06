#!/bin/bash
set -e # Exit on error

# Definition of colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================================${NC}"
echo -e "${CYAN}      Agent Setup & SWE-bench Eval           ${NC}"
echo -e "${CYAN}=============================================${NC}"

# 1. Build and Install Agent
echo -e "${GREEN}[1/5] Installing Agent in Editable Mode...${NC}"

# Uninstall previous version
echo "Removing previous installation..."
python3 -m pip uninstall -y daveagent 2>/dev/null || echo "No previous installation"

# Clean previous builds and memory
rm -rf build dist *.egg-info src/*.egg-info
rm -rf .daveagent/memory  # Clean corrupted memory

# Install in editable mode (uses source code directly, not a copy)
echo "Installing in editable mode..."
python3 -m pip install -e .

# 2. Install Dependencies
echo -e "${GREEN}[2/5] Installing Dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
fi
echo "Installing swebench..."
python3 -m pip install swebench datasets pandas

# 3. Validation
echo -e "${GREEN}[3/5] Validating Installation...${NC}"
if command -v daveagent &> /dev/null; then
    echo -e "${GREEN}✓ daveagent installed successfully${NC}"
else
    echo -e "${RED}Warning: daveagent command not found in PATH${NC}"
fi

# 4. Run Inference
echo -e "${GREEN}[4/5] Running Inference (Limit 200 Tasks)...${NC}"
# Use the correct path for the script
python3 eval/run_inference.py --limit 200 --output eval/predictions.jsonl --repo_dir_base eval/repos

# 5. Run Evaluation Harness
echo -e "${GREEN}[5/5] Running Evaluation Harness...${NC}"
# This requires Docker to be running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH. Required for swebench.${NC}"
    exit 1
fi

echo "Running SWE-bench evaluation..."
# Reduced workers from 4 to 1 to avoid WSL vsock errors
# WSL has issues with multiple simultaneous Docker connections
python3 -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path eval/predictions.jsonl \
    --run_id evaluacion_prueba_v1 \
    --max_workers 1

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}      Evaluation Process Completed           ${NC}"
echo -e "${GREEN}=============================================${NC}"
