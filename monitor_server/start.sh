#!/bin/bash
# EC2 Startup script for Monitor Server (Port 9000)
# Run: chmod +x start.sh && ./start.sh

set -e
echo "=== Honey SOC Monitor Server Setup ==="

pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[!] Created .env. PLEASE set SOC_PASS, LOG_SECRET, and OPENAI_API_KEY!"
fi

# Start server (bind to 0.0.0.0 - secure with AWS Security Group to limit access)
PORT=9000 python app.py
