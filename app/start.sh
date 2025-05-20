#!/bin/bash

# Commit-ID als ENV (wird via --build-arg beim Docker-Build injiziert)
echo "Using CURRENT_COMMIT_ID=$CURRENT_COMMIT_ID"

# Path to pre-generated scans baked into the image
PRE_GENERATED_SCANS_DIR="/app/pre_generated_scans"
# Path to the mounted PersistentVolume where scans should be served from
PV_ANALYSIS_DIR="/app/analysis"

# Copy pre-generated scan results to the PV mount if they exist
if [ -d "$PRE_GENERATED_SCANS_DIR" ] && [ "$(ls -A $PRE_GENERATED_SCANS_DIR)" ]; then
  echo "▶️ Found pre-generated scan results. Copying to $PV_ANALYSIS_DIR ..."
  # Ensure target directory exists (it should be created by the PVC mount, but good to be safe)
  mkdir -p "$PV_ANALYSIS_DIR"
  # Copy contents, overwrite if necessary
  cp -r $PRE_GENERATED_SCANS_DIR/* "$PV_ANALYSIS_DIR/"
  echo "✅ Copied pre-generated scan results."
else
  echo "⚠️ No pre-generated scan results found in $PRE_GENERATED_SCANS_DIR or directory is empty."
fi

# 3) Bots nacheinander starten
echo "▶️ Running main.py (likely to start api_server and serve results from $PV_ANALYSIS_DIR)..."
python3 /app/main.py

# 4) Container am Leben halten (optional, wenn nötig)
# sleep infinity.
