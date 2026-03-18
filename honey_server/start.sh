#!/bin/bash
# EC2 Startup script for Honeypot Server (Port 8080)
# Run: chmod +x start.sh && ./start.sh

set -e
echo "=== Honey Honeypot Server Setup ==="

# Install Python deps
pip install -r requirements.txt

# Initialize mock database
echo "[*] Initializing mock database..."
python database/init_db.py

# Copy .env from example if not present
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[!] Created .env from example. PLEASE update MONITOR_URL and LOG_SECRET!"
fi

# Start server
PORT=8080 python app.py
