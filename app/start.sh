#!/bin/sh
set -e

echo "▶️ Running main.py..."
python3 /app/main.py

echo "▶️ Running bazinga_cve_bot.py..."
python3 /app/bazinga_cve_bot.py
