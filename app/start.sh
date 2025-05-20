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

# Run main.py in serve mode to prepare/validate data from PV
# This script will now exit after completing its tasks in 'serve' mode.
echo "▶️ Running main.py in serve mode (should use results from $PV_ANALYSIS_DIR)..."
python3 /app/main.py --mode serve 

# Check the exit code of main.py. If it failed, we might not want to start the server.
if [ $? -ne 0 ]; then
  echo "❌ main.py --mode serve failed. Exiting without starting API server."
  exit 1
fi

# NOW, start the FastAPI server as the main long-running process
# It will serve data that main.py has ensured is on the PV.
echo "🚀 Starting FastAPI server (api_server.py) on port 3000..."
exec uvicorn api_server:app --host 0.0.0.0 --port 3000 --log-level info

# The 'exec' command replaces the shell process with uvicorn,
# ensuring uvicorn is the main process (PID 1 if it's the only command after this point)
# and receives signals correctly from Kubernetes.
