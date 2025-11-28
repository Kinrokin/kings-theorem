#!/bin/bash
set -e  # Exit on error

# Configuration
LEVEL=7
COUNT=50
RUN_ID="flywheel_run_$(date +%Y%m%d_%H%M%S)"
DATA_DIR="data/flywheel/$RUN_ID"
MODEL_DIR="models/kt-dpo-v1"

echo "🚀 KT SAFE FLYWHEEL INITIALIZED [$RUN_ID]"
mkdir -p "$DATA_DIR"

# 1. GENERATE (Crucibles)
echo -e "\n[1/4] Generating D$LEVEL Crucibles..."
python scripts/generate_crucibles.py \
    --level $LEVEL \
    --count $COUNT \
    --output-dir "$DATA_DIR"

# 2. IGNITE (Safe Async Execution)
echo -e "\n[2/4] Igniting Safe Traces (Async+Lazarus)..."
CRUCIBLE_FILE="$DATA_DIR/kt_crucibles_d$LEVEL.jsonl"
RAW_TRACE_FILE="$DATA_DIR/raw_traces.jsonl"

python scripts/ignite_async_safe.py \
    --input "$CRUCIBLE_FILE" \
    --output "$RAW_TRACE_FILE" \
    --teacher "gpt-4o"

# 3. FILTER (The Critic)
echo -e "\n[3/4] Filtering Quality..."
CLEAN_TRACE_FILE="$DATA_DIR/clean_traces.jsonl"

python scripts/filter_quality.py \
    --input "$RAW_TRACE_FILE" \
    --output "$CLEAN_TRACE_FILE" \
    --threshold 7

# 4. REFINE (Prepare Training Data)
echo -e "\n[4/4] Refining for DPO..."
python scripts/refine_data.py \
    --input "$CLEAN_TRACE_FILE" \
    --output-dir "$DATA_DIR/training" \
    --format dpo

echo -e "\n✅ Data Pipeline Complete. Training Data at: $DATA_DIR/training"
echo -e "   To start training run:"
echo -e "   python scripts/train_dpo_unsloth.py --config config/dpo_config.yaml"
