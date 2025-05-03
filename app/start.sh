#!/bin/bash

# Commit-ID als ENV (wird via --build-arg beim Docker-Build injiziert)
echo "Using CURRENT_COMMIT_ID=$CURRENT_COMMIT_ID"

# 1) OWASP Dependency-Check
echo "▶️ Running OWASP Dependency-Check..."
dependency-check \
  --project heybot \
  --scan /app \
  --format JSON \
  --out /app/analysis/dependency-check-${CURRENT_COMMIT_ID}.json

# 2) Trivy filesystem scan
echo "▶️ Running Trivy scan..."
trivy fs /app -f json -o /app/analysis/trivy-${CURRENT_COMMIT_ID}.json

# 3) Bots nacheinander starten
echo "▶️ Running main.py..."
python3 /app/main.py

echo "▶️ Running bazinga_cve_bot.py..."
python3 /app/bazinga_cve_bot.py

# 4) Container am Leben halten (optional, wenn nötig)
sleep infinity
