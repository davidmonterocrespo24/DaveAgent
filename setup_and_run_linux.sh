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
echo -e "${GREEN}[1/5] Building and Installing Agent...${NC}"

# Clean previous builds and memory
rm -rf build dist *.egg-info
rm -rf .daveagent/memory  # Clean corrupted memory


# Install build tool if missing
if ! python3 -m pip show build &> /dev/null; then
    echo "Installing build..."
    python3 -m pip install build
fi

# Build
python3 -m build

# Install
WHEEL_FILE=$(ls -t dist/*.whl | head -n 1)
if [ -z "$WHEEL_FILE" ]; then
    echo -e "${RED}Error: Build failed, no wheel file found.${NC}"
    exit 1
fi
echo "Installing $WHEEL_FILE..."
python3 -m pip install "$WHEEL_FILE" --force-reinstall

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
echo -e "${GREEN}[4/5] Running Inference (Limit 20 Tasks)...${NC}"
# Use the correct path for the script
python3 eval/run_inference.py --limit 20 --output eval/predictions.jsonl --repo_dir_base eval/repos

# 5. Run Evaluation Harness
echo -e "${GREEN}[5/5] Running Evaluation Harness...${NC}"
# This requires Docker to be running
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH. Required for swebench.${NC}"
    exit 1
fi

echo "Running SWE-bench evaluation..."
python3 -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path eval/predictions.jsonl \
    --run_id evaluacion_prueba_v1 \
    --max_workers 4

echo -e "${GREEN}=============================================${NC}"
echo -e "${GREEN}      Evaluation Process Completed           ${NC}"
echo -e "${GREEN}=============================================${NC}"
