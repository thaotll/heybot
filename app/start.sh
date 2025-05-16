#!/bin/bash

# Commit-ID als ENV (wird via --build-arg beim Docker-Build injiziert)
echo "Using CURRENT_COMMIT_ID=$CURRENT_COMMIT_ID"

# 3) Bots nacheinander starten
echo "▶️ Running main.py..."
python3 /app/main.py

# 4) Container am Leben halten (optional, wenn nötig)
# sleep infinity.
